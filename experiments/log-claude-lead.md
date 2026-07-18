# Experiment log - claude-lead

Append-only. Lead ticks record their Phase 1 review rationale as
`## Lead review <UTC timestamp>` entries and any Phase 2 deep experiment
using the standard template in `AGENTS.md`. Read `log-claude.md` and
`log-gpt.md` from `origin/main` before starting.

## Lead review 2026-07-16T17:08:00Z

First tick under the dedicated `claude-lead` identity (the 2026-07-16
01:55Z and 10:05Z lead reviews predate this worktree and live in
`log-claude.md`). Rebased `lead/claude` onto `origin/main` (33bf5bc at
review start; re-rebased onto 15fa6d2 after the worker's B32 claim and
rejection landed mid-review — see Backlog changes).
Environment on this machine: `uv sync --frozen` clean, whestbench
0.12.0rc3, flopscope 0.8.0rc5 — matches both workers; scores comparable.

### State reconciliation
- Read all three logs, `champion.json`, `BACKLOG.md`, and the recent
  result reports. Shared state is coherent: no claim races, no duplicate
  IDs, logs append-only.
- Submission ledger: NO active `submitting` reservation. The two
  2026-06-11 pre-scaffold entries remain null-ID `pending`
  manual-recovery history; per protocol they stay untouched and must
  never be timestamp-matched.
- **B22** is validly CLAIMED by gpt (claim commit 6b31613, true commit
  time 09:23Z) and actively in progress (candidate committed at
  b0f209d, 16:04Z; no result yet). Not stale; left untouched.
- Recent infra commits on main (53aa15f, 4013f1e, 33bf5bc, 21ab275) are
  the user's scheduler/protocol changes, authored/reviewed outside
  worker ticks — consistent with the protocol-change rule.

### Champion audit (B25 radial-exact MC)
- `estimator.py` is bit-identical to the promotion commit 2227ef3
  (empty `git diff 2227ef3 HEAD -- estimator.py`); `whest validate`
  passes on this machine.
- Math re-derived from scratch and confirmed: for z~N(0,I_d), u=z/||z||
  is uniform on the sphere and independent of r=||z||~chi(d); bias-free
  ReLU nets are exactly positively homogeneous, so
  E[h_l(z)] = E[r]*E[h_l(u)] at EVERY layer (each layer activation is
  degree-1), justifying scaling all 32 rows by the same closed-form
  E[r] = sqrt(2)*Gamma((d+1)/2)/Gamma(d/2), implemented correctly via
  lgamma with d = mlp.width = the input dimension. Seeding follows the
  `default_rng(mlp.seed)` contract. The unreachable legacy
  covariance-propagation code after the `return` is dead but part of
  the B26-gated file identity; deliberately left untouched.
- B26 Full gate (1000/1000, zero failure flags) and B29 paired Full
  comparison re-checked for internal consistency: numbers in
  `champion.json` match the raw-report aggregates cited in the logs.

### Metadata audit findings (recorded, no files rewritten)
1. **Worker log "UTC" labels run ahead of true UTC.** Examples: B31
   labeled 19:30:00Z but committed 16:44Z; B30 labeled 19:00Z,
   committed 16:13Z; B22 claim labeled 12:15Z, committed 09:23Z; B25
   labeled 16:00Z, promotion committed 11:34Z. Ordering is internally
   consistent, so no reconciliation hazard (and the protocol already
   forbids timestamp matching), but commit timestamps are the
   authoritative record. Workers should take UTC from a real clock.
2. **`uv_lock_commit` labels are inconsistent** across result records
   (2c84f3b vs 9b677e2). `git log -- uv.lock` shows the last content
   change to `uv.lock` is 9b677e2 (2026-06-27); 2c84f3b never touched
   `uv.lock`. All 2026-07-16 runs therefore used identical lockfile
   content and identical reported tool versions — no comparability
   issue; results stay immutable, label noted here for the record.

