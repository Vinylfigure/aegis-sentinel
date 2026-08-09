# Aegis Sentinel — Learnings Genome

This file is the project's **learnings genome** in the Janus discipline (charter: corpus `04_build_prds/Sentinel_JIT_UI_DB_Janus.md` §4). Rules:

- **Append-only.** Entries are appended, never edited in place and never deleted. A wrong or outdated entry is superseded by a later entry, not rewritten.
- **Status is one of three values:**
  - `CANDIDATE` — believed true, sourced, but no fixture test yet proves the system acts on it correctly.
  - `PROMOTED` — a passing fixture test demonstrates the learning is real. Promotion **requires naming the fixture/test that proves it**; a promotion without a named proof is invalid.
  - `STALE` — drift detected: the fact has been superseded by a later entry. The stale entry stays in the file, pointing at its successor. Never deleted.
- **Evidence-gated promotion** (the middle loop): a candidate is promoted only when a passing fixture test demonstrates it — this is the discipline that stops the genome accumulating plausible-sounding folklore.
- **Scheduled recalibration** (the outer loop): a heartbeat re-verifies external-API facts in this genome against live behaviour, because the corpus itself records facts that changed underneath it (see `02_design_decisions/Version_Drift_Ledger.md` — its own headline is "the correction itself carries drift"). Any entry about GitHub, AWS, Slack, Replit, FedRAMP, or the SCF release is a recalibration target.
- **Failure-lane tags** (from `02_design_decisions/API_Constraints_By_Trust_Consequence.md`): `lane1_fail_loud` (agent may learn/own — wrong value throws), `lane2_runner_assert` (fail-silent completeness trap — deterministic runner/verifier must own), `lane3_human_owned` (semantic/judgment — human ratification required). Tagged only where the corpus assigns one.
- Source paths are relative to the corpus root (`~/PycharmProjects/aegis-corpus/`).

---

## GitHub API

### L-001 — GitHub returns 404, not 403, for resources the token cannot see
- **Date:** 2026-07-25 · **Status:** PROMOTED · **Lane:** lane2_runner_assert
- **Fact:** Some GitHub endpoints "return 404-for-403" — a missing resource and a forbidden resource are indistinguishable to the caller. A 404 on an expected resource must therefore be treated as UNKNOWN (visibility/permission gap), never as evidence of compliant absence. The 404 ambiguity is explicitly Lane 2 (runner assertion), while endpoint paths and parameter names are Lane 1.
- **Source:** `04_build_prds/Sentinel_JIT_UI_DB_Janus.md` §4, §5.
- **Proof:** `tests/test_seeded_failure.py` (seeded 404-for-403 case) with the visibility probe in `src/probe.py`.

### L-002 — A partial collection is a population-level UNKNOWN, never a partial pass
- **Date:** 2026-07-25 · **Status:** PROMOTED · **Lane:** lane2_runner_assert
- **Fact:** A collection that completes partially (pagination not exhausted, API returned a subset, connector-style "exit 4 partial" with the run continuing) is the fail-silent completeness leak; the intake/runner must convert it into a hard UNKNOWN(basis_missing) at population level. This is a deterministic runner assertion, not a convention.
- **Source:** `05_prior_art/Aegis_Prior_Art_GRCEngClub_Toolkit.md` §3.4 (the exit-code-4 trap); `02_design_decisions/API_Constraints_By_Trust_Consequence.md` Lane 2.
- **Proof:** `src/completeness.py` (partial-collection → UNKNOWN rule) and `tests/test_seeded_failure.py`.

### L-003 — Pagination exhaustion is a runner assertion, never agent memory
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane2_runner_assert
- **Fact:** Every population pull must assert pagination exhaustion (cursor drained, not first-page-only) — standard C&A attribute C2. Which endpoints paginate (and which lie about counts) is exactly the class of environmental knowledge each collector port teaches.
- **Source:** `03_testing_libraries/SOC2_TSC_Agent_Testing_Library.md` §2 (C2); `04_build_prds/Sentinel_JIT_UI_DB_Janus.md` §4.

