# AGENTS.md — Aegis operating contract (shared source of truth)

This is the single contract both **Claude Code** (`CLAUDE.md`) and **Cursor**
(`.cursor/rules/`) obey. Keep it short and current. If the two tools drift, fix it here.

## What Aegis is
A deterministic, automated **compliance-evidence platform** for a GCP org (FedRAMP High +
SOC 2), covering two controls: **Audit Logging & Retention Integrity** and **Backup &
Restore Validation**. It continuously collects control-tagged, **immutable** evidence and
**proves its own completeness and accuracy** so an auditor can rely on it by sampling.
Specs: `docs/PRD.md` (build), `docs/CONTROL_COVERAGE_MATRIX.md` (control mapping),
`docs/DEMO_RUNBOOK.md` (live drift demo).

## Non-negotiable rules
1. **Zero LLM in the runtime.** Discovery, collection, and verdicts are deterministic
   Python. AI is build-time only (Claude Code + Cursor). This is the headline design
   decision — do not introduce a model call into the evidence/verdict path.
2. **Collectors are READ-ONLY & idempotent.** Only `get`/`list`/`describe` GCP calls.
   Never create/update/delete or mutate IAM from collector code.
3. **Verdicts are PURE functions** of `raw_observation` (`src/aegis/verdict/engine.py`):
   no I/O, no clock, no randomness, no globals — recomputable at read time. Every verdict
   has a non-empty `reason` naming the control parameter.
4. **UNKNOWN is first-class, never silent.** Any permission/API error → `UNKNOWN`, never
   `PASS`. Rate-limited reads back off and retry; still-unreadable → UNKNOWN, never dropped.
5. **The evidence schema is FROZEN** (`src/aegis/schema.py`, `schema_version 1.0`). Never
   break it silently — bump `SCHEMA_VERSION` and migrate. Old records stand under their
   stamped policy.
6. **Secrets: none in git, none to AI.** No downloaded service-account key JSON anywhere —
   runtime auth via attached SA / Workload Identity; CI via Workload Identity Federation
   (OIDC); runtime secrets in Secret Manager. Never paste secrets/keys into AI tools.
   Org/project IDs are config, not secrets.
7. **Everything runs in GCP — no localhost dependency.** Collectors → Cloud Run **Jobs**;
   dashboard → Cloud Run **Service** (same container also runs on a Compute Engine VM
   behind IAP if a persistent host is wanted). The repo is container-ready (`Dockerfile`).
8. **Build-time SoD.** Infra mutations go only through `scripts/bootstrap_gcp.sh` (reviewed,
   idempotent). Ad-hoc `gcloud` mutations are blocked by the PreToolUse hook.

## GCP target
Project `aegis-8472`, org id from `AEGIS_ORG_ID` (see `.env.example`), region `europe-west1`.
There is **no GCP MCP** connected — GCP work is via the `gcloud` CLI and Python client
libraries. Verify/provision with the `verify-gcp` skill or `scripts/verify_gcp.sh` /
`scripts/bootstrap_gcp.sh`.

## How to work
- New collector / control → use the **`scaffold-collector`** skill (or the
  **`collector-builder`** subagent), then the **`verifier`** subagent for an independent
  purity/re-performance audit.
- The deterministic test suite (`tests/verdict/`) is the contract. The PostToolUse and
  Stop hooks run it automatically; CI is the real backstop. A task is not "done" while it
  is red.
- Reference repos: `usnistgov/oscal-content`, `GoogleCloudPlatform/python-docs-samples`,
  `GoogleCloudPlatform/deploystack-auditlogs-to-bq`.

## Open decisions
- **Dashboard framework** — recommended **Streamlit** (single Python stack, satisfies the
  live WORM-pull + hash re-verify requirement, fastest); **FastAPI + HTMX** is the
  more "product-grade" upgrade path. Pure-BI tools (Looker Studio) can't do the live hash
  re-verify, so they are at most a secondary view. Decide when the dashboard is built.
