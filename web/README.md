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
- **Q4b — `verdict_records` grouping keys.** poisons.json groups embedded
  records under `existence` / `non_existence` / `timing` — lower-snake family
  names that do not match the ratified `AssertionType` values (`EXISTENCE`,
  `NON-EXISTENCE`, `TIMING`; note the hyphen). Is the key set closed at these
  three, and should it reuse the enum spelling?
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
- **Q6 — member identifier scheme is inconsistent.** `boundary_exclusions[].member`
  is a bare email; every bucket entry uses a prefixed `member_ref`
  (`email:...`, `okta:...`). One scheme, please — joins in the UI otherwise
  need prefix-stripping heuristics. **B2 consequence:** the excluded delta ↔
  `boundary_exclusions` join is performed by `strippedMemberRef`, and the
  excluded card labels that on screen (`PREFIX_JOIN_NOTE`) rather than
  stripping silently. Deleting the exclusion makes the card say so — it is a
  real join, not decoration.
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
- **Q9 — no D-7 join-failure cause on the wire.** `Delta` carries `bucket` but
  not the D-7 cause family. B2 infers it (`unresolvable` → identity-fuzzy /
  `UNKNOWN_POPULATION`; `left_only` → basis-missing / `UNKNOWN_EVIDENCE`;
  `right_only` → no-basis-anywhere / `UNKNOWN_POPULATION`; `conflict` is a D-8
  attribute disagreement, *not* a join failure) and marks every rendering as
  inferred. Given D-7 §5 makes the per-cause UNKNOWN rate itself a verdict
  input, should `Delta` carry `cause` plus its D-U1 why-code so the UI stops
  guessing?
- **Q10 — `counts` can disagree with `buckets`.** Two representations of one
  fact. B2 renders `buckets[b].length` as truth and shows `counts[b]` beside it
  as the artifact's own diagnostic, flagging any divergence on screen. Is
  `counts` a deliberate checksum, or should it drop off the wire as computable?
- **Q11 — `blocked_by_open_deltas` is a flat ref list.** No bucket, no
  resolution state; the page re-derives both by cross-referencing `buckets` and
  `dispositions`, and cannot distinguish "was blocking, now answered" from
  "still blocking" except by that join. Should the ladder carry
  `{ref, bucket, dispositioned}`? Related: nothing on the wire says *why*
  RATIFIED was not reached.
- **Q12 — derivation basis on the wire.** *(ANSWERED at B2 — it now travels.)*
  `reconciliation.json` gained `population_type`, `definition`,
  `derivation_rule` and `authoritative_source`, emitted from the `Population`
  the reconciler already holds, so the why-complete rail can state invariant
  №3's basis instead of inferring it from `sources[].role`. The population's
  own `state` was deliberately *not* added — `ladder.after_dispositions`
  already carries it, and duplicating it would manufacture another Q10-shaped
  disagreement.
- **Q11b — a legal AssuranceState can leave the strip.** `STALE` is reachable
  from RATIFIED (`schema/models.py` LADDER_TRANSITIONS) but is not a rung. The
  stepper now handles it as an explicit off-strip marker via `ladderPosition`,
  whose `never` arm makes any unhandled state a compile error. Should the
  ladder block on the wire say *why* it went stale (period rolled, source
  drift, re-collection due), the way `blocked_by_open_deltas` says why
  RECONCILED was blocked?
- **Q13 — no per-source temporal window.** `period` is on the report, but each
  source's own collection window (and CAP01's Okta 90-day history caveat, which
  lives in `registry.json`) does not travel with the reconciliation — so the
  join panel cannot show whether a source could even observe the whole period.
  Should `ReconciliationSource` carry its own `time_window` + capability ref?
- **Q14 — the EQC travels as an identity, not a contract.** `verdict.spec_hash`
  IS the EvidenceQualityContract's `contract_hash`
  (scripts/build_demo_engagement.py), but the contract itself — the five
  quality properties with their independent methods and failure modes — is
  never emitted. The /proof contract stage can name the contract by hash and
  nothing more. Should the engagement emit the EQCs (they are already built
  in-memory by every collector)?
- **Q15 — claim and assertion ids are not fields anywhere.** Claims exist only
  in Python memory (sole wire trace: `registry.compile_errors[].claim_id`), and
  the assertion id appears only inside the verdict `message` prose; the
  poisons `verdict_records` grouping implies the assertion family but with
  non-ratified spellings (Q4b). /proof renders both stages as trace-only. Should
  verdict records carry `claim_id` and `assertion_id` fields?
- **Q16 — commitment, requirement, and manifest snapshot are absent from the
  wire.** No artifact carries any of the three, so /proof renders those stages
  as not-yet-emitted. The ManifestSnapshot model exists
  (src/aegis_sentinel/manifest/snapshot.py) but the demo never builds one.
  UI01's full chain needs at least the snapshot emitted; commitment/requirement
  need modeling first.
- **Q17 — the poison run's verdict records live only inside poisons.json.**
  The real `verdicts.json` carries one walking-skeleton record; the five-state
  spread (10 records) is embedded in `poisons.json.verdict_records`, so
  `/verdicts` and `/proof` merge two runs client-side (`combinedRecords` /
  `verdictRuns`, dedup by record_id). Should VAL02 emit the poison records
  into a flat `verdicts.json` — or a run envelope (cf. Q3) — so the roster is
  one artifact?

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

## Deployment (Owner console action — not automated)

Vercel project creation is an Owner action in the Vercel console; nothing in
this repo or CI calls Vercel:

- Root Directory: `web/`
- Ignored Build Step: skip the build unless `web/` or `artifacts/` changed,
  e.g. `git diff --quiet HEAD^ HEAD -- :/web :/artifacts` (exit 0 skips,
  non-zero builds). `artifacts/` must be in the diff because C2 renders the
  real demo-engagement output.
