# Aegis — Control Coverage Matrix (FedRAMP High + SOC 2)

*Crypto Widget automated evidence-collection platform. Purpose: confirm every control element is captured by a concrete build component, produces a defensible **evidence record**, and has explicit **PASS / FAIL / UNKNOWN** logic — and that the evidence system itself proves its own **completeness** and **accuracy** for audit reliance.*

**Legend** — **Capture** = what evidences it · **Evidence** = the immutable record produced · **Verdict** = how PASS/FAIL/UNKNOWN is decided.
**SOC 2 scope:** Security (CC), Availability (A), Confidentiality (C). Processing Integrity / Privacy out of scope.
**Canonical target = the project scope** (e.g., retention ≥365d wins over broader real-world figures).
**Provenance:** control IDs/parameters sourced from the FedRAMP High Rev5 baseline (OSCAL via `usnistgov/oscal-content`); collectors are **native, evidence-first code** — Prowler/ScoutSuite/Steampipe studied as prior art only (field selection, mapping validation), **never a runtime dependency**; each record serializes to OSCAL Assessment Results (observation + finding).

---

## 1. Audit Logging & Log Retention Integrity

| Element | FedRAMP High / SOC 2 | Capture | Evidence | Verdict |
|---|---|---|---|---|
| Audit logging enabled (config) | AU-2, AU-12(a) / CC7.2 | `projects.getIamPolicy` → read `auditConfigs`; Admin Activity always-on | Per-project audit-config snapshot (raw IAM policy excerpt) | PASS if required `auditConfigs` present, **no `exemptedMembers`**; FAIL if missing/exempted; UNKNOWN if API denied |
| Required event coverage | AU-2 High event set, AU-3 / AU-3(1) | Map AU-2 High classes (logon success+fail, account mgmt, object access, policy change, privileged functions, process tracking, system events; web-app: admin activity, authn/authz, data access/changes/deletes, permission changes) → GCP log types | Coverage map: event class → GCP log type → enabled? | PASS only if every required class covered; FAIL on any gap |
| Data Access logging scoped to regulated stores | AU-2 / CC7.2, C1.1 | Data Access logs **off by default**. **Eligibility = type + environment** (e.g., all Cloud SQL / BigQuery / Spanner in prod-tier projects are regulated-eligible *by default* — derived from resource metadata, **no content inspection**); the `data-classification=regulated` label can **narrow within** the eligible set but **cannot exempt** an eligible store from scope. Check `DATA_READ`/`DATA_WRITE` on (config switch, not data contents). *(Same "type/location-driven, a tag can't let a store escape scope" principle used for backups — closes the mislabel hole.)* | Per-store data-access-config record | PASS if eligible store has DATA_READ/WRITE on, no exemptions; **FAIL if an eligible store has it off** (not merely a finding); unlabeled non-eligible store → no finding. *(Implemented label-driven: a `data-classification=regulated` store makes its project in-scope; the type+environment floor is the documented future hardening — an unlabeled regulated store is an honestly-disclosed blind spot.)* |
| Logs exported to central destination | AU-6(3), AU-6(4), AU-9(2) / CC7.2 | Org-level **aggregated sink** (`google_logging_organization_sink`, `include_children=true`); confirm destination + **no unexpected exclusion filters**; dest is a separate project (AU-9(2)) | Sink-config record (destination, filter, exclusions, children flag, dest project) | PASS if aggregated sink routes all in-scope projects, no silent exclusions; FAIL on exclusion/child gap |
| Retention meets policy | AU-11, SI-12 / C1.1, **C1.2** | Read destination retention. **Policy target = 365 days (project scope is canonical).** *Verified against the FedRAMP High baseline: AU-11 High = on-line ≥90 days + off-line per NARA + an M-21-31 export-capability requirement; 365d clears the 90-day floor, and prod would target M-21-31's tiered 12-mo-active / 18-mo-cold — worth noting for FedRAMP-literate reviewers.* Retention/immutability targets a **locked Logging bucket or GCS Bucket Lock** destination (BigQuery is the analysis/index layer, not the retention surface). *(C1.2 = disposal/retention of confidential info; C1.1 = its maintenance.)* | Retention record (retention days, lock state, storage class) | PASS if retention ≥ **365 days** **and locked**; FAIL if below or unlocked |
| Immutability / WORM | AU-9, SI-12 / CC6.1 | Confirm **GCS Bucket Lock retention policy `locked: true`**; versioning on. *(Bucket Lock is a retention/immutability control, not a cryptographic one — AU-9(3) crypto-integrity lives on the tamper-evidence row.)* | Immutability record (lock state, retention, versioning) | PASS only if retention policy **locked** — *unlocked ≠ immutable*; FAIL otherwise |
| Crypto protection of audit info (at rest) | **SC-28, SC-28(1), SC-13** / CC6.1 | Confirm **FIPS 140-validated** encryption; read key type + protection level; CMEK (SC-12) only where the org's key-management parameter requires it. *(Encryption-at-rest is SC-28/SC-13, not AU-9(3) — AU-9(3) is the **integrity** of audit info, evidenced in the row below.)* | Crypto record (FIPS status, key type, protection level, rotation) | PASS if encrypted per org key-management parameter (FIPS-validated; CMEK/HSM only if required); FAIL if not FIPS-validated or a required CMEK/HSM key absent — **not** an automatic FAIL for Google-managed keys |
| Integrity of evidence (tamper-**evident**) | **AU-9(3)** (crypto integrity of audit info), AU-9, AU-10 (non-repudiation) / CC6.1 | **Primary anti-tamper = GCS Bucket Lock (locked WORM)** — immutable, no edit/delete, prevents backfilling mechanically. **Per-record SHA-256** + endpoint/timestamps enables re-performance and detects any single-record edit. CMEK on bucket; detailed access logging. *Chained run-digest (appending prior run's hash) is an **extension**, not core — Bucket Lock already does the anti-backfill heavy lifting and the collector SA is a trusted root, so the chain's marginal assurance is low.* | Locked-retention state + per-record hash + access log | Integrity FAIL if a record's recomputed hash ≠ stored hash, or if Bucket Lock is unlocked/absent. *(KMS/HSM signing of records in a segregated project removes the collector-trust assumption — §7 extension)* |
| Access restricted to subset | AU-9(4) / CC6.3 | Read IAM on log/evidence buckets; log-reader role least-privilege | IAM-on-logs record | PASS if read access ⊆ defined privileged set; FAIL on broad grant |
| Logging-process-failure handling + alerting | AU-5, AU-5(1), **AU-5(2) real-time**, AU-4 / CC7.2 | Log-based metric + Cloud Monitoring alert on logging/export failure; failure behavior = overwrite-oldest (AU-5 b); capacity warning at 75% (AU-5(1)) | Alert-config record + fired-alert log | PASS if real-time alert policy exists and routes; FAIL if absent |
| Audit-config / high-risk change detected | **SI-4, CA-7, AU-6(5)** / CC7.1, CC7.2 | Log-based metric + alert on `SetIamPolicy` w/ `auditConfigDeltas`, **IAM role grants (esp. on the log/evidence bucket and audit-config)**, `sinks.delete`, retention change, bucket-permission / custom-role / project-ownership / SQL-instance-config changes (each a concrete log-based-metric filter). *(Detection of unauthorized change is SI-4/CA-7 monitoring — not AU-12(3), which is the capability for **authorized** roles to change logging.)* | Detection-rule record | PASS if detective rules present and route; FAIL otherwise |
| **Prevention** of unauthorized change | **CM-5** (access restrictions for change), **AC-6(9)** (log use of privileged functions) / CC6.1, CC8.1 | **Read** (evidence, don't author) the **IAM Deny** on `sinks.delete`, retention-update, `auditConfigs` `setIamPolicy` except monitored break-glass + **Org Policy** guardrails. Standing the guardrails up is environment config; Aegis evidences that they exist. *(AU-12(3)'s "authorized individuals only" intent is subsumed here under CM-5.)* | Deny-policy + org-policy record | PASS if deny policy attached at org/folder with monitored break-glass; FAIL/UNKNOWN otherwise |
| No project/region excluded | AU-12(a), **CM-8** / CC2.1 | CAI enumeration (org/boundary, deterministic) reconciled against type-driven + label-scoped requirements; Asset **feed** (Pub/Sub) for new resources; unenrolled/unconfigured resources → findings. **Completeness asserted per (project × region):** every region holding in-scope resources must produce records — a region with in-scope resources and no record is a run FAIL, not a silent omission (regions are named explicitly in the requirements). | Completeness reconciliation record (§3), keyed by project×region | **Run = FAIL if any in-scope resource lacks a record**; unenrolled findings raised separately |
| Review / analysis workflow | AU-6, AU-6(a) (≥weekly), AU-6(4) | Dashboard surfaces per-control state for the ≥weekly review; BigQuery index over logs | (dashboard + stored evidence) | n/a — supports the human review control |
| Historical sampling | AU-11, SI-12 / CC4.1 | Date-partitioned WORM objects; BigQuery index; sample served = the WORM object itself (§4) | (the stored evidence) | n/a — **Bucket Lock immutability** + per-record hash prevent backdating |

---

## 2. Backup & Restore Validation

| Element | FedRAMP High / SOC 2 | Capture | Evidence | Verdict |
|---|---|---|---|---|
| Required systems have backups | **CP-9(a)** / A1.2 | Enumerate **all resources of in-scope backup-eligible types** within the boundary via CAI (**type-driven, not label-driven** — a DB/disk needs backups by virtue of its type); read snapshot schedules / Cloud SQL backup config. **Verified FedRAMP wording: CP-9(a/b/c) = "≥3 backup copies, ≥1 online, *or provides an equivalent alternative*."** GCP doesn't expose a literal "copy count = 3", so define the mapping: **equivalent-alternative posture = automated backups ON + PITR/binlog ON + cross-region or dual/multi-region destination**; Compute = scheduled snapshots with ≥N retained + a cross-region copy. | Per-system backup-config record (automated-backups, PITR, retained count, destination geo, online copy) | PASS if **(≥3 retained copies w/ ≥1 online)** OR **(equivalent-alternative posture above)**; FAIL if none / single-copy with no PITR / no cross-region; UNKNOWN if config unreadable |
| RPO / freshness | CP-9, CP-6(2) / A1.2 | Age of latest successful backup vs. a **single policy RPO** (CP-9 daily-incremental/weekly-full ⇒ ~24h). **PITR-aware:** where PITR/binlog is enabled, freshness = recovery-point currency (binlog/transaction-log recency), not last full-backup age — a 25h-old automated backup with current PITR is **not** a stale-RPO FAIL. | Freshness record (last-backup ts, age, RPO, delta, pitr_enabled, recovery-point currency) | PASS if backup age ≤ RPO **or** PITR window current; FAIL if stale beyond RPO with no current recovery point |
| Cadence | CP-9 (a/b/c) [**daily incremental; weekly full**] | Confirm schedule meets daily-incremental / weekly-full | Cadence record | PASS if schedule ≥ baseline cadence; FAIL otherwise |
| Retention | CP-9, SI-12 / A1.2, C1.1, **C1.2** | Read backup retention policy; alert on change | Retention record | PASS if retention ≥ required; changes PR-approved (§1 prevention) |
| Encryption (FIPS) | **CP-9(8)** [all backup files], SC-13/SC-28 / CC6.1 | Read per-resource encryption + key type + protection level; primitive inherited via Google's **FedRAMP authorization + CRM**, customer-responsible config evidenced; CMEK only where org parameter requires | Encryption record (FIPS status, key type, CMEK ref if applicable, protection level) | PASS if encrypted per org key-management parameter; FAIL if not FIPS-validated or required CMEK absent |
| **Restore actually works** | **CP-9(1)** (≥monthly), **CP-9(2)** (test restoration using sampling), CP-10(4) / **A1.3** | Scheduled **sampled live test restore** (Cloud SQL backup → temp instance → integrity check → teardown); restore within SLA; result written to the evidence log. Compute-disk restore described as the extension. | Restore-test record (operation log, integrity result, elapsed vs SLA) | PASS if sampled restore succeeded **and** integrity invariant (row-count/checksum on seeded table) passed within SLA; FAIL otherwise |
| Backup-failure handling | A1.2 (corrective action) | Detect failed backups; track until subsequent success within RPO **or** linked ticket | Exception record (FAIL → closing PASS / ticket) | FAIL stays **open** until closed; open beyond RPO = escalation |
| Offsite / recoverability | CP-6, CP-6(1), CP-9(5) / A1.2 | Confirm cross-region backup location separated from primary | Location record | PASS if backup region-separate from primary; FAIL if co-located |

---

## 3. Completeness & Accuracy — the evidenced control *of the evidence system*

> Aegis doesn't just collect evidence; each run produces evidence that the collection itself was **complete** and **accurate**, and that the evidence cannot be backfilled.

**Completeness — boundary by org structure; enrollment type-driven (label-driven only where type can't tell you); CAI is the check.**
- **Authorization boundary = org/folder structure.** In-scope projects live under the org node (a defined FedRAMP boundary folder); the population denominator is the deterministic CAI enumeration under that node — **never a model's judgment**.
- **Enrollment is type-driven where the requirement is inferable from the resource type, label-driven only where it isn't:**
  - **Backups** attach to the *type* — every in-scope Cloud SQL instance / Compute disk within the boundary is required to have a compliant backup (no label needed; a missing tag can't let a database escape scope).
  - **Data Access logging** uses a **type+environment eligibility floor** (e.g., Cloud SQL / BigQuery / Spanner in prod-tier projects are regulated-eligible by default, from metadata — no content inspection); the `data-classification=regulated` label can **narrow within** that floor but **cannot exempt** an eligible store. This keeps the label useful without letting a mislabel create a blind spot.
  - **Audit-log capture** is neither — the org aggregated sink (`include_children=true`) routes all projects automatically.
- **CAI enumeration is the check.** Each run reconciles: every in-scope resource must produce exactly one record (gap → **run FAIL**); any backup-eligible resource with no backup config → an **unenrolled/unconfigured finding**; any **eligible-by-type-and-environment** store with Data Access logging **off** → a **FAIL** (the label can't exempt it), while a non-eligible store is simply out of scope (how an untagged or misconfigured prod store still answers "did you miss it?").
- **CAI is the denominator but isn't omniscient** — it covers supported resource types with some ingestion latency. Aegis documents the **coverage boundary** (which types are in the population) rather than claiming total omniscience.
- New resources auto-appear via the Asset Inventory **feed** (Pub/Sub on change).
- Log export: confirm `include_children=true` and **no unexpected exclusion filters** (the org-sink `exclusions` block is exactly where a silent gap originates) **+** bounded **source↔destination sampling reconciliation** as the accuracy spot-check.
- **Verdict: run = incomplete (FAIL) if any in-scope resource is unaccounted for; unenrolled findings raised separately.** Partial success is not success.

**Accuracy — provenance + re-performance.**
- Control IDs/parameters sourced from the **FedRAMP High Rev5 baseline in OSCAL** (`oscal-content`), not hand-typed — traceable to NIST/FedRAMP machine-readable source.
- Each record stores the **raw API observation**, source endpoint, `collected_at`, `collector_version`, `policy_version` — not just the verdict.
- Verdict is a **pure deterministic function** of the raw observation, **stamped at write time and recomputable at read time** (re-perform routine recomputes from raw and asserts equality — auditor re-performance test).
- Policy-logic changes do **not** rewrite historical records; they stand under their stamped `policy_version`, new logic forward-only.
- Each record serializes to an **OSCAL Assessment Results** document: raw observation → OSCAL `observation`; verdict → OSCAL `finding` (target = control, status satisfied/not-satisfied). Ingestable by OSCAL-aware GRC/FedRAMP tooling. *(OSCAL construct names per the standard; confirm against oscal-content at build.)*

**Chain of custody — tamper-evident (current scope).**
- **Primary anti-tamper = the locked WORM bucket** (GCS Bucket Lock, no edit/delete, can't be shortened) + CMEK + access logging. This is what mechanically prevents backfilling and tampering, and it needs no caveat in front of an auditor.
- Each evidence record also carries its own **SHA-256** (with source endpoint + timestamps), which powers re-performance and detects any single-record edit — this is the **AU-9(3)** crypto-integrity mechanism (cryptographic protection of the *integrity* of audit information).
- **Chaining run digests (appending the prior run's hash) is an extension, not core.** Bucket Lock already does the anti-backfill heavy lifting, and the collector SA computes the hashes, so it's a trusted root — a compromised collector could regenerate a clean chain. Building/demoing chain-verify spends time on a mechanism whose marginal assurance you'd have to disclaim in a demo. Lead with Bucket Lock; mention the chain (and **KMS/HSM signing in a segregated project, AU-10/AU-9(3)**) as the §7 upgrade that removes the collector-trust assumption. No blockchain/ZKP — say so explicitly.

---

## 4. Dashboard, Continuous Monitoring & Auditor Sampling

| Element | FedRAMP High / SOC 2 | Capture |
|---|---|---|
| Control-health dashboard | **CA-7**, AU-6(4) / **CC4.1, CC4.2** | Per-control × per-scope state (PASS/FAIL/UNKNOWN), freshness age, open exceptions. The dashboard *is* the ongoing-evaluation + deficiency-communication surface |
| Continuous / scheduled collection | CA-7 / CC4.1 | Cloud Scheduler → Cloud Run Job + Asset-feed/Pub-Sub event triggers. Freshness SLO = max age of latest evidence per (control, resource) |
| Error + partial-failure alerting | AU-5(2), SI-4 / CC4.2, CC7.2 | **UNKNOWN is first-class** (permission/API error ≠ PASS) → Pub/Sub → Google Chat; counts against completeness. **Loss of visibility is high-severity** — an attacker can turn a FAIL into an UNKNOWN by removing the collector's read access, so going blind is treated as suspicious, not benign |
| Auditor sampling read path | AU-11, AU-9, SI-12 / CC4.1 | Dashboard filters (control × project × date) query **BigQuery as a non-authoritative index**. "Pull sample" returns the actual **WORM GCS object(s)**, **re-verifies the per-record hash and shows the Bucket Lock state** on the fly, displays raw observation + verdict. *BQ never serves as the verdict source* |
| Durable, sampleable store | AU-11, SI-12 / CC4.2 | WORM GCS (canonical) + BigQuery (index/query) |

---

## 5. Verdict model (stable across all controls)

`PASS` — observed config satisfies the control parameter.
`FAIL` — observed config violates it (with the specific reason).
`UNKNOWN` — could not observe (permission denied, API error, resource skipped). **Never silently PASS.** UNKNOWN is high-severity, triggers alerting, and counts against completeness.

---

## 6. AI boundary & what TRM would actually run (at scale)

Built as if deploying inside TRM. **Zero LLM anywhere in the runtime** — not in the verdict path, not in discovery, not in orchestration. Deliberate: it's what makes the scale and cost story airtight (deterministic Cloud Run scales predictably; no per-run token cost; nothing to attack on "how do you know the model didn't skip a project").

- **Production engine = deterministic, Terraform-deployed Cloud Run** invoking versioned Python collectors on schedule + Asset-feed/Pub-Sub event triggers. Enumeration is a deterministic **CAI** call — never a model's judgment — so the completeness denominator can't be pinned on an LLM.
- **AI is the build accelerator, and only that.** Claude Code (skills, subagents, **hooks**) authors/maintains collectors, schema, control mappings, tests. Hooks enforce determinism + SoD at build: `PostToolUse`/test hook blocks a commit if a verdict function isn't pure or a re-performance test fails; `PreToolUse` blocks any non-allowlisted `gcloud` mutation. AI's role is confined to accelerating the **build**.
- **Collectors are native** — Prowler/ScoutSuite/Steampipe studied as prior art only (field selection, mapping validation), never a dependency. A posture scanner emits a transient PASS/FAIL with no population denominator and no immutable record, so it answers neither "did you miss a project?" nor "how do you prevent backfilling?". Aegis is exactly the pipeline that does.
- Subagent "SoD" is build organization. **Runtime SoD is identity:** write-once collector SA vs. a separate admin identity owning Org Policies and the bucket lock.

## 7. Extensions ("with more time")

- **Stronger chain of custody:** KMS/HSM signing of each record (or per-run Merkle root) in a segregated integrity project — removes the collector-trust assumption, full AU-10 non-repudiation.
- Tiered RPO via a `backup-tier` label (per-system recovery objectives) instead of a single policy RPO.
- Change-management correlation (CC8.1 / CM): correlate high-risk audit events to a change ticket/PR.
- Full automated restore harness across **all** in-scope systems (Compute-disk + GKE) vs. sampled Cloud SQL.
- Drift detection: live CAI state vs. Terraform state.
- Native **FedRAMP 20x KSI** output alongside Rev5 mapping — aligns with FedRAMP's machine-readable direction.
- **Optional read-only AI layer:** MCP query server for auditor self-service + alert triage — human-invoked, read-only, off the collection path. Kept out of core to preserve an LLM-free runtime and a clean scale story.
