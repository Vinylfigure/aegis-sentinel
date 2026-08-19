# Aegis v3 — Execution Plan

The living build plan for turning this scaffold into the Aegis assurance compiler
(spec: `docs/PRD-v3.md`, task contract: `docs/HANDOFF.md`) plus a Next.js frontend
(`web/`, deployed on Vercel). Each merged PR ticks its box in the same commit.
Parallel streams run as git worktrees off the base checkout (file-disjoint tracks;
see `.claude/skills/worktree-parallel/`). The frontend is a permanently disjoint track.

Rulings already ratified by the Owner: verdict enum (D-V1), UNKNOWN taxonomy (D-U1),
redaction (D-R1), naming (D-N1), lifecycle collapse (D-L1, ruled at the SCH00 PR:
ratification is the freeze — draft → frozen(=ratified) → superseded).

## Phase 0 — gate & ontology

- [x] **PR-0** — redaction sweep (D-R1: client/personal names zeroed, corpus manifest
  regenerated), redacted+retitled `docs/PRD-v3.md` + `docs/HANDOFF.md`, prototypes at
  `docs/prototypes/`, `docs/DECISIONS.md`, this plan, `scripts/check-redaction.sh`
  wired into `verify.sh full`, LICENSE holder → `vinylfigure`, ruff excludes `web/`.
- [x] **SCH00** — `docs/manifest-reconciliation.md`: PRD-v3 manifest blocks mapped onto
  the Build Execution PRD v2 plan→freeze→execute contract
  (`knowledge/01_corpus/04_build_prds/Sentinel_Build_Execution_PRD.md`). Presented D-L1
  for ruling (ruled: collapse — see DECISIONS.md). **Hard gate: no P1 task starts
  before this merges.**
- [x] **SCH01** — core ontology as pydantic v2 models in `src/aegis_sentinel/schema/`
  (Population ×3 + assurance ladder + derivation rules + source roles; Claim; Assertion
  ×7; Evidence Quality Contract identity + 5 properties; Verdict ×5 + why-codes;
  Disposition ×6). Generated JSON schemas committed under `schemas/`; `docs/invariants.md`
  merges PRD-v3's six invariants with the prior scaffold's eight (recording D-V1/D-U1).
  Tests: round-trip byte-identical, fixture triads (invalid fixtures REJECTED), ladder
  transitions, schema drift. Owner reviews before Phase 1.
- [x] **SCH02** — capability entry schema + versioned registry (`registry/capabilities/`);
  unratified entries mechanically unusable (`Registry.usable()` excludes them; tested).
- [x] **SCH03** — manifest snapshots + human-readable diff + `PROPOSED_SCOPE_CHANGE`
  (transition requires a ratifier identity; structural-exclusion pattern).
- [x] **VAL01** — mutation harness in `tests/mutation/` (detection rate computed;
  a deliberately-silent-PASS stub proves the harness turns the build red).
- [x] **INFRA01** — verdict-path purity tests (AST import/impurity bans + registered
  file roster), per-file purity check script wired into `verify.sh quick`,
  `.github/CODEOWNERS`. Owner: enable branch protection (required checks
  `verify` + `web-verify`, CODEOWNERS, 1 review).
- [x] **LANE01** — termination-lane template as data (`templates/lanes/termination.json`)
  + instantiation into populations/claims.

## Phase 1 — the termination lane, made nasty

- [x] **CAP01** — 7 capability entries across HRIS/Okta/GitHub/GCP/Slack with vendor-doc
  citations; Okta System Log 90-day window recorded as history caveat;
  `ratified_by: "vinylfigure (Ratifier)"`.
- [x] **TYP01** — type checker + E-codes (E204 temporal insufficiency w/ satisfiable-via
  suggestion, E117 missing capability, E302 schema drift); zero collectors executable
  with unresolved E-codes. Acceptance: 6-month TIMING assertion vs Okta 90d fails with
  E204 and the correct suggestion.
- [x] **WALKING SKELETON** — COL01 (HRIS) → one claim → minimal reconcile/evaluate →
  one real verdict record → `artifacts/demo-engagement/verdicts.json`
  (`scripts/build_demo_engagement.py`; drift-tested byte-for-byte). The `web`
  `/verdicts` rendering half rides the frontend track (B3/C2). First end-to-end
  milestone; ontology proof-of-fit.
