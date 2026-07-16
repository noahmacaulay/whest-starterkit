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
