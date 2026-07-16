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

- [x] **B4** (explore, lead-priority 1) - DONE claude 2026-07-16T02:47:00Z - QMC plus antithetic sampling. Sobol
  points and/or antithetic pairs for whatever MC component the champion uses,
  applied in the active subspace first. Hypothesis: error decays faster than
  `N^(-1/2)`, strictly dominating plain MC at fixed FLOPs. Lead note
  2026-07-16: the B0 champion is plain MC at C≈3.01e10 > the 2.72e10 floor,
  so its adjusted score is approximately N-invariant (MSE∝1/N cancels
  against multiplier∝N). Any variance reduction divides the score directly,
  and faster-than-`N^(-1/2)` error decay makes the score fall with N all the
  way up to the full 2.72e11 budget — the largest and cheapest expected win.
  Result: input-level antithetic pairing (z, -z) at unchanged FLOPs was
  REJECTED — mean paired delta negative (-6.3e-08, -6.6% relative) but the
  95% CI straddled zero (52/100 MLPs regressed). Layer-wise MSE diagnostic
  showed the variance reduction decaying from -46% at layer 0 to noise level
  by layer ~25, i.e. depth-32 collapse scrambles the antithetic correlation
  before the scored final layer. See `experiments/log-claude.md` and
  `experiments/results/claude/B4-claude-20260716T024700Z-1598169-summary.json`.
  Sobol/QMC and true active-subspace-first framing were not attempted this
  iteration (timeboxed to the antithetic sub-hypothesis); still open for a
  future iteration if desired. Follow-up queued as B7.

- [x] **B1** (exploit, lead-priority 2) - Productionize active-subspace Gauss-Hermite quadrature. DONE gpt 2026-07-16T02:21:15Z
  From `experiments/active_subspace_quadrature_depth32.ipynb`.
  Hypothesis: depth-32 collapse makes the net approximately 1-D along the
  dominant Jacobian direction; 8-32 GH nodes along it plus a cheap orthogonal
  correction beats both covariance propagation and the 6.5k-sample MC
  baseline. Lead note 2026-07-16: an analytic-only method must beat
  9.39e-07, i.e. close a 9x gap versus covariance propagation; even if it
  falls short outright, it becomes the analytic core for B2. (Claimed by gpt
  before the lead reprioritization landed; the claim predates and therefore
  supersedes the B4-first ordering for this iteration.)

- [x] **B2** (explore, lead-priority 3) - DONE gpt 2026-07-16T02:21:51Z - Control-variate hybrid.
  Deterministic estimate (best available analytic method — post-B1 core if it
  exists, else covariance propagation) plus a small MC batch correcting its
  bias: `final = analytic + mean(MC_true - MC_analytic_prediction)` on shared
  inputs. Hypothesis: residual variance is much smaller than raw variance, so
  a few hundred samples suffice; unbiased by construction. Composes with B4's
  QMC on the residual term.

- [x] **B3** (exploit, lead-priority 4) - DONE claude 2026-07-16T03:32:00Z - Exact ReLU cross-moments in
  covariance propagation. Replace the gain-product off-diagonal approximation
  from the B0-era analytic estimator
  (`cov_post[i,j] approximately Phi(alpha_i)Phi(alpha_j)cov_pre[i,j]`) with
  the exact bivariate Gaussian ReLU cross-moment (arccos-kernel form). FLOPs
  are irrelevant at the 0.1 floor; hypothesis: compounding off-diagonal bias
  over 32 layers is a dominant error term. Lead note 2026-07-16: value is
  mainly as a better analytic core for B2, since covariance propagation alone
  trails the MC champion by 9x.
  Result: REJECTED — implemented and validated the exact correction (Price's
  theorem + arccos-substitution quadrature; matched brute-force Monte Carlo
  to ~1e-4 across 13 test cases). Official Mini score (8.4606e-06) is
  statistically indistinguishable from the B0-era gain-product
  approximation's own score (8.3663e-06) it replaces — confirmed via a
  direct in-process diagnostic (not a bug: near-identical outputs, exact
  version marginally more accurate against a 2M-sample MC reference on one
  MLP). Both remain ~9x worse than the MC champion. This refutes the
  compounding-off-diagonal-bias hypothesis: fixing that specific
  approximation exactly does not close the gap, so it is not a dominant
  error term here. See `experiments/log-claude.md` and
  `experiments/results/claude/B3-claude-20260716T032500Z-1598169-summary.json`.
  Useful negative result for B2's choice of analytic core.

- [ ] **B5** (explore) - CLAIMED gpt 2026-07-16T02:51:43Z - Rank-adaptive low-rank covariance propagation.
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

- [ ] **S1** (admin, user action required - not claimable as an experiment) -
  Unblock the submission pipeline. `last_submitted_score` is null and the
  ledger holds two pre-scaffold manual submissions (2026-06-11T05:00:33Z and
  2026-06-11T19:50:10Z) with no submission IDs, so the required "5% better
  than last submitted" gate is undecidable and workers correctly refuse to
  submit. Per AGENTS.md these entries must never be reconciled by timestamp
  matching (their embedded notes suggesting timestamp matching contradict the
  protocol and should be ignored). The user must backfill exact
  submission IDs/scores from the AIcrowd submissions board, or explicitly
  rule that a null `last_submitted_score` permits a first scaffold
  submission. Until then the Full gate can still be run and recorded, but no
  network submission may happen.

- [ ] **B7** (explore) - Depth-localized re-antithetization. B4's layer-wise
  diagnostic shows antithetic-pair (z, -z) correlation, and thus its
  variance-reduction benefit, decaying from -46% MSE at layer 0 to noise
  level by layer ~25 of 32, well before the scored final layer. Hypothesis:
  periodically reflecting the running activations at intermediate layers
  (or reflecting only along B1's active-subspace direction) sustains the
  antithetic benefit deeper into the depth-32 collapse at the same FLOP
  cost, instead of letting it decay from a single input-level pairing.

## Done

(nothing yet)
