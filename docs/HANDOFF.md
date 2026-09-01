# HANDOFF — Aegis v3 Build · for Claude Code in `vinylfigure/aegis-sentinel`

**Companion to:** `sentinel-PRD-v3.md` (the spec; commit both to the repo, PRD at `docs/PRD-v3.md`, this file at `docs/HANDOFF.md`)
**Date:** 2026-08-12 · **Owner:** `vinylfigure`
**One-line mission:** turn the aegis-sentinel scaffold into the Aegis assurance compiler specified in PRD v3, starting with the manifest-schema gate and the termination lane.

---

## 1. Read order (do this before writing any code)

1. `CLAUDE.md` (repo root) — the Janus entry point (prime directives, project facts). The prior scaffold's **eight invariants** live at `knowledge/02_repo_knowledge/CLAUDE.repo-copy.md` — read them there.
2. `knowledge/02_repo_knowledge/docs/PLAN.md` — the existing comprehensive build plan; PRD v3 *supersedes its product scope* but its Janus protocol, validation levels, and EngClub adoption stances remain binding.
3. `knowledge/INDEX.md` → then, from `knowledge/01_corpus/`:
   - `01_architecture/` — investigator architecture: **two-verb split, five layers, plan→freeze→execute**. PRD v3's Overlord/manifest model must land inside this, not beside it.
   - `02_design_decisions/` — the decision ledger; **D7 (UNKNOWN decomposition), D8 (model reconciliation), D9 (decentralization discipline)** are prior art for PRD §2's UNKNOWN-why, set reconciliation, and agent-boundary invariant. Cite them in code comments where implemented.
   - `03_testing_libraries/SOC2_Control_Testing_Matrix.md` — the assertion vocabulary (lettered attributes, population/C&A/sample structure). AM-06 is the termination lane's canonical control; its "Splunk deprovisioning evidence" requirement is the TIMING-assertion argument in the wild.
   - `04_build_prds/` — **Build Execution PRD v2**: the plan→freeze→execute contract that task SCH00 reconciles against. This is the hard gate.
4. `docs/PRD-v3.md` — the spec this handoff implements.
5. Project-external design references (copy into `docs/prototypes/` when committing): `scope-tool.html`, `sentinel-workbench.html`, `process-graph.html` — UI intent, not UI code to reuse.

**Invariant reconciliation duty:** PRD v3 declares six invariants (§1). The repo's CLAUDE.md declares eight. Before P0 completes, produce `docs/invariants.md` merging them; **any conflict is a stop-and-ask to the Owner, never a silent resolution.**

## 2. Locked rulings (do not relitigate; full rationale in PRD §8 and the adjudication)

- North star: **assurance as compiled proof**; the denominator (population completeness) is the differentiating claim.
- Substrate = **universal question set + dispositions** (implemented / inherited / shared / vendor-managed / compensating / N-A-with-rationale). Never generate a silent N/A.
- **Three population types** (entity / event / relationship); process assigns scope-relevance; populations carry derivation rules with **source roles** (authoritative / contributing / corroborating / discovery / exclusion) and the **assurance-state ladder** (UNDEFINED→DEFINED→DISCOVERED→RECONCILED→RATIFIED→STALE). No coverage % against an unratified denominator — ladder states only.
- Reconciliation is **set-based** (canonical identity; intersection; left-only; right-only; conflicts; unresolvable; excluded). Counts are diagnostics, never evidence.
- **CLAIM** is the semantic unit; assertions are typed (STATE/EVENT/SEQUENCE/AGGREGATE/EXISTENCE/NON-EXISTENCE/TIMING); the type constrains admissible evidence.
- **Evidence Quality Contract**: full identity incl. schema_version, collector_version, time window, contract hash; five properties (provenance / integrity / population / semantics / **temporal validity**), each with independent method and failure mode; contracts declare which assertion types they may support.
- Verdicts: **PASS / FAIL / UNKNOWN / EXCLUDED / EXCEPTION**, never interchangeable; UNKNOWN carries a why-code and blocks ratification unless dispositioned (justification + owner + review date).
- **Capability Registry** per PRD §3; Cartographer proposes (docs + citations only, never probes), human ratifies, Surveyor (deterministic) verifies; type checker emits **E-codes** and refuses to compile unprovable programs.
- MCP: inbound = LLM lane freely, verdict path **only pinned** (version + tool schema in contract hash); default verdict-path collectors are native code on versioned APIs. Outbound = Sentinel's own MCP server (P2).
- Lanes are **templates only** in V1. No freeform editor. No published derivation percentage — instrumented per engagement.
- **Six PRD invariants** verbatim, especially: *no agent may expand its own boundary* — discovery emits PROPOSED_SCOPE_CHANGE; ratification is human; manifest versions as ratified scope snapshots with diffs.

## 3. Repo conventions & guardrails

