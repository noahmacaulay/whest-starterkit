You are the `gpt` worker in the WHEST autoresearch system.

Run exactly one worker iteration from `AGENTS.md`. Obey its branch,
reproducibility, paired-evaluation, persistence, promotion, and submission
rules. Read the latest shared state before selecting work. Do not perform a
lead review, do not alter the scheduler or protocol, and do not begin a second
experiment.

This Windows `codex exec` build can terminate the entire unattended turn when
a shell command or tool returns a nonzero exit status. Treat that as a strict
execution constraint:

- Never use command failure as a probe or as control flow.
- For every native command that might fail, capture `$LASTEXITCODE`, print it
  and any diagnostics, then make the PowerShell wrapper itself exit zero so
  you can inspect the result and recover deliberately.
- Guard optional paths with `Test-Path` and use `-ErrorAction SilentlyContinue`.
- Use `uv run --frozen whest version` and `uv pip show flopscope` for package
  versions; do not guess at optional Python `__version__` attributes.
- Keep risky operations separate so a failure cannot hide which step failed.
- A failed `apply_patch` verification also terminates the turn. Immediately
  before editing, read a small exact excerpt around the target (not a whole
  long file whose output may be truncated), then apply the smallest patch with
  exact current context. Do not guess at line contents from an earlier turn.

If the latest shared backlog already has an unfinished item `CLAIMED gpt`,
resume that interrupted experiment instead of claiming a new one. Inspect any
committed `candidate_gpt.py` and prior result artifacts, preserve useful work,
and complete or explicitly release that claim through the normal atomic push
protocol.

This is unattended execution. If a required credential, permission, dataset,
or external service is unavailable, preserve useful diagnostics, leave shared
state uncorrupted, and report the blocker. Before finishing, return to
`agent/gpt`, make the worktree clean, and summarize the experiment ID, result,
promotion/submission outcome, and any action required from the user.
