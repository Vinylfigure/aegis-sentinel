# Aegis invariants — merged ledger

**Merged from:** PRD-v3's six invariants (`docs/PRD-v3.md` §1, "the
constitution") and the prior scaffold's eight
(`knowledge/02_repo_knowledge/CLAUDE.repo-copy.md`, "Invariants"
section). Origins tagged per entry: `PRD-n` = PRD-v3 §1 invariant n;
`scaffold-n` = the nth bullet of the prior scaffold's list. Module
paths are re-pathed to the v3 layout
`src/aegis_sentinel/{schema,capability,collectors,reconcile,evaluate,compile,manifest}`
per `docs/manifest-reconciliation.md` §1 (collectors row).

Produced for the HANDOFF §1 invariant-reconciliation duty: any conflict
is a stop-and-ask to the Owner, never a silent resolution. The two
conflicts found were both already resolved by ratified rulings (§
"Resolved conflicts" below); no unresolved conflict remains.

## The merged list

1. **No verdict without a claim.** (PRD-1)
2. **No claim without a defined population.** (PRD-2)
3. **No population without a derivation rule or authoritative
   source** — the authoritative source is the degenerate case of a
   derivation rule (PRD-3; PRD §8 D5). `Population` construction
   enforces that every derivation-rule source ref names a declared
   source (`src/aegis_sentinel/schema/population.py`).
4. **No evidence without provenance and temporal semantics.** (PRD-4)
   Mechanized as the Evidence Quality Contract's provenance and
   temporal-validity properties (`src/aegis_sentinel/schema/contract.py`).
5. **No PASS unless the evidence is fit to prove the claim.** (PRD-5)
   Contracts declare `supported_assertion_types`; the type checker
   (TYP01) refuses to compile unprovable programs.
6. **No agent may expand its own boundary.** Discovery emits
   `PROPOSED_SCOPE_CHANGE`; a human ratifies; the manifest versions;
   deterministic execution resumes. (PRD-6; scaffold-5 supplies the
   mechanism: baselines, specs, rosters, and capability entries take
   effect only via human ratification of a hash — F-4. Per D-S1 the
   unit of ratification is the manifest snapshot; contract hashes are
   leaves inside it.)
7. **Every verdict is produced by a plain deterministic function; no
   LLM/AI client import anywhere in the verdict path.** (scaffold-1;
   PRD §4 Evaluator lane + §5 non-goal "no LLM in the verdict path.")
   Verdict path = `src/aegis_sentinel/{schema,collectors,reconcile,evaluate,compile,manifest}/`;
   LLM-lane code (Cartographer, Overlord) lives apart and cannot import
   it. Purity/SoD hook enforcement is INFRA01.
8. **Agent output is advisory only.** LLM-lane records structurally
   cannot validate as verdict records and never reach exports
   (scaffold-2, F-7; carried per `docs/manifest-reconciliation.md` §4 —
   `PROPOSED_SCOPE_CHANGE` reuses the same structural-exclusion
   pattern; OSCAL itself deferred per PRD §8 D6).
9. **Every collector ships with a seeded failing fixture it must
   detect — no detection proof, no merge.** (scaffold-3) Generalized in
   v3 to the mutation suite wired as the verify step (PRD §6-§7,
   VAL01/VAL02: any silent PASS is a build-stopping bug).
10. **Partial collection is UNKNOWN at population level, never a
    partial pass.** (scaffold-4) In v3 vocabulary: the prior
    `completeness_basis` is the EQC population property's named method,
    and the failure surfaces as `UNKNOWN_EVIDENCE` with
    `d7_family=basis_missing` (D-U1).
11. **UNKNOWN always carries its cause and never maps to satisfied.**
    (scaffold-6; PRD §2 verdict vocabulary) Why-codes are the enum;
    D-7 cause families ride along as `d7_family` (D-U1;
    `knowledge/01_corpus/02_design_decisions/Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md`).
    UNKNOWN propagates and blocks ratification unless dispositioned
    (justification + owner + review date).
12. **Schemas are closed and invalid fixtures must be rejected.**
    (scaffold-7) `extra="forbid"` + `frozen=True` on every model
    (D-P1); committed `schemas/*.schema.json` carry
    `additionalProperties: false`; `tests/fixtures/schema/invalid/`
    fixtures MUST fail validation — never "fix" a failing
    invalid-fixture test by loosening a schema.
13. **The build plane never enters the runtime.** (scaffold-8) Vendored
    build-plane scaffolding (`.janus/`-style tooling, `knowledge/`,
    `scripts/`) is never imported by `src/aegis_sentinel/` and never
    appears in the runtime diagram.

## Resolved conflicts (the only two found)

- **D-V1 — verdict vocabulary.** Prior scaffold enum
  `PASS/FAIL/UNKNOWN/NOT_APPLICABLE` vs. PRD-v3's five states.
  Ratified: `NOT_APPLICABLE → EXCLUDED`, carrying the
  ratification-reference requirement; `EXCEPTION` added, requiring a
  disposition reference. Implemented in
  `src/aegis_sentinel/schema/verdict.py`; see `docs/DECISIONS.md` D-V1.
- **D-U1 — UNKNOWN taxonomy.** Prior scaffold's three D-7 cause
  families vs. PRD-v3's five why-codes. Ratified: why-codes are the
  enum; families ride along as `d7_family` with the fixed mapping
  `basis_missing→UNKNOWN_EVIDENCE`, `identity_fuzzy→UNKNOWN_POPULATION`,
  `no_basis_anywhere→UNKNOWN_TESTABILITY` (`D7_FAMILY` in
  `src/aegis_sentinel/schema/verdict.py`); see `docs/DECISIONS.md` D-U1.

Near-conflict, judged not a conflict: scaffold-4 phrased partial
collection as `UNKNOWN(basis_missing)`; under D-U1 the same fact is
`UNKNOWN_EVIDENCE` + `d7_family=basis_missing` — a renaming with the
prior term preserved as the family, not a semantic change (entry 10).

## Open (deliberately not implemented in SCH01)

- **D-L1 — lifecycle collapse** (`draft → ratified → frozen` vs.
  ratification-is-the-freeze) is OPEN in `docs/DECISIONS.md`; snapshot
  lifecycle is SCH03 and is not modeled here. `AssuranceState` in
  `population.py` is the *population* ladder, not the manifest
  lifecycle.
