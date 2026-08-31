# Demo Mutation Playbook

**Status:** canonical, per Owner ruling on issue #51 (2026-08-29, "RULING —
Owner, via operator-directed session, after exhaustive search"). A
standalone Demo Mutation Playbook document does not exist anywhere in the
Owner's corpus, GitHub history, or off-GitHub archives — the poison-case
content was authored directly into `docs/PRD-v3.md` §6 during adjudication,
and the citations to a separate document were aspirational. This file
promotes PRD §6 into the document those citations expect: it is now the
canonical instrument the nine (sixteen, at the individual-marker count)
`TODO(playbook)` references point at.

**Escape clause:** if a standalone source playbook later surfaces in the
Owner's off-GitHub archives, it supersedes via `docs/DECISIONS.md`; until
then this file is canonical. No firing invents additional poison cases
beyond the six below without a dogfooded need (L-014/L-015).

**Scope:** exactly the six cases PRD-v3 §6 names for V1's termination lane
— no more, no fewer. Each is implemented in `tests/fixtures/poisons/` and
exercised end-to-end by `scripts/build_demo_engagement.py poisons` through
the real pipeline (lane instantiation → compile gate → collectors →
`reconcile_sets` → typed evaluator), asserted case-by-case in
`tests/test_poison_suite.py`. The headline metric this suite exists to
prove (PRD §7): **assurance defect detection rate == 100%** — every seeded
defect must produce a compile error, `UNKNOWN`, `FAIL`, or a ratified
`EXCEPTION` carrying its disposition ref; a silent `PASS` on a poisoned
case is a build-stopping bug, not a suite failure to be tuned around
(`tests/test_poison_suite.py::test_assurance_defect_detection_rate_is_
100_percent` enforces this exact invariant: `expected.kind != "PASS"`
for every case).

## Case 1 — Contractor absent from HRIS

- **Seeded defect:** `mira.chen@example.com` is a real agency contractor —
  deactivated in Okta (`pvt-0009`) and closed out via offboarding tracker
  ticket `POF-3309` — but carries **no row** in `hris_terminations.json`.
  She was engaged outside the HRIS worker population entirely (a
  vendor-MSA relationship, not an HRIS-tracked employee), so the
  authoritative source the population claim is defined against never had
  her to begin with.
- **Expected detection path:** the set reconciler buckets her as a
  `RIGHT_ONLY` delta (present in the downstream systems, absent from the
  authoritative HRIS side). `RIGHT_ONLY` deltas block the population
  ladder from advancing past `DISCOVERED` to `RECONCILED` until a human
  dispositions them — the existence claim is evaluated against that
  blocked, still-`DISCOVERED` denominator.
- **Expected verdict:** `UNKNOWN`, `unknown_cause: UNKNOWN_POPULATION` —
  never a silent pass on incomplete population data. Disposed after the
  fact in `tests/fixtures/poisons/dispositions.json` (`compensating`:
  escalated to HR as a finding, vendor-MSA boundary review scheduled) —
  the disposition unblocks the *ladder*, it does not retroactively change
  the recorded verdict.
- **Fixture:** `hris_terminations.json` (row omitted),
  `okta_system_log/page-001.json` (`pvt-0009`), `offboarding_tracker.json`
  (`POF-3309`), `dispositions.json` (`email:mira.chen@example.com`).

## Case 2 — Dormant GitHub local account

- **Seeded defect:** Rhea Bell (`rhea.bell@example.com`) is terminated in
  HRIS on `2026-11-16`. `github_members/page_2.json` carries a member
  login `rhea-bell-local` with `sso_identity: null` — a local (non-SSO)
  GitHub account outside the identity provider's reach, so termination
  in HRIS/Okta never automatically revokes it. `identity_map.json` (the
  engagement-ratified local-account ownership register) is the only thing
  that names `rhea-bell-local` as belonging to Rhea Bell at all — without
  it the account would be unattributable, not just unrevoked.
- **Expected detection path:** the non-existence claim asserts that no
  residual GitHub access exists for terminated members. Because
  `rhea-bell-local` is a real, still-active member and the identity map
  resolves it to Rhea Bell, the evaluator can name the exact residual
  access rather than merely flag "something's wrong."
- **Expected verdict:** `FAIL`, naming `rhea.bell@example.com` in
  `support.field_values.residual_access_members` — a residual-access
  finding, not an `UNKNOWN`, because the evidence is complete and
  unambiguous.
