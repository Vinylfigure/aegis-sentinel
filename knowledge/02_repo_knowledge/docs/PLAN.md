# Aegis Sentinel — Comprehensive Build Plan

**Date:** 2026-07-25 · **Author:** scaffolded by Claude (Cowork session), decisions per Mike's ratified corpus
**Companions:** the 23-doc authoring corpus (`~/PycharmProjects/aegis-corpus/`, SHA-256 manifest inside), `Sentinel_Build_Execution_PRD.md` (v2), `Sentinel_v0.2_Event_Driven_Agentic_OSCAL.md`, `Sentinel_JIT_UI_DB_Janus.md`, `Aegis_Prior_Art_GRCEngClub_Toolkit.md`

---

## 1. Decisions taken this session

Three questions were put to Mike and answered:

1. **Repo:** new `vinylfigure/aegis-sentinel` (private), exactly per Build Execution PRD v2 §3. `vinylfigure/aegis` stays what it is — the GCP-scoped evidence platform (CAI discovery, GCS Bucket Lock WORM, BigQuery index) — and serves as architectural prior art, not as host. Its verdict/evidence/collector shape was consulted; its GCP specifics were not imported.
2. **Documentation corpus:** lives in a local folder on the Mac (`~/PycharmProjects/aegis-corpus/`), organized by function, with a SHA-256 `MANIFEST` computed at export — intake discipline applied to our own authoring documents. The repo carries a pointer, not the corpus. (If the corpus should later become CODEOWNERS-protected and hashable in CI, move it to `docs/corpus/` in-repo; the manifest makes that move verifiable.)
3. **Scope:** plan + working scaffold. The scaffold exists, its validation harness runs green (50 tests), and it is delivered as a ready-to-push git repo.

## 2. What exists now (the scaffold)

Built this session, all tests passing:

