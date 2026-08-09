# Decision Ledger

## Use S3 Object Lock in Compliance Mode for AI Audit Logs

- **Decision:** New AI audit log buckets should default to Amazon S3 Object Lock configured in compliance mode.
- **Rationale:** Compliance mode ensures that objects cannot be deleted or overwritten by any user, including the root account, for the duration of the retention period. This strict immutability satisfies the reconstruction requirements expected by regulators for AI audit logs.
- **Alternatives Considered:** Governance mode was considered but rejected for this use case because it allows users with specific permissions to bypass or shorten retention, making it a weaker choice for regulatory compliance and a target for attackers.
- **Source:** AI Audit Log Immutability: Object Lock, WORM Storage, and the Storage-Layer Contract a Regulator Accepts — DeepInspect.ai.

## Inclusion of Content Hashes in Audit Log Records

- **Decision:** Every AI audit log record must include a content_hash field containing the SHA-256 hash of the record's content, computed at the moment of decision.
- **Rationale:** This allows an auditor to independently compute the hash of the stored record and confirm it matches the recorded hash. Any modification to the record will break the match, making tampering detectable without relying on external state.
- **Source:** AI Audit Log Immutability: Object Lock, WORM Storage, and the Storage-Layer Contract a Regulator Accepts — DeepInspect.ai.

## Implementation of Hash Chains for Chain-of-Custody

- **Decision:** Audit log records should be extended into a hash chain where each record includes the content hash of the previous record.
- **Rationale:** This produces a cryptographically linked list where a modification to any historical record breaks every subsequent hash in the chain. It provides strong evidence for the capture and preservation of security events, satisfying SOC 2 CC7.3 expectations.
- **Source:** AI Audit Log Immutability: Object Lock, WORM Storage, and the Storage-Layer Contract a Regulator Accepts — DeepInspect.ai.

## Content-Addressable Storage for Prompts and Responses

- **Decision:** Large audit artifacts like prompts and responses should be stored in a separate object store with content-addressable pointers (derived from the hash) in the main audit record.
- **Rationale:** Prompts and responses often exceed practical size limits for inline storage within an audit record. Storing them separately at paths derived from their own hashes ensures that any modification to the content will result in a mismatch with the reference pointer in the audit record.
- **Source:** AI Audit Log Immutability: Object Lock, WORM Storage, and the Storage-Layer Contract a Regulator Accepts — DeepInspect.ai.

## Explicit Write-Path Separation for Audit Logs

- **Decision:** The AI application is explicitly denied write access to the audit log store, with the inspection layer writing records under its own separate identity.
- **Rationale:** This separation is enforced at the cloud IAM layer to ensure that even if the AI application is compromised, an attacker has no path to modify the audit records.
- **Source:** AI Audit Log Immutability: Object Lock, WORM Storage, and the Storage-Layer Contract a Regulator Accepts — DeepInspect.ai.

## Provisioning of Scoped Auditor Read Roles

- **Decision:** Auditors should be assigned a read-only role scoped strictly to the audit log bucket with no other application permissions.
- **Rationale:** For regulator-driven audits, this role is often provisioned per audit with a defined time bound to ensure the auditor can retrieve records without any possibility of modifying them.
- **Source:** AI Audit Log Immutability: Object Lock, WORM Storage, and the Storage-Layer Contract a Regulator Accepts — DeepInspect.ai.

## Minimum 12-Field AI Audit Trail Schema

- **Decision:** A defensible AI audit trail must capture a minimum of 12 specific fields for every decision, including NTP-synced UTC timestamps, unique decision IDs, and authenticated human user identities.
- **Rationale:** These fields represent a convergence of requirements across SOX, HIPAA, GDPR, the EU AI Act, and FFIEC examinations. Failure to capture these specific attributes often results in audit findings regarding individual attribution or reconstructability.
- **Source:** AI Audit Trail Requirements: 2026 Checklist for Finance, Healthcare, Banking | Kognitos.

## Capture of Authenticated Human Identity Over Service Accounts

- **Decision:** AI audit trails must link decisions to the authenticated human user identity rather than just a service account or API key.
- **Rationale:** Service account logging cannot provide the individual attribution required by HIPAA's unique user identification rule, GDPR's accountability principle, and SOX's audit trail requirements.
- **Source:** AI Audit Trail Requirements: 2026 Checklist for Finance, Healthcare, Banking | Kognitos.