### Policy responses to B29/B30 (lead rulings)
1. **Promotion policy guidance** (B30's request): a Mini paired win
   with a small effect size can be a favorable suite-sampling draw
   (B25's Mini delta was ~16x the Full population mean). Until the user
   ratifies a protocol amendment, lead guidance to workers: treat a
   Mini-gate pass whose relative aggregate improvement is under ~5% as
   PROVISIONAL — promotion is still valid per AGENTS.md, but plan a
   Full paired confirmation before treating it as submission-relevant
   progress, and prefer hypotheses with plausibly larger effects.
   Recommended AGENTS.md amendment (for user review, not applied): add
   a minimum-effect or Full-confirmation clause to step 6.
2. **Submission ruling (unblocks B29's escalation).** B29 correctly
   refused to waive AGENTS.md step 7 unilaterally and asked for a
   lead/user ruling. Ruling: the S1 addendum's second clause — "if all
   previous submitted scores are null, then any scoring solution can
   be submitted" — is a positive permission that covers the FIRST
   scored submission. The step-7 paired Full gate exists to protect a
   previously-submitted baseline; no such baseline exists (B0 was
   never submitted; both 2026-06-11 artifacts are null-scored). B25 is
   not-worse than B0 on the Full split (paired mean -8.7e-09, aggregate
   -1.14%), has a COMPLETE 1000/1000 Full-split record (B26) with zero
   failure flags, and validates cleanly. Therefore the first scored
   submission of the current champion is PERMITTED, under the unchanged
   reservation protocol (unique attempt ID, atomic reservation push,
   hashed artifact, exact-ID reconciliation only). Every SUBSEQUENT
   submission again requires the full step-7 gate, including the paired
   Full comparison against the last submitted champion and the 5% rule
   against the then-non-null `last_submitted_score`. Queued as **S3**;
   `champion.json.submission_readiness` updated to reference this
   ruling.

### Backlog changes (only lead ticks may reorder)
- **B32 race — convergent thinking, resolved by the worker's data.**
  While this review was being drafted, the worker independently queued,
  claimed, AND feasibility-rejected B32 (quadratic control variate on
  the dominant-direction projection, f4c0619/15fa6d2) — the same idea
  this review had drafted as its own B32, plus a t-stratified variant
  (B33). The worker's measurement (corr(f,(u.a)^2)^2 = 0.1-0.4%; t
  explains ~0.2% of directional variance) decisively rejects both:
  neither was queued. The deeper finding — input dependence is diffuse
  across ~255 dimensions, and the 1-D radius (already used by B25) was
  the only low-dimensional input handle — is accepted; the
  direction/subspace family is closed for good.
- **Pushback on B32's "converged" conclusion.** It only covers variance
  reduction via input structure. Two untouched axes queued instead:
  - **B34** (lead-priority 1): inverse-error fusion (precision-weighted
    shrinkage) of the MC champion with the analytic covariance-
    propagation estimate. The analytic error (MSE 8.4e-06, B0/B3) and
    the champion's MC noise (7.2-7.7e-06) are comparable AND
    independent, so a data-weighted convex combination targets a
    ~40-50% MSE cut — an order of magnitude larger than any post-B25
    margin. Distinct from B2's failed per-sample control variate:
    fusion needs no per-sample correlation, only independent errors of
    comparable size, which are already measured.
  - **B35** (lead-priority 2): optimal N under an affine
    effective-compute model — if the ~9% effective-compute excess over
    raw FLOPs has a genuinely fixed (per-call) component b, score
    strictly decreases in N above the floor (a*v/B + b*v/(B*N));
    measure (a, b) cheaply first, close if b~0.
- Queued **S3** (first scored submission, lead-priority 0) — claiming
  it myself as this tick's Phase 2, since it rests on the lead ruling.
- No pruning needed: B0-B32 are all DONE with persisted results; B22
  remains gpt's.

Phase 2 of this tick: claim and execute S3.

## 2026-07-16T17:20:10Z - S3-claude-lead-20260716T171600Z: first scored submission
- Hypothesis: not an estimator experiment — execute the first scored
  submission of the current champion under the Phase-1 lead ruling
  (S1 addendum permits it; no previously-submitted baseline exists for
  the paired Full gate to protect).
- Base champion: B25 radial-exact MC, `estimator.py` @ 2227ef3
  (bit-identical since promotion; re-verified this tick), Full gate
  COMPLETE per B26 (1000/1000, zero failure flags,
  adjusted_final_layer_score=8.507033588741e-07).
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5, uv.lock last
  changed @ 9b677e2; `uv sync --frozen` clean on the claude-lead
  machine; `whest validate` passed.
- Evaluation: no new harness runs — submission gated on the existing
  immutable B26 Full report per the lead ruling.
- Change: packaged `estimator.py` with `whest package` →
  `submissions/S3-claude-lead-20260716T171600Z-2227ef3.tar.gz`
  (sha256 d6c807381092c244e1936e36b8d1e26e5f95ecc7f4a3547b5a258503b27fa7a5;
  packaged estimator.py sha256 verified identical to the repo champion
  via the manifest, aec3ca5b...). Artifact retained locally
  (*.tar.gz gitignored). Reservation pushed atomically (9398a6d) as the
  sole active `submitting` entry BEFORE any network call.
- Result: `whest submit <artifact> --watch --format json` returned
  submission_id=316676, created 2026-07-16T17:18:08Z, status GRADED
  ("Graded successfully"): leaderboard score=6.684538479656953e-07
  (primary), 6.488121769052668e-06 (secondary/MSE). Both are BETTER
  than our local Full-split numbers (8.507e-07 / 7.693e-06) — the
  private evaluation is consistent with, indeed slightly friendlier
  than, our local contract; no adverse-generalization signal.
- Verdict: DONE — first scored submission on the board.
  `last_submitted_score` set to the exact recorded LOCAL Full score
  8.507033588741281e-07 per protocol (leaderboard numbers recorded in
  the ledger entry but not used for the 5% rule). The
  first-submission ruling is spent: every future submission needs the
  full step-7 gate (paired Full vs this champion + >=5% over
  last_submitted_score + reservation).
- Full/submission gate: PASS (per lead ruling); attempt
  S3-claude-lead-20260716T171600Z, submission 316676, graded.
- New ideas queued: none beyond Phase 1's B34/B35 (B34 inverse-error
  fusion is now also the most direct route to a future >=5%-better
  submission).
- Housekeeping note: my own claim-label timestamp for S3 (17:35:00Z)
  was written ahead of the true clock (~17:14Z) — the exact defect
  flagged in this tick's Phase 1 audit. Commit b2c4e3c is
  authoritative; timestamps in this entry are from the real clock.

## Lead review 2026-07-17T01:14:19Z

Second scheduled tick under the `claude-lead` identity. Rebased
`lead/claude` onto `origin/main` (15fd88c) from a clean worktree.
Environment: `uv sync --frozen` clean; whestbench=0.12.0rc3,
flopscope=0.8.0rc5+np2.2.6, uv.lock last changed @ 9b677e2 — matches
both workers; scores comparable.

### State reconciliation
- Read all three logs, `champion.json`, `BACKLOG.md`, and the recent
  result reports (B34–B41). Shared state is coherent: no claim races,
  no duplicate IDs, logs append-only, no items stuck CLAIMED.
- Submission ledger: S3 (attempt S3-claude-lead-20260716T171600Z) is
  `graded` with exact submission_id 316676; `last_submitted_score` =
  8.507033588741281e-07 (local Full) recorded per protocol. NO active
  `submitting` reservation. The two 2026-06-11 pre-scaffold null-ID
  entries remain untouched manual-recovery history.
- gpt's B41 interruption was recovered correctly (recovery addendum
  23:40:45Z, commit 15fd88c): feasibility verdict pushed before the
  supplemental official pair; append-only record intact; verdicts
  consistent.
