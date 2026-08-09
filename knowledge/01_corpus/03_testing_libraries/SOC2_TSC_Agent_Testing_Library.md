# SOC 2 TSC Agent Testing Library — Full Control Universe Mapped to Trust Services Criteria

**Status:** Working artifact (July 16, 2026)
**Scope:** Extends `SOC2_Control_Testing_Matrix.md` (the 22 transcribed controls) to the complete SOC 2 control universe, mapped to the 2017 TSC (2022 points of focus). Every control follows the same schema: description → test procedure → population request → sample request → C&A → testing attributes — plus an **Agent Methodology** block tying each control to the Aegis architecture (authoritative source declaration §4, plan→freeze→execute §3, three-lane constraint model, human-ratified judgment set §5).

**Framing note:** SOC 2 has canonical *criteria* (33 common criteria CC1.1–CC9.2, plus A1, C1, PI1, P-series), not canonical *controls*. Control statements below use industry-standard language consistent with the existing 22; IDs marked *(inferred)* fill gaps in your numbering scheme (e.g., CFG-01 is referenced by CM-05 but wasn't in the screenshots; DP-01/DP-03, BR-01/BR-02, IM-01/02/03/06 are presumed to exist). Reconcile inferred IDs against the live control matrix before freezing skill files.

---

## 1. Agent Testability Tiers

Every control gets one rating, derived from the Aegis trust boundary — the question is *where the evidence lives and whether the pass/fail predicate is a pure function*:

- **Tier 1 — Fully agent-testable.** Population pulled deterministically from an authoritative API; every attribute computable as a pure function over hashed records (PASS/FAIL/UNKNOWN). The agent plans the collection spec once per control-per-system; the deterministic runner owns C&A. These are the priority for skill files.
- **Tier 2 — Hybrid.** Population is deterministic (Tier 1 mechanics), but one or more attributes require inspection of an unstructured artifact (report PDF, meeting materials, third-party attestation) or a human-ratified judgment. The agent retrieves and stages; the attribute verdict routes through the D-4 semantic review gate. Automate the population, C&A, and structured attributes; human closes the loop.
- **Tier 3 — Governance/manual.** Evidence is inherently narrative (board minutes, org design, fraud-risk deliberation). The agent's only role is deterministic anchoring: document hash, version, review date, approver identity. No attribute testing above that.

**The dividing rule (from `API_Constraints_By_Trust_Consequence.md`):** if a wrong value produces a visible error, the agent may own it; if a wrong value produces a plausible-looking answer, the runner or a human must own it. Tier assignments below apply that rule per attribute, not just per control.

---

## 2. Standard C&A Template (applies to every sample-based control)

AM-01 was the only control in the source workbook with explicit C&A attributes. The pattern generalizes; the deterministic runner asserts this for **every** population pull, so skill files should reference this template rather than restating it:

**Completeness:**
- C1. Extract row count matches an independent count from the source system (count endpoint, UI total, or report footer).
- C2. Pagination exhaustion asserted by the runner (cursor drained, not first-page-only) — Lane 2 fail-silent trap; never left to agent memory.
- C3. Period boundary check: earliest and latest record timestamps fall inside the examination window; records straddling the boundary flagged UNKNOWN, not silently excluded.
- C4. Two-source reconciliation where an independent population exists (e.g., HRIS terminations vs. IdP deactivations; MDM inventory vs. EDR inventory). Deltas emitted as exceptions, not resolved by the agent.

**Accuracy:**
- A1. Sample 1 record extract→source: all data elements match the source-of-truth screen/API.
- A2. Sample 1 record source→extract: record independently located in source appears in extract with matching elements.
- A3. SHA-256 hash at intake, WORM write under separate writer identity (per architecture §2).

---

## 3. TSC Coverage Map

| TSC | Criterion theme | Controls | Tier |
| --- | --- | --- | --- |
| CC1.1 | Integrity & ethical values | HR-03, GV-05 | 1 / 3 |
| CC1.2 | Board oversight | GV-02 | 3 |
| CC1.3 | Org structure & reporting lines | GV-03 | 3 |
| CC1.4 | Competence: hiring, background, training | HR-01, HR-02, HR-04 | 2 / 1 / 3 |
| CC1.5 | Accountability & sanctions | HR-05 | 3 |
| CC2.1 | Internal information quality | LM-01, GV-01 | 1 / 2 |
| CC2.2 | Internal communication | HR-02, HR-03, GV-04 | 1 / 1 / 3 |
| CC2.3 | External communication | **ELC-03**, CM-08, IM-06 | 2 / 1 / 2 |
| CC3.1–3.4 | Risk assessment | RM-01, RM-02, RM-03 | 2 / 2 / 3 |
| CC4.1 | Monitoring evaluations | MA-01, TVM-03 | 2 / 2 |
| CC4.2 | Deficiency remediation | MA-02 | 1 |
| CC5.1–5.3 | Control activities & policies | GV-01, CFG-01 | 2 / 2 |
| CC6.1 | Logical access security | **AM-01**, **AM-05**, AM-03, AM-04, AM-07, AM-08, **DP-04**, DP-03, ASM-01 | mostly 1 |
| CC6.2 | Provisioning & deprovisioning authorization | **AM-05**, **AM-06**, AM-02 | 1 |
| CC6.3 | Access modification/removal, SoD, reviews | AM-02, AM-04, **AM-06** | 1 |
| CC6.4 | Physical access | PS-01 | 2 (usually inherited) |
| CC6.5 | Data/asset disposal | **ASM-05**, DP-06 | 1 / 2 |
| CC6.6 | External access protection | NS-01, AM-03, AM-09 | 1 |
| CC6.7 | Transmission/movement of data | DP-01, **DP-02** | 1 |
| CC6.8 | Unauthorized/malicious software | **ASM-03**, ASM-02, **CFG-02/03** | 1 |
| CC7.1 | Vulnerability & config monitoring | **TVM-01**, TVM-02, **CFG-03**, CFG-01 | 1 |
| CC7.2 | Anomaly monitoring | LM-01, LM-02, NS-02, **BR-03**, **CAP-01** | 1 |
| CC7.3 | Incident evaluation | IM-02, **IM-04**, **IM-07** | 1 |
| CC7.4 | Incident response | **IM-05**, IM-01, IM-06 | 1 / 2 / 2 |
| CC7.5 | Incident recovery | **IM-05**, IM-01, DR-01 | 1 / 2 / 2 |
| CC8.1 | Change management | **CM-02 – CM-08**, **CFG-02**, LM-04 | 1 / 2 |
| CC9.1 | Risk mitigation / resilience | RM-04, DR-01, BR-* | 3 / 2 / 1 |
| CC9.2 | Vendor & business partner risk | VRM-01, VRM-02, **CM-02**, **CM-06** | 2 |
| A1.1 | Capacity | **CAP-01**, **CAP-02** | 1 / 2 |
| A1.2 | Environmental protections, backup, recovery infra | BR-01, BR-02, **BR-03**, **BR-04** | 1 |
| A1.3 | Recovery testing | DR-01, **BR-04** | 2 / 1 |
| C1.1 | Confidential info identification & protection | DP-03, **DP-02**, **DP-04**, **DP-05**, GV-06 | 1 / 2 |
| C1.2 | Confidential info disposal | DP-06, **ASM-05** | 2 / 1 |
| PI1.1–1.5 | Processing integrity | PI-01, PI-02, PI-03 | scope-dependent, see §8 |
| P-series | Privacy | Out of scope unless privacy category contracted — see §9 |

**Bold** = already fully specced in `SOC2_Control_Testing_Matrix.md`; not restated below.

---

## 4. Access Management & Identity (CC6) — new controls

### AM-02 — User Access Reviews *(inferred ID)*
**TSC:** CC6.2, CC6.3 | **Approach:** Sample Based | **Tier 1** (review execution) / **Tier 2** (reviewer judgment appropriateness)

**Control Description:** User access to in-scope systems is reviewed on a quarterly basis by system owners. Access identified as inappropriate is revoked in a timely manner.

**Test Procedures:** For a sample of quarterly access reviews performed during the examination period, inspect review records to verify the review was performed by the designated system owner, covered the complete user population of the system, and was completed within the defined cadence. For access flagged for removal, inspect deprovisioning evidence to verify revocation occurred within the defined SLA.

**Population Request:**
1. Population of access reviews scheduled/performed during the review period, by system, including reviewer, start date, completion date.
2. Population of remediation items (flagged access) arising from each review, including flag date and revocation date.

**Sample Request:** For the (X) selected reviews, please provide the review record showing reviewer identity, user population reviewed, review completion date, sign-off, and for any flagged access, the ticket and system evidence showing revocation date.

**C&A:** Standard template. C4 two-source: review-tool population vs. live system user list *as of the review snapshot date* — snapshot-vs-live drift is a Lane 2 fail-silent trap; the runner must compare against the archived snapshot, not current state.

**Testing Attributes:**
- A. Review population complete (all in-scope systems covered per cadence)
- B. Review performed within defined cadence
- C. Reviewer is the designated owner (not the access holder — SoD)
- D. Reviewed user list reconciles to system user list at snapshot date
- E. Flagged access revoked within SLA
- F. Review sign-off/completion evidence retained

**Agent Methodology:** Authoritative source: access-review tool (or IdP entitlement export where reviews run in sheets). Attributes A–B, D–F are pure functions. Attribute C requires the human-ratified approver/owner designation list (§5 judgment set — "who is an authorized reviewer" is management designation, never model inference). SLA tolerance semantics (business days, calendar, clock start) are human-ratified.

---

### AM-03 — Multi-Factor Authentication
**TSC:** CC6.1, CC6.6 | **Approach:** Configuration + full population | **Tier 1**

**Control Description:** Multi-factor authentication is enforced for all user access to in-scope systems and for remote/administrative access.

**Test Procedures:** Inspect identity provider authentication policies to verify MFA is required for in-scope applications. For the full population of active users, inspect enrollment status to verify MFA factors are enrolled; inspect policy exclusion groups and verify any exclusions are documented and approved.

**Population Request:**
1. IdP sign-on/authentication policy configurations for in-scope applications, including rule priority order and assigned groups.
2. Full population of active users with MFA enrollment status and factor types.
3. Population of users in any MFA-exempt/exclusion groups.

**Sample Request:** N/A (config + full-population test; exceptions tested 100%).

**C&A:** Standard template. Lane 2 hazard: policy *rule ordering* — a permissive rule above the MFA rule silently defeats it; the runner asserts on the full ordered rule set, not the presence of an MFA rule.

**Testing Attributes:**
- A. MFA policy enabled for all in-scope apps
- B. Policy rule ordering does not bypass MFA
- C. Active user population fully enrolled (or in documented exception)
- D. Exclusion group membership approved and time-boxed
- E. Factor types meet policy (e.g., phishing-resistant for admins)
- F. Policy unchanged during period, or changes tie to approved change tickets

**Agent Methodology:** Okta/Entra APIs; all attributes pure functions. Attribute F joins to the change-management population (CM series) — deterministic join on policy ID + audit log. This is the archetypal Tier 1 control.

---

### AM-04 — Privileged Access Restriction *(inferred ID)*
**TSC:** CC6.1, CC6.3 | **Approach:** Full population | **Tier 1**

**Control Description:** Administrative and privileged access to in-scope systems is restricted to authorized personnel based on job responsibility.

**Test Procedures:** Obtain the full population of accounts holding privileged roles in in-scope systems as of period end (and grants during the period). Compare against the management-approved privileged-access authorization list to verify all privileged holders are authorized; verify privileged grants during the period followed the access-request process (join to AM-05 population).

**Population Request:**
1. Full listing of privileged roles/groups per in-scope system and their current members, with grant dates.
2. Management-approved list of personnel authorized for privileged access, by system and role.
3. Population of privileged access grants during the review period.

**Sample Request:** For the (X) privileged grants selected, provide the request ticket, approval, and provisioning evidence (per AM-05 schema).

**C&A:** Standard template. C4: privileged membership from target system vs. IdP group membership. Note the architecture §4 override: authoritative source for the *current privileged review* is the **target system**, not HR/IdP.

**Testing Attributes:**
- A. Privileged role/group population complete per system
- B. Every current holder appears on the authorized list
- C. Grants during period tie to approved requests
- D. No dormant privileged accounts (last-login within threshold, else flagged)
- E. Service/break-glass accounts identified and separately governed (→ AM-08)
- F. Removals executed when authorization lapsed

**Agent Methodology:** Attribute B depends entirely on the human-ratified authorization list — the definition of "authorized" is management designation (§5). Everything else is pure function. GitHub caveat (Lane 1/Lane 2 mix): no read-only OAuth scope for private repos — `repo` scope includes write; the collector identity must be constrained by IAM, and the hook allowlist compensates.

---

### AM-07 — Authentication Configuration *(inferred ID)*
**TSC:** CC6.1 | **Approach:** Configuration | **Tier 1**

**Control Description:** Password and session parameters for in-scope systems are configured in accordance with the company's authentication policy (length, complexity, lockout, session timeout), or authentication is delegated to SSO.

**Test Procedures:** Inspect authentication configurations for in-scope systems to verify parameters align to policy; for systems behind SSO, verify local authentication is disabled or restricted.

**Population Request:**
1. Authentication/password policy configurations per in-scope system.
2. Listing of in-scope systems with SSO enforcement status and any local-auth accounts.

**Sample Request:** N/A.

**Testing Attributes:**
- A. Config parameters ≥ policy minimums per system
- B. SSO enforced where required; local auth disabled or justified
- C. Local/legacy accounts enumerated and approved
- D. Config unchanged during period or changes tie to approved tickets

**Agent Methodology:** Pure Tier 1. Policy minimums are the human-ratified predicate constants; encode as versioned test fixtures with seeded failing cases.

---

### AM-08 — Service & Shared Account Management *(inferred ID)*
**TSC:** CC6.1 | **Approach:** Full population | **Tier 1** population / **Tier 2** ownership judgment

**Control Description:** Service accounts and non-human identities are inventoried, assigned an owner, restricted from interactive login where feasible, and their credentials are rotated or vaulted per policy.

**Test Procedures:** Obtain the full population of service accounts/NHIs across in-scope systems; verify each has a documented owner, interactive login restrictions where applicable, and credential rotation/vaulting evidence within policy.

**Population Request:**
1. Population of service accounts / NHIs per in-scope system (cloud IAM, IdP, K8s service accounts, API keys) with creation date and last-used date.
2. NHI ownership register.
3. Credential rotation/vault records for the period.

**Sample Request:** For the (X) selected NHIs, provide ownership record, vault entry or rotation evidence, and configuration showing interactive login disabled where applicable.

**C&A:** C4 two-source: cloud IAM listing vs. NHI discovery tooling. Per `Constraints.md`, NHI offboarding is triggered by **inactivity monitoring, not HR termination** — the JML assumption does not hold; the dormancy attribute is the compensating test.

**Testing Attributes:**
- A. NHI population complete across IAM/OAuth/K8s
- B. Owner assigned for each NHI
- C. Interactive login disabled where applicable
- D. Credential rotation/vaulting within policy interval
- E. Dormant NHIs (last-used beyond threshold) flagged and dispositioned
- F. Orphaned NHIs (owner departed) reassigned or disabled

**Agent Methodology:** Attribute F is a deterministic join: NHI owner register × AM-06 termination population. Workday ISU constraint applies to the collector itself (no `\` in ISU usernames — Lane 1, fails loud).

---

### AM-09 — Remote Access *(inferred ID)*
**TSC:** CC6.6 | **Approach:** Configuration | **Tier 1**

**Control Description:** Remote access to the production environment requires VPN/ZTNA with MFA; direct administrative access from the public internet is prohibited.

**Test Procedures:** Inspect VPN/ZTNA and network configurations to verify remote administrative paths require authenticated, MFA-backed access and that no in-scope administrative interface is exposed publicly.

**Population Request:**
1. VPN/ZTNA configuration and authentication policy.
2. Inventory of administrative interfaces (SSH, RDP, consoles) for in-scope systems with network exposure (security-group/firewall rules).

**Sample Request:** N/A.

**Testing Attributes:**
- A. Remote access requires MFA-backed auth
- B. No admin interface exposed to 0.0.0.0/0 (or documented, approved exceptions)
- C. Exposure inventory complete against cloud asset inventory
- D. Exceptions time-boxed with owner and expiry

**Agent Methodology:** Pure function over AWS security groups / firewall configs. Attribute C reconciles against ASM-01 inventory (Lane 2: partial-region enumeration is a fail-silent trap — the runner must iterate all enabled regions and assert region coverage).

---

## 5. Infrastructure, Network, Data, Availability — new controls

### ASM-01 — Asset Inventory *(inferred ID)*
**TSC:** CC6.1, A1.1 | **Approach:** Full population | **Tier 1**

**Control Description:** An inventory of in-scope infrastructure assets and company-managed workstations is maintained and kept current through automated discovery.

**Test Procedures:** Inspect the asset inventory and its automated population mechanism; reconcile inventory against independent sources (cloud provider listings, MDM, EDR) to verify completeness and currency.

**Population Request:**
1. Current asset inventory export with asset identifier, type, owner, and environment.
2. Independent listings: cloud provider resource inventory, MDM device list, EDR device list.

**Sample Request:** N/A (reconciliation-based).

**Testing Attributes:**
- A. Inventory mechanism automated
- B. Inventory reconciles to cloud provider listing (delta = exceptions)
- C. Workstation inventory reconciles MDM ↔ EDR ↔ IdP-active-users
- D. Assets carry owner and environment classification
- E. Deltas investigated/dispositioned

**Agent Methodology:** This control is the **completeness backbone** — ASM-03/04/05, DP-05, NS-01 all inherit their population from it. Build it first; every workstation-scoped skill declares it as the authoritative source. Three-way reconciliation (C) is exactly the two-source C4 pattern extended.

---

### ASM-02 — MDM Enrollment *(inferred ID)*
**TSC:** CC6.8 | **Approach:** Full population | **Tier 1**

**Control Description:** Company-managed workstations are enrolled in mobile device management, which enforces security configuration baselines.

**Test Procedures:** Inspect MDM enrollment for the full workstation population and inspect the enforced configuration profiles to verify baseline enforcement (screen lock, disk encryption trigger, OS version floor).

**Population Request:**
1. Population of workstations (per ASM-01) with MDM enrollment status.
2. MDM configuration profiles and assignment scope.

**Sample Request:** For the (X) selected devices, provide device-level MDM status showing enrolled, compliant, and profile application.

**Testing Attributes:**
- A. Workstation population fully enrolled (or documented exceptions, e.g., Linux devices with compensating control per DP-05)
- B. Baseline profiles assigned to all-device scope
- C. Compliance status healthy or non-compliance dispositioned
- D. Un-enrolled devices flagged against ASM-01 population

---

### NS-01 — Network Security Controls *(inferred ID)*
**TSC:** CC6.6 | **Approach:** Configuration + full population | **Tier 1**

**Control Description:** Network access to production is restricted through security groups/firewall rules following least privilege; changes to network rules follow change management.

**Test Procedures:** Inspect security group/firewall configurations for in-scope environments to verify ingress restricted to required ports/sources; verify rule changes during the period tie to approved changes.

**Population Request:**
1. Full security group / firewall rule listing for in-scope accounts/VPCs (all regions).
2. Population of network rule changes during the period (cloud audit log).

**Sample Request:** For the (X) selected rule changes, provide the associated change ticket and approval.

**Testing Attributes:**
- A. No unrestricted ingress on sensitive ports (documented exceptions only)
- B. Rule set covers all in-scope accounts and regions
- C. Rule changes tie to approved change records
- D. Exceptions time-boxed with owner

**Agent Methodology:** Attribute C is a deterministic join of CloudTrail events × Jira change tickets on time-window + actor. Lane 2 traps: region enumeration and account enumeration (org-wide listing, not default account).

---

### NS-02 — Network/Threat Monitoring *(inferred ID)*
**TSC:** CC7.2 | **Approach:** Configuration + sample | **Tier 1**

**Control Description:** Network and threat detection tooling (e.g., GuardDuty/IDS) is enabled across in-scope environments; alerts are triaged and investigated.

**Population Request:**
1. Detection tooling enablement status per in-scope account/region.
2. Population of high/critical detections during the period with triage status.

**Sample Request:** For the (X) selected detections, provide triage record, investigation notes, and disposition.

**Testing Attributes:**
- A. Detection enabled across all in-scope accounts/regions
- B. Alert routing configured to responsible team
- C. Detection population complete
- D. Sampled detections triaged within SLA
- E. Disposition documented

---

### DP-01 — Encryption in Transit *(inferred ID)*
**TSC:** CC6.7 | **Approach:** Configuration | **Tier 1**

**Control Description:** Data transmitted over public networks is encrypted using TLS 1.2+.

**Test Procedures:** Inspect load balancer/endpoint TLS policies for in-scope public endpoints to verify minimum protocol version and certificate validity.

**Population Request:**
1. Inventory of public endpoints (from ASM-01/cloud listing) with TLS policy and certificate details.

**Sample Request:** N/A.

**Testing Attributes:**
- A. Endpoint inventory complete
- B. TLS policy ≥ 1.2 on all endpoints
- C. Certificates valid (not expired) during period
- D. Exceptions documented and approved

---

### DP-03 — Encryption at Rest *(inferred ID)*
**TSC:** CC6.1, C1.1 | **Approach:** Configuration + full population | **Tier 1**

**Control Description:** Production data stores (databases, object storage, volumes) are encrypted at rest using managed keys.

**Population Request:**
1. Full listing of in-scope data stores with encryption status and key ARN (all regions/accounts).
2. KMS key policies and rotation status for keys in use.

**Sample Request:** N/A (full population).

**Testing Attributes:**
- A. Data store population complete (reconciles to ASM-01)
- B. Encryption enabled on 100% of in-scope stores
- C. Key policies restrict administration to authorized principals
- D. Key rotation enabled where policy requires
- E. Exceptions dispositioned

---

### DP-06 — Data Retention & Disposal *(inferred ID)*
**TSC:** C1.2 | **Approach:** Configuration + sample | **Tier 2**

**Control Description:** Confidential data is retained per the retention schedule and disposed of securely when retention lapses.

**Test Procedures:** Inspect retention configurations (lifecycle policies, log retention) against the retention schedule; for a sample of disposal events, inspect disposal evidence.

**Population Request:**
1. Retention configurations for in-scope stores/logs.
2. Retention schedule (policy document — human-ratified constants).
3. Population of disposal events/requests during the period.

**Sample Request:** For the (X) selected disposal events, provide the request, approval, and completion evidence.

**Testing Attributes:**
- A. Configured retention ≥ policy minimum per data class (SOX operational logs ≥ 366 days; work papers 7 years; framework floors per `Constraints.md`)
- B. WORM/legal-hold controls where required
- C. Disposal events approved and evidenced
- D. Configuration changes tie to approved changes

**Agent Methodology:** Attribute A predicate constants come straight from the retention table in `Constraints.md` — encode as versioned fixture. Tier 2 only because the retention *schedule mapping* (which store holds which data class) is human-ratified.

---

### BR-01 — Backup Configuration *(inferred ID)*
**TSC:** A1.2 | **Approach:** Configuration | **Tier 1**

**Control Description:** Backups of in-scope production data are configured to run on the defined schedule with defined retention.

**Population Request:**
1. Backup plan/policy configurations per in-scope data store (schedule, retention, target).
2. Population of backup job executions during the period with status.

**Sample Request:** N/A.

**Testing Attributes:**
- A. Every in-scope data store covered by a backup plan (reconciles to DP-03/ASM-01 population)
- B. Schedule matches policy cadence
- C. Retention matches policy
- D. Execution success rate evidenced; failures route to BR-03

---

### BR-02 — Backup Protection *(inferred ID — and the likely true home of the row-shifted BR-04 attributes)*
**TSC:** A1.2, C1.1 | **Approach:** Configuration | **Tier 1**

**Control Description:** Backup data is encrypted, access-restricted, and retained/disposed per policy.

**Testing Attributes (adopting the attribute set that appeared under BR-04 in the source workbook):**
- A. Backup security requirements defined
- B. Backup data encrypted/protected
- C. Access to backups restricted
- D. Retention/disposal controls configured
- E. Backup storage location/environment documented
- F. Evidence supports confidentiality and recoverability

**Agent Methodology:** Pure config test over backup vault policies, KMS, IAM. Resolving the BR-03/BR-04 row shift in the source workbook should land these attributes here.

---

### DR-01 — Disaster Recovery Plan & Testing *(inferred ID)*
**TSC:** A1.3, CC9.1 | **Approach:** Sample Based | **Tier 2**

**Control Description:** A disaster recovery/business continuity plan is documented, reviewed annually, and tested at least annually; results and lessons learned are documented.

**Population Request:**
1. Current DR/BCP document with version history and approval.
2. Population of DR tests performed during the period with date, scenario, and result.

**Sample Request:** For the selected DR test, provide the test plan, scenario/scope, execution evidence, results, issues identified, and remediation tracking.

**Testing Attributes:**
- A. DR plan current (reviewed within 12 months, approved)
- B. Test performed within required frequency
- C. Test scenario and scope documented
- D. Outcome/success documented against RTO/RPO targets
- E. Issues/lessons learned tracked to closure
- F. Test frequency aligns to policy

*(Attributes C–F mirror the restoration-test attribute set that appeared row-shifted under BR-03 — same archetype, applied at DR level.)*

**Agent Methodology:** Population and metadata (dates, versions, approvals) are Tier 1 via document-system APIs. The judgment "did the test outcome demonstrate recoverability against RTO/RPO" is a D-4 semantic gate item.

---

## 6. Operations, Monitoring, Incidents, Change — new controls

### LM-01 — Centralized Logging Configuration *(inferred ID)*
**TSC:** CC7.2, CC2.1 | **Approach:** Configuration | **Tier 1**

**Control Description:** Security-relevant logs from in-scope systems are centralized in the SIEM/log platform and protected from modification.

**Population Request:**
1. Log source inventory: in-scope systems vs. sources reporting into the SIEM (with last-event timestamps).
2. Log pipeline/ingestion configurations and log-storage immutability settings.

**Sample Request:** N/A.

**Testing Attributes:**
- A. All in-scope systems represented as active log sources (reconciles to ASM-01)
- B. Sources actively reporting during the period (no silent gaps > threshold)
- C. Log storage write-protected/immutable (Object Lock requires versioning — Lane 1, fails loud)
- D. Ingestion changes tie to approved changes

**Agent Methodology:** Attribute B is the critical fail-silent check — a source that stopped reporting mid-period looks fine in a config screenshot. The runner asserts event-continuity per source across the window.

---

### LM-02 — Security Alert Triage *(inferred ID)*
**TSC:** CC7.2 | **Approach:** Sample Based | **Tier 1**

**Control Description:** Security alerts generated by monitoring tooling are triaged, investigated, and dispositioned within defined SLAs.

**Population Request:**
1. Alerting rule configurations and routing.
2. Population of security alerts during the period with severity, created/triaged/closed timestamps.

**Sample Request:** For the (X) selected alerts, provide the alert record, investigation notes, and disposition.

**Testing Attributes:**
- A. Alert population complete
- B. Severity assigned at creation
- C. Triage within SLA by severity
- D. Investigation documented
- E. Disposition/closure documented

**Agent Methodology:** Same archetype as IM-07 — severity-based SLA constants are human-ratified from the IR policy (carrying forward the IM-07 reviewer note), then attributes are pure timestamp math.

---

### LM-04 — Time Synchronization *(inferred ID)*
**TSC:** CC7.2, CC8.1 | **Approach:** Configuration | **Tier 1**

**Control Description:** In-scope systems synchronize clocks to an authoritative NTP source; audit timestamps are recorded in UTC.

**Testing Attributes:**
- A. NTP configuration present on in-scope systems
- B. Authoritative source configured
- C. Timestamps recorded in UTC
- D. Drift within tolerance where measurable

*(Mandatory per `Constraints.md` — clock drift is no longer acceptable; also a precondition for every timestamp-based attribute in this library.)*

---

### IM-01 — Incident Response Plan *(inferred ID)*
**TSC:** CC7.3–7.5 | **Approach:** Inspection | **Tier 2**

**Control Description:** An incident response plan defining roles, severity classification, escalation, and communication is documented, approved, reviewed annually, and exercised (tabletop) at least annually.

**Population Request:**
1. Current IR plan with version history, approval, and review date.
2. Evidence of the most recent tabletop/exercise with participants and outcomes.

**Testing Attributes:**
- A. Plan current (reviewed ≤ 12 months, approved)
- B. Severity/SLA matrix defined (feeds IM-07, LM-02 predicates)
- C. Exercise performed within frequency
- D. Exercise outcomes and improvements tracked

---

### IM-02 — Incident Identification & Logging *(inferred ID)*
**TSC:** CC7.3 | **Approach:** Sample Based | **Tier 1**

**Control Description:** Security events are logged as incident tickets with required fields at creation (reporter, description, severity, timestamps).

**Population Request:**
1. The population of tickets created for identified security events during the period under review. *(Same population as IM-04/05/07 — one pull, four controls.)*

**Sample Request:** For the (X) selected tickets, provide ticket creation record with required fields.

**Testing Attributes:**
- A. Incident population complete (C4: SIEM escalations vs. ticket population)
- B. Required fields populated at creation
- C. Creation timestamp within detection SLA of triggering alert

---

### IM-06 — External Incident Communication *(inferred ID)*
**TSC:** CC7.4, CC2.3 | **Approach:** Sample Based | **Tier 2**

**Control Description:** For incidents meeting defined criteria, affected customers and regulators are notified within committed/contractual timeframes.

**Population Request:**
1. Population of incidents meeting external-notification criteria during the period.

**Sample Request:** For the (X) selected incidents, provide the notification artifact, recipients, and send timestamp versus the contractual/regulatory clock.

**Testing Attributes:**
- A. Notification-triggering incidents identified per criteria
- B. Notification issued
- C. Notification within committed timeframe
- D. Content approved per plan

**Agent Methodology:** Tier 2 because "meets notification criteria" is a semantic judgment (D-4 gate); once the trigger population is ratified, timing attributes are pure functions.

---

### TVM-02 — Vulnerability Remediation *(inferred ID)*
**TSC:** CC7.1 | **Approach:** Sample Based | **Tier 1**

**Control Description:** Identified vulnerabilities are remediated within SLAs defined by severity; exceptions are documented with risk acceptance.

**Population Request:**
1. Population of vulnerabilities identified during the period with severity, detection date, and resolution date/status.
2. Population of open vulnerability exceptions with approval and expiry.

**Sample Request:** For the (X) selected vulnerabilities, provide remediation evidence (patch/fix record, rescan showing closure) or the approved exception.

**Testing Attributes:**
- A. Vulnerability population complete (scanner API, all in-scope assets per ASM-01)
- B. Severity assigned
- C. Remediated within SLA by severity
- D. Closure verified by rescan
- E. Exceptions approved, time-boxed, with owner (per Constraints: expiry + owner + closure criteria)

---

### TVM-03 — Penetration Testing *(inferred ID)*
**TSC:** CC4.1, CC7.1 | **Approach:** Inspection + sample | **Tier 2**

**Control Description:** An independent penetration test is performed at least annually; findings are tracked to remediation or risk acceptance.

**Population Request:**
1. Most recent penetration test report with scope, methodology, tester independence, and date.
2. Population of findings with severity and remediation status.

**Sample Request:** For the (X) selected findings, provide remediation evidence or approved risk acceptance.

**Testing Attributes:**
- A. Test performed within frequency
- B. Scope covers in-scope systems
- C. Tester independent of the environment
- D. Findings tracked with owner
- E. Findings remediated or risk-accepted within SLA

**Agent Methodology:** Findings-tracking attributes are Tier 1 once findings are in the tracker; report scope adequacy (B) is the semantic-gate item. This resolves the CM-02 reviewer question the same way: **"material findings tracked to closure or risk acceptance" is the general attribute archetype for any third-party assessment control** — apply it uniformly to CM-02, CM-06, TVM-03, VRM-02.

---

## 7. Governance, People, Risk, Vendors (CC1–CC5, CC9)

### HR-01 — Background Checks
**TSC:** CC1.4 | **Approach:** Sample Based | **Tier 2**

**Control Description:** Background checks are performed for new hires prior to or within a defined period of the start date, to the extent permitted by law.

**Population Request:**
1. Population of new hires during the period from the HRIS, with start dates and worker type.

**Sample Request:** For the (X) selected new hires, provide the background check completion record and completion date.

**C&A:** Authoritative source is HRIS (Workday). Lane hazards from the constraint catalog apply directly: RaaS 30-min timeout and 50,000-row boundary (Lane 1, loud); report must be Advanced + web-service-enabled (Lane 1). Pseudo-pagination via report parameters where needed.

**Testing Attributes:**
- A. New hire population complete
- B. Background check record present per hire
- C. Check completed before start date or within defined window
- D. Adverse results dispositioned per policy (Tier 2 — human judgment)

---

### HR-02 — Security Awareness Training
**TSC:** CC1.4, CC2.2 | **Approach:** Full population | **Tier 1**

**Control Description:** Personnel complete security awareness training upon hire and annually thereafter.

**Population Request:**
1. Active personnel population from HRIS with hire dates.
2. LMS training completion records with completion dates and course version.

**Sample Request:** N/A (full-population join).

**Testing Attributes:**
- A. Personnel population complete (HRIS ↔ IdP reconciliation)
- B. New-hire training completed within onboarding window
- C. Annual refresher completed within the period for all tenured staff
- D. Non-completions escalated/dispositioned

**Agent Methodology:** Textbook Tier 1 join: HRIS population × LMS completions on employee ID. The join key discovery is exactly the agent's §3 planning job; the join executes deterministically.

---

### HR-03 — Policy Acknowledgment *(inferred ID)*
**TSC:** CC1.1, CC2.2 | **Approach:** Full population | **Tier 1**

**Control Description:** Personnel acknowledge the code of conduct and acceptable use/security policies upon hire and upon material update.

**Population/Attributes:** Same join archetype as HR-02 (HRIS population × acknowledgment records). Attributes: population complete; acknowledgment present; within window; re-acknowledgment after material policy updates.

---

### GV-01 — Policy Review Cadence *(inferred ID)*
**TSC:** CC5.3, CC2.1 | **Approach:** Full population of policies | **Tier 2**

**Control Description:** Information security policies are documented, approved by management, and reviewed at least annually.

**Population Request:**
1. Policy register: in-scope policies with owner, version, last-review date, approver.

**Testing Attributes:**
- A. Policy register complete against required policy set
- B. Each policy reviewed ≤ 12 months
- C. Approval by designated owner captured
- D. Material changes communicated (→ HR-03 re-acknowledgment)

**Agent Methodology:** Document-platform APIs give version/date/approver deterministically (Tier 1 mechanics); "required policy set" is human-ratified. Content adequacy is not tested here — only cadence and approval anchors.

---

### GV-02 — Board/Committee Oversight | **CC1.2 | Tier 3**
### GV-03 — Organizational Structure & Reporting Lines | **CC1.3 | Tier 3**
### GV-04 — Internal Communication of Objectives | **CC2.2 | Tier 3**
### GV-05 — Code of Conduct Program | **CC1.1 | Tier 3** (acknowledgment mechanics live in HR-03, Tier 1)
### HR-04 — Job Descriptions/Competence | **CC1.4 | Tier 3**
### HR-05 — Accountability & Sanctions | **CC1.5 | Tier 3**
### RM-03 — Fraud Risk Consideration | **CC3.3 | Tier 3**
### RM-04 — Insurance & Risk Mitigation | **CC9.1 | Tier 3**

**Tier 3 register treatment (uniform):** the agent's only deliverable is a deterministic anchor record — document/minutes hash, version, date, approver identity, meeting cadence count — written to WORM. No attribute testing above the anchor; auditor inspects content directly. Do not build attribute skills for these; build one generic `governance-anchor` skill that takes a document register as its population.

---

### RM-01 — Annual Risk Assessment *(inferred ID)*
**TSC:** CC3.1–3.4 | **Approach:** Inspection | **Tier 2**

**Control Description:** A formal risk assessment covering in-scope systems is performed at least annually; identified risks are rated and treatment decisions documented.

**Testing Attributes:**
- A. Assessment performed within frequency
- B. Scope covers in-scope systems/objectives
- C. Risks rated per methodology
- D. Treatment decisions documented with owners
- E. Management approval retained

---

### RM-02 — Risk Register Maintenance *(inferred ID)*
**TSC:** CC3.2 | **Approach:** Full population | **Tier 2**

**Population Request:** Risk register export with risk, rating, owner, treatment, review date.

**Testing Attributes:** A. Register current (reviewed within cadence) B. Each risk has owner and treatment C. High risks tie to remediation items (join → MA-02) D. Changes tracked.

---

### MA-01 — Control Monitoring / Internal Assessment *(inferred ID)*
**TSC:** CC4.1 | **Approach:** Inspection | **Tier 2**

**Control Description:** Management performs periodic internal assessments of control operation (internal audit, control self-assessment, or continuous monitoring) and reports results.

**Testing Attributes:** A. Assessment performed per cadence B. Scope defined C. Results documented D. Deficiencies routed to MA-02.

**Agent Methodology:** Note the recursion — Aegis itself becomes the evidence for this criterion. The WORM-backed run ledger (every deterministic execution, hash-chained) *is* CC4.1 continuous-monitoring evidence. Design the run ledger export as a first-class artifact now.

---

### MA-02 — Deficiency Remediation Tracking *(inferred ID)*
**TSC:** CC4.2 | **Approach:** Sample Based | **Tier 1**

**Control Description:** Control deficiencies and audit findings are logged, assigned an owner, and remediated within defined timelines; exceptions are risk-accepted with expiry.

**Population Request:**
1. Population of deficiencies/findings opened or open during the period, with severity, owner, open/close dates.

**Sample Request:** For the (X) selected items, provide remediation evidence or approved, time-boxed risk acceptance.

**Testing Attributes:** A. Finding population complete B. Owner assigned C. Remediated within SLA by severity D. Closure evidence retained E. Exceptions time-boxed with expiry and owner.

---

### VRM-01 — Vendor Risk Assessments *(inferred ID)*
**TSC:** CC9.2 | **Approach:** Sample Based | **Tier 2**

**Control Description:** New vendors with access to confidential data or production are risk-assessed prior to onboarding; existing critical vendors are reassessed on a defined cadence.

**Population Request:**
1. Vendor inventory with criticality tier and onboarding date.
2. Population of vendor assessments during the period.

**Sample Request:** For the (X) selected vendors, provide the completed assessment, reviewer, date, and disposition.

**Testing Attributes:** A. Vendor population complete (procurement/payments reconciliation as C4) B. Assessment prior to onboarding C. Reassessment within cadence for critical vendors D. Issues dispositioned.

---

### VRM-02 — Vendor SOC Report / Attestation Review *(inferred ID)*
**TSC:** CC9.2 | **Approach:** Sample Based | **Tier 2**

**Control Description:** SOC 2 (or equivalent) reports for critical subservice organizations are obtained and reviewed annually, including CUEC mapping and exception evaluation.

**Testing Attributes:** A. Report obtained for each critical vendor B. Coverage period appropriate (bridge letter where gapped) C. Review documented D. Exceptions/CUECs evaluated and mapped to internal controls E. Material findings tracked to closure or risk acceptance.

---

### PS-01 — Physical Access *(inferred ID)*
**TSC:** CC6.4 | **Approach:** Inherited/Inspection | **Tier 2**

For cloud-native scope: inherited from the cloud provider — the testable artifact is VRM-02 review of the provider's SOC 2 (data-center physical criteria) plus CUEC mapping. Only build office badge-system testing if offices are in scope.

---

## 8. Processing Integrity (PI1) — scope-dependent

Include only if PI is a contracted category. Given data-feed products, PI is a plausible scope; the archetypes are strong Tier 1 candidates because feed systems are heavily instrumented:

### PI-01 — Input Validation *(inferred ID)* | PI1.2 | Tier 1/2
Data inputs (source data, oracle inputs) are validated against defined quality criteria before processing; rejects are logged and dispositioned.
**Attributes:** A. Validation rules configured per input class B. Rules match documented data quality criteria (human-ratified) C. Reject/exception population complete D. Sampled rejects dispositioned.

### PI-02 — Processing Monitoring & Deviation Detection *(inferred ID)* | PI1.3 | Tier 1
Processing (e.g., feed computation/aggregation) is monitored for deviation/anomaly; deviations alert and are investigated.
**Attributes:** A. Deviation monitoring configured with thresholds B. Alert population complete C. Sampled deviations investigated within SLA D. Resolution documented. *(Same archetype as CAP-01/LM-02 — reuse the alert-triage skill.)*

### PI-03 — Output Completeness & Delivery *(inferred ID)* | PI1.4–1.5 | Tier 1/2
Outputs are delivered completely, accurately, and timely to authorized destinations; delivery failures are detected and remediated.
**Attributes:** A. Output/delivery population complete B. Delivery success monitored C. Failures alerted and remediated D. Output retained per requirements.

---

## 9. Privacy (P-series)

Out of scope unless the privacy category is contracted. If it enters scope, the agent-testable subset follows the same archetypes: consent records (full-population join), DSR request SLAs (ticket-population timestamp math, Tier 1), data inventory/lineage (reconciliation, Tier 1 mechanics — note the column-level lineage requirements already in `Constraints.md`), retention/disposal (extends DP-06). Notice/choice content adequacy is Tier 3.

---

## 10. Build Order (what "easily testable" means in practice)

Priority is determined by three factors: population already API-native, attributes pure-function, and reuse of an existing archetype. Recommended skill-file build sequence:

**Wave 1 — pure Tier 1, single-source, existing archetypes:**
AM-03 (MFA), AM-04 (privileged), ASM-01 (inventory backbone — build first, everything reconciles to it), ASM-02, DP-01, DP-03, BR-01, BR-02, NS-01, LM-01, LM-04, HR-02, HR-03, TVM-02, MA-02.

**Wave 2 — Tier 1 with cross-system joins or SLA predicates needing one-time human ratification:**
AM-02, AM-08, NS-02, LM-02, IM-02, plus the already-specced sample-based set (AM-01/05/06, ASM-03/04/05, IM-04/05/07, CM-03/04/05/07, TVM-01, CFG-02/03, DP-02/05, BR-03/04, CAP-01).

**Wave 3 — Tier 2 hybrids (deterministic population + D-4 semantic gate):**
CM-02, CM-06, CM-08 (existing), DR-01, TVM-03, VRM-01/02, HR-01, GV-01, RM-01/02, MA-01, IM-01/06, DP-06, CAP-02, ELC-03, PS-01, PI-01/03.

**Not built (Tier 3 — generic governance-anchor skill only):**
GV-02/03/04/05, HR-04/05, RM-03/04.

**Cross-cutting reuse:** five attribute archetypes cover ~80% of the library — (1) approval-before-action with SoD, (2) full-population config assertion, (3) population join across two systems, (4) alert/ticket SLA timestamp math with severity-tiered constants, (5) third-party assessment with findings-tracked-to-closure. Build these as shared skill primitives; individual control skills become thin declarations (authoritative source, join key, predicate constants, tolerance semantics) over the five primitives.

---

## Open items

1. Reconcile all *(inferred)* control IDs against the live control matrix; renumber where real controls exist.
2. Ratify the severity-SLA matrix once (IR policy) — it parameterizes IM-07, LM-02, TVM-02, MA-02, NS-02.
3. Confirm PI scope (data feeds) — changes Wave planning materially.
4. Resolve BR-03/BR-04 attribute row shift; BR-02 above is the proposed landing spot.
5. Decide the CUEC mapping owner for inherited criteria (CC6.4 physical, portions of A1.2 environmental).
