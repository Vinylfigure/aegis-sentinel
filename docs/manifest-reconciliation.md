# SCH00 — Assurance Manifest ⇄ plan→freeze→execute reconciliation

**Status:** awaiting Owner merge (hard gate — no Phase 1 task starts before this).
**Reconciles:** the PRD-v3 Assurance Manifest (`docs/PRD-v3.md` §6)
against the Build Execution PRD v2 contract
(`knowledge/01_corpus/04_build_prds/Sentinel_Build_Execution_PRD.md` §1–§3) and the
prior scaffold's collection-spec lifecycle (its `collection-spec.schema.json`:
`draft → ratified → frozen → superseded`, "deterministic runner executes only frozen,
ratified specs whose hash matches the ratification table").
**Open ruling presented here:** D-L1 (lifecycle collapse) — see §3.

## 1. Block-by-block map

| PRD-v3 manifest block | v2-contract counterpart | Resolution |
|---|---|---|
| `boundary` | No explicit block; scope implicit in each collection spec's `population` + `control_ids`; scope-discovery agent "proposes the collection spec; human ratifies before freeze" | **Generalize.** Boundary becomes first-class; `PROPOSED_SCOPE_CHANGE` mechanizes v2's propose-then-ratify flow at manifest level. No v2-side change. |
| `populations` (+derivation rules, states) | Spec `population`, `authoritative_source`, `join_key` | **Generalize.** Authoritative source = degenerate case of a derivation rule (PRD D5). Three population types, source roles, and the assurance-state ladder are v3 enrichments; v2 fields survive as the simplest case. |
| `claims` (+typed assertions) | Spec `control_ids` (controls with lettered attributes per the SOC 2 testing matrix) | **Invert cleanly.** Claim is the semantic unit; control IDs become framework projections mapped onto claims. Lettered attributes ⇒ typed assertions. |
| `evidence_contracts` (+quality properties, capability refs) | Spec `endpoints` ("which endpoints and fields carry the attributes") + hash discipline; verdict record carries `spec_id`/`spec_hash`/`ratification_ref` | **Formalize.** The EQC is the endpoints block grown up: full identity + five quality properties + supported assertion types + `contract_hash`. Verdict records carry `(manifest_version, snapshot_hash, contract_hash)` where v2 had `(spec_id, spec_hash, ratification_ref)` — see §2. |
| `capabilities` | **No counterpart — new in v3.** | **Add.** Capability entries enter under F-4 mechanics: `ratified_by` is a human-signed hash row, same table discipline as baselines. Unratified entries are mechanically unusable by the compiler (SCH02 test). |
| `collectors` (+permissions) | Replit-era build-plane rules are withdrawn; what carries is the **mechanical gate table**: CODEOWNERS over the verdict path, seeded failing fixture per collector as a required check, Troublemaker standing proof, F-4 ratification-table assertion at run start | **Carry whole, re-path.** CODEOWNERS paths become `src/aegis_sentinel/{schema,capability,collectors,reconcile,evaluate,compile,manifest}/`. v3 adds the compile gate in front: zero collectors executable for claims with unresolved E-codes. |
| `tests` | Seeded-fixture requirement + Troublemaker (manual, ledger-recorded) | **Mechanize.** The mutation suite (VAL01/VAL02) is the seeded-fixture rule generalized to the whole pipeline and wired as the verify step. Troublemaker-style live-tenant seeding stays a Phase-2 concern (needs the fixtures org). |

## 2. Unit of ratification — ADOPTED (D-S1)

v2 ratifies **per-collector collection specs**; v3 ratifies **one engagement-wide
manifest snapshot**. Adopted resolution: the snapshot is the unit. Each evidence
contract's `contract_hash` is a leaf inside the ratified snapshot, so per-collector
integrity survives; ratifying v(N+1) re-signs every leaf it contains. A verdict record
references `(manifest_version, snapshot_hash, contract_hash)`; the run refuses to start
if the loaded snapshot hash has no ratification row — byte-for-byte the v2 F-4
assertion, one level up. No information the v2 contract required is lost.

## 3. Lifecycle — OPEN RULING (D-L1, decide at this PR)

Prior lifecycle: `draft → ratified → frozen → superseded`, where *ratified* = human
signed the hash and *frozen* = the currently-executing immutable version. The v3
snapshot model has: `PROPOSED_SCOPE_CHANGE` (draft delta) → ratification → v(N+1)
active, v(N) superseded.

**Option A (recommended): collapse ratified+frozen — ratification is the freeze.**
A `PROPOSED_SCOPE_CHANGE` is a draft delta against the current frozen snapshot;
ratifying it produces v(N+1) frozen; the prior snapshot becomes superseded.
Simpler state machine, no ratified-but-dormant limbo where a signed-but-not-executing
spec can drift stale. Cost: loses staged ratification (sign now, activate later).
**Option B: keep all four states** at snapshot level (a snapshot can be ratified and
not yet executing). Preserves staging; adds a state the V1 demo never uses.

Ruling recorded in `docs/DECISIONS.md` D-L1 when the Owner merges this PR.

## 4. Carried conditionals (resolved rulings applied)

- **Verdict enum (D-V1, ratified):** `NOT_APPLICABLE → EXCLUDED` keeps the prior
  schema's conditional (EXCLUDED requires a ratification reference); `EXCEPTION` is new
  and requires a disposition reference. FAIL keeps message+support requirements.
- **UNKNOWN (D-U1, ratified):** why-codes are the enum; D-7 cause families ride along
  as `d7_family` (`basis_missing→UNKNOWN_EVIDENCE`, `identity_fuzzy→UNKNOWN_POPULATION`,
  `no_basis_anywhere→UNKNOWN_TESTABILITY`). Population-level partial collection stays a
  hard UNKNOWN — the prior `completeness_basis` becomes the EQC population property's
  named method.
- **Advisory exclusion (F-7):** advisory/LLM-lane records structurally cannot validate
  as verdict records (no verdict fields by construction). `PROPOSED_SCOPE_CHANGE`
  reuses the same structural-exclusion pattern. OSCAL export is deferred (PRD D6,
  shallow OSCAL) but the invariant is retained now.

## 5. What this gate unblocks

SCH01 (ontology) builds these blocks as pydantic models; SCH03 implements the snapshot
+ diff + `PROPOSED_SCOPE_CHANGE` machine per the D-L1 ruling; INFRA01 re-paths
CODEOWNERS; VAL01 mechanizes the seeded-fixture rule. Every mismatch found while
building that contradicts this document is a stop-and-ask, not a silent fix.
