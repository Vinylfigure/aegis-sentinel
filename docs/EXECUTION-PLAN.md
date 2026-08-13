# Aegis v3 — Execution Plan

The living build plan for turning this scaffold into the Aegis assurance compiler
(spec: `docs/PRD-v3.md`, task contract: `docs/HANDOFF.md`) plus a Next.js frontend
(`web/`, deployed on Vercel). Each merged PR ticks its box in the same commit.
Parallel streams run as git worktrees off the base checkout (file-disjoint tracks;
see `.claude/skills/worktree-parallel/`). The frontend is a permanently disjoint track.

Rulings already ratified by the Owner: verdict enum (D-V1), UNKNOWN taxonomy (D-U1),
redaction (D-R1), naming (D-N1). Open: lifecycle collapse (D-L1, due at SCH00 PR).

## Phase 0 — gate & ontology

- [x] **PR-0** — redaction sweep (D-R1: client/personal names zeroed, corpus manifest
  regenerated), redacted+retitled `docs/PRD-v3.md` + `docs/HANDOFF.md`, prototypes at
  `docs/prototypes/`, `docs/DECISIONS.md`, this plan, `scripts/check-redaction.sh`
  wired into `verify.sh full`, LICENSE holder → `vinylfigure`, ruff excludes `web/`.
- [ ] **SCH00** — `docs/manifest-reconciliation.md`: PRD-v3 manifest blocks mapped onto
  the Build Execution PRD v2 plan→freeze→execute contract
  (`knowledge/01_corpus/04_build_prds/Sentinel_Build_Execution_PRD.md`). Presents D-L1
  for ruling. **Hard gate: no P1 task starts before this merges.**
- [x] **SCH01** — core ontology as pydantic v2 models in `src/aegis_sentinel/schema/`
  (Population ×3 + assurance ladder + derivation rules + source roles; Claim; Assertion
  ×7; Evidence Quality Contract identity + 5 properties; Verdict ×5 + why-codes;
  Disposition ×6). Generated JSON schemas committed under `schemas/`; `docs/invariants.md`
  merges PRD-v3's six invariants with the prior scaffold's eight (recording D-V1/D-U1).
  Tests: round-trip byte-identical, fixture triads (invalid fixtures REJECTED), ladder
  transitions, schema drift. Owner reviews before Phase 1.
- [x] **SCH02** — capability entry schema + versioned registry (`registry/capabilities/`);
  unratified entries mechanically unusable (`Registry.usable()` excludes them; tested).
- [ ] **SCH03** — manifest snapshots + human-readable diff + `PROPOSED_SCOPE_CHANGE`
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
  E204 and the correct suggestion. Bonus: the break-glass poison is now runnable in the
  VAL01 harness — the real compiler detects it with E117 (detection rate 1/1 runnable).
- [x] **WALKING SKELETON** — COL01 (HRIS) → one claim → minimal reconcile/evaluate →
  one real verdict record → `artifacts/demo-engagement/verdicts.json` (rendering by
  `web` `/verdicts` lands with B3). First end-to-end milestone; ontology proof-of-fit:
  fixture tenant + seeded truncated-feed fixture (detected → population-level UNKNOWN);
  emitted artifacts carry a real PASS, a real UNKNOWN, and the real E204.
- [x] **COL02–05** — Okta / GitHub / GCP / Slack collectors (worktrees): injected
  transport, fixture tenants only, pagination exhaustion, hashed raw responses, EQC with
  all five property methods named; each ships a seeded failing fixture it must detect.
  Six poisons seeded coherently across the fixture tenants
  (tests/fixtures/tenants/README.md poison-placement table, PRD §6).
- [x] **REC01** — canonical identity join + set reconciler
  (`src/aegis_sentinel/reconcile/{identity,setops,deltas}.py`): exact-key clustering
  with employee_id > email > login precedence, D-8 conflicts (never guessed), six delta
  buckets as first-class DeltaObjects (frontend-aligned fields) with owner + disposition
  human-filled only; negative-space left_only deltas with sources_absent naming the
  authoritative source; DISCOVERED→RECONCILED refused while any delta is
  undispositioned; RECONCILED→RATIFIED only with a ratifier identity.
