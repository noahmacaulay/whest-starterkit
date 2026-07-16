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

## 2026-07-16T03:32:00Z - B3-claude-20260716T032500Z: Exact bivariate ReLU cross-moment
- Hypothesis: replacing the B0-era gain-product off-diagonal covariance
  approximation `cov_post[i,j] ~= Phi(alpha_i)*Phi(alpha_j)*cov_pre[i,j]`
  with the exact bivariate ReLU cross-moment closes a meaningful fraction of
  the ~9x gap between covariance propagation and the MC champion (per the
  B1 lead note's compounding-off-diagonal-bias theory).
- Base champion: estimator.py @ 1598169 (B0-gpt-20260716T002459Z source
  result 58900f1); candidate_claude.py @ c149f43, claimed from 3926f2e.
- Derivation: for jointly Gaussian (X,Y) with correlation rho, Price's
  theorem gives d/drho E[X+ Y+] = sigma_x*sigma_y*P(X>0,Y>0). Integrating
  from rho=0 (closed form via independence) and swapping the order of the
  resulting double integral reduces the correction to a single integral of
  the plain bivariate normal density in rho. Substituting t=cos(theta)
  exactly cancels that density's 1/sqrt(1-t^2) factor (the "arccos kernel"
  form named in the backlog item), leaving a smooth, bounded integrand with
  no singularity at rho -> +-1 -- evaluated with fixed 16-point
  Gauss-Legendre quadrature, in float64 (matching the existing float64
  upcast already used for `gain`), vectorized over the full width x width
  pair matrix.
- Validation before wiring in: (1) the closed-form correction integral
  matched brute-force 20M-sample Monte Carlo cross moments to ~1e-4 across
  13 (mu_x,mu_y,sigma_x,sigma_y,rho) cases including |rho| up to 0.999999
  and mixed signs; (2) a layer-by-layer PSD/correlation diagnostic on both
  a synthetic MLP and a real dataset MLP showed no instability; (3) the
  official Mini-split aggregate initially looked like a 788% regression
  (see `paired.mean_delta` below), which I did not take at face value --
  called `candidate_claude.py`'s actual `Estimator.predict()` in-process on
  real dataset MLP #0 and compared directly against
  `examples/03_covariance_propagation.py`'s gain-product estimator on the
  same MLP: final-layer outputs differ by an L2 norm of only 0.0152 (vs
  |mu|~12.4), and against an independent 2,000,000-sample MC reference the
  exact-cross-moment version was marginally *more* accurate (MSE
  3.524e-05 vs 4.133e-05 for the gain-product version). This confirms the
  formula/implementation are correct, not buggy.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5+np2.2.6,
  uv.lock@2c84f3b0131859397fbfecea333503af142fd50f.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1
  (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433),
  split=mini (100 MLPs), budget=272000000000, runner=subprocess. Champion
  report reused byte-identical from the B4 experiment (same
  estimator.py@1598169, same deterministic dataset/seeds); candidate report
  freshly executed. Exact commands and reports are in
  results/claude/B3-claude-20260716T032500Z-1598169-summary.json.
- Result: candidate adjusted score=8.460563353429e-06; champion (MC) adjusted
  score=9.524083760984e-07; relative_change=+788.333573% vs. champion.
  Reference: the B0-era gain-product covariance-propagation baseline's own
  official Mini score was 8.366271929845e-06 -- i.e. the exact candidate
  (8.4606e-06) is statistically indistinguishable from (~1% worse than) the
  approximation it replaces. paired_mean_delta=7.508154977331e-06 (vs.
  champion); paired_95pct_CI=[6.269998308988e-06, 8.746311645673e-06];
  worst_per_MLP_regression=2.951486299528e-05 (99/100 regressed vs.
  champion). All failure/budget/time/error flags=0; candidate mean
  effective compute 2.876e10, still well under the 2.72e10 floor.
- Verdict: REJECTED. Not a bug (see validation above) -- a real result that
  refutes the hypothesis. Compounding off-diagonal bias is not a dominant
  error term for this covariance-propagation method at depth 32: fixing it
  exactly leaves the aggregate score essentially unchanged. Remaining error
  is more likely from higher-order (beyond-pairwise) non-Gaussianity
  introduced by ReLU, or breakdown of the mean-field/Gaussian assumption
  itself, neither of which a pairwise cross-moment correction can fix.
- Full/submission gate: NOT_RUN; the Mini paired gate failed.
- New ideas queued: none directly, but this is a relevant negative result
  for B2 (lead note: B3 was intended mainly as a better analytic core for
  B2) -- an exact pairwise-correlation fix is not where B2's analytic core
  should invest further; B5/B6 (rank-adaptive and mean-field-asymptotic
  approaches, which target different error sources) remain the more
  promising analytic directions.

## 2026-07-16T04:20:00Z - B7-claude: Depth-localized re-antithetization (design-invalidated)
- Hypothesis (as queued): periodically reflecting the running activations at
  intermediate layers sustains B4's antithetic variance-reduction benefit
  deeper into the depth-32 collapse, since the layer-wise diagnostic in B4
  showed pair correlation decaying to noise by layer ~25.
- Base: claimed from bcaba93, base champion estimator.py @ 1598169 (no
  candidate file needed -- see below).
- What happened: before implementing, worked through what "reflecting the
  running activation" at an intermediate layer actually means distributionally,
  since B4's valid input-level antithetic trick relies on a specific fact --
  Z and -Z are equal in distribution for Z~N(0,I) -- that does not carry
  through a ReLU. Post-ReLU activations are supported on the non-negative
  orthant, so h_l and -h_l are *not* equal in distribution once l>=1; there
  is also no fresh randomness re-entering at any layer (the whole depth-32
  trajectory is a deterministic pushforward of the single random input), so
  there is no valid resampling opportunity to exploit mid-network at all.
  Negating a running activation partway through is therefore not "another
  valid antithetic draw" -- it silently changes what quantity is being
  estimated.
