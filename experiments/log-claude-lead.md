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
