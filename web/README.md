# Aegis web

Next.js 15 frontend for the Aegis assurance compiler — the demo-engagement
surface. CSS Modules on a token sheet extracted from `docs/prototypes/*.html`
(`src/styles/tokens.css`); no Tailwind, no component library. Fonts load via
`next/font/google` (Inter, Space Grotesk, IBM Plex Mono — the prototypes'
families).

## Run

```bash
cd web
npm install        # or npm ci for the locked install
npm run dev        # http://localhost:3000
```

Verify (what CI runs in `.github/workflows/web-verify.yml`, job `web-verify`):

```bash
npm ci
npx tsc --noEmit
npm run build
```

## Layout

- `src/app/` — App Router pages. `/scope`, `/controls`, `/process`,
  `/reconciliation`, `/verdicts`, `/registry`, `/proof` are stubs today; each
  page states the execution-plan task (A3–B4) that fills it in.
- `src/components/` — `AppShell` (two-column shell), `NavTabs` (route tabs),
  `GaugesRail` (sticky right rail), `StubPage`.
- `src/data/` — the data layer. `types.ts` holds the hand-authored
  ontology/artifact types, generated-checked by `bridge.ts` against
  `__generated__/` (C1); `seed/*.json` is the prototype-ported demo data,
  genericized to the invented demo company "Meridian Financial" (scope,
  controls, process lanes, gauges); the engagement data is imported straight
  from `artifacts/demo-engagement/` via the `@artifacts/*` tsconfig path
  (C2) — the pipeline-emitted, drift-tested originals, never vendored
  copies; `index.ts` typed-exports all of it so `tsc --noEmit` structurally
  checks every JSON file against the types. Pages import from `@/data`,
  never from the JSON directly.
- `src/styles/tokens.css` — the single source of color/type/scale tokens.
  Extend it only from a prototype or ratified design, never ad hoc.

## Data contract: `artifacts/demo-engagement/`

The later pages consume the artifact set emitted by the Python pipeline
(`scripts/build_demo_engagement.py`, drift-tested byte-for-byte — do not hand
edit those files, and do not vendor copies into `web/`):