- Champion audit: `estimator.py` bit-identical to promotion commit
  2227ef3 (`git diff 2227ef3 HEAD -- estimator.py` empty). B25 math
  re-audited last tick; unchanged. B26 Full gate and B29/B30 records
  consistent with `champion.json`.

### Main finding: the backlog is empty and two of its recent
### rejections rest on an instrumentation artifact

All items B0–B41 are DONE. Since B25, every axis was closed by
converging negatives: directions/subspaces (B31/B32), analytic
denoising (B34/B36/B38), sample count (B16/B35), orthogonal blocks
(B22/B39/B40/B41). With nothing claimable, this review audited the
SCORING MODEL ITSELF from the installed harness source (read-only —
no harness modification):

1. `whestbench/budget.py` is the single source of truth:
   `C = flops_used + 1e11 * residual_wall_time_s`, multiplier
   `max(0.1, C/B)`. `flopscope/_budget.py`:
   `residual = wall − backend_time − overhead_time`. Wall-clock of
   INSTRUMENTED fnp ops (backend) is never charged — only their
   symbolic FLOPs. flopscope's own dispatch overhead is not charged
   either. The ONLY charged time is un-instrumented work: user Python
   between ops, allocation/GC, and PLAIN-numpy calls flopscope cannot
   see. Subprocess runner uses the worker's own stats (scoring.py:742),
   so this holds for our official numbers.
2. Champion decomposition (B25 candidate raw report, mean/MLP): wall
   245.5ms = backend 177.3ms (free) + overhead 42.1ms (free) +
   residual 26.1ms → 2.61e9 charged = 9.5% of raw FLOPs. Driving the
   residual toward 0 is worth up to −8.7% adjusted score with
   essentially unchanged predictions (the trivially-promotable B23
   shape). B23 attacked this blind (call counts) and closed the item
   without ever measuring WHERE the 26ms lives; the decomposition
   fields were in every raw report all along. Reopened as **B42**.
3. B22's candidate (b0f209d) generated its Haar blocks with PLAIN
   numpy (`_np.linalg.qr`, `_np` RNG) — so its ~0.5s/MLP of QR +
   radius-sampling wall was charged as residual at 1e11 FLOPs/s
   (the whole +149% penalty), and the QR FLOPs (~1.1e9 for 25 blocks,
   +4.1%) never appeared in flops_used. B22's officially-paired −5.5%
   MSE gain is real; its compute penalty was an artifact of bypassing
   the instrumented namespace. B39 (structured orthogonality, wrong
   direction law) stands on its own merits, but B40's benchmark-based
   "QR wall time is inherent, orthogonal-directions line CLOSED" and
   B41's wall-time-derived 2.60x compute estimates rest on the false
   premise that QR wall is charged. Lead ruling: B40's line-closing
   verdict is WITHDRAWN; the corrected design (fnp.linalg.qr +
   radial-exact, expected net ~−1.5%) is queued as **B43**.
4. Guardrail note for both workers, from the same source audit: NEVER
   call plain `numpy` inside `predict()` for anything nontrivial —
   flopscope cannot see it, and its wall time is charged at 1e11
   FLOPs/s (1ms ≈ 1e8 FLOPs ≈ 0.37% of the champion's C). Everything
   must go through `fnp`/`flops.stats`. Conversely, instrumented ops'
   wall time is free, so wall-clock benchmarks of fnp code are NOT a
   proxy for charged compute — per-MLP report fields
   (`flops_used`/`residual_wall_time_s`) are.

### Backlog changes (lead-only reordering)
- Queued **B42** (lead-priority 1): attribute and reduce the
  champion's 26ms charged residual (−8.7% ceiling, gate-trivial
  shape). CLAIMED claude-lead as this tick's Phase 2.
- Queued **B43** (lead-priority 2): B22's exact-Haar blocks via
  instrumented `fnp.linalg.qr` + radial-exact scaling (−5.5% MSE for
  ~+4% FLOPs, expected net ~−1.5%; submission-relevant only stacked
  with B42). Left unclaimed for a worker.
- No pruning: B0–B41 all DONE with persisted results.

