# Aegis Sentinel — Build Execution PRD (v2)

**Author:** Mike (`vinylfigure`) · **Date:** 2026-07-24 · **Status:** Launch Readiness
**Supersedes:** v1 of this document. v1 split authorship between Replit Agent and Claude Code along the fail-loud/fail-silent axis. That was a category error — see §1 — and the scheme is withdrawn.
**Companions:** `PRD_Aegis_GitHub_Sentinel.md` (product), `Sentinel_Audit_And_Replit_Execution.md` (F-1…F-9), `Sentinel_JIT_UI_DB_Janus.md` (JIT/UI/DB/Janus)

---

## 1. What changed and why

v1 protected the verdict path by **provenance**: Claude Code authored it, therefore it could be trusted. That is the exact reasoning `D-8` rejects — independence is methodological, not provenance. It is also a misuse of the three-lane model, which governs *runtime* ownership (who may be wrong about a constraint while the system runs), not *authorship*. A collector written by Replit Agent and reviewed by a human is precisely as trustworthy as one written by Claude Code and reviewed by a human. **The review gate confers the safety; the tool that typed the code does not.**

v2 protects the verdict path **mechanically**:

| Gate | Mechanism | Blocks |
|---|---|---|
| Human review of decision logic | `CODEOWNERS` covering `src/verdict.py`, `src/evidence.py`, `src/db.py`, `src/probe.py`, `src/completeness.py`, `src/controls/**`, `src/jit/preconditions.py`, `src/oscal/**` | Any merge to the verdict path without your approval |
| Proven detection | Fixture tests as **required status checks** — every collector ships with a seeded failing case it must catch | A collector that cannot detect its own seeded failure |
| Standing independence proof | Troublemaker seed → assert → restore, run manually, ledger-recorded | Silent regression of detection capability |
| Baseline integrity | Ratification table: run asserts the loaded baseline hash was human-ratified (F-4) | An unratified edit quietly loosening the standard |

These are the same ITGCs Sentinel audits. You are not defending the verdict path with a bespoke process; you are defending it with the controls your own product tests — and on demo day Sentinel can be pointed at its own repo to prove they held.

---

## 2. Build planes

**Replit Agent builds everything.** App, UI, Slack handlers, database wiring, deployment config, agent-role runtime, *and the collectors*. One build plane, no coordination tax, maximum evidence of genuine adoption of their tooling.

**Claude Code is reviewer, test runner, and Troublemaker operator.** Reviewing is not authoring. Three jobs: read every PR touching CODEOWNERS-protected paths; run the fixture suite locally where iteration is fastest; operate Troublemaker from your machine against the fixture org — a destructive harness must never live in a deployed app where it can fire by accident.

**Janus is a measured side experiment, off the critical path.** Give it audits 6, 7, and 9 on a branch after the marquee collectors are done by Replit. Its deliverable is not the ports — it is the time-per-port curve across iterations, which is your honest answer to whether the scaffold accelerates anything. If it stalls, nothing is lost.

**The connector is a third path.** Replit's MCP connector is live in this chat: the app can be created, changed by natural-language instruction, and queried about its own codebase without leaving the conversation. Worth using for at least one visible increment, because conversational agent-driven development is itself a demonstrable workflow.

---

## 3. Repo topology

| Repo | Purpose |
|---|---|
| `vinylfigure/aegis-sentinel` (private) | Canonical source, synced to the Replit App via GitHub integration. `main` protected: 1 approving review, required status checks, CODEOWNERS enforced. |
| `vinylfigure-fixtures` (new free **org**) | Troublemaker target. Repos tagged `aegis-fixture`. Required — external collaborators, teams, and CODEOWNERS audits are org-level concepts that will not exercise against personal repos. |
| `vinylfigure/janus` | Scaffold source, vendored to `.janus/` for the side experiment. |
| `obelisk/gh-ec-audit` | Prior art and port source. *Verified: depends on reqwest/serde/clap/csv only — it does not use plaid. Plaid is a separate obelisk repo, unrelated here.* |

No directory-ownership scheme. Branch protection and CODEOWNERS do the work that territory was doing badly.

---

## 4. What Replit provides