**Schemas (the #1 blocker, converted from design task to editing task).** `schemas/verdict-record.schema.json` @ 0.1.0 forked from GRCEngClub `finding.schema.json` v1.0.0 (commit `e98e63e`, pinned) with every §3.1 delta applied: `record_hash` + `chain_prev` (D-1), population block with `completeness_basis`, `spec_id`/`spec_hash` (frozen plan reference), `test_function_version`, `ratification_ref`, and the ratified status enum — PASS / FAIL / UNKNOWN(+D-7 cause) / NOT_APPLICABLE(+ratification), `skipped` rejected with rationale in the schema description. `collection-spec.schema.json` encodes plan→freeze→execute: draft/ratified/frozen/superseded lifecycle, frozen requires ratified hash, endpoints carry their `failure_lane` triage from `API_Constraints_By_Trust_Consequence`. `advisory-record.schema.json` gives agent output a shape that structurally cannot validate as a verdict.

**Verdict path (`src/`).** `evidence.py` (canonical hashing, seal, `verify_chain` naming the first bad index), `verdict.py` (verdict engine; invalid verdicts cannot be constructed), `controls/branch_protection.py` (first ported evaluation, PASS/FAIL/UNKNOWN with 404-for-403 discipline), `completeness.py` (partial collection → hard UNKNOWN(basis_missing), the EngClub exit-4 trap closed), `probe.py` (visibility probe), `jit/preconditions.py` (all five AM-05 attributes plus replay window as pure functions), `oscal/exporter.py` (result/ratification only, UNKNOWN→not-satisfied+cause), `db.py` (append-only-by-GRANT DDL, ratification gate). `agents/` is a documented advisory lane with the ten-tool-call cap stated.

**Validation harness (the "way to validate that all this works").** Six suites, wired as the CI required status check:

| Suite | Proves |
|---|---|
| `test_contract.py` | Every fixture validates; every `invalid/` fixture is REJECTED (schema guardrails can't silently loosen) |
| `test_seeded_failure.py` | The collector detects its own seeded drift — a collector that can't turn red doesn't merge |
| `test_chain_and_ledger.py` | Code-produced records conform to schema end-to-end; tamper detected and named, including the rehash attack; unratified baseline fails the run |
| `test_jit_preconditions.py` | Every AM-05 deny path fires, including case-variant self-approval and shadowed-failure reporting |
| `test_verdict_path_purity.py` | AST-level ban: no AI client or `src.agents` import anywhere in the verdict path; new modules must be registered deliberately |
| `test_oscal_no_advisory.py` | F-7: advisory content cannot reach an export; UNKNOWN never maps to satisfied |

**Governance.** `.github/CODEOWNERS` over the verdict path, schemas, seeded fixtures, and CI itself; `contract-tests.yml` workflow; JIT Issue Form (AM-05 attribute A). Janus vendored at `.janus/` with its source commit recorded.

## 3. The documentation corpus

`~/PycharmProjects/aegis-corpus/`, 23 documents + `MANIFEST.md`/`MANIFEST.sha256` (export 2026-07-25T01:20:59Z):

- `01_architecture/` — Investigator architecture & design decisions, workflow theory, glossary
- `02_design_decisions/` — Decision ledger, constraints, contradictions, design fixes D7/D8/D9, red-team reconciliation, API constraints by trust consequence, control-evidence API chains, version drift ledger
- `03_testing_libraries/` — SOC 2 control testing matrix, SOC 2 TSC / FedRAMP / SOX agent testing libraries
- `04_build_prds/` — Sentinel Build Execution PRD v2, Sentinel v0.2 event-driven spec, JIT/UI/DB/Janus companion
- `05_prior_art/` — GRCEngClub toolkit review (quarantined external source)

Note: the claude.ai project lists `Sentinel_Build_Execution_PRD.md` twice; `project_read` returns only v2 (Launch Readiness), which is what was exported. v1 is withdrawn per v2's header, so nothing is lost.

Discipline going forward: the corpus folder is a snapshot; the claude.ai project stays the authoring surface. On any doc change, re-export and re-manifest (the `Version_Drift_Ledger` gets a row when an external fact changes underneath a doc). When Wave-1 Skills are drafted, they cite corpus paths + hashes, not memory.

## 4. Immediate next actions (you, ~30 minutes)

1. Create the private GitHub repo `vinylfigure/aegis-sentinel`, then from `~/PycharmProjects/aegis-sentinel`: `git remote add origin … && git push -u origin main`.
2. Branch protection on `main`: require 1 approving review, require the `contract-tests` status check, enforce CODEOWNERS, disallow force pushes, include administrators.
3. Create the `vinylfigure-fixtures` free org (`[NEED: 7/25]` in the PRD — gates every org-level audit: external collaborators, teams, CODEOWNERS audits). Tag fixture repos `aegis-fixture`.
4. Confirm in-product: Replit Postgres offering + deployment types/pricing, and Slack free-tier slash-command/interactivity support (both flagged `[NEED: 7/25]`; unverifiable from the build sandbox).
5. Open the repo in Claude Code. This session's scaffold is the seed; Claude Code is the reviewer/test-runner/Troublemaker plane from here on.

## 5. Build sequence to 7/30 (PRD v2 day-by-day, adjusted for today)

The PRD's Fri/Sat items (app creation, GitHub link, Postgres bootstrap, fixture org, CODEOWNERS) are partly done by this scaffold; the remainder compresses into today.

| Day | Replit Agent (build plane) | You + Claude Code (gate plane) |
|---|---|---|
| **Sat 7/25** | Create Replit app, link repo, provision Postgres, bootstrap ledger schema from `src/db.py` DDL; dashboard reading the ledger; port BPR + rulesets collector | Push repo, set protections, create fixtures org; review; ratify first baseline (F-4 row in `ratifications`) |
| **Sun 7/26** | External-collaborator collector; Slack digest + signature verification | Review; extend seeded fixture set for each new collector |
| **Mon 7/27** | Admin, deploy-key, CODEOWNERS collectors | Review; start Janus side experiment on a branch (§7) |
| **Tue 7/28** | JIT: Issue Form intake, approval buttons, grant/revoke, reconciliation | Review `src/jit/preconditions.py` integration line by line — highest-risk code |
| **Wed 7/29** | Agent roles per Sentinel v0.2; OSCAL exporter wired to ledger with schema validation in CI | Verify F-7 test still gates; webhook completeness reconciliation live |
| **Thu 7/30** | Polish; Verify-Ledger button; findings detail view | Troublemaker: seed → assert → restore against fixtures org; dress-rehearse demo twice |

**Cut line (unchanged from PRD):** drop remediation-PR agent, then OSCAL, then the CODEOWNERS collector. Never drop Troublemaker.

## 6. EngClub toolkit adoption — status against the §5 sequence

1. ✅ Verdict-record schema fork-and-delta — done (this scaffold).
2. ✅ Status-enum decision locked into the schema layer — done; record it as a D-ledger entry in the corpus (one paragraph, PASS/FAIL/UNKNOWN(+cause)/NOT_APPLICABLE, `skipped` rejected).
3. ✅ CI harness lifted and upgraded — done, and upgraded past schema-conformance to detection-proof (seeded-failure suite) on day one rather than later.
4. ⬜ SCF crosswalk intake: one-time fetch of SOC2-TSC / FedRAMP / SOX crosswalk JSONs from `GRCEngClub/scf-api`, SHA-256 at intake, pinned upstream release recorded in the Version Drift Ledger. CC BY-ND: attribute, never modify. Use evidence-request/assessment-objective entries as Wave-1 Skill seed material (agent drafts, human ratifies).
5. ⬜ Port `fedramp-20x` update-hook pattern into Janus as the recalibrate heartbeat against the pinned SCF release and FedRAMP docs.
6. ⬜ Add the exit-code/partial-collection rule to `API_Constraints_By_Trust_Consequence.md` as a fail-silent row (the code half is already enforced by `src/completeness.py`).
7. Portfolio move (§6 of the prior-art doc, post-demo): an integrity-extensions RFC against their Finding schema — hash, population, spec-reference fields as an optional conformance tier. The delta is literally this repo's schema diff; the PR validates under their own contract-test CI.

## 7. Janus experiment protocol (measured, off the critical path)

Janus is vendored at `.janus/` (source commit in `VENDORED_COMMIT`). It stays strictly in the build plane — the workshop, never a runtime component.

Protocol: port audits 5 and 1 by hand first (marquee demos). Then hand audits 2, 4, 6, 7, 8, 9 to Janus on a branch. The deliverable is the **time-per-port curve across iterations**, which should decline if the learnings genome is doing its job. Middle-loop discipline: a candidate learning is promoted only when a passing fixture test demonstrates it (the harness in `tests/` is exactly that gate). Outer loop: the recalibrate heartbeat (item 5 above) re-verifies genome facts against live API behaviour. If Janus stalls, nothing is lost; if it flies, it's the second story.

## 8. Validation, end to end (the answer to "how do I know this all works")

Four levels, cheapest to most expensive, each already partly mechanized:

1. **Merge time** — the 50-test harness as a required status check: schemas can't loosen (invalid fixtures must reject), collectors can't ship without detection proof, the verdict path can't import an AI client, advisory can't reach OSCAL, tampering is detectable and nameable.
2. **Run start** — ratification gate: the loaded baseline/spec hash must match a human-ratified row or the run refuses to produce anything (F-4).
3. **Continuous** — event-driven detection with hourly reconciliation proving delivery completeness (the sweep is the proof the events didn't lie by omission); every evaluation records `event` vs `reconciliation` mode as evidence.
4. **Standing proof** — Troublemaker: seed a real drift in the fixtures org → assert the next cycle turns red end-to-end (ledger record, Slack alert, investigator narrative) → restore, ledger-recorded. Run manually from your machine, never deployed. On demo day, point Sentinel at its own repo: the controls defending the verdict path are the controls the product tests.

## 9. Open items carried from the corpus

- `[NEED: 7/25]` fixtures org; Replit product confirmation; Slack free-tier confirmation (all in §4).
- `[NEED: 7/26]` whether fine-grained PAT `created_at` is API-readable for the 90-day token-age assertion; else a manual attestation record (honest UNKNOWN, human-attest lane).
- D-ledger entry for the status enum (item 2 in §6).
- Corpus re-export cadence: on any project-doc change, or weekly, whichever comes first.
