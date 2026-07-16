# Experiment log - claude

Append-only. One entry per iteration, using the reproducibility and paired
comparison template in `AGENTS.md`. Read the latest `origin/main` version of
`log-gpt.md` and both agents' immutable result reports before starting.

(no entries yet)

## Lead review 2026-07-16T01:55:18Z
- Role: scheduled lead review on `lead/claude` (no experiment, no estimator
  edit, no submission). Rebased onto `origin/main` at ca50e28.
- State read: `log-gpt.md` B0 entry, all seven B0 result reports under
  `experiments/results/gpt/`, `champion.json`, `BACKLOG.md`. `log-claude.md`
  had no worker entries yet. The B0 promotion (commit 1598169) landed at
  2026-07-16T01:32:05Z, ~23 minutes before this review.
- Submission reconciliation: no active `submitting` reservation and no
  pending entry with an exact submission or attempt ID, so there is nothing
  reconcilable. The two 2026-06-11 pre-scaffold entries remain manual-recovery
  items; their embedded notes suggest backfilling by timestamp matching,
  which contradicts the AGENTS.md rule against timestamp-only matching —
  queued as admin item S1 for the user rather than acted on. Left
  `champion.json` untouched.
- Champion audit (B0-gpt-20260716T002459Z, MC 6,500 samples): recomputed from
  the per-MLP records in the raw mini JSON reports. Mean per-MLP adjusted
  score 9.393561814840653e-07, mean MSE 8.504929468e-06, and a full
  recomputation of `mse * max(0.1, C/B)` per MLP all match the recorded
  aggregates to machine precision. Paired delta vs the incumbent recomputed
  as -7.42691574836045e-06 with 95% CI [-8.6256238e-06, -6.2282077e-06]
  (matches; t-based, n=100), 1 regressed MLP with worst regression
  +2.0201e-06 (matches). All budget/time/error flags are zero across all
  four reports; effective compute spans [2.975e10, 3.076e10], every MLP
  under the 2.72e11 budget. Champion math is sound; no defect found, so no
  defect backlog item was needed.
- Metadata audit: dataset revision, sha256, split, budget, runner,
  whestbench/flopscope versions, and environment identity are all present
  and self-consistent. One nit: `uv_lock_commit`
  (2c84f3b0131859397fbfecea333503af142fd50f) is the git *blob* hash of
  `uv.lock` (verified: `git hash-object uv.lock` reproduces it), not a
  commit SHA. Content-addressing is actually the stronger identifier, so
  reproducibility is intact; future entries should either keep using blob
  hashes consistently or record both. Log-only observation, no action.
- Structural insight driving reprioritization: the champion runs at
  C≈3.01e10 > the 2.72e10 floor, so its multiplier is ~0.1107 and, for
  plain MC, adjusted score is approximately invariant to sample count
  (MSE∝1/N cancels multiplier∝N above the floor). Consequences: (a)
  trimming samples to the floor buys nothing; (b) variance reduction divides
  the score directly; (c) any method with error decaying faster than
  N^(-1/2) makes score fall with N up to the full budget, worth up to ~9x.
- Backlog changes: reordered queue to B4 > B1 > B2 > B3 > B5 > B6 with
  lead-priority annotations and per-item rationale (B4 is the cheapest
  direct upgrade to the MC champion; B1 may produce a strong analytic core;
  B2 composes that core with MC and with B4's QMC; B3's main value is as a
  better analytic core for B2). No items pruned or merged — all remain
  plausible. Added admin item S1 (submission pipeline blocked on user
  backfill of the two legacy pre-scaffold submissions; null
  `last_submitted_score` makes the 5% gate undecidable).
- Escalations for the user: S1 above. Also note the Full-split gate for the
  new champion has not been run yet; it is required before any submission
  and can be run by a worker as part of the (currently blocked) submission
  path.
- Race note: while this review was in progress, gpt claimed B1
  (CLAIMED gpt 2026-07-16T02:21:15Z) and pushed it to origin/main, which
  conflicted with the backlog reorder. Resolved by preserving gpt's valid
  claim in place under the new ordering; the claim predates the
  reprioritization, so gpt proceeding with B1 this iteration is correct, and
  B4 stands as the top unclaimed item for the next worker.
