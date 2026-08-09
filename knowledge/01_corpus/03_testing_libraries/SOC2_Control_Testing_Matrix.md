# SOC 2 Control Testing Matrix — Test Procedures, Population/Sample Requests, and Testing Attributes

**Source:** Transcribed from workpaper spreadsheet screenshots (Book1.xlsx, Sheet1), 2026-07-16.
**Purpose:** Canonical context for building agentic testing skill files. Each control entry captures: control metadata, SOC 2 test procedure language, population request (from Anec), sample request (from Anec), C&A (completeness & accuracy) attributes where defined, and draft testing attributes.

**Transcription notes:**
- All controls are marked **Sample Based** in the testing-approach column unless noted.
- Items in `[RED]` were highlighted red in the source (draft edits/additions under discussion).
- Items under **Reviewer Notes** were in the far-right notes column (column K) — these are open comments, not final attributes.
- `[...]` marks text cut off at the edge of a screenshot or illegible.
- ⚠️ Apparent data-quality issue in source: the Testing Attributes for BR-03 and BR-04 appear row-shifted (BR-03's attributes describe restoration testing; BR-04's describe backup protection). Flagged inline — reconcile against the live workbook.

---

## Access Management

### AM-01 — Source Code Access
**Domain:** Access Management | **Approach:** Sample Based

**Control Description:** InfoSec team grants access to the source code repositories to appropriate personnel on an as-needed basis. Access is approved by the reporting manager prior to being granted.

**Test Procedures (From SOC 2):** For a sample of source code repository access requests approved during the examination period, inspect the corresponding request tickets to verify access was approved by the requester's reporting manager prior to provisioning. Further inspect provisioning evidence (e.g., repository access logs or user/role screenshots) to verify the access granted aligned to the approved request and that the approver and the individual provisioning access were different.

**Population Request (From Anec):**
1. The population of personnel granted access to the source code repositories.

**Sample Request (From Anec):** For selected users, provide the Jira ticket showing:
1. Request date
2. Manager approval
3. InfoSec provisioning execution

**C&A Attributes:**
- *Completeness:* a. Extract row count matches source report.
- *Accuracy:* a. Sample 1 user from extract to ensure all details match source. b. Sample 1 user from source to ensure all data elements match extract.

**Testing Attributes (Draft):**
- A. Ticket/request present
- B. Approval obtained before access grant
- C. Reporting manager or Security approval present `[RED]`
- D. Assignee is not the same as approver
- E. InfoSec/security provisioning `[RED]`
- F. Access level/repository matches approved request

---

### AM-05 — Access Approval
**Domain:** Access Management | **Approach:** Sample Based

**Control Description:** Requests for new access, or modifications to existing access for employees or contractors, are submitted and approved prior to granting access to the in-scope systems.

**Test Procedures (From SOC 2):** For a sample of new access and access modification requests during the examination period, inspected request and approval evidence and inspected system provisioning evidence (e.g., administration screens or audit logs) to ascertain access was granted/changed only after approval and in accordance with the approved request.

**Population Request (From Anec):**
1. The population of access grants to in-scope systems.

**Sample Request (From Anec):** For the (X) selected samples, please provide Jira tickets for selected users showing request submission and manager approval prior to the access being granted.

**Testing Attributes (Draft):**
- A. Ticket/request present
- B. Approval obtained before provisioning date
- C. Granted access matches approved request
- D. Assignee is not the same as approver
- E. Scope includes new and modified access (permission/role)

---

### AM-06 — Terminations
**Domain:** Access Management | **Approach:** Sample Based

**Control Description:** Logical access to systems for employees and contractors is revoked as part of the termination process within 5 business days of the individual's [termination date...].

**Test Procedures (From SOC 2):** For a sample of employee and contractor terminations for the review period, inspect termination notification evidence and inspect Okta deprovisioning evidence to ascertain logical access was revoked within 5 business days of the termination date. For a sample of time-bound external collaborator access grants for the review period, inspect the approved [...].