- [x] **EVAL01** — typed assertion evaluator (`src/aegis_sentinel/evaluate/assertions.py`,
  strict purity lane): TA-2 TIMING over the honest 60-day window (marcus.webb 9 business
  days → FAIL; the six-month E204 stays as the compile exhibit), TA-3 NON_EXISTENCE per
  system (dormant bm-legacy-bot → FAIL; kai.moreno → EXCEPTION under DISP-2026-114),
  TERM-JOIN.a AGGREGATE over the identity join, ratified EXCLUDED record (RAT-2026-031);
  sealed D-S1 records, re-performance byte-identical, five states distinct;
  D-7/D-8 citations in code.
- [x] **VAL02** — all six poisons run against the REAL pipeline
  (`aegis_sentinel.engagement.run_demo_engagement`; runners in tests/mutation/conftest.py):
  assurance defect detection rate = 6/6 = 100% with runnable=6 asserted; emits the full
  `artifacts/demo-engagement/*.json` set (verdicts + compile errors, populations ladder,
  reconciliation w/ negative space, capability registry, manifest, ten-stage proof
  graph), drift-tested emit-twice + committed==regenerated.

## Frontend track (worktree; independent until Phase C)

UI redesign in progress — prototype-derived screens are being replaced by a
process-flow-first design (Owner directive).

- [x] **A1** — Next.js 15 scaffold in `web/` (CSS Modules + token sheet from the
  prototypes; fonts via next/font; AppShell + NavTabs + GaugesRail), Aegis branding,
  `.github/workflows/web-verify.yml` (npm ci, tsc, build, artifact-sync drift check),
  Vercel project (root `web/`, ignored-build-step diffing `web/ artifacts/`).
- [x] **A2** — seed data ported from prototypes into `web/src/data/seed/*.json`,
  genericized to a neutral demo company (Meridian Financial).
- [x] **A3** — `/scope` (merged scope-tool + workbench stage 1) + ledger/regime rail.
- [x] **A4** — `/controls`, `/datasets` (derived registry), `/overlord` (generated
  missions + manifest export) + posture/dataset/agent gauges.
- [x] **A5** — `/process` lanes + control-point detail rail.
- [x] **B1** — TS ontology/artifact types + hand-authored mock
  `web/src/data/engagement/*.json` encoding the six poisons (doubles as the review
  artifact for SCH01/REC01 output shapes).
- [x] **B2** — `/reconciliation` + `/reconciliation/[populationId]` (ladder stepper,
  identity join panel, six-bucket board, why-complete rail).
- [x] **B3** — `/verdicts` (five distinct states, why-code chips, mutation scorecard)
  + `/registry` (capability entries, E-codes as compiler errors).
- [x] **B4** — `/proof/[verdictId]` ten-stage SVG lineage + node inspector.
- [x] **C1** — pydantic JSON-Schema export + codegen (`json-schema-to-typescript`) +
  assignability checks (needs SCH01).
- [x] **C2** — swap mocks for real `artifacts/demo-engagement/` output (needs VAL02);
  deep-link process-graph TA control points → reconciliation/verdicts.
- [ ] **C3** — demo polish against PRD §6 acceptance: five verdict states visibly
  distinct, every seeded defect visibly caught, population click answers "why complete".

## Phase 1.5 / 2 — blocked until VAL02 passes

- [ ] LANE02 (AP lane from template) · MCP01 (Aegis MCP server, read-only) ·
  CAP10 (Cartographer, needs D7 allowlist ruling) · REC10 (Surveyor probes).

## Owner's open items

1. Mutation playbook document (fixtures authored from PRD §6 carry `TODO(playbook)`).
2. Reference-engagement population sizes (placeholders ~200 employees / ~15
   terminations, documented in fixture READMEs).
3. D-L1 lifecycle ruling at SCH00 PR.
4. D7 Cartographer doc-allowlist ruling (blocks CAP10 only).
5. Branch protection on `main` (required checks `verify` + `web-verify`, CODEOWNERS).
