# Control → Evidence → API Chain — Verified & Challenged

Status: research pass over the six-domain chain (the "spine"), pressure-tested against live sources (July 2026) and against the ratified invariant in `Aegis_Investigator_Design_Decisions.md`.
Purpose: Skill-file raw material. Every claim below is tagged as **VERIFIED**, **CORRECTED**, **UNVERIFIED**, or **CARRIED** (taken from your project docs, not independently re-checked this pass). Judgment calls are left to you — this is the retrieval-and-challenge sweep, not ratification.

---

## Headline findings (read these first)

1. **One section of doc 8 violates your own invariant.** The termination/deprovisioning domain proposes "computer-use AI agents capture application-level evidence." Design Decision **D-5 rejects exactly this** from the evidence/verdict path and redirects computer-use to the human-attest/investigation lane. Doc 8 as written would reinstate a non-deterministic agent in the verdict path for the controls hardest to make reliable. Correct it before it becomes a Skill.

2. **The AWS `UserStatus` win is real but brand-new (Nov 6, 2025)** — and it *removes* one of doc 8's justifications for computer-use. You can now pull account-disabled state deterministically from the Identity Store API instead of screen-scraping the console. Any collector on a pre-Nov-2025 SDK won't see the field.

3. **The GitHub "no read-only scope, forced to grant write" framing is stale.** True for *classic* OAuth tokens only. Fine-grained PATs and GitHub App installation tokens give `Contents: Read-only` on private repos — the least-privilege path your auditor wants. Both doc 8 and `Contradictions.md` are written against the old model.

4. **The FedRAMP "machine-readable package updates within one month of a significant change" tolerance did not verify.** The actual mechanism is different and the timing figure appears conflated. Do not encode "one month" as a tolerance without a primary-source citation.

5. **"Amazon DataZone PostLineageEvent" still works but the product is being absorbed into SageMaker Unified Studio / SageMaker Catalog.** API namespace is unchanged (`datazone`); the console and branding are not.

---

## Domain 1 — Logical Access Provisioning

**Authoritative population source.** HRIS as the onboarding engine (Workday, SAP SuccessFactors, Gusto, ADP). This is correct and aligns with architecture §4 (source-of-truth declared in the Skill, enforced at intake). Note the §4 two-tier override: at *control* level the population can differ from the domain default — CC6 provisioning keys off Workday new-hires, but a privileged-access review keys off the *target system's* current privileged accounts, not HR.

**Proving attributes → endpoint/field.**

| Attribute | System | Endpoint / field | Status |
| --- | --- | --- | --- |
| Birthright access (Dept, Location, Job Title) | Workday | Advanced Report via RaaS (JSON/XML) | CARRIED |
| Account identity + status + create date | AWS IAM Identity Center | `identitystore:ListUsers` / `DescribeUser` → `UserName`, `UserStatus`, `DisplayName`, `CreatedAt` | **VERIFIED (with date caveat, below)** |
| Assigned roles / permissions | NetSuite | SuiteQL over `rolepermissions`, `employee` via REST | CARRIED |
| Approval linkage (individual → grant) | Jira / GitHub | approval ticket / PR metadata | CARRIED |

**Tolerances & timing.** Access ready Day 1; CI/CD example "two approvals from CODEOWNERS + passing required checks." Flag: the two-approvals figure is a *configuration example*, not a standard — it belongs in the human-judgment set, not baked into a test predicate.