- **Janus loops are live.** Wire real checks into `scripts/verify.sh` early (task VAL01) — the mutation suite *is* the verify step. Use `/reflect` and `/evolve` per session; log to `\.claude/memory/LEARNINGS.md`; **CLAUDE.md is capped at 20 concepts — never bloat it directly; promote via `/evolve`.**
- **Verdict purity is hook-enforced by design intent:** evaluator functions must be pure and re-performable; the corpus specifies PostToolUse-style hooks that block commits when a verdict function fails purity or re-performance tests. If those hooks aren't wired yet, wiring them is part of EVAL01, not optional.
- **Python** (`pyproject.toml` present). Schemas as typed models (pydantic or dataclasses — pick once in SCH01, record in the decision ledger). Layout: `src/aegis_sentinel/{schema,capability,collectors,reconcile,evaluate,compile,manifest}` + `tests/` mirroring.
- **Manual-by-design steps (do not automate):** ratification of scope, capability entries, delta dispositions, residual-UNKNOWN acceptance, and authoritative-source/derivation-rule declarations. Build the surfaces that make the human act visible and attributable; automating the judgment violates invariant 6 and the Owner's manual-first principle.
- **No LLM calls anywhere in `collectors/ reconcile/ evaluate/ compile/`.** LLM-lane code (Cartographer, Overlord) lives apart and cannot import the verdict path.
- **Seed data realism:** V1 termination-lane fixtures derive from the mutation playbook's six poison cases as described in PRD §6 (the playbook document itself is not in this repo — `[NEED: Owner]`; fixtures carry `TODO(playbook)` markers until it lands); reference-engagement population sizes ruled on issue #52 (2026-08-29) — see the "Resolved" note under §6.
- Stop-and-ask triggers: invariant conflicts; manifest-schema mismatches that require changing the Build Execution PRD side; any temptation to add a framework-content feature, GRC-platform feature, or freeform editor (all non-goals).

## 4. Task list (spec-to-task format; prefixes adapted for this repo)

Prefixes: `SCH` schema/ontology · `CAP` capability registry · `COL` collectors · `REC` reconciliation · `TYP` type checker/compiler · `EVAL` evaluator · `LANE` process lanes · `VAL` validation/mutation · `UI` lineage/proof views · `MCP` Sentinel MCP server · `INFRA` CI/hooks.

### Phase 0 — Gate & ontology (nothing else starts until SCH00 passes)

| Task ID | Title | Depends on | Effort | Acceptance criteria |
|---|---|---|---|---|
| SCH00 | Reconcile Assurance Manifest vs. plan→freeze→execute contract | — | M | `docs/manifest-reconciliation.md` maps every PRD-v3 manifest block (boundary, populations, claims, evidence_contracts, capabilities, collectors, tests) to the Build Execution PRD v2 contract; every mismatch resolved or logged as a Owner-decision; decision-ledger entries written. **Hard gate: P1 tasks blocked until this is merged.** |
| SCH01 | Core ontology as typed models | SCH00 | L | `src/aegis_sentinel/schema/` defines Population (3 types, ladder, derivation rule + source roles, period, deltas), Claim, Assertion (7 types), EvidenceQualityContract (full identity + 5 properties + supported-assertion-types), Verdict (5 states + UNKNOWN why-codes), Disposition (6 values). Round-trip serialization tests pass. Invariants doc merged (`docs/invariants.md`). |
| SCH02 | Capability entry schema + registry store | SCH01 | M | Capability entry per PRD §3 schema incl. provenance/ratified_by; registry versioned on disk; unratified entries mechanically unusable by the compiler (test proves it). |
| SCH03 | Ratified scope snapshots + diff | SCH01 | M | Manifest serializes; v(N)→v(N+1) produces a human-readable diff (added/removed populations, claims, contracts); PROPOSED_SCOPE_CHANGE objects exist and cannot transition to IN without a ratifier identity. |
| VAL01 | Mutation suite skeleton wired as verify | SCH01 | M | Playbook mutations encoded as fixtures; `scripts/verify.sh` runs the suite; **assurance defect detection rate computed**; a deliberately-silent-PASS fixture fails the build (proving the harness bites). |
| INFRA01 | Purity/SoD hooks live | SCH01 | S | Commit containing an impure verdict function or an LLM import inside the verdict path is blocked locally and in CI. |

### Phase 1 — The termination lane, made nasty