**Population Request (From Anec):**
1. Population of terminated employees and contractors during the review period, including termination date, worker type, and system account identifier.
2. Population of time-bound external collaborator access grants during the review period, including approved end date and system/account identifier.

**Sample Request (From Anec):**
1. For the (X) selected terminated individuals, please provide termination notification evidence, termination date, and evidence showing Okta access was revoked within 5 business days of termination.
2. For the (X) selected collaborators, please provide the approved request showing the end date and evidence that access was revoked at the defined expiration.

**Testing Attributes (Draft):**
- *Okta:*
  - A. Termination or end-date notification present
  - B. Deprovisioning evidence present (Splunk)
  - C. Access revoked within 5 business days or defined expiration
- *GitHub:*
  - D. Time-bound external collaborator access to GitHub

---

## Asset Management

### ASM-03 — Endpoint Protection
**Domain:** Asset Management | **Approach:** Sample Based

**Control Description:** Endpoint Detection and Response (EDR) software is installed on all company-managed workstations to detect malware infections. EDR software is configured to receive updates on a periodic basis.

**Test Procedures (From SOC 2):** Inspect endpoint detection and response (EDR) deployment and update configuration within endpoint management tooling to ascertain EDR was required on company-managed workstations and configured to receive periodic updates. For a sample of workstations, inspect endpoint status evidence to corroborate the EDR agent was installed and reporting during the examination period.

**Population Request (From Anec):**
1. The population of workstations (Linux, Windows, Mac) issued to employees and contractors.
2. Please provide evidence of EDR agents deployed to workstations issued to all employees and contractors.
3. Please provide evidence of security definitions being updated on all workstations.
4. Please provide evidence of follow-ups for workstations where the EDR were not timely updated.

**Sample Request (From Anec):** For the (X) selected sample(s), please provide endpoint status evidence showing the EDR agent was installed and reporting on the sampled workstation during the period.

**Testing Attributes (Draft):**
- A. EDR installed on sampled devices
- B. EDR agent reporting/healthy
- C. Periodic updates configured
- D. Population of managed workstations complete
- E. Non-reporting devices investigated as applicable

---

### ASM-04 — Patch Management
**Domain:** Asset Management | **Approach:** Sample Based

**Control Description:** Company-managed workstations are updated with security patches after testing and approval by IT team. The IT team follows up with custodians of workstations if the security patches are not applied correctly.

**Test Procedures (From SOC 2):** For a sample of workstation security patch deployments for the review period, inspect patch testing and approval evidence and inspect deployment status/reporting evidence to verify patches were applied after appropriate testing and approval. Where devices were not successfully patched within expected timelines, inspect follow-up evidence to verify the IT team followed up with workstation custodians.

**Population Request (From Anec):**
1. Population of workstations (Linux, Windows, Mac) issued to employees and contractors.
2. Evidence of security patches for OS and applications being tested and approved prior to deployment to all employees and contractors.
3. Evidence of security patches being applied on all workstations.
4. Evidence of follow-ups for workstations where the security patches were not timely applied.

**Sample Request (From Anec):** For the (X) selected sample(s), please provide evidence of patch testing and approval prior to deployment, deployment status/reporting showing patches were applied, and follow-up evidence for any devices not patched within the expected timeline.

**Testing Attributes (Draft):**
- A. Patch population/deployments identified
- B. Patch testing evidence present
- C. Patch approval evidence present
- D. Deployment status/reporting evidence present
- E. Patches applied after testing/approval
- F. Unpatched devices followed up with custodians

---

### ASM-05 — Data Sanitization
**Domain:** Asset Management | **Approach:** Sample Based

**Control Description:** Upon termination of employees and contractors, the data residing on company-managed workstations is purged in [accordance with the IT Offboarding Procedure...].

**Test Procedures (From SOC 2):** For a sample of terminated employees and contractors for the review period, inspect IT offboarding records to verify company-managed workstation data was purged in accordance with the IT Offboarding Procedure.

**Population Request (From Anec):**
1. Population of terminated employees and contractors during the period under review.

**Sample Request (From Anec):**
1. For a sample, please provide evidence of all data being wiped from the company-issued workstation upon termination.

