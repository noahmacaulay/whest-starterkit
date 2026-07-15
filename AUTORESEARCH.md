# Codex autoresearch scheduler

This repository includes a Windows scheduler for the `gpt` side of the WHEST
research loop. It deliberately contains no model coordinator: a small
PowerShell runner chooses the due role, while each Codex run follows
`AGENTS.md` and coordinates with Claude through `origin/main`.

## Cadence

| Role | Model | Reasoning | Frequency |
|---|---|---|---|
| Worker | GPT-5.6 Terra | High | Every 30 minutes |
| Lead review | GPT-5.6 Sol | High | Every 6 hours, replacing that worker tick |
| Deep review | GPT-5.6 Sol | XHigh | Every 24 hours, replacing that worker tick |

Max and Ultra are not scheduled. The public `codex exec` configuration exposes
reasoning effort through `xhigh`; Ultra is an app-level multi-agent mode and is
best reserved for deliberate, divisible reviews.

The runner starts a fresh ephemeral Codex session each time. A Windows named
mutex and Task Scheduler's `IgnoreNew` policy prevent overlap. Three
consecutive failures pause the loop, with exponential backoff before then.

## Files

- `autoresearch-config/config.json`: cadence, branch, profile, and failure policy.
- `autoresearch-config/prompts/`: durable prompts for each role.
- `autoresearch-config/profiles/`: templates copied into `$CODEX_HOME` by the
  installer.
- `scripts/autoresearch.ps1`: role selection, locking, preflight, execution,
  failure handling, and token accounting.
- `scripts/install-autoresearch-task.ps1`: installs profiles and registers the
  Windows task.
- `scripts/manage-autoresearch.ps1`: status, pause/resume, enable/disable, and
  manual role runs.
- `scripts/uninstall-autoresearch-task.ps1`: removes the task and optionally
  local profiles/runtime state.
- `.autoresearch-runtime/`: ignored machine-local state, JSONL logs, final
  messages, stderr, and `usage.csv`.

Credit estimates use the GPT-5.6 token rates current when this scaffold was
created. They are useful for comparing runs but are not an authoritative plan
balance. Check `/status` or the Codex usage dashboard for actual remaining
limits.

## Safety model

Automated profiles use `workspace-write`, `approval_policy = "never"`, and
outbound network access. This allows unattended Git synchronization and fixed
dataset access while keeping filesystem writes inside the worktree. Do not put
secrets in the repository, prompts, environment variables, or logs.

The runner refuses to start Codex unless:

- it is at the root of a Git worktree;
- the checked-out branch is exactly `agent/gpt`; and
- the worktree is completely clean.

Each model run must finish on `agent/gpt` with a clean tree. A stale promotion
branch, merge conflict, uncommitted edit, missing profile, or failed command
backs off and eventually pauses instead of accumulating damage.

External submission remains governed by the reservation protocol in
`AGENTS.md`. If AIcrowd authentication is inaccessible inside the sandbox, the
run must leave an exact-ID blocker rather than weakening the sandbox or
guessing whether submission succeeded.

## One-time setup on the research laptop

First commit and push the scheduler/protocol scaffold to `main`. From the
admin checkout, create the GPT worktree:

```powershell
git fetch origin
git worktree add ..\whest-gpt -b agent/gpt origin/main
```

If `agent/gpt` already exists, omit `-b` and pass the existing branch name.
Then enter the new worktree and prepare the environment:

```powershell
Set-Location ..\whest-gpt
uv sync --frozen
codex login
uv run --frozen whest login
```

Confirm Git push credentials and download/validate the pinned Phase 1 Mini
dataset once before enabling unattended runs. Keep the laptop logged in,
powered, and awake enough for Task Scheduler; the task itself requests wake
permission.

Install profiles and register the task in a disabled state:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-autoresearch-task.ps1
```

The installer refuses to run from `main` or a dirty/non-Git directory. It
copies only the three named profile templates and does not alter your base
`~/.codex/config.toml`.

## Test and enable

Preview the exact selected profile, prompt, and command without invoking a
model or changing scheduler state:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\autoresearch.ps1 -Role Worker -DryRun
powershell -ExecutionPolicy Bypass -File .\scripts\autoresearch.ps1 -Role Lead -DryRun
powershell -ExecutionPolicy Bypass -File .\scripts\autoresearch.ps1 -Role Deep -DryRun
```

Inspect the registered task and state:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\manage-autoresearch.ps1 -Action Status
```

Enable the recurring task:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\manage-autoresearch.ps1 -Action Enable
```

Review the first several runs before leaving the loop unattended. Runtime
artifacts appear under `.autoresearch-runtime/`.

## Operations

```powershell
# Pause scheduling and preserve state.
powershell -ExecutionPolicy Bypass -File .\scripts\manage-autoresearch.ps1 -Action Pause -Reason "Reviewing results"

# Clear failure/backoff state and re-enable.
powershell -ExecutionPolicy Bypass -File .\scripts\manage-autoresearch.ps1 -Action Resume

# Run a role immediately, still respecting mutex/branch/cleanliness checks.
powershell -ExecutionPolicy Bypass -File .\scripts\manage-autoresearch.ps1 -Action RunWorker
powershell -ExecutionPolicy Bypass -File .\scripts\manage-autoresearch.ps1 -Action RunLead
powershell -ExecutionPolicy Bypass -File .\scripts\manage-autoresearch.ps1 -Action RunDeep

# Disable future ticks without changing state.
powershell -ExecutionPolicy Bypass -File .\scripts\manage-autoresearch.ps1 -Action Disable
```

To remove only the Windows task:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\uninstall-autoresearch-task.ps1
```

Add `-RemoveProfiles` or `-RemoveRuntimeState` only when those local files are
no longer needed. Runtime removal is recursive and asks for confirmation.
