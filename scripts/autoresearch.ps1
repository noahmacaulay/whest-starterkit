[CmdletBinding()]
param(
    [string]$RepoPath,
    [ValidateSet("Auto", "Worker", "Lead", "Deep")]
    [string]$Role = "Auto",
    [switch]$DryRun,
    [switch]$SkipGitPreflight
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoPath)) {
    $RepoPath = Split-Path -Parent $PSScriptRoot
}

function Get-UtcTimestamp {
    return [DateTime]::UtcNow.ToString("o")
}

function Get-UtcFileTimestamp {
    return [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
}

function Get-PropertyValue {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Name,
        $Default = $null
    )

    if ($null -eq $Object) {
        return $Default
    }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property -or $null -eq $property.Value) {
        return $Default
    }
    return $property.Value
}

function Save-State {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $temporaryPath = "$Path.tmp"
    $State | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $temporaryPath -Encoding UTF8
    Move-Item -LiteralPath $temporaryPath -Destination $Path -Force
}

function New-State {
    param([Parameter(Mandatory = $true)][string]$Now)

    # Delay lead/deep reviews for their configured cadence after installation.
    return [pscustomobject]@{
        schema_version = 1
        created_utc = $Now
        paused = $false
        pause_reason = $null
        consecutive_failures = 0
        retry_after_utc = $null
        last_error = $null
        active_run = $null
        last_worker_started_utc = $null
        last_worker_completed_utc = $null
        last_lead_started_utc = $Now
        last_lead_completed_utc = $Now
        last_deep_started_utc = $Now
        last_deep_completed_utc = $Now
        total_estimated_credits = 0.0
    }
}