- [x] **COL02–05** — Okta / GitHub / GCP / Slack collectors (worktrees): injected
  transport, fixture tenants only, pagination exhaustion, hashed raw responses, EQC with
  all five property methods named; each ships a seeded failing fixture it must detect.
- [x] **REC01** — canonical identity join + set reconciler; six delta buckets as
  first-class objects with owner + disposition; DISCOVERED→RECONCILED blocked while any
  delta is undispositioned.
- [x] **EVAL01** — typed assertion evaluator (pure; business-day math tested;
  re-performance byte-identical; five verdict states distinct; D-7/D-8/D-9 citations).
- [x] **VAL02** — six poison fixtures per PRD §6 (expected: UNKNOWN_POPULATION-or-FAIL ·
  NON-EXISTENCE FAIL · E117 compile error · unresolvable→UNKNOWN · TIMING FAIL ·
  EXCEPTION). Assurance defect detection rate = 100%; emits the full
  `artifacts/demo-engagement/*.json` set for the frontend.

## Frontend track (worktree; independent until Phase C)

- [x] **A1** — Next.js 15 scaffold in `web/` (CSS Modules + token sheet from the
  prototypes; fonts via next/font; AppShell + NavTabs + GaugesRail), Aegis branding,
  `.github/workflows/web-verify.yml` (npm ci, tsc, build, artifact-sync drift check),
  Vercel project (root `web/`, ignored-build-step diffing `web/ artifacts/`).
- [x] **A2** — seed data ported from prototypes into `web/src/data/seed/*.json`
  (scope/controls/process/gauges), genericized to Meridian Financial (redaction
  gate green; fictional `@meridian.example` people).
- [x] **A3** — `/scope` (merged scope-tool + workbench stage 1) + ledger/regime rail:
  products/data-classes/asset-layers/system-registry all rendered from `@/data`
  seed exports (deletion-falsifier proven — no literals, counts computed); shared
  `RailLayout`; a11y-upgraded controls (buttons + aria states).
- [x] **A4** — `/controls`, `/datasets` (derived registry), `/overlord` (generated
  missions + manifest export) + posture/dataset/agent gauges: registry derived in
  code (`web/src/data/derived.ts`, 29 refs → 26 datasets), one mission per entry;
  deletion-falsifier proven across the whole chain; shared `StageTabs` strip on
  stages 1–4.
- [x] **A5** — `/process` lanes + control-point detail rail: 3 lanes / 13 steps /
  10 TA markers all iterated from `processSeed` (deletion- and reorder-falsifier
  proven); rail controls derived by flanking-system adjacency (real
  controlPoint→control mapping is a recorded seed-shape question); onward links
  are bare hrefs (C2 wires them).
- [x] **B1** — TS ontology/artifact types (`web/src/data/types.ts`) + hand-authored
  mock `web/src/data/engagement/*.json` encoding the six poisons; JSON wired
  through `checked<T>(json: Widen<T>)` assignability so tsc checks every record
  (enum VALUES stay unchecked until C1 codegen — JSON inference widens strings);
  shape divergences recorded in `web/README.md` "SCH01/REC01 shape review
  questions" — the review artifact for the backend output shapes.
- [x] **B2** — `/reconciliation` (population index) + `/reconciliation/[populationId]`:
  ladder stepper (the DISCOVERED→RECONCILED gate rendered with the engine's own
  blocking sentence; RECONCILED marked *claimed but contradicted* when a blocker
  is unanswered), canonical identity join matrix (every source member keys or
  appears as a named join failure; D-7 cause families inferred and labelled as
  inferred), six-bucket board split open-vs-resolved per `OPEN_BUCKETS`, and the
  why-complete rail that assembles derivation → join → reconciliation →
  dispositions into a conclusion computed from whether every blocker was
  answered, never echoed from `after_dispositions`. Emitter extended so the
  derivation basis travels (`population_type`/`definition`/`derivation_rule`/
  `authoritative_source` — answers README Q12); Q5 answered as two moments, not
  two truths; deletion-falsifier proven across counts, dispositions, sources,
  exclusions and the D-7 classification. No control on the page sets a
  disposition (invariant №11).
