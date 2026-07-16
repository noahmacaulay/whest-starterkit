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

## 2026-07-16T02:47:00Z - B4-claude-20260716T024700Z: Antithetic-paired MC
- Hypothesis: antithetic-paired sampling (z, -z) at the same total sample
  count/FLOPs as the B0 MC champion reduces estimator variance, which divides
  the adjusted score directly since effective compute (and thus the score
  multiplier) is unchanged.
- Base champion: estimator.py @ 1598169 (B0-gpt-20260716T002459Z source
  result 58900f1); candidate_claude.py @ 56b4223, claimed from ebffd25.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5+np2.2.6,
  uv.lock@2c84f3b0131859397fbfecea333503af142fd50f (matches the recorded
  champion metadata; confirmed via `uv sync --frozen` + `whest version` at
  the start of this iteration).
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1
  (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433),
  split=mini (100 MLPs), budget=272000000000, runner=subprocess. Exact
  commands and raw reports are in
  results/claude/B4-claude-20260716T024700Z-1598169-summary.json.
- Change: candidate_claude.py draws 3,250 iid standard-normal rows per MLP
  and concatenates them with their negation to form the same 6,500 total
  rows the champion uses, so per-MLP FLOPs are unchanged; only the sample
  construction differs (paired instead of fully iid).
- Result: candidate adjusted score=8.892516550819e-07; champion
  adjusted score=9.524083760984e-07; relative_change=-6.631265%;
  paired_mean_delta=-6.315672101643e-08; paired_95pct_CI=
  [-4.059104786305e-07, 2.795970365976e-07]; worst_per_MLP_regression=
  3.193724772486e-06 (52/100 regressed). Candidate final-layer MSE=
  7.949875915756e-06 vs champion=8.504929468245e-06; mean effective compute
  3.043846e10 vs 3.036330e10 (multiplier 0.111906 vs 0.111630, essentially
  flat as intended). All failure/budget/time/error flags=0.
- Layer-wise diagnostic (mean MSE by layer, champion vs candidate):
  layer 0 -46.4%, layer 1 -34.6%, layer 2 -28.4%, layer 5 -16.4%, layer 10
  -11.2%, layer 15 -8.9%, layer 20 -4.4%, layer 25 +2.6%, layer 31 (scored)
  -6.5%. The antithetic pair's variance reduction is strong near the input
  and decays through depth-32 mean-field collapse until it is smaller than
  MLP-suite sampling noise at the scored final layer — consistent with the
  known rank-1/collapse structure scrambling the (z, -z) correlation faster
  than it scrambles ordinary iid variance.
- Verdict: REJECTED (within-uncertainty): mean paired delta is negative but
  the conservative 95% CI is not entirely below zero (52/100 MLPs
  regressed), so this does not clear the promotion gate despite the
  favorable aggregate relative change.
- Full/submission gate: NOT_RUN; the Mini paired gate failed.
- New ideas queued: B7 - re-antithetize at intermediate layers instead of
  only at the input, since the layer-wise diagnostic shows pair correlation
  (and thus variance reduction) decaying to noise well before layer 31;
  periodically reflecting the running activations (or reflecting only in the
  active-subspace direction from B1's Jacobian estimate) may sustain the
  antithetic benefit deeper into the network at the same FLOP cost.
