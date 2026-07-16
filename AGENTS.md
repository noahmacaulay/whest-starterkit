# WHEST autoresearch protocol (two agents)

Autonomous research loop for Phase 1 of the ARC White-Box Estimation
Challenge (WHEST) 2026. Two agents, `claude` and `gpt`, work in separate
worktrees on long-lived local branches named `agent/claude` and `agent/gpt`.
They coordinate through `origin/main`; no model acts as a central research
coordinator.

The Git server is the concurrency control. A claim, persisted result,
promotion, or submission reservation counts only after a normal
fast-forward push to `origin/main` succeeds. Never force-push and never use a
plain `git pull` or `git push` in an agent worktree: always name
`origin/main` explicitly.

## Ground truth about the task

- Estimate per-neuron post-ReLU means of random MLPs under standard-normal
  inputs. `predict()` returns shape `(mlp.depth, mlp.width)`.
- Phase 1 shape: width 256, depth 32. Phase 1 FLOP budget:
  `B = 272000000000` per MLP.
- Score (lower is better): `final_layer_mse * max(0.1, C/B)`, averaged over
  MLPs. Only the final layer is scored; other layers are diagnostics.
- A budget breach zeros the predictions and forces the multiplier to 1.0.
  Check `budget_exhausted`, `combined_budget_exhausted`, and all time/error
  flags before accepting a result.
- The 0.1 floor binds at `C = 2.72e10` FLOPs. Analytic methods currently use
  much less, so accuracy is the main lever while they remain below the floor.
- Phase 1 is depth 32. Do not use warmup defaults or the `v1-warmup` dataset.
- Known structure: at depth 32 the net is deep in mean-field collapse and the
  Jacobian/covariance is often rank-1 dominated. Supporting analysis lives in
  `experiments/*.ipynb`.

## Reproducibility contract

`uv.lock`, not an existing `.venv`, is the dependency source of truth. A
machine may have a stale environment even when the lockfile is current.

Before its first iteration, and whenever `uv.lock` changes, each worker runs:

```text
uv sync --frozen
uv run --frozen whest version
```

Record the WhestBench/Flopscope versions and the `uv.lock` commit in every
result. If the two machines report different versions, stop: their scores are
not comparable. Run all research commands as `uv run --frozen ...` so an
iteration cannot silently rewrite or upgrade the environment.

The canonical evaluation dataset is the immutable public Phase 1 release:

```text
hf://aicrowd/arc-whestbench-public-2026@v1-phase1
```

- Use split `mini` (100 MLPs) for routine paired comparisons.
- Use the independent `full` split (1,000 MLPs) before submission.
- Never compare numbers measured on different dataset revisions, splits,
  budgets, lockfile versions, or runner configurations.
- A private local bake is optional for quick debugging only. If one is used
  for a decision, commit an explicit `--mlp-seeds` JSON manifest and record
  the complete bake command plus the dataset metadata hash. `dataset bake`
  has no `--seed` option; omitting `--mlp-seeds` generates fresh random seeds
  and is not reproducible across machines.

## Branch and file ownership

| File/ref | Owner | Rule |
|---|---|---|
| `origin/main` | shared | Serialization point and complete research history. Every accepted update is a normal fast-forward push. |
| `agent/claude`, `agent/gpt` | per-agent | Local worktree branches. Rebase onto `origin/main`; never push them implicitly. |
| `estimator.py` | shared | Always the current champion. Change only in an atomic promotion commit. |
| `candidate_claude.py`, `candidate_gpt.py` | per-agent | Scratch implementation. Never edit the other agent's candidate. |
| `champion.json` | shared | Champion and submission ledger. Never update it separately from the estimator/result it describes. |
| `BACKLOG.md` | shared | Idea queue. Claims become valid only when pushed to `origin/main`. |
| `experiments/log-claude.md`, `experiments/log-gpt.md` | per-agent | Append-only human summaries. Read both from `origin/main` each iteration. |
| `experiments/results/<agent>/` | per-agent | Immutable machine-readable reports, named by experiment ID and base-champion short SHA. |

At the beginning and end of every tick, the worktree must be clean. Candidate
work must be committed before fetching/rebasing; do not rely on autostash for
untracked files.

## Atomic shared update

All shared updates use this optimistic-concurrency pattern:

1. Commit the local change on the agent branch.
2. `git fetch origin`.
3. Rebase the clean agent branch onto `origin/main` and resolve only genuine
   metadata/log conflicts. Never resolve a conflict by overwriting a newer
   `estimator.py` or `champion.json`.
4. Re-check any invariant affected by the new `origin/main` state.
5. Push explicitly with `git push origin HEAD:main`.
6. A rejected push means another worker won the race. Fetch and reconsider;
   never force-push and never mechanically replay stale champion or submission
   state.

For ordinary claims and rejected-result logs, rebasing and retrying is safe.
A promotion is different: build it on a short-lived promotion branch created
from the latest `origin/main`. If its push is rejected, discard only that
unpushed promotion proposal, preserve the candidate/result commit, and build
a new proposal from the new `origin/main` after reevaluation. Do not blindly
rebase a stale promotion commit, because it contains an old `estimator.py`
and old `champion.json`.