**VERIFIED — AWS Identity Store fields.** `UserStatus` and the `CreatedAt`/`CreatedBy`/`UpdatedAt` metadata fields were added to the Identity Store User/Group/Membership APIs on **2025-11-06** (AWS SSO Identity Store API changelog). As of a May 2025 feature request they did not exist, so this is a genuine, recent capability shift. Consequence for the Skill: the collector must run an SDK/CLI build from Nov 2025 or later; any Skill authored against the older "status isn't in the API, crawl the console" assumption is now obsolete. (I confirmed the field's addition and date; the `ENABLED / DISABLED / UNKNOWN` value set is per your `Contradictions.md` and matches the console states — I did not separately enumerate the API enum this pass.)

**Human-judgment gaps (what no source specifies — do not infer).** The authorized-approver whitelist for non-standard access; which job titles map to "high-privilege" roles; the specific calendar for "Day 1" (localized holidays). These are the §5 human-ratified set. The agent may *draft* the candidate approver population; a human *ratifies* it.

---

## Domain 2 — Termination & Deprovisioning

**Authoritative population source.** HRIS termination records ("Leaver" event) as trigger. Correct. For agents/NHIs that fall outside HR, inactivity monitoring is the substitute trigger (consistent with your Constraints.md and the Hacker News source).

**Proving attributes → endpoint/field.**

| Attribute | System | Endpoint / field | Status |
| --- | --- | --- | --- |
| Termination date | Workday | RaaS filtered by `Termination_Date` | CARRIED |
| Account disabled | AWS IAM Identity Center | `identitystore` → `UserStatus = DISABLED` | **VERIFIED (native since Nov 2025)** |
| Inactivity | Cloud IAM / logs | last-request timestamp vs. window | CARRIED |

**CORRECTED — the computer-use claim.** Doc 8 says: *"'Computer-use' AI agents capture application-level evidence (e.g., a 'Delete' button being restricted or a user marked 'Inactive' in a UI that lacks an API)."* This is the trap **D-5 explicitly rejects**. Hashing a screen recording makes the *artifact* tamper-evident; it does **not** make the *act of collection* deterministic or complete, and "I clicked through and it looked disabled" is an LLM assertion about state — the exact category the invariant bars from the verdict path. Two corrections:

- **Re-tag computer-use as investigation / human-attest lane**, never autonomous PASS, never into the deterministic population. It may drive a UI to help a *human* capture evidence they then attest to.
- **The AWS example is now moot anyway.** Since `UserStatus = DISABLED` is API-native as of Nov 2025, AWS account-disabled state is deterministic evidence — no UI navigation needed. Computer-use only survives for genuinely API-less UIs, and even there it stays in the human-attest lane.

**Human-judgment gaps.** Grace period for disabled users to retain read-only access (paystubs/tax docs); the exact inactivity threshold (30 vs 90 days) to force-revoke a service account. Human-ratified.

---

## Domain 3 — Key Management

**Authoritative population source.** Cloud KMS + Secrets Managers (AWS KMS, Azure Key Vault, HashiCorp Vault). Correct.

**Proving attributes → endpoint/field.** Key ID, rotation status, FIPS 140-2/3 validation, access policies. S3 `ObjectLockConfiguration` (`Mode = COMPLIANCE`, retention) for the WORM side; `DescribeUser` / `ListGroups` to audit who holds "Key Administrator." All CARRIED — stable AWS surfaces, not re-verified this pass, but nothing suggests drift.

**Tolerances & timing.** FIPS 140-validated keys; rotation schedule defined in the SSP. CARRIED.

**Human-judgment gaps.** Per-class rotation frequency (root CA vs. application API key); the break-glass personnel list for master-key access. Human-ratified — and note these are precisely the "break-glass provisioning approved out-of-band" cases the honest-ceiling section (§9) says the mechanical test cannot adjudicate: each is an UNKNOWN or FAIL for a human, not something the agent rules satisfied-in-spirit.

---

## Domain 4 — Backup & Recovery

**Authoritative population source.** Backup job logs; S3 Inventory / Athena reports for large stores. Correct.

**Proving attributes → endpoint/field.** Backup timestamp, success/failure, retention period, WORM status. `S3 Batch Operations` status logs; `ObjectLockConfiguration` with `DefaultRetention`. CARRIED. (Object Lock's own constraints — enable-at-bucket-creation-only, versioning prerequisite, Batch Operations to retrofit existing objects — are already correctly captured in your Constraints.md and Decision Ledger.)

**Tolerances & timing.** Semi-annual restoration testing (recommended standard); FedRAMP backup retention windows (e.g., 3 years for certain IT records). The "semi-annual" and "3 years" figures are CARRIED — treat as defaults to confirm against the current baseline, not as verified constants.

**Human-judgment gaps.** Company-specific RTO/RPO numeric targets; the definition of "Critical Data" that scopes backups. Human-ratified.

---

## Domain 5 — Change Management

**Authoritative population source.** Version control (GitHub, GitLab) + CD pipelines. Correct.

**Proving attributes → endpoint/field.**

| Attribute | System | Endpoint / field | Status |
| --- | --- | --- | --- |
| PR ID, approver identity, status checks, merge protection | GitHub | REST PR + branch-protection endpoints | **CORRECTED (token model, below)** |
| GL change tracking | NetSuite | System Notes / Audit Trail | CARRIED |
| PR → control UUID correlation | Lula2 | `npx lula2 crawl` → per-file UUID + sha256, PR comment | **VERIFIED (with maturity caveat)** |

**CORRECTED — GitHub read-only access.** Doc 8 lists `repo` / `repo:status` classic scopes, and `Contradictions.md` records the "no read-only scope for private repos, forced to grant write" complaint as current. That complaint is real only for **classic** tokens. **Fine-grained PATs and GitHub App installation tokens** grant `Repository contents: Read-only` (+ `Metadata: Read-only`, and `Pull requests` / `Commit statuses: Read-only` as needed) on private repos — practitioners confirm a Contents+Metadata read token clones private code with no write grant. For an audit collector this is the correct least-privilege posture and it dissolves the "forced to over-permission" objection. Caveats to record: (a) fine-grained PATs still carried beta-era gaps at last check (outside-collaborator repos, a few endpoints); a GitHub App is the more robust production path. (b) "Read-only" does not prevent issue creation on *public* repos — a real agentic-token gotcha, but irrelevant to private-repo evidence pulls.

**VERIFIED — Lula, with a naming trap.** Two distinct tools share the name. The PR-crawl capability doc 8 describes is **Lula2** (`npx lula2 crawl`), a newer TypeScript tool that maps changed lines to control UUIDs and posts a compliance comment carrying per-file **UUID + sha256** — which fits your hash-chain discipline cleanly. It is **not** the original Go-based Lula (an OSCAL validation engine: API/Kubernetes/Files domains, OPA/Kyverno providers). Lula2 is explicitly early-stage ("expect breaking changes," v0.x). Adopt as an *assist* for change-impact triage, not as a hardened verdict-path evidence source, and pin the version.

**Tolerances & timing.** "Merges require passing checks + authorized approval" — correct in spirit; the *required-checks list* and the *authorized-approver set* are human-judgment gaps, not constants. The "FedRAMP Rev5 requires machine-readable package updates within one month of a significant change" claim is handled below (it did not verify).

**Human-judgment gaps.** The threshold for a "Significant Change" (e.g., 10% of codebase, any new API endpoint); the definitive required-status-checks list (coverage vs. security linting). Human-ratified.

---

## Domain 6 — Monitoring & Continuous Assurance

**Authoritative population source.** Cloud audit trails (CloudTrail, Azure Activity Log) + CSPM findings. Correct.

**Proving attributes → endpoint/field.** Alert-rule inventory, alert-event timestamps, remediation linkage. AWS Config Rules (managed + custom) for config-vs-baseline; `datazone:PostLineageEvent` for data-movement lineage. Compliance crons weekly/monthly to catch drift.

**CORRECTED / CLARIFIED — DataZone lineage.** `PostLineageEvent` is real and current, still under the **`datazone`** API namespace (`aws datazone list-lineage-events` / `get-lineage-event`). But the capability went GA in Dec 2024 and now lives inside **SageMaker Unified Studio / SageMaker Catalog** ("powered by DataZone"); AWS is actively pushing DataZone domains to "upgrade to SageMaker." A source that cites DataZone lineage as a June-2024 *preview* is stale. Concrete constraints for the Skill: **300 KB per-lineage-event size cap**; column-level lineage requires `spark.openlineage.columnLineage.datasetLineageEnabled=true`; the OpenLineage transport is `amazon_datazone_api` (`AmazonDataZoneTransport`). Write permission = IAM `ALLOW` on `PostLineageEvent` (enforced at the API Gateway layer); read = `ListLineageEvents` + `GetLineageEvent`. This maps directly to doc 8's own requirement that lineage be captured at column level, not table level.

**Human-judgment gaps.** MTTD / MTTR target metrics; the risk-tolerance line separating a "Warning" from a "Gate/Block." Human-ratified — and this is the same gate/warning split your Constraints.md and the DevSecOps decision already treat as policy, not inference.

---

## The claim that did not survive: FedRAMP "within one month"

Doc 8: *"FedRAMP Rev5 requires machine-readable package updates within one month of a 'significant change.'"* **UNVERIFIED — do not encode as a tolerance.** What the current FedRAMP.gov materials actually show (July 2026):

- The traditional Rev5 mechanism is the **Significant Change Request (SCR)** — a *pre-implementation* approval process, not an after-the-fact "within one month" filing.
- The newer **Significant Change Notification (SCN)** process is a 20x construct (first release 25.06A, 2025-06-17), initially for 20x Phase One pilot participants. For Rev5 it became an **optional** alternative to the SCR process only from **2026-02-27** (wide release), adopted by opt-in email to FedRAMP.
- **Machine-readable authorization packages** are *projected* to be required for all Rev5 providers around **September 2026** (with a 2027 backstop and possible revocation for non-compliance) — reported as "may be required," not a settled mandate, and not tied to a per-change "one month" clock.
- Context: 20x submissions open **July 2026** (Class A–C); Rev5 retires **end of 2027**.

Net: the "one month" figure looks conflated (possibly with a continuous-monitoring cadence or POA&M timeline). If a change-management tolerance needs a FedRAMP number, pull it from the current SCN/SCR standard directly and cite the release ID — the ground is moving release-to-release (the SCN doc alone revised five times between June and Nov 2025).

---

## Verification ledger (honesty)

**Independently verified this pass (with dates/sources):** AWS Identity Store `UserStatus`/`CreatedAt` addition (2025-11-06, AWS SSO Identity Store changelog); Lula2 `crawl` capability and its distinction from Go-Lula (defenseunicorns/lula repo); DataZone `PostLineageEvent` status, SageMaker consolidation, 300KB cap, column-lineage flag (AWS SageMaker Unified Studio docs, June 2025 AWS big-data blog); GitHub fine-grained PAT / App `Contents: Read-only` on private repos (github.blog Oct 2022, GitHub Docs, community discussions); FedRAMP SCN/SCR structure and dates (fedramp.gov SCN standard 25.06A–25.11B, secureframe/ignyte/gotomyerp 2026).

**Carried from your project docs, not independently re-verified this pass:** NetSuite SuiteQL `Prefer: transient` header + `rolepermissions`/`employee` tables; Workday RaaS `Termination_Date` filtering, 30-min timeout / 50,000-row boundary, ISU no-backslash rule; S3 Object Lock mechanics; FIPS-140 key requirements; semi-annual restore testing and the "3 years" FedRAMP backup figure. These are internally consistent across your sources; treat as reliable defaults, but re-verify the FedRAMP/backup numbers against the current baseline before they enter a tolerance.

**Structural check against the architecture.** Doc 8's per-domain "authoritative population source" and its "what no source specifies" lists map cleanly onto architecture §4 (declared source) and §5 (human-ratified judgment set) — with the single exception of the Domain-2 computer-use claim, which crosses the line D-5 draws. Fix that one and the chain is faithful to the invariant: agent proposes collection mechanics, human ratifies semantic mapping and authoritative population, deterministic code executes and decides.

---

## Sources

- AWS SSO Identity Store API changelog (UserStatus/CreatedAt added 2025-11-06); AWS Identity Store `ListUsers`/`DescribeUser` reference; boto3 `describe_user`.
- defenseunicorns/lula (Lula2 `crawl`, README + index.ts); docs.lula.dev (Go-Lula validations, OPA/Kyverno).
- AWS: "Announcing GA of data lineage in next-gen SageMaker and Amazon DataZone"; SageMaker Unified Studio data-lineage docs (authorization, automate-capture, troubleshooting — 300KB cap, column-lineage flag); "Capture data lineage from dbt/Airflow/Spark with SageMaker" (2025-06-30).
- GitHub: "Introducing fine-grained personal access tokens" (github.blog); "Permissions required for fine-grained PATs" + "Managing your PATs" (GitHub Docs); community discussions #160497/#160535 (Contents:Read-only clones private repos), #180063 (read-only ≠ no-issue-creation on public repos).
- FedRAMP.gov: Significant Change Notification Requirements (releases 25.06A–25.11B); 20x SCN standard; Rev5 SCN wide-release 2026-02-27; docs changelog v0.9.0-beta (2026-02-04). Secondary: secureframe, ignyteplatform, gotomyerp (2026) on 20x timeline and machine-readable package projections.
