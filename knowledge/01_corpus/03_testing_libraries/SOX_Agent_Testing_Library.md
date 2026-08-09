# SOX Agent Testing Library — ITGCs, IPE/IUC, SOD, and Automated Controls Mapped to Agent Methodology

**Status:** Working artifact (July 16, 2026)
**Scope:** Companion to `SOC2_TSC_Agent_Testing_Library.md` and `FedRAMP_Agent_Testing_Library.md`. Maps the SOX/ICFR testing universe to the Aegis agent methodology. Delta library: shared archetypes reference SOC 2 IDs; full specs only for SOX-unique mechanisms.

**Framing — where the agent boundary sits in SOX:** SOX has no canonical control catalog; ICFR scope is risk-based per issuer (PCAOB AS 2201 top-down approach: entity-level → significant accounts/disclosures → relevant assertions → key controls). The agent-testable surface is precisely defined:

- **In scope for full agent testing (Tier 1/2):** ITGCs over financially relevant systems, IPE/IUC validation, automated application controls, interface/batch controls, SOD analysis, journal-entry population controls.
- **Agent anchors only (Tier 3):** entity-level controls, management review controls (MRCs), disclosure committee, 302/906 certifications, control rationalization judgments, materiality and scoping.
- **Never agent-owned:** materiality thresholds, significant-account scoping, key-control designation, deficiency severity evaluation (deficiency → significant deficiency → material weakness). These are management/auditor judgments — the SOX equivalent of the §5 human-ratified set, and the consequences of leakage are higher here because the assertion is a legal certification, not an attestation opinion.

**Retention constants (from `Constraints.md`, encode as fixtures):** operational logs on SOX-relevant systems ≥ 366 days; audit work papers and relevant electronic communications ≥ 7 years (SOX §802). The Aegis WORM store for SOX engagements must carry the 7-year class — this is a storage-lifecycle design input, not just a tested attribute.

---

## 1. The two structural facts that shape SOX skill files

**1. IPE/IUC validation *is* the C&A template.** SOX auditors independently test every report/extract used as evidence or relied on by a control: source-data completeness, report-logic accuracy, parameter appropriateness. That is exactly `SOC2 §2` (row counts, pagination exhaustion, boundary checks, bidirectional trace, hash-at-intake) with one addition — **report-logic inspection** (the query/filter definition itself is evidence). Aegis's frozen collection spec is the report logic, versioned and human-ratified; the architecture doesn't just *pass* IPE testing, it *mechanizes* it. This is the strongest cross-framework selling point of the platform.

**2. Baselining/benchmarking makes ITGCs load-bearing.** Under the benchmarking strategy for automated application controls, an automated control tested at baseline need not be re-tested each year *provided* ITGCs (especially change management and access) are effective and the control hasn't changed. Consequence: the CM-series and AM-series skills aren't just controls among many — they are the reliance foundation that lets every automated-control test amortize. The agent's change-population monitoring (did the configuration underlying a baselined control change?) is the benchmarking evidence itself.

---

## 2. ITGC Domain Map

| ITGC domain | Reuse from SOC 2 library | SOX delta | Tier |
| --- | --- | --- | --- |
| **Access to programs & data** | AM-01…AM-09, DP-03/04/05 | Scope = financially relevant systems (ERP, HRIS/payroll, treasury, consolidation, key spreadsheets/EUCs); access reviews often quarterly; SOD is a first-class control (full spec below); privileged ERP roles (e.g., NetSuite Administrator) tested 100% | 1 |
| **Program changes** | CM-03/04/05/07, CFG-01/02/03 | Population = changes to financially relevant systems incl. ERP configuration changes (not just code); SoD between developer and migrator; emergency-change ratification | 1 |
| **Program development** | CM-02, CM-05, CM-07 | System implementations/migrations affecting ICFR: data-conversion reconciliation attributes; go-live approval | 1 / 2 |
| **Computer operations** | BR-01…BR-04, LM-01/02, IM-02/04/05, CAP-01 | Batch job scheduling/monitoring and interface controls (full spec below); backup scope = financial data stores | 1 |

