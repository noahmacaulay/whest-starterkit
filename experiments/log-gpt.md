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

## 2026-07-16T04:12:58Z - B9-gpt-20260716T035249Z: Scrambled Sobol QMC
- Hypothesis: a per-MLP digital-shifted Sobol input net, transformed by the normal inverse CDF, reduces final-layer MC error enough to overcome the higher compute multiplier at a 32,768-point power-of-two batch.
- Base champion: estimator.py @ 0cd32b3 (B0-gpt-20260716T002459Z source result 58900f1); candidate_gpt.py @ da3cb39.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5, uv.lock@9b677e2b91b0b4791c73c9449b6d5e5491093ddb.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1 (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433), split=mini (100 MLPs), budget=272000000000, runner=subprocess. Exact commands and raw reports are in results/gpt/B9-gpt-20260716T035249Z-0cd32b3-summary.json.
- Change: generated a 32-bit Sobol digital net with a per-dimension random digital shift from `fnp.random.default_rng(mlp.seed)`, transformed the points through `flops.stats.norm.ppf`, and ran the existing tracked ReLU forward pass for 32,768 samples.
- Result: candidate adjusted score=0.321098933595; champion=9.290663024139e-07; relative_change=+34561365.932018%; paired_mean_delta=0.321098004528; paired_95pct_CI=[0.156571998698,0.485624010358]; worst_per_MLP_regression=6.620156135154 (100/100). Candidate final-layer MSE=0.321147337293 vs champion=8.504929468245e-06; candidate mean effective compute=1.222814740469e+11 vs champion=2.969721159935e+10. The candidate had 27 `error` flags (all budget/time flags=0).
- Verdict: REJECTED: conversion to float32 before the inverse CDF rounded some endpoint-adjacent Sobol uniforms to exactly 0 or 1, returning infinite inputs and non-finite predictions for 27 MLPs. This alone fails the gate; the 73 finite runs also regress sharply, so a rerun with endpoint clipping would not be a meaningful promotion attempt.
- Full/submission gate: NOT_RUN; the Mini gate failed and S1 still blocks any submission reservation.
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

## 2026-07-16T02:21:51Z - B2-gpt-20260716T022151Z: Soft-gate affine control variate
- Hypothesis: a diagonal-Gaussian soft-gate affine control, whose sampled expectation is the analytic intercept, reduces MC variance enough to dominate the plain 6,500-sample champion at comparable FLOPs.
- Base champion: estimator.py @ 1598169 (B0-gpt-20260716T002459Z source result 58900f1); candidate_gpt.py @ c4b2b50.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5, uv.lock@2c84f3b0131859397fbfecea333503af142fd50f.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1 (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433), split=mini (100 MLPs), budget=272000000000, runner=subprocess. Exact commands and immutable raw reports are in results/gpt/B2-gpt-20260716T022151Z-f46426c-summary.json.
- Change: B2 propagates diagonal Gaussian moments and a soft-gated input Jacobian, then returns `analytic_mean + mean(true_MC - affine_control)` using 3,250 shared standard-normal draws. The affine control has the analytic mean by construction, so the correction remains unbiased even if the diagonal recursion is inaccurate.
- Result: candidate adjusted score=1.705461503122e-06; champion=9.372216070962e-07; relative_change=+81.969930%; paired_mean_delta=7.682398960260e-07; paired_95pct_CI=[4.160712073034e-07,1.120408584749e-06]; worst_per_MLP_regression=8.084468507160e-06 (78/100). Candidate final-layer MSE=1.373127810325e-05 vs champion=8.504929468245e-06; candidate mean effective compute=3.381394405609e+10 vs 2.999551920011e+10. All failure/budget/time/error flags=0.
- Verdict: REJECTED: the control both increased final-layer MSE and added enough compute to worsen adjusted score; its paired interval is wholly positive.
- Full/submission gate: NOT_RUN; the Mini promotion gate failed.
- New ideas queued: none.