**Testing Attributes (Draft):**
- A. Terminated user population complete
- B. IT offboarding record present
- C. Company-managed workstation identified
- D. Data purge/wipe evidence present
- E. Purge follows IT Offboarding Procedure

---

## Backup and Restoration

### BR-03 — Backup Monitoring
**Domain:** Backup and Restoration | **Approach:** Sample Based

**Control Description:** Backups are continuously monitored for failures using an automated system. In an event of a failure, an alert is generated and assigned to the appropriate team member for investigation and resolution.

**Test Procedures (From SOC 2):** Inspect the configuration for monitoring backup execution; configurations are set to alert the InfoSec team when a backup fails. Inspected a sample of backup failures to ensure alerts were generated, investigated, and resolved. **D&T note there currently is no monitoring of backups.**

**Population Request (From Anec):**
1. Configurations for backup monitoring and alerting for in-scope products.
2. The population of failed backups for the period under review.

**Sample Request (From Anec):**
1. From the samples in the population, please provide evidence of investigation and resolution.

**Testing Attributes (Draft) — ⚠️ as shown in source; these describe restoration testing and likely belong to BR-04 (row shift):**
- A. Restoration test performed
- B. Test scenario and scope documented
- C. Backup used for restoration is identifiable
- D. Restoration outcome/success documented
- E. Issues/lessons learned tracked
- F. Test frequency aligns to policy

---

### BR-04 — Backup Integrity Testing
**Domain:** Backup and Restoration | **Approach:** Sample Based

**Control Description:** Management restores archival data on a periodic basis in accordance with CLL's Backup & Restoration Schedule to ascertain integrity and availability of backups.

**Test Procedures (From SOC 2):** Inspect a sample of monthly backup restore tests to ensure backup integrity and availability was appropriate.

**Population Request (From Anec):**
1. Population of backup restore tests performed during the review period for in-scope systems, including test date, system, and result.
2. The results of the most recent periodic restore for in-scope products.

**Sample Request (From Anec):** For the (X) selected samples, please provide restore test evidence, including the test performed, results, any issues identified, and evidence of follow-up or remediation where applicable.

**Testing Attributes (Draft) — ⚠️ as shown in source; these describe backup protection/security, not restore testing (row shift suspected):**
- A. Backup security requirements defined
- B. Backup data encrypted/protected
- C. Access to backups restricted
- D. Retention/disposal controls configured
- E. Backup storage location/environment documented
- F. Evidence supports confidentiality and recoverability

---

## Capacity Management

### CAP-01 — Capacity Monitoring (Ongoing)
**Domain:** Capacity Management | **Approach:** Sample Based

**Control Description:** The Infra team monitors infrastructure processing capacity on an ongoing basis. Monitoring tools are configured to identify and automatically alert administrators [...].

**Test Procedures (From SOC 2):** Inspect evidence of periodic infrastructure capacity reviews and forecasts to verify that current usage, future demand, and scaling requirements are assessed and documented by Infra and Product teams.

**Population Request (From Anec):**
1. Configurations for in-scope capacity and utilization monitoring, including defined thresholds and alert routing.
2. Population of capacity-related alerts generated during the review period for in-scope systems.

**Sample Request (From Anec):** For the (X) selected samples, please provide the alert record, evidence of investigation, ticket or tracking record, and evidence of resolution or other action taken.

**Testing Attributes (Draft):**
- A. Capacity/utilization monitoring configured
- B. Thresholds defined
- C. Alerts generated on breach
- D. Alert/ticket logged
- E. Investigation and escalation evidenced
- F. Resolution tracked
- G. Monitoring covers in-scope infrastructure

---

### CAP-02 — Capacity Monitoring (Annual Review/Forecast)
**Domain:** Capacity Management | **Approach:** Sample Based

**Control Description:** Annually, the Infra team, in coordination with product teams, assesses its current infrastructure usage and demands for all upcoming projects and forecasts future processing demand for infrastructure components.