- **Fixture:** `github_members/page_2.json` (`rhea-bell-local`,
  `sso_identity: null`), `identity_map.json` (names the owner),
  `hris_terminations.json` (Rhea Bell's termination row).

## Case 3 — Break-glass cloud account, no usable capability

- **Seeded defect:** `breakglass-admin` sits in
  `gcp_service_accounts/page-1.json` as a real service account, but the
  claim that would assert something about it is wired to
  `breakglass.config` — a system with **no entry at all** in
  `registry/capabilities/`. This is deliberately not a data-quality
  problem; it's a claim that names a system the registry has never
  ratified a capability for.
- **Expected detection path:** the type checker refuses to compile the
  claim before any collector runs — a capability-registry miss is caught
  at compile time, not discovered as a runtime data gap. No collector,
  reconciler, or evaluator ever sees this claim.
- **Expected verdict:** `E117` compile error (`"no usable capability
  entry"` naming `breakglass.config`) — never a verdict record. This is
  the one poison case whose "detection" is the *absence* of a
  `verdict_records` entry: `tests/test_poison_suite.py` asserts no record
  exists whose `spec_id` starts with `spec-poison-breakglass`.
- **Fixture:** `gcp_service_accounts/page-1.json` (the account itself,
  present but never reached); the compile error is produced directly from
  the claim/registry mismatch, with no dedicated data fixture beyond that.

## Case 4 — Failed identity join (garbled email)

- **Seeded defect:** `okta_system_log/page-001.json` event `pvt-0003`
  records a deactivation whose `target.alternate_id` is
  `quinn.ash%example.com` — a `%` where the `@` belongs. The canonical
  identity join key (email) cannot be derived from a string with no `@`,
  so the event cannot be attributed to any canonical identity by
  construction, not by a missing lookup.
- **Expected detection path:** the reconciler cannot resolve
  `okta:00u9104`'s target to a canonical member and buckets it
  `UNRESOLVABLE` (distinct from `LEFT_ONLY`/`RIGHT_ONLY` — those describe
  a *resolved* identity missing from one side; `UNRESOLVABLE` describes a
  source record the join step could not even place). Quinn Ash herself
  appears as a separate `LEFT_ONLY` delta (present in HRIS, no resolvable
  revocation evidence downstream) — two distinct deltas from one garbled
  event, not one delta wearing two hats.
- **Expected verdict:** `UNKNOWN`, `unknown_cause: UNKNOWN_EVIDENCE` on
  Quinn's timing verdict — the revocation may well have happened, but no
  evidence attributable to her proves it, so the honest answer is
  "unknown," never a guessed `PASS` or `FAIL`. This is deliberately a
  *different* `UNKNOWN` cause from case 1's `UNKNOWN_POPULATION` — the
  suite's distinctness test (`test_five_verdict_states_and_e117_all_
  visibly_distinct`) checks both causes appear, not just two `UNKNOWN`s.
- **Fixture:** `okta_system_log/page-001.json` (`pvt-0003`, garbled
  `alternate_id`), `hris_terminations.json` (Quinn Ash's termination row),
  `dispositions.json` (`email:quinn.ash@example.com`, `okta:00u9104`).

## Case 5 — Delayed revocation

- **Seeded defect:** Omar Diaz is terminated `2026-10-26` (Monday); his
  Okta deactivation (`pvt-0002`) doesn't land until `2026-11-06`
  (Friday) — 9 business days later, against a 5-business-day timing
  constraint. This is the "everything resolves cleanly, the numbers are
  just bad" case — no ambiguity, no missing data, a plain miss.
- **Expected detection path:** the timing evaluator computes elapsed
  business days between the termination event and the deactivation event
  and compares against the assertion's `constraint_business_days`. Both
  timestamps are unambiguous and both sides of the identity join resolve
  cleanly, so this reaches a definite verdict rather than an `UNKNOWN`.
- **Expected verdict:** `FAIL`, with `support.field_values` recording
  `constraint_business_days: 5` and `elapsed_business_days: 9` — the
  evidence for *why* it failed travels with the verdict, not just the
  fact that it did.
- **Fixture:** `hris_terminations.json` (Omar Diaz, `2026-10-26`),
  `okta_system_log/page-00{1,2}.json` (`pvt-0002`, `2026-11-06`).

## Case 6 — Legitimate exception

- **Seeded defect:** Pia Voss is on a phased offboarding — her Okta
  deactivation doesn't land until `2026-12-01`, 21 business days after
  her termination date, blowing through the 5-day constraint even more
  than case 5's delayed revocation. Unlike case 5, this delay is
  legitimate and pre-approved, not a miss.
- **Expected detection path:** the same timing evaluator that FAILs case
  5 would FAIL this too on elapsed time alone — the thing that makes it
  different is a ratified disposition record
  (`exceptions.json`: `pia.voss@example.com` →
  `dispositions/poisons/pia-voss-phased-offboarding.json`) that the
  evaluator consults before finalizing status. D-V1 (`docs/DECISIONS.md`)
  rules that an `EXCEPTION` must always carry its disposition ref — there
  is no code path that turns a timing miss into a silent `PASS`.
- **Expected verdict:** `EXCEPTION`, `disposition_ref:
  "dispositions/poisons/pia-voss-phased-offboarding.json"` — a fifth,
  visibly distinct verdict state from `PASS`/`FAIL`/`UNKNOWN`/`EXCLUDED`,
  proving the suite exercises all five states plus the `E117` compile
  error across six cases.
- **Fixture:** `hris_terminations.json` (Pia Voss, termination date),
  `okta_system_log/page-00{1,2}.json` (`2026-12-01` deactivation),
  `exceptions.json` (the disposition ref).

## Detection rate

Per PRD §7's headline metric, `tests/test_poison_suite.py::
test_assurance_defect_detection_rate_is_100_percent` recomputes the
summary from the six cases themselves (never trusts a hand-maintained
total): `total == 6`, `detected == 6`, `detection_rate == 1.0`,
`misses == []`, and — the structural guarantee behind the number — no
case's `expected` classification is ever `PASS`. A poison that expected a
silent pass would be a defect in the suite, not evidence the pipeline
works.

## Non-poison board seasoning

Two further fixture entries exist to exercise reconciliation-board buckets
that the six poison cases alone don't reach — not poison cases, and not
governed by this playbook's escape clause:

- Uma Wynn's `worker_type` conflicts between HRIS and the offboarding
  tracker (`CONFLICT` bucket), resolved by ratifying HRIS as authoritative.
- `vik.rao@example.com` is a ratified boundary exclusion
  (`boundary_exclusions.json`, `EXCLUDED` bucket, born dispositioned —
  the human act happened upstream of the engine, which only matches the
  ref, per the boundary-exclusion decision already encoded there).
