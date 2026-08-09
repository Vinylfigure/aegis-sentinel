# Aegis — Automated Compliance Evidence Platform (PRD)

**Date:** 2026-06-13 · **Status:** v1 build spec
**Repo:** github.com/Vinylfigure/Aegis · **Env:** personal GCP **org** (no prod data)
**Scope frameworks:** FedRAMP High (Rev5 baseline) + SOC 2 (Security/Availability/Confidentiality). See `docs/CONTROL_COVERAGE_MATRIX.md` for the control-by-control mapping; this PRD is the build spec.

---

## 0. Objective

Build a working, deterministic system that **continuously collects control-tagged, immutable compliance evidence across a GCP org** for two controls — Audit Logging & Retention Integrity, and Backup & Restore Validation — and that **proves its own completeness and accuracy** so an auditor can rely on the evidence by sampling, without re-verifying the collector code. The differentiator over a posture scanner (Prowler et al.) is the evidence pipeline: immutable, reconciled, re-performable, time-sampled, with a live restore.

The one-sentence summary: *"The checks are the easy part; what I built is the evidence system around the checks — so any project an auditor samples from any date answers 'is the control met, was the population complete, and can this be tampered with' from the record itself."*

---

## 1. Scope & Non-Goals

**In scope (build + demo):** two deterministic collectors; org-wide discovery via Cloud Asset Inventory (CAI), keyed by **project × region**; WORM evidence store (GCS Bucket Lock) + BigQuery index; per-run completeness reconciliation and per-record re-performance; **per-record SHA-256** (the run-digest *chain* is a §7 extension, not a build/demo centerpiece — Bucket Lock is the primary anti-tamper); real-time alerting to Google Chat; a read-only dashboard with auditor sampling and a per-control supporting-technology inventory; a **pre-run sampled Cloud SQL restore evidence record** (live kickoff optional, never load-bearing). **Stretch (only if the core pipeline is solid):** one schema-valid OSCAL record.

**Non-Goals (explicit):**
- **No LLM in the runtime.** AI is build-time only (Claude Code). Discovery, collection, and verdicts are deterministic Python. This is a deliberate scale/cost decision, not a gap.
- **No Terraform authored for the demo.** Production would be Terraform-deployed; that is an operational upgrade, not a build item here.
- **No MCP connectors** (BigQuery/Compute Engine MCP) in core — descoped; an optional read-only query layer is a §7-style extension, kept off the runtime to preserve the LLM-free story.
- **No 7 months of seeded history.** We generate ~2 days of *real* dated evidence and demonstrate the sampling mechanism; we never fabricate backdated records (that would contradict the anti-backfill claim).
- **No full OSCAL SSP per control** — just the supporting-technology slice rendered per control.
- **No re-proving GCP's encryption primitive** — inherited via Google's FedRAMP authorization + CRM; we evidence the customer-responsible config.
- **No live test-restore for every system** — Cloud SQL evidenced by a **pre-run restore record** (integrity invariant + elapsed-vs-SLA); a live restore may be kicked off and revisited but is never depended on live; Compute-disk restore described as the extension.
- **No authoring of IAM Deny / Org Policy guardrails.** This is an *evidence-collection* system: Aegis **reads** the deny/org-policy config as evidence (a verdict row). Standing the guardrails up is environment configuration, not the deliverable.
- **No build of an AI meta-framework as a deliverable.** AI accelerates the build and the *story* is captured (tools, prompts, a caught hallucination, a determinism guard); an elaborate hooks/subagents apparatus is not itself a demo artifact.

---

## 2. Architecture & Run Lifecycle

Production engine is a **Cloud Run Job** invoked by **Cloud Scheduler** (scheduled floor) and by **Cloud Asset Inventory feed → Pub/Sub** (event-driven, for new/changed resources). One run = one pass of the pipeline:

