# Invariants — merged constitution (SCH01)

PRD-v3 declares six invariants; the prior scaffold declared eight
(`knowledge/02_repo_knowledge/CLAUDE.repo-copy.md`). This document merges
them, as HANDOFF.md §1 requires. **No conflict between the two sets was
found** — every pairing is either identical intent or orthogonal — so
nothing here needed an Owner ruling; one application note (№10) is called
out for visibility because it joins two vocabularies through ratified
mappings (D-V1, D-U1).

Where enforced, the enforcement is named — per the enforcement-ladder rule
(L-046), prose is the rung of last resort.

## The constitution

1. **No verdict without a claim.** (PRD-v3 №1. Structural: verdicts are
   emitted only by the evaluator, which consumes `Claim` objects;
   `Claim.population_id` is a required field.)
2. **No claim without a defined population.** (PRD-v3 №2. Structural, same
   models.)
3. **No population without a derivation rule or authoritative source.**
   (PRD-v3 №3. Enforced: `Population` requires exactly one of
   `derivation_rule` / `authoritative_source` — validator in
   `src/aegis_sentinel/schema/models.py`, invalid fixture rejected in
   `tests/test_ontology.py`.)
4. **No evidence without provenance and temporal semantics.** (PRD-v3 №4.
   Enforced: `EvidenceQualityContract` requires all five quality
   properties — each with an independent method and failure mode — plus a
   `time_window`; the missing-property fixture is rejected.)
5. **No PASS unless the evidence is fit to prove the claim.** (PRD-v3 №5.
   Mechanism: contracts declare `supported_assertion_types`; the TYP01
   compiler refuses claims whose assertions no contract supports.)
6. **No agent may expand its own boundary.** (PRD-v3 №6. Discovery emits
   `PROPOSED_SCOPE_CHANGE`; a human ratifies; the manifest versions as
   ratified snapshots — lifecycle per D-L1: `draft → frozen(=ratified) →
   superseded`.)
7. **Every verdict is produced by a plain deterministic function; no
   AI-client or network import anywhere in the verdict path.** (Prior №1.
   Enforced: `tests/test_verdict_path_purity.py` sweeps all of
   `src/aegis_sentinel/`; new modules join CODEOWNERS deliberately.)
8. **Agent output is advisory only — it can never validate as a verdict,
   and never reaches an export.** (Prior №2. The advisory-record shape
   returns with the LLM lane; the structural separation is the invariant.)
9. **Every collector ships with a seeded failing fixture it must detect.
   No detection proof, no merge.** (Prior №3 = PRD-v3's mutation-suite
   discipline. Enforced today for branch_protection in
   `tests/fixtures/seeded/`; VAL01 scales it and computes the detection
   rate.)
10. **Partial collection is UNKNOWN at population level — never a partial
    pass.** (Prior №4, joined to the v3 vocabulary: the failing EQC
    property — `population`, e.g. pagination not exhausted — is named in
    the verdict's support, and the why-code follows D-U1's ratified
    mapping of the D-7 `basis_missing` family → `UNKNOWN_EVIDENCE`. The
    why-code axis and the quality-property axis are orthogonal; both
    survive. Application note, not a conflict.)
11. **Baselines, specs, rosters, and allowlists take effect only via human
    ratification of a hash.** (Prior №5 = the plan→freeze→execute gate;
    ratification is the freeze per D-L1. Agents may draft; only the Owner
    ratifies. Ratification, delta dispositions, and residual-UNKNOWN
    acceptance are manual by design — build surfaces, never automation.)
12. **UNKNOWN always carries a why-code and never maps to satisfied.**
    (Prior №6 under D-U1's enum. Enforced: `Verdict` validator requires
    `unknown_why` iff UNKNOWN; UNKNOWN blocks ratification unless
    dispositioned through the residual-acceptance path.)
13. **Schemas are closed and version-pinned; invalid fixtures must be
    REJECTED — never loosen a schema to fix a failing invalid-fixture
    test.** (Prior №7 = D-P1: `extra="forbid"`, `frozen=True`, generated
    schemas committed with a drift test.)
14. **The scaffold is build-plane only.** (Prior №8, adapted: `.claude/`
    is this repo's Janus plane; nothing under `src/` imports it, and it
    never appears in the runtime diagram. The learnings genome is part of
    the deliverable, not part of the product.)
