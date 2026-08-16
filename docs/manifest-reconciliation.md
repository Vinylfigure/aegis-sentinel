# Manifest reconciliation — PRD-v3 blocks vs. the plan→freeze→execute contract (SCH00)

**Status:** the Phase-0 hard gate (EXECUTION-PLAN.md): no P1 task starts before
this merges. **Sources reconciled:**
[PRD-v3](PRD-v3.md) §6's Assurance Manifest block list, against the Build
Execution PRD v2 contract — the plan→freeze→execute pattern as specified in
`knowledge/01_corpus/01_architecture/Aegis_Investigator_Agentic_Architecture.md`
§3 and §7, `knowledge/01_corpus/04_build_prds/Sentinel_Build_Execution_PRD.md`
§1's gate table, and the prior scaffold's spec lifecycle recorded in
`knowledge/02_repo_knowledge/docs/PLAN.md` ("draft/ratified/frozen/superseded
lifecycle, frozen requires ratified hash").

## The v2 contract, restated (anchors, verbatim where load-bearing)

1. **Plan** — the agent drafts a structured collection spec (JSON): "a plan,
   not data."
2. **Freeze** — "The spec is schema-validated, human-ratified at the trust
   boundary, then frozen and versioned." Lifecycle enum:
   `draft → ratified → frozen → superseded`; frozen requires the ratified hash.
3. **Execute** — "Deterministic runner executes the frozen spec … **Completeness
   asserted here.**" then "Deterministic tests execute … **Accuracy asserted
   here**," each test carrying "a seeded fixture proving it can fail."
4. **Change control** — "Learned improvements flow through the same
   freeze-validate-approve gate as human changes — proposed diffs in version
   control, never live mutations."

## Block-by-block mapping

| PRD-v3 manifest block | v2 contract counterpart | Verdict |
|---|---|---|
| `boundary` | None — v2 scopes implicitly via each spec's "declared source" and repo topology. PRD-v3 adds the commitment → obligation → boundary provenance chain as first-class data. | **Additive.** No conflict; nothing on the v2 side changes. |
| `populations` (+derivation rules, states) | The runner's population pull + "completeness asserted here", with two-source reconciliation. | **Refining, compatible.** v3's set-based N-source reconciliation (D-8) generalizes v2's two-source count check ("counts are diagnostics, never evidence" — HANDOFF locked ruling); v2's completeness assertion becomes the RECONCILED→RATIFIED rung of the assurance ladder. Strictly stronger: no coverage claim against an unratified denominator, where v2 asserted completeness only at execution. |
| `claims` (+typed assertions) | Control + lettered testing-matrix attributes; per-attribute verdicts. | **Refining, compatible.** A lettered attribute becomes a typed assertion (STATE/…/TIMING); the type now constrains admissible evidence, which v2 implied (AM-06's Splunk requirement) but never encoded. |
| `evidence_contracts` (+quality properties, capability refs) | The collection spec itself (endpoints, fields, join key, pagination) plus hash + WORM discipline. | **Additive, one binding kept.** The spec's execution identity is subsumed into the EQC (identity + 5 properties + supported-assertion-types). The verdict record keeps `spec_id`/`spec_hash` (the frozen-plan reference v2 requires — already in `schemas/verdict-record.schema.json` v0.1.0) and the EQC adds its own contract hash and capability refs. |
| `capabilities` | None — the registry is new. Nearest v2 concept: §7's self-learning fence, where API-shape knowledge is "safe above the gate." | **Additive, same gate.** The registry formalizes the above-the-gate layer into ratified data: Cartographer proposes (draft), human ratifies, Surveyor verifies — the v2 lifecycle applied to a new artifact kind. Capability entries must carry the same lifecycle enum the D-L1 ruling selects (one lifecycle, three artifact kinds: specs, capability entries, manifest snapshots). |
| `collectors` (+permissions) | Deterministic runner; permissions lived in deployment config (v2 §4 secrets/roles). | **Additive, strengthening.** Declaring collector permissions in the ratified manifest moves a deployment fact into reviewed scope — invariant 6's boundary becomes inspectable data. |
| `tests` | "Fixture tests as required status checks — every collector ships with a seeded failing case it must catch"; Troublemaker seed→assert→restore. | **Direct descendant.** The mutation playbook + assurance-defect-detection-rate (VAL01/VAL02) is v2's seeded-fixture discipline, scaled from per-collector to per-engagement. |

**Result: zero mismatches require changing the Build Execution PRD v2 side.**
Every v3 block either refines a v2 mechanism compatibly or adds a new one that
passes through the same human-ratification gate. One decision is genuinely
open and reserved to the Owner: the lifecycle enum itself (D-L1, below).

## D-L1 — lifecycle collapse (Owner ruling; per DECISIONS.md, never resolved silently)

**v2 as built:** `draft → ratified → frozen → superseded`, with freeze as a
separate act that requires the ratified hash.
**PRD-v3 proposal:** ratification *is* the freeze — a `PROPOSED_SCOPE_CHANGE`
is a draft delta against the current frozen snapshot; ratifying it produces
v(N+1) frozen and marks v(N) superseded (`draft → frozen(=ratified) →
superseded`).

- **Case for collapsing:** in v2, nothing happens between `ratified` and
  `frozen` — freeze adds no information beyond the ratified hash it requires,
  and two states that always transition together are one state. Snapshot
  versioning already provides immutability.
- **Case for keeping four states:** a ratified-but-unfrozen window lets several
  approvals batch into one freeze (one v(N+1) for multiple rulings), and a
  separate freeze is an explicit "in force" act — the audit trail then
  distinguishes *approved* from *effective*.

Whichever way the ruling goes, it applies uniformly to collection specs,
capability entries, and manifest snapshots, and `superseded` and `draft`
survive in both options.

**Ruling (2026-08-16, Owner-delegated research): collapse.** Three grounds:
(1) the v2 contract itself ratifies and freezes in one breath and assigns no
semantics to a ratified-but-unfrozen artifact — freeze is derivable from the
ratified hash it requires; (2) effectivity is already proven by execution
records — every verdict carries `spec_id`/`spec_hash`, so "approved vs. in
force" is answered per-run by evidence, and a separate state flag would
duplicate what records prove; (3) approval batching is served upstream by
bundling `PROPOSED_SCOPE_CHANGE` deltas into a single proposal before
ratification. Recorded as D-L1 RATIFIED in [DECISIONS.md](DECISIONS.md).

## Decision-ledger entries written by this reconciliation

- **D-M1 (ADOPTED)** — the block mapping above: all seven PRD-v3 manifest
  blocks reconcile against the v2 contract additively or refiningly; no
  v2-side change required; `spec_id`/`spec_hash` retained on verdict records
  alongside the EQC contract hash.
- **D-L1** — surfaced here for ruling; recorded in `DECISIONS.md` when ruled.