**Test Procedures (From SOC 2):** Inspect the most recent review of the Infra and product teams where both teams assessed the current infrastructure usage and demands and demand for all upcoming projects. Further, D&T inspect the most recent forecast for future processing demands for infrastructure components.

**Population Request (From Anec):**
1. Evidence of the most recent infrastructure capacity review or forecast meeting for in-scope systems.
2. Forecast outputs, capacity plans, or action logs resulting from those reviews.

**Sample Request (From Anec):** For the (X) selected samples, please provide meeting materials, capacity forecasts, documented conclusions, and evidence of resulting actions taken based on forecasted demand.

**Testing Attributes (Draft):**
- A. Capacity review/forecast performed
- B. Infra and product stakeholders involved
- C. Current and future needs assessed
- D. Metrics/materials support conclusions
- E. Actions or resource needs documented
- F. Management review/approval retained

---

## Configuration Management

### CFG-02 — Baseline Enforcement
**Domain:** Configuration Management | **Approach:** Sample Based

**Control Description:** Baseline configurations are enforced on critical applications and infrastructure in line with the hardening standards.

**Test Procedures (From SOC 2):** Inspect system configurations and a sample of infrastructure components to verify that defined hardening standards are implemented consistently across environments.

**Population Request (From Anec):**
1. Evidence that hardening standards are enforced for in-scope systems.

**Sample Request (From Anec):** N/A

**Testing Attributes (Draft):**
- A. Baseline configurations enforced
- B. In-scope components identified
- C. Configuration evidence matches hardening standard

---

### CFG-03 — Drift Monitoring
**Domain:** Configuration Management | **Approach:** Sample Based

**Control Description:** Baseline configurations are monitored for hardening drifts and re-enforced as necessary.

**Test Procedures (From SOC 2):** Inspect monitoring processes and a sample of alerts to verify that deviations from hardening standards are detected, reported, and remediated in a timely manner.

**Population Request (From Anec):**
1. Evidence of monitoring tool/process used for detecting hardening drifts and raising alerts.
2. Population of alerts raised from hardening drifts along with remediation performed.

**Sample Request (From Anec):**
1. For (X) sample alerts, provide evidence supporting the investigation and remediation of hardening drift.

**Testing Attributes (Draft):**
- A. Enforcement automated or centrally managed reporting
- B. Exceptions/remediation tracked

---

## Data Protection

### DP-02 — Data Loss Prevention
**Domain:** Data Protection | **Approach:** Sample Based

**Control Description:** Data loss prevention rules are configured to monitor emails, cloud storage providers, and workstations for confidential information, as defined in the Data Classification Standard, in outgoing transmissions. Alerts are generated for cases of sensitive information being exfiltrated and investigated by the ITT team.

**Test Procedures (From SOC 2):** Inspect data loss prevention (DLP) rule configurations for email, cloud storage, and workstations to verify monitoring rules for confidential information were configured in accordance with the Data Classification Standard. For a sample of DLP alerts generated for the review period, inspect alert records and investigation documentation to ascertain alerts were generated as configured and were investigated by the ITT team.

**Population Request (From Anec):**
1. Evidence of DLP/data protection rules configured for email, cloud storage, and workstations for monitoring confidential information.
2. Population of DLP alerts generated during the review period related to potential sensitive information exfiltration.

**Sample Request (From Anec):**
1. For sample of alerts selected, please provide evidence of actions taken to resolve the alerts raised.

**Testing Attributes (Draft):**
- A. DLP rules configured for email/cloud/workstations
- B. Rules map to confidential information definitions
- C. Alerts generated for potential exfiltration
- D. Alert population complete
- E. Sample alerts investigated by ITT
- F. Disposition/remediation documented

---

### DP-04 — Key Storage Encryption
**Domain:** Data Protection | **Approach:** Sample Based

**Control Description:** Private key material used to sign blockchain transactions is stored in a vault in an encrypted manner.

**Test Procedures (From SOC 2):** Inspect evidence of how private key material used to sign blockchain transactions is stored in a vault in an encrypted manner.