### L-004 — `/orgs/{org}/outside_collaborators` has no independent count endpoint
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane2_runner_assert
- **Fact:** There is no independent count endpoint for outside collaborators, so the completeness basis for that population must be `exhaustive_pagination` (the corpus's own example of a genome-promotable learning).
- **Source:** `04_build_prds/Sentinel_JIT_UI_DB_Janus.md` §4 (middle-loop example).

### L-005 — Register the webhook at organization level, with the four event types
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** One org-level hook covers every repository including ones created later (a repo created without protection is exactly the case to catch); per-repo hooks do not. Subscribe to `branch_protection_rule` (created/edited/deleted), `repository_ruleset` (created/edited/deleted), `branch_protection_configuration` (enabled/disabled), and `repository` (created); answer `ping` with 200 so registration succeeds.
- **Source:** `04_build_prds/Sentinel_v0.2_Event_Driven_Agentic_OSCAL.md` (event ingestion; Part B).

### L-006 — Deduplicate webhook deliveries on the `X-GitHub-Delivery` GUID
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** Every delivery carries a unique `X-GitHub-Delivery` GUID; GitHub retries on failure, so the GUID must be stored and repeats ignored or events get double-recorded.
- **Source:** `04_build_prds/Sentinel_v0.2_Event_Driven_Agentic_OSCAL.md`.

### L-007 — The org-hook deliveries endpoint makes delivery completeness enumerable
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane2_runner_assert
- **Fact:** `GET /orgs/{org}/hooks/{hook_id}/deliveries` enumerates recent deliveries with status; a non-successful delivery is a gap whose detail can be fetched and redelivered. Gaps and their resolutions are ledger-recorded — a failed-and-recovered webhook is a completeness event worth evidencing.
- **Source:** `04_build_prds/Sentinel_v0.2_Event_Driven_Agentic_OSCAL.md` (delivery completeness).

### L-008 — Reading hook deliveries needs organization-administration read on the token
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** The `/orgs/{org}/hooks/{hook_id}/deliveries` call requires "organization administration: read" added to the fine-grained token — still read-only.
- **Source:** `04_build_prds/Sentinel_v0.2_Event_Driven_Agentic_OSCAL.md` Part B.

### L-009 — Verify webhook HMAC over raw body bytes, constant-time, and ledger rejections
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** GitHub signs each delivery with HMAC-SHA256 in `X-Hub-Signature-256`, computed over the **raw request body**. Verify against the raw bytes (not a re-serialized parse) using constant-time comparison; reject mismatches with 401 and record the rejection in the ledger — a forged or misconfigured delivery is itself a security event. Capture the full payload verbatim, hashed as received, before any interpretation.
- **Source:** `04_build_prds/Sentinel_v0.2_Event_Driven_Agentic_OSCAL.md` (event ingestion).

### L-010 — Dropped deliveries are fail-silent; the hourly sweep is the completeness proof
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane2_runner_assert
- **Fact:** A dropped webhook delivery produces nothing, and nothing is indistinguishable from no-change-occurred. The hourly reconciliation (delivery audit + full state re-collection vs. the event stream's implied state) is not a second detector — it is the proof the first didn't miss anything. A live-vs-event-stream mismatch is a high-severity `completeness_gap` finding. Every evaluation records its mode (`event` or `reconciliation`) as meaningful evidence; assessors are entitled to the detection window.
- **Source:** `04_build_prds/Sentinel_v0.2_Event_Driven_Agentic_OSCAL.md` (delivery completeness; "Why the sweep survives").

### L-011 — [superseded] "GitHub has no read-only access to private repos"
- **Date:** 2026-07-25 · **Status:** STALE (superseded by L-012)
- **Fact:** The corpus's early claim that GitHub forces write-bearing `repo` scope for private-repo reads is true **only for classic OAuth scopes** and stale as a general statement.
- **Source:** `02_design_decisions/Contradictions.md` (GitHub scopes entry); corrected in `02_design_decisions/Version_Drift_Ledger.md` §5.

### L-012 — Fine-grained PATs / GitHub Apps give read-only private-repo access; never carry `repo` scope on the evidence path
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** Fine-grained PATs and GitHub App installation tokens grant `Repository contents: Read-only` (+ `Metadata: Read-only`, plus Pull requests / Commit statuses read as needed) on private repos; a GitHub App is the more robust production path. The evidence-read collector must never hold the classic write-bearing `repo` scope — that over-grant is itself an ITGC finding. Residuals: a small set of endpoints still lack fine-grained support, and "read-only" does not prevent issue creation on public repos.
- **Source:** `02_design_decisions/API_Constraints_By_Trust_Consequence.md` correction 3; `02_design_decisions/Version_Drift_Ledger.md` §5; `02_design_decisions/Control_Evidence_API_Chain_Verified.md` Domain 5.

### L-013 — Open question: is fine-grained PAT `created_at` API-readable?
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane3_human_owned (fallback)
- **Fact:** Whether a fine-grained PAT's `created_at` is readable via API — needed for the 90-day token-age assertion — was unresolved at PRD time. If it is not, the assertion falls back to a manual attestation record: an honest UNKNOWN in the human-attest lane, not a fabricated PASS.
- **Source:** `04_build_prds/Sentinel_Build_Execution_PRD.md` §7 (open questions, NEED 7/26).

### L-014 — GitHub token creation limits and scope normalization fail loud
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane1_fail_loud
- **Fact:** 10 tokens per user/app/scope and a 10-token/hour creation limit (throttled visibly); scope normalization collapses redundant scopes (`user, user:email` → `user`), surfacing in the `X-OAuth-Scopes` header; `X-OAuth-Scopes` / `X-Accepted-OAuth-Scopes` are the debugging surface. All fail-loud — safe in the agent's self-learning lane.
- **Source:** `02_design_decisions/API_Constraints_By_Trust_Consequence.md` Lane 1.

### L-015 — Org-level audits require a real org, not personal repos
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** External collaborators, teams, and CODEOWNERS audits are org-level concepts that will not exercise against personal repositories — hence the dedicated fixtures **org** (`vinylfigure-fixtures`, repos tagged `aegis-fixture`) as the Troublemaker target.
- **Source:** `04_build_prds/Sentinel_Build_Execution_PRD.md` §3.

## Slack

### L-016 — Slack needs public HTTPS and an acknowledgment within 3 seconds
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** Slack endpoints must be publicly reachable over HTTPS and respond inside 3 seconds — acknowledge immediately and process in the background. A cold start that eats the window kills the interaction, which is the argument for a reserved (warm) instance on demo day.
- **Source:** `04_build_prds/Sentinel_Build_Execution_PRD.md` §4.

### L-017 — Slack approval preconditions: valid signature with timestamp inside 5 minutes, then the deterministic chain
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** The JIT approval handler checks, in order and all required: signature valid with timestamp inside 5 minutes (replay defense), approver ∈ ratified roster, approver ≠ requester, repo ∈ JIT-eligible allowlist, TTL ≤ cap. Any failure = deny + ledger record. (For signature checks generally, the corpus rule is verify over raw body bytes — see L-009.)
- **Source:** `04_build_prds/Sentinel_JIT_UI_DB_Janus.md` §1 (flow step 3).

### L-018 — A Slack outage must not be able to extend a JIT grant
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** The revoker cron (every 5 minutes) reads only the database and the write-scoped token, and restores the captured `prior_permission` (never a hardcoded default) at expiry. It retries ×3 then raises CRITICAL and writes a FAIL finding. Revocation is deliberately independent of Slack.
- **Source:** `04_build_prds/Sentinel_JIT_UI_DB_Janus.md` §1 (flow step 5).

## Replit

### L-019 — Replit deployments have separate filesystems; shared state must live in Postgres
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** The always-reachable web deployment and the scheduled monitor deployment are separate processes with separate filesystems — which is exactly why the ledger lives in Postgres (F-1), not on disk. JIT grant state and ratification records need the database for the same reason.
- **Source:** `04_build_prds/Sentinel_Build_Execution_PRD.md` §4; `04_build_prds/Sentinel_JIT_UI_DB_Janus.md` §3.

### L-020 — Use Replit's built-in PostgreSQL, not the key-value DB or object storage
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** The key-value Replit DB gives no ordering guarantees or transactional insert for a hash chain; object storage adds latency to a small, high-integrity relational workload. The built-in PostgreSQL (Neon-backed as of the doc's knowledge cutoff) is provisioned from the workspace and exposed as `DATABASE_URL`. Current offering and free-tier limits flagged for in-product verification — recalibration target.
- **Source:** `04_build_prds/Sentinel_JIT_UI_DB_Janus.md` §3; `04_build_prds/Sentinel_Build_Execution_PRD.md` §4.

### L-021 — Append-only is enforced by grant, and it is tamper-evidence, not immutability
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** The ledger table is made append-only by `REVOKE UPDATE, DELETE, TRUNCATE` with the app connecting as a role holding only `INSERT, SELECT` — a grant, not a convention. Even that is tamper-*evidence*: an owner-role connection can still rewrite rows; the hash chain is what makes rewriting detectable. State it precisely.
- **Source:** `04_build_prds/Sentinel_JIT_UI_DB_Janus.md` §3.

## AWS (recalibration targets)

### L-022 — [superseded] "S3 Object Lock can only be enabled at bucket creation"
- **Date:** 2026-07-25 · **Status:** STALE (superseded by L-023)
- **Fact:** The corpus's original constraint ("cannot be retrofitted to existing buckets") has been false since November 2023; carrying it forward was itself caught as drift.
- **Source:** `02_design_decisions/Constraints.md` (Audit Log Storage); corrected in `02_design_decisions/Version_Drift_Ledger.md` §1.

### L-023 — Object Lock retrofits onto existing versioned buckets; versioning stays a fail-loud prerequisite
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane1_fail_loud (versioning prerequisite)
- **Fact:** Since Nov 20, 2023, Object Lock can be enabled on an existing bucket (versioning required, no support ticket), and existing objects are locked in bulk via S3 Batch Operations driven off an S3 Inventory manifest, in COMPLIANCE or GOVERNANCE mode. There is no architectural blocker to WORM-protecting a pre-existing evidence bucket. The enable call fails without versioning — fail-loud.
- **Source:** `02_design_decisions/Version_Drift_Ledger.md` §1; `02_design_decisions/API_Constraints_By_Trust_Consequence.md` correction 1 and Lane 1.

### L-024 — [superseded] "Identity Store `UserStatus` returns ENABLED | DISABLED | UNKNOWN"
- **Date:** 2026-07-25 · **Status:** STALE (superseded by L-025)
- **Fact:** The three-value enum recorded in `Contradictions.md` is an overstatement; the live API reference lists two values. The overstatement was re-imported into a correction once already — the exact failure mode the drift ledger exists to catch.
- **Source:** `02_design_decisions/Contradictions.md`; corrected in `02_design_decisions/Version_Drift_Ledger.md` §2.

### L-025 — `UserStatus` is `ENABLED | DISABLED` only; write the predicate two-value and treat a missing field as your own UNKNOWN
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane3_human_owned (predicate semantics)
- **Fact:** `UserStatus` plus `CreatedAt`/`CreatedBy`/`UpdatedAt` were added to the Identity Store User/Group/Membership APIs on 2025-11-06 — collectors must run an SDK/CLI build from Nov 2025 or later. Valid values are `ENABLED | DISABLED`; there is no API-returned `UNKNOWN`. Write the deprovisioning predicate as a two-value check; model a missing/absent field as UNKNOWN in *your* schema. AWS's own doc examples don't populate the field — validate against a live call before a collector depends on it.
- **Source:** `02_design_decisions/Version_Drift_Ledger.md` §2; `02_design_decisions/Control_Evidence_API_Chain_Verified.md` Domains 1–2; `02_design_decisions/API_Constraints_By_Trust_Consequence.md` Lane 3.

### L-026 — Identity Store has no server-side status filtering
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane2_runner_assert
- **Fact:** Assuming a server-side `status` filter yields a silently truncated population (the API ignores/omits it). Pull the full population and filter client-side; the verifier asserts `count(retrieved) == count(authoritative source)`.
- **Source:** `02_design_decisions/API_Constraints_By_Trust_Consequence.md` Lane 2.

### L-027 — Identity Store throttles with explicit `ThrottlingException`/429
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane1_fail_loud
- **Fact:** Token-bucket throttling under high-concurrency scans surfaces as `ThrottlingException`/429 — explicit error, retry with exponential backoff. Also fail-loud: the `Extensions` map's `Document` type is unsupported by old CLI and Java/Go V1 SDKs.
- **Source:** `02_design_decisions/API_Constraints_By_Trust_Consequence.md` Lane 1.

### L-028 — Evidence buckets use S3 Object Lock Compliance Mode, not Governance Mode
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** Compliance Mode blocks deletion/overwrite by any user including the root account for the retention period; Governance Mode was considered and rejected because permissioned users can bypass or shorten retention, making it weaker and an attacker target.
- **Source:** `02_design_decisions/Decision_Ledger.md` (Object Lock decision); `02_design_decisions/Constraints.md`.

## Workday / NetSuite (future-scope systems — Decision Ledger rows; Sentinel is GitHub-first)

### L-029 — Workday RaaS: 30-min timeout, 50,000-row boundary, pseudo-pagination drops records silently
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane2_runner_assert (boundary/chunking); lane1_fail_loud (timeout)
- **Fact:** [FUTURE-SCOPE] RaaS enforces a 30-minute timeout (fail-loud: the request dies) and a 50,000-row execution boundary with no native pagination — chunk via date-entered prompt "pseudo-pagination." Records with null date fields or falling between chunk boundaries are silently dropped: reconcile the sum of chunk counts against an independent total, sweep null dates, verify/overlap chunk boundaries. WQL was the considered alternative for very large sets.
- **Source:** `02_design_decisions/API_Constraints_By_Trust_Consequence.md` Lanes 1–2; `02_design_decisions/Decision_Ledger.md` (pseudo-pagination); `02_design_decisions/Constraints.md`.

### L-030 — Workday RaaS setup constraints all fail loud
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane1_fail_loud
- **Fact:** [FUTURE-SCOPE] ISU usernames must not contain `\` (401/403 via URL-parsing failure in REST proxies); the report must be "Advanced" with "Enable As Web Service" checked; report owner + name are hardcoded in the URL (only connection-level fields like `{tenant_id}` templatable) — a wrong URL simply fails.
- **Source:** `02_design_decisions/API_Constraints_By_Trust_Consequence.md` Lane 1; `02_design_decisions/Constraints.md`; `02_design_decisions/Decision_Ledger.md`.

### L-031 — Workday integrations use a dedicated ISU in an ISSG
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** [FUTURE-SCOPE] Create a dedicated Integration System User assigned to an Integration System Security Group; robot accounts avoid breakage from personal-account password changes/departures, and sharing the report only with the ISSG is the least-privilege pattern.
- **Source:** `02_design_decisions/Decision_Ledger.md` (ISU/ISSG decision).

### L-032 — NetSuite SuiteQL mechanics: `Prefer: transient`, Oracle syntax, TBA, workbook permission
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane1_fail_loud
- **Fact:** [FUTURE-SCOPE] Every SuiteQL REST call needs the mandatory header `Prefer: transient` (rejected without it); row limits use Oracle-style `FETCH FIRST N ROWS ONLY`, not `LIMIT` (syntax error); auth is TBA with HMAC-SHA256 signatures; the executing role needs Reports → SuiteAnalytics Workbook permission (403 otherwise). All fail loud — verbatim applicable to the SOX-SOD-01 collector.
- **Source:** `02_design_decisions/API_Constraints_By_Trust_Consequence.md` Lane 1; `02_design_decisions/Decision_Ledger.md`; `03_testing_libraries/SOX_Agent_Testing_Library.md` (SOX-SOD-01).

### L-033 — NetSuite offset paging over a mutating table skips or double-counts rows
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane2_runner_assert
- **Fact:** [FUTURE-SCOPE] Manual `limit`/`offset` pagination over a table that mutates mid-pull silently skips or duplicates rows. Use a stable sort key (keyset pagination preferred); the verifier dedups on primary key and reconciles the total.
- **Source:** `02_design_decisions/API_Constraints_By_Trust_Consequence.md` Lane 2.

### L-034 — NetSuite booleans are strings `'T'`/`'F'` and can silently mis-filter
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane2_runner_assert
- **Fact:** [FUTURE-SCOPE] Wrong boolean coercion mis-filters the population without erroring. Treat as completeness-affecting: reconcile the returned count against an independent count for the filtered predicate.
- **Source:** `02_design_decisions/API_Constraints_By_Trust_Consequence.md` Lane 2.

### L-035 — `BUILTIN.DF()` labels vs internal IDs is a semantic trap needing D-4 sign-off
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane3_human_owned
- **Fact:** [FUTURE-SCOPE] `BUILTIN.DF()` returns display labels; bare fields return internal numeric IDs. A test mapped to the ID when the criterion is written against the label (or vice versa) matches genuinely-but-irrelevantly. The field mapping requires D-4 semantic sign-off before freeze.
- **Source:** `02_design_decisions/API_Constraints_By_Trust_Consequence.md` Lane 3.

## SOX / retention / regulatory / OSCAL

### L-036 — SOX: 366 days is a testing window; 7 years is the retention law (SEC Rule 2-06, not the bare statute)
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** 366 days is the operating-effectiveness testing window (practitioner convention, one full audit cycle). The 7-year workpaper-retention mandate comes from SEC Rule 2-06 (17 CFR 210.2-06, adopted under SOX §802); the bare criminal statute 18 U.S.C. §1520(a)(1) says 5 years, extended to 7 by the SEC rule; destruction carries up to 10 years imprisonment (§1520(b)). An evidence bucket expiring at 366 days passes a testing-window sample but violates the 7-year rule — SOX-relevant WORM retention must carry the 7-year class.
- **Source:** `02_design_decisions/Version_Drift_Ledger.md` §6; `02_design_decisions/Aegis_Design_Fixes.md` §0; `02_design_decisions/Aegis_RedTeam_Reconciliation.md` §1; `03_testing_libraries/SOX_Agent_Testing_Library.md`.

### L-037 — PCAOB Rel. 2025-004: the "remote possibility" carve-out is the architecture's strongest regulatory hook
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** The Board Policy Statement of Sept 18, 2025 (Rel. 2025-004) says that where the auditor concludes there is no more than a remote possibility the information was modified in a way rendering it unreliable, absence of separate AS 1105.10A(b) testing is not noncompliance. SHA-256-at-intake + WORM + hash-chain provenance is engineered to establish exactly that standard — the storage-layer contract *is* the carve-out condition; lead the reviewer-facing story with it. (.10A itself effective for fiscal years beginning on/after Dec 15, 2025.)
- **Source:** `02_design_decisions/Version_Drift_Ledger.md` §7; `02_design_decisions/Aegis_RedTeam_Reconciliation.md` §1; `02_design_decisions/Contradictions.md`.

### L-038 — OSCAL is mandated but had near-zero production adoption; ship the minimal valid AR first
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** Per FedRAMP's own RFC-0024 text, 100+ Rev5 authorizations were processed in 2025 with no submission using OSCAL, and no formal 20x Phase 1 pilot participant used it (do not overstate this as "chose alternatives"). OSCAL remains the mandated direction (machine-readable requirement projected ~Sept 30, 2026). The D-3 scope fence — minimal valid Assessment Results (results, observations, findings, subjects) first — is vindicated by the adoption reality; expect agency ingest tooling to lag.
- **Source:** `02_design_decisions/Version_Drift_Ledger.md` §4; `01_architecture/Aegis_Investigator_Design_Decisions.md` D-3; `01_architecture/Workflow_Theory_Supporting_Information.md` §4.

### L-039 — OSCAL export: UNKNOWN maps to `not-satisfied` + `unknown-cause`, and advisory records never enter a document
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** OSCAL has no native unknown state. Map UNKNOWN to `not-satisfied` with an `unknown-cause` property carrying the triage classification; never map it to `satisfied` (that converts absence of evidence into a claim of compliance). The exporter reads only `result` and `ratification` records; a test must assert no advisory content can appear in an export and fail loudly if the invariant breaks. Per observation, record whether evidence was event-backed or reconciliation-backed.
- **Source:** `04_build_prds/Sentinel_v0.2_Event_Driven_Agentic_OSCAL.md` (OSCAL export).

### L-040 — The FedRAMP "machine-readable update within one month of a significant change" claim did not verify
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** Do not encode "one month" as a tolerance. The Rev5 mechanism is the pre-implementation Significant Change Request; the newer Significant Change Notification is a 20x construct, optional for Rev5 only from 2026-02-27; machine-readable packages are projected (~Sept 2026, 2027 backstop), not tied to a per-change one-month clock. If a FedRAMP change tolerance is needed, pull it from the current SCN/SCR standard and cite the release ID — the SCN doc alone revised five times in six months.
- **Source:** `02_design_decisions/Control_Evidence_API_Chain_Verified.md` ("The claim that did not survive").

### L-041 — Non-SOX retention floors: HIPAA 6 years, EU AI Act 6 months, PCI DSS 12 months
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** HIPAA: minimum 6 years from creation or last effective date. EU AI Act (Art. 12): minimum 6 months for high-risk AI system logs. PCI DSS v4.0: 12 months total, 3 months immediately available. These are the only retention rows grounded in the corpus; AML/BSA, NARA, and SEC 17a-4(f) figures are quarantined as external and must not be cited as corpus.
- **Source:** `02_design_decisions/Constraints.md` (Data Retention Standards); `02_design_decisions/Aegis_RedTeam_Reconciliation.md` §1–§2.

### L-042 — FedRAMP ODP values in the library are provisional, stated from memory
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane3_human_owned
- **Fact:** The seeded Moderate ODP registry values (inactive-account disable 90 days; POA&M SLAs High 30 / Moderate 90 / Low 180; audit retention ≥90 days available / ≥1 year total; IR-6 1-hour US-CERT/CISA reporting; monthly scan and ConMon cadence; FIPS 140-2/3) are typical values the library itself flags as unverified. Every ODP is a §5 human-ratified constant: extract the real set from the SSP into a versioned registry and verify against the live baseline before any predicate freezes — predicates read from the registry, never inline values.
- **Source:** `03_testing_libraries/FedRAMP_Agent_Testing_Library.md` §2, verification caveat, open items.

## GRC Engineering Club toolkit (external prior art — quarantined source)

### L-043 — SCF data is CC BY-ND: fetch, attribute, never modify — and consume it frozen, not live
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** The SCF crosswalk (via `GRCEngClub/scf-api`: 1,468 controls × 249 crosswalks, 5,776 assessment objectives, 303 evidence-request entries) is licensed CC BY-ND — attribute and never modify. Consume as a WORM-intaken artifact: one-time fetch, SHA-256 at intake, pinned upstream quarterly release recorded in the Version Drift Ledger; never a live runtime dependency in the verdict path.
- **Source:** `05_prior_art/Aegis_Prior_Art_GRCEngClub_Toolkit.md` §2, §3.3, §5.

### L-044 — Pin adopted EngClub artifacts by commit hash, never by branch
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** The repo is pre-1.0 and moving (v2 RFC accepted 2026-04-30, directory restructure pending). Any adopted artifact (Finding schema, CI harness, update hook) is pinned by commit hash at intake, not branch.
- **Source:** `05_prior_art/Aegis_Prior_Art_GRCEngClub_Toolkit.md` (source caveat).

### L-045 — Their `inconclusive` covers only basis_missing; adopting their status enum as-is rebuilds the D-7 funnel
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** The Finding schema's `inconclusive` ("tool tried and couldn't determine: dropped API call, missing permission, rate-limited") maps precisely and only to D-7's basis-missing family — not identity-fuzzy or no-basis-anywhere. Keep the Aegis PASS/FAIL/UNKNOWN triad with a required `unknown_cause ∈ {basis_missing, identity_fuzzy, no_basis_anywhere}` companion; adopt `not_applicable` with a required `ratification_ref`; reject `skipped` (a population-testing system has no legitimate skip that isn't `not_applicable` or a completeness failure). Steal the conventions: const-pinned semver, `additionalProperties: false`, `allOf`/`if`/`then` conditional requirements, the `source`+`source_version`+`run_id`+`collected_at` reproducibility tuple, severity independent of status.
- **Source:** `05_prior_art/Aegis_Prior_Art_GRCEngClub_Toolkit.md` §3.1.

### L-046 — Their `evidence_refs` point into a mutable cache; adopt the fields, not the reproducibility claim
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** EngClub `evidence_refs` resolve into `~/.cache/claude-grc/` — user-writable, no hash at intake, no WORM, no chain, no frozen spec, no ratification. None of it survives hostile re-performance. The Aegis verdict-record deltas (record_hash, chain_prev, population_id/count/completeness_ref, spec_id+spec_hash, test_function_version, ratification_ref) are what convert the schema into audit-grade.
- **Source:** `05_prior_art/Aegis_Prior_Art_GRCEngClub_Toolkit.md` §3.1, §4.

### L-047 — The fedramp-20x update hook is a working template for this genome's recalibrate loop
- **Date:** 2026-07-25 · **Status:** CANDIDATE
- **Fact:** `plugins/frameworks/fedramp-20x/hooks/hooks.json` + `scripts/check-fedramp-updates.js` implement an auto-sync drift check against the official FedRAMP docs repo — a concrete implementation of the Janus recalibrate heartbeat. Port the pattern; point it at this genome's external-API entries and the pinned SCF release.
- **Source:** `05_prior_art/Aegis_Prior_Art_GRCEngClub_Toolkit.md` §3.5; `04_build_prds/Sentinel_JIT_UI_DB_Janus.md` §4 (outer loop).

## Other environmental facts

### L-048 — Splink identity resolution is deterministic only if four things are pinned
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane3_human_owned (weights/thresholds/comparison design); lane1_fail_loud (blocking rules)
- **Fact:** [FUTURE-SCOPE — D-7 identity-fuzzy branch] Re-performance of the frozen linkage model requires: (1) seeding the parameter-estimation/random-sampling step, (2) freezing `model.json` and predicting from it (never retraining), (3) freezing the term-frequency tables (or recomputing from the identical frozen population snapshot — the subtle gotcha), (4) pinning the exact Splink version. Blocking/cascade rules are Lane 1 (agent may draft); m/u weights, thresholds, comparison design, and TF tables are Lane 3 (D-4 sign-off).
- **Source:** `02_design_decisions/Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md` §4b, §8.

### L-049 — Apache Doris lineage fires only on writes; event-absence is not completeness
- **Date:** 2026-07-25 · **Status:** CANDIDATE · **Lane:** lane2_runner_assert
- **Fact:** [FUTURE-SCOPE] Doris column-level lineage fires only on `INSERT` / `INSERT OVERWRITE` / `CTAS` — `SELECT`-derived transforms produce no lineage event, and `__internal_schema` targets and VALUES-only inserts are filtered by design. Never infer read-path lineage from Doris events or read absence-of-events as "no data movement"; declare the gap in the Skill. Related: DataZone `PostLineageEvent` remains under the `datazone` namespace but lives in SageMaker Unified Studio, with a 300 KB per-event cap and column lineage requiring `spark.openlineage.columnLineage.datasetLineageEnabled=true`.
- **Source:** `02_design_decisions/API_Constraints_By_Trust_Consequence.md` Lane 2; `02_design_decisions/Constraints.md`; `02_design_decisions/Control_Evidence_API_Chain_Verified.md` Domain 6.
