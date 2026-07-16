[CmdletBinding()]
param(
    [string]$RepoPath,
    [ValidateSet("Status", "Pause", "Resume", "Enable", "Disable", "RunWorker", "RunLead", "RunDeep", "RunRecovery")]
    [string]$Action = "Status",
    [string]$Reason = "Paused by user"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoPath)) {
    $RepoPath = Split-Path -Parent $PSScriptRoot
}

$RepoPath = (Resolve-Path -LiteralPath $RepoPath).Path
$config = Get-Content -Raw -LiteralPath (Join-Path $RepoPath "autoresearch-config\config.json") | ConvertFrom-Json
$runtimePath = Join-Path $RepoPath ".autoresearch-runtime"
$statePath = Join-Path $runtimePath "state.json"
$runnerPath = Join-Path $RepoPath "scripts\autoresearch.ps1"
$taskName = [string]$config.task_name

function Save-ManagedState {
    param($State)
    New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
    $temporaryPath = "$statePath.tmp"
    $State | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $temporaryPath -Encoding UTF8
    Move-Item -LiteralPath $temporaryPath -Destination $statePath -Force
}

function Get-ManagedState {
    if (-not (Test-Path -LiteralPath $statePath)) {
        throw "No runtime state exists yet. Run a dry test or enable the task first."
    }
    return Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
}

switch ($Action) {
    "Status" {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($null -eq $task) {
            Write-Host "Scheduled task: not installed"
        }
        else {
            $info = Get-ScheduledTaskInfo -TaskName $taskName
            Write-Host "Scheduled task: $($task.State)"
            Write-Host "Last run: $($info.LastRunTime) (result $($info.LastTaskResult))"
            Write-Host "Next run: $($info.NextRunTime)"
        }
        if (Test-Path -LiteralPath $statePath) {
            Get-Content -Raw -LiteralPath $statePath
        }
        else {
            Write-Host "Runtime state: not created"
        }
    }
    "Pause" {
        Disable-ScheduledTask -TaskName $taskName | Out-Null
        $state = Get-ManagedState
        $state.paused = $true
        $state.pause_reason = $Reason
        Save-ManagedState $state
        Write-Host "Paused and disabled '$taskName'."
    }
    "Resume" {
        $state = Get-ManagedState
        $state.paused = $false
        $state.pause_reason = $null
        $state.consecutive_failures = 0
        $state.retry_after_utc = $null
        $state.last_error = $null
        Save-ManagedState $state
        Enable-ScheduledTask -TaskName $taskName | Out-Null
        Write-Host "Resumed and enabled '$taskName'."
    }
    "Enable" {
        Enable-ScheduledTask -TaskName $taskName | Out-Null
        Write-Host "Enabled '$taskName'."
    }
    "Disable" {
        Disable-ScheduledTask -TaskName $taskName | Out-Null
        Write-Host "Disabled '$taskName'."
    }
    "RunWorker" { & $runnerPath -RepoPath $RepoPath -Role Worker; exit $LASTEXITCODE }
    "RunLead" { & $runnerPath -RepoPath $RepoPath -Role Lead; exit $LASTEXITCODE }
    "RunDeep" { & $runnerPath -RepoPath $RepoPath -Role Deep; exit $LASTEXITCODE }
    "RunRecovery" { & $runnerPath -RepoPath $RepoPath -Role Recovery; exit $LASTEXITCODE }
}
