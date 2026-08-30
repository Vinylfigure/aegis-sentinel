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

## D-L1 · 2026-08-16 · RATIFIED · Owner (ruling delegated to research at the SCH00 PR)

**Lifecycle collapse: ratification IS the freeze.** The enum is
`draft → frozen(=ratified) → superseded`, applied uniformly to collection
specs, capability entries, and manifest snapshots. Grounds
(`docs/manifest-reconciliation.md` §D-L1): the v2 contract ratifies and
freezes in one breath ("human-ratified at the trust boundary, then frozen and
versioned") and gives no semantics to a ratified-but-unfrozen artifact —
"frozen requires ratified hash" makes freeze derivable from ratification;
effectivity ("in force for this run") is already evidenced by each verdict
record's `spec_id`/`spec_hash`, so a separate frozen state would duplicate in
a flag what execution records prove; approval batching is served upstream by
bundling `PROPOSED_SCOPE_CHANGE` deltas into one proposal before ratifying.
A `PROPOSED_SCOPE_CHANGE` is a draft delta against the current frozen
snapshot; ratifying it produces v(N+1) frozen and marks v(N) superseded.

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

## D7 · 2026-08-29 · RATIFIED · Owner

**Cartographer documentation-source allowlist** (PRD-v3 §8's own open question D7 —
distinct from the corpus's identically-numbered `Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md`,
already cited under D-U1). Ruled via issue #46, comment 2026-08-29 (posted through an
operator-directed session):

1. **Allowlist for V1, by rule rather than enumeration:** a source is allowed iff it is
   the vendor's own first-party documentation domain. Applied to the five in-scope
   systems: GitHub → `docs.github.com`; GCP → `cloud.google.com`; Okta →
   `help.okta.com` and `developer.okta.com`; Slack → `api.slack.com` and
   `slack.com/help`; Workday → official Workday documentation only.
2. **Workday exception, explicit:** Workday's documentation sits behind Community
   authentication a sandboxed session cannot reach. Workday capabilities stay DRAFT
   with UNKNOWN-cause `source_unreachable` until the Owner supplies cited excerpts —
   no substituting secondary sources to ratify.
3. **Unreachable-source rule, general:** when an allowed source is unreachable (the
   `docs.github.com` 404-through-proxy case already recorded in
   `registry/capabilities/github.audit_log.json` is the canonical example), the
   capability stays DRAFT, records `source_unreachable`, and may carry secondary-source
   notes marked non-ratifiable. Missing evidence is UNKNOWN, never PASS.
4. **D-L1 holds unchanged:** proposals stay DRAFT; only the Owner ratifies.

Unblocks CAP10 (`src/aegis_sentinel/capability/allowlist.py`,
`src/aegis_sentinel/capability/cartographer.py` mechanize rules 1–3: citations outside
the allowlist force a recorded `DRAFT:`/`source_unreachable` caveat rather than silent
omission; the propose function has no parameter through which a caller can set
`ratified_by` or a non-DRAFT lifecycle, so ratification stays structurally a human act).