**Scoping note (human-ratified):** the in-scope system list is management's ICFR scoping decision. It enters every skill file as the authoritative-population boundary declaration (§4) — the agent never infers which systems are financially relevant.

---

## 3. SOX-Unique Full Specs

### SOX-SOD-01 — Segregation of Duties Analysis (ERP)
**Approach:** Full population | **Tier 1** (conflict detection) / **Tier 2** (ruleset ratification, mitigation adequacy)

**Control Description:** User access within the ERP is assigned to prevent conflicting duties (e.g., create vendor + approve payment; enter JE + post JE; maintain user access + process transactions); identified conflicts are mitigated by compensating controls or removed.

**Test Procedures:** Obtain the full population of ERP users, roles, and permissions; evaluate against the management-approved SOD conflict ruleset; for identified conflicts, inspect mitigation (compensating control or documented acceptance); verify conflict remediation from prior period.

**Population Request:**
1. Full ERP user listing with status and last-login.
2. Role and permission assignments per user (NetSuite: via SuiteQL against role/permission tables).
3. Management-approved SOD conflict matrix (ruleset).
4. Register of accepted conflicts with compensating controls and owners.

**Sample Request:** For the (X) selected conflicted users, provide the compensating-control evidence or removal evidence.

**C&A:** Standard template. C4: ERP active users ↔ IdP ↔ HRIS actives (terminated-with-access is both an AM-06 exception and an SOD-population integrity issue).

**Testing Attributes:**
- A. User/role/permission population complete
- B. Ruleset evaluation covers all users (including NHIs/integration users)
- C. No unmitigated conflicts (each hit maps to accepted-conflict register)
- D. Compensating controls exist and operated for accepted conflicts
- E. Administrator/superuser population restricted and 100%-tested
- F. Prior-period conflicts remediated or re-accepted with approval

**Agent Methodology:** The Lane 1 constraint set from `Constraints.md`/`API_Constraints` applies verbatim to the collector: SuiteQL requires the `Prefer: transient` header (rejected without it), Oracle-style `FETCH FIRST N ROWS ONLY` (not `LIMIT`), TBA with HMAC-SHA256, and the executing role needs Reports → SuiteAnalytics Workbook permission. All fail loud — safe in the agent's self-learning lane. The **ruleset** (which permission pairs conflict) is the human-ratified judgment; conflict *detection* over the ratified ruleset is a pure function. This control is the strongest single demo of the platform for SOX buyers: full-population, zero-sampling, re-runnable.

---

### SOX-IPE-01 — IPE/IUC Validation (Key Report Testing)
**Approach:** Full population of key reports | **Tier 1** mechanics / **Tier 2** logic-appropriateness sign-off

**Control Description:** Reports and system-generated information used in the execution of key controls (IUC) or provided as audit evidence (IPE) are validated for completeness and accuracy, including source data, report logic, and parameters.

**Population Request:**
1. Register of key reports/IPE items with source system, owner, and consuming control.
2. Report definitions (query logic, filters, parameters) per item.
3. Per-instance generation evidence (run date, parameters used, row counts).

**Sample Request:** For the (X) selected report instances, provide the C&A validation performed (or Aegis executes it directly per below).

