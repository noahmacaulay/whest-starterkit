# WHEST autoresearch

Read `AGENTS.md` and follow it exactly. It is the canonical protocol for this
repo's two-agent autonomous research loop. Your agent ID is `claude`, your
local worktree branch is `agent/claude`, and all shared changes must be
explicitly rebased onto and fast-forward pushed to `origin/main`.

Key traps it protects against are warmup/depth-8 defaults, stale virtual
environments, incomparable datasets, claim and promotion races, noisy
unpaired wins, and duplicate submissions. Treat `uv.lock` plus the pinned
Phase 1 dataset revision as the reproducibility source of truth; an existing
`.venv` may be stale. Never use a plain `git pull`, plain `git push`,
force-push, or automatic retry of an ambiguous submission.