**Population Request (From Anec):**
1. Population of in-scope private keys or signing keys supporting blockchain transaction signing.
2. Configuration listings showing the storage location and protection mechanism for each in-scope key.

**Sample Request (From Anec):** For the (X) selected samples, please provide evidence that the private key material is stored in an approved encrypted key management system, including configuration screenshots, KMS settings, vault settings, or equivalent evidence of encrypted storage and access restriction.

**Testing Attributes (Draft):**
- A. Private/signing key population identified
- B. Key storage location/tool documented
- C. Vault/encryption configuration enabled
- D. Access restricted to authorized personnel/processes
- E. Sample key evidence supports encryption
- F. Exceptions tracked/remediated

---

### DP-05 — Disk Encryption
**Domain:** Data Protection | **Approach:** Sample Based

**Control Description:** Hard disks (HDDs) or solid state drives (SSDs) of the workstation issued by the company are encrypted.

**Test Procedures (From SOC 2):** Inspect encryption configuration evidence for company-managed workstations to verify disk encryption was required. For a sample of workstations, inspect encryption status outputs to corroborate encryption was enabled for the review period.

**Population Request (From Anec):**
1. Evidence of disk encryption configurations enforced centrally for company-managed workstations.
2. Population of company-managed workstations not centrally managed through MDM (if applicable), such as Linux devices, including device identifier and owner.

**Sample Request (From Anec):**
1. For samples selected, please provide screenshot evidence indicating that HDD or SSD encryption was enabled.

**Testing Attributes (Draft):**
- A. Disk encryption policy/configuration enabled
- B. Managed workstation population complete
- C. Sample device encryption status present
- D. Encryption enabled during period
- E. Evidence includes HDD/SSD where applicable
- F. Noncompliant devices investigated

---

## Entity Level Controls

### ELC-03 — Client Communication *(partial — cut off in source)*
**Domain:** Entity Level Controls | **Approach:** Sample Based

**Control Description:** Management communicates with clients its terms of service and service [...].

**Test Procedures (From SOC 2):** Inspect fully executed contracts to verify clients were provided a formal service [...].

**Population Request (From Anec):**
1. Population of customer agreements executed during the review period that required formal [...].

**Sample Request (From Anec):** For a sample of customer agreements executed for the review period, inspect fully executed [...].

**Testing Attributes (Draft):**
- A. Customer agreement/terms present
- B. Service responsibilities [...]

---

## Incident Management

### IM-04 — Root Cause Analysis
**Domain:** Incident Management | **Approach:** Sample Based

**Control Description:** For security incidents identified, a root cause analysis is prepared and documented by the Incident Response team.

**Test Procedures (From SOC 2):** For a sample of security incidents recorded for the review period, inspect incident records and inspect associated root cause analysis documentation to verify root cause analysis was prepared and documented by the Incident Response team.

**Population Request (From Anec):**
1. The population of tickets created for identified security events during the period under review.

**Sample Request (From Anec):** For the (X) selected sample(s), please provide incident tickets created along with the root cause analysis performed.

**Testing Attributes (Draft):**
- A. Incident population complete
- B. Incident record present
- C. Root cause analysis prepared
- D. RCA documented by IR team
- E. RCA linked to incident
- F. RCA completed timely/appropriately

---

### IM-05 — Corrective Action Plans
**Domain:** Incident Management | **Approach:** Sample Based

**Control Description:** Based on the root cause analysis for identified security incidents, corrective action plans are created and remediation is performed.

**Test Procedures (From SOC 2):** For a sample of incidents with completed root cause analyses for the review period, inspect corrective action plans and remediation evidence to verify corrective actions were created and remediation was performed.

**Population Request (From Anec):**
1. The population of tickets created for identified security events during the period under review.

**Sample Request (From Anec):** For the (X) selected sample(s), please provide evidence of the corrective action plans that were created and the actions performed for remediation. If the incident is open, please provide current status of remediation of the incident.

**Testing Attributes (Draft):**
- A. RCA completed for incident
- B. Corrective action plan created
- C. Action owner assigned
- D. Remediation evidence retained
- E. Remediation performed/tracked
- F. Closure documented