**Database.** Replit's built-in PostgreSQL, exposed as `DATABASE_URL`. Bootstrap once as the owning role, then connect as a role holding only `INSERT, SELECT` on the ledger table — append-only enforced by grant, not convention. Not the key-value DB (no ordering or transactional insert for a hash chain); not object storage (wrong shape for a small relational integrity workload).

**Two deployments.** An always-reachable deployment hosts the web app and Slack endpoints — Slack needs public HTTPS and a response inside 3 seconds, so acknowledge immediately and process in the background; prefer a reserved instance on demo day so no button dies from a cold start. A scheduled deployment runs the monitor every 30 minutes and the JIT revoker every 5. Separate processes, separate filesystems — which is exactly why the ledger lives in Postgres (F-1).

**Secrets.** Monitor token, JIT token, Slack bot token, Slack signing secret, database URL, Anthropic key. Log token fingerprints, never tokens. Do not invite collaborators to the Repl holding the write-scoped JIT token.

**The agentic runtime.** All four agent roles run on Replit as application code calling the Anthropic API: scope discovery (proposes the collection spec; human ratifies before freeze), investigator (fires on FAIL/UNKNOWN, bounded read-only tool use, produces narrative), UNKNOWN triage (D-7 cause families), and remediation-PR (drafts a PR restoring the baseline, which then passes through the change-management control the tool audits). None can produce a verdict.

---

## 5. Day-by-day to 2026-07-30

| Day | Replit (build) | You (gate) |
|---|---|---|
| **Fri 7/24** | Create app, link GitHub repo, provision Postgres, bootstrap ledger schema | Create fixture org; set CODEOWNERS + branch protection |
| **Sat 7/25** | Dashboard reading the ledger; port BPR + rulesets collector | Review; ratify first baseline |
| **Sun 7/26** | External-collaborator collector; Slack digest + signature verification | Review; write the seeded fixture cases |
| **Mon 7/27** | Admin, deploy-key, CODEOWNERS collectors | Review; start Janus side experiment on a branch |
| **Tue 7/28** | JIT: Issue Form intake, approval buttons, grant/revoke, reconciliation | Review JIT preconditions line by line — highest-risk code in the build |
| **Wed 7/29** | Agent roles; OSCAL exporter with schema validation in CI | Verify no advisory record can reach an OSCAL document (F-7) |
| **Thu 7/30** | Polish; Verify-Ledger button; findings detail view | Troublemaker: seed → assert → restore. Dress-rehearse the demo twice. |

**Cut line:** drop remediation-PR agent, then OSCAL, then the CODEOWNERS collector. Never drop Troublemaker — it is the proof that detection is real, and it is the piece nobody else builds.

---

## 6. Demo script (10 minutes)

Dashboard on a real run → Troublemaker seeds a drift on a fixture repo → next cycle turns red → Slack alert fires → investigator narrates when and by whom → open the finding, show its ledger record, hit Verify → tamper a copy, show the chain break naming the record index → run the JIT flow live: Issue Form request, Slack approval, admin granted, monitor reconciles that grant against AM-04 attribute C → close on the remediation PR the agent drafted, which must itself pass the branch protection the tool audits.

Closing line: *"The agent decides what to look at and explains what it found. Versioned code decides whether it passes. Re-performability, not accuracy, is what auditors actually buy — and I protected the verdict path with the same controls the product tests."*

---

## 7. Open questions

- `[NEED: 7/25]` Create `vinylfigure-fixtures` org — gates the org-level audits.
- `[NEED: 7/25]` Confirm in-product: current Postgres offering, deployment types and pricing, Agent capabilities. *Knowledge boundary stated honestly: end of May 2026. Direct research this session was blocked — network access is allowlisted to GitHub and package registries, and replit.com is unreachable. What was verifiable: `@replit/river` shipped v0.220.0 on 2026-07-24 (platform actively developed); `@replit/database` v3.0.1 and `@replit/object-storage` v1.0.0 last published April 2024 (stable client libraries). Nothing about deployments or Agent could be confirmed from here.*
- `[NEED: 7/25]` Confirm Slack free-tier app creation still supports slash commands and interactivity.
- `[NEED: 7/26]` Whether fine-grained PAT `created_at` is API-readable for the 90-day token-age assertion; else a manual attestation record (honest UNKNOWN, human-attest lane).
