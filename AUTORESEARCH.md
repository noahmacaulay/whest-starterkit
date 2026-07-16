# Codex autoresearch scheduler

This repository includes a Windows scheduler for the `gpt` side of the WHEST
research loop. It deliberately contains no model coordinator: a small
PowerShell runner chooses the due role, while each Codex run follows
`AGENTS.md` and coordinates with Claude through `origin/main`.

## Cadence

| Role | Model | Reasoning | Frequency |
|---|---|---|---|
| Worker | GPT-5.6 Sol | High | Every 15 minutes |
| Lead review | GPT-5.6 Sol | XHigh | Every 2 hours, replacing that worker tick |
| Deep review | GPT-5.6 Sol | Ultra | Every 6 hours, replacing that worker tick |
| Backup recovery | GPT-5.6 Sol | XHigh | Replaces any tick whose worktree is dirty |

The installed `codex exec` build was validated with Sol Ultra before enabling
that profile. All roles remain serialized: lead, deep, or recovery replaces a
worker tick, and the mutex prevents overlapping writes to the worktree.
In-session multi-agent spawning is disabled in unattended profiles; the backup
is a fresh scheduler-launched process with its own trace.

The runner starts a fresh ephemeral Codex session each time. A Windows named
mutex and Task Scheduler's `IgnoreNew` policy prevent overlap. Three
consecutive failures pause the loop, with exponential backoff before then.
The runner also forces UTF-8 for Python and child-process I/O so Windows'
legacy console code page cannot break tests or WhestBench reports.

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

Automated profiles use `danger-full-access` with `approval_policy = "never"`.
This is required because a complete worker tick writes Git metadata, pushes to
GitHub, writes package/dataset caches, and may submit to AIcrowd; the Windows
`workspace-write` sandbox deliberately protects Git metadata. Run this task
only from a dedicated Windows account on the research laptop. That account has
the security boundary: do not keep unrelated credentials, documents, mounted
shares, browser sessions, secrets, or SSH keys accessible to it. Repository,
Codex, GitHub, and AIcrowd credentials are necessarily in scope.

The runner refuses to start Codex unless:

- it is at the root of a Git worktree;
- the checked-out branch is exactly `agent/gpt`.

Any tracked or untracked worktree change routes to the dedicated Sol XHigh
backup recovery agent instead of an ordinary research role. Recovery inspects
diffs and logs, may commit a coherent interrupted checkpoint, and may preserve
clearly invalid partial outputs under ignored runtime storage. It may not reset,
clean, force, delete, or overwrite ambiguous work. Ordinary research resumes
only after recovery leaves `agent/gpt` clean; otherwise the runner backs off and
eventually pauses with the recovery trace available for review.

Interrupted WhestBench output is handled specially because Mini and Full runs
can outlive a shell tool's default timeout. The worker prompt requires a
30-minute tool timeout and continued polling of yielded commands. If a process
still ends early, the next tick launches the recovery role to inspect all dirty
paths, preserve invalid partial output under
`.autoresearch-runtime/interrupted/`, and hand the already-claimed experiment
back to the next worker.

External submission remains governed by the reservation protocol in
`AGENTS.md`. If AIcrowd authentication is unavailable, the run must leave an
exact-ID blocker rather than guessing whether submission succeeded.

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
copies only the four named profile templates and does not alter your base
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
powershell -ExecutionPolicy Bypass -File .\scripts\manage-autoresearch.ps1 -Action RunRecovery

# Disable future ticks without changing state.
powershell -ExecutionPolicy Bypass -File .\scripts\manage-autoresearch.ps1 -Action Disable
```

To remove only the Windows task:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\uninstall-autoresearch-task.ps1
```

Add `-RemoveProfiles` or `-RemoveRuntimeState` only when those local files are
no longer needed. Runtime removal is recursive and asks for confirmation.