function Convert-ToUtcDate {
    param([AllowNull()][string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }
    return [DateTime]::Parse(
        $Value,
        [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::RoundtripKind
    ).ToUniversalTime()
}

function Test-RoleDue {
    param(
        [AllowNull()][string]$LastStartedUtc,
        [Parameter(Mandatory = $true)][double]$IntervalMinutes,
        [Parameter(Mandatory = $true)][DateTime]$Now
    )

    $lastStarted = Convert-ToUtcDate $LastStartedUtc
    if ($null -eq $lastStarted) {
        return $true
    }

    # A small tolerance prevents scheduler jitter from turning 30 minutes into 60.
    $effectiveInterval = [Math]::Max(1.0, $IntervalMinutes - 2.0)
    return (($Now - $lastStarted).TotalMinutes -ge $effectiveInterval)
}

function Get-RoleConfiguration {
    param(
        [Parameter(Mandatory = $true)]$Config,
        [Parameter(Mandatory = $true)][string]$RoleName
    )

    $property = $Config.roles.PSObject.Properties[$RoleName]
    if ($null -eq $property) {
        throw "Missing role configuration: $RoleName"
    }
    return $property.Value
}

function Select-AutomaticRole {
    param(
        [Parameter(Mandatory = $true)]$Config,
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][DateTime]$Now
    )

    if (Test-RoleDue $State.last_deep_started_utc ([double]$Config.deep_interval_hours * 60.0) $Now) {
        return "deep"
    }
    if (Test-RoleDue $State.last_lead_started_utc ([double]$Config.lead_interval_hours * 60.0) $Now) {
        return "lead"
    }
    if (Test-RoleDue $State.last_worker_started_utc ([double]$Config.worker_interval_minutes) $Now) {
        return "worker"
    }
    return $null
}

function Assert-GitPreflight {
    param(
        [Parameter(Mandatory = $true)][string]$Repository,
        [Parameter(Mandatory = $true)][string]$ExpectedBranch
    )

    $topLevel = (& git -c "safe.directory=$Repository" -c "core.excludesFile=" -C $Repository rev-parse --show-toplevel 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Not a Git worktree: $Repository`n$topLevel"
    }

    $resolvedTop = (Resolve-Path -LiteralPath $topLevel).Path.TrimEnd('\', '/')
    $resolvedRepo = (Resolve-Path -LiteralPath $Repository).Path.TrimEnd('\', '/')
    if (-not $resolvedTop.Equals($resolvedRepo, [StringComparison]::OrdinalIgnoreCase)) {
        throw "RepoPath must be the worktree root. Expected '$resolvedTop', got '$resolvedRepo'."
    }

    $branch = (& git -c "safe.directory=$Repository" -c "core.excludesFile=" -C $Repository branch --show-current 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($branch)) {
        throw "Unable to determine the current branch. Detached HEAD is not supported."
    }
    if ($branch -ne $ExpectedBranch) {
        throw "Expected branch '$ExpectedBranch', but worktree is on '$branch'."
    }

    $status = (& git -c "safe.directory=$Repository" -c "core.excludesFile=" -C $Repository status --porcelain --untracked-files=normal 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "git status failed: $status"
    }
    if (-not [string]::IsNullOrWhiteSpace($status)) {
        throw "Worktree is not clean. Commit or resolve these paths before automation:`n$status"
    }
}

function Get-UsageSummary {
    param(
        [Parameter(Mandatory = $true)][string]$JsonlPath,
        [Parameter(Mandatory = $true)][string]$Model
    )

    [long]$inputTokens = 0
    [long]$cachedInputTokens = 0
    [long]$outputTokens = 0
    [long]$reasoningOutputTokens = 0

    if (Test-Path -LiteralPath $JsonlPath) {
        foreach ($line in Get-Content -LiteralPath $JsonlPath) {
            if ([string]::IsNullOrWhiteSpace($line)) {
                continue
            }
            try {
                $event = $line | ConvertFrom-Json
                if ($event.type -ne "turn.completed" -or $null -eq $event.usage) {
                    continue
                }
                $inputTokens += [long](Get-PropertyValue $event.usage "input_tokens" 0)
                $cachedInputTokens += [long](Get-PropertyValue $event.usage "cached_input_tokens" 0)
                $outputTokens += [long](Get-PropertyValue $event.usage "output_tokens" 0)
                $reasoningOutputTokens += [long](Get-PropertyValue $event.usage "reasoning_output_tokens" 0)
            }
            catch {
                # Retain the raw JSONL even if a future event shape is unfamiliar.
            }
        }
    }

    $rates = switch ($Model) {
        "gpt-5.6-sol" { @(125.0, 12.5, 750.0); break }
        "gpt-5.6-terra" { @(62.5, 6.25, 375.0); break }
        "gpt-5.6-luna" { @(25.0, 2.5, 150.0); break }
        default { @(0.0, 0.0, 0.0); break }
    }

    $uncachedInputTokens = [Math]::Max(0, $inputTokens - $cachedInputTokens)
    $estimatedCredits = (
        ($uncachedInputTokens * $rates[0]) +
        ($cachedInputTokens * $rates[1]) +
        ($outputTokens * $rates[2])
    ) / 1000000.0

    return [pscustomobject]@{
        input_tokens = $inputTokens
        cached_input_tokens = $cachedInputTokens
        output_tokens = $outputTokens
        reasoning_output_tokens = $reasoningOutputTokens
        estimated_credits = [Math]::Round($estimatedCredits, 4)
    }
}

$RepoPath = (Resolve-Path -LiteralPath $RepoPath).Path
$configPath = Join-Path $RepoPath "autoresearch\config.json"
if (-not (Test-Path -LiteralPath $configPath)) {
    throw "Missing scheduler config: $configPath"
}
$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json

$runtimePath = Join-Path $RepoPath ".autoresearch-runtime"
$logPath = Join-Path $runtimePath "logs"
$statePath = Join-Path $runtimePath "state.json"
$usagePath = Join-Path $runtimePath "usage.csv"
New-Item -ItemType Directory -Path $logPath -Force | Out-Null
$runnerLogPath = Join-Path $runtimePath "runner.log"

function Write-RunnerLog {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [ValidateSet("INFO", "WARN", "ERROR")][string]$Level = "INFO"
    )

    $record = "{0} [{1}] {2}" -f (Get-UtcTimestamp), $Level, $Message
    Add-Content -LiteralPath $runnerLogPath -Value $record -Encoding UTF8
    Write-Host $record
}

