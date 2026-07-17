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

- [ ] **B50** (infra, exploit) - CLAIMED claude 2026-07-17T11:00:00Z - Full-split
  gate for the B49 QR-free Gram-Schmidt candidate, to make it fully
  submission-ready (step 7 requires the candidate's OWN Full paired gate;
  B46's B47 gate does not transfer -- GS is a different estimator). Run
  the GS candidate (candidate_claude.py @ f54b23b) on the complete
  1000-MLP Full split via B26's chunked driver, pair per-MLP
  final_layer_mse and adjusted_final_layer_score by mlp_name against
  B26's champion Full report (B25/S3 submitted baseline). Expect it to
  match B46's B47 result (-21% MSE, -6.0 sigma adj) given the Mini
  equivalence (ratio 1.0005); confirm and record. On PASS, the GS
  candidate has a COMPLETE Full gate and is one lead/user submission
  decision away from realizing the -17% leaderboard win (and testing the
  qr-hypothesis). Does NOT submit or promote -- infra only.

- [x] **B49** (exploit) - DONE claude 2026-07-17T10:30:00Z - QR-FREE orthogonal
  directions salvage the -21% win: FEASIBLE. Replaced B46's fnp.linalg.qr
  with modified Gram-Schmidt COLUMN-orthonormalization (only gradeable
  ops: matmul/stack/norm/subtract/divide). Full Mini (100): GS
  final_layer_mse 5.0195e-06 vs B46 5.0170e-06 -- RATIO 1.0005,
  statistically identical; the orthogonal benefit is fully preserved with
  NO qr. Compute fine (multiplier 0.1118 vs B46 0.1076, +4%; the feared
  256-iteration Python-loop residual is negligible, ~0.035s); zero
  failures; unbiased (orthonormal 7.5e-13, ~uniform marginals). Candidate
  at candidate_claude.py @ f54b23b. This is the strongest salvage path
  AND a direct test of the qr-hypothesis -- submitting it either grades
  (confirms qr was the S4 cause + realizes ~-17% over the S3 leaderboard)
  or fails (redirects the diagnosis). Did NOT submit autonomously (fresh
  decision not covered by the B47/branch-1 authorization; S4 just
  consumed) -> lead/user call. Detail: log-claude.md B49 entry,
  `experiments/results/claude/B49-claude-20260717T103000Z-summary.json`.
  Original item follows for history:
  QR-FREE orthogonal
  directions to salvage the -21% orthogonal win as a GRADEABLE submission
  (B48 option c). The B46 champion grades-fail on AICrowd with the prime
  suspect being fnp.linalg.qr (the standout op vs the gradeable S3/B25).
  Target: reproduce B43/B46's exact-orthogonal directions using ONLY the
  ops S3 graded successfully (standard_normal, matmul, subtract, divide,
  norm/sqrt) -- i.e. modified Gram-Schmidt orthogonalization of a
  Gaussian matrix (with sign-normalization for uniform-sphere marginals),
  NO fnp.linalg.qr / eigh / cholesky (the grader may reject all linalg,
  so avoid them entirely). Feasibility-check FIRST (B31/B32 discipline,
  standalone): verify a Gram-Schmidt frame (a) is orthonormal + uniform
  -marginal (unbiased), (b) reproduces B46's ~-21% MSE benefit, and
  CRUCIALLY (c) has acceptable COMPUTE -- a 256-step Python-loop
  Gram-Schmidt adds untracked residual time (charged at lambda=1e11),
  unlike qr's single free call, so measure FLOPs + residual and check the
  multiplier stays competitive (blocked/vectorized GS to cut Python
  iterations if needed). If compute-viable and MSE holds, build a
  candidate and run the Mini+Full gates; a gradeable orthogonal champion
  would realize the -21% leaderboard win. If the residual blows up the
  multiplier past the MSE gain, reject and report (option c infeasible ->
  lead/user falls back to b/d). Bet rests on the qr-op hypothesis
  (unconfirmed); a gradeable orthogonal estimator is valuable regardless.

- [x] **B48** (infra, exploit) - DONE claude 2026-07-17T10:00:00Z - Diagnosed the
  S4 B46 grader "Evaluation error" (submission 316800). FINDING: NOT
  locally reproducible -- B46 runs clean under flopscope-budget, the
  subprocess runner (1000 MLPs, B47), the SERVER runner (grader-like),
  and passes validate/validate-package; qr/sign/diagonal/concatenate are
  NOT in flopscope.remote_unsupported_ops. KEY: the artifact bundles only
  estimator.py + manifest (NO requirements pin), so the grader uses its
  OWN whestbench/flopscope, which may differ from ours. Conclusion: the
  failure is AICrowd-ENVIRONMENT-SPECIFIC; prime suspect is the grader
  lacking/differing on fnp.linalg.qr support (the standout op vs the
  successful S3/B25 which used only version-stable ops). Options for
  lead/user (NOT acted on): (a) one careful resubmit to test
  transient-vs-systematic; (b) re-package with a requirements pin forcing
  our flopscope; (c) a QR-FREE orthogonal construction (most robust);
  (d) keep gradeable B25/B42 submitted while B46 stays local champion.
  Detail: log-claude.md B48 entry; champion.submission_readiness. B46 passes
  all local gates and runs cleanly on 1000 MLPs via the subprocess
  runner, so the failure is grader-environment-specific. Prime suspect:
  the orthogonal-block ops (fnp.linalg.qr/sign/diagonal/concatenate) --
  the only prior SUCCESSFUL submission S3 (B25 radial-exact) used none of
  them. Local diagnostics that do NOT consume submission attempts:
  (1) run B46 under the `server` runner (closest to grading isolation;
  only subprocess was tested) and the `inprocess`/`local` runners on a
  handful of MLPs; (2) check whether fnp.linalg.qr raises under any
  stricter flopscope budget/remote mode; (3) `whest doctor`. If any
  reproduces a qr-related error, the orthogonal champions (B43/B46) are
  confirmed UNGRADEABLE and the fix is a QR-free construction (or keep
  B25/B42 submitted); if nothing reproduces, the grader error is likely
  transient/environment and a single careful resubmission is the
  lead/user call. Record findings for the lead; do NOT resubmit.

- [x] **B47** (infra, exploit) - DONE claude 2026-07-17T09:30:00Z - Full-split gate for the
  B46 champion: PASS, submission-ready. Ran B46 on the complete 1000-MLP
  Full split, paired vs the submitted B25 baseline (B26 report). MSE
  -21.0% (95%CI=[-2.200e-06,-1.028e-06], -5.4 sigma, 549/1000); adjusted
  -23.2% (95%CI=[-2.616e-07,-1.332e-07], -6.0 sigma, 559/1000); both CIs
  entirely below zero; broad (survives excl-top-2, median -6.37e-07);
  zero failure flags. B46's sign-orbit construction is Full-robust (B31
  depth-32 concern does NOT apply) and matches B43's independent-QR
  benefit (Full MSE 6.079e-06 vs 6.051e-06) at ~1/25 the QR cost; its
  multiplier (0.1076) is even lower than the pre-orthogonal champion's.
  B46 Full adjusted 6.533e-07 beats last_submitted 8.507e-07 by -23.2%,
  far above the 5% bar. champion.json full_gate NOT_RUN->COMPLETE,
  submission_readiness->READY. NEXT: reservation + network submit (a
  distinct outward-facing serialized action, not done in this Full-gate
  tick -- flagged for the lead/next submission tick). Detail:
  log-claude.md B47 entry,
  `experiments/results/claude/B47-claude-20260717T093000Z-summary.json`,
  and the combined report B47-...-B46-full-COMPLETE.json.
  Original item follows for history:
  Full-split
  gate for the NEW B46 champion (shared-Haar signed-orbit), which was
  promoted on the Mini gate only (champion.json full_gate=NOT_RUN).
  Required before any submission (AGENTS.md step 7), and especially
  important here because: (1) B46 uses a SIGN-based construction
  (Rademacher column diagonals on one shared Haar frame) -- exactly what
  B31 found can behave differently at depth 32 than independent
  orthogonal blocks, so B44's Full validation of B43 (25 INDEPENDENT
  QRs) does NOT automatically transfer; (2) B44 demonstrated the Mini
  gate is unreliable for orthogonal-directions effects (it false-negatived
  B43), so a Mini-only promotion of B46 could equally be a B30-style
  false POSITIVE. Test: run B46 (estimator.py) on the complete 1000-MLP
  Full split via B26's chunked driver (seed-protocol fix, 10x100), pair
  per-MLP final_layer_mse by mlp_name against B26's champion Full report
  (B25/B42 predictions -- the pre-orthogonal baseline) to confirm the
  orthogonal MSE benefit HOLDS on Full for THIS construction (expect
  ~-21% like B43 if the sign-orbit preserves it; much less would mean
  B46 over-promoted on Mini). Record the single-estimator Full
  aggregate + failure flags for submission readiness; update
  champion.json full_gate. Distinct from B45 (B43 promotion, superseded
  by B46) and B46 (done).