```
Cloud Scheduler (cron)  ─┐
CAI feed → Pub/Sub  ─────┼──►  Cloud Run Job  ──►  [1] DISCOVERY (deterministic CAI, org-scoped)
                         │                              enumerate projects / SQL instances / disks / sinks / buckets
                         │                         ──►  [2] COLLECTORS (read-only, idempotent, native Python)
                         │                              audit_logging_collector | backup_collector
                         │                         ──►  [3] VERDICT (pure fn: raw observation → PASS/FAIL/UNKNOWN)
                         │                         ──►  [4] EVIDENCE WRITE → WORM GCS (hash each record)
                         │                         ──►  [5] RECONCILE (two-source completeness; emit reconciliation record)
                         │                         ──►  [6] RUN DIGEST (hash sorted record-hashes; chain prior run digest)
                         │                         ──►  [7] INDEX → BigQuery (non-authoritative)
                         └──────────────────────── ──►  [8] ALERT (FAIL/UNKNOWN/incomplete → Pub/Sub → Google Chat)
```

Run states: `complete` (all in-scope resources reconciled, 0 unaccounted), `incomplete` (≥1 unaccounted → run FAIL + alert), `partial` (finished with N UNKNOWN → alert, counts against completeness). A run is never silently successful.

**Why these primitives:** CAI is one org-scoped call regardless of fleet size (the 10× enumerator); Cloud Run is serverless/auditable and scales by sharding; GCS Bucket Lock is GCP-native WORM that GCP documents as suitable for FINRA/SEC/CFTC-grade immutability (apt for a crypto company). Reference routing pattern: `GoogleCloudPlatform/deploystack-auditlogs-to-bq` (`google_logging_organization_sink`, `include_children=true`, `exclusions`).

---

## 3. Evidence Record Schema (the contract — lock before building collectors)

Every collected fact is one immutable record. The verdict is a **pure deterministic function** of `raw_observation`, stamped at write time and recomputable at read time.

```json
{
  "schema_version": "1.0",
  "run_id": "2026-06-13T03:00:00Z-7f3a",
  "control_id": "AU-11",
  "framework_refs": ["FedRAMP-High:AU-11", "SOC2:C1.1", "FedRAMP-20x:KSI-MLA"],
  "resource": {
    "project": "cw-prod-eu", "region": "europe-west1",
    "type": "logging_sink_destination", "id": "gs://cw-audit-central"
  },
  "collected_at": "2026-06-13T03:00:11Z",
  "collector_version": "0.4.1",
  "policy_version": "2026.06.1",
  "source_endpoint": "storage.buckets.get",
  "raw_observation": { "retention_seconds": 2592000, "retention_locked": false },
  "assessment": "FAIL",
  "reason": "retention 30d < 365d policy AND retention policy not locked",
  "record_hash": "sha256:…"
}
```

Per-run there are two additional records:
- **Reconciliation record** (completeness/accuracy of *this run*): `{run_id, population_by_source: {cai: 42, list_api: 42}, extracted_count: 42, delta: 0, unenrolled_findings: [...], coverage_boundary: ["sqladmin.Instance","compute.Disk",...], sampling_reconciliation: {method, window, projects_sampled, source_count, dest_count, delta}}`.
- **Run-digest record** (integrity): `{run_id, run_digest: sha256(sorted record_hashes), prev_run_digest: "sha256:…", record_count}`.

**OSCAL serialization:** each record maps to an OSCAL Assessment-Results `observation` (raw + method TEST/EXAMINE + `collected`) and `finding` (target = control, status satisfied/not-satisfied). We emit **one** schema-valid `observation`+`finding` validated against `usnistgov/oscal-content` so the RFC-0024 machine-readable claim is demonstrable, not asserted. (Construct names confirmed against oscal-content at build.)

**Verdict examples (these double as the pure-function test suite — build ~15):**