**Testing Attributes:**
- A. Key report register complete (every key control's inputs mapped)
- B. Report logic version-controlled; changes tie to approved change records (→ CM reliance)
- C. Parameters match the control's requirement (period, entity, status filters)
- D. Completeness validated per standard C&A template (counts, boundaries, pagination)
- E. Accuracy validated (bidirectional trace, hash)
- F. Logic appropriateness ratified by control owner (semantic gate, once per version)

**Agent Methodology:** For reports Aegis itself pulls, D and E are asserted natively by the runner every execution — IPE testing collapses into the substrate. For residual human-run reports (EUC spreadsheets), the agent's role is anchor + reconciliation against an independent pull where an API exists. Attribute B is the benchmarking hinge: an unchanged, version-controlled report logic under effective ITGCs lets the C&A validation amortize across instances.

---

### SOX-JE-01 — Journal Entry Controls
**Approach:** Full population | **Tier 1**

**Control Description:** Manual journal entries require approval by someone other than the preparer prior to posting; posting access is restricted; standard/recurring entries are systematically controlled.

**Population Request:**
1. Full population of journal entries for the period from the ERP with preparer, approver, entry type (manual/auto/recurring), created/approved/posted timestamps, amount, period.
2. Listing of users with JE posting permission.
3. ERP workflow configuration enforcing JE approval.

**Sample Request:** For the (X) selected manual JEs (or 100% via attribute engine), provide approval evidence where workflow evidence is insufficient.

**Testing Attributes:**
- A. JE population complete (reconciles to GL activity / trial balance movement)
- B. Approval workflow configured and enforced for manual entries (config attribute)
- C. Approver ≠ preparer for every manual JE (full population, not sample)
- D. Approval timestamp precedes posting timestamp
- E. Posting access restricted to authorized users (join → SOX-SOD-01)
- F. Entries posted to open periods only; period-close config enforced
- G. High-risk strata flagged for management review (weekend/period-end/round-amount/unusual-account entries — strata definitions human-ratified)

**Agent Methodology:** Full-population attribute testing replaces JE sampling for C/D/F entirely — the classic agentic-audit win. Attribute G doesn't judge entries; it deterministically produces the risk-strata population that management's review control consumes (the agent feeds the MRC, never performs it). Attribute A's reconciliation (JE detail ↔ TB movement) is the completeness assertion auditors care most about — build it as a first-class deterministic test.

---

### SOX-OPS-01 — Batch Job & Interface Monitoring
**Approach:** Full population | **Tier 1**

**Control Description:** Scheduled jobs and interfaces supporting financial processing (subledger→GL posts, payroll files, bank interfaces, consolidation loads) are monitored; failures are alerted, investigated, and resolved; reprocessing is complete.

**Population Request:**
1. Job/interface inventory for financially relevant flows with schedule.
2. Execution log population for the period with status and record counts.
3. Failure/incident tickets with resolution.

**Sample Request:** For the (X) selected failures, provide investigation and resolution/reprocessing evidence including record-count reconciliation.

**Testing Attributes:**
- A. Job/interface inventory complete against data-flow map
- B. Executions complete per schedule (missing runs detected, not just failed runs)
- C. Failures alerted and ticketed
- D. Resolution timely; reprocessing record counts reconcile (in = out + rejects dispositioned)
- E. Interface control totals/hash checks configured where available

**Agent Methodology:** Attribute B is the fail-silent classic — a job that never ran produces no failure record. The runner asserts against the *expected* schedule grid, not the execution log alone.

---

### SOX-AAC-01 — Automated Application Control Baseline & Benchmark
**Approach:** Configuration + baseline test | **Tier 1**

**Control Description:** Automated application controls (three-way match tolerances, credit limits, posting-period locks, approval workflows, system calculations) are configured per management's design; configurations are baselined and changes are governed by change management.

**Population Request:**
1. Register of key automated controls with system, configuration location, and baseline date.
2. Current configuration values per control.
3. Configuration-change audit log for the period, filtered to baselined objects.

**Sample Request:** N/A — configuration assertion plus change-log reconciliation.

**Testing Attributes:**
- A. Automated-control register complete against key-control listing
- B. Current configuration matches ratified baseline values
- C. No changes to baselined configurations during period, **or** every change ties to an approved change record with re-test
- D. ITGC reliance intact (AM + CM series effective for the hosting system)
- E. Baseline re-test performed where C triggered

**Agent Methodology:** This is benchmarking mechanized: attribute C is a continuous diff of config state + audit log against the frozen baseline. When C fires, the skill emits a re-test trigger rather than a verdict. Attribute D is a cross-skill dependency — the first place the skill graph (control → reliance-on-control) becomes explicit in Aegis; represent it in the skill metadata so a CM-series failure automatically degrades AAC reliance to UNKNOWN rather than leaving a stale PASS.

---

### SOX-EUC-01 — End-User Computing / Key Spreadsheet Controls
**Approach:** Sample Based | **Tier 2**

**Control Description:** Key spreadsheets/EUC tools used in financial reporting are inventoried and subject to access restriction, version control, and input/formula integrity checks.

**Testing Attributes:** A. EUC inventory complete B. Access restricted (file-system/SharePoint permissions — API-pullable, Tier 1) C. Version history retained D. Input data ties to validated source (→ SOX-IPE-01) E. Formula/logic changes reviewed.

**Agent Methodology:** B and C are deterministic via M365/Drive APIs. D and E route through the semantic gate. Long-term answer is migrating key EUCs into governed reports where the full IPE machinery applies — track that as a remediation metric, not just a test result.

---

### SOX-ELC anchors — **Tier 3 register**
302/906 certification records, disclosure committee minutes, MRC evidence (management review controls), fraud-program artifacts (→ SOC2:RM-03), whistleblower/hotline program, audit committee reporting. Generic governance-anchor skill: hash, date, approver, cadence count. **Explicitly out:** the agent never evaluates MRC precision/sensitivity — it can deterministically deliver the *inputs* an MRC consumed (per SOX-JE-01 G) and anchor the reviewer's sign-off, nothing more.

---

## 4. Deficiency handling — a hard boundary

Aegis emits FAIL/UNKNOWN attribute results with record hashes. **Severity classification of a failed control (deficiency vs. significant deficiency vs. material weakness) is never emitted by the system.** That evaluation depends on magnitude/likelihood judgments against materiality — management and auditor territory. The skill output vocabulary stops at: attribute result, exception population, exception rate, affected-assertion mapping. Encode this as a hook-level output constraint, not a convention.

---

## 5. Build Order

**Wave 1 — the ERP spine:** SOX-SOD-01 → SOX-JE-01 → SOX-AAC-01. All three ride the same NetSuite collector (SuiteQL constraints already cataloged); together they cover the highest-hour SOX asks and are full-population, sampling-free demos.
**Wave 2 — ITGC deltas:** re-parameterize AM/CM/BR/LM skills for the financially-relevant scope list and quarterly cadences; add developer/migrator SoD attribute to CM-03.
**Wave 3 — evidence machinery:** SOX-IPE-01 (formalize the substrate's native C&A as auditor-consumable IPE documentation), SOX-OPS-01.
**Wave 4 — periphery:** SOX-EUC-01, governance anchors, deficiency-output constraint hook.

## Cross-Framework Rationalization (test once, satisfy three)

The common-control spine — one skill execution, three framework mappings:

| Aegis skill | SOC 2 | FedRAMP | SOX |
| --- | --- | --- | --- |
| AM-03 MFA | CC6.1/6.6 | IA-2 | ITGC access (financially relevant systems) |
| AM-06 Terminations | CC6.2/6.3 | AC-2, PS-4 (same-day delta) | ITGC access |
| AM-02 Access reviews | CC6.2/6.3 | AC-2 (ODP cadence) | ITGC access (quarterly delta) |
| CM-03/05/07 Change series | CC8.1 | CM family, SA-11 | ITGC program changes + AAC reliance |
| ASM-01 Inventory | CC6.1/A1.1 | CM-8 (monthly delta) | Ops scope boundary |
| TVM-01/02 Vuln mgmt | CC7.1 | RA-5 (monthly), CA-5 SLAs | Ops (supporting) |
| LM-01 Logging | CC7.2 | AU family (retention ODPs) | Ops + 366-day retention |
| BR series | A1.2 | CP family | Ops (financial data stores) |
| MA-02 Remediation | CC4.2 | CA-5 POA&M | Deficiency tracking (inputs only) |

Skill metadata should carry all three mappings so one frozen run emits per-framework evidence packages — that's the rationalization payoff, and it's free once the mapping table lives in the skill files.

## Open items
1. Obtain management's ICFR scoping list (in-scope systems) — the boundary declaration for every SOX skill.
2. Ratify the SOD conflict matrix and JE risk-strata definitions (the two big §5 constant sets).
3. Confirm ERP audit-log coverage for configuration changes (SOX-AAC-01 attribute C is only as good as the log's object coverage — a Lane 2 completeness question to resolve per system).
4. Decide the 7-year WORM storage class for SOX engagement artifacts vs. the standard class.