$mutex = $null
$hasMutex = $false
$state = $null
$scriptExitCode = 0

try {
    $mutexName = "Global\$($config.mutex_name)"
    try {
        $mutex = New-Object Threading.Mutex($false, $mutexName)
    }
    catch {
        $mutexName = "Local\$($config.mutex_name)"
        $mutex = New-Object Threading.Mutex($false, $mutexName)
    }

    try {
        $hasMutex = $mutex.WaitOne(0)
    }
    catch [Threading.AbandonedMutexException] {
        $hasMutex = $true
    }

    if (-not $hasMutex) {
        Write-RunnerLog "Skipped: another autoresearch run holds $mutexName."
        return
    }

    $now = [DateTime]::UtcNow
    if (Test-Path -LiteralPath $statePath) {
        $state = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
    }
    else {
        $state = New-State $now.ToString("o")
        if (-not $DryRun) {
            Save-State $state $statePath
        }
    }

    if ($null -ne $state.active_run) {
        $abandonedId = Get-PropertyValue $state.active_run "run_id" "unknown"
        $state.active_run = $null
        $state.consecutive_failures = [int]$state.consecutive_failures + 1
        $state.last_error = "Recovered abandoned run $abandonedId."
        Write-RunnerLog $state.last_error "WARN"
    }

    if ([bool]$state.paused) {
        Write-RunnerLog "Paused: $($state.pause_reason)" "WARN"
        return
    }

    $retryAfter = Convert-ToUtcDate $state.retry_after_utc
    if ($null -ne $retryAfter -and $now -lt $retryAfter) {
        Write-RunnerLog "Backoff active until $($retryAfter.ToString('o'))."
        return
    }

    $roleKey = if ($Role -eq "Auto") {
        Select-AutomaticRole $config $state $now
    }
    else {
        $Role.ToLowerInvariant()
    }

    if ([string]::IsNullOrWhiteSpace($roleKey)) {
        Write-RunnerLog "No role is due on this scheduler tick."
        return
    }

    $roleConfig = Get-RoleConfiguration $config $roleKey
    $promptPath = Join-Path $RepoPath ($roleConfig.prompt -replace '/', '\')
    if (-not (Test-Path -LiteralPath $promptPath)) {
        throw "Missing role prompt: $promptPath"
    }

    $codexCommand = Get-Command codex -ErrorAction Stop
    $codexPath = $codexCommand.Source
    if ([string]::IsNullOrWhiteSpace($codexPath)) {
        $codexPath = $codexCommand.Name
    }

    if (-not $SkipGitPreflight) {
        Assert-GitPreflight $RepoPath ([string]$config.expected_branch)
    }

    $arguments = @(
        "exec",
        "--profile", [string]$roleConfig.profile,
        "--sandbox", "workspace-write",
        "--ephemeral",
        "--json",
        "-"
    )

    if ($DryRun) {
        Write-RunnerLog ("DRY RUN role={0} model={1} effort={2}" -f $roleKey, $roleConfig.model, $roleConfig.reasoning_effort)
        Write-Host ("Working directory: {0}" -f $RepoPath)
        Write-Host ("Prompt: {0}" -f $promptPath)
        Write-Host ("Command: {0} {1}" -f $codexPath, ($arguments -join ' '))
        return
    }

    $runId = "{0}-{1}" -f (Get-UtcFileTimestamp), $roleKey
    $startedUtc = Get-UtcTimestamp
    $jsonlPath = Join-Path $logPath "$runId.jsonl"
    $stderrPath = Join-Path $logPath "$runId.stderr.log"
    $lastMessagePath = Join-Path $logPath "$runId.final.txt"
    $arguments = @(
        "exec",
        "--profile", [string]$roleConfig.profile,
        "--sandbox", "workspace-write",
        "--ephemeral",
        "--json",
        "--output-last-message", $lastMessagePath,
        "-"
    )

    $state.active_run = [pscustomobject]@{
        run_id = $runId
        role = $roleKey
        profile = [string]$roleConfig.profile
        model = [string]$roleConfig.model
        started_utc = $startedUtc
        pid = $PID
    }
    $startedProperty = "last_{0}_started_utc" -f $roleKey
    $state.$startedProperty = $startedUtc
    Save-State $state $statePath
    Write-RunnerLog "Starting $runId with profile '$($roleConfig.profile)'."

    $prompt = Get-Content -Raw -LiteralPath $promptPath
    Push-Location $RepoPath
    try {
        $prompt | & $codexPath @arguments 1> $jsonlPath 2> $stderrPath
        $codexExitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    $completedUtc = Get-UtcTimestamp
    $usage = Get-UsageSummary $jsonlPath ([string]$roleConfig.model)
    $usageRecord = [pscustomobject]@{
        run_id = $runId
        role = $roleKey
        profile = [string]$roleConfig.profile
        model = [string]$roleConfig.model
        reasoning_effort = [string]$roleConfig.reasoning_effort
        started_utc = $startedUtc
        completed_utc = $completedUtc
        exit_code = $codexExitCode
        input_tokens = $usage.input_tokens
        cached_input_tokens = $usage.cached_input_tokens
        output_tokens = $usage.output_tokens
        reasoning_output_tokens = $usage.reasoning_output_tokens
        estimated_credits = $usage.estimated_credits
    }
    if (Test-Path -LiteralPath $usagePath) {
        $usageRecord | Export-Csv -LiteralPath $usagePath -NoTypeInformation -Append
    }
    else {
        $usageRecord | Export-Csv -LiteralPath $usagePath -NoTypeInformation
    }
    $state.total_estimated_credits = [double]$state.total_estimated_credits + [double]$usage.estimated_credits
    $state.active_run = $null

    if ($codexExitCode -ne 0) {
        throw "Codex exited with code $codexExitCode. See $stderrPath"
    }

    $completedProperty = "last_{0}_completed_utc" -f $roleKey
    $state.$completedProperty = $completedUtc
    $state.consecutive_failures = 0
    $state.retry_after_utc = $null
    $state.last_error = $null
    Save-State $state $statePath
    Write-RunnerLog ("Completed {0}; estimated credits={1}." -f $runId, $usage.estimated_credits)
}
catch {
    $message = $_.Exception.Message
    Write-RunnerLog $message "ERROR"
    $scriptExitCode = 1

    if ($null -ne $state -and -not $DryRun) {
        $state.active_run = $null
        $state.consecutive_failures = [int]$state.consecutive_failures + 1
        $state.last_error = $message
        $failureCount = [int]$state.consecutive_failures
        $backoffMinutes = [Math]::Min(
            240.0,
            [double]$config.failure_backoff_minutes * [Math]::Pow(2.0, [Math]::Max(0, $failureCount - 1))
        )
        $state.retry_after_utc = [DateTime]::UtcNow.AddMinutes($backoffMinutes).ToString("o")

        if ($failureCount -ge [int]$config.max_consecutive_failures) {
            $state.paused = $true
            $state.pause_reason = "Paused after $failureCount consecutive failures. Last error: $message"
            Write-RunnerLog $state.pause_reason "WARN"
        }
        Save-State $state $statePath
    }
}
finally {
    if ($hasMutex -and $null -ne $mutex) {
        try {
            $mutex.ReleaseMutex()
        }
        catch {
        }
    }
    if ($null -ne $mutex) {
        $mutex.Dispose()
    }
}

exit $scriptExitCode