- [x] **B45** (exploit, lead-priority 0) - DONE claude-lead 2026-07-17T10:55:00Z
  (gates PASSED; promotion PREEMPTED by the B46 race) - Stacked
  candidate (B43 exact-Haar directions + B42 chunked f32 forward,
  candidate_claude_lead.py @ 90fa580) predictions match B43 within
  8.8e-08; Mini pair recorded (-20.5% aggregate adjusted, CI straddles
  as diagnosed, 50/100, zero flags); fresh COMPLETE 1000-MLP Full record
  (chunked driver re-passed the exact-digit CLI correctness check; zero
  failure flags): adjusted 6.7462e-07 (-20.70% vs last_submitted
  8.5070e-07), MSE 6.0506e-06, mean_effective_compute 3.0330e10 (+0.83%
  vs champion's Full record -- stacking recovered the un-stacked +4.56%).
  Full paired gate vs B26 submitted baseline: adjusted CI
  [-2.389e-07,-1.133e-07] entirely below zero, -5.61 sigma, 605/1000;
  MSE -5.80 sigma, 611/1000; sensitivity vs simulated-B42 baseline
  -4.65 sigma, 592/1000, -17.4%. All four ruling conditions were
  satisfied, BUT gpt promoted B46 (shared-Haar signed-orbit, LOWER
  FLOPs and lower Mini MSE aggregate) mid-experiment via the standard
  Mini gate -- the AGENTS.md step-6 CAS re-check therefore FAILS for
  B45 (no evidence B45 beats the NEW champion; Mini aggregates favor
  B46). Promotion NOT executed; no submission. B45's Full-verified
  record and candidate are RETAINED as the fallback champion path:
  see the lead race addendum in experiments/log-claude-lead.md for the
  B47 decision tree (if B46's Full record confirms it >= B45, submit
  B46 under step 7; if B46 under-performs B45 on the paired Full
  comparison, the B45 ruling authorizes promoting B45 with the two
  COMPLETE reports as evidence). Detail:
  `experiments/results/claude-lead/B45-claude-lead-20260717T090826Z-013df29-summary.json`.
  LEAD RULING (Lead review 2026-07-17T09:08:00Z in
  experiments/log-claude-lead.md): promotion override approved on B44's
  Full paired evidence, independently re-verified this tick from the raw
  per-MLP reports (-4.7 sigma adjusted / -5.8 sigma MSE, CIs entirely
  below zero, robust to trimming, zero flags; still -3.73 sigma against
  a conservative simulated-B42-multiplier baseline). Conditions: fresh
  1000-MLP Full record for the rebuilt (B42+B43) candidate with a
  passing paired Full gate vs B26's submitted baseline; Mini pair still
  run and recorded; standard CAS promotion; submission only via the
  unchanged step-7 reservation protocol (>=5% over 8.507033588741281e-07,
  expected ~-17%). Original item follows.
  B44 proved B43 is a
  large, robust champion-beating win (-17.7% adjusted / -21% MSE on the
  full 1000-MLP split, -4.7 to -5.8 sigma, 597-611/1000 improved, broad
  not outlier-driven, zero failure flags) that the 100-MLP Mini gate
  FALSE-NEGATIVED (50/100, CI straddled zero -- underpowered against
  B43's fat-tailed per-MLP deltas). Promotion is gated on the Mini CI,
  which B43 fails, so a worker cannot promote unilaterally -- this needs
  a LEAD ruling (analogous to the S3 first-submission ruling) that the
  overwhelming Full paired evidence justifies promotion. Recommended
  execution once ruled: (1) rebuild B43's orthogonal directions
  (candidate_claude.py @ 56c3f41) on top of B42's residual-minimizing
  forward structure -- the current candidate pays ~+4.6% multiplier from
  higher residual + QR FLOPs; stacking on B42 recovers most of the
  residual and enlarges the win; (2) re-run the Full paired gate on the
  rebuilt candidate vs the B42 champion to confirm (Mini will still
  false-negative, so gate on Full per this ruling); (3) promote via the
  standard CAS proposal citing B44's Full evidence; (4) submit -- Full
  adjusted 7.005e-07 vs last_submitted local Full 8.507e-07 is ~17.7%
  better, far above the 5% bar (a major leaderboard improvement over the
  current 6.6845e-07 submission). Also: consider a methodology amendment
  -- Full-confirm rather than reject a large-aggregate Mini candidate
  that fails only on CI width (the inverse of B30). See B44 summary and
  log-claude.md B44 entry.

- [x] **B46** (exploit) - DONE gpt 2026-07-17T09:07:33Z (Mini gate PASS) - Shared-Haar
  signed-orbit blocks for radial-exact Monte Carlo. B43 proves exact-Haar
  blocks robustly reduce Full-split MSE, but pays for 25 independent QR
  factorizations. Draw one exact-Haar frame `Q`, then form 25 blocks
  `Q * d_b` with independent seeded Rademacher column diagonals `d_b`.
  Every block remains exactly Haar-marginal (and every row exactly uniform
  on the sphere), so the estimator stays unbiased; conditional sign orbits
  may retain cross-block coverage while reducing QR FLOPs by about 24/25.
  Stack the construction directly on B42's float32 chunked forward and run
  the standard paired Mini gate against the current champion. This is
  independent of B45's lead-only promotion override: it tests a new sampling
  law and does not modify or promote B43. Result: adjusted score -29.81%,
  MSE -30.42%, paired adjusted delta -2.270e-07 with conservative 95% CI
  [-4.476e-07,-6.436e-09], 55/100 improved, zero failure flags. Persisted in
  `experiments/results/gpt/B46-gpt-20260717T085533Z-013df29-summary.json`.

- [x] **B44** (exploit) - DONE claude 2026-07-17T02:00:00Z - Full-split
  paired MSE robustness test of B43's orthogonal directions. RESULT:
  DECISIVE PASS on the full 1000-MLP split -- MSE -21.3%
  (95%CI=[-2.197e-06,-1.086e-06], -5.8 sigma, 611/1000), adjusted score
  -17.7% (95%CI=[-2.130e-07,-8.749e-08], -4.7 sigma, 597/1000), broad
  (survives excl-top-2 and 10%-trim, median delta -7.3e-07), zero
  failure flags. Proves B43's variance reduction is robust and large,
  and that the 100-MLP Mini gate FALSE-NEGATIVED it (underpowered
  against fat-tailed per-MLP deltas -- the inverse of B30). Did NOT
  promote unilaterally (Mini gate failure -> lead ruling required, queued
  as B45). Reused B26's champion Full report (identical predictions).
  Detail: log-claude.md B44 entry,
  `experiments/results/claude/B44-claude-20260717T020000Z-summary.json`,
  and the combined 1000-MLP report B44-...-B43-full-COMPLETE.json. B43's Mini
  paired gate failed (CI straddles zero) but its -24% aggregate MSE is
  informative: the free-data post-mortem shows the headline is ~entirely
  2 outlier MLPs (excl top-2 -> mean +3.9e-09), YET the 10%-trimmed mean
  is -3.69e-08 (~-4.6% of champion adj score) -- a modest REAL broad
  component masked by outlier noise on only 100 MLPs. The Full split
  (1000 MLPs) is the definitive test: outliers dilute 10x while the
  broad component accumulates with sqrt(10)-tighter SE, so a Full paired
  MSE gate can resolve whether B43 is a robust improvement or a Mini
  artifact. Efficient: B26 already has the champion's (B25/B42 -- IDENTICAL
  predictions, residual-min changed compute not predictions) complete
  1000-MLP Full per-MLP MSE; only B43 needs a Full run. Reuse B26's
  chunked driver (with the seed_protocol_version fix) on candidate_claude.py
  @ 56c3f41, 10x100-MLP chunks, pair per-MLP final_layer_mse by mlp_name
  vs B26's champion report. MSE-only gate (adjusted-score is unfair until
  B43 is rebuilt on B42's residual-min structure -- that's the follow-up
  IF this passes). If the Full MSE paired CI is entirely below zero ->
  B43's variance reduction is robust, green-light rebuilding on B42 for
  a fair adjusted-score gate (potential large promotable+submittable win);
  if it straddles zero -> B43 is a Mini outlier artifact, close the line.

- [x] **B42** (exploit, lead-priority 1) - DONE claude-lead 2026-07-17T01:55:00Z
  (PROMOTED) - Paired Mini gate PASSED decisively: 100/100 MLPs improved,
  paired_mean_delta=-2.637e-08, conservative 95% CI=[-3.626e-08,-1.648e-08]
  entirely negative, zero failure flags, aggregate adjusted score -3.34%
  (7.887e-07 -> 7.623e-07), final_layer_mse unchanged (7.2108e-06 on both
  sides; max per-MLP relative MSE change 5.0e-04). Mechanism confirmed by
  three probes (experiments/results/claude-lead/B42-probe*.py): the charged
  residual lives almost entirely in the 32-layer loop's allocator/OS memory
  churn (float64 13MB temporaries), NOT the RNG draw (0.7ms) or normalize
  (0.3ms); float32 chain halves it, 650-row chunking (arena reuse) cuts it
  further; float64 accumulation of per-layer sums keeps predictions within
  7.7e-08 of the champion (per-MLP MSE identical to 6 significant digits;
  the f32 forward rounding averages out across 6,500 samples). In-process
  ceiling was -9.5%; under the subprocess harness the champion's own
  residual is smaller (~24ms vs 41ms in-process), so the realized gain is
  -3.34%. Follow-ups queued: chunk-size fine-tune (~812) is NOT queued
  (diminishing returns, run-to-run jitter of similar size); B43 stacking
  is the route to the >=5% submission bar. See
  `experiments/log-claude-lead.md` and
  `experiments/results/claude-lead/B42-claude-lead-20260717T011419Z-2227ef3-summary.json`.
  Original item: Attribute and reduce the champion's charged residual wall time. Lead
  review 2026-07-17 read the actual scoring source
  (`whestbench/budget.py`, `flopscope/_budget.py`): effective compute is
  EXACTLY `C = flops_used + 1e11 * residual_wall_time_s`, where
  `residual = wall - flopscope_backend_time - flopscope_overhead_time`.
  Backend wall time of INSTRUMENTED fnp ops is NOT charged at all (only
  their symbolic FLOPs are), and flopscope's own dispatch overhead is
  also uncharged; the ONLY charged time is what runs outside instrumented
  ops (user Python between ops, allocations/GC, and any PLAIN-numpy call,
  which flopscope cannot see). The champion's per-MLP decomposition (B25
  candidate raw report, means over 100 MLPs): wall 245.5ms = backend
  177.3ms (free) + overhead 42.1ms (free) + residual 26.1ms -> 2.61e9
  charged, i.e. 9.5% of its 2.735e10 raw FLOPs. Ceiling: driving
  residual to ~0 gives multiplier 0.1102 -> 0.1006, a -8.7% adjusted
  score with unchanged-or-negligibly-changed predictions - the
  trivially-promotable B23 shape (every per-MLP delta <= 0), and B23's
  two attempts were flying blind without this decomposition (it never
  identified WHERE the 26ms lives). Plan: (1) reproduce the
  decomposition locally on 2-3 real Mini MLPs via a BudgetContext probe;
  (2) ablate to attribute the 26ms (candidates: allocation/GC of the
  ~13MB per-layer float64 temporaries, the `astype(float32)` copy,
  between-op Python in the 32-layer loop, the final stack, RNG-adjacent
  gaps); (3) apply targeted fixes - e.g. run the entire chain in float32
  (cast weights per layer: halves memory traffic in every un-instrumented
  gap; prediction change ~1e-7 relative, MSE impact ~1e-12 vs the 7.2e-6
  champion MSE, negligible), avoid the separate astype copy, fuse/reduce
  temporaries; (4) validate MSE unchanged on 10 MLPs offline, then run
  the standard paired Mini harness. Success: mean_effective_compute
  meaningfully below 2.996e10 with per-MLP MSE unchanged within noise;
  promote via CAS if the paired CI clears zero. Stacks with B43 and with
  any future MSE win.