| Task ID | Title | Depends on | Effort | Acceptance criteria |
|---|---|---|---|---|
| CAP01 | Capability entries ×5 (HRIS, Okta, GitHub, GCP, Slack) | SCH02 | L | Entries authored from vendor docs with citations (Cartographer-style research; agent optional in V1 — hand-authored acceptable), ratified fields populated; **Okta 90-day System Log window recorded as a history caveat.** |
| TYP01 | Type checker + E-codes | SCH01, SCH02 | L | Compiler matches (claim, assertion, population) against registry; emits E204 (temporal insufficiency, with satisfying-combination suggestion), E117 (missing capability for derivation-rule source), E302 (schema-version drift); **test: six-month TIMING assertion vs. Okta 90-day window fails compilation with the correct suggestion.** Zero collectors executable for claims with unresolved E-codes. |
| COL01–05 | Lane collectors (HRIS feed · Okta System Log · GitHub members+audit · GCP IAM · Slack) | CAP01, TYP01 | L | Each: enumeration exhausts pagination; raw response hashed; EQC produced with all five properties' methods named; runs against fixture tenants; no live-tenant calls in tests. |
| REC01 | Canonical identity + set reconciler | SCH01, COL01–05 | L | Given N source sets → canonical-identity join; outputs intersection/left-only/right-only/conflicts/unresolvable/excluded as first-class delta objects with owner + disposition fields; ladder transitions (DISCOVERED→RECONCILED) only when deltas dispositioned. |
| EVAL01 | Typed assertion evaluator | REC01, TYP01, INFRA01 | L | AM-06-derived assertions run: TIMING (≤5 business days, business-day math tested), EXISTENCE/NON-EXISTENCE per system; pure functions; re-performance test (same inputs → byte-identical verdict record); five verdict states emitted distinctly. |
| LANE01 | Termination lane template + instantiation | SCH01 | M | Lane template (nodes, edges, control points) as data, not code; instantiating with the five fixture systems produces the populations + claims the compiler consumes. |
| VAL02 | Nasty demo dataset + full mutation run | VAL01, EVAL01, LANE01 | M | Fixtures include: contractor absent from HRIS · dormant GitHub local account · break-glass cloud account · failed identity join · delayed revocation · legitimate exception. Run yields correct PASS/FAIL/UNKNOWN/EXCLUDED/EXCEPTION per case; **assurance defect detection rate = 100% on the playbook suite.** |
| UI01 | Proof-graph lineage view | EVAL01 | M | For any verdict: commitment→requirement→claim→population→sources→reconciliation→contract→snapshot→assertion→verdict rendered with typed arrows; clicking the population answers "why complete" (shows derivation rule + reconciliation + dispositions). Static HTML acceptable (evolve `process-graph.html`). |

### Phase 1.5 / 2 (blocked until VAL02 passes — do not start early)

| Task ID | Title | Depends on | Effort | Acceptance criteria |
|---|---|---|---|---|
| LANE02 | Rudd AP-automation lane from template | VAL02 | M | AP lane instantiates from the same template schema; where it doesn't fit, the misfit is *recorded* in the decision ledger as evidence, not papered over. |
| MCP01 | Sentinel MCP server (collectors as tools, evidence as resources) | VAL02 | L | Read-only; Overlord/auditor can query verdicts and pull WORM samples; no tool mutates scope or records verdicts. |
| CAP10 | Cartographer agent (LLM lane) | CAP01, SCH03 | L | Proposes capability entries with citations from an allowlisted doc set (D7-open: allowlist pending the Owner); proposals are drafts; cannot probe; cannot ratify. |
| REC10 | Surveyor deterministic probes | CAP01 | M | One ratified enumeration per entry against real tenant; observed-vs-documented drift emitted as findings. |

**Critical path:** SCH00 → SCH01 → TYP01 → COL01–05 → REC01 → EVAL01 → VAL02. Bottleneck: SCH01 blocks everything — get the ontology reviewed by the Owner before Phase 1 starts. Second bottleneck: TYP01 gates all collectors by design (that's the compiler being a compiler).

## 5. Glossary (terms exactly as used; don't invent synonyms)

Assurance Manifest · ratified scope snapshot · PROPOSED_SCOPE_CHANGE · population (entity/event/relationship) · derivation rule · source role · assurance-state ladder · claim · assertion type · Evidence Quality Contract (spoken: C&A) · disposition · capability entry · Cartographer / Surveyor / Collector / Reconciler / Evaluator / Overlord · E-code · negative-space discovery · assurance defect detection rate · verdict states (PASS/FAIL/UNKNOWN/EXCLUDED/EXCEPTION) · UNKNOWN why-codes.

## 6. Owner's open items (`[NEED]` ledger)

1. D2 ruling (open schema vs. proprietary rules) — not blocking P0/P1.
2. D7 ruling (Cartographer doc allowlist) — blocks CAP10 only.
3. Greenfield-scoping hour baselines — metrics doc only.
4. Ratifier identities for the fixture engagement (who signs the snapshot in the demo — probably "vinylfigure (Ratifier)").

Resolved: realistic termination-population sizes from the reference engagement,
ruled on issue #52 (2026-08-29) — sanitized synthetic profile (750 employees /
12-mo window / 105 terminations / 90 contractors / 3 rehires / 2 same-day / 1
period-boundary).

*Session ritual: end every Claude Code session with `/reflect`; promote stable lessons with `/evolve`; the learnings genome is part of the deliverable.*
