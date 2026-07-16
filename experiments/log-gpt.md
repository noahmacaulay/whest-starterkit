# Experiment log - gpt

Append-only. One entry per iteration, using the reproducibility and paired
comparison template in `AGENTS.md`. Read the latest `origin/main` version of
`log-claude.md` and both agents' immutable result reports before starting.

## 2026-07-16T01:32:05Z - B0-gpt-20260716T002459Z: Phase 1 Mini baseline
- Hypothesis: the four baseline estimators establish the first measurable champion; a 6,500-sample MC estimator should be competitive at the compute-floor boundary.
- Base champion: estimator.py @ a6fca1e; candidate_gpt.py @ 966a985.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5, uv.lock@2c84f3b0131859397fbfecea333503af142fd50f.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1 (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433), split=mini (100 MLPs), budget=272000000000, runner=subprocess. Exact commands and raw reports are in results/gpt/B0-gpt-20260716T002459Z-a6fca1e-summary.json.
- Change: compared the incumbent full-covariance gain-product estimator, plain 6,500-sample MC, supplied mean propagation, and supplied covariance propagation. Console warnings are retained beside each extracted valid JSON report.
- Result: MC adjusted score=9.393561814841e-07; incumbent=8.366271929845e-06; relative_change=-88.772106%; paired_mean_delta=-7.426915748360e-06; paired_95pct_CI=[-8.625623788742e-06,-6.228207707979e-06]; worst_per_MLP_regression=2.020052241232e-06 (1/100); MC mean flops=3.010941500058e+10; all failure/budget/time/error flags=0. Mean propagation=9.482214921445e-05 and covariance propagation=8.366271929845e-06.
- Verdict: PROMOTION_PENDING: the MC Mini paired gate passes; persist this result, then perform the required fresh-state compare-and-swap promotion.
- Full/submission gate: NOT_RUN.
- New ideas queued: none.
- Promotion resolution: PROMOTED atomically to origin/main at 1598169 after a fresh-state check against result commit 58900f1.
- Submission resolution: NOT_RUN. `last_submitted_score` is null and the ledger contains only legacy `pending` records without exact IDs, so the required 5% improvement comparison and safe reconciliation cannot be made; no reservation was created.

## 2026-07-16T02:21:15Z - B1-gpt-20260716T022115Z: Active-subspace Gauss-Hermite conditional MC
- Hypothesis: depth-32 collapse makes a top-1 soft-gate-Jacobian direction suitable for 16-node Gauss-Hermite integration, with antithetic conditional Monte Carlo correcting the orthogonal subspace more efficiently than plain MC.
- Base champion: estimator.py @ 1598169 (B0-gpt-20260716T002459Z source result 58900f1); candidate_gpt.py @ a0dbad7.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5, uv.lock@2c84f3b0131859397fbfecea333503af142fd50f.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1 (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433), split=mini (100 MLPs), budget=272000000000, runner=subprocess. Exact commands and immutable raw reports are in results/gpt/B1-gpt-20260716T022115Z-76c2ab2-summary.json.
- Change: B1 derives a dominant direction through four soft-gate power iterations, integrates it with a fixed 16-node probabilists' Gauss-Hermite rule, and propagates weighted antithetic conditional batches through every layer. Pair allocations are proportional to quadrature mass (6,516 total forward samples).
- Result: candidate adjusted score=1.144664880338e-06; champion=9.480602897957e-07; relative_change=+20.737562%; paired_mean_delta=1.966045905419e-07; paired_95pct_CI=[-1.079136381728e-07,5.011228192566e-07]; worst_per_MLP_regression=4.120869834933e-06 (64/100). Candidate final-layer MSE=7.995440876130e-06 vs champion=8.504929468245e-06, but candidate mean effective FLOPs=3.891589193513e+10 vs 3.034638999961e+10 and multiplier=0.143073132114 vs 0.111567610293. All failure/budget/time/error flags=0.
- Verdict: REJECTED: the adjusted score regressed and the conservative paired confidence interval is not entirely below zero.
- Full/submission gate: NOT_RUN; the Mini promotion gate failed.
- New ideas queued: none.
