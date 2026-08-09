# Aegis Sentinel

**Deterministic GitHub compliance sentinel.** Agents plan and investigate; versioned pure functions decide. Re-performability, not accuracy, is what auditors buy.

The architectural rule, non-negotiable: every pass/fail decision is made by a plain deterministic Python function. The AI layer investigates and explains findings that have *already* been decided — it never produces, revises, or influences a verdict. This is enforced mechanically, not by convention:

| Gate | Mechanism |
|---|---|
| Human review of decision logic | `.github/CODEOWNERS` over the verdict path |
| Proven detection | Seeded-failure fixtures as required status checks (`tests/test_seeded_failure.py`) |
| Schema guardrails | `tests/fixtures/*/invalid/` records MUST be rejected (`tests/test_contract.py`) |
| No AI in the verdict path | `tests/test_verdict_path_purity.py` — AST-level import ban, merge blocker |
| No advisory in evidence | `tests/test_oscal_no_advisory.py` — F-7, fails loudly |
| Tamper evidence | D-1 hash chain; `tests/test_chain_and_ledger.py` proves breaks are detected and named |
| Baseline integrity | Ratification gate: unratified baseline hash fails the run (F-4) |

## Layout

- `schemas/` — verdict-record, collection-spec, advisory-record (forked from GRCEngClub `finding.schema.json` v1.0.0 with the Aegis §3.1 deltas; provenance in each `description`)
- `src/` — verdict path (`verdict.py`, `evidence.py`, `db.py`, `probe.py`, `completeness.py`, `controls/`, `jit/`, `oscal/`) and the advisory lane (`agents/`)
- `tests/` — the validation harness; 50 tests, all required status checks
- `.janus/` — vendored Janus scaffold (build plane only; see `VENDORED_COMMIT`)
- `docs/PLAN.md` — the comprehensive build execution plan
- `.github/ISSUE_TEMPLATE/jit-admin-request.yml` — AM-05 attribute A, as a form

## Run the validation harness

```bash
pip install -e ".[dev]"
pytest
```

## Provenance

Corpus of 23 authoring documents lives outside this repo (hash manifest: see `docs/PLAN.md` §3). Prior art: [GRCEngClub/claude-grc-engineering](https://github.com/GRCEngClub/claude-grc-engineering) @ e98e63e — adopt the contracts, reject the trust model.