- Empirical confirmation (cheap synthetic check, width=64 depth=4,
  200,000 pairs, weights He-initialized as in `local_engine.build_mlp`,
  ground truth from a 4,000,000-sample plain MC estimate): B4's valid
  input-only antithetic pairing gave MSE=5.006e-07 against ground truth, vs.
  MSE=5.799e-02 (about 10^5 times worse) for the literal B7 construction
  that negates the running activation after layer 1 -- with a clear
  systematic bias of -0.0623 (mean(meanB)=0.5069 vs. mean(true_mean)=0.5692),
  not just added noise. Confirms this is a design flaw, not an
  implementation detail to debug.
- Verdict: REJECTED at the design stage -- the method is a biased estimator
  and was never run through `whest validate`/`whest run` against the real
  Mini split, since doing so would only have (mis)measured a biased
  estimator rather than tested the intended hypothesis. No candidate_claude.py
  was committed for this item (nothing to keep: `candidate_claude.py`
  remains at its B3 state on disk/HEAD). This is a legitimate timeboxed
  research outcome per AGENTS.md ("a logged rejected experiment is a
  completed product") -- catching an invalid method by reasoning plus a
  cheap synthetic check, before spending a full paired Mini-split run on it,
  is the correct amount of effort for a flaw this decisive.
- Full/submission gate: NOT_RUN.
- New ideas queued: B8 - any depth-localized variance reduction must stay
  within the *input* distribution's actual symmetries (or introduce new,
  independent randomness), not negate downstream nonlinear state. One
  concretely valid direction: at layer 1 only (where z and -z are both
  legitimate draws), h+ = relu(Wz) and h- = relu(-Wz) satisfy the *exact*,
  free identities h+ - h- = Wz and h+ + h- = |Wz| elementwise. A control
  variate or Rao-Blackwellized combination built from this exact layer-1
  relationship (rather than trying to re-derive an analogous identity at
  deeper layers, where none exists) could recover some of B4's lost
  variance reduction without bias and without extra FLOPs. Needs a careful
  from-scratch derivation to confirm unbiasedness before implementing --
  do not skip that step, per this iteration's lesson.

## 2026-07-16T05:35:00Z - B8-claude: Exact layer-1 control variate (feasibility-rejected)
- Hypothesis (as queued): a control variate or Rao-Blackwellized combination
  built from the exact, free layer-1 identities h+ - h- = Wz and
  h+ + h- = |Wz| (available at zero extra FLOP cost from the antithetic
  pair already computed) recovers some of B4's lost variance reduction at
  the scored final layer, without bias.