---

### IM-07 — Incident Risk Assessment
**Domain:** Incident Management | **Approach:** Sample Based

**Control Description:** The risk and impact of security incidents are assigned during initial triage.

**Test Procedures (From SOC 2):** For a sample of incidents recorded during the examination period, inspect incident ticket fields and workflow history to verify risk/impact (e.g., severity) was assigned during initial triage and that the incident was tracked through investigation to closure in accordance with documented procedures.

**Population Request (From Anec):**
1. The population of tickets created for identified security events during the period under review.

**Sample Request (From Anec):** For the (X) selected sample(s), please provide incident ticket evidence showing severity/risk/impact was assigned during initial triage and workflow history demonstrating the incident was tracked through investigation to closure in accordance with documented procedures.

**Testing Attributes (Draft):**
- A. Incident triage performed
- B. Risk/impact/severity assigned during initial triage
- C. Ticket workflow history supports timing
- D. Incident tracked through investigation
- E. Closure/disposition documented
- F. Severity aligns to procedure
- G. Incident remediation aligns with predefined SLA

**Reviewer Notes:** Check from the incident response policy how incidents with different severity are treated, and verify in sample testing whether the sampled incidents were treated on the timeline described in the policy based on severity level.

---

## SDLC / Application Security (Change Management)

### CM-02 — Third-Party Code Review
**Domain:** SDLC / Application Security | **Approach:** Sample Based

**Control Description:** Management engages a third-party code security audit firm to perform design review for new product development and before major changes to existing products to determine security requirements for the engineering team to be implemented. These security requirements are documented as part of functional specifications.

**Test Procedures (From SOC 2):** For a sample of new product developments and major changes for the review period, inspect third-party design review reports and inspect associated functional specifications to ascertain security requirements were identified by the third party and documented for engineering implementation.

**Population Request (From Anec):**
1. The population of new product developments and major changes associated with in-scope products.

**Sample Request (From Anec):** Select a sample of new product developments and major changes during the examination period; inspect third-party design/security review reports and inspect associated functional specifications to verify security requirements were identified by the third party and documented for engineering implementation.

**Testing Attributes (Draft):**
- A. New product/major change population complete
- B. Third-party design/security review performed
- C. Security requirements identified
- D. Requirements documented in functional specifications
- E. Engineering implementation requirements traceable
- F. Review completed before implementation milestone

**Reviewer Notes:** For point E — is it the same as my recommendation: material security findings tracked to closure or risk acceptance.

---

### CM-03 — Approval SOD
**Domain:** SDLC / Application Security | **Approach:** Sample Based

**Control Description:** Changes to the production environment are approved by a person other than the requester of the change, prior to deployment to production.

**Test Procedures (From SOC 2):** Selected a sample of repositories from the in-scope population. For each selected repository, inspected branch protection rules in GitHub and a sample of one change to confirm that changes to the production environment require approval by a person other than the change requestor, prior to deployment to production.

**Population Request (From Anec):**
1. Evidence that branch protection rules are enabled for all relevant repos.
2. Sample of 1 pull request to indicate the changes were approved by a person other than the author of the change prior to merging to master.

**Sample Request (From Anec):** N/A

**Testing Attributes (Draft):**
- A. In-scope repository population selected
- B. Branch protection/ruleset configured
- C. Approval required before production deployment/merge
- D. Approver differs from requester
- E. Sample PR/variant supports enforcement
- F. Bypass/admin exceptions considered

---

### CM-04 — Emergency Changes
**Domain:** SDLC / Application Security | **Approach:** Sample Based

**Control Description:** Emergency changes performed are tested and approved by Engineering Management within 24 hours of the change being implemented.

**Test Procedures (From SOC 2):** For a sample of emergency changes implemented for the review period, inspect emergency change records to ascertain the changes were designated emergency, implemented, and subsequently tested and approved by Engineering Management within 24 hours of implementation, with evidence retained.

**Population Request (From Anec):**
1. The population of emergency changes performed during the period of 6/1/2025 – 11/30/2025.

