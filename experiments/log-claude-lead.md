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