| File | Shape | Consumed by |
| --- | --- | --- |
| `verdicts.json` | array of verdict records (`record_id`, `control_id`, `status`, `population_id`, `evidence_refs`, hashes) | `/verdicts` (B3), `/proof` (B4) |
| `reconciliation.json` | one population: `ladder`, `sources`, `canonical_members`, six-bucket `buckets`, `dispositions`, `counts` | `/reconciliation` (B2) |
| `registry.json` | `entries` (capability entries with `lifecycle` + `history_caveats`), `compile_errors` (E-codes), top-level `note` | `/registry` (B3) |
| `poisons.json` | `cases` + `detection` + embedded `verdict_records` | `/verdicts` mutation scorecard (B3) |
| `contracts.json` | Evidence Quality Contracts keyed by `contract_hash`: five `quality` properties, `supported_assertion_types`, identity fields | `/proof` contract stage (Q14, issue #48) |
| `snapshot.json` | ratified `ManifestSnapshot`: `version`, `lifecycle`, `ratified_by`/`ratified_at`, `blocks` (populations/claims/capabilities/collectors/evidence_contracts) | `/proof` snapshot stage (Q16, issue #47) |

B1 landed hand-authored mocks in `web/src/data/engagement/` matching these
shapes (Meridian Financial cast, synthetic hashes); C2 deleted them and
pointed the imports at the real artifacts above via `@artifacts/*` — the
no-vendoring rule is now honored by construction, and because the imported
files are pydantic-validated before the pipeline emits them, the
enum-value hole `Widen<T>` leaves open is closed at the source.

## SCH01/REC01 shape review questions

Review artifact for the backend output shapes, recorded while hand-authoring
the B1 types and mock engagement. Since C1, part of this review is
mechanical: `npm run codegen` generates TypeScript from the committed JSON
Schemas into `src/data/__generated__/` (committed; byte-drift checked by
`npm run codegen:check` in `scripts/verify-web.sh` and CI), and
`src/data/bridge.ts` holds compile-time `Exact` assertions between the
hand-authored enums/wire-record and the generated ones. Two honest limits:
the bridge guards the TYPES — JSON imports still widen enum literals to
`string` (`Widen<T>` in index.ts), which C2's direct consumption of the
pipeline-validated artifacts closes at the source; and `support.field_values`
is compared one-directionally because the schema leaves it an open object
while the hand type refines it (documented in bridge.ts). Rule followed: the mock keeps the artifact
shape verbatim; every place the shape diverges from the ontology models or is
awkward for rendering is a question here, not a silent frontend workaround.
Numbers are referenced from comments in `src/data/types.ts`.

- **Q1 — `unknown_cause` vs `unknown_why`.** Verdict records on the wire
  carry the UNKNOWN why-code as `unknown_cause`; `schema/models.py` `Verdict`
  calls the field `unknown_why`. Same D-U1 concept, two names — which one is
  canonical for SCH01's exported schema? *(C1 note: now schema-confirmed —
  the ontology and wire schemas generate different TypeScript shapes, and
  `bridge.ts` deliberately asserts nothing between them.)*
- **Q2 — EXCEPTION ref naming.** Artifact records carry `disposition_ref`;
  the `Verdict` model calls it `exception_disposition_ref` (EXCLUDED's
  `ratification_ref` matches in both). Also: the conditional fields are
  *absent keys* on the wire but nullable-always-present on the model — codegen
  (C1) needs one convention.
- **Q3 — `verdicts.json` has no run envelope.** It is a bare array;
  `run_id`, `period`, `tenant`, `collected_at` exist only per-record (period
  not at all). `/verdicts` must derive run metadata by folding over records —
  a `{run, records}` wrapper (like poisons.json's envelope) would render
  directly. Intentional?
- **Q4 — poison classification is stringly typed.** `expected` /
  `actual_class` encode "UNKNOWN:UNKNOWN_POPULATION" and E-codes as strings
  the client must parse; a structured `{kind, status, unknown_cause?, code?}`
  would avoid string-splitting in the scorecard. Related: `evidence` is an
  open keyset that varies per case (typed as `PoisonEvidence` with all-optional
  known keys — fragile by construction).
- **Q4b — `verdict_records` grouping keys.** *(ANSWERED — issue #77.)* Closed
  at these three families, and now spelled with the ratified `AssertionType`
  values verbatim (`EXISTENCE`, `NON-EXISTENCE`, `TIMING`; note the hyphen)
  instead of lower-snake names — the key IS the assertion type, so there is
  no second hand-maintained vocabulary to drift out of sync
  (`tests/test_poison_suite.py::test_poison_verdict_record_groups_match_ratified_assertion_type`
  proves it).
- **Q5 — dispositions live in two places in reconciliation.json.**
  *(ANSWERED at B2 — they are two moments, not two truths.)* The buckets are
  the pre-disposition snapshot (taken before `apply_dispositions`); the
  top-level map records the human acts applied after the first verdict. The
  EXCLUDED delta carries its disposition inline because it is born
  dispositioned (D-9). `/reconciliation/[populationId]` therefore renders both
  moments — `at_first_verdict` → `blocked_by_open_deltas` → `after_dispositions`
  — and tags every disposition with which record it came from
  (`resolveDisposition` returns `source: "inline" | "map"`), so the choice is
  visible rather than merged away. Still worth the Owner's confirmation that
  the pre-disposition snapshot is deliberate and should stay on the wire.
- **Q6 — member identifier scheme is inconsistent.** *(ANSWERED — issue #78.)*
  `boundary_exclusions[].member` now carries the same prefixed `member_ref`
  scheme (`email:...`) bucket entries use, derived from
  `BoundaryExclusion.member_ref` (`reconcile/engine.py`) via the same
  `canonical_email` the engine already joins on — no new identity model. The
  excluded-delta ↔ `boundary_exclusions` join in `BucketBoard.tsx` is now a
  direct `===` compare; the prefix-stripping heuristic (`strippedMemberRef`
  applied to `boundary_exclusions`) and its on-screen caveat are gone.
  `strippedMemberRef` itself stays — it still strips a delta's `member_ref`
  prefix to compare against a source's raw email in `attributeDisagreements`,
  an unrelated join.
- **Q7 — `severity` vocabulary is not in the ontology.**
  *(ANSWERED at C1 — by the wire schema itself.)* `verdict-record.schema.json`
  carries the full set: `critical | high | medium | low | informational`, and
  `severity` is optional on the wire. The hand-authored three-value guess was
  wrong and is now generated-checked (`bridge.ts` `_severity`). Remaining for
  the Owner: should Severity also join `schema/enums.py` as ontology?
- **Q8 — registry vocabularies not in the ontology.**
  *(ANSWERED at C1 — they ARE ontology.)* `capability_entry.schema.json`
  `$defs` carries both: `PaginationMethod = cursor | page | none` and
  `TemporalKind = state-only | event-history | full-history |
  snapshot-cadence` — a fourth member the hand-authored guess had missed.
  Both are now generated-checked in `bridge.ts`.
- **Q9 — no D-7 join-failure cause on the wire. ANSWERED — issue #69.** `Delta`
  now carries `cause`, a `@computed_field` on `schema/models.py`'s `Delta`
  computed once from `bucket` (`unresolvable` → identity-fuzzy; `left_only` →
  basis-missing; `right_only` → no-basis-anywhere; `conflict` /
  `intersection` / `excluded` → `null`, since a conflict is a D-8 attribute
  disagreement, not a join failure — never independently settable, so it
  cannot drift from `bucket`). `reconciliation.ts`'s retired `D7_BY_BUCKET` /
  `d7Family()` / `D7_INFERENCE_CAVEAT` are gone; `d7Classify()` now just
  attaches the presentational why-code/meaning to the wire-carried family.
  **Caveat this does not settle:** the verdict-level `unknown_cause`
  (`evaluate/minimal.py` / `evaluate/typed.py`) is computed independently
  from `population.state` and `contract.supports(...)` at evaluation time — a
  different pipeline stage — and is *not* actually derived from which
  `Delta` bucket a member fell into. Wiring reconciliation-time D-7
  classification into that computation would be new modeling, left open.
- **Q10 — `counts` can disagree with `buckets`. ANSWERED — issue #68.** A
  deliberate checksum, not a candidate for dropping. `DeltaBucket`'s own
  docstring (`schema/enums.py`) states it: *"counts are diagnostics, never
  evidence."* `build_demo_engagement.py` emits both fields on purpose, with an
  explicit `counts_note` saying the same. `reconciliation.ts` renders
  `counts[b]` beside the real `buckets[b].length` specifically so a divergence
  between the two is visible on screen rather than silently reconciled away —
  that cross-check is the entire point of carrying a value that could in
  principle be computed from `buckets`. Dropping it would delete the check
  `BucketBoard.tsx` was built to perform.
- **Q11 — `blocked_by_open_deltas` is a flat ref list. ANSWERED — issue #54.**
  Each entry is now `{ref, bucket, cause, dispositioned}` (`cause` added by
  issue #69), computed once in
  `scripts/build_demo_engagement.py` from the same `Delta` objects the
  buckets hold — `bucket` and `dispositioned` travel with the ref instead of
  the page re-deriving both by joining against `buckets`/`dispositions`.
  Related, still open: nothing on the wire says *why* RATIFIED was not
  reached.
- **Q12 — derivation basis on the wire.** *(ANSWERED at B2 — it now travels.)*
  `reconciliation.json` gained `population_type`, `definition`,
  `derivation_rule` and `authoritative_source`, emitted from the `Population`
  the reconciler already holds, so the why-complete rail can state invariant
  №3's basis instead of inferring it from `sources[].role`. The population's
  own `state` was deliberately *not* added — `ladder.after_dispositions`
  already carries it, and duplicating it would manufacture another Q10-shaped
  disagreement.
- **Q11b — a legal AssuranceState can leave the strip. Narrowed — issue #59.**
  `STALE` is reachable from RATIFIED (`schema/models.py` LADDER_TRANSITIONS)
  but is not a rung. The stepper handles it as an explicit off-strip marker
  via `ladderPosition`, whose `never` arm makes any unhandled state a compile
  error. Two separable questions were tangled here:
  - *Is STALE ever really reached?* ANSWERED —
    `tests/test_ladder.py::test_ratified_stale_discovered_cycle_reaches_the_wire`
    now disposes a real delta to legally clear the RECONCILED gate, then walks
    RATIFIED → STALE → DISCOVERED through `advance()`, asserting `.state.value`
    (the same field the real `ladder` wire block serializes) at each step —
    not just the isolated `advance()` unit call `test_full_forward_chain_is_legal`
    already made. The real pipeline (`build_demo_engagement.py`) still never
    produces a STALE population itself; this proves the transition is real
    and wire-safe, not that the demo engagement exercises it end-to-end.
  - *Should the ladder block on the wire say why it went stale* (period
    rolled, source drift, re-collection due), the way `blocked_by_open_deltas`
    says why RECONCILED was blocked? Still OPEN — no in-scope model field
    (timestamp, freshness window, source-fingerprint) exists to read a reason
    from, and no real trigger path produces STALE today, so this needs actual
    new modeling, not exposure of data already in scope.
- **Q13 — no per-source temporal window.** `period` is on the report, but each
  source's own collection window (and CAP01's Okta 90-day history caveat, which
  lives in `registry.json`) does not travel with the reconciliation — so the
  join panel cannot show whether a source could even observe the whole period.
  Should `ReconciliationSource` carry its own `time_window` + capability ref?
- **Q14 — the EQC travels as an identity, not a contract. ANSWERED — issue
  #48.** `scripts/build_demo_engagement.py poisons` now emits
  `artifacts/demo-engagement/contracts.json`, keyed by `contract_hash`: the
  three EvidenceQualityContracts an `evaluate_*` call was actually passed
  (hris/okta/github — `gcp.contract` is collected but never itself the
  contract behind a verdict, so it stays out of this artifact rather than
  emitting an orphan). Every verdict record's `spec_hash` IS a key into this
  map; `tests/test_poison_suite.py` proves the join both directions (no
  dangling hash, no orphaned contract) and that each contract's
  `supported_assertion_types` covers the assertion type it was evaluated
  against. `evidence_quality_contract.schema.json` joined the codegen
  `ROSTER` (`web/scripts/codegen.mjs`). `/proof`'s contract stage renders
  `emitted` — the five quality properties' methods, `supported_assertion_types`,
  and the contract's identity — for any record whose `spec_hash` resolves;
  otherwise it still falls back to the old identity-only rendering.
- **Q15 — claim and assertion ids are not fields anywhere. ANSWERED — issue
  #53.** Every `evaluate_*` call site's `_base_record` (and
  `evaluate.minimal.evaluate_existence`) now writes `claim_id`/`assertion_id`
  onto the record from the `Claim`/`Assertion` objects already in scope at
  evaluation time — no new modeling, the ids existed in memory and were
  simply never written to the wire. `schemas/verdict-record.schema.json`
  requires both; `tests/test_poison_suite.py` proves the join both directions
  (no dangling `claim_id`, no `assertion_id` absent from that claim, no
  assertion of the wrong type for the group it was evaluated under — same
  join-exactness pattern as Q14/issue #48's contract test). `/proof`'s claim
  and assertion stages render `emitted` with the real ids; the poisons
  `verdict_records` grouping (Q4b) now shows only as a diagnostic
  cross-reference, not the identification path.
- **Q16 — commitment and requirement are absent from the wire.**
  *(Manifest snapshot half ANSWERED — issue #47.)* No artifact carries either,
  so /proof still renders those two stages as not-yet-emitted; they need
  modeling first. The manifest snapshot is now emitted:
  `scripts/build_demo_engagement.py poisons` calls `genesis()`
  (src/aegis_sentinel/manifest/snapshot.py) over the ids the same pipeline run
  just produced and writes `artifacts/demo-engagement/snapshot.json`, ratified
  by a DEMO-ONLY identity (`ratified_by` carries the caveat on the wire itself,
  the same way `registry.json`'s `note` does) — never the Owner's real act.
  `/proof`'s snapshot stage renders `emitted` for any record whose
  `population_id` the snapshot's `blocks.populations` covers, listing version,
  ratifier, ratified-at, and the frozen populations/claims/collectors.
  `tests/test_poison_suite.py` proves every population/claim/capability id the
  snapshot cites resolves inside `reconciliation.json`/`poisons.json`/
  `registry.json`, so the ratified scope cannot drift into fiction.
- **Q17 — the poison run's verdict records live only inside poisons.json.
  ANSWERED — issue #58.** `build_poison_artifacts()` now writes
  `verdicts.json` as the consolidated roster — the walking-skeleton record
  plus all ten poison records, sorted by `record_id` — instead of leaving
  the five-state spread embedded only in `poisons.json.verdict_records`.
  Both artifacts carry the same record objects (no independent
  recomputation, so they cannot drift apart;
  `tests/test_poison_suite.py::test_verdicts_json_carries_every_poison_record_no_second_source_of_truth`
  checks it). Took the flat-merge branch of the question, not a run
  envelope — Q3 stays open. `combinedRecords`/`recordCollisions` in
  `web/src/data/verdicts.ts` stay, but only as a redundancy check over an
  already-consolidated artifact now, not a real client-side merge;
  `verdictRuns` is unaffected — two `run_id`s inside one array is still
  legitimate. `main()` alone is unaffected: it still writes the one
  walking-skeleton record, byte-identical to before.

## SATISFIED at B3: ratification caveats on `/registry`

`registry.json` carries a top-level DEMO-ONLY `note` ("workday.terminated_workers
appears frozen because the demo registry ratifies a COPY in memory; the on-disk
entry stays DRAFT pending the Owner's real act") and several entries whose
`history_caveats` begin with `DRAFT:` (github.audit_log, okta.users,
slack.scim_users, workday.terminated_workers). Per the #28 PR note requirement,
the `/registry` page MUST render the top-level `note` and every entry's DRAFT
caveats verbatim alongside the lifecycle badge. A registry page that shows these
entries as usable/frozen without the caveats misrepresents ratification state —
that is a demo-correctness bug, not a styling choice.

**Done at B3.** `/registry` renders `note` verbatim at the top of the page and
every `DRAFT:` caveat verbatim inside the entry card, and usability is *derived*
(`usability()` in `src/data/registry.ts`) from lifecycle + ratifier rather than
asserted, so a DRAFT entry renders "NOT usable" with the SCH02 reason attached.
A frozen entry missing its ratifier is surfaced as a self-contradiction rather
than rounded off (D-L1 makes ratification the freeze). Proven by value
falsifiers: flipping an entry to `draft` moves it to NOT-usable, and nulling
`ratified_by` on a frozen entry produces the contradiction notice.

## PRD §6 acceptance walkthrough (C3)

PRD §6's acceptance, mapped to the screen that carries it and the falsifier
that proves the screen is data, not prose:

| Criterion | Screen | Falsifier that proves it |
| --- | --- | --- |
| Five verdict states render distinctly | `/verdicts` — five sections, each with its own on-screen definition; state is always text, colour only reinforces | `Record<VerdictState, …>` is exhaustive (a sixth state fails `tsc`); flipping a record's `status` moves it between sections and its `/proof` page follows |
| Every seeded defect visibly caught | `/verdicts` mutation scorecard, recomputed from the cases on screen — never read from `detection` | setting a case `detected:false` renders MISSED and drops the rate; a stated/computed divergence renders the "cases are the truth" banner; non-empty `misses` cites PRD §7 |
| A practitioner says "now I know why the population is complete" | `/verdicts` record inspector → population link → `/reconciliation/pop-termination-events` why-complete rail; same from the `/proof` population node (UI01) and the TA-1 process control point | the population link renders only when a reconciliation report exists for that id (else honest no-report text); deleting a blocker's disposition flips the rail's conclusion to "not reconciled" |

Standing note: the detection-rate percentage on `/verdicts` is PRD §7's
required headline metric (`detected / introduced`, denominator = the seeded
defects), not the PRD §2-forbidden coverage percentage against an unratified
population denominator — documented in `src/data/verdicts.ts`.

Deep-link scheme: `/verdicts#record=<encodeURIComponent(record_id)>` selects
and scrolls to a record (`verdictRecordAnchor`/`verdictRecordHref` in
`src/data/verdicts.ts` — one helper pair, so producers and the consumer agree
by construction). Seed TA-2/TA-3 deliberately link to plain `/verdicts`, not a
record anchor: a seed hardcoding an engagement `record_id` would fail silently
(dead fragment, no 404) if VAL02 ever renamed a record, while TA-1's
population href fails visibly (404) under `dynamicParams=false`.

## Deployment (Owner console action — not automated)

Vercel project creation is an Owner action in the Vercel console; nothing in
this repo or CI calls Vercel:

- Root Directory: `web/`
- Ignored Build Step: skip the build unless `web/` or `artifacts/` changed,
  e.g. `git diff --quiet HEAD^ HEAD -- :/web :/artifacts` (exit 0 skips,
  non-zero builds). `artifacts/` must be in the diff because C2 renders the
  real demo-engagement output.