## Use of Human-Readable Reasoning Instead of Confidence Scores

- **Decision:** Audit trails must record reasoning in human-readable language rather than just probabilistic confidence scores.
- **Rationale:** Confidence scores are statistical signals and do not satisfy the "right to explanation" under GDPR Article 22, the "specific principal reasons" required by ECOA for adverse actions, or COSO 2026 guidance for internal controls.
- **Source:** AI Audit Trail Requirements: 2026 Checklist for Finance, Healthcare, Banking | Kognitos.

## Minimum Retention Period for SOX-Relevant AI Logs

- **Decision:** Operational AI audit logs for SOX-relevant systems must be retained for at least 366 days.
- **Rationale:** This ensures that logs are available for at least one full audit cycle.
- **Source:** AI Audit Trail Requirements: 2026 Checklist for Finance, Healthcare, Banking | Kognitos.

## Automated Evidence Collection via API Integrations

- **Decision:** Organizations should use AI platforms to connect directly to their tech stack via APIs for continuous SOC 2 evidence collection.
- **Rationale:** API-driven collection replaces manual tasks like taking screenshots and exporting logs, cutting audit preparation time by 80–90%. This shift enables continuous 24/7 monitoring rather than periodic point-in-time assessments.
- **Alternatives Considered:** Manual evidence collection was considered but rejected because it is time-consuming, prone to human error, and easy to manipulate.
- **Source:** AI-Powered SOC 2 Evidence Collection Explained — Censinet.

## Implementation of Customizable Rules and Approval Hierarchies

- **Decision:** AI compliance tools must be configured with customizable rules, passing criteria, and approval hierarchies.
- **Rationale:** This ensures that the AI supports the organization's unique requirements and that critical findings are routed to designated human stakeholders ("air traffic control") rather than the AI dictating the process.
- **Source:** AI-Powered SOC 2 Evidence Collection Explained — Censinet.

## Retention of Human Oversight for Critical Compliance Decisions

- **Decision:** AI validation must be paired with human oversight for all control evaluations and conclusions.
- **Rationale:** While AI is efficient at identifying anomalies in large datasets, it lacks the ability to determine which controls are audit-relevant or to interpret nuanced business contexts. Human judgment remains essential for strategic risk remediation and accountability.
- **Source:** AI-Powered SOC 2 Evidence Collection Explained — Censinet.

## Adoption of OpenLineage-Compatible Data Lineage

- **Decision:** Capture and store data lineage movement using an OpenLineage-compatible API.
- **Rationale:** OpenLineage provides a consistent, unified object model to collect and analyze lineage metadata across heterogeneous analytical services. This enables data producers to assess the impact of changes and data consumers to gain confidence in an asset's origin.
- **Source:** Amazon DataZone introduces OpenLineage-compatible data lineage visualization in preview — AWS.

## Versioning of Data Lineage Events

- **Decision:** Lineage must be versioned with each event rather than providing only a single snapshot of current state.
- **Rationale:** Versioning allows for the visualization of lineage at any point in time and the comparison of transformations across history, which is essential for troubleshooting, auditing, and point-in-time reconstruction.
- **Source:** Amazon DataZone introduces OpenLineage-compatible data lineage visualization in preview — AWS; Data Lineage Requirements for AI Systems — EWSolutions; What Is Metadata Lineage? — DataHub.

## Use of S3 Batch Operations to Retrofit Object Lock

- **Decision:** Use S3 Batch Operations to apply Object Lock and retention settings to existing enterprise data at scale.
- **Rationale:** Default bucket-level retention settings only apply to newly uploaded objects; retroactive protection for petabytes of existing data requires an automated batch approach.
- **Source:** Applying Amazon S3 Object Lock at scale for petabytes of existing data | AWS Storage Blog.

## Decoupled Multi-Agent State Machine Architecture

- **Decision:** Automated compliance workflows must be architected as decoupled, multi-agent state machines.
- **Rationale:** This design prevents the non-deterministic output drift associated with monolithic AI agents by ensuring each agent has a single, bounded role with strict input-output schemas.
- **Source:** Architecting an Agentic Compliance and Audit Workflow.

## Immediate Hashing of Evidence at Acquisition