| control | raw_observation | verdict | reason |
|---|---|---|---|
| AU-2 | `auditConfigs present, exemptedMembers: []` | PASS | required config, no exemptions |
| AU-2 | `auditConfigs present, exemptedMembers: ["user:x"]` | FAIL | exempted member breaks coverage |
| AU-2 | `getIamPolicy → 403` | UNKNOWN | permission denied — never PASS |
| AU-11 | `retention_seconds: 31536000, locked: true` | PASS | ≥365d and locked |
| AU-11 | `retention_seconds: 31536000, locked: false` | FAIL | unlocked ≠ immutable |
| SC-28(1) | `kms: google-managed, fips_validated: true` | PASS | FIPS-validated per org param (CMEK not required) |
| SC-28(1) | `kms: none` (required CMEK org param) | FAIL | required CMEK absent |
| AU-9(3) | `record_hash recomputed == stored hash; bucket locked` | PASS | integrity of audit info intact (crypto-integrity mechanism) |
| sink | `include_children: true, exclusions: []` | PASS | routes all children, no silent exclusion |
| sink | `include_children: true, exclusions: ["resource.type=gce_instance"]` | FAIL | unexpected exclusion filter |
| CP-9 | `retained_copies: 3, online: 1, schedule: daily` | PASS | ≥3 copies, ≥1 online, cadence met |
| CP-9 | `automated: true, pitr: true, dest: dual-region, online: 1` | PASS | equivalent-alternative posture (PITR + cross/dual-region) |
| CP-9 | `retained_copies: 1, pitr: false` | FAIL | single copy, no PITR — neither ≥3 nor equivalent-alternative |
| CP-9 freshness | `last_backup_age_h: 30, rpo_h: 24, pitr: false` | FAIL | stale beyond RPO, no current recovery point |
| CP-9 freshness | `last_backup_age_h: 30, rpo_h: 24, pitr: true, binlog_current: true` | PASS | PITR recovery-point current despite 30h full-backup age |
| CP-9(2) restore | `restore: success, row_count_match: true, elapsed<sla` | PASS | sampled restore + integrity invariant |
| completeness | `cai: 42, list_api: 41` | FAIL(run) | source disagreement — 1 unaccounted |
| enrollment | `type: sqladmin.Instance, backup_config: none` | FINDING | backup-eligible, no backup → unenrolled |

---

## 4. Collector 1 — Audit Logging & Retention Integrity

Reads (read-only): `projects.getIamPolicy` → `auditConfigs`; org `logging.organizations.sinks` (destination, `include_children`, `exclusions`); destination bucket `storage.buckets.get` (retention, lock state, versioning, CMEK); IAM on the log/evidence bucket; Cloud Monitoring alert policies + log-based metrics for the high-risk-change set. **Data Access logging** is scoped by a **type+environment eligibility floor** (prod-tier Cloud SQL/BigQuery/Spanner are regulated-eligible by default, from metadata — no content inspection); the `data-classification` label can narrow within that floor but cannot exempt an eligible store (an eligible store with DATA_READ/WRITE off is a FAIL, not a finding). Verdicts per §3 and the matrix. **Change-detection (SI-4/CA-7/AU-6(5) territory)** filters (concrete, validated against prior art): `SetIamPolicy` with `auditConfigDeltas`, **IAM role grants — especially on the log/evidence bucket and audit-config (answers the "should I alert on IAM access grants?" assumption: yes)** — `sinks.delete`, retention change, bucket-permission / custom-role / project-ownership / SQL-instance-config changes. Implementation references: `GoogleCloudPlatform/python-docs-samples` (logging, asset, storage clients).

## 5. Collector 2 — Backup & Restore Validation

