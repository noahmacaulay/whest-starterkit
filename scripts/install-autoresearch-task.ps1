[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$RepoPath,
    [switch]$Enable,
    [switch]$ForceProfiles
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoPath)) {
    $RepoPath = Split-Path -Parent $PSScriptRoot
}

if ($env:OS -ne "Windows_NT") {
    throw "This installer targets Windows Task Scheduler."
}

$RepoPath = (Resolve-Path -LiteralPath $RepoPath).Path
$configPath = Join-Path $RepoPath "autoresearch\config.json"
$runnerPath = Join-Path $RepoPath "scripts\autoresearch.ps1"
$profilesPath = Join-Path $RepoPath "autoresearch\profiles"

foreach ($requiredPath in @($configPath, $runnerPath, $profilesPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Missing required scaffold path: $requiredPath"
    }
}

$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
$topLevel = (& git -c "safe.directory=$RepoPath" -c "core.excludesFile=" -C $RepoPath rev-parse --show-toplevel 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "RepoPath is not a Git worktree: $RepoPath"
}
$resolvedTop = (Resolve-Path -LiteralPath $topLevel).Path.TrimEnd('\', '/')
if (-not $resolvedTop.Equals($RepoPath.TrimEnd('\', '/'), [StringComparison]::OrdinalIgnoreCase)) {
    throw "RepoPath must be the root of the GPT worktree: $resolvedTop"
}

$branch = (& git -c "safe.directory=$RepoPath" -c "core.excludesFile=" -C $RepoPath branch --show-current | Out-String).Trim()
if ($branch -ne [string]$config.expected_branch) {
    throw "Install from '$($config.expected_branch)', not '$branch'. See AUTORESEARCH.md."
}

$codexCommand = Get-Command codex -ErrorAction Stop
Write-Host "Using $($codexCommand.Source)"
& codex login status
if ($LASTEXITCODE -ne 0) {
    throw "Codex is not logged in. Run 'codex login' first."
}

$codexHome = if ([string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
    Join-Path $HOME ".codex"
}
else {
    $env:CODEX_HOME
}
New-Item -ItemType Directory -Path $codexHome -Force | Out-Null

foreach ($roleName in @("worker", "lead", "deep")) {
    $role = $config.roles.PSObject.Properties[$roleName].Value
    $fileName = "$($role.profile).config.toml"
    $source = Join-Path $profilesPath $fileName
    $destination = Join-Path $codexHome $fileName
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Missing profile template: $source"
    }

    if (Test-Path -LiteralPath $destination) {
        $same = (Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash -eq
            (Get-FileHash -Algorithm SHA256 -LiteralPath $destination).Hash
        if (-not $same -and -not $ForceProfiles) {
            throw "Profile exists with different content: $destination. Use -ForceProfiles to replace it."
        }
    }

    if ($PSCmdlet.ShouldProcess($destination, "Install Codex profile")) {
        Copy-Item -LiteralPath $source -Destination $destination -Force
        Write-Host "Installed profile $destination"
    }
}

Import-Module ScheduledTasks -ErrorAction Stop
$taskName = [string]$config.task_name
$powershellPath = (Get-Command powershell.exe -ErrorAction Stop).Source
$argument = '-NoLogo -NoProfile -ExecutionPolicy Bypass -File "{0}" -RepoPath "{1}"' -f `
    $runnerPath.Replace('"', '""'), $RepoPath.Replace('"', '""')

$action = New-ScheduledTaskAction -Execute $powershellPath -Argument $argument -WorkingDirectory $RepoPath
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval ([TimeSpan]::FromMinutes([double]$config.worker_interval_minutes)) `
    -RepetitionDuration ([TimeSpan]::FromDays(3650))
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -WakeToRun `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::FromMinutes([double]$config.task_execution_limit_minutes))
$userId = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
    -Description "Runs the GPT side of the WHEST autoresearch loop with model/cadence selection."

if ($PSCmdlet.ShouldProcess($taskName, "Register Windows scheduled task")) {
    Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null
    if ($Enable) {
        Enable-ScheduledTask -TaskName $taskName | Out-Null
        Write-Host "Registered and enabled task '$taskName'."
    }
    else {
        Disable-ScheduledTask -TaskName $taskName | Out-Null
        Write-Host "Registered task '$taskName' in a disabled state."
        Write-Host "Test first, then enable with: powershell -ExecutionPolicy Bypass -File .\scripts\manage-autoresearch.ps1 -Action Enable"
    }
}

Write-Host "Profiles: $codexHome"
Write-Host "Worktree: $RepoPath"
Write-Host "Runtime logs will be written to: $(Join-Path $RepoPath '.autoresearch-runtime')"