## One worker iteration

### 1. Sync and recover

- Confirm the worktree is clean.
- `git fetch origin`, then rebase the agent branch onto `origin/main`.
- Read `champion.json`, both logs, recent result reports, and `BACKLOG.md`.
- If an unfinished item is already `CLAIMED <this agent>`, resume that
  interrupted iteration and its committed candidate/results instead of
  claiming a second item. Complete it or explicitly release it through the
  same atomic shared-update protocol.
- If the submission ledger contains an active `submitting` reservation, do
  not submit anything else. Reconcile it only from an exact submission ID or
  exact attempt ID. Never guess a score from a nearby timestamp or team name.

### 2. Claim exactly one experiment

Pick the top unclaimed backlog item, respecting the explore/exploit
alternation. Mark it `CLAIMED <agent> <UTC timestamp>`, commit, and push it
with the atomic shared-update procedure before doing experimental work.

If the push is rejected, fetch and rebase. If the other agent claimed the
item, drop only your unpushed claim edit and choose the next item. A claim on
an agent-only branch is not a claim.

### 3. Implement

Create an experiment ID such as `B3-gpt-20260715T143000Z`. Copy the current
`estimator.py` to `candidate_<agent>.py`, implement one timeboxed hypothesis,
and commit the candidate before the next sync/rebase.

### 4. Evaluate as a paired experiment

First validate:

```text
uv run --frozen whest validate --estimator candidate_<agent>.py
```

Then run both the current champion and the candidate on the same immutable
Mini split, using subprocess isolation and JSON output:

```text
uv run --frozen whest run --estimator estimator.py --runner subprocess \
    --dataset hf://aicrowd/arc-whestbench-public-2026@v1-phase1 \
    --split mini --flop-budget 272000000000 --format json

uv run --frozen whest run --estimator candidate_<agent>.py --runner subprocess \
    --dataset hf://aicrowd/arc-whestbench-public-2026@v1-phase1 \
    --split mini --flop-budget 272000000000 --format json
```

Save the raw reports under `experiments/results/<agent>/`. Record the base
champion/result commit, exact commands, environment versions, dataset
revision/split, aggregate scores, FLOPs, and all failure flags.

For each MLP compute the paired difference
`d_m = candidate_adjusted_score_m - champion_adjusted_score_m`. Lower is
better. Ground-truth Monte Carlo noise is not the only uncertainty: the
finite set of MLPs also creates suite-sampling uncertainty. Promote only when
the mean paired difference is negative and its conservative 95% confidence
interval is entirely below zero. Also report the relative aggregate
improvement and worst per-MLP regressions. Never promote a within-uncertainty
win or any run with a failure/budget/time flag.

### 5. Persist the result before promotion

Append to your log, save the machine-readable reports, mark the backlog item
`DONE <agent>`, and queue any follow-up ideas. Commit the candidate, result,
log, and backlog together and push them to `origin/main` with the shared
update procedure. This commit does not modify `estimator.py` or champion
state. A logged rejected experiment is a completed product.

### 6. Promote with compare-and-swap semantics

If the candidate passed the paired gate:

1. Fetch `origin/main` again and re-read `champion.json`.
2. If `estimator.py`, its recorded result, the dataset contract, or the
   environment changed since evaluation, rerun the paired comparison against
   the new champion.
3. From the latest `origin/main`, build a short-lived promotion proposal that
   copies only your candidate over `estimator.py` and updates `champion.json`
   with the experiment ID, source result commit, scores, dataset revision and
   split, environment versions, timestamp, agent, and description.
4. Validate the proposed `estimator.py`, commit the estimator and champion
   update atomically, and push with `git push origin HEAD:main`.
5. Only a successful push is a promotion. On rejection, abandon the stale
   proposal and return to step 1; do not overwrite or blindly rebase the
   winner's champion state.

### 7. Reserve and submit only a meaningful improvement

Submission is serialized separately from promotion. The preferred eventual
implementation is a single-concurrency CI job triggered by `main`; until
then, `champion.json` is the compare-and-swap submission ledger.

Submit only when the new champion:

- passes the same paired gate on the independent `full` split;
- improves by at least 5% over `last_submitted_score` measured under the same
  full-split/environment contract; and
- has no active `submitting` reservation in the ledger.

Before any network submission:

1. Confirm the exact champion is still current on `origin/main`.
2. Validate it and run the Full gate.
3. Package it to a stable artifact path, compute its SHA-256, and retain the
   artifact until grading finishes.
4. Add a ledger entry with a unique attempt ID, champion/result identity,
   exact submitted champion commit, local Full score/report, artifact
   path/hash, timestamp, and `status: submitting` with no submission ID yet.
   Commit and atomically push this reservation to `origin/main`.
5. Proceed only if that reservation push succeeds and the reservation is
   still the sole active one. Otherwise do not submit.

Submit the already-hashed artifact, not a freshly repackaged estimator:

```text
uv run --frozen whest submit <artifact.tar.gz> --watch --format json \
    --description "<attempt-id> <champion-result-id>"
```

Immediately update the same ledger entry with the returned `submission_id`,
leaderboard score, and `graded`, `pending`, or `failed` status; update
`last_submitted_score` only for the exact recorded local Full score.

If the command times out after returning a submission ID, retain `pending`
and poll that exact ID later. If it fails or crashes before returning an ID,
do not automatically retry: the server may have accepted it. Reconcile using
the exact attempt description or escalate to a lead/user. Pre-scaffold
submissions with neither an ID nor an exact attempt ID are manual-recovery
items and must never be matched automatically by timestamp alone.

### 8. Finish cleanly

Persist any final ledger/log changes through the shared update procedure and
switch back to `agent/<agent>`, then leave the worktree clean. Do not start a
second experiment in the same tick. The unattended scheduler treats the wrong
branch or a dirty worktree as a failure and pauses after repeated failures.

## One-time machine/worktree setup

Create both worktrees from the same `origin/main`, with one long-lived local
branch per agent. The exact parent paths are machine-specific; the invariant
is that no **agent** worktree has `main` checked out and both agent branches
explicitly fetch/rebase/push against `origin/main`. An admin-only checkout of
`main` may remain at the original repository path, but do not run a worker
loop from it.

For a fresh clone, a typical layout is:

```text
git fetch origin
git worktree add ../whest-claude -b agent/claude origin/main
git worktree add ../whest-gpt -b agent/gpt origin/main
```

If a branch or worktree already exists, reuse it rather than recreating it.
Run the following inside each agent worktree:

```text
uv sync --frozen
uv run --frozen whest version
uv run --frozen whest login
```

The public Mini/Full datasets download once per machine and are cached. Do
not copy API keys into the repo, logs, prompts, or submission artifacts.

Claude worker invocation from Claude's worktree: start `claude`, then run
`/loop 30m Run one worker iteration following AGENTS.md`.

The GPT worker can be run unattended on Windows using the single-instance
scheduler documented in `AUTORESEARCH.md`. Its routine/lead/deep profiles are
Terra High every 30 minutes, Sol High every 6 hours, and Sol XHigh every 24
hours. Max and Ultra remain manual modes because they are not ordinary
`codex exec` reasoning-effort values.

The Claude lead review runs unattended once daily (07:00 local) via the
Windows scheduled task `WHEST Claude Lead Review`, from the dedicated
`whest-claude-lead` worktree on the lead-only branch `lead/claude` (this
branch performs lead reviews only — no experiments, no submissions — and
pushes shared changes to `origin/main` like any agent branch). The runner and
its prompt are machine-local under that worktree's `.autoresearch-runtime/`.
The Claude worker remains an interactive `/loop` session in `whest-claude`
on `agent/claude` and is not scheduled.

## Worker ticks and lead reviews

- **Worker tick** (default): perform exactly one iteration above. Workers may
  append ideas but do not reorder priorities or delete lines of research.
- **Lead review** (strong model, explicitly invoked about once or twice per
  day): perform no experiment. Read both logs/results, reconcile exact-ID
  pending submissions, audit the champion math and reproducibility metadata,
  and reprioritize/prune/merge backlog items with rationale in the lead's own
  log. Never clear an ambiguous submission reservation automatically.

## Guardrails

- Do not modify the harness, WhestBench internals, tests, scoring, or this
  protocol during a worker tick. Protocol changes are reviewed separately.
- Do not edit the other agent's candidate, result files, or log.
- Randomness in `predict()` seeds from `mlp.seed` via
  `fnp.random.default_rng(mlp.seed)`; in `setup()` it seeds from `ctx.seed`.
  Do not call `fnp.random.seed(...)` or invent cross-MLP state.
- No `print()` in `predict()`; no filesystem/network access outside
  `SetupContext.scratch_dir`; keep `setup()` idempotent and under about 5s.
- Timebox one hypothesis per iteration. Split larger work into backlog items.
- Logs and result records are append-only. Never rewrite successful pushes,
  delete another agent's work, use `--force`, or resolve a race by choosing
  your own stale champion.
- If a clean checkout fails validation, fixing it is the iteration.

## Log entry template

```markdown
## <UTC timestamp> - <experiment ID: title>
- Hypothesis:
- Base champion: <result/commit identity>
- Environment: whestbench=..., flopscope=..., uv.lock@...
- Evaluation: dataset=...@v1-phase1, split=mini, budget=272000000000,
  runner=subprocess, exact commands/results=...
- Change: <one paragraph; candidate_<agent>.py @ commit>
- Result: candidate_score=..., champion_score=..., relative_change=...,
  paired_mean_delta=..., paired_95pct_CI=..., flops_used=..., failures=...
- Verdict: PROMOTED | REJECTED | INCONCLUSIVE, with reason
- Full/submission gate: NOT_RUN | PASS | FAIL; attempt/submission ID if any
- New ideas queued: <IDs or "none">
```
