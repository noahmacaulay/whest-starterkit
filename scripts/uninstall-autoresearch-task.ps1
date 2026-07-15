[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = "High")]
param(
    [string]$RepoPath,
    [switch]$RemoveProfiles,
    [switch]$RemoveRuntimeState
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoPath)) {
    $RepoPath = Split-Path -Parent $PSScriptRoot
}

$RepoPath = (Resolve-Path -LiteralPath $RepoPath).Path
$configPath = Join-Path $RepoPath "autoresearch-config\config.json"
$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
$taskName = [string]$config.task_name

Import-Module ScheduledTasks -ErrorAction Stop
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    if ($PSCmdlet.ShouldProcess($taskName, "Unregister Windows scheduled task")) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "Removed task '$taskName'."
    }
}

if ($RemoveProfiles) {
    $codexHome = if ([string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
        Join-Path $HOME ".codex"
    }
    else {
        $env:CODEX_HOME
    }
    foreach ($roleName in @("worker", "lead", "deep")) {
        $role = $config.roles.PSObject.Properties[$roleName].Value
        $profilePath = Join-Path $codexHome "$($role.profile).config.toml"
        if ((Test-Path -LiteralPath $profilePath) -and
            $PSCmdlet.ShouldProcess($profilePath, "Remove Codex profile")) {
            Remove-Item -LiteralPath $profilePath -Force
        }
    }
}

if ($RemoveRuntimeState) {
    $runtimePath = Join-Path $RepoPath ".autoresearch-runtime"
    if ((Test-Path -LiteralPath $runtimePath) -and
        $PSCmdlet.ShouldProcess($runtimePath, "Remove autoresearch logs and state recursively")) {
        $resolvedRuntime = (Resolve-Path -LiteralPath $runtimePath).Path
        $expectedRuntime = Join-Path $RepoPath ".autoresearch-runtime"
        if (-not $resolvedRuntime.Equals($expectedRuntime, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove unexpected runtime path: $resolvedRuntime"
        }
        Remove-Item -LiteralPath $resolvedRuntime -Recurse -Force
    }
}
