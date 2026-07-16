# Experiment backlog

Claim protocol: start from a clean worktree, fetch/rebase the agent branch
onto `origin/main`, mark the item `CLAIMED <agent> <UTC timestamp>`, commit,
and explicitly run `git push origin HEAD:main` **before starting work**. A
claim that exists only on `agent/claude` or `agent/gpt` is not valid. A
rejected push means another worker updated the shared state: fetch/rebase and
check again; if the item was taken, drop only the unpushed claim edit and pick
the next item. Never force-push.

When finished, mark the item `DONE <agent>` and leave it in place. Persist the
candidate, immutable result report, and your append-only log before any
promotion. Alternate explore/exploit where possible. Add new ideas as
unclaimed items with the next free ID and a one-line hypothesis.

## Queue

- [x] **B0** (exploit, run this first) - Baseline everything. DONE gpt 2026-07-16T01:32:05Z
  Use the immutable public Phase 1 Mini split
  (`aicrowd/arc-whestbench-public-2026@v1-phase1`, 100 MLPs) with the explicit
  `272000000000` budget and subprocess runner. Measure on exactly the same
  MLPs: current `estimator.py` (full-cov propagation, gain-product
  off-diagonal), `examples/02_mean_propagation.py`,
  `examples/03_covariance_propagation.py`, and a plain Monte Carlo estimator
  at about 6,500 samples (the 0.1-floor sampling baseline,
  `C approximately 2.72e10`). Save raw JSON reports and the
  WhestBench/Flopscope/lockfile metadata. Fill `champion.json` with the winner
  and its paired-comparison evidence. Use the independent Full split for the
  first submission gate. Until B0 is done, no other item may be claimed.

- [ ] **B1** (exploit) - Productionize active-subspace Gauss-Hermite
  quadrature from `experiments/active_subspace_quadrature_depth32.ipynb`.
  Hypothesis: depth-32 collapse makes the net approximately 1-D along the
  dominant Jacobian direction; 8-32 GH nodes along it plus a cheap orthogonal
  correction beats both covariance propagation and the 6.5k-sample MC
  baseline.

- [ ] **B2** (explore) - Control-variate hybrid. Deterministic estimate
  (champion analytic method) plus a small MC batch correcting its bias:
  `final = analytic + mean(MC_true - MC_analytic_prediction)` on shared
  inputs. Hypothesis: residual variance is much smaller than raw variance, so
  a few hundred samples suffice; unbiased by construction.

- [ ] **B3** (exploit) - Exact ReLU cross-moments in covariance propagation.
  Replace the gain-product off-diagonal approximation in `estimator.py`
  (`cov_post[i,j] approximately Phi(alpha_i)Phi(alpha_j)cov_pre[i,j]`) with
  the exact bivariate Gaussian ReLU cross-moment (arccos-kernel form). FLOPs
  are irrelevant at the 0.1 floor; hypothesis: compounding off-diagonal bias
  over 32 layers is a dominant error term.

- [ ] **B4** (explore) - QMC plus antithetic sampling. Sobol points and/or
  antithetic pairs for whatever MC component the champion uses, applied in
  the active subspace first. Hypothesis: error decays faster than
  `N^(-1/2)`, strictly dominating plain MC at fixed FLOPs.

- [ ] **B5** (explore) - Rank-adaptive low-rank covariance propagation.
  Propagate `Sigma approximately D + UU^T` with rank chosen per MLP from the
  spectrum (see `experiments/covariance_spectrum_depth32.ipynb`). Verify
  rank-1 dominance across many seeds, not just the notebook's. Payoff: similar
  accuracy to full covariance at approximately `n^2 k` cost, and a diagnostic
  of when low-rank assumptions break.

- [ ] **B6** (explore) - Mean-field asymptotic correction. Fit the known
  depth-asymptotics of the ReLU collapse (fixed-point plus `1/layer`
  correction terms) as an analytic prior for deep layers; use early-layer
  exact propagation plus an asymptotic tail. Hypothesis: cheaper and possibly
  more accurate than propagating approximation error through all 32 layers.

## Done

(nothing yet)