## 2026-07-16T03:10:25Z - B5-gpt-20260716T025143Z: Rank-adaptive low-rank covariance propagation
- Hypothesis: an adaptively truncated diagonal-plus-low-rank covariance recursion preserves sufficient deep rank structure to improve analytic propagation at lower FLOPs.
- Base champion: estimator.py @ 1598169 (B0-gpt-20260716T002459Z source result 58900f1); candidate_gpt.py @ b417d79.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5, uv.lock@2c84f3b0131859397fbfecea333503af142fd50f.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1 (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433), split=mini (100 MLPs), budget=272000000000, runner=subprocess. Exact commands and immutable raw reports are in results/gpt/B5-gpt-20260716T025143Z-1598169-summary.json.
- Change: B5 represents covariance as `diag(d) + U U^T`; at each layer, it applies deflated power iterations to the implicit propagated covariance, retains up to 16/8/4 directions by depth, and discards components under 0.5% of total variance before the soft-gate ReLU update.
- Result: candidate adjusted score=8.921633108632e-05; champion=9.359644650594e-07; relative_change=+9432.021184%; paired_mean_delta=8.828036662126e-05; paired_95pct_CI=[7.511143152093e-05,1.014493017216e-04]; worst_per_MLP_regression=4.175872130467e-04 (100/100). Candidate final-layer MSE=8.655785491283e-04 vs champion=8.504929468245e-06; candidate mean effective compute=2.352669817635e+10 vs 2.991925450011e+10; mean FLOPs=3.308926730000e+08 vs 2.734617600000e+10. All failure/budget/time/error flags=0.
- Verdict: REJECTED: low-rank truncation loses correlation structure throughout the network; the adjusted score is about 95x worse and the conservative paired interval is wholly positive.
- Full/submission gate: NOT_RUN; the Mini promotion gate failed.
- New ideas queued: none.

### B5 metadata correction
- The normal rebase before result persistence rewrote the evaluated candidate commit from local `b417d79` to reachable commit `990f73d`; the candidate contents and raw reports are unchanged.

## 2026-07-16T05:02:00Z - B6-gpt-20260716T050200Z: Empirical-prefix mean-field tail
- Hypothesis: at depth 32, retaining the exact 6,500-sample Monte Carlo path through layer 24 and then continuing from its empirical diagonal moments with an 8-layer Gaussian mean-field recursion preserves enough collapse structure to reduce the score at the 0.1 compute floor.
- Base champion: estimator.py @ c25eff6 (B0-gpt-20260716T002459Z source result 58900f1); candidate_gpt.py @ b96ef2e.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5, uv.lock@9b677e2b91b0b4791c73c9449b6d5e5491093ddb.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1 (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433), split=mini (100 MLPs), budget=272000000000, runner=subprocess. Exact commands and immutable raw reports are in results/gpt/B6-gpt-20260716T050200Z-c25eff6-summary.json.
- Change: sample normally through layer 24, estimate the activation mean and marginal second moment from that prefix, then propagate the remaining eight layers with independent-Gaussian ReLU moment updates. This tests a deliberately conservative deep-tail mean-field approximation while lowering mean FLOPs below the 2.72e10 score floor.
- Result: candidate adjusted score=1.243952942605e-04; champion=9.291407001645e-07; relative_change=+13288.208507%; paired_mean_delta=1.234661535603e-04; paired_95pct_CI=[1.040306558238e-04,1.429016512968e-04]; worst_per_MLP_regression=5.261040339943e-04 (100/100). Candidate final-layer MSE=1.243952942605e-03 vs champion=8.504929468245e-06; candidate mean FLOPs=2.052491443200e+10 (multiplier=0.1) vs champion=2.734617600000e+10 (multiplier=0.109273349633). All failure/budget/time/error flags=0.
- Verdict: REJECTED: the tail approximation's systematic bias emerges immediately at layer 25 and overwhelms its 25% compute saving; the conservative paired interval is wholly positive.
- Full/submission gate: NOT_RUN; the Mini promotion gate failed.
- New ideas queued: none.

### B9 metadata correction
- The normal rebase after result persistence rewrote evaluated candidate commit `da3cb39` to reachable commit `38de845`; candidate contents and all persisted reports are unchanged.

