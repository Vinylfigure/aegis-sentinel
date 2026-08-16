# Decision ledger — aegis-sentinel

Repo-local decisions. Each entry cites the corpus path or ruling that grounds it.
Corpus documents under `knowledge/01_corpus/` are cited, never re-imported from memory.

Format: `D-<id> · <date> · <status: RATIFIED|ADOPTED|OPEN> · <decider>`

---

## D-R1 · 2026-08-12 · RATIFIED · Owner (`vinylfigure`)

**Redaction of client and personal names, including hash-manifested corpus files.**
The repo must be generic for anyone to use: zero occurrences of the client's name or
any personal name, anywhere. This supersedes the corpus no-modify discipline for one
deliberate pass: prior-art references to the identically-named public oracle protocol
were rewritten generically ("decentralized oracle network (DON) protocol"), the vendor
example in the SOC 2 testing matrix was genericized, author lines now use `vinylfigure`
or "the Owner", and the corpus hash manifest (`knowledge/01_corpus/`) was regenerated
over the redacted files. Corpus discipline holds going forward from the new hashes.
Enforced mechanically by `scripts/check-redaction.sh` in `verify.sh full` (patterns
stored encoded so the gate does not trip itself).

## D-N1 · 2026-08-12 · RATIFIED · Owner

**Naming: the product is _Aegis_; the agents are _Sentinels_.**
All branding, UI copy, and authored docs call the product Aegis; the agent roster
(Cartographer, Surveyor, Collector, Reconciler, Evaluator, Overlord) are collectively
the Sentinels. Landed copies of earlier docs are retitled accordingly. The Python
package `aegis_sentinel` and repo name already fit.

## D-V1 · 2026-08-12 · RATIFIED · Owner

**Verdict vocabulary merge.** Prior-scaffold enum `PASS/FAIL/UNKNOWN/NOT_APPLICABLE`
merges into PRD-v3's five states as `NOT_APPLICABLE → EXCLUDED` (carrying the
ratification-reference requirement with it) plus the new `EXCEPTION` state for
dispositioned legitimate exceptions. See `docs/PRD-v3.md` §2 and the prior scaffold's
`verdict-record.schema.json` conditional rules.

## D-U1 · 2026-08-12 · RATIFIED · Owner

**UNKNOWN taxonomy merge.** PRD-v3 why-codes are the enum
(`UNKNOWN_DISCOVERY / _OWNER / _POPULATION / _EVIDENCE / _TESTABILITY`); each maps to a
D-7 cause family from the prior scaffold
(`basis_missing → UNKNOWN_EVIDENCE`, `identity_fuzzy → UNKNOWN_POPULATION`,
`no_basis_anywhere → UNKNOWN_TESTABILITY`). Cited to
`knowledge/01_corpus/02_design_decisions/Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md`
in code where implemented.

## D-L1 · 2026-08-12 · OPEN · Owner (decide at SCH00 PR)

**Lifecycle collapse.** Proposal: merge the Build Execution PRD v2 spec lifecycle
`draft → ratified → frozen` so ratification *is* the freeze (a `PROPOSED_SCOPE_CHANGE`
is a draft delta against the current frozen manifest snapshot; ratifying it produces
v(N+1) frozen; v(N) becomes superseded). Changes the v2 contract's four-state enum —
held for explicit Owner ruling at the SCH00 PR, never resolved silently.

## D-P1 · 2026-08-12 · ADOPTED

**Schemas as pydantic v2** (`pydantic>=2.8,<3`), `extra="forbid"`, `frozen=True` on
every model; generated `model_json_schema()` output committed under `schemas/` with a
generated==committed drift test. Rationale: maps directly to the closed-schema
invariant; discriminated unions native; deterministic validation; one pinned dep.

## D-P2 · 2026-08-12 · ADOPTED

**Registry and manifest artifacts are JSON, not YAML** (verify.sh already jq-validates
JSON; closed pydantic schemas validate them; no runtime YAML dep).

## D-P3 · 2026-08-12 · ADOPTED

**Determinism discipline.** Canonical-JSON SHA-256 hashing (volatile fields nulled);
clock values are explicit function inputs; AST-level ban on `datetime.now`, `random`,
`uuid`, `os.environ`, and network modules in `evaluate/` and `compile/`.

## D-P4 · 2026-08-12 · ADOPTED

**Business-day math is Mon–Fri, no holiday calendar in V1.** The manifest carries an
optional `holiday_calendar` field (empty in V1) so adding one later is a manifest
change, not a code change.

## D-P5 · 2026-08-12 · ADOPTED

**Doc locations.** Spec at `docs/PRD-v3.md` + `docs/HANDOFF.md`; prototypes preserved
at `docs/prototypes/`; reconciliation at `docs/manifest-reconciliation.md`; merged
invariants at `docs/invariants.md`; this ledger at `docs/DECISIONS.md`; the living
build plan at `docs/EXECUTION-PLAN.md`.