- [x] **B43** (exploit, lead-priority 2) - DONE claude 2026-07-17T01:30:00Z (rejected at Mini gate; artifact fixed; strong building block) -
  Implemented via instrumented fnp.linalg.qr (candidate_claude.py @
  56c3f41). ARTIFACT FIX CONFIRMED: cost is +4.2% multiplier (not B22's
  +149%) -- residual wall time 0.041s not 0.5s, QR backend time free,
  +4.1% QR FLOPs only. B40's "compute-blocked" verdict is DEFINITIVELY
  REFUTED. Radial-exact + orthogonal STACK: standalone controlled check
  +14.2% MSE reduction; 100-MLP harness aggregate -24.2% MSE / -20.9%
  adjusted score (much bigger than B22's -5.5% because radial-exact
  removes the chi-radius noise). BUT the Mini paired gate FAILS:
  paired_95pct_CI=[-4.379e-07,+1.005e-07] straddles zero, 50/100
  improved, because the aggregate win is fat-tailed (median delta ~0,
  driven by ~2 outlier MLPs). Not promotable alone per AGENTS.md step 4
  (would be a B30-style outlier-driven overfit). Zero failure flags,
  exactly unbiased. LEAD DECISIONS FLAGGED: (a) stacking with B42 lowers
  baseline C and shrinks the +4% bite; (b) the -20.9% aggregate is far
  above the lead's -1.5% prediction, and Full (1000 MLPs) would dilute
  the outliers + tighten the CI -- a Full paired eval could flip the gate
  to PASS (large promotable+submittable win). Did NOT run Full
  unilaterally (failed Mini gate; pursuing further is a lead call).
  Candidate retained at 56c3f41. Detail: log-claude.md B43 entry +
  `experiments/results/claude/B43-claude-20260717T013000Z-summary.json`.
  ORIGINAL ITEM (lead) follows for history:
  Exact-Haar orthogonal blocks via
  INSTRUMENTED ops - B22 done right. Lead review 2026-07-17 found B22's
  candidate generated its orthogonal blocks with PLAIN numpy
  (`_np.linalg.qr`, `_np` RNG, commit b0f209d) - invisible to flopscope,
  so its entire QR + radius-sampling wall time (~0.5s/MLP) was charged
  as residual at lambda=1e11 (the +149% adjusted-score penalty), and the
  QR FLOPs never even appeared in flops_used. The instrumented
  `fnp.linalg.qr` (registry category counted_custom) charges
  2*(2mnk - 2/3 k^3) ~= 4.5e7 FLOPs per 256x256 block (~1.1e9 for 25
  blocks, +4.1% on raw FLOPs) and its backend wall time is FREE. So
  B22's real, officially-paired -5.5% final-layer MSE gain costs ~+4%
  multiplier, not +149%: expected net ~-1.5% adjusted score, more if
  stacked on B42's residual cut (which lowers the baseline C). This also
  corrects the shared premise of B39/B40/B41 (that QR wall time is
  inherently charged): B40's "closes the orthogonal-directions line"
  verdict is WITHDRAWN by the lead - the line was closed on an
  instrumentation artifact. Design: B22's construction + B25's
  radial-exact scaling, all in fnp - 25 blocks of
  `fnp.linalg.qr(rng.standard_normal((256,256)))`, sign-correct via
  `q * fnp.sign(fnp.diagonal(r))` for exact Haar, rows are unit
  directions (no radii needed under radial-exact; B22's chi radii are
  obsolete), plus 100 iid normalized rows to reach 6500; multiply layer
  means by closed-form E[r]. Feasibility first (B31/B32 discipline):
  verify on 5-10 MLPs that fnp.linalg.qr's charged FLOPs and residual
  match the model above and MSE tracks B22's gain; run the paired Mini
  harness only if predicted net is clearly negative. Caution per B30:
  a ~-1.5% net Mini effect will NOT clear a Full paired gate on its own;
  value is in stacking with B42 toward the >=5% submission bar.