Enrollment is **type-driven**: every in-scope Cloud SQL instance and Compute disk within the boundary is *required* to have a compliant backup (no label needed). Reads backup config/schedules, **copy posture** (CP-9's "≥3 copies / ≥1 online **or equivalent alternative**" → in GCP: automated-backups-on + PITR/binlog-on + cross-region or dual/multi-region destination), retention, **PITR-aware freshness** (recovery-point currency where PITR is on, not just last full-backup age vs the ~24h policy RPO), encryption key type + protection level. **Restore (CP-9(1)/(2), A1.3):** the shown evidence is a **pre-run** restore record — restore latest Cloud SQL backup → throwaway instance → assert integrity invariant (row-count/checksum on a seeded table) → record result → teardown; a fresh live restore may be kicked off early and revisited but is **never depended on completing live**. **Cross-control tie-in:** the restore operation appears in Admin Activity logs that Collector 1 already captures — control 1 evidences control 2 for free; show this explicitly.

## 6. Completeness & Accuracy Engine (the IPE differentiator)

This is the evidenced control *of the evidence system* — the answer to PCAOB AS 1105 / SOC IPE C&A without the auditor re-reading code.

- **Completeness — two independent sources, reconciled.** Population denominator = CAI enumeration **and** independently the per-service list APIs (`sqladmin.instances.list`, `compute.disks.aggregatedList`, projects API). Reconcile counts; agreement = completeness demonstrated; disagreement = named gap → run FAIL. Two non-adversarial-but-independently-fallible sources catch CAI ingestion lag, a list-API/pagination bug, and our own extraction error. Document the **coverage boundary** (which asset types are in the population) — CAI isn't omniscient.
- **Unenrolled findings vs FAILs:** a backup-eligible resource with no backup is a high-visibility **finding** (alerts, not a run-FAIL — the run did its job by catching it); a Data Access **eligible-by-type-and-environment** store with logging **off** is a **FAIL** (the `data-classification` label narrows within the eligible floor but can't exempt a store from it).
- **Accuracy — provenance + re-performance.** Store `raw_observation` verbatim + endpoint + timestamps + versions; verdict recomputable from raw (re-perform routine asserts equality). Trace any sampled record → raw → re-call the live API within freshness to confirm the row. Historical records are never rewritten when `policy_version` changes; old records stand under their stamped policy.
- **Boundary statement (say it in the demo):** GCP APIs are a subservice provider under FedRAMP authorization; source-data *truthfulness* is inherited via the CRM/CUECs. Aegis's C&A scope begins **at the API response boundary** — proving nothing is dropped (completeness) or mutated (accuracy) from there onward.

## 7. Integrity & Chain of Custody (tamper-evident)

**Primary anti-tamper = the locked GCS Bucket Lock bucket** (immutable; objects can't be edited/deleted; the locked retention can't be shortened) + CMEK + detailed access logging. This is the strong, caveat-free integrity story and the mechanical guarantee against backfilling — lead with it.

**Per-record SHA-256** (over `raw_observation` + endpoint + timestamps) is the **AU-9(3)** crypto-integrity mechanism: re-verification recomputes a sampled record's hash and asserts equality, detecting any single-record edit and powering re-performance.

**Extension (not core):** chaining run digests — `run_digest = sha256(sorted record hashes)` with each run embedding the prior run's digest — adds an ordering-of-runs ledger, but Bucket Lock already prevents backfilling and the collector SA computes the hashes (a trusted root, so a compromised collector could regenerate a clean chain). So the chain's marginal assurance is low and it's not worth a fragile live chain-verify beat. **Framing: tamper-evident, not tamper-proof.** The real upgrade is **KMS/HSM signing of records/run-digests in a segregated integrity project** (+ optional external anchoring), which removes the collector-trust assumption — full **AU-10** non-repudiation / **AU-9(3)** integrity. No blockchain/ZKP — say so explicitly.

## 8. Dashboard, Auditor Sampling & Per-Control OSI Inventory (UI/UX)

Lightweight **read-only** app (Streamlit for build speed; production = a proper web app on Cloud Run). Reads the BigQuery index for navigation; **never serves verdicts from BQ** — "pull sample" fetches the actual WORM object and re-verifies the run-digest chain on the fly.

Views:
- **Control health grid:** per-control × per-scope state (PASS/FAIL/UNKNOWN), freshness age, open exceptions. This is the CA-7 / CC4.1-CC4.2 continuous-monitoring + deficiency surface.
- **Auditor sampling:** filter by control × project × date → returns the immutable evidence object(s), shows raw observation + verdict + **per-record hash re-verify and Bucket Lock state** (primary anti-tamper). (Demoed over the real ~2-day window; same mechanism serves 7-month-old samples in prod.)
- **Per-control supporting-technology inventory (OSI):** for each control, the in-scope resources that support it (= the completeness denominator, shown from the other side) and the **entity-responsible vs inherited-from-GCP** split with the subservice reference. Generated from CAI; maps to OSCAL system-implementation `component`/`inventory-item` and `leveraged-authorization` (names confirmed at build) so it stays on the RFC-0024 machine-readable path.

**Alerting model:** the dashboard is the source of truth for current health (every control's PASS/FAIL/UNKNOWN + freshness); Google Chat carries only a per-run digest and immediate high-severity *transitions* (new/changed FAIL, UNKNOWN/loss-of-visibility, incomplete run, integrity-chain break) — threaded per run, severity-routed, deep-linked to the dashboard. Alert on transitions, not steady-state levels, to avoid fatigue.

UI states to handle: empty/first-run, UNKNOWN-heavy run (render amber, surface as loss-of-visibility), integrity-verify failure (hash mismatch or bucket unlocked → render red + block reliance), stale freshness (> SLO).

## 9. Security & Separation of Duties

- **Collector SA:** org-scoped **read-only** roles only (`cloudasset.viewer`, `logging.viewer`, `cloudsql.viewer`, monitoring viewer, custom least-privilege). **Write-once** to the evidence bucket: `storage.objects.create` without delete/overwrite; the bucket lock enforces immutability even against the writer.
- **Runtime SoD by identity:** a *separate* admin identity owns the bucket lock and Org Policies; the collector cannot weaken its own evidence store.
- **Auth:** Cloud Run via attached SA / Workload Identity. **Never a downloaded SA key JSON** — no key to leak, and it's a control finding in itself.
- **Secrets & repo hygiene — layered, no long-lived keys anywhere:** runtime secrets in **Secret Manager**, mounted to Cloud Run via its attached identity (not files, not the repo); **GitHub Actions → GCP via Workload Identity Federation (OIDC)** so CI holds no GCP key to leak/rotate; `.gitignore` + **gitleaks pre-commit** + **GitHub push protection/secret scanning** keep secrets out of git (history is permanent). `.gitignore` and a repo/Actions secret solve *different* problems — the former keeps secrets out of commits, the latter injects a CI token at run time — so use both, but prefer WIF/OIDC over any stored key. Org/project IDs are *config*, not secrets. The whole posture is itself a compliance-hygiene signal.

## 10. Build Workflow (Cursor + Claude Code, current conventions)

- **Drive:** Claude Code in the terminal *inside* Cursor as the autonomous build agent; Cursor's IDE for surgical edits, visual diffs, and Tab. Best-practice loop: plan in Cursor **Ask**, implement via Claude Code **Agent**, review diffs / surgical fixes in Cursor **Manual**.
- **Context contracts:** `CLAUDE.md` (Claude Code's operating contract) + `.cursor/rules/` for Cursor's native agent; keep an `AGENTS.md` as the shared source if drift between the two becomes annoying. Keep them short and current.
- **Skills:** package repeatable build workflows (e.g., "scaffold a new collector + its verdict test + metadata") as invocable Claude Code skills.
- **Hooks (build-time determinism + SoD):** `PreToolUse` blocks any non-allowlisted `gcloud`/Bash mutation and blocks reads/writes of secret files; `PostToolUse` runs the pure-verdict + re-performance tests and the secret scan; `Stop`/`SubagentStop` gates a task as done only if tests pass. (Events/handlers per code.claude.com/docs/en/hooks; exit 2 blocks.)
- **Subagents (specialization):** e.g., a `collector-builder` and a separate `verifier` subagent that checks verdict purity/re-performance — build-organization SoD, not a runtime control.
- **CI is the real backstop:** GitHub Actions runs the same pure-verdict, re-performance, and secret-scan checks on every PR. Local hooks accelerate; CI enforces. This is the honest answer to "how do you guarantee determinism."
- **Terraform:** not authored for the demo; production-architecture talking point. Correct the drift nuance: `terraform plan` shows drift **on demand**; continuous drift detection = scheduled plan or live-CAI-vs-state diff (extension).
- **Reference repos:** `oscal-content` (FedRAMP High baseline + validators), `python-docs-samples` / `professional-services` (CAI, logging, Cloud SQL admin clients), `deploystack-auditlogs-to-bq` (org-sink pattern). Authoritative API docs: docs.cloud.google.com.

## 11. Edge Cases (with resolutions)

1. **Historical sampling vs anti-backfill.** Generate ~2 days of real dated evidence; demo sampling on it; explain write-time timestamps + lock prevent backdating. Never seed fake old records.
2. **Bucket Lock is one-way.** A locked policy can't be shortened/removed and the bucket can't be deleted until all objects age out (docs.cloud.google.com/storage/docs/bucket-lock). Demo on a throwaway bucket with **short** locked retention (e.g., 1h–1d) to prove the mechanism live; state prod = 365d. Note: KMS key versions encrypting locked objects can't be destroyed until retention expires — a teardown gotcha.
3. **Parallel collection has no record order.** Resolved by the per-run digest of sorted record hashes (§7), not a per-record chain.
4. **UNKNOWN is adversarial.** Removing the collector's read access turns a FAIL into an UNKNOWN; treat loss-of-visibility as high-severity, count UNKNOWN against completeness.
5. **Partial failure.** A run that finishes with N UNKNOWN still alerts and is not `complete`.
6. **CAI ingestion latency / coverage.** Document the coverage boundary; the two-source reconciliation catches CAI lag.
7. **Backup-failure aging.** A FAIL stays open until a subsequent success within RPO or a linked ticket; open beyond RPO escalates.
8. **Restore runtime.** Cloud SQL restore takes minutes — pre-run so a record exists to show; optionally kick a live one to revisit.
9. **Demo all-green is unconvincing.** Induce a reversible failure live (add a sink exclusion → export-completeness FAIL; revoke one project's read → UNKNOWN). Script the revert.
10. **Rate limits — back off, never drop.** Under throttling: bounded concurrency + pagination + exponential backoff/retry; a resource still unreadable after retries becomes **UNKNOWN** (alerts, counts against completeness), never silently omitted — dropping resources to stay under a limit manufactures false completeness. Batch projects (configurable concurrency/batch size) so a bounded set is processed at a time. Demo small: the batch-size knob + a forced backoff/retry + a forced UNKNOWN, narrated over the 10× math.

## 12. Tradeoffs (the decisions worth defending)

- **Deterministic runtime over agentic runtime** — gives a clean scale/cost story and nothing to attack on "did the model skip a project"; costs the flashy live-agent demo. Worth it.
- **Two/three sources, not a quorum** — sources share a root (one provider), so >3 adds reconciliation noise without assurance; Chainlink-style consensus is the wrong tool here. Spend the trust-minimization on the integrity *root* (KMS/HSM signing) instead.
- **Bucket Lock + per-record hash now, chain/KMS signing later** — locked WORM is the primary, caveat-free anti-tamper; per-record SHA-256 gives integrity + re-performance (AU-9(3)); the run-digest chain and KMS/HSM signing are named extensions, with the collector-trust residual stated, not hidden.
- **Type-driven backup enrollment over labels** — a missing tag can't let a database escape scope; tiered-RPO-by-label is the extension.
- **Config-evidence + sampled reconciliation for log export, not full entry counting** — full counting is infeasible at scale and isn't how the routing guarantee works.
- **Streamlit dashboard** — fast to build, less "product"; acceptable for a demo, flagged as such.

## 13. Demo Script (60 min, live screen-share)

The live-mutation segment is the heart of the demo: for **every element Aegis logs, there is a config you edit live and watch the evidence record flip + the alert fire.** Those edits, their expected verdicts, and the revert steps are in **`docs/DEMO_RUNBOOK.md`** — have it open as a second screen. Pre-flight: a baseline all-green run exists, the throwaway test-restore record is pre-generated, and every revert is scripted.

1. **Frame (3m):** mission, assumptions (from the assumptions doc), the "evidence platform not a scanner" thesis.
2. **Architecture (5m):** the run lifecycle diagram; deterministic, LLM-free runtime; AI used to *build*.
3. **Live collection (8m):** trigger a run; show records landing in the WORM bucket and the BigQuery index; open one record (raw observation + verdict + hash).
4. **Live mutation → evidence flips → alert (16m):** drive the **demo runbook** end to end — audit-config exemption (AU-2 FAIL), sink exclusion (export FAIL), retention drop / unlock (AU-11 FAIL), broaden IAM on the evidence bucket + grant a role (AU-9(4) FAIL + high-risk-change alert), Data Access off on an eligible store (FAIL — label can't exempt), disable a Cloud SQL backup / age it past RPO (CP-9 FAIL), revoke a project's read → **UNKNOWN as high-severity (loss of visibility)**; watch each alert land in Google Chat as a transition; revert each.
5. **Completeness & accuracy (8m):** the two-source reconciliation record (scope the live cross-check to Cloud SQL); add a project/region → auto-discovery picks it up; re-perform a verdict from raw; trace a record to the live API.
6. **Sampling + integrity (5m):** pull a sample by control × project × date → the WORM object; **re-verify the per-record hash and show the Bucket Lock state** (primary anti-tamper); show the per-control OSI inventory with the entity-vs-inherited split.
7. **Backup + restore (8m):** the pre-run restore record + integrity invariant + elapsed-vs-SLA; the restore op appearing in the audit logs (cross-control tie-in); PITR-aware freshness.
8. **AI build story + scale (5m):** which AI tools built what, 2–3 real prompts, one caught hallucination, one determinism guard; the bounded-batch knob + a live backoff→UNKNOWN; the 10× bottlenecks with numbers (lead with the per-resource fan-out reads + quotas, not the single CAI call). *(OSCAL record only if built — stretch.)*
9. **Close (2m):** tamper-evident-not-proof honesty, M-21-31 one-liner, extensions (chain→KMS signing, full restore harness, tiered RPO).

## 14. Success Criteria

- **Completeness:** two-source reconciliation + coverage boundary; run FAILs on any unaccounted resource.
- **Correctness:** verdict = named control parameter, recomputable from raw.
- **Reliability:** UNKNOWN first-class; retries/backoff; partial-failure alerting.
- **Audit defensibility:** WORM + run-digest chain; sampling serves the immutable object; re-performance.
- **Scalability:** CAI enumerator + bounded-concurrency fan-out/sharding; rate limits handled by backoff→UNKNOWN (never drop); named 10× bottlenecks with numbers.
- **AI leverage:** Claude Code skills/hooks/subagents materially accelerated the build; CI enforces determinism; zero LLM in the verdict path (the AI-risk mitigation, made architectural).

## 15. Resolved Decisions & Build-Time Verifications

- **Data-Access enrollment = labels (decided).** `data-classification=regulated` scopes which stores get Data Access logging — corporate-standard tag-driven scoping. Unlabeled regulated-eligible stores surface as findings (completeness backstop). Demo: add a labeled store → discovery auto-scopes it → perform a data read/write → the Data Access log flows to the central sink.
- **Restore = pre-run + optional live kickoff (decided).** Shown evidence is a pre-run restore record (integrity invariant + elapsed vs SLA); optionally kick a fresh live restore early and circle back, but never depend on it completing live.
- **Alert channel = Google Chat (confirmed).** Alert on transitions, not levels: the dashboard is the source of truth for current health; Chat carries a per-run digest + immediate high-severity transitions (new/changed FAIL, UNKNOWN/loss-of-visibility, incomplete run, integrity-chain break), threaded per run, severity-routed, deep-linked to the dashboard. Not one message per finding.
- **OSCAL constructs (decided; field spelling validated against oscal-content at build):** evidence → Assessment Results `observation` (method TEST, `collected`) + `finding` (target = control, status satisfied/not-satisfied) under `results`; per-control OSI inventory → SSP `component` + `inventory-item`, with `leveraged-authorization` for the GCP-inherited slice. Start from the FedRAMP OSCAL templates in `oscal-content` and validate with their tooling rather than hand-authoring. **OSCAL is a stretch goal — build it only if the core pipeline is solid.**
- **Control-mapping corrections (verified against the FedRAMP High baseline workbook):**
  - **Encryption-at-rest = SC-28 / SC-28(1) / SC-13, not AU-9(3).** AU-9(3) is the *integrity* of audit information — it's the home for the per-record hash / KMS-signing, so the fix actually strengthens the integrity story.
  - **High-risk-change detection = SI-4 / CA-7 / AU-6(5); prevention = CM-5 / AC-6(9) — not AU-12(3).** AU-12(3) is "the capability for *authorized* roles to change logging," which is the wrong control for detect/prevent-unauthorized-change. **IAM access-grant changes are in the detection set** (answers the assumptions-doc question: yes, alert on them, especially on the evidence bucket + audit-config).
  - **Retention adds C1.2** (disposal/retention of confidential info) alongside C1.1. AU-11 High verified = on-line ≥90d + off-line per NARA + M-21-31 export capability; 365d is this project's canonical simplification.
- **Backup "3 copies / ≥1 online" (decided measurement).** FedRAMP wording verified as "…*or provides an equivalent alternative*." GCP mapping for the equivalent alternative = automated-backups-on + PITR/binlog-on + cross/dual/multi-region destination; freshness is **PITR-aware** (recovery-point currency, not just last-full-backup age). Avoids false FAILs on well-protected instances.
- **Data Access eligibility floor (decided).** Eligibility = type + environment (prod-tier Cloud SQL/BigQuery/Spanner regulated-eligible by default, from metadata, no content inspection); the `data-classification` label **narrows within** the floor but **cannot exempt** — an eligible store with logging off is a FAIL. Refines the assumptions-doc label approach without contradicting the "no content inspection" constraint.
- **Integrity scope (decided).** Primary anti-tamper = locked GCS Bucket Lock; per-record SHA-256 = AU-9(3) integrity + re-performance; the **run-digest chain is a §7 extension, not a demo centerpiece** (Bucket Lock already prevents backfilling; the collector SA is a trusted root).
- **Guardrails: collect, don't author (decided).** Aegis *reads* IAM Deny / Org Policy config as evidence; standing them up is environment config, out of scope.
- **Completeness keyed by project × region (decided).** Region completeness is a named requirement — a region holding in-scope resources with no record is a run FAIL.

---

### References (authoritative)
- GCS Bucket Lock — docs.cloud.google.com/storage/docs/bucket-lock
- Claude Code hooks — code.claude.com/docs/en/hooks · Agent SDK hooks — platform.claude.com/docs/en/agent-sdk/hooks
- Org log sink pattern — github.com/GoogleCloudPlatform/deploystack-auditlogs-to-bq
- OSCAL — github.com/usnistgov/OSCAL · FedRAMP baselines in OSCAL — github.com/usnistgov/oscal-content
- GCP client samples — github.com/GoogleCloudPlatform/python-docs-samples · /professional-services
