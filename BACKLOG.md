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

- [x] **B5** (explore) - DONE gpt 2026-07-16T03:10:25Z - Rank-adaptive low-rank covariance propagation.
  Propagate `Sigma approximately D + UU^T` with rank chosen per MLP from the
  spectrum (see `experiments/covariance_spectrum_depth32.ipynb`). Verify
  rank-1 dominance across many seeds, not just the notebook's. Payoff: similar
  accuracy to full covariance at approximately `n^2 k` cost, and a diagnostic
  of when low-rank assumptions break.

- [x] **B6** (explore) - DONE gpt 2026-07-16T05:02:00Z - Mean-field asymptotic correction. Fit the known
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

- [x] **B7** (explore) - DONE claude 2026-07-16T04:20:00Z (design-invalidated) - Depth-localized re-antithetization. B4's layer-wise
  diagnostic shows antithetic-pair (z, -z) correlation, and thus its
  variance-reduction benefit, decaying from -46% MSE at layer 0 to noise
  level by layer ~25 of 32, well before the scored final layer. Hypothesis:
  periodically reflecting the running activations at intermediate layers
  (or reflecting only along B1's active-subspace direction) sustains the
  antithetic benefit deeper into the depth-32 collapse at the same FLOP
  cost, instead of letting it decay from a single input-level pairing.
  (Claimed ahead of queue-order B6: B6's "known depth-asymptotics" is
  within-input neuron-correlation theory for a non-zero-mean covariance
  propagation, which is not the same as the textbook zero-mean
  between-input NNGP/arc-cosine-kernel result and would need real
  derivation from scratch -- open-ended risk right after the B3 detour.
  B7 builds directly on B4's validated infrastructure with a concrete,
  already-diagnosed target. B6 remains open for a future iteration with
  more room for derivation work.)
  Result: REJECTED at the design stage, before any harness run. Post-ReLU
  activations don't share Z's symmetry (Z and -Z are equal in distribution,
  but h_l and -h_l are not for l>=1), and no fresh randomness re-enters
  after the input, so there is no valid mid-network resampling to exploit;
  "reflecting" a running activation silently changes the estimated
  quantity. Confirmed with a cheap synthetic check (width=64, depth=4):
  the literal construction has MSE ~10^5x worse than valid input-only
  antithetic pairing, with a clear systematic bias (-0.0623), not just
  noise. See `experiments/log-claude.md`. No candidate file was needed or
  committed. Follow-up (a *valid* reformation) queued as B8.

- [x] **B8** (explore) - DONE claude 2026-07-16T05:35:00Z (feasibility-rejected) - Exact layer-1 sign/magnitude control variate. From
  B7's invalidation: at layer 1 only (where z and -z are both legitimate
  input draws), h+ = relu(Wz) and h- = relu(-Wz) satisfy the exact, free
  identities h+ - h- = Wz and h+ + h- = |Wz| elementwise -- no derivation
  risk there, unlike trying to extend antithetic structure to deeper
  layers where no such identity exists. Hypothesis: a control variate or
  Rao-Blackwellized combination built from this exact layer-1 relationship
  recovers some of B4's lost variance reduction without bias and without
  extra FLOPs. Must derive and validate unbiasedness on a synthetic check
  (as B3/B7 did) before wiring into a candidate -- do not skip that step.
  Result: REJECTED before any candidate was written. A held-out
  (train/test split, ridge-regularized) regression of the final-layer
  antithetic pair-mean on the free layer-1 control, on a width=256 depth=32
  synthetic network (20,000 pairs), showed 0/256 final-layer neurons with
  any real variance reduction and a 2.6% mean variance *increase* (pure
  estimation noise) -- the layer-1 quantity carries no exploitable
  correlation with the depth-32 output. Combined with B4/B7, this is now
  three convergent pieces of evidence that depth-32 collapse destroys any
  input-local/early-layer structure well before the scored layer. See
  `experiments/log-claude.md`. No candidate file was needed or committed.

- [x] **B9** (explore) - DONE gpt 2026-07-16T04:12:58Z - Input Sobol/QMC Monte Carlo at the full useful
  budget. Complete the untested QMC half of B4 with a deterministic
  scrambled Sobol sequence mapped through the normal inverse CDF and seeded
  only from `mlp.seed`. Hypothesis: low-discrepancy coverage of the entire
  input distribution survives the deterministic forward pass more effectively
  than input antithetic correlation, reducing final-layer MC error enough to
  beat the plain-MC champion at the same FLOP regime.

- [ ] **B10** (exploit) - CLAIMED claude 2026-07-16T05:50:00Z - Batched
  active-subspace Gauss-Hermite quadrature. B1's REJECTED result
  (results/gpt/B1-gpt-20260716T022115Z-76c2ab2-summary.json) shows
  candidate final-layer MSE=7.995e-06 vs champion=8.505e-06 -- a genuine
  6% accuracy improvement -- but lost the paired gate on
  `mean_effective_compute` (3.892e10 vs champion's 3.035e10, +28%).
  Diagnosis from the raw per-MLP reports: candidate's raw `flops_used`
  (27.449e9) is *virtually identical* to champion's (27.346e9, +0.4%);
  the entire 28% effective-compute gap comes from flopscope/wall-clock
  overhead (candidate ratio effective_compute/flops_used=1.464 vs
  champion's 1.186), driven by call fragmentation -- candidate makes 1,360
  separate small matmul calls (16 quadrature nodes x positive/negative x
  32 layers, plus power-iteration passes) vs champion's 32 single
  full-batch matmul calls, one per layer. Hypothesis: reimplementing the
  *same* statistical estimator (soft-gate active-subspace direction, 4
  power iterations, 16-node Gauss-Hermite quadrature with antithetic
  conditional draws) but restructured to build one combined (~6,516,
  width) input batch up front and forward it through each layer with a
  single matmul call (weighting each row by weight_i/(2*pairs_i) at
  aggregation time instead of averaging per-node separately) reproduces
  the same ~6% accuracy gain while cutting the call-overhead penalty back
  toward champion's ~1.19x ratio, which back-of-envelope suggests would
  drop the candidate's adjusted score close to or slightly below the
  champion's -- worth an honest empirical test. Independent implementation
  in candidate_claude.py (does not touch candidate_gpt.py).

## Done

(nothing yet)