- Base: claimed from aaa87c8; base champion estimator.py @ 1598169.
- What happened: before implementing, worked through whether this control
  can plausibly help at all. Two considerations: (1) B2 already tried a
  *richer*, more expensive analytic control (diagonal-Gaussian soft-gate
  propagation through all 32 layers) and it was REJECTED -- its own
  approximation error dominated any variance it removed. A layer-1-only
  control has access to strictly less information about the network's
  depth-32 behavior than B2's control did, so it is a priori unlikely to
  do better on the correlation-with-truth axis, even though it is cheaper
  (near-zero marginal FLOPs vs. B2's ~13% overhead). (2) There is no
  leftover randomness to condition on after layer 1 -- the entire depth-32
  trajectory is a deterministic pushforward of the single input draw z, so
  this is not a classic Rao-Blackwellization setting; it reduces to an
  ordinary (optimal-coefficient) control variate, whose value depends
  entirely on how correlated the free layer-1 quantity is with the final
  *scored* layer -- exactly the quantity B4/B7's diagnostics already showed
  decaying to noise well before layer 32.
- Empirical confirmation (cheap synthetic check, width=256 depth=32,
  matching the real problem shape, 20,000 antithetic pairs, He-initialized
  weights as in `local_engine.build_mlp`): fit the per-final-neuron
  optimal-coefficient regression of the antithetic pair-mean on the free
  layer-1 control (`Wz`, i.e. `h+_1 - h-_1`), ridge-regularized, using a
  train/test split to get an honest (not in-sample-overfit) estimate of
  variance reduction. Held-out result: mean variance *increased* by 2.6%
  (0.026686 vs. 0.025998), and 0/256 final-layer neurons showed any real
  reduction -- i.e. the free layer-1 signal carries no exploitable
  correlation with the depth-32 output; what a nonzero in-sample
  correlation would show is pure regression/estimation noise from fitting
  256 coefficients on finite data, not a real effect.
- Verdict: REJECTED at the feasibility-check stage, before any candidate
  was written or harness run. This is a completed, informative product
  (AGENTS.md: "a logged rejected experiment is a completed product") --
  the ~2 minutes of synthetic validation here is strictly cheaper than
  writing, validating, and running a doomed candidate through the full
  Mini-split paired gate.
- Full/submission gate: NOT_RUN.
- New ideas queued: none directly. Taken together, B4/B7 (antithetic decay)
  and B8 (zero correlation of any layer-1-derived quantity with the final
  layer) now give three independent, convergent pieces of evidence that
  depth-32 mean-field collapse destroys *any* exploitable structure tied to
  early-layer values or input-level coordinate symmetries well before the
  scored layer. Cheap, input-local tricks (antithetic pairs, layer-1
  control variates) are very likely exhausted as a research direction for
  this problem; MC-side gains would have to come from something that
  persists through depth by construction (e.g. genuinely low-discrepancy
  structure across the *whole* forward pass, not a single-layer trick --
  the still-untested Sobol/QMC half of B4's original hypothesis) rather
  than anything anchored to layer 1 specifically.

## 2026-07-16T06:15:00Z - B10-claude-20260716T060000Z: Batched active-subspace GH quadrature
- Hypothesis: gpt's B1 experiment (active-subspace Gauss-Hermite quadrature)
  measured a genuine final-layer MSE improvement over the champion
  (7.995e-06 vs 8.505e-06, ~6%) but was REJECTED because its
  mean_effective_compute was 28% higher than the champion's, even though
  its raw flops_used was within 0.4% of the champion's. Root-caused this
  before implementing: B1's candidate made 1,360 separate small matmul
  calls (16 GH nodes x positive/negative x 32 layers, plus 256
  power-iteration and 32 diagonal-soft-gate calls) vs. the champion's 32
  single full-batch matmul calls; the effective_compute/flops_used ratio
  was 1.464 for B1's candidate vs. 1.186 for the champion -- overhead from
  call fragmentation, not real arithmetic. Hypothesis: reimplementing the
  *same* statistical estimator with one combined (~6,516, width) batch
  forwarded through each layer via a single matmul call recovers most of
  that overhead while preserving the accuracy gain.
- Base champion: estimator.py @ 1598169 (B0-gpt-20260716T002459Z source
  result 58900f1); candidate_claude.py @ 6275a01, claimed from 1daf685
  (independent reimplementation -- did not touch candidate_gpt.py).
- Change: same soft-gate diagonal Jacobian, 4-iteration power method for
  the dominant direction, and 16-node probabilists' Gauss-Hermite
  quadrature with antithetic conditional draws as B1, but restructured:
  builds one (total_pairs, width) noise batch and one (2*total_pairs,
  width) positive/negative sample batch up front (vectorized `repeat`
  instead of a per-node Python loop), assigns each row a fixed weight
  `weight_i/(2*pairs_i)`, and forwards the whole batch through each layer
  with a single matmul + weighted-sum, matching the champion's per-layer
  call structure.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5+np2.2.6,
  uv.lock@2c84f3b0131859397fbfecea333503af142fd50f.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1
  (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433),
  split=mini (100 MLPs), budget=272000000000, runner=subprocess. Champion
  report reused byte-identical from the B4 experiment; candidate report
  freshly executed. Exact commands/reports:
  results/claude/B10-claude-20260716T060000Z-1598169-summary.json.
- Result: candidate adjusted score=1.034172374622e-06; champion=
  9.524083760984e-07; relative_change=+8.584973% (vs. B1's +20.737562%).
  candidate final_layer_mse=7.995433086876e-06 -- matches B1's
  7.995440876130e-06 to 6 significant figures, confirming this is the
  mathematically identical estimator. paired_mean_delta=8.176399852398e-08
  (vs. B1's 1.966045905419e-07, 58% smaller); paired_95pct_CI=
  [-2.268208497568e-07, 3.903488468048e-07] (narrower and shifted toward
  zero vs. B1's [-1.079e-07, 5.011e-07], but still not entirely below
  zero). worst_per_MLP_regression=3.675427219380e-06 (60/100 regressed,
  vs. B1's 64/100). All failure/budget/time/error flags=0.
- Overhead diagnostic: matmul calls dropped from B1's 1,360 to 353 (a 74%
  reduction); effective_compute/flops_used ratio dropped from 1.464 to
  1.307 (champion's ratio is 1.186) -- roughly half of B1's excess overhead
  recovered. The remaining ~321 extra calls (vs. champion's 32) come from
  two still-unbatched phases: the 256 power-iteration matrix-vector
  products (4 iterations x 32 layers x 2 traversals) and the 32 diagonal
  soft-gate propagation matmuls. Both are currently per-layer vector ops,
  not batched.
- Verdict: REJECTED -- the paired 95% CI is not entirely below zero. But
  this is real, quantified progress on a previously-rejected method: the
  accuracy gain is reproducible and the compute-overhead penalty that sank
  B1 is now roughly half-closed purely by an implementation change (no
  algorithm change). This is a much stronger candidate for a follow-up
  iteration than a fresh idea would be.
- Full/submission gate: NOT_RUN; the Mini paired gate failed.
- New ideas queued: B11 - finish batching B10's estimator: fold the 256
  power-iteration matrix-vector products and 32 diagonal-soft-gate matmuls
  into far fewer, larger calls (e.g. stack the per-layer power-iteration
  vector into a small batch, or algebraically combine steps) to close the
  remaining gap from ratio 1.307 to the champion's 1.186. If the full
  overhead gap closes while the ~6% MSE improvement is preserved (as this
  run demonstrates it survives batching), the paired mean delta should
  cross entirely below zero and this becomes a promotable champion.

## 2026-07-16T07:10:00Z - B12-claude-20260716T065000Z: Two-direction active-subspace quadrature
- Hypothesis: AGENTS.md notes depth-32 covariance is "often rank-1
  dominated", not purely rank-1. B1/B10 use only the single top
  power-iteration direction; a second, deflated power-iteration direction,
  exploited via a 4-way antithetic split of the orthogonal-complement noise
  (independently sign-flipping the d2 component and the residual, instead
  of a second quadrature that would need new unverified GH constants under
  time pressure) might capture residual signal the first direction misses.
- Context: gpt claimed and finished B11 in parallel this iteration
  (materializing the full soft-gate Jacobian to cut power-iteration call
  count 256->40) -- result: effective_compute only dropped from B10's
  3.5156e10 to 3.4706e10 (matrix-matrix products raised raw FLOPs enough
  to offset most of the call-count win), CI still not entirely below zero,
  REJECTED. That result made B12 a genuinely complementary (not
  duplicate) lever: a statistical change rather than another overhead
  squeeze on the same 1-D estimator.
- Base champion: estimator.py @ 1598169 (B0-gpt-20260716T002459Z source
  result 58900f1); candidate_claude.py @ be2f794, claimed from 64b71a8.
  Also checked B9's raw per-MLP data before claiming (no claim needed, B9
  already DONE): even its 73/100 non-crashed MLPs scored ~27x worse MSE
  than champion on average (0/73 better) -- confirms full-ambient-space
  Sobol/QMC is a genuine dead end here, not just B9's float32-before-ppf
  crash bug, so a bug-fixed Sobol retry was not queued.
- Pre-implementation validation: synthetic width=32/depth=6 network,
  budget-matched 4-way (300k independent base draws -> 1.2M total rows)
  vs. B10-style 2-way (600k independent base draws -> 1.2M total rows)
  against a 2,000,000-sample conditional-MC reference, using a RANDOM
  (not power-iteration) d2 to isolate correctness. Result: unbiased
  (mean(m_all-ref)~1e-4, within MC noise) and modestly better than the
  2-way baseline (MSE 3.30e-07 vs 3.43e-07, ~3.7% better) in that toy
  setting -- correctly validated unbiasedness, but in hindsight was not a
  reliable predictor of whether a genuine *second* direction exists at the
  real problem's width=256/depth=32 scale.
- Change: same soft-gate diagonal Jacobian and 4-iteration power method
  for d1 as B1/B10; added a second 4-iteration deflated power iteration
  (projecting out d1 at each step) for d2. Halved the base random-draw
  count and built 4 antithetic variants per draw -- (+d2,+resid),
  (-d2,+resid), (+d2,-resid), (-d2,-resid) -- concatenated into one
  (~6,516, width) batch, single matmul per layer (same batching
  discipline as B10).
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5+np2.2.6,
  uv.lock@2c84f3b0131859397fbfecea333503af142fd50f.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1
  (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433),
  split=mini (100 MLPs), budget=272000000000, runner=subprocess. Champion
  report reused byte-identical from the B4 experiment; candidate report
  freshly executed. Exact commands/reports:
  results/claude/B12-claude-20260716T065000Z-1598169-summary.json.
- Result: candidate adjusted score=1.551411402337e-06; champion=
  9.524083760984e-07; relative_change=+62.893507%. candidate
  final_layer_mse=1.171051423910e-05 -- 46% WORSE than B10's
  7.995433086876e-06, and worse than the champion's 8.505e-06 too.
  paired_mean_delta=5.990030262390e-07; paired_95pct_CI=
  [1.516057416245e-07, 1.046400310854e-06] (wholly positive, i.e.
  significantly worse, not just inconclusive). worst_per_MLP_regression=
  9.188928047317e-06 (77/100 regressed). Overhead also regressed vs. B10:
  matmul calls 353->610 (running power iteration twice roughly doubles
  that phase), effective_compute/flops_used ratio 1.307->1.368. All
  failure/budget/time/error flags=0.
- Verdict: REJECTED, decisively (CI wholly positive, not straddling zero
  like B10/B11). Regressed on both accuracy and overhead versus B10.
  Diagnosis: halving the independent base random-draw count to afford the
  4-way antithetic split traded away more direct variance reduction than
  the second direction recovered -- most likely because the covariance is
  rank-1 dominated enough that the deflated "second direction" is closer
  to arbitrary residual noise than a genuine persistent signal axis. This
  is the fourth distinct technique (after B4 antithetic, B7
  re-antithetization, B8 layer-1 control variate) confirming that only the
  single top active-subspace direction (B1/B10's validated core) carries
  usable structure at depth 32; extending beyond it does not pay off.
- Full/submission gate: NOT_RUN; the Mini paired gate failed.
- New ideas queued: none. Multi-direction extensions of B1/B10 are now a
  well-evidenced dead end (this result plus the general depth-32 collapse
  pattern from B4/B7/B8). The remaining promising lever for the
  B1/B10/B11 lineage is purely overhead reduction on the existing 1-D
  estimator (B11's specific approach -- materializing the full Jacobian --
  didn't close it; a cheaper power-iteration reduction, e.g. fewer than 4
  iterations given the strong rank-1 dominance this very experiment's
  failure mode reconfirms, remains untried).

## 2026-07-16T07:45:00Z - B13-claude-20260716T073500Z: Fewer power iterations
- Hypothesis: B1/B10/B11 all used 4 power iterations for the dominant
  active-subspace direction, unchanged from the original B1 experiment.
  B12's failure mode (a deflated second direction carried ~no exploitable
  signal beyond noise) reconfirmed the covariance is strongly rank-1
  dominated -- power iteration should converge in far fewer than 4 steps.
  Reducing the count should cut power-iteration call count at zero extra
  raw-FLOP cost per call (same O(width^2) matvecs, just fewer of them),
  unlike B11's full-Jacobian materialization which traded call count for
  bigger, costlier calls and barely moved effective_compute.
- Pre-implementation validation: loaded 5 real dataset MLPs directly (no
  local synthetic stand-in this time -- direction convergence is exactly
  the kind of thing that could differ between a toy network and the real
  problem), computed the power-iteration direction at 1-6 iterations, and
  measured cosine similarity to the 6-iteration reference. Result: after 2
  iterations, similarity was >=0.998567 for all 5 MLPs (worst case MLP
  index 5). After 1 iteration it dropped to 0.901160 in the worst case --
  materially less converged, so chose 2 iterations as the safe reduction
  rather than pushing to 1.
- Base champion: estimator.py @ 1598169 (B0-gpt-20260716T002459Z source
  result 58900f1); candidate_claude.py @ 410ce40, claimed from 55d60ec.
  Otherwise identical to B10's estimator (same batched single-matmul-per
  -layer structure) -- the only change is `_POWER_ITERATIONS = 2` instead
  of the hardcoded 4 loop count.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5+np2.2.6,
  uv.lock@2c84f3b0131859397fbfecea333503af142fd50f.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1
  (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433),
  split=mini (100 MLPs), budget=272000000000, runner=subprocess. Champion
  report reused byte-identical from the B4 experiment; candidate report
  freshly executed. Exact commands/reports:
  results/claude/B13-claude-20260716T073500Z-1598169-summary.json.
- Result: candidate adjusted score=1.016318942792e-06; champion=
  9.524083760984e-07; relative_change=+6.710416% (vs. B10's +8.584973%).
  candidate final_layer_mse=7.931290535907e-06 -- marginally BETTER than
  B10's 7.995433086876e-06, confirming the 2-iteration direction loses no
  accuracy for this dataset (matches the convergence check). matmul calls
  353->225 (halving the power-iteration phase cut total calls by 36%,
  256->128 of that phase). effective_compute/flops_used ratio 1.278->1.266
  (aggregate mean) -- a real but modest reduction, smaller than the
  call-count cut alone would suggest, since the 32 still-unbatched
  diagonal soft-gate matmuls are untouched and now a larger share of the
  remaining gap to the champion's ~1.19 ratio. paired_mean_delta=
  6.391056669405e-08 -- the smallest in the whole B1/B10/B11 lineage
  (B1=1.966e-07, B10=8.176e-08, B11=9.179e-08). paired_95pct_CI=
  [-2.444267097992e-07, 3.722478431873e-07], still straddling zero.
  worst_per_MLP_regression=3.615554736344e-06 (59/100 regressed, fewer
  than B10's 60/100). All failure/budget/time/error flags=0.
- Verdict: REJECTED -- CI not entirely below zero. Real incremental
  progress, though: closest paired_mean_delta to zero yet in this
  lineage, with accuracy confirmed intact (not traded away for the
  overhead cut) and no costly materialization tradeoff like B11's.
- Full/submission gate: NOT_RUN; the Mini paired gate failed.
- New ideas queued: B14 - batch the remaining 32 diagonal soft-gate
  matmuls (`pre_variance = (w*w).T @ variance`, one per layer, currently
  unbatched like the old power-iteration calls were). These are now a
  proportionally larger share of the B1/B10/B11/B13 lineage's remaining
  overhead than before. Unlike the power iteration, this phase doesn't
  need multiple sequential rounds -- it is already just one pass per
  layer -- so "batching" here would mean finding a way to fold it into
  the same single matmul as the main quadrature sampling pass, or
  otherwise reducing its per-layer call footprint, without changing the
  diagonal-Gaussian-moment math at all.

## 2026-07-16T08:20:00Z - B15-claude-20260716T081000Z: Halved main sample budget
- Hypothesis: B13's aggregate flops_used (27.49e9) was already close to
  the champion's (27.35e9), while effective_compute (34.80e9) was ~7.3e9
  higher -- consistent with a largely fixed per-call overhead from the
  128 power-iteration + 32 diagonal calls, independent of main-sampling
  row count. The 16-node Gauss-Hermite quadrature gives zero sampling
  variance along the dominant direction, so this estimator should be more
  sample-efficient per FLOP than plain MC. Distinct from gpt's claimed
  B14 (batching the fixed-overhead calls directly): this targets the
  dominant raw-FLOP term instead, by halving the main pair-count scale
  factor (3250->1625, ~6,500->~3,250 total forward rows).
- Base champion: estimator.py @ 1598169 (B0-gpt-20260716T002459Z source
  result 58900f1); candidate_claude.py @ 4780908, claimed from 75494d0.
  Otherwise identical to B13's estimator -- only `_GH_PAIRS` base scale
  changed from 3,250 to 1,625.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5+np2.2.6,
  uv.lock@2c84f3b0131859397fbfecea333503af142fd50f.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1
  (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433),
  split=mini (100 MLPs), budget=272000000000, runner=subprocess. Ran
  champion.py *fresh* this time (not reused from an earlier experiment),
  back-to-back with the candidate, since effective_compute carries real
  wall-clock measurement noise and this experiment hinges on a delicate
  compute-vs-accuracy tradeoff near the promotion threshold. Exact
  commands/reports:
  results/claude/B15-claude-20260716T081000Z-1598169-summary.json.
- Result: candidate adjusted score=1.337600066449e-06; champion=
  9.428206161020e-07; relative_change=+41.872170%. candidate
  final_layer_mse=1.337600066449e-05 -- 57% WORSE than champion's
  8.504929468245e-06 (and worse than B13's 7.931e-06). candidate
  mean_effective_compute=1.831135614561e10, multiplier hit exactly the
  0.1 floor (down from champion's 0.110666) -- confirming the raw-FLOP
  reduction did cut effective_compute substantially, but MSE rose much
  more steeply than expected from halving the orthogonal-complement
  sample count. paired_mean_delta=3.947794503474e-07 (worse);
  paired_95pct_CI=[-1.235831022336e-08, 8.019172109181e-07] (essentially
  entirely positive, i.e. this run is significantly worse, not just
  inconclusive). worst_per_MLP_regression=6.906934828498e-06 (75/100
  regressed). All failure/budget/time/error flags=0.
- Verdict: REJECTED -- overshot the reduction. The multiplier only
  dropped ~10% (0.1107->0.1, floor-clamped) while MSE rose 57%, so the
  net score is 42% worse than champion. Worse: the candidate's
  effective_compute (1.831e10) landed *below* the 2.72e10 floor, meaning
  8.89e9 of "free" compute headroom was left completely unused -- MSE was
  sacrificed for zero further multiplier benefit past the floor boundary.
- Full/submission gate: NOT_RUN; the Mini paired gate failed.
- New ideas queued: B16 - retry with a precisely calibrated pair-count
  scale instead of a blind halving. Using this run's data point
  (pair_scale=1625, mean_effective_compute=1.8311e10) and B13's
  (pair_scale=3250, mean_effective_compute=3.4803e10), a linear fit
  (slope ~1.015e7 per unit pair_scale) solving for effective_compute=
  2.72e10 (the floor boundary) gives pair_scale ~2500. That should land
  right at the floor (multiplier ~0.1, same as this run) but with ~54%
  more orthogonal-complement samples than B15, recovering most of the
  MSE this run gave up for nothing -- strictly better than both B13
  (overhead above the floor, unused margin) and B15 (accuracy sacrificed
  below the floor, unused margin) if the linear model holds.

## 2026-07-16T08:55:00Z - B16-claude-20260716T084500Z: Calibrated pair scale + elementwise diagonal
- Hypothesis: combine two independently-verified, complementary fixes:
  (1) pair-count scale ~2,500 (linear-fit calibration from B13/B15 to hit
  the 2.72e10 floor boundary exactly, avoiding B15's overshoot), and (2)
  gpt's B14 fix, independently reimplemented: diagonal soft-gate variance
  via elementwise multiply+sum instead of a matmul call. These target
  different overhead sources (raw main-sample FLOPs vs. diagonal-phase
  call fragmentation), so stacking them should combine their reductions.
- Base champion: estimator.py @ 1598169 (B0-gpt-20260716T002459Z source
  result 58900f1); candidate_claude.py @ 3eda8eb, claimed from cfbd4bd.
  gpt's B14 (finished in parallel this session) also got REJECTED on its
  own (paired_mean_delta=5.477e-08, the smallest single-lever result at
  the time) but confirmed the elementwise fix preserves B13's MSE exactly
  and reduces effective_compute (3.4803e10->3.3729e10) without changing
  the estimator's statistics -- safe to combine with the N calibration.
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5+np2.2.6,
  uv.lock@2c84f3b0131859397fbfecea333503af142fd50f.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1
  (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433),
  split=mini (100 MLPs), budget=272000000000, runner=subprocess. Champion
  run fresh again (not reused), back-to-back with the candidate. Exact
  commands/reports:
  results/claude/B16-claude-20260716T084500Z-1598169-summary.json.
- Result: candidate adjusted score=9.968414113022e-07; champion=
  9.400532341054e-07; relative_change=+6.040953%. Calibration landed
  almost exactly on target: candidate mean_effective_compute=
  2.717881136265e10, within 0.07% of the 2.72e10 floor, multiplier=
  0.100484 (just above the floor). candidate final_layer_mse=
  9.936290850874e-06 (worse than champion's 8.505e-06 and B13's
  7.931e-06 -- the N cut does cost real accuracy). matmul calls 225->193
  (exactly the 32 diagonal calls removed, confirming the elementwise fix
  stacked cleanly). paired_mean_delta=5.678817719684e-08;
  paired_95pct_CI=[-2.394494641580e-07, 3.530258185517e-07], still
  straddling zero.
- KEY FINDING: B16 (N=2500 + elementwise diagonal) essentially TIES B14
  (N=3250, full budget + elementwise diagonal, no N reduction at all) on
  paired_mean_delta (5.679e-08 vs 5.477e-08) -- B14 is marginally
  *better* despite using MORE samples and MORE raw compute. The
  N-reduction lever contributes ~nothing once the diagonal-matmul
  overhead is already fixed. Explanation: the lead's original insight for
  plain MC -- adjusted score is approximately N-invariant above the
  compute floor, since MSE~1/N cancels multiplier~N -- applies to ANY
  MC-based estimator whose dominant cost is the sample-dependent forward
  pass, not specifically plain MC. The 16-node quadrature makes ONE
  dimension's variance exactly zero, which lowers the *invariant score
  level itself* (that's the ~6% MSE edge over plain MC B10/B13/B14 all
  show), but it does not break the invariance property for the other 255
  dimensions' sampling variance. B15's failure (below the floor) and
  B16's near-tie with B14 (at/above it) are two sides of the same fact:
  this lineage's only real remaining lever is the FIXED, N-independent
  call overhead (currently ~128 power-iteration calls + ~65 main/misc),
  not the main sample count.
- Verdict: REJECTED -- CI not entirely below zero, and no better than
  B14 alone. Still useful: confirms the calibration model was accurate
  (compute landed almost exactly on the floor target) and definitively
  rules out sample-count tuning as a further lever for this architecture.
- Full/submission gate: NOT_RUN; the Mini paired gate failed.
- New ideas queued: B17 - since N-tuning is now a confirmed dead end for
  this estimator, the only remaining lever is cutting the ~128
  power-iteration calls further (already reduced from 256 in B13). Given
  B12's and this experiment's reconfirmation of strong rank-1 dominance,
  revisit whether even fewer iterations (or a cheaper convergence check,
  e.g. stopping early once consecutive directions' cosine similarity
  exceeds a threshold) holds up on more MLPs than the 5 checked for B13.
  If power iteration can be cut further without sacrificing direction
  quality, combine with B14's elementwise diagonal fix (already validated
  safe to stack) at the FULL N=3250 budget (not reduced, per this
  experiment's finding) for the best remaining shot at closing the gap.

## 2026-07-16T09:20:00Z - B17-claude: Power-iteration convergence, full-dataset recheck (feasibility-rejected)
- Hypothesis (as queued): since B16 ruled out sample-count tuning, the
  only remaining lever is cutting the ~128 power-iteration calls further
  (B13's 2 iterations, down from B1/B10/B11's 4). B12/B16 reconfirmed
  strong rank-1 dominance, suggesting even fewer iterations (or an
  adaptive early-stopping check) might still converge safely, given B13's
  spot-check found cosine similarity >=0.9986 at 2 iterations across 5
  MLPs.
- What happened: before implementing anything, re-ran the convergence
  check B13 used, but across all 100 Mini-split MLPs instead of 5. The
  result overturned B13's finding rather than extending it. At 2
  iterations: min cosine similarity across the 100 MLPs is 0.443 (not
  0.9986), with 35/100 MLPs below 0.999 similarity to a 6-iteration
  reference. At 1 iteration: min similarity is 0.137 (essentially
  uncorrelated with the true direction for the worst MLP), with 68/100
  below 0.99. B13's 5-MLP sample (indices 0,1,2,5,10) was not
  representative -- it happened to avoid the ~35 MLPs where 2-iteration
  convergence is genuinely poor (e.g. MLP indices 34, 46, 54, 81, 84 are
  the worst at 1 iteration; MLP 46 is still only 0.443 similar even at 2
  iterations). For reference, 4 iterations (B1/B10/B11's original choice)
  converges solidly: min=0.906, only 4/100 below 0.999.
- Base: claimed from 3332dc5; no candidate needed (see below).
- Given 1-iteration convergence is this poor for over two-thirds of the
  dataset, did not run a harness experiment to confirm -- the pre
  -implementation check already shows unambiguously that reducing below
  B13's 2 iterations is not defensible, so a costly paired Mini-split run
  would only be confirming a foregone conclusion (same reasoning as B7/B8:
  a decisive cheap check beats spending a full run on a doomed candidate).
- Verdict: REJECTED at the feasibility-check stage -- "cut iterations
  further" is now closed off definitively, not just left untested. This
  is also an important methodological correction to B13/B16, which both
  used 2 power iterations on the strength of the (non-representative)
  5-MLP check: their AGGREGATE final-layer MSE across the official
  100-MLP Mini harness runs was still competitive/good in every actual
  measurement (B13=7.931e-06, B16=9.936e-06 with also-reduced N), so the
  poor per-MLP direction convergence for ~35% of MLPs did not translate
  into an aggregate accuracy problem in practice -- but this was not
  something the 5-MLP proxy check could have told us, and should not be
  trusted again without a full-dataset check. No regression to B13/B16's
  own results is implied; their promotion-relevant numbers stand as
  measured. This closes the "fewer iterations" sub-lever of the
  B1/B10/B11/B13/B14/B16 lineage; 2 iterations (B13's choice) is the
  floor worth keeping, not something to push further, and going back up
  to 3-4 remains an open question but is not urgent given B13's measured
  aggregate results already looked fine at 2.
- Full/submission gate: NOT_RUN.
- New ideas queued: none directly. The B1/B10/B11/B13/B14/B16 lineage's
  levers are now largely exhausted: N-tuning is a dead end (B16),
  iteration count has a hard floor at 2 (this experiment), and the
  diagonal/main-sampling phases are already batched (B10/B14). What
  remains untried is whether the power-iteration phase itself can be
  restructured (not just shortened) -- e.g. a genuinely batched multi
  -vector iteration (power method on a small block instead of one
  vector, amortizing the per-call overhead across several starting
  vectors at once) -- but that is a real engineering undertaking, not a
  quick hyperparameter tweak, and would need its own careful scoping.

## 2026-07-16T09:45:00Z - B18-claude: Seeded random power-iteration start (inconclusive, rejected)
- Hypothesis: B17's full-dataset recheck found 2-iteration convergence
  poor for ~35/100 Mini-split MLPs. Before attempting a real engineering
  restructure (block power iteration), tested a much cheaper idea: is
  this a starting-vector artifact rather than a fundamental convergence
  -rate limit? The fixed, deterministic `ones(width)` start could have
  systematically poor overlap with the true dominant direction for
  certain He-initialized weight structures; a per-MLP seeded random start
  (`fnp.random.default_rng(mlp.seed).standard_normal(width)`, consistent
  with the seeding contract elsewhere) should have generically
  non-degenerate overlap on average.
- Base: claimed from 6f3b7d7; no candidate needed (see below).
- Method: recomputed the full-100-MLP convergence check three ways --
  the current `ones(width)` start, a per-MLP seeded random start, and a
  third deterministic alternating-sign start ([1,-1,1,-1,...]) added as
  a control once the random-start result looked ambiguous.
- Result: seeded-random start substantially IMPROVED convergence for
  most of the previously-poor MLPs (e.g. MLP 28: 0.891->1.000, MLP 34:
  0.905->0.9999, MLP 46: 0.443->0.908, MLP 54: 0.808->0.995, MLP 81:
  0.835->0.994) -- but it also *introduced* a new bad case that wasn't
  there before: MLP 57 went from 0.996 (excellent with ones-start) to
  0.275 (worse than the original global minimum). Aggregate: mean
  improved marginally (0.979226->0.981545), min got WORSE (0.443->0.275),
  n<0.999 improved only modestly (35->31). The alternating-sign start
  showed the same pattern with yet another different set of poorly
  -converged MLPs (worst: MLP 61 at 0.286, MLP 79, 98, 46, 5...), mean
  0.978166, n<0.999=39 (worse than ones-start).
- Interesting secondary finding: even the 6-iteration "converged"
  reference direction itself differs depending on the starting vector for
  several MLPs (e.g. MLP 46, 57, 76, 98 show ref_agreement of 0.975-0.993
  between ones-start and random-start references, not 1.0) -- for these
  specific MLPs, power iteration has not fully converged to a single
  well-defined dominant direction even after 6 iterations regardless of
  start, consistent with a genuinely small top-1/top-2 eigenvalue gap
  rather than an unlucky initialization.
- Verdict: REJECTED -- inconclusive/no reliable improvement. Three
  different starting vectors (deterministic ones, seeded-random,
  alternating) all show comparable aggregate convergence quality but each
  fails on a *different* subset of MLPs, with no start dominating the
  others. This rules out "pick a better starting vector" as a fix: poor
  convergence for specific MLPs is an intrinsic spectral-gap property of
  that MLP's soft-gate Jacobian (a near-degenerate top-2 eigenvalue
  structure), not an artifact of a poorly-chosen deterministic start.
  Switching to a random or alternative start would trade one set of edge
  cases for another with no net gain, and would also make behavior
  seed-dependent in a way that's harder to reason about for future
  (Full-split or private) MLPs than the current deterministic choice.
- Full/submission gate: NOT_RUN.
- New ideas queued: none. This closes the "cheap fix" branch of the
  power-iteration convergence problem definitively (alongside B17 closing
  the "fewer iterations" branch). The only remaining lever identified so
  far -- a genuinely restructured block/multi-vector power iteration,
  which could plausibly narrow the spectral gap sensitivity by tracking
  more than one direction during the iterative phase itself, not just at
  the end (unlike B12's rejected post-hoc second direction) -- remains a
  real engineering undertaking that no iteration in this lineage has
  attempted yet. Given the diminishing returns across B10/B11/B12/B13/
  B14/B15/B16/B17/B18 (nine iterations narrowing paired_mean_delta from
  B1's 1.966e-07 down to B14's 5.477e-08 without crossing zero), the
  B1/B10 lineage may be approaching a natural stopping point for
  low-risk, incremental engineering fixes; a block-iteration attempt
  would need to be scoped as its own careful, non-trivial experiment
  rather than another quick tweak.

## 2026-07-16T10:30:00Z - B19-claude-20260716T101500Z: Block power iteration
- Hypothesis: B18 found no single starting vector reliably converges well
  for all MLPs. Batching K=4 starting vectors into one (K, width) block
  and applying the soft-gate Jacobian to the whole block costs the *same*
  number of matmul calls per round as a single vector (O(width^2*K), not
  O(width^3) like gpt's B11 full-Jacobian materialization), so running 4
  independent starts through 2 rounds and picking whichever grew the most
  (a cheap proxy for best eigenvalue alignment) should recover most of an
  oracle's accuracy at negligible extra FLOP cost and zero extra calls.
- Pre-implementation validation (all 100 Mini-split MLPs, same discipline
  as B13/B17/B18): block+heuristic min cosine similarity to a 6-round
  reference improved from 0.443 (single ones-start) to 0.823, exactly
  matching an oracle that always picks the true best-converged vector;
  mean 0.979->0.996; MLPs below 0.999 similarity dropped from 35 to 9;
  the heuristic picked the oracle's exact choice in 81/100 cases.
- Base champion: estimator.py @ 1598169 (B0-gpt-20260716T002459Z source
  result 58900f1); candidate_claude.py @ 31e8c1e, claimed from 843fbf4.
  Combined with B14's elementwise diagonal fix and B16's full N=3250
  budget (both already validated).
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5+np2.2.6,
  uv.lock@2c84f3b0131859397fbfecea333503af142fd50f.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1
  (sha256=5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433),
  split=mini (100 MLPs), budget=272000000000, runner=subprocess. Champion
  run fresh again, back-to-back with the candidate. Exact commands/reports:
  results/claude/B19-claude-20260716T101500Z-1598169-summary.json.
- Result (surprising): candidate final_layer_mse=8.360547565189e-06 --
  slightly better than champion's 8.504929468245e-06, but WORSE than
  B13's single-vector 2-iteration result (7.931290535907e-06), despite
  B19's direction being far better converged on the proxy metric. Ran a
  post-hoc bug check before accepting this: re-derived the exact
  block-iteration logic standalone on 5 MLPs and matched the validation
  script exactly (e.g. MLP 46 cos_sim=0.822550 in both); confirmed the
  main quadrature-sampling `rng` is freshly re-seeded independent of the
  power-iteration random starts, so the main noise draw is byte-identical
  to B13's -- no RNG-state confound, no bug found. matmul calls=193 and
  flops_used=27.54e9, both matching B13/B16's range exactly, confirming
  the engineering mechanism (K=4 blocking adds zero calls, negligible
  FLOPs) worked precisely as designed. paired_mean_delta=
  1.324302774825e-07 (worse than B13/B14/B16's 5.5-6.4e-08);
  paired_95pct_CI=[-2.382e-07, 5.031e-07].
- KEY FINDING: much better direction convergence (proxy metric: cosine
  similarity to the power-iteration eigenvector) did NOT translate to
  better final-layer MSE. Possible explanations: (1) the soft-gate
  Jacobian's top eigenvector is itself only an approximation of the truly
  MSE-optimal quadrature axis for the real nonlinear network -- deviating
  from it isn't necessarily worse for the actual target; (2) MLPs with a
  near-degenerate top-2 eigenvalue gap (B18: MLP 46, 57, 76, 98) may have
  two directions of genuinely similar quadrature value, so "better
  convergence to the nominal top eigenvector" doesn't clearly help those
  either way; (3) ordinary between-MLP heterogeneity in one 100-MLP draw
  -- aggregate MSE isn't a smooth function of average direction quality.
- Verdict: REJECTED. Not an implementation failure -- a genuine,
  well-verified negative result about the limits of the convergence
  proxy metric this whole B17/B18/B19 sub-thread has been optimizing.
- Full/submission gate: NOT_RUN; the Mini paired gate failed.
- New ideas queued: none. This closes the power-iteration-convergence
  sub-thread (B17, B18, B19) with a clear lesson: cosine similarity to
  the soft-gate Jacobian's eigenvector is not a reliable target to
  optimize for this estimator's actual final-layer MSE, so further work
  on convergence quality specifically (better starts, block methods,
  more iterations) is unlikely to pay off without first establishing a
  proxy metric that correlates with real MSE (e.g. by measuring MSE
  directly on a battery of directions rather than convergence to a
  reference). Combined with B16 (N-tuning is a dead end) and B11/B14
  (overhead reduction has diminishing returns), the B1/B10/B11/B13/B14/
  B16/B19 active-subspace lineage has now had essentially every
  low-to-medium-risk lever tried (12 sub-experiments total). The
  remaining honest options are: (a) accept B13/B14's ~5.5e-08 mean delta
  as close to this architecture's ceiling and move to a genuinely
  different idea family, or (b) a fundamentally different, higher-risk
  redesign of the quadrature/direction-selection approach itself, not a
  tweak to the existing one.