- **Decision:** The Intake Agent must apply cryptographic SHA-256 hashing to every incoming data payload at the millisecond of acquisition.
- **Rationale:** Immediate hashing establishes a verifiable chain of custody and prevents manual post-extraction database edits, mitigating the absence of tamper-evidence.
- **Source:** Architecting an Agentic Compliance and Audit Workflow.

## Purely Deterministic Evaluation Functions for Evidence

- **Decision:** The Evaluator Agent must use purely deterministic evaluation functions operating on structured schemas.
- **Rationale:** This mitigates the risk of using probabilistic confidence scores in place of rationale, providing auditors with an explicit procedural trace for every check.
- **Source:** Architecting an Agentic Compliance and Audit Workflow.

## Use of Workday Reports-as-a-Service (RaaS) for Identity Events

- **Decision:** The automated workflow uses Workday Reports-as-a-Service (RaaS) as the authoritative gateway for identity lifecycle events.
- **Rationale:** Accessing data through RaaS turns custom reports into API endpoints, enabling automated data exports that avoid the manual file manipulation risks present in traditional exports.
- **Source:** Architecting an Agentic Compliance and Audit Workflow; Workday RaaS Explained: Reporting as a Service — A Complete Guide — Go Fig.

## Creation of Dedicated Workday ISU and ISSG for Integrations

- **Decision:** For Workday RaaS integrations, create a dedicated Integration System User (ISU) assigned to an Integration System Security Group (ISSG).
- **Rationale:** Dedicated robot accounts prevent integration failures that occur when personal accounts change passwords or leave the company. Sharing the report only with the authorized ISSG follows least-privilege principles.
- **Source:** Architecting an Agentic Compliance and Audit Workflow; Workday RaaS Explained: Reporting as a Service — A Complete Guide — Go Fig.

## Validation to Exclude Backslash Characters in ISU Usernames

- **Decision:** The system must validate that the Workday ISU username does not contain backslash characters.
- **Rationale:** Backslash characters can disrupt URL parsing in REST-based API proxy networks, leading to GET request authentication failures.
- **Source:** Architecting an Agentic Compliance and Audit Workflow.

## Implementation of Workday RaaS Pseudo-Pagination

- **Decision:** The Intake Agent must implement "pseudo-pagination" using date-entered prompt parameters for Workday RaaS.
- **Rationale:** Workday RaaS does not support pagination by default and enforces a 30-minute timeout and 50,000-row execution boundary; large datasets require chunking to avoid failure.
- **Alternatives Considered:** Workday Query Language (WQL) API was considered as an alternative for very large datasets exceeding the row boundary. Workday Studio was considered but rejected for simple data retrieval as it requires more technical skill than RaaS.
- **Source:** Architecting an Agentic Compliance and Audit Workflow; Workday RaaS Explained: Reporting as a Service — A Complete Guide — Go Fig.

## Use of NetSuite SuiteQL for Read-Only REST Queries

- **Decision:** Automated access checks for NetSuite should use SuiteQL via REST Web Services.
- **Rationale:** SuiteQL allows direct querying of system tables like rolepermissions and employeeRolesForSearch, providing a comprehensive list of users and their specific permissions for verification.
- **Source:** Architecting an Agentic Compliance and Audit Workflow; Find All NetSuite Users With a Specific Permission Using SuiteQL; NetSuite Applications Suite — Using SuiteQL with the Connect Service.

## Inclusion of Required Transient Header in NetSuite REST Queries

- **Decision:** NetSuite SuiteQL queries sent via REST must include the required header parameter `Prefer: transient`.
- **Rationale:** This is a mandatory requirement for executing these specific API use cases.
- **Source:** NetSuite Applications Suite — Use Case for Finding IDs of Roles Assigned to an Employee; NetSuite Applications Suite — Use Case for Retrieving Permissions Assigned to a Role.

## Establishment of a Risk Operations Center (ROC)

- **Decision:** Organizations should consolidate detection, response, compliance, and remediation into a single Risk Operations Center (ROC) platform.
- **Rationale:** Standard security stacks are often fragmented across multiple vendors (SIEM, SOAR, CSPM, GRC), leading to slower incident response times and manual reconciliation glue. An ROC ensures that security is operated continuously, and evidence is emitted as a byproduct.
- **Source:** Defining the Risk Operations Center: The Future of Security Compliance.

## Emission of Compliance Data in OSCAL Format