**Sample Request (From Anec):** For the (X) selected sample(s), please provide the emergency change record/ticket and supporting evidence showing the change was designated as an emergency, implemented, tested, and approved by Engineering Management within 24 hours of implementation, including incident tracking or war room documentation where applicable.

**Testing Attributes (Draft):**
- A. Emergency change population complete
- B. Change designated emergency
- C. Implementation timestamp evidenced
- D. Testing performed within 24 hours
- E. Engineering management approval within 24 hours
- F. Evidence retained

**Reviewer Notes:** 1. PRs were closed post-implementation.

---

### CM-05 — Change Testing
**Domain:** SDLC / Application Security | **Approach:** Sample Based

**Control Description:** All application changes undergo security testing and functional testing prior to being implemented in production.

**Test Procedures (From SOC 2):** For a sample of in-scope repositories during the examination period, inspect configuration evidence (e.g., branch protection and required CI/CD checks) and inspect pipeline/run evidence for a sample of changes to verify security testing and functional testing were required and completed prior to production implementation.

**Population Request (From Anec):**
1. Evidence that branch protection rules are enabled for all SOC 2 repos.
2. Show that CodeQL is enabled on all SOC 2 repos.
3. Sample of 1 pull request to indicate that required checks must pass for PR to merge. *(Numbered "2)" twice in source.)*

**Sample Request (From Anec):** N/A

**Testing Attributes (Draft):**
- *Configuration Test — Rely on CFG-01 – CFG-03*
- *Sample of 1:*
  - A. In-scope repositories identified
  - B. Required security tests configured
  - C. Required functional/CI tests configured
  - D. Pipeline/run evidence retained
  - E. Required tests completed before production implementation
  - F. Failed checks prevented merge/deployment

**Reviewer Notes:**
1. Security test results were reviewed.
2. Issues noted in test were resolved before implementation.
- Configuration (CFG-01 – CFG-03): 1. BPRs are configured with required checks.
- Note: As we review the checks, let's identify/confirm which are security vs. function checks.

---

### CM-06 — Smart Contract Review
**Domain:** SDLC / Application Security | **Approach:** Sample Based

**Control Description:** Management contracts with a third party to perform a security code review of each smart contract and subsequent changes to the smart contract prior to being deployed on production blockchain or mainnet.

**Test Procedures (From SOC 2):** For a sample of smart contract releases/changes during the examination period, inspect third-party security code review reports and inspect release artifacts (e.g., PR/commit references) to verify the review scope and traceability to the specific code version to be deployed were documented and completed prior to production/mainnet deployment.

**Population Request (From Anec):**
1. The population of smart contract deployments for in-scope products for the period under review.

**Sample Request (From Anec):** For each selected sample, for the (X) selected sample(s), please provide the third-party security code review report and release artifacts demonstrating the review scope and traceability to the specific code version deployed to production/mainnet.
1. Evidence showing the smart contract was deployed by GitHub Actions using the Deployment key.
2. Evidence of CLD/Pipeline PR, the Proposal PR, the GitHub Actions which ran to perform the deployment and ownership change.

**Testing Attributes (Draft):**
- A. Smart contract release/change population complete
- B. Third-party code review report obtained
- C. Review scope matches contract/version
- D. PR/commit/release artifacts traceable
- E. Review completed before mainnet/production deployment
- F. Findings dispositioned

**Reviewer Notes:** 1. Issues noted in the review were resolved prior to being deployed on prod environment.

---

### CM-07 — Release Approval
**Domain:** SDLC / Application Security | **Approach:** Sample Based

**Control Description:** Releases are documented, tested, reviewed, and approved by the Engineering team prior to being implemented in production.

**Test Procedures (From SOC 2):** For a sample release during the examination period, inspect end-to-end release evidence (e.g., pull request documentation, test results, peer review approvals, and deployment evidence) to verify releases were documented, tested, reviewed, and approved by the Engineering team prior to production implementation.

