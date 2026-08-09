# CLAUDE.md

**Read `AGENTS.md` first — it is the shared operating contract** (Aegis purpose, the
non-negotiable rules, the GCP target). This file adds only Claude-Code specifics. Keep
both short and current.

## TL;DR
Aegis is a deterministic GCP compliance-evidence platform. **Zero LLM in the runtime.**
Collectors are read-only; verdicts are pure functions of `raw_observation`; UNKNOWN is
first-class; the evidence schema is frozen; no SA keys / secrets ever; everything runs in
GCP. See `AGENTS.md` for the full list — those rules bind you.

## Build harness (this repo)
- **Skills:** `scaffold-collector` (new collector + verdict + tests + metadata),
  `verify-gcp` (connection check + idempotent provisioning), `ai-build-log` (keep
  `docs/AI_BUILD_LOG.md` current — the AI-assisted build story).
- **Subagents:** `collector-builder` (writes a collector), `verifier` (independent
  purity / re-performance / UNKNOWN audit — build-time SoD).
- **Hooks** (`.claude/hooks/`, wired in `.claude/settings.json`):
  - *PreToolUse* — blocks ad-hoc cloud mutations + any access to secret files. Infra
    changes go only through `scripts/bootstrap_gcp.sh` (allowlisted).
  - *PostToolUse* — on `src/**` or `tests/**` edits, runs `tests/verdict` + a secret scan.
  - *Stop / SubagentStop* — won't let a task be "done" while `tests/verdict` is red.

## Compose with installed skills (don't reinvent)
- `superpowers:brainstorming` before designing a new collector; `test-driven-development`
  and `verification-before-completion` for the verdict suite.
- `figma-generate-diagram` for the PRD §2 run-lifecycle architecture diagram.
- `/code-review` and `/security-review` before merging (mirror the CI backstop).

## Running things
- Python is in `.venv/` — use `.venv/bin/python -m pytest -q`.
- GCP is via `gcloud` + Python client libs (no GCP MCP). Target project `aegis-8472`.
- To add infrastructure, **edit `scripts/bootstrap_gcp.sh`** and run it — do not issue
  raw mutating `gcloud` commands (they are blocked, by design).