### Metadata notes
- Worker "UTC" log labels continue to run slightly ahead of commit
  times (e.g. claude's B40 labeled 21:30Z, committed 21:39Z-equivalent)
  — ordering still consistent; commit times remain authoritative.
- No coordination problems requiring escalation. Phase 2 proceeds.

## 2026-07-17T01:55:00Z - B42-claude-lead-20260717T011419Z: Minimize the champion's charged residual (PROMOTED)
- Hypothesis: the scorer charges C = flops_used + 1e11*(wall - backend -
  overhead) (verified in whestbench/budget.py + flopscope/_budget.py this
  tick); the champion's ~24-26ms/MLP charged residual is allocator/OS
  memory churn from its float64 13MB per-layer temporaries and can be
  removed without changing the estimator: float32 forward chain (halves
  memory traffic), 650-row chunks (every temporary ~650KB -> allocator
  arena reuse instead of OS churn), float64 accumulation of per-layer
  sums (predictions stay within ~7.7e-08 of the champion because the f32
  forward rounding averages out over 6,500 samples).
- Base champion: B25 radial-exact MC, estimator.py @ 2227ef3 (verified
  bit-identical to promotion this tick); champion Mini reference re-run
  fresh alongside the candidate (not reused).
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5+np2.2.6, uv.lock
  last changed @ 9b677e2; `uv sync --frozen` clean; `whest validate`
  passed on candidate_claude_lead.py.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1
  (sha256 5b00938b...c433), split=mini (100 MLPs), budget=272000000000,
  runner=subprocess, both runs exit 0, JSON reports + stderr persisted
  under experiments/results/claude-lead/.
- Pre-validation (three committed probes, B42-probe*.py): residual
  attribution by phase — RNG draw 0.7ms residual (its 17ms wall is
  uncharged overhead), normalize 0.3ms, 32-layer loop ~41ms f64 /
  ~22ms f32 / ~10-13ms f32-chunked; free-deferral made it WORSE
  (page pressure), confirming churn not frees per se. In-process
  end-to-end: champion 0.1164 multiplier vs candidate 0.1053 (-9.5%).
  MSE sanity on 3 real MLPs: identical to 6 significant digits
  (max |pred diff| 7.7e-08).
- Change: candidate_claude_lead.py @ ed58a93 — same seeded draw, same
  directions, same statistics as the champion; f32 chain, chunk=650,
  f64 sums, scale by closed-form E[r]/n at the end.
- Result: candidate_score=7.623281542134e-07 vs
  champion_score=7.886986699953e-07, relative_change=-3.3435%;
  final_layer_mse 7.210819040324e-06 vs 7.210787749159e-06 (+4.3e-06
  relative, i.e. unchanged; max per-MLP relative MSE change 5.0e-04);
  mean_effective_compute 2.87546e10 vs 2.97460e10;
  paired_mean_delta=-2.637051578190e-08,
  conservative 95% CI=[-3.626087959213e-08, -1.648015197167e-08]
  (tcrit=2.0), 100/100 MLPs improved, worst per-MLP delta -2.590e-09
  (still an improvement), all budget/time/residual/error flags zero.
- Verdict: PROMOTED. The CI is entirely below zero with every single
  MLP improving — the B23 "same predictions, lower multiplier" shape
  realized. Note the realized -3.34% is smaller than the -9.5%
  in-process ceiling: under the subprocess harness the champion's own
  residual is ~24ms (not 41ms), and the candidate floors at ~14ms.
- Full/submission gate: NOT_RUN this tick. -3.34% Mini alone will not
  clear the >=5%-over-last_submitted_score bar; the submission route is
  stacking with B43 (instrumented exact-Haar blocks, expected ~-1.5 to
  -2% net) and/or further residual reduction, then a fresh paired Full
  gate vs the submitted champion per AGENTS.md step 7. Per B30/B29
  precedent the multiplier-only effect is machine-stable and should
  replicate on Full (MSE identical by construction), but the full gate
  must still be run before any reservation.
- New ideas queued: none beyond B43 (already queued this tick's Phase 1).

## Lead review 2026-07-17T09:08:00Z

Third scheduled tick under the `claude-lead` identity (started 09:00:50Z
real clock). Rebased `lead/claude` onto `origin/main` (c81496b) from a
clean worktree. Environment: `uv sync --frozen` clean;
whestbench=0.12.0rc3, flopscope=0.8.0rc5, uv.lock last changed @
9b677e2 -- matches both workers; scores comparable.

### State reconciliation
- Read all three logs, `champion.json`, `BACKLOG.md`, and the recent
  result reports (B42/B43/B44). Shared state is coherent: no claim
  races, no duplicate IDs, logs append-only, no ambiguous reservations.
- Submission ledger: S3 remains `graded` with exact submission_id
  316676; `last_submitted_score` = 8.507033588741281e-07 (local Full).
  NO active `submitting` reservation. The two 2026-06-11 null-ID
  pre-scaffold entries remain untouched manual-recovery history.
- **B46** is validly CLAIMED by gpt (claim commit 1381f00, 06:42Z) and
  actively in progress: the gpt scheduler recovery profile preserved a
  candidate checkpoint at c81496b (07:55Z). Not stale (~1h old at
  review time); left untouched. B46 (shared-Haar signed-orbit blocks)
  is complementary to, not conflicted with, B45 below: if B45 promotes
  a stacked B42+B43 champion, B46's baseline shifts and the CAS
  promotion protocol protects the race as usual.
- Champion audit: `estimator.py` bit-identical to promotion commit
  013df29 (empty diff); `whest validate` passes on this machine. B42
  math was derived and audited at promotion (last tick);
  `champion.json`'s B42 record matches the persisted B42 summary/raw
  reports.

### B44 audit (basis for the B45 ruling)
Independently recomputed both paired gates from the raw per-MLP data in
`B44-...-B43-full-COMPLETE.json` vs `B26-...-full-COMPLETE.json`
(1000 unique `mlp_name`s, exact match across reports; zero failure
flags on every row):
- MSE: paired_mean_delta=-1.6419e-06, CI(t=2.0)=[-2.208e-06,-1.076e-06],
  -5.80 sigma, 611/1000 improved, median -7.29e-07, 10%-trim
  -1.054e-06, excl-best-2 -1.525e-06. Aggregate 7.6925e-06 ->
  6.0506e-06 (-21.34%).
- Adjusted score: paired_mean_delta=-1.5023e-07,
  CI=[-2.142e-07,-8.628e-08], -4.70 sigma, 597/1000, median -6.69e-08.
  Aggregate 8.5070e-07 -> 7.0047e-07 (-17.66%). Matches B44's summary.
- Sensitivity to the champion-baseline choice: B44 paired against B26's
  report (B25 multipliers), but today's champion (B42) has a lower
  multiplier. Rescaling the champion's per-MLP effective compute by the
  B42/B25 Mini ratio (0.95987, re-floored at 0.1) still gives
  mean=-1.161e-07, CI=[-1.784e-07,-5.381e-08], -3.73 sigma, 573/1000,
  aggregate -14.22% -- the gate passes even against a simulated-B42
  baseline, while the actual B45 rebuild will do better than the tested
  candidate (it inherits B42's residual cut, which the B44 candidate
  did not have).

### LEAD RULING: B45 promotion override GRANTED (conditions below)
AGENTS.md step 4 gates promotion on the Mini paired CI to prevent
noisy, unpaired, or suite-sampling-overfit promotions. B44's evidence
satisfies that intent with strictly stronger statistics than the rule
itself demands: a PAIRED comparison with conservative 95% CI entirely
below zero on the 10x-larger independent Full split (-4.7 sigma
adjusted, -5.8 sigma MSE), broad rather than outlier-driven (negative
median, survives 10%-trim and excl-top-2), zero failure flags, and a
diagnosed mechanism for the Mini false negative (fat-tailed per-MLP
deltas at n=100 -- the inverse of B30's over-promotion case). Like the
S3 ruling, this resolves a case the mechanical rule mis-handles without
amending the protocol text. Conditions imposed on execution (this
tick's Phase 2):
1. The actual promotion candidate (B43's directions rebuilt on B42's
   residual-minimized forward) must be evaluated FRESH on the complete
   Full split -- its own 1000-MLP record, not an extrapolation -- and
   pass the paired Full gate (CI entirely below zero) against B26's
   submitted-champion baseline; report the simulated-B42-baseline
   sensitivity as well.
2. A standard Mini pair must still be run and recorded first (expected
   to CI-straddle; it also sanity-checks flags, FLOPs, and validity).
3. Promotion via the standard CAS proposal citing B44 + the fresh Full
   evidence and this ruling.
4. Submission only via the unchanged step-7 protocol: >=5% over
   last_submitted_score 8.507033588741281e-07 on the fresh Full record
   (expected ~-17%), reservation before any network call, exact-ID
   reconciliation.
Methodology recommendation for the user (not applied to AGENTS.md): add
a Full-confirmation path to step 4 for candidates with large aggregate
Mini improvements that fail only on CI width.

### Backlog changes (lead-only reordering)
- **B45** marked CLAIMED claude-lead (this tick's Phase 2) with the
  ruling recorded; it stays lead-priority 0. Everything else unchanged;
  B46 remains gpt's.
- No pruning: all other items DONE with persisted results.

No coordination problems requiring escalation. Phase 2 proceeds.

## 2026-07-17T10:40:00Z - B45-claude-lead-20260717T090826Z: B43-on-B42 stacked rebuild, Full-gated per lead ruling (result persisted pre-promotion)
- Hypothesis: rebuilding B43's exact-Haar orthogonal directions on B42's
  residual-minimized forward keeps B44's robust Full-split variance
  reduction (predictions carry over up to f32 rounding) while recovering
  most of the un-stacked candidate's residual penalty; per the B45 lead
  ruling (this tick's Phase 1), promotion gates on fresh Full paired
  evidence because the Mini gate false-negatives this fat-tailed effect.
- Base champion: B42 residual-minimized radial-exact MC, estimator.py @
  013df29 (bit-identical since promotion; validates).
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5, uv.lock last
  changed @ 9b677e2; `uv sync --frozen` clean; `whest validate` passed
  on candidate_claude_lead.py @ 90fa580.
- Evaluation: dataset=hf://aicrowd/arc-whestbench-public-2026@v1-phase1
  (sha256 5b00938b...c433), budget=272000000000, runner=subprocess.
  Mini: both sides fresh via official CLI, exit 0, zero failure flags.
  Full: B26's validated chunked driver (B45-full-driver.py; the
  seed_protocol_version weakref fix), ten sequential foreground 100-MLP
  chunks; MANDATORY correctness check re-run for this new estimator
  first -- chunked full[0:20] and mini[0:30] final_layer_mse matched the
  official CLI to the exact last printed digit.
- Pre-validation probe (B45-probe1.py): candidate predictions match
  B43's candidate within 8.8e-08 across all 32 layers on 3 real Mini
  MLPs; in-process residual 44-45ms (B43) -> 15-17ms (B45) vs champion
  13-14ms.
- Change: candidate_claude_lead.py @ 90fa580 -- B43's direction
  construction verbatim (25 exact-Haar QR blocks + 100 iid rows, same
  rng order) + B42's forward (f32 weights, 650-row chunks, f64 sums,
  closed-form E[r] scale).
- Result (Mini, recorded per ruling condition 2): candidate 6.0535e-07
  vs champion 7.6128e-07 aggregate (-20.48%); MSE -24.24%; paired CI
  [-4.131e-07, +1.012e-07] straddles zero at 50/100 -- the exact
  fat-tail false-negative shape B44 diagnosed; zero failure flags.
- Result (Full, 1000/1000, zero failure flags): adjusted
  6.746212708916e-07, final_layer_mse 6.050641874367e-06,
  mean_effective_compute 3.03302e10 (+0.83% over B26's champion record;
  the un-stacked B44 candidate paid +4.56%). Paired vs B26 submitted
  baseline: adjusted mean delta -1.7608e-07, CI(t=2.0)
  [-2.3889e-07, -1.1328e-07] entirely below zero (-5.61 sigma), 605/1000
  improved, median -7.69e-08, robust to 10%-trim and excl-best-2; MSE
  -5.80 sigma, 611/1000. Sensitivity vs simulated-B42 baseline
  (champion effective compute rescaled by 0.95987, refloored): -4.65
  sigma, 592/1000, aggregate -17.38%. Prediction carryover confirmed:
  per-MLP MSE vs B44's B43 record max rel diff 5.2e-04 (f32 rounding,
  B42-precedent magnitude).
- Verdict: PASS per the B45 lead ruling -- all four ruling conditions
  satisfied. Proceeding to CAS promotion and then the step-7 submission
  protocol (Full adjusted -20.70% vs last_submitted_score
  8.507033588741281e-07, 4x the 5% bar).
- Full/submission gate: Full COMPLETE (report
  B45-claude-lead-20260717T090826Z-013df29-full-COMPLETE.json); this
  commit persists the result BEFORE promotion per AGENTS.md step 5.
- New ideas queued: none (B46 already covers the QR-FLOP reduction
  follow-up).

## 2026-07-17T11:00:00Z - B45 race addendum: promotion preempted by B46; fallback path recorded
- While B45's Full chunks were running, gpt promoted B46 (shared-Haar
  signed-orbit on B42's forward, commit b42e05c) through the standard
  Mini paired gate (CI [-4.476e-07,-6.436e-09] entirely below zero,
  55/100, zero flags -- a valid promotion) and the claude worker claimed
  B47 (B46's Full gate). The AGENTS.md step-6 CAS re-check therefore
  fails for B45: the champion changed since evaluation and there is no
  evidence B45 beats the NEW champion. Free per-MLP Mini MSE pairing
  (B46 candidate report vs B45 candidate report, same 100 canonical
  MLPs; MSE is machine-independent): B46 better on 57/100, median
  -3.36e-07, 10%-trim -2.91e-07, aggregate -8.17% MSE, AND -3.87%
  flops_used (one QR vs 25). CI straddles (t=-0.76, the usual n=100
  fat tails) but every robust indicator favors B46. Promotion of B45
  is ABANDONED, not merely deferred, unless B47 overturns this.
- B45's stale promotion intent was discarded per protocol (only the
  unpushed proposal; the candidate/result commits are preserved). No
  reservation was made; no submission attempted.
- DECISION TREE recorded for B47 (binding lead guidance, extending the
  B45 ruling):
  1. If B46's COMPLETE Full record (B47) confirms robustness and its
     paired Full comparison vs B45's COMPLETE record (both by mlp_name;
     B45 report: experiments/results/claude-lead/
     B45-claude-lead-20260717T090826Z-013df29-full-COMPLETE.json) shows
     B46 not-worse, then B46 stands as champion and SHOULD BE SUBMITTED
     under the unchanged step-7 protocol (its expected Full adjusted
     ~5.3-6.7e-07 clears the 5% bar vs 8.507e-07 by a wide margin).
  2. If B46's Full record shows its Mini win was a B30-style favorable
     draw AND the paired Full comparison favors B45 with CI entirely
     below zero, the B45 lead ruling AUTHORIZES promoting the
     Full-verified B45 candidate (candidate_claude_lead.py @ 90fa580 on
     this branch history) via standard CAS citing the two COMPLETE
     reports, followed by step-7 submission.
  3. Either way the loser remains a documented building block; do not
     discard the B45 record.
- Note for the record: B45's Full evidence remains the strongest
  verified result to date (adjusted 6.7462e-07 = -20.7% vs
  last_submitted, -5.61 sigma paired vs the submitted baseline). B46
  plausibly exceeds it (-30% Mini aggregate at lower FLOPs) -- the
  B44-style Full confirmation (B47) is the right next step and is
  already claimed by the worker. No further lead action this tick.

## Lead review 2026-07-17T17:07:00Z
- Synced: lead/claude rebased onto origin/main @ 3b5aa43 (fast-forward,
  12 new commits since last lead tick). Worktree clean before and after.
- Reviewed all three logs, champion.json, BACKLOG.md, and the recent
  result reports (B47/B48/B49/B50 summaries; B50 GS-full-COMPLETE
  metadata). Events since the last lead tick: gpt's B46 promotion stood;
  B47 gave B46 a decisive Full gate PASS (-23.2% vs last_submitted,
  -6.0 sigma); S4 submitted B46 per my B47 decision-tree branch 1 and
  AICrowd ACCEPTED it (submission_id 316800) but grading FAILED
  ("Error : Evaluation error", score null); B48 diagnosed the failure as
  AICrowd-environment-specific (not locally reproducible under any
  runner/flopscope mode; artifact has no requirements pin; prime suspect
  fnp.linalg.qr, the standout op vs the successfully-graded S3); B49
  built a QR-free classical-Gram-Schmidt orthogonal frame that matches
  B46's Mini MSE exactly (ratio 1.0005) using only S3-graded ops; B50
  gave the GS candidate its OWN complete 1000-MLP Full gate: PASS
  (adjusted -20.1% vs last_submitted 8.507e-07, CI entirely below zero
  at -5.16 sigma, MSE -5.40 sigma, zero failure flags). The user then
  recorded S5 (2026-07-17T16:41Z, commit 3b5aa43): authorization for
  exactly ONE submission attempt of this exact GS candidate.
- Submission-ledger reconciliation: S4 is fully reconciled by EXACT id
  (submission_id 316800, status failed, last_submitted_score correctly
  UNCHANGED at 8.507033588741281e-07 from S3). Zero active `submitting`
  reservations. The two 2026-06-11 pre-scaffold null entries remain
  manual-backfill items (unchanged, correctly never auto-matched).
- Candidate identity audit (important clarification for the record):
  "f54b23b" in B49/B50/S5 is the BLOB hash of candidate_claude.py
  (git hash-object), NOT a commit SHA -- there is no commit f54b23b
  containing the file. Verified: candidate_claude.py at origin/main
  HEAD (3b5aa43) hashes to exactly f54b23bb9ca6952b63e3c8293153107ba0408837
  and contains the B49 Gram-Schmidt construction. Future references
  should say "blob f54b23b" to avoid ambiguity. Cosmetic finding: the
  file's top docstring still describes B46's shared-Haar-QR variant
  (stale); the B49 change is documented at the construction site
  (lines 47-49). Not edited -- worker claude owns that file; flagged
  here instead. Grading is unaffected by comments.
- Math audit of the GS candidate (lead check before spending the S5
  attempt): classical Gram-Schmidt of a Gaussian matrix with positive
  normalization IS the QR decomposition under the positive-diag(R)
  convention, so Q is exactly Haar-distributed -- B46's explicit
  sign-correction q*sign(diag(r)) is subsumed, not lost. Rows of a Haar
  orthogonal matrix are exactly uniform on the sphere; independent
  seeded Rademacher column sign flips preserve Haar marginals; hence
  every one of the 6,500 directions is uniform and the radial-exact
  estimator stays unbiased. E[r] = sqrt(2)*Gamma((d+1)/2)/Gamma(d/2) is
  the correct chi(d) mean. Seeding via fnp.random.default_rng(mlp.seed);
  no plain numpy in the sampling path; no print/filesystem. B49 verified
  orthonormality (7.5e-13) and ~uniform marginals empirically. Sound.
- Reproducibility audit: this machine reports whestbench 0.12.0rc3 /
  flopscope 0.8.0rc5+np2.2.6, uv.lock last changed @ 9b677e2 -- exactly
  the B50/champion contract. `uv sync --frozen` clean;
  `whest validate --estimator candidate_claude.py` passes.
- Backlog rulings: S5 is the top item and I am claiming it for Phase 2
  (it is explicitly claimable by a lead review tick). No reordering
  needed otherwise: every other item is DONE with persisted results; no
  pruning; the queue below S5 is empty of unclaimed research items, so
  workers should add new ideas next tick regardless of the S5 outcome.
  Post-S5 guidance recorded now (binding until the next lead tick):
  (1) if GS GRADES, the qr-hypothesis is confirmed for practical
  purposes; promote GS as champion of record per B50/S5 and treat
  fnp.linalg.qr (and untested exotic linalg ops) as unsubmittable until
  proven otherwise; queue an idea to recover GS's +4% multiplier gap
  (e.g. blocked/vectorized GS with fewer Python-loop iterations).
  (2) if GS ALSO FAILS grading, do NOT resubmit anything without a new
  user ruling; queue diagnosis toward B48 options (a)/(b) (transient
  test / requirements-pin repackage) as LEAD-decision items only.
- Phase 2: proceeding to execute S5 as a submission tick under the
  unchanged step-7 reservation protocol (package blob f54b23b as-is,
  sha256, sole-active reservation pushed BEFORE any network call, exact
  attempt-id S5-claude-lead-20260717T170700Z, no automatic retry of any
  ambiguous outcome). On a successful grade: set last_submitted_score to
  the exact B50 local Full score 6.7972266077423043e-07 and promote GS
  over the ungradeable B46 via standard CAS citing S5/B50. On a failed
  grade: record by exact id and stop.

## 2026-07-17T17:20:00Z - S5-claude-lead-20260717T170700Z: GS submission attempt -- grading FAILED identically; qr-hypothesis REFUTED
- Hypothesis (S5 user ruling + B49/B50): the B49 QR-free Gram-Schmidt
  candidate reproduces the orthogonal -21% win with only S3-graded ops;
  submitting it either grades (realizes ~-17% leaderboard, confirms qr
  caused S4) or fails (qr was not the cause).
- Base: candidate_claude.py = git blob f54b23bb9ca6952b63e3c8293153107ba0408837
  (verified by hash-object at origin/main 3b5aa43; packaged estimator.py
  bit-identical). NOT the estimator.py champion (B46, ungradeable-in-practice).
- Environment: whestbench=0.12.0rc3, flopscope=0.8.0rc5+np2.2.6,
  uv.lock@9b677e2; `uv sync --frozen` clean; validate + validate-package OK.
- Evaluation: no new local runs needed -- B50's COMPLETE 1000-MLP Full
  gate (adjusted -20.1% vs last_submitted, CI [-2.360e-07,-1.060e-07]
  entirely below zero, -5.16 sigma, zero flags) satisfies step 7 under
  BOTH the old 5% rule and the newly relaxed significance-only rule
  (user ruling commit 6c81bd2, landed mid-tick and re-checked).
- Execution (protocol-exact): packaged via `whest package --estimator
  candidate_claude.py` -> submissions/S5-claude-lead-20260717T170700Z-
  GS-f54b23b.tar.gz (sha256 cda55d67c44fb86b1257178f456a0780f5f53528b9
  cc8d2d90b909771d1726bf); ledger reservation pushed atomically as the
  SOLE active submitting entry (commit 6d0f46b) BEFORE any network call;
  then `whest submit <artifact> --watch --format json --description
  "S5-claude-lead-20260717T170700Z B49-claude-20260717T103000Z"`.
- Result: ACCEPTED, submission_id 316855 (server created_at
  2026-07-17T17:05:15Z; local clock ~5-7 min ahead of server, same drift
  S3 noted). Grading FAILED: "Error : Evaluation error", score null --
  the IDENTICAL signature as S4 (B46, 316800). Ledger updated by exact
  id (submitting -> failed); NOT retried; S5 authorization consumed;
  last_submitted_score UNCHANGED (8.507033588741281e-07, S3).
- KEY INFERENCE: the failing candidate contains NO fnp.linalg.qr, so the
  S4 qr-hypothesis is REFUTED. Remaining suspects = what S4/S5 share
  that graded S3/B25 lacks: (a) B42's float32 chunked forward
  (astype(float32), 650-row chunks, per-layer fnp.sum(axis=0,
  dtype=fnp.float64)); (b) frame-construction ops (fnp.where signs,
  broadcast multiply, fnp.concatenate, per-iteration fnp.stack in the
  256-step GS loop); (c) a grader-side resource/time limit both frame
  builds trip. Note: `whest package --requirements` is documented
  deprecated/ignored ("the grader installs no third-party packages"),
  so B48 option (b) (version pinning) is INFEASIBLE -- bisection by
  minimal diagnostic submissions is the only direct probe available.
- Verdict: submission FAILED grading; conditional GS promotion (S5) NOT
  executed; B46 remains local champion of record; leaderboard remains
  S3/B25 (6.6845e-07).
- Full/submission gate: Full PASS (B50, pre-existing); submission
  attempt 2/10 of the UTC day; reservation opened and closed by exact
  id within this tick.
- New ideas queued: B51 (lead-authorized diagnostic submission of the
  B42 estimator @ 013df29 -- bisects forward-vs-frame-ops; hypothesis
  and both outcome branches recorded in the item per the new diagnostic
  provision) and B52 (desk audit of exact fnp op-set deltas between the
  graded and failing artifacts, cross-checked against the installed
  flopscope/whestbench grader-relevant registries, to rank suspects and
  minimize further diagnostic attempts).

## Lead review 2026-07-18T01:03Z
- Rebase onto origin/main clean (b9790a4). Worktree clean, branch lead/claude.
- Ledger reconciliation (exact-id only): B51-claude-20260717T180000Z ->
  submission_id 316871 GRADED (6.9403e-07), recorded correctly; S5 (316855)
  and S4 (316800) remain `failed`; S3 (316676) `graded`. ZERO active
  `submitting` reservations. The two 2026-06-11 pre-scaffold entries remain
  `pending` with no submission_id -- per AGENTS.md these are manual-recovery
  items (user backfill from the submissions board); left untouched, as in
  every prior review.
- Daily cap: S4/S5/B51 all fell on UTC 2026-07-17 (3 attempts). It is now
  UTC 2026-07-18 -> 0/10 used today (also true under the known ~5-7 min
  server clock drift, checked before any submit below).
- Champion audit: champion.json still records B46 (gpt, blob c81496b),
  metadata internally consistent with its result report, but B46 is
  UNGRADEABLE in practice (S4 failure). last_submitted_score
  8.507033588741281e-07 (S3/B25 local Full) correctly unchanged after the
  B51 diagnostic (B51 graded WORSE than S3, so the S3 baseline stands).
- B53 audit (the submission-ready candidate): blob verified --
  candidate_claude.py at origin/main hashes to 208dcf5, matching the log,
  summary JSON, and Full report. Math audited: GS-of-Gaussian frame is
  exactly Haar, so rows are exactly uniform sphere directions; per-column
  Rademacher signing preserves Haar marginals; bias-free ReLU positive
  homogeneity justifies the closed-form chi-mean radial factor
  sqrt(2)*exp(lgamma((w+1)/2)-lgamma(w/2)); per-block float64 sums are
  exactly the concatenated-batch sums. Unbiased. Source inspected: live
  code contains NO fnp.concatenate/where/qr/reshape calls (dead analytic
  code below `return` also present in graded S3 -- established harmless).
  Full gate re-checked from the persisted report: adjusted CI
  [-2.059e-07,-7.492e-08] entirely below zero, -4.21 sigma, 546/1000, zero
  failures, -16.5% vs last_submitted. Step-7 prerequisites all PASS.
  Honest caveat (also in the worker log): the 256-iteration GS loop
  (stack-per-iteration) and the q*signs broadcast multiply are not
  individually exonerated by B51; a failure would implicate them.
- Reproducibility: uv.lock last changed @ 9b677e2; `uv sync --frozen`
  clean; whestbench 0.12.0rc3 / flopscope 0.8.0rc5 / numpy 2.2.6 verified;
  `whest validate --estimator candidate_claude.py` PASSES.
- Governance ruling (lead): the post-S5 hold ("no resubmission without a
  new user ruling") recorded by the 2026-07-17T17:07Z lead review was
  explicitly binding only until the next lead tick -- this one. Its
  rationale (grader failure of unknown cause) is resolved: B51's bisect
  proved the forward grader-safe and localized the failure to the frame
  ops, and B53 removes exactly those ops. The step-7 STANDING user
  authorization (commit 6c81bd2) therefore applies: all gate conditions
  are met, so a lead submission of B53 needs no fresh per-submission user
  ruling. Hold SUPERSEDED; recorded as backlog item S6.
- Backlog rulings: no unclaimed research items and no reordering needed
  (all items DONE with persisted results). Added S6 (submit B53 under
  standing authorization; hypothesis + both outcome branches in the item)
  and claimed it for Phase 2. Workers should continue adding new research
  ideas next tick regardless of the S6 outcome; if S6 grades, the queued
  follow-up is recovering the ~3.6% margin gap to GS (iid tail
  reinstatement via a grader-safe pad, or blocked/vectorized GS).
- Phase 2: proceeding to execute S6 as a submission tick under the
  unchanged step-7 reservation protocol (package blob 208dcf5 as-is,
  sha256, sole-active reservation pushed BEFORE any network call, exact
  attempt-id S6-claude-lead-20260718T010300Z, no automatic retry of any
  ambiguous outcome). On a successful grade: set last_submitted_score to
  B53's exact local Full adjusted 7.102855471943654e-07 and promote B53
  over the ungradeable B46 via standard CAS (same submittability
  precedent as the planned S5/GS promotion). On a failed grade: record by
  exact id, do NOT retry, and queue the remaining-suspect diagnosis
  (GS-loop stack pattern vs broadcast multiply vs resource limit) as a
  LEAD-decision item.