- **Decision:** Compliance evidence and audit artifacts should be emitted in the Open Security Controls Assessment Language (OSCAL) format.
- **Rationale:** OSCAL is the NIST-developed standard for machine-readable security data, allowing for automated validation and 3PAO-ready reporting.
- **Source:** Architecting an Agentic Compliance and Audit Workflow; Defining the Risk Operations Center: The Future of Security Compliance.

## Implementation of Compliance Controls In-Path for CI/CD

- **Decision:** Compliance controls must be enforced inside the CI/CD pipeline rather than as a separate project.
- **Rationale:** This treats audit readiness as an output of the delivery system, maintaining release velocity and providing a verifiable chain from change to deployment. It replaces manual "audit seasons" with continuous evidence capture.
- **Source:** DevSecOps Compliance: CI/CD Controls, Evidence, and SOC 2 — Cloudaware.

## Separation of Enforcement into Gates and Warnings

- **Decision:** CI/CD enforcement points must be separated into gates and warnings based on impact, confidence, and environment.
- **Rationale:** Blocking every signal kills delivery speed, while warning on everything creates noise that teams eventually ignore. Gates are reserved for high-confidence, high-impact noncompliant outcomes.
- **Source:** DevSecOps Compliance: CI/CD Controls, Evidence, and SOC 2 — Cloudaware.

## Implementation of Time-Boxed, Expiring Exceptions

- **Decision:** Exceptions to compliance controls must be treated as first-class objects that are time-boxed with an expiry date and a defined owner.
- **Rationale:** Permanent exceptions lead to hidden policy and bypass debt; mandatory expiry with revalidation ensures waivers do not outlive the risk they accepted.
- **Source:** DevSecOps Compliance: CI/CD Controls, Evidence, and SOC 2 — Cloudaware.

## Policy-as-Code for Compliance Rules

- **Decision:** Compliance requirements must be implemented as enforceable policy-as-code that is version-controlled and tested like production code.
- **Rationale:** Policy changes are risk changes; treating them as files in Git with PR reviews ensures they are proposed, reviewed, and rolled out safely with full traceability.
- **Source:** DevSecOps Compliance: CI/CD Controls, Evidence, and SOC 2 — Cloudaware.

## Use of S3 Glacier Deep Archive for Compliance Backups

- **Decision:** Use S3 Glacier Deep Archive as the storage class for long-term compliance backups under Object Lock.
- **Rationale:** This minimizes the cost of non-negotiable storage charges for locked objects that must be retained for years to satisfy regulatory requirements.
- **Source:** How to Use Object Lock in Amazon S3 with Compliance Mode for Immutable Backups and WORM Regulatory… | by Rise of Cloud.

## Implementation of Continuous Automated Identity Discovery for Agents

- **Decision:** Organizations must implement continuous, automated discovery of AI agent identities across all deployment surfaces, including cloud IAM, OAuth servers, and CI/CD pipelines.
- **Rationale:** AI agents are often created by developers via platform API calls that bypass traditional HR-driven IGA tools, creating structural blind spots in human-centric governance models.
- **Source:** Identity Lifecycle Management Wasn't Built for AI Agents — The Hacker News.

## Use of Inactivity Monitoring as a Trigger for Agent Offboarding

- **Decision:** Agent offboarding and credential revocation should be triggered by operational status and inactivity monitoring.
- **Rationale:** Unlike humans, agents do not have HR termination dates; an API key that has not generated a request within a defined window is the most reliable signal for deprecation.
- **Source:** Identity Lifecycle Management Wasn't Built for AI Agents — The Hacker News.

## Adoption of Hardware-Enforced MicroVM Isolation for AI Agents

- **Decision:** AI agent execution environments should use microVM-based isolation with hardware-enforced boundaries.
- **Rationale:** Provides strong security boundaries between execution environments, which is critical for agents that generate and execute code at runtime.
- **Source:** SOC 2 Compliance for AI Agents in 2026 | Blaxel Blog.

## Implementation of Perpetual Sandboxes with Scale-to-Zero

- **Decision:** High-context agents should use perpetual sandboxes that enter a standby state rather than purely ephemeral compute.
- **Rationale:** Perpetual sandboxes maintain filesystem and memory state (like conversation history and authentication tokens) while eliminating the "cold-start" penalty that often forces a choice between security scanning and acceptable latency.
- **Alternatives Considered:** Ephemeral sandboxes were considered but can break audit trail continuity and require pay-for-always-on infrastructure to maintain state.
- **Source:** SOC 2 Compliance for AI Agents in 2026 | Blaxel Blog.