- [x] **B3** — `/verdicts`: the five states each render their own section with
  their own on-screen definition (`Record<VerdictState, …>` is exhaustive, so a
  sixth state fails `tsc` rather than vanishing), UNKNOWN why-code chips + a
  per-cause roll-up (D-U1/D-7 §5), and the mutation scorecard recomputed from the
  cases on screen rather than read from `detection` — divergence, misses and
  conditional-field breaches (EXCLUDED without a ratification_ref, etc.) all
  surface as visible defects. `/registry`: usability DERIVED per SCH02 (a DRAFT
  entry can never read as available), the DEMO-ONLY note and every DRAFT caveat
  rendered verbatim per the README's hard requirement, and E-codes rendered as
  refusals with their consequence ("zero collectors execute", TYP01) rather than
  warnings; server-only, no client state. Nine falsifiers: six VALUE probes
  (detection divergence, undetected case, non-empty misses, frozen→draft,
  missing ratifier, missing why-code), two deletion probes, and an exhaustiveness
  probe proving a new `VerdictState` fails the build.
- [x] **B4** — `/proof` (index grouped by the five states) + `/proof/[verdictId]`:
  the ten-stage SVG lineage with typed arrows as visible edge labels (imposes →
  compiled into → quantifies over → derived from → reconciled into → evidence
  gated by → frozen in → executes → evaluates to) and a node inspector. Honest to
  the wire: five stages render from data (population/sources/reconciliation via
  the population_id join, contract identity via spec_hash == the EQC
  contract_hash, verdict itself); the other five are labelled on-diagram —
  not-emitted (commitment/requirement/snapshot, Q16), trace-only
  (claim via compile_errors claim ids, Q15; assertion family inferred from the
  poisons grouping, Q4b/Q15). Clicking the population node links into the
  why-complete rail (UI01). Routes generated from `engagementVerdictRecords`
  (verdicts.json + poisons verdict_records, deduped — the B1 mock duplicates
  them; real artifacts are disjoint, so C2 lifts this to 11 pages with zero
  route changes); `@`-bearing record ids prerender fine. Exhaustive stage/kind
  Records + never-arm inspector switch, so an eleventh stage or new kind fails
  tsc.
- [x] **C1** — codegen from the committed JSON Schemas
  (`json-schema-to-typescript@15.0.4`, exact-pinned, the tree's first non-Next
  dep): `web/scripts/codegen.mjs` generates six modules into
  `web/src/data/__generated__/` (committed; `codegen:check` byte-diffs in
  verify-web.sh + CI, mirroring the Python generate→commit→drift discipline);
  `web/src/data/bridge.ts` holds compile-time `Exact` assertions — eleven enum
  unions plus the wire verdict-record shape (index-signature artifact stripped;
  `support` compared one-directionally, both documented). Deliberately NO
  assertion between the ontology Verdict model and the wire record (Q1/Q2).
  The schemas corrected the hand types: Severity is the five-value wire set
  (answers Q7), TemporalKind gains `snapshot-cadence` and both registry
  vocabularies are ontology (answers Q8), and message/severity are optional on
  the wire with schema_version const-pinned. Falsifiers: dropped enum member →
  4 tsc errors; hand-edited generated literal → codegen:check + bridge both
  fail; schema $defs edit → drift; deleted generated file → missing-file fail.
- [ ] **C2** — swap mocks for real `artifacts/demo-engagement/` output (needs VAL02);
  deep-link process-graph TA control points → reconciliation/verdicts.
- [ ] **C3** — demo polish against PRD §6 acceptance: five verdict states visibly
  distinct, every seeded defect visibly caught, population click answers "why complete".

## Phase 1.5 / 2 — blocked until VAL02 passes

- [x] LANE02 (AP lane from template) — fit verdict in docs/lane-fit-notes.md:
  4 control families fit; 5 misfits recorded as evidence (FIT-001..005), extensions
  deferred per L-014.
- [x] MCP01 — read-only Aegis MCP server (`src/aegis_sentinel/mcp_server/`): the
  four demo-engagement artifacts as resources + a `query_verdicts` tool; official
  `mcp` SDK as an optional extra (core package imports without it); mutation
  structurally impossible (exact tool-set assertion + AST scan banning write- and
  deletion-shaped calls; stdio e2e subprocess test).
- [ ] CAP10 (Cartographer, needs D7 allowlist ruling) · REC10 (Surveyor probes).

## Owner's open items

1. Mutation playbook document (fixtures authored from PRD §6 carry `TODO(playbook)`).
2. Reference-engagement population sizes (placeholders ~200 employees / ~15
   terminations, documented in fixture READMEs).
3. D-L1 lifecycle ruling at SCH00 PR.
4. D7 Cartographer doc-allowlist ruling (blocks CAP10 only).
5. Branch protection on `main` (required checks `verify` + `web-verify`, CODEOWNERS).
