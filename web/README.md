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
- `src/data/` — the data layer (A2 + B1). `types.ts` holds hand-authored
  ontology/artifact types (C1 codegen replaces them); `seed/*.json` is the
  prototype-ported demo data, genericized to the invented demo company
  "Meridian Financial" (scope, controls, process lanes, gauges); `engagement/`
  is the hand-authored mock engagement encoding the six poison cases, shaped
  to the `artifacts/demo-engagement/` contracts; `index.ts` typed-exports all
  of it so `tsc --noEmit` structurally checks every JSON file against the
  types. Pages import from `@/data`, never from the JSON directly.
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
shapes (Meridian Financial cast, synthetic hashes); C2 swaps them for the real
artifacts above.

## SCH01/REC01 shape review questions

Review artifact for the backend output shapes, recorded while hand-authoring
the B1 types and mock engagement. Rule followed: the mock keeps the artifact
shape verbatim; every place the shape diverges from the ontology models or is
awkward for rendering is a question here, not a silent frontend workaround.
Numbers are referenced from comments in `src/data/types.ts`.

- **Q1 — `unknown_cause` vs `unknown_why`.** Verdict records on the wire
  carry the UNKNOWN why-code as `unknown_cause`; `schema/models.py` `Verdict`
  calls the field `unknown_why`. Same D-U1 concept, two names — which one is
  canonical for SCH01's exported schema?
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
- **Q7 — `severity` vocabulary is not in the ontology.** Only `"high"` is
  observed; `schema/enums.py` has no Severity enum. Typed as
  `"low" | "medium" | "high"` by guess — needs ratification.
- **Q8 — registry vocabularies not in the ontology.** `temporal.kind`
  (`state-only` / `event-history` / `full-history`) and `pagination.method`
  (`page` / `cursor` / `none`) are closed-looking sets that exist nowhere in
  `schema/enums.py`. If they are ontology, they belong in SCH01; if they are
  free text, the types should say `string`.
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

## REQUIRED for B3: render ratification caveats on `/registry`

`registry.json` carries a top-level DEMO-ONLY `note` ("workday.terminated_workers
appears frozen because the demo registry ratifies a COPY in memory; the on-disk
entry stays DRAFT pending the Owner's real act") and several entries whose
`history_caveats` begin with `DRAFT:` (github.audit_log, okta.users,
slack.scim_users, workday.terminated_workers). Per the #28 PR note requirement,
the `/registry` page MUST render the top-level `note` and every entry's DRAFT
caveats verbatim alongside the lifecycle badge. A registry page that shows these
entries as usable/frozen without the caveats misrepresents ratification state —
that is a demo-correctness bug, not a styling choice.

## Deployment (Owner console action — not automated)

Vercel project creation is an Owner action in the Vercel console; nothing in
this repo or CI calls Vercel:

- Root Directory: `web/`
- Ignored Build Step: skip the build unless `web/` or `artifacts/` changed,
  e.g. `git diff --quiet HEAD^ HEAD -- :/web :/artifacts` (exit 0 skips,
  non-zero builds). `artifacts/` must be in the diff because C2 renders the
  real demo-engagement output.