## 2026-07-16T04:44:30Z - B11-gpt-20260716T042143Z: Materialized soft-gate Jacobian power iteration
- Hypothesis: B10's active-subspace Gauss-Hermite estimator has a reproducible 6% final-layer-MSE advantage, but its fragmented power iteration causes enough Flopscope overhead to fail the adjusted-score gate. Materializing the full soft-gate Jacobian once per MLP and applying it in the same four forward/reverse power iterations should replace 256 small matvec calls with 32 matrix products plus 8 matvec calls while retaining B10's statistical estimator.
- Base champion: estimator.py @ 136db85 (B0-gpt-20260716T002459Z source result 58900f1); candidate_gpt.py @ 2d3e0fd.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5, uv.lock@9b677e2b91b0b4791c73c9449b6d5e5491093ddb.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1 (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433), split=mini (100 MLPs), budget=272000000000, runner=subprocess. Exact commands and UTF-16 JSON raw reports are in results/gpt/B11-gpt-20260716T042143Z-136db85-summary.json.
- Change: copied B10's 16-node Gauss-Hermite conditional sampling unchanged. Its soft-gate layer Jacobians were multiplied to J = diag(g_L)W_L^T...diag(g_1)W_1^T, then the existing four J/J^T power iterations produced the direction. This is algebraically equivalent to B10 but changes the operation grouping.
- Result: candidate_score=1.020054551790e-06; champion_score=9.282648109981e-07; relative_change=+9.888314%; paired_mean_delta=9.178974079157e-08; paired_95pct_CI=[-2.062819180994e-07,3.898613996825e-07]; worst_per_MLP_regression=3.668090503424e-06 (60/100 regressed). Candidate final-layer MSE=7.995433086876e-06 vs champion=8.504929468245e-06; candidate mean effective compute=3.470575014855e+10 vs champion=2.968605609961e+10; mean FLOPs=2.854392894800e+10 vs 2.734617600000e+10. All failure/budget/time/error flags=0.
- Verdict: REJECTED. The numerical estimator retained B10's MSE exactly, and candidate effective compute fell modestly versus B10's 3.515560582827e+10, but the matrix-product arithmetic raised raw FLOPs and the paired confidence interval still crosses zero. It is therefore not promotable.
- Full/submission gate: NOT_RUN; the Mini promotion gate failed and the shared ledger also has unresolved manual submission entries.
- New ideas queued: none.

## 2026-07-16T05:35:21Z - B14-gpt-20260716T052400Z: Elementwise diagonal soft-gate variance propagation
- Hypothesis: B13's 2-iteration active-subspace Gauss-Hermite estimator retained its ~6% final-layer-MSE advantage but still paid for 32 small `pre_variance = (w*w).T @ variance` calls. Computing the same diagonal products as exact elementwise reductions could eliminate that matmul tracing overhead without altering the estimator.
- Base champion: estimator.py @ a43d388 (B0-gpt-20260716T002459Z source result 58900f1); candidate_gpt.py @ a12116c.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5, uv.lock@9b677e2b91b0b4791c73c9449b6d5e5491093ddb.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1 (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433), split=mini (100 MLPs), budget=272000000000, runner=subprocess. Exact commands and immutable raw reports are in results/gpt/B14-gpt-20260716T052400Z-a43d388/summary.json.
- Change: reused B13's 2-pass layer-wise power iteration, 16-node Gauss-Hermite quadrature, antithetic orthogonal-complement samples, and one main batched forward pass per layer. Replaced only the diagonal variance matmul with `sum((w*w)*variance[:,None], axis=0)`.
- Result: candidate_score=9.823833763060e-07; champion_score=9.276159262378e-07; relative_change=+5.904108%; paired_mean_delta=5.476745006812e-08; paired_95pct_CI=[-2.424236863733e-07,3.519585865095e-07]; worst_per_MLP_regression=3.506124165489e-06 (59/100 regressed). Candidate final-layer MSE=7.931290535907e-06 vs champion=8.504929468245e-06, but candidate mean effective compute=3.372870757778e+10 vs champion=2.965928580012e+10; mean FLOPs=2.748591627600e+10 vs 2.734617600000e+10. All failure, budget, time, residual-wall-time, and combined-budget flags=0.
- Verdict: REJECTED. The calculation preserved B13's accuracy exactly and reduced its effective compute relative to B13, but not enough to overcome the remaining overhead; the adjusted score regressed and the conservative paired confidence interval is not entirely below zero.
- Full/submission gate: NOT_RUN; the Mini promotion gate failed and no submission reservation was created.
- New ideas queued: none.

### B14 metadata correction
- The rebase before result persistence rewrote the evaluated candidate commit from local `a12116c` to reachable commit `6e9f547`; candidate contents and raw reports are unchanged.