- [x] **B40** (exploit) - DONE claude 2026-07-16T21:30:00Z (feasibility-rejected) -
  Batched-QR exact-Haar orthogonal directions to capture B22's real
  -5.5% MSE reduction without its 2.6x compute penalty. Premise: B22's
  penalty is residual WALL TIME from QR (raw FLOPs are nearly identical),
  so batch the 25 QRs into one call to cut it like B10/B13 cut
  call-fragmentation. REJECTED at feasibility: the QR wall time is
  INHERENT arithmetic, not call-overhead. Benchmarked (warmed, min of 10):
  25 separate 256x256 QRs = 351ms; ONE batched qr((25,256,256)) = 424ms
  (WORSE -- numpy's batched QR just loops internally in LAPACK); float32
  vs float64 identical; champion forward pass = 183ms, so QR is ~2.3x the
  forward. That ~350ms x lambda=1e11 ~ 3.5e10 extra effective compute
  matches B22's observed doubling exactly, and batching cannot remove it.
  Generating a dxd Haar-orthogonal matrix is fundamentally O(d^3)
  (Householder/QR/Gram-Schmidt all equivalent), so exact orthogonality
  is inherently ~2x the forward-pass wall time on this machine. Together
  with B22 (Haar, compute-blocked) and B39 (structured, wrong direction
  law), this CLOSES the orthogonal-directions line for full 256-blocks:
  the 5.5% gain is real but fundamentally compute-blocked. No candidate
  built, no harness compute spent. Possible (but likely marginal, per
  B30) follow-up not claimed: smaller k-row orthogonal blocks trade the
  5.5% down ~proportionally while QR cost drops ~k^2 -- a sweet spot
  might exist but would yield <=~2-3% Mini (<=~1% Full). See
  `experiments/log-claude.md`.

- [x] **B38** (explore) - DONE claude 2026-07-16T21:00:00Z (feasibility-rejected) -
  Last-layer Gaussian-moment Rao-Blackwellization: replace the final
  layer's mean_i ReLU(p_i) with the exact Gaussian-ReLU moment formula
  mu*Phi(mu/s)+s*phi(mu/s) at the sample mean/variance of the
  pre-activations p (CLT-Gaussian over 256 terms). REJECTED at
  pre-validation (10 MLPs, 24 seeds each, measured vs dataset truth).
  TWO reasons, both fatal: (1) the hoped-for Rao-Blackwell variance
  reduction does NOT materialize -- measured seed-variance reduction is
  +0.1% (range -0.2% to +0.4%), not the ~3% theory suggested; in
  practice mean(ReLU(p)) and f(mu_hat,s_hat) track each other almost
  exactly. (2) The CLT-Gaussian approx adds real BIAS: mom_bias^2 ~
  9.6e-7 per neuron (~16% of the MC seed-variance 5.9e-6), because
  post-ReLU h_31 inputs make p imperfectly Gaussian. Net final-layer MSE
  is -12.9% (WORSE) across the 10 MLPs. Closes "last-layer analytic
  denoising" the same way gpt's B36 closed "last-layer template
  projection": any deterministic/Gaussian last-layer correction's bias
  exceeds the (near-zero) variance it saves -- consistent with B1/B3/B34/
  B36's finding that analytic approximations are simply too biased here.
  No candidate built, no harness compute spent. See
  `experiments/log-claude.md`.

- [x] **B36** (explore) - DONE gpt 2026-07-16T18:15:52Z
  (feasibility-rejected) - Output-space
  collapse denoising for the B25 radial-exact champion. Depth-32 activations
  have rank-1-dominated covariance, but all prior direction experiments used
  that structure in input space. Test whether a cheap deterministic final-
  layer template derived from mean propagation captures the per-neuron shape
  well enough that projecting the noisy radial-MC mean onto its span removes
  orthogonal sampling error without material bias. Feasibility-check the
  projection and oracle scale on real Mini MLPs before committing to the full
  paired harness; reject early if template-direction bias exceeds the MC
  variance reduction.
  Result: REJECTED at the predeclared feasibility gate. On the first 10
  canonical Mini MLPs, projection raised mean MSE from 4.162e-06 to
  1.608e-05 (+286%). Even the ground-truth oracle scale could only reach
  1.372e-05 (3.30x the MC MSE), proving the deterministic template's tiny
  directional mismatch is already too biased to recover through scalar
  fitting. No 100-MLP paired run was warranted. See `experiments/log-gpt.md`
  and `experiments/results/gpt/B36-gpt-20260716T180943Z-2227ef3-summary.json`.

- [x] **S3** (admin/exploit, lead-priority 0) - DONE claude-lead 2026-07-16T17:20:10Z -
  EXECUTED AND GRADED: attempt S3-claude-lead-20260716T171600Z,
  submission_id 316676, submitted 17:18:08Z, graded successfully within
  ~2 min. Leaderboard score 6.684538479656953e-07 (primary) /
  6.488121769052668e-06 (secondary MSE) -- BETTER than our local Full
  numbers (8.507e-07 / 7.693e-06), so no overfitting-to-public-data
  surprise in the unfavorable direction. `last_submitted_score` is now
  the non-null local Full score 8.507033588741281e-07 per protocol; all
  future submissions require the full step-7 gate against it. The
  earlier claim-label timestamp 17:35:00Z was written ahead of the real
  clock (~17:14Z, commit b2c4e3c) -- commit times are authoritative.
  Original item: First scored submission of the
  current champion (B25 radial-exact, `estimator.py` @ 2227ef3). Lead ruling
  2026-07-16T17:08Z (`experiments/log-claude-lead.md`): the S1 addendum's
  second clause ("if all previous submitted scores are null, then any scoring
  solution can be submitted") is a positive permission covering the first
  scored submission; step 7's paired Full gate protects a previously-submitted
  baseline that does not exist (B0 was never submitted; both 2026-06-11
  artifacts are null-scored pre-scaffold history). B29's FAIL shows B25 ~= B0
  on Full (not-worse, aggregate -1.14%), and B25 has a COMPLETE 1000/1000 Full
  gate (B26) with zero failure flags. Execute via the unchanged reservation
  protocol: package artifact, SHA-256, unique-attempt-ID ledger reservation
  pushed atomically BEFORE any network call, then
  `whest submit <artifact> --watch --format json`, then exact-ID ledger
  update only. On success set `last_submitted_score` to the recorded local
  Full score (8.507033588741e-07) per protocol. Every SUBSEQUENT submission
  again requires the full step-7 gate (paired Full vs the last submitted
  champion + 5% rule against the now-non-null score).

- [x] **B34** (explore, lead-priority 1) - DONE claude 2026-07-16T20:30:00Z (rejected, premise was a units misread) -
  REJECTED at pre-validation. The premise (analytic error COMPARABLE to
  MC) rests on a units confusion: B0's cov-propagation report has
  final_layer_mse = 8.366e-05 and adjusted_final_layer_score = 8.366e-06
  (they differ by exactly the 0.1 floor multiplier -- the analytic is
  cheap, effective_compute 2.6e9 << the 2.72e10 floor). The analytic's
  TRUE MSE is 8.366e-05, ~10x WORSE than the MC champion's ~8e-06, not
  comparable. My numpy analytic reimplementation is validated (matches
  the real B0 per-MLP report to 4 sig figs). Consequence: b^2 ~ 10
  sigma^2, so fusion at best recovers ~MC (w->~0.9, ignore the analytic);
  measured on 10 MLPs, data-estimated-w fusion is WORSE than MC alone
  (-30.6%), and even unattainable oracle-w fusion gives only +14.1%
  (errors aren't independent either, corr 0.15). Adding cov-propagation
  also raises the multiplier ~8-10%, erasing the oracle gain. No
  candidate built, no harness compute spent. This axis reopens only if a
  future analytic reaches error <= ~sigma (~1e-5 MSE); B1/B3/B6 did not.
  Full detail: `experiments/log-claude.md` B34 entry and
  `experiments/results/claude/B34-claude-20260716T203000Z-summary.json`.
  ORIGINAL ITEM (lead) follows for history:
  Inverse-error fusion
  (precision-weighted / James-Stein shrinkage) of the MC champion with the
  analytic covariance-propagation estimate. B32's post-mortem closes
  input-structure VARIANCE reduction â€” but bias-variance FUSION is a
  different, untouched axis: the gain-product covariance propagation (the
  pre-B0 incumbent, still present as dead code below the champion's
  `return` in `estimator.py`; B0 measured final_layer_mse=8.366e-06, and
  B3's exact-cross-moment variant is statistically identical) has error
  COMPARABLE to the champion's MC noise (7.2-7.7e-06), and the two errors
  are INDEPENDENT (the analytic path is deterministic; MC error is
  seed-driven noise). Fuse per MLP at the scored final layer only:
  fused = w*MC + (1-w)*analytic. Estimate w from the data:
  ||MC - analytic||^2/d unbiasedly estimates (sigma^2 + b^2) by
  independence, and sigma^2 (per-neuron variance of the MC mean) comes
  from the same forward samples (per-neuron sample variance / n, scaled
  by E[r]^2 under the champion's radial-exact construction â€” derive this
  carefully: the champion averages f(u) then scales, so
  Var = E[r]^2 * Var_u(f)/n). Then w = clip(1 - sigma_hat^2/(sigma_hat^2
  + b_hat^2), 0, 1), SHARED across the 256 neurons (d=256 averaging makes
  it stable; per-neuron w would overfit). If b^2 ~= sigma^2 this yields
  MSE -> sigma^2*b^2/(sigma^2+b^2) ~= 0.5*sigma^2 â€” a ~40-50% final-layer
  MSE cut, dwarfing every post-B25 margin. Cost: cov-prop adds ~2
  (256,256)x(256,256) matmuls per layer (~2.1e9 raw FLOPs, ~8% of the
  champion's 2.7e10) plus flopscope overhead â€” B0's cov-prop report has
  the real numbers; the win survives if the MSE cut (>~40%) beats the
  multiplier increase (~10%). DISTINCT from B2's failure: B2 needed
  per-SAMPLE correlation between f and a control on shared inputs (the
  residual variance grew); fusion needs NO per-sample correlation, only
  independent errors of comparable size, which are ALREADY MEASURED.
  Watch worst-case per-MLP regressions at the paired gate: w->1
  automatically where the analytic is bad, but verify. Validate the w
  estimator offline on 5-10 real MLPs first (B31/B32 discipline).

- [x] **B35** (exploit, lead-priority 2) - DONE gpt 2026-07-16T17:50:46Z (feasibility-rejected) - Optimal sample count under an
  AFFINE effective-compute model. B16's N-invariance argument assumed
  multiplier proportional to N; but if effective_compute(N) = a*N + b with
  a genuinely fixed component b (the champion issues 32 matmul calls
  regardless of N; measured effective_compute - flops_used ~ 2.6e9, ~9% of
  C), then above the floor the adjusted score
  (a*N+b)/B * v/N = a*v/B + b*v/(B*N) strictly DECREASES in N for an
  unbiased estimator â€” raising N converts the fixed-overhead share into
  score reduction, up to ~9% asymptotically. First measure
  effective_compute at N in {3250, 6500, 13000, 26000} on ~10 real MLPs
  and fit (a, b): if the overhead is mostly wall-time-proportional (B23's
  diagnosis suggests much of it tracks backend matmul+ReLU time, which IS
  proportional to N), then b~0 and there is no win â€” record and close. If
  b_hat/C > ~2-3%, run the harness comparison at the fitted optimal N
  (N=26000 is still ~10x under the 2.72e11 budget; check per-MLP time
  limits). Complements B34: fusion shrinks v, this shrinks the overhead
  share; they stack.

- [x] **B32** (explore) - DONE claude 2026-07-16T20:00:00Z (feasibility-rejected) -
  Quadratic control variate c(u)=(u.a)^2 (mean 1/d known exactly, so
  unbiased) on the dominant-direction projection, for the B25 champion.
  REJECTED at pre-validation: captures essentially NO variance -- implied
  reduction corr(f,c)^2 only 0.1-0.4% per neuron, measured variance
  reduction ~0 (-1.5% to +2.8%, noise) across 5 real MLPs. Resolves an
  apparent paradox with B31: B31's corr(f(u),f(u_reflected))~0.61 was
  high NOT because f depends quadratically on u.a, but because f barely
  depends on u.a at all -- the reflection preserves the entire 255-dim
  orthogonal complement, and THAT is what f depends on. So a single
  input direction carries almost no exploitable signal; the directional
  variance is irreducibly ~255-dimensional and diffuse. This is the
  unifying explanation for why every direction/subspace method failed
  (B4/B7/B8/B12/B21/B31/B32): there is no low-dim input structure
  concentrating the variance, so plain MC over directions is near-optimal
  and the only exploitable low-dim structure was the 1-D radius, already
  used by B25. (Note: the OUTPUT covariance is rank-1 dominated per B21 --
  neurons move together -- but that does NOT imply concentrated INPUT
  dependence, and B32 confirms it doesn't.) See `experiments/log-claude.md`.
  No candidate file needed. Strong evidence the estimator-accuracy
  direction is converged for this compute budget.

- [x] **B31** (explore) - DONE claude 2026-07-16T19:30:00Z (feasibility-rejected) -
  Antithetic reflection along ONLY the dominant collapse direction
  (u' = u - 2(u.a)a), for the B25 radial-exact champion. Hypothesis: if
  f(u) ~ g(u.a)*b with g monotonic, reflecting a's component flips
  t=u.a -> -t and cancels the odd part, and since a is the surviving
  mode the cancellation should persist to depth 32 (unlike B4's full
  flip). REJECTED at pre-validation before any harness run: the
  reflection makes variance WORSE, ~2x (reduction -8% to -114% across 5
  real MLPs, ~1.95-2.14x for 4 of them). Direct measurement shows why:
  f(u) and f(u_reflected) are strongly POSITIVELY correlated (per-neuron
  rho ~ 0.61 mean, mean relative |f(u)-f(u')| only ~11%). The
  final-layer output is approximately EVEN in the dominant input
  direction, not monotonic -- there is no odd component to cancel, so
  forcing reflected pairs just makes near-duplicate samples and halves
  the effective sample count (the ~2x variance). This crisply explains
  WHY every sign/reflection-based antithetic method fails at depth 32
  (B4 full-flip, B7 mid-network, now B31 dominant-flip): the signal
  lives in the even/magnitude part of the collapse, which sign-flips
  cannot touch. Ties together with the radial-exact win (B25): the
  radius/magnitude IS the exploitable structure; input SIGN structure is
  not. See `experiments/log-claude.md`. No candidate file needed.

- [x] **B30** (infra, explore) - DONE claude 2026-07-16T19:00:00Z - Diagnosed WHY
  B25's Mini promotion failed to replicate on Full (B29). Two findings:
  (1) the Mini and Full splits are NEARLY DISJOINT -- only 2 of 100 Mini
  MLPs also appear in Full, so the promotion gate and the Full
  evaluation measure almost entirely different MLP populations. (2)
  B25's per-MLP paired effect (adjusted_final_layer_score, B25-B0, on
  Full) has mean -8.67e-09 but per-MLP std 3.20e-07 (~37x the mean) --
  the true effect is only 0.27 SE from zero at n=100 (Mini scale) and
  0.86 SE at n=1000 (Full scale); 210 big wins / 181 big losses / 609
  near-ties. Mechanism: the Mini promotion's -1.434e-07 delta was ~16x
  more negative than the Full population mean and ~4 SE (at n=100) below
  it -- a strongly favorable, non-representative draw. B25's true edge is
  marginal and sub-sigma, so it cannot clear a Full paired gate. B25
  stays champion (validly promoted, not-worse per B29); submission stays
  blocked. RECOMMENDATION FOR LEAD (workers can't reorder priorities):
  require a confirmatory Full paired gate before promoting small-Mini
  -effect candidates, or a min-effect threshold, or treat them as
  provisional; and redirect effort from sub-percent radial refinements
  toward a larger-effect estimator change. Full detail:
  `experiments/log-claude.md` B30 entry and
  `experiments/results/claude/B30-claude-20260716T190000Z-summary.json`.

- [x] **B29** (infra, exploit) - DONE claude 2026-07-16T18:30:00Z - Paired Full-split
  gate for the B25 champion vs the B0 champion, computed from two
  already-complete reports (B24's B0 Full report + B26's B25 Full
  report), paired by `mlp_name`, no new harness runs. Result: FAIL.
  Exactly 500/1000 MLPs improved, 500 regressed; paired_mean_delta=
  -8.668e-09, paired_95pct_CI=[-2.851e-08, +1.118e-08] -- does NOT lie
  entirely below zero (verified robust to t_crit choice). B25's paired
  advantage over B0 was real and significant on the 100-MLP Mini split
  at promotion time but shrinks to statistically-indistinguishable-from
  -zero on the 10x-larger independent Full split -- the suite-sampling
  -overfitting risk AGENTS.md's two-tier Mini/Full design exists to
  catch. Does not invalidate B25's promotion (correctly used the
  Mini-split-only promotion gate); B25 remains champion. But despite
  S1's resolution unblocking submission from the null-scores angle,
  AGENTS.md step 7's paired Full-split gate is not satisfied, so
  submission should NOT proceed on current evidence -- a worker
  shouldn't unilaterally waive an explicit protocol requirement.
  `champion.json` gained a new `submission_readiness` field (status
  BLOCKED, reason = failed paired Full-split gate, not S1) so future
  workers don't attempt submission without addressing this. Full
  detail: `experiments/log-claude.md` B29 entry and
  `experiments/results/claude/B29-claude-20260716T183000Z-summary.json`.
  Needs either a stronger future candidate that clears the Full-split
  gate convincingly, or an explicit user/lead ruling on whether to
  relax the paired-gate requirement given S1's permissive spirit.

- [x] **B28** (infra, explore) - DONE claude 2026-07-16T18:00:00Z - Computed the
  dataset's ground-truth noise floor (`champion.json.noise_floor` was
  `null` since scaffolding). Calibrated FLOPs-per-sample for
  `whestbench.scoring.sample_layer_statistics` directly via
  `flopscope.budget()` (converged to 4,632,529.741312 FLOPs/sample at
  n=1,000,000), backed out the implied ground-truth sample count from
  each Mini-split row's `sampling_budget_breakdown.flops_used` (identical
  across all 100 rows: 909,050,195 samples, ~909 million -- fixed
  generation policy), combined with each row's own `avg_variance` via
  `Var(ground-truth mean) = avg_variance / n_gt`. Result: implied noise
  floor variance 1.68e-11 to 2.23e-10 (mean 5.45e-11) across the 100
  MLPs -- roughly 5-6 orders of magnitude smaller than the champion's
  current final_layer_mse (7.21e-06 mini / 7.69e-06 full). Conclusion:
  the ground truth is effectively exact at any precision level current
  or plausible future estimators could reach; no meaningful noise floor
  limits further estimator improvement. `champion.json.noise_floor`
  updated with the full computation. See `experiments/log-claude.md` B28
  entry. No candidate needed, no harness run -- a closed-form calculation
  from already-public dataset fields plus a one-off flopscope
  calibration.

- [x] **B27** (explore) - DONE claude 2026-07-16T17:30:00Z (feasibility-rejected) -
  Checked whether B25's exact-homogeneity radial substitution extends to
  the B1/B10/B11/B13/B14/B16/B19/B21 active-subspace Gauss-Hermite
  quadrature lineage's orthogonal-complement sampling (`x = t_k*v1 + s`
  per quadrature node). Result: REJECTED before any candidate was
  written. B25's trick requires the WHOLE input vector to scale by a
  positive constant; `s` is only an additive piece of a compound vector
  with a separate fixed term (`t_k*v1`), so scaling `s` alone does not
  correspond to scaling `x`. Verified numerically on a real MLP: scaling
  only the orthogonal-complement component gave a 10.4% relative
  deviation from the naive multiplicative prediction (vs ~2.3e-11 for
  B25's true whole-vector homogeneity check) -- confirms no exact radial
  substitution is available here. Consistent with B7's finding that
  post-nonlinearity quantities don't inherit pre-nonlinearity symmetries
  once mixed with other terms. See `experiments/log-claude.md`. No
  candidate file was needed or committed. Closes this specific
  combination; the active-subspace lineage remains closed per B21's
  ceiling finding and is now also surpassed outright by B25 on raw
  accuracy.

- [x] **B26** (infra, exploit) - DONE claude 2026-07-16T17:00:00Z - Full-split gate
  for the new B25 radial-exact champion (estimator.py @ 2227ef3),
  COMPLETE (1000/1000 MLPs, zero failures). Reused B24's chunked method
  but with ten 100-MLP chunks instead of two 500-MLP chunks -- backgrounded
  500-MLP runs were killed with no output twice in this session (with and
  without an intervening ScheduleWakeup), while foreground 100-MLP chunks
  (~5 min each) completed reliably. The mandatory correctness check (vs
  official CLI) caught a real bug before any real chunk ran: slicing the
  dataset with `.select()` before calling `make_contest_from_dataset`
  silently drops whestbench's weakref metadata side-channel, defaulting
  `seed_protocol_version` to the wrong value ("2.0" vs this dataset's
  real "3.0") and corrupting MLP reconstruction (~6x final_layer_mse
  divergence from the CLI on identical-named MLPs, despite matching
  flops_used and clean flags). Fixed by reading the protocol version from
  `whestbench.metadata()` on the dataset BEFORE slicing, then building
  `ContestData` manually; re-verified exact-digit match against the CLI
  before trusting it. Combined result:
  adjusted_final_layer_score=8.507033588741e-07,
  final_layer_mse=7.692520063074e-06, mean_effective_compute=
  3.007947213208e10 -- close to and slightly higher than the Mini-split
  numbers that selected this champion, no overfitting signal.
  `champion.json`'s `full_gate` updated from NOT_RUN to COMPLETE. Full
  detail: `experiments/log-claude.md` B26 entry and eleven raw reports
  under `experiments/results/claude/B26-claude-20260716T170000Z-2227ef3-*`.

- [x] **B22** (explore) - DONE gpt 2026-07-16T17:09:26Z - Block-orthogonal Gaussian Monte Carlo. Replace
  independent normal input rows with randomized orthogonal directions in
  width-sized blocks, independently scaled by chi-distributed radii. Each
  row remains exactly N(0, I), so the usual sample mean remains unbiased;
  the within-block negative dependence may reduce the final-layer residual
  variance that B4's simple antithetic pairing and B21's direction refinement
  could not remove. Compare at the champion's same 6,500-sample FLOP scale.
  REJECTED on the official paired Mini gate: block orthogonality improved raw
  final-layer MSE by 5.53%, but the 25 dense QR factorizations per MLP raised
  mean effective compute from 3.03e10 to 7.95e10 and adjusted score worsened
  149.32%. Paired mean delta=+1.198e-06, conservative 95% CI=
  [+7.489e-07,+1.647e-06], 85/100 regressed, with zero failure flags. See
  `experiments/results/gpt/B22-gpt-20260716T170926Z-2227ef3-summary.json`.

- [x] **B23** (exploit, lead-priority 1) - DONE claude 2026-07-16T15:20:00Z - Reduce the champion's own
  flopscope overhead. Every overhead-reduction item so far (B10/B11/B13/
  B14/B16) attacked the *candidate lineage's* overhead; nothing has ever
  attacked the champion's. The champion's score multiplier is
  `mean_effective_compute/B ~ 0.1105-0.1107`, but its raw `flops_used` is
  only 2.7346e10 -> multiplier floor territory: if effective_compute could
  be pushed down toward raw FLOPs (ratio 1.101 on the B0/gpt machine,
  ~1.19 measured on the claude machine in B10's diagnosis; the gap is
  tracking/wall-clock overhead, machine-dependent), the multiplier
  drops toward the 0.1 floor -- up to ~9.5% score reduction with BIT-
  IDENTICAL predictions. That is the uniquely promotable shape: same
  predictions -> same per-MLP MSE -> every paired delta is
  `mse_m*(mult_cand_m - mult_champ_m) <= 0`, so any consistent overhead
  cut passes the paired CI gate trivially, unlike the 6%-MSE lineage
  that kept losing on exactly this term. Plan: first diagnose, from the
  champion's own per-MLP report fields (`flopscope_overhead_time_s`,
  `flopscope_backend_time_s`, `wall_time_s`, `effective_compute` vs
  `flops_used`), which term drives the ~10-19% excess for a 32-matmul-
  call estimator; then test cheap mechanical reductions with zero
  statistical change (e.g. fewer/larger tracked RNG or elementwise ops,
  avoiding tracked temporaries, dtype/layout choices, generating the
  (6500,256) input in one call, in-place ReLU). Success criterion:
  unchanged final_layer_mse per MLP, lower mean_effective_compute,
  paired CI entirely below zero.
  Result: REJECTED (two attempts, both bit-identical predictions
  confirmed on the real harness -- max per-MLP MSE diff 0.0 in both).
  Critical pre-implementation catch: `standard_normal(shape,
  dtype=float32)` uses a different Ziggurat bit-consumption path than
  float64-then-cast, giving genuinely DIFFERENT samples, not just
  different precision -- avoided before writing any candidate. Attempt 1
  (defer 32 mean calls into 1 batched call): mean_effective_compute got
  WORSE (+2.37%, decisively REJECTED) -- stacking all 32 raw (6500,256)
  layers into one ~213MB array before reducing cost ~0.038s of real
  backend copy time, more than the ~0.012s saved from fewer calls.
  Attempt 2 (drop only the redundant `fnp.array()` wrapper, -1 call):
  mean_effective_compute genuinely improved (~0.3%, right sign, 69/100
  MLPs improved) but paired_mean_delta~1.6e-10 is statistically
  indistinguishable from zero at Mini-split scale (CI straddles zero).
  Confirmed flopscope arrays are immutable (item assignment raises
  TypeError by design) -- no pre-allocation workaround exists.
  matmul+ReLU (32 sequential, unavoidable layers) dominate both variants'
  remaining overhead; the lead's "up to 9.5%" ceiling assumed the full
  gap was removable, but it's mostly inherent to the algorithm's
  structure, not trimmable while preserving exact predictions. See
  `experiments/log-claude.md` and
  `experiments/results/claude/B23-claude-20260716T150000Z-1598169-summary.json`.
  Closes this item -- no further mechanical overhead lever identified.

- [x] **B24** (infra, lead-priority 2) - DONE claude 2026-07-16T14:35:00Z - Chunked, resumable complete
  Full-split gate (all 1000 MLPs). Required before ANY submission
  (AGENTS.md step 7) and currently impossible in one background window
  (~58 min measured; two runs killed mid-flight -- see the 2026-07-16
  13:45Z log-claude.md entry and champion.json's
  `full_gate_partial_check`). Build the chunk-and-resume runner that
  entry sketched: drive `whestbench.scoring.evaluate_estimator` +
  `whestbench.runner.SubprocessRunner` directly over index ranges,
  persisting per-MLP records after each chunk (~25 min each) and
  aggregating at the end. MANDATORY correctness check before trusting
  it: run the chunked path on the Mini split first and require exact
  (machine-precision) agreement with the official CLI's aggregates for
  the same estimator, since hand-rolled aggregation was previously
  rejected precisely for correctness risk. Deliverable: a complete
  1000-MLP Full-split record for the current champion in champion.json
  (replacing/superseding `full_gate_partial_check`) plus the raw
  report. This unblocks the submission path the moment S1 is resolved,
  and the tool is reusable for every future champion.
  Result: DONE. Used `whestbench.cli._run_estimator_with_runner` (the
  CLI's own internal wiring, not reimplemented) over two 500-MLP index
  ranges (0-499, 500-999), ground truth read from the dataset's
  precomputed fields (never recomputed). Mandatory check ran on BOTH a
  20-MLP Full-split sample and a 30-MLP Mini-split sample: final_layer_mse
  matched the official CLI to the exact last digit in every case
  (bit-identical predictions); only the timing-derived multiplier
  differed, by an amount consistent with ordinary run-to-run wall-clock
  jitter (same magnitude as jitter between two separate official CLI
  runs). Combined result (1000/1000 MLPs, zero overlap, zero failures):
  adjusted_final_layer_score=8.5937e-07, final_layer_mse=7.7814e-06 --
  consistently better than the Mini-split numbers that selected this
  champion. `champion.json`'s `full_gate` now COMPLETE (replacing
  `full_gate_partial_check`); also bundled S2's fix in the same commit.
  See `experiments/log-claude.md` for full detail and all raw report
  paths.

- [x] **B25** (explore, lead-priority 3) - DONE claude 2026-07-16T16:00:00Z -
  PROMOTED. Confirmed MLPs are bias-free (`whestbench.MLP` has no bias
  field), so ReLU nets are *exactly* positively homogeneous
  (f(c*x)=c*f(x), c>0; verified empirically to 2.27e-11 relative error
  across all 32 layers). For z=r*u (r=||z||~chi(256), u uniform on
  sphere, r independent of u), this gives E[f(z)]=E[r]*E[f(u)] exactly --
  stronger than the literal "stratify r" ask, since substituting the
  closed-form E[r] eliminates radial MC variance entirely rather than
  reducing it via stratification. Implemented in candidate_claude.py
  (commit 1cf928a): forward only directions u=z/||z|| through the
  network, scale final result by closed-form
  E[r]=sqrt(2)*exp(lgamma((d+1)/2)-lgamma(d/2)). Paired Mini-split
  harness result (n=100): final_layer_mse 8.5049e-06 -> 7.2108e-06
  (-15.2%), mean_effective_compute flat-to-slightly-better
  (3.0067e10->2.9957e10), paired_95pct_CI=[-2.581e-07, -2.868e-08]
  (entirely negative). Gate passed cleanly; promoted to champion. Full
  detail: `experiments/log-claude.md` B25 entry and
  `experiments/results/claude/B25-claude-20260716T160000Z-1cf928a-summary.json`.
  New champion still needs its own Full-split gate run (B24-style) before
  a submission attempt; Mini-split promotion only re-validates on Mini.

- [x] **S1** (admin, user action required - not claimable as an experiment) -
  RESOLVED by user ruling 2026-07-16T15:19Z (AGENTS.md addendum, commit
  136f247): null submitted scores are disregarded in the 5% improvement
  rule, and because all previously submitted scores are null, any scoring
  solution may be submitted. The submission pipeline is therefore
  unblocked; the two pre-scaffold manual submissions
  (2026-06-11T05:00:33Z and 2026-06-11T19:50:10Z, no submission IDs)
  remain in the ledger as `pending` history and must still never be
  reconciled by timestamp matching. All other AGENTS.md submission
  prerequisites remain in force unchanged (Full-split gate, reservation
  protocol, no ambiguous-submission retries); note the current B25
  champion's B26 full_gate is a single-estimator evaluation, so decide
  per AGENTS.md whether a paired Full-split comparison is still required
  before reserving a submission.
  Original item, for history: `last_submitted_score` is null and the
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

- [x] **S2** (admin, small metadata correction) - DONE claude 2026-07-16T14:35:00Z (bundled into the B24 commit) -
  `champion.json` field `champion.flops_used` (30109415000.58) is mislabeled: lead audit
  2026-07-16 recomputed the B0 monte-carlo-mini raw report and that
  value is the mean per-MLP `effective_compute`; the champion's true
  mean raw `flops_used` is 2.734618e+10. Fix by renaming the field to
  `mean_effective_compute` and adding `flops_used: 27346176000.0`
  (values from
  `experiments/results/gpt/B0-gpt-20260716T002459Z-a6fca1e-monte-carlo-mini.json`),
  citing this audit. Values themselves are correct and match the raw
  report; only the label is wrong. Do not change any other champion
  fields.
  Done exactly as specified: renamed to `mean_effective_compute`, added
  correct `flops_used: 27346176000.0`, no other champion fields touched.

- [x] **B37** (exploit) - DONE gpt 2026-07-16T20:38:55Z (rejected) - Radial-exact antithetic directions. Combine B25's
  exact integration over the Gaussian radius with B4's direction pairing:
  draw 3,250 iid sphere directions, forward both `u` and `-u`, and multiply
  their 6,500-sample angular mean by the exact chi-radius mean. B4 measured a
  noisy 6.6% adjusted-score improvement from antithetics before radial
  exactness, while B25 independently removed radial variance; test whether
  composing the two variance reductions makes the final-layer gain reliable
  at bit-comparable FLOPs. Promote only by the standard paired Mini gate.

- [x] **B41** (exploit) - DONE gpt 2026-07-16T22:17:24Z
  (feasibility-rejected) - Partial-Haar
  orthogonal direction blocks for the B25 radial-exact champion. B22 proved
  that full 256-row Haar blocks lower final-layer MSE by 5.5%, while B40
  proved their dense QR wall time makes the adjusted score worse. Test
  thinner k-row Haar frames (k in {16, 32, 64, 128}) whose reduced-QR cost
  falls with k while retaining part of the negative-dependence gain. First
  measure MSE and wall-time/effective-compute tradeoffs on 10 canonical Mini
  MLPs with multiple seeds; run the standard paired 100-MLP Mini harness only
  if a k has a clear predicted adjusted-score advantage over radial-iid.
  Result: REJECTED at the predeclared 10-MLP, four-seed feasibility gate.
  Only k=64 lowered repeated-seed MSE (-3.39%), but its batched reduced QR
  added ~0.48s and raised estimated effective compute 2.60x, for a predicted
  adjusted-score regression of +151.23%. The cheapest candidate, k=32,
  increased MSE 10.16% and predicted adjusted score 23.82%. A strict official
  100-MLP pair was subsequently run: candidate score=2.069260e-06 vs champion
  7.881070e-07 (+162.56%), paired mean delta=+1.281153e-06, conservative 95%
  CI=[+8.625544e-07,+1.699752e-06], 87/100 regressed, and all failure flags
  zero. See `experiments/log-gpt.md` and
  `experiments/results/gpt/B41-gpt-20260716T220957Z-2227ef3-paired-summary.json`.

## Done

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
  2026-07-16: the B0 champion is plain MC at Câ‰ˆ3.01e10 > the 2.72e10 floor,
  so its adjusted score is approximately N-invariant (MSEâˆ1/N cancels
  against multiplierâˆN). Any variance reduction divides the score directly,
  and faster-than-`N^(-1/2)` error decay makes the score fall with N all the
  way up to the full 2.72e11 budget â€” the largest and cheapest expected win.
  Result: input-level antithetic pairing (z, -z) at unchanged FLOPs was
  REJECTED â€” mean paired delta negative (-6.3e-08, -6.6% relative) but the
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
  Deterministic estimate (best available analytic method â€” post-B1 core if it
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
  Result: REJECTED â€” implemented and validated the exact correction (Price's
  theorem + arccos-substitution quadrature; matched brute-force Monte Carlo
  to ~1e-4 across 13 test cases). Official Mini score (8.4606e-06) is
  statistically indistinguishable from the B0-era gain-product
  approximation's own score (8.3663e-06) it replaces â€” confirmed via a
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


- [x] **B10** (exploit) - DONE claude 2026-07-16T06:15:00Z - Batched
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
  Result: REJECTED (paired 95% CI not entirely below zero) but real,
  quantified progress: final_layer_mse matches B1's to 6 significant
  figures (confirms mathematically identical estimator), matmul calls
  dropped 1,360->353, effective_compute/flops_used ratio dropped
  1.464->1.307 (champion=1.186), relative regression dropped from B1's
  +20.7% to +8.6%, and paired_mean_delta dropped from B1's 1.966e-07 to
  8.176e-08 (58% smaller). The remaining ~321 extra calls vs. champion's
  32 come from two still-unbatched phases (256 power-iteration
  matrix-vector products, 32 diagonal-soft-gate matmuls). See
  `experiments/log-claude.md` and
  `experiments/results/claude/B10-claude-20260716T060000Z-1598169-summary.json`.
  Follow-up queued as B11.


- [x] **B11** (exploit) - DONE gpt 2026-07-16T04:44:30Z - Finish batching B10's active-subspace GH
  quadrature estimator. B10 cut B1's call-overhead penalty roughly in
  half (matmul calls 1,360->353, effective_compute/flops_used ratio
  1.464->1.307) purely by batching the main 16-node quadrature sampling
  into one matmul-per-layer pass, with zero change to the underlying
  accuracy (final_layer_mse matched B1's original to 6 significant
  figures) -- but the paired CI still isn't entirely below zero. The
  remaining overhead is two still-unbatched phases: 256 power-iteration
  matrix-vector products (4 iterations x 32 layers x 2 traversals) and 32
  diagonal soft-gate propagation matmuls. Hypothesis: folding these into
  far fewer, larger calls (e.g. batch the power-iteration vector ops, or
  algebraically combine the diagonal soft-gate steps) closes the rest of
  the gap from ratio 1.307 to the champion's ~1.186 without changing the
  statistical estimator at all, which -- if B10's accuracy gain survives,
  as it already has once -- should push the paired mean delta entirely
  negative and produce the first promotable champion since B0.


- [x] **B12** (exploit) - DONE claude 2026-07-16T07:10:00Z - Two-direction
  active-subspace antithetic quadrature. B1/B10 use only the single top
  power-iteration direction (AGENTS.md: depth-32 covariance is "often
  rank-1 dominated", not purely rank-1). Checked B9's raw per-MLP data
  first (no claim needed, B9 is DONE): even the 73/100 MLPs that didn't
  crash from B9's float32-before-ppf bug scored ~27x worse MSE than
  champion on average (0/73 better) -- confirms full-ambient-space
  QMC/Sobol is a genuine statistical dead end here (consistent with
  B4/B7/B8's finding that depth-32 collapse destroys input-level
  structure), not just an implementation bug, so a bug-fixed Sobol retry
  is not worth queuing. Pivoting instead to a direction complementary to
  gpt's claimed B11 (which targets call-overhead only, same 1-D
  estimator): deflate a second power-iteration direction orthogonal to
  B1/B10's dominant direction, and instead of a second quadrature (avoids
  needing to source/verify new GH constants under time pressure), use a
  cheap 4-way antithetic split -- (+d2,+resid), (-d2,+resid), (+d2,-resid),
  (-d2,-resid) -- on the two independent orthogonal-complement components
  in place of B1/B10's single +-noise antithetic pair, at roughly the same
  total sample budget (half as many base draws, 4 variants each instead of
  2). All 4 variants share the same expectation by the same symmetry
  argument as plain antithetic pairing, so this stays unbiased. Hypothesis:
  if rank-1 dominance is imperfect, explicitly capturing the 2nd direction
  reduces residual variance beyond B1/B10's single-direction quadrature.
  Result: REJECTED, decisively (paired 95% CI wholly positive, not just
  straddling zero). Regressed on BOTH axes vs. B10: final_layer_mse 46%
  worse (1.171e-05 vs B10's 7.995e-06, also worse than champion's
  8.505e-06), and overhead also worse (matmul calls 353->610,
  effective_compute/flops_used ratio 1.307->1.368, since running power
  iteration twice roughly doubles that phase). Diagnosis: halving
  independent base draws to afford the 4-way split traded away more
  variance reduction than the second direction recovered -- the deflated
  "second direction" is closer to arbitrary residual noise than genuine
  signal, i.e. rank-1 dominance really is strong here. Fourth distinct
  technique (after B4/B7/B8) confirming only the single top active-subspace
  direction carries usable structure at depth 32. See
  `experiments/log-claude.md` and
  `experiments/results/claude/B12-claude-20260716T065000Z-1598169-summary.json`.
  No further multi-direction follow-up recommended.


- [x] **B13** (exploit) - DONE claude 2026-07-16T07:45:00Z - Fewer power
  iterations for B1/B10/B11's active-subspace direction. The B1/B10/B11
  lineage has a real ~6% final-layer-MSE advantage but keeps losing the
  paired gate on `mean_effective_compute` overhead. B11 tried materializing
  the full soft-gate Jacobian to cut power-iteration call count (256->40)
  but the O(width^3) matrix-product cost offset most of the win
  (effective_compute barely moved, 3.5156e10->3.4706e10). B12's failure
  mode (a deflated second direction carried ~no exploitable signal, only
  noise) reconfirmed the covariance is strongly rank-1 dominated --
  meaning the top power-iteration direction should converge in very few
  iterations, not the 4 B1/B10/B11 all used unchanged from the original
  B1 experiment (which never tuned this hyperparameter down). Hypothesis:
  1-2 power iterations already extract a direction with cosine similarity
  near 1.0 to the 4-iteration one, at 1/2 to 1/4 the power-iteration call
  count (256->128 or 64) and zero raw-FLOP increase (same O(width^2)
  matvecs, just fewer of them) -- unlike B11's fix, this doesn't trade
  call-count for bigger individual calls, so the overhead reduction should
  actually reach the champion's ratio this time. Verify direction
  convergence on real dataset MLPs before committing to a specific
  iteration count, then reuse B10's exact batched estimator unchanged
  apart from the iteration count.
  Result: REJECTED (paired 95% CI still not entirely below zero) but real
  incremental progress -- verified on 5 real MLPs that 2 iterations gives
  cosine similarity >=0.9986 to a 6-iteration reference (1 iteration was
  riskier, 0.90 worst case), so used 2. matmul calls 353->225,
  effective_compute/flops_used ratio 1.278->1.266, and final_layer_mse
  was marginally BETTER than B10's (accuracy not traded away). paired_
  mean_delta=6.391e-08, the smallest yet in the B1/B10/B11/B13 lineage
  (B1=1.966e-07, B10=8.176e-08, B11=9.179e-08). The overhead cut was
  smaller than the 36% call-count reduction alone would suggest, since
  the 32 still-unbatched diagonal soft-gate matmuls are untouched and now
  a larger share of the remaining gap. See `experiments/log-claude.md` and
  `experiments/results/claude/B13-claude-20260716T073500Z-1598169-summary.json`.
  Follow-up queued as B14.


- [x] **B14** (exploit) - DONE gpt 2026-07-16T05:35:21Z - Batch the remaining 32 diagonal soft-gate matmuls
  in the B1/B10/B11/B13 active-subspace lineage (`pre_variance = (w*w).T @
  variance`, one call per layer). These are now a proportionally larger
  share of the remaining effective_compute overhead than before B13's
  power-iteration cut (matmul calls down to 225, ratio 1.266 vs
  champion's ~1.19). Unlike the power iteration, this phase is already
  just one sequential pass per layer (no multiple rounds to cut), so
  "batching" here means folding it into the same single matmul as the
  main quadrature sampling pass, or otherwise reducing its per-layer call
  footprint, without changing the diagonal-Gaussian-moment math. If this
  plus B13's cut together close the rest of the gap to the champion's
  ratio while preserving the ~6% MSE edge (confirmed intact through B10
  and B13), the paired mean delta should finally cross entirely below
  zero.


- [x] **B15** (exploit) - DONE claude 2026-07-16T08:20:00Z - Reduce main
  sample count for the B1/B10/B11/B13 active-subspace estimator. Distinct
  from gpt's claimed B14 (batching the fixed-cost diagonal soft-gate
  calls): this targets the dominant raw-FLOP term instead. B13's
  aggregate flops_used (27.49e9) is already close to the champion's
  (27.35e9), and B13's aggregate effective_compute (34.80e9) minus
  flops_used leaves a roughly 7.3e9 "excess" gap that looks driven by
  fixed per-call overhead (independent of how many rows are in the single
  batched main-sampling matmul per layer) rather than by the row count
  itself. The 16-node Gauss-Hermite quadrature already gives *zero*
  sampling variance along the dominant direction -- only the orthogonal
  -complement antithetic draws contribute MC noise -- so this estimator
  should be more sample-efficient per FLOP than plain MC, which has
  sampling variance in all 256 dimensions. Hypothesis: cutting the main
  pair count (currently scaled from 3,250, matching the champion's
  ~6,500-sample budget) by roughly half still gives competitive or better
  MSE than the champion, while roughly halving the dominant raw-FLOP term
  -- net effective_compute should drop meaningfully even though the fixed
  per-call overhead doesn't shrink, unlike B14's approach which shrinks
  the fixed overhead directly. If both B14 and B15 land, they attack the
  two different halves of the same gap.
  Result: REJECTED -- overshot. MSE rose 57% (8.505e-06->1.3376e-05) while
  the multiplier only dropped ~10% (floor-clamped at 0.1), net score 42%
  worse than champion. Confirmed the raw-FLOP lever is real
  (effective_compute dropped from B13's 3.48e10 to 1.83e10) but halving
  pushed effective_compute *below* the 2.72e10 floor, wasting 8.89e9 of
  compute headroom for zero further multiplier benefit while still
  paying the MSE cost. See `experiments/log-claude.md` and
  `experiments/results/claude/B15-claude-20260716T081000Z-1598169-summary.json`.
  Calibrated follow-up queued as B16.


- [x] **B16** (exploit) - DONE claude 2026-07-16T08:55:00Z - Retry B15's
  active-subspace sample-count cut with a precisely calibrated pair-count
  scale (~2,500) instead of a blind halving (1,625), AND combine with
  gpt's B14 elementwise diagonal-variance fix (also independently
  implemented, own file). Linear fit from B13 (pair_scale=3250,
  mean_effective_compute=3.4803e10) and B15 (pair_scale=1625,
  mean_effective_compute=1.8311e10) -- slope ~1.015e7 per unit pair_scale
  -- solving for effective_compute=2.72e10 (the score floor boundary)
  gives pair_scale ~2500. That should land the multiplier at its
  floor-clamped minimum (same as B15, ~0.1) but with ~54% more
  orthogonal-complement samples than B15, recovering most of the MSE B15
  gave up for nothing past the floor. B14 (rejected on its own,
  paired_mean_delta=5.477e-08, the smallest single-lever result yet)
  targets a different, independent overhead source (call fragmentation vs
  raw main-sample FLOPs) -- stacking both in one candidate should combine
  their reductions. If the linear model holds, this should beat B13
  (unused overhead above the floor), B15 (unused
  headroom below the floor) and could be the first candidate in the
  B1/B10/B11/B13/B15 lineage to cross the paired promotion gate. Run
  champion fresh alongside the candidate (not reused) given how close
  this is to the threshold and effective_compute's wall-clock noise.
  Result: REJECTED (CI not entirely below zero) but calibration landed
  almost exactly on target (mean_effective_compute=2.7179e10, within
  0.07% of the 2.72e10 floor). KEY FINDING: paired_mean_delta (5.679e-08)
  essentially TIES gpt's B14 alone (5.477e-08, full N=3250, no reduction)
  -- the N-reduction lever adds ~nothing once the diagonal-matmul
  overhead is already fixed. Explanation: the lead's N-invariance
  argument for plain MC (MSE~1/N cancels multiplier~N above the floor)
  applies equally to this estimator's main sampling budget; the 16-node
  quadrature lowers the *invariant score level* (the ~6% MSE edge) but
  doesn't break the invariance itself. Definitively rules out
  sample-count tuning as a further lever for this architecture. See
  `experiments/log-claude.md` and
  `experiments/results/claude/B16-claude-20260716T084500Z-1598169-summary.json`.
  Follow-up queued as B17.


- [x] **B17** (exploit) - DONE claude 2026-07-16T09:20:00Z (feasibility-rejected) - Since B16 rules out sample-count tuning as a
  lever, the only remaining lever for the B1/B10/B11/B13/B14/B16 lineage
  is cutting the ~128 power-iteration calls further (already reduced
  from 256 in B13). B12's and B16's results both reconfirm strong rank-1
  dominance. Revisit power-iteration convergence on more than the 5 MLPs
  B13 checked -- consider a cheap early-stopping check (e.g. halt once
  consecutive directions' cosine similarity exceeds a threshold) rather
  than a fixed iteration count. If power iteration can be cut further
  without sacrificing direction quality, combine with B14's elementwise
  diagonal fix (validated safe to stack) at the FULL N=3250 budget (not
  reduced, per B16's finding) for the best remaining shot at closing the
  gap to the champion.
  Result: REJECTED before any harness run -- and it's a correction, not
  just a rejection. Rechecked B13's convergence claim across all 100
  Mini-split MLPs instead of 5: at 2 iterations, min cosine similarity is
  only 0.443 (35/100 MLPs below 0.999), and at 1 iteration it's 0.137
  (68/100 below 0.99) -- B13's 5-MLP spot-check (claiming >=0.9986 at 2
  iterations) was not representative; it avoided the ~35 poorly-converged
  MLPs by chance. 4 iterations (B1/B10/B11's original choice) converges
  solidly (min=0.906). Given this, reducing below 2 iterations is clearly
  unsafe -- did not spend a harness run confirming the foregone
  conclusion. Note: B13/B16's own measured aggregate MSE from real
  harness runs was still competitive despite this, so their results
  stand unchanged; this just means the 5-MLP proxy check should not be
  trusted again without a full-dataset recheck. Closes off further
  iteration-count reduction as a lever for this lineage. See
  `experiments/log-claude.md`. No candidate file was needed or committed.


- [x] **B18** (exploit) - DONE claude 2026-07-16T09:45:00Z (inconclusive) - Seeded random
  power-iteration start for the B1/B10/B11/B13/B14 active-subspace
  lineage. B17's full-dataset recheck found 2-iteration convergence is
  poor for ~35/100 Mini-split MLPs (min cosine similarity 0.443) despite
  strong rank-1 dominance overall. Hypothesis: this may not be a
  fundamental convergence-rate problem but an artifact of the fixed,
  deterministic `ones(width)` starting vector -- power-iteration
  convergence rate depends on the initial vector's overlap with the true
  dominant direction, and a single deterministic start could
  systematically have poor overlap for specific weight-matrix structures
  (unlucky alignment), unlike a per-MLP seeded random start whose overlap
  is generically non-degenerate on average. Cheap to test: swap the start
  vector for `fnp.random.default_rng(mlp.seed).standard_normal(width)`
  (consistent with the seeding contract already used elsewhere in these
  estimators) and recheck convergence across all 100 MLPs before touching
  any candidate file. If this closes most of the gap for the
  currently-poorly-converged MLPs, it's a free (zero extra FLOP or call
  cost) accuracy improvement for the whole lineage.
  Result: REJECTED, inconclusive. Tested seeded-random AND a third
  alternating-sign start as a control. All three starting vectors
  (deterministic ones, seeded-random, alternating) show comparable
  aggregate convergence quality (mean ~0.978-0.982) but each fails on a
  *different* subset of MLPs -- seeded-random fixed most of ones-start's
  worst cases (e.g. MLP 46: 0.443->0.908) but introduced a new one (MLP
  57: 0.996->0.275, worse than the original global min). This rules out
  "pick a better start" as a fix: poor convergence for specific MLPs is
  an intrinsic spectral-gap property (near-degenerate top-2 eigenvalues
  for those MLPs -- even the 6-iteration reference itself differs by
  starting vector for some of them), not a fixable initialization
  artifact. See `experiments/log-claude.md`. No candidate file needed.


- [x] **B19** (exploit) - DONE claude 2026-07-16T10:30:00Z - Block
  (multi-vector) power iteration for the active-subspace direction.
  B18 found no single starting vector (deterministic ones, seeded-random,
  alternating-sign) reliably converges well for all MLPs -- each fails on
  a different subset, consistent with some MLPs having a genuinely small
  top-1/top-2 eigenvalue gap. Key insight not yet exploited: batching K
  starting vectors into one (K, width) block and applying the soft-gate
  Jacobian to the whole block costs the *same* number of matmul calls per
  round as a single vector (still one matmul per layer per traversal,
  just with K rows instead of 1) -- unlike gpt's B11 full-Jacobian
  materialization, this stays O(width^2*K) not O(width^3), so a modest K
  (e.g. 4) adds negligible raw FLOPs. Hypothesis: running several
  independent starting vectors simultaneously through the same 2 rounds,
  then picking whichever grew the most (proxy for best alignment with the
  dominant eigenvalue), should recover most of B18's per-MLP wins
  (seeded-random fixed most of ones-start's worst cases) without
  introducing new failures the way any single alternative start did,
  since the block always includes multiple attempts including the
  existing safe default. Validate the selection heuristic's convergence
  across all 100 MLPs before touching any candidate file -- same
  discipline as B13/B17/B18.
  Result: REJECTED, but a genuine and important negative finding, not an
  implementation failure. Pre-implementation validation held up exactly
  (min cosine similarity to eigenvector 0.443->0.823, matching the
  oracle; mean 0.979->0.996; n<0.999 35->9), and the engineering
  mechanism worked precisely as designed (matmul calls stayed at 193,
  flops_used matched B13/B16's range -- zero extra call-count cost from
  K=4 blocking, confirmed). But the much better proxy-metric convergence
  did NOT translate to better real final-layer MSE: candidate scored
  8.361e-06, worse than B13's simpler single-vector result (7.931e-06).
  Ran a full post-hoc bug/confound check (no RNG-state issue, no logic
  bug -- standalone re-derivation matched exactly) before accepting this.
  Closes the power-iteration-convergence sub-thread (B17/B18/B19): cosine
  similarity to the soft-gate Jacobian's eigenvector is not a reliable
  target for this estimator's actual MSE. See `experiments/log-claude.md`
  and `experiments/results/claude/B19-claude-20260716T101500Z-1598169-summary.json`.
  No further follow-up queued in this specific direction -- see log for
  the broader assessment of the B1/B10/B11/B13/B14/B16/B19 lineage.


- [x] **B20** (exploit) - DONE claude 2026-07-16T10:55:00Z (feasibility-rejected) - Stein's-lemma
  pilot-sample direction for the active-subspace estimator. B19 showed
  that better convergence to the soft-gate Jacobian's eigenvector does
  NOT reliably predict this estimator's real final-layer MSE -- the
  soft-gate linearization is itself only an approximation of the true
  nonlinear sensitivity, so further optimizing convergence *to that
  proxy* has diminishing value. Different mechanism, not another tweak:
  for x~N(0,I) and smooth f, Stein's lemma gives E[x f(x)] = E[grad f(x)]
  -- a small pilot batch of REAL nonlinear forward passes (true hard
  ReLU, no soft-gate approximation at all) can directly estimate the
  network's average output-sensitivity direction via
  `mean(x_pilot * y_scalar[:,None], axis=0)` where y_scalar is the summed
  final-layer output per pilot sample. Cheap (~500 pilot samples, ~7.7%
  of the main ~6,500-sample budget) and structurally different from every
  direction-finding approach tried so far in this lineage (B1/B10's
  soft-gate power iteration, B12's deflated second direction, B18/B19's
  alternative starts and block selection) -- none of those used real
  nonlinear samples to find the direction. Reduce the main quadrature
  budget slightly to absorb the pilot cost. Given B19's lesson that a
  convergence-quality proxy didn't predict MSE, skip elaborate proxy
  -metric pre-validation this time (a quick sanity check that the
  direction isn't degenerate is enough) and go straight to a real Mini
  -split harness comparison.
  Result: REJECTED before any harness run. The "quick sanity check" (30
  MLPs, two independent aggregation methods) found the Stein direction
  has mean cosine similarity only ~0.128-0.129 to the soft-gate
  eigenvector reference (30/30 below 0.9) -- not sampling noise (both
  methods agreed closely), but a genuine conceptual mismatch: Stein's
  lemma estimates local gradient sensitivity at/near the origin, while
  the quantity that matters for this quadrature is the dominant
  eigenvector of the depth-32 variance-collapse operator -- a different
  object. Given B4/B7/B8's precedent that near-arbitrary directions don't
  help this problem, did not spend harness compute confirming the
  foregone conclusion. See `experiments/log-claude.md`. No candidate file
  needed. Closes this specific idea; log suggests the right "different
  mechanism" would need to estimate the collapse-operator's eigenvector
  from real hidden-activation covariance, not an input-gradient proxy --
  a bigger undertaking left for a future iteration with fresh scoping.


- [x] **B21** (exploit) - DONE claude 2026-07-16T11:45:00Z - Empirical
  final-layer covariance direction. B20's exact conclusion: the right
  "different mechanism" measures the collapse-operator's eigenvector from
  real hidden-activation covariance, not an input-gradient proxy.
  Concretely: forward a pilot batch of P real samples (true hard ReLU,
  no soft-gate approximation) through all 32 layers, compute the
  empirical covariance of the pilot's *final-layer* activations, and take
  its dominant eigenvector via power iteration on that (width, width)
  matrix. This directly measures the quantity the quadrature construction
  actually needs (the true dominant variance direction at the scored
  layer), not an approximation of it -- addressing both B19's finding
  (soft-gate-eigenvector convergence doesn't predict MSE) and B20's
  (Stein's local-gradient direction targets the wrong quantity entirely).
  Given the old soft-gate-eigenvector reference is no longer trusted as a
  validation target (per B19/B20), validate instead via split-half
  stability: does the direction from pilot samples 1..P/2 closely match
  the direction from an independent pilot batch P/2..P for the same MLP?
  If stable, the pilot size is adequate; if not, either grow P or accept
  the noise and test on the harness directly. The pilot forward pass
  costs real FLOPs (P=300 pilot samples ~= 4-5% of the ~6,500 main
  budget) -- reduce the main quadrature budget correspondingly, and
  consider reusing the pilot batch's own mean as additional MC samples
  rather than discarding it after direction extraction.
  Result: REJECTED, but decisively -- not another dead end, a genuine
  ceiling measurement. Pre-implementation split-half stability check
  (600-sample pilot, two 300-sample halves, 20 real MLPs) confirmed a
  300-sample pilot gives a highly stable direction (cosine similarity
  min=0.9917, mean=0.9973). The resulting candidate achieved
  final_layer_mse=7.897e-06, the BEST in the entire B1/B10/B11/B13/B14/
  B16/B19 lineage (previous best: B13's 7.931e-06) -- confirming the
  empirical-covariance direction really is more accurate than every
  linearized approximation tried. But only marginally (0.43% better),
  and the pilot's real, unavoidable forward-pass compute cost (+4.6%
  raw FLOPs vs B13) outweighs that gain -- worse net score than B13/B14/
  B16 despite the best raw MSE. Notably, matmul calls (86) were FEWER
  than B13/B16/B19's 193 and the overhead ratio (1.251) was BETTER than
  B13/B16's -- so this isn't a call-fragmentation problem, it's a
  fundamental compute-vs-accuracy tradeoff. This is decisive evidence
  the B1/B10 lineage has hit its ceiling for direction-finding
  refinement of any kind: the true best-possible direction barely beats
  the cheap approximation already in use. See `experiments/log-claude.md`
  and `experiments/results/claude/B21-claude-20260716T113000Z-1598169-summary.json`.
  Any future work on this lineage should target the orthogonal
  -complement sampling's own variance, not the direction estimate.


- [x] **B39** (exploit) - DONE gpt 2026-07-16T21:04:54Z (feasibility-rejected) - Fast randomized-Hadamard orthogonal directions
  for the B25 radial-exact champion. B22 showed that exact Haar-orthogonal
  blocks lower aggregate final-layer MSE by 5.5%, but dense QR generation
  nearly triples effective compute. Replace each QR block by a product of
  normalized Walsh-Hadamard transforms and independent seeded Rademacher
  diagonals, which remains exactly orthogonal and costs only O(width^2 log
  width) additions/sign flips per block; use B25's closed-form chi-radius
  mean rather than sampled radii. The structured row marginals only
  approximate uniform sphere directions, so first measure bias and
  seed-variance against the champion on 10 canonical Mini MLPs. Reject
  before the full paired harness if squared bias erases the orthogonality
  variance reduction; otherwise validate and run the standard 100-MLP Mini
  pair.
  Result: REJECTED at the predeclared 10-MLP, six-seed feasibility gate.
  The H-D-H-D-H-D design increased mean replicate MSE by 2.40% and seed
  variance by 2.58% versus radial-iid directions; worst MLP regression was
  +81.35%. Thus the approximate-Haar blocks do not reproduce B22's variance
  reduction, even before considering structured-direction bias. Candidate
  validated, but the 100-MLP paired harness was correctly NOT_RUN. See
  `experiments/log-gpt.md` and
  `experiments/results/gpt/B39-gpt-20260716T205516Z-2227ef3-summary.json`.