**Population Request (From Anec):**
1. Population of releases for in-scope systems during the review period.
2. For each release, available release evidence such as PR documentation, test results, peer review approvals, and deployment evidence.

**Sample Request (From Anec):** N/A

**Testing Attributes (Draft):**
- A. Release population complete
- B. Release documentation present
- C. Testing evidence retained
- D. Engineering review performed
- E. Engineering approval obtained
- F. Deployment evidence after approval

**Reviewer Notes:**
1. Review date and reviewed by.
2. Approval date and approved by.
3. Releases were approved by the appropriate personnel.
Additionally we need to check: sampled release version should match with approved version.

---

### CM-08 — Release Communication
**Domain:** SDLC / Application Security | **Approach:** Sample Based

**Control Description:** New releases are communicated to both internal and external users through release notes posted on the Company's internet site.

**Test Procedures (From SOC 2):** For a sample of releases during the examination period, inspect published release notes on the Company's internet site and inspect posting dates/links to verify releases were communicated to external users; where internal communication is also required by policy, inspect internal notifications to verify releases were communicated internally.

**Population Request (From Anec):**
1. The population of new releases for Data Feeds during the period.

**Sample Request (From Anec):** For selected sample, provide evidence of release notes published on Chainlink's website.

**Testing Attributes (Draft):**
- A. Release population complete
- B. External release notes published
- C. Posting date/link retained
- D. Release notes match sampled release
- E. Internal communication retained where required
- F. Communication occurred timely

---

## Threat and Vulnerability Management

### TVM-01 — Vulnerability Scanning *(partial — cut off in source)*
**Domain:** Threat and Vulnerability Management | **Approach:** Sample Based

**Control Description:** Vulnerability scans are performed by the InfoSec team on a weekly basis and reviewed.

**Test Procedures (From SOC 2):** Observed the configurations of the vulnerability scans to verify that the scans are performed by the InfoSec team on a weekly basis. [Source: ...]

**Population Request (From Anec):**
1. Configurations for weekly vulnerability scans performed on in-scope AWS accounts.
2. Evidence of the weekly review of [...].

**Sample Request (From Anec):** N/A

**Testing Attributes (Draft):**
- A. Weekly vulnerability scan configuration enabled
- B. In-scope assets/accounts covered
- C. Scan cadence weekly [...]
- D. Scan results reviewed by appropriate personnel *(from notes column)*

---

## Structural Schema (for agentic workflow / skill-file design)

Every control in this matrix follows the same testing pattern, which maps cleanly to an agent pipeline:

1. **Population Request** — evidence request defining the complete population (and/or configurations for config-based controls).
2. **C&A Validation** — completeness (row counts vs. source report) and accuracy (bidirectional 1-sample trace: extract→source and source→extract). Explicitly defined only for AM-01 in source, but the pattern generalizes.
3. **Sample Request** — per-sample evidence request template ("For the (X) selected sample(s)..."). Controls marked N/A are config-inspection controls (CFG-02, CM-03, CM-05, CM-07, TVM-01) tested via configuration evidence rather than transaction samples.
4. **Attribute Testing** — lettered pass/fail attributes per sample (or per configuration). Common attribute archetypes across controls:
   - Population completeness
   - Artifact/record present (ticket, report, notification)
   - Approval present and *timing* (before grant/deployment, within SLA)
   - Segregation of duties (requester ≠ approver ≠ provisioner)
   - Granted/deployed state matches approved state
   - Exception/follow-up handling evidenced
5. **Reviewer Notes** — open items to resolve before finalizing attributes (severity-based SLA verification, version matching, security-vs-functional check classification, findings-tracked-to-closure).

**Open items carried from source:**
- BR-03/BR-04 attribute row-shift needs reconciliation.
- AM-01 red attributes (C, E) are proposed edits, not confirmed.
- CM-02 point E vs. "material findings tracked to closure or risk acceptance" unresolved.
- CM-05: classify required checks as security vs. functional.
- IM-07: severity-based SLA timelines from IR policy need to be encoded into attribute G.
- ELC-03 and TVM-01 are partial transcriptions — recapture from the workbook.
