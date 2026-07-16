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