## Isolation of Compliance Evidence in Dedicated Accounts

- **Decision:** Compliance evidence must be isolated from production workloads in a dedicated "Security/Audit" AWS account.
- **Rationale:** Limits the blast radius; if production credentials are compromised, an attacker cannot delete the logs and evidence that would reveal their presence.
- **Source:** SOC 2 Evidence Storage Best Practices: A Walkthrough (2026) | Konfirmity.

## Use of Pre-Audit Validation AI Agents

- **Decision:** Implement Evidence Review AI Agents to perform pre-audit validation of uploaded evidence.
- **Rationale:** This acts as a "second line of defense," automatically catching gaps and auditor-flagged concerns before external reviews occur, streamlining SOC 2 Type II readiness.
- **Source:** SOC 2 evidence pre-audit validation — AI Agents — Complyance.

## Use of "Computer-Use" Verification for SOX ITGC

- **Decision:** AI automation for SOX ITGC should use "computer-use" verification to capture application-level evidence.
- **Rationale:** API-only platforms cannot "see" certain application-level controls like specific user permissions in accounting software or restricted delete buttons; AI agents navigate these interfaces to close the "20% manual gap".
- **Source:** The Best AI Tools for Automating SOX ITGC Evidence in 2026 — Screenata.

## Implementation of Weekly/Monthly "Compliance Crons"

- **Decision:** Schedule automated "Compliance Crons" for weekly or monthly evidence collection.
- **Rationale:** Monthly or continuous collection allows organizations to catch "control drift" immediately rather than discovering unauthorized access months later during a quarterly audit.
- **Source:** The Best AI Tools for Automating SOX ITGC Evidence in 2026 — Screenata.

## Automation of Testing Inside Existing Excel Workpapers

- **Decision:** Purpose-built audit AI should execute procedures inside the existing Excel workpaper.
- **Rationale:** Most audit teams continue to use Excel for testing work; running AI inside the workpaper allows for automated matching and recalculation while ensuring every result is directly linked to the source evidence section.
- **Source:** The SOX AI Playbook: Automate Evidence Collection and Controls — DataSnipper.

## Adoption of Delta-Based Access Reviews

- **Decision:** Access reviews must be delta-based, surfacing only the entitlements that have changed since the last cycle.
- **Rationale:** Standard full-list reviews across thousands of entitlements lead to rubber-stamp exercises; delta reviews focus manager attention on risk and new access, reducing review time by up to 70%.
- **Source:** The 5 Best ConductorOne Competitors for Identity Governance in 2026 — Lumos; The Guide to User Access Management for IT and Security Teams — Lumos.

## Use of Column-Level and Feature-Level Lineage Granularity

- **Decision:** Data lineage for AI systems must provide column-level and feature-level granularity.
- **Rationale:** Table-level lineage is insufficient for compliance; column-level tracking is necessary to show exactly which sensitive data element entered a model and traveled downstream to honor privacy requests or prove regulatory boundaries.
- **Alternatives Considered:** Table-level lineage was considered but rejected because it leaves a "warehouse blind spot" where tracking halts at the data warehouse, treating downstream training pipelines as an unmonitored black box.
- **Source:** Data Lineage Requirements for AI Systems — EWSolutions; Data Lineage: Tracking Data From Source to Consumption — Conduktor; Data Lineage — Apache Doris.

## Implementation of Automated Lineage Extraction

- **Decision:** Data lineage capture must be automated through query parsing or instrumentation rather than manual mapping.
- **Rationale:** Manual lineage documentation is obsolete the day it is written and cannot keep pace with environments that change weekly.
- **Source:** Data Lineage Requirements for AI Systems — EWSolutions; Data Lineage: Tracking Data From Source to Consumption — Conduktor.

## Capture and Versioning of Metadata Lineage

- **Decision:** Organizations must capture the lineage of metadata (the history of how tags, ownership, and classifications change).
- **Rationale:** Data lineage only tells where data came from; metadata lineage tells what the organization believed about that data when a decision was made (e.g., certification status at the time of a training run), which is now a requirement for AI auditability.
- **Source:** What Is Metadata Lineage? — DataHub.
