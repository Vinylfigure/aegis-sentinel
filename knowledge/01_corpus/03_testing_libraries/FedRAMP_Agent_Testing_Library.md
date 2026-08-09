# FedRAMP Agent Testing Library — 800-53 Rev 5 Families & 20x KSIs Mapped to Agent Methodology

**Status:** Working artifact (July 16, 2026)
**Scope:** Companion to `SOC2_TSC_Agent_Testing_Library.md`. Maps the FedRAMP control universe (NIST 800-53 Rev 5 baselines + FedRAMP 20x Key Security Indicators) to the Aegis agent methodology using the same schema and tiering. This is a **delta library**: where a FedRAMP control shares an archetype with an already-specced SOC 2 control, it is referenced (`→ SOC2:AM-03`) with only the FedRAMP-specific deltas stated — parameters, cadence, reporting obligations. Full specs appear only for FedRAMP-unique mechanisms.

**Verification caveat:** FedRAMP 20x and the PMO's parameter guidance are actively evolving (per `Constraints.md`, 20x shifts toward automated validation and may reduce 3PAO reliance). Baseline parameter values below (scan cadence, POA&M SLAs, retention) reflect Rev 5 Moderate as commonly implemented; **verify each against the current FedRAMP baseline/KSI publication before freezing predicate constants.** These are exactly the human-ratified constants of architecture §5 — they must enter skill files as versioned fixtures, not agent memory.

---

## 1. Why FedRAMP is the best-fit framework for this methodology

Three structural facts make FedRAMP *more* agent-native than SOC 2:

1. **20x KSIs are machine-validation-first.** The KSI model replaces narrative-and-screenshot assessment with machine-readable true/false validations against the live environment. That is literally the Aegis deterministic substrate: population from authoritative API, pure-function predicate, PASS/FAIL/UNKNOWN. The Aegis run ledger *is* the KSI evidence stream — the design goal should be emitting KSI validations as a native output format.
2. **OSCAL is the required interchange direction.** SSP, SAP, SAR, and POA&M are moving to OSCAL (NIST machine-readable standard, already in your glossary). The frozen collection spec + attribute results serialize naturally into OSCAL assessment-results; build the exporter once.
3. **Continuous monitoring is a standing population, not an annual sample.** Monthly ConMon (scans, inventory, POA&M) means the populations Aegis pulls are *already contractually required deliverables*. The agent isn't creating new evidence obligations — it's mechanizing existing ones.

The countervailing fact: FedRAMP has hard Tier 3 mass that SOC 2 doesn't — the SSP narrative, authorization boundary description, PIA/SORN, contingency plan documents. Those get the generic `governance-anchor` treatment (hash, version, approval, review date) and nothing more.

---

## 2. Org-Defined Parameter (ODP) Registry — the human-ratified constant set

800-53 controls are parameterized ("the organization defines the frequency…"). FedRAMP fixes many parameters; the CSP fixes the rest in the SSP. **Every ODP is a §5 human-ratified constant.** Before any skill file freezes, extract the ODP set from the SSP into a versioned registry; predicates read from the registry, never from inline values. Typical Moderate values to seed the registry (verify per caveat above):

| ODP | Typical Moderate value | Consumed by |
| --- | --- | --- |
| Inactive account disable | 90 days | FR-AC-02 |
| Account review cadence | At least annually (privileged: more frequent per SSP) | FR-AC-02, → SOC2:AM-02 |
| Session lock / timeout | 15 min lock; session termination per SSP | FR-AC-11 |
| Vulnerability scan cadence | Monthly OS/infra, monthly DB, monthly web app | FR-RA-05 |
| POA&M remediation SLAs | High 30 / Moderate 90 / Low 180 days from identification | FR-CA-05 |
| Audit record retention | ≥ 90 days immediately available; ≥ 1 year total | FR-AU-11 |
| Incident reporting | US-CERT/CISA within 1 hour of confirmation | FR-IR-06 |
| CP test cadence | At least annually | FR-CP-04 |
| ConMon deliverable cadence | Monthly (scans, inventory, POA&M) | FR-CM-MON |
| Crypto | FIPS 140-2/140-3 validated modules | FR-SC-13 |

---

## 3. Family-by-Family Map (Rev 5 Moderate)

| Family | Reuse from SOC 2 library | FedRAMP delta | Tier |
| --- | --- | --- | --- |
| **AC — Access Control** | AM-01…AM-09 (full series) | ODP cadences; AC-2 automated disable at 90-day inactivity; AC-6 least privilege review; AC-17 remote access | 1 |
| **AU — Audit & Accountability** | LM-01, LM-04, DP-06 | AU-11 retention parameters; AU-6 review cadence; AU-9 protection (WORM) | 1 |
| **AT — Awareness & Training** | HR-02 | Role-based training (AT-3) adds a role→course matrix join | 1 |
| **CA — Assessment & Authorization** | MA-01, MA-02, TVM-03 | POA&M is a named, PMO-governed artifact with hard SLAs (full spec below); annual 3PAO assessment; ConMon reporting | 1 / 2 |
| **CM — Configuration Management** | CFG-01/02/03, CM-03/04/05/07, ASM-01 | CM-8 integrated inventory as a *monthly deliverable*; CM-6 checklist-based baselines (STIG/CIS); significant change request process (full spec below) | 1 / 2 |
| **CP — Contingency Planning** | BR-01…BR-04, DR-01, CAP-01/02 | CP-4 annual test with defined test types; ISCP document anchor; alternate site/storage attributes | 1 / 2 |
| **IA — Identification & Authentication** | AM-03, AM-07, AM-08 | Phishing-resistant MFA direction (IA-2); PIV/federal identity where applicable; IA-5 authenticator lifecycle | 1 |
| **IR — Incident Response** | IM-01…IM-07 | IR-6 1-hour US-CERT/CISA reporting clock (delta spec below); IR-8 plan anchor | 1 / 2 |
| **MA — Maintenance** | — (new, light) | Maintenance records population; nonlocal maintenance MFA | 1 |
| **MP — Media Protection** | ASM-05, DP-06 | Media sanitization records (NIST 800-88 method attribute) | 2 |
| **PE — Physical & Environmental** | PS-01 | Inherited from IaaS for cloud-native CSPs; CUEC/CRM mapping is the testable artifact | 2 |
| **PL — Planning** | GV-01 | SSP itself: version, approval, annual update anchor | 3 |
| **PS — Personnel Security** | HR-01, HR-03, HR-05 | PS-3 screening per position risk designation; PS-4 termination same-day access actions (tighter SLA than SOC 2) | 1 / 2 |
| **RA — Risk Assessment** | RM-01, TVM-01, TVM-02 | RA-5 monthly authenticated scanning, full spec below | 1 |
| **SA — System & Services Acquisition** | CM-02, CM-06, VRM-01/02 | SA-11 developer security testing (→ CM-05); SA-9 external services with FedRAMP-authorized-services attribute | 1 / 2 |
| **SC — System & Communications Protection** | DP-01, DP-03, DP-04, NS-01 | SC-13 FIPS-validated crypto (delta spec below); SC-7 boundary protection tied to authorization boundary | 1 / 2 |
| **SI — System & Information Integrity** | ASM-03, TVM-02, LM-02, NS-02, PI-01 | SI-2 flaw remediation timelines = POA&M SLAs; SI-4 monitoring coverage vs. boundary | 1 |
| **SR — Supply Chain Risk Management** | VRM-01/02 | SBOM/provenance attributes where required | 2 |

---

## 4. FedRAMP-Unique Full Specs

### FR-RA-05 — Continuous Vulnerability Scanning (RA-5)
**Approach:** Configuration + full population | **Tier 1** | Extends → SOC2:TVM-01/TVM-02

**Control Description:** Authenticated vulnerability scans are performed monthly across operating systems/infrastructure, databases, and web applications for all components within the authorization boundary; findings are tracked in the POA&M within required timelines.

**Test Procedures:** Inspect scanner configurations and scan execution records for each monthly cycle in the period to verify cadence, authenticated coverage, and boundary completeness; reconcile scanned-asset lists against the integrated inventory; verify findings flow to POA&M with correct discovery dates.

**Population Request:**
1. Scan execution records for the period by scan type (OS/infra, DB, web app) with date, scope, authentication status.
2. Scanned-asset list per cycle.
3. Integrated inventory (FR-CM-08) as the completeness reference.
4. Raw findings per cycle with severity and first-detected date.

**Sample Request:** N/A — full-population reconciliation per cycle.

**C&A:** Standard template. C4 is the control's core: scanned assets ↔ inventory ↔ cloud listing, per cycle. An asset in inventory but absent from scans is the fail-silent condition this control exists to catch.

**Testing Attributes:**
- A. Monthly cadence met for all three scan types, every cycle
- B. Scans authenticated (credentialed) where required
- C. Scan scope reconciles to integrated inventory (deltas = exceptions)
- D. Findings carried to POA&M with accurate discovery dates
- E. Scanner signature/plugin currency at execution
- F. Failed/partial scans rerun or dispositioned

---

### FR-CA-05 — POA&M Management (CA-5)
**Approach:** Full population | **Tier 1** | Extends → SOC2:MA-02

**Control Description:** Weaknesses from scans, assessments, and incidents are recorded in the POA&M with scheduled completion dates and remediated within FedRAMP timelines (High 30 / Moderate 90 / Low 180 days); deviations (false positive, risk adjustment, operational requirement) are documented and approved.

**Population Request:**
1. Full POA&M export as of each monthly submission, with item ID, source, severity, discovery date, scheduled/actual completion, status.
2. Population of deviation requests (FP/RA/OR) with approval status.

**Sample Request:** For the (X) selected closed items, provide remediation evidence and closure validation (rescan). For selected deviations, provide the DR artifact and approval.

**Testing Attributes:**
- A. POA&M population complete (reconciles to scan findings + assessment findings + incident-derived items)
- B. Discovery dates accurate (match first-detected in source)
- C. Remediation within SLA by severity, or approved deviation in place
- D. Closure supported by rescan/validation evidence
- E. Scheduled completion dates not silently re-baselined (date-change history tracked)
- F. Monthly submission occurred each cycle

**Agent Methodology:** Attribute E is the audit-failure classic — completion dates pushed monthly with no deviation request. The runner must diff consecutive monthly POA&M snapshots; this requires WORM-archiving each submission, which the substrate does by default. Attribute B is a deterministic join back to FR-RA-05 findings.

---

### FR-CM-08 — Integrated Inventory (CM-8)
**Approach:** Full population | **Tier 1** | Extends → SOC2:ASM-01

**Control Description:** A complete inventory of all components within the authorization boundary is maintained and submitted monthly with the ConMon package.

**Delta attributes over ASM-01:**
- A. Inventory matches the FedRAMP integrated inventory template fields
- B. Monthly submission cadence met
- C. Inventory reconciles to cloud listing *and* to scanned assets (three-way, per cycle)
- D. All components attributable to the authorization boundary; out-of-boundary components absent
- E. Month-over-month deltas explained (adds/removes tie to change records → CM series)

---

### FR-SCR-01 — Significant Change Requests
**Approach:** Sample Based | **Tier 2**

**Control Description:** Changes meeting the FedRAMP significant-change criteria (new services, boundary changes, new interconnections, major architecture shifts) are submitted for AO/PMO review prior to implementation.

**Population Request:**
1. Population of changes during the period (→ CM population), classified for significance.
2. Population of SCR submissions with approval status and dates.

**Sample Request:** For the (X) selected significant changes, provide the SCR, approval, and implementation date demonstrating approval preceded implementation.

**Testing Attributes:**
- A. Change population screened for significance criteria
- B. SCR submitted for each qualifying change
- C. Approval preceded implementation
- D. Post-change assessment/scan performed where required

**Agent Methodology:** Tier 2 because "is this change significant" is a semantic classification — the D-4 gate item. Once classified, timing attributes are pure functions. A practical pattern: agent pre-screens the change population against the criteria list and proposes classifications; human ratifies the screen, runner tests the ratified set.

---

### FR-SC-13 — FIPS-Validated Cryptography (SC-13)
**Approach:** Configuration | **Tier 1** (module inventory) / **Tier 2** (CMVP certificate mapping)

**Control Description:** Cryptographic protection of federal data uses FIPS 140-2/140-3 validated modules.

**Population Request:**
1. Inventory of cryptographic implementations in the boundary (TLS termination points, KMS, disk encryption, libraries) with module identifiers and versions.
2. CMVP certificate references per module.

**Testing Attributes:**
- A. Crypto implementation inventory complete against boundary components
- B. Each implementation maps to an active CMVP certificate
- C. Module operated in FIPS mode where mode-switchable
- D. Non-validated crypto absent or covered by approved deviation

**Agent Methodology:** Attribute B can be mechanized against the NIST CMVP database, but module-to-certificate mapping (exact version/platform match) is where false PASS risk lives — route the mapping through the semantic gate once, then freeze it as a ratified lookup table.

---

### FR-IR-06 — Federal Incident Reporting (IR-6)
**Approach:** Sample Based | **Tier 2** | Extends → SOC2:IM-06

**Delta:** the notification clock is **1 hour to US-CERT/CISA from incident confirmation**. Attributes: A. Reportable incidents identified per federal criteria (semantic gate) B. Report submitted C. Submission within 1 hour of confirmation timestamp D. AO notified per SSP. Attribute C is pure timestamp math once A is ratified — but the "confirmation" timestamp definition (whose clock, which ticket field) is itself a §5 tolerance-semantics ratification.

---

### FR-CP-04 — Contingency Plan Testing (CP-4)
**Approach:** Sample Based | **Tier 2** | Extends → SOC2:DR-01

**Delta attributes:** test type matches the baseline requirement (tabletop vs. functional per SSP commitment); ISCP document anchor current; test results reported to AO where required; lessons learned incorporated into plan revision (version diff evidences it).

---

### FR-KSI-01 — 20x Key Security Indicator Emission *(forward-looking)*
**Approach:** Continuous | **Tier 1 by construction**

**Control Description:** For 20x-track authorizations, KSI validations are produced as machine-readable true/false results with supporting evidence, continuously or per the required cadence.

**Agent Methodology:** This isn't a control Aegis tests — it's the output contract Aegis should target. Each KSI maps to one or more attribute tests already in the library; the deliverable is a KSI→attribute mapping table plus an emitter that serializes attribute results (with record hashes) into the KSI submission format / OSCAL assessment-results. Design decision to log: KSI emission reads only from the WORM store, never from live agent state — the same front-door rule as everything else.

---

## 5. Tier 3 register (governance-anchor only)

SSP narrative and annual update (PL-2), authorization boundary & data-flow diagrams, PIA/privacy artifacts, IRP/ISCP/CMP documents (anchored; their *execution* is tested above), Rules of Behavior, interconnection agreements (ISA/MOU). Anchor fields: document hash, version, approval identity, review date, submission date.

---

## 6. Build Order

**Wave 1 (mechanize the monthly ConMon spine):** FR-CM-08 inventory → FR-RA-05 scanning → FR-CA-05 POA&M. These three are one reconciliation chain and constitute the recurring deliverable; they also produce the highest assessor-visible value immediately.
**Wave 2 (parameter deltas on existing SOC 2 skills):** AC/AU/IA/AT/PS families — same skills, ODP registry values swapped in.
**Wave 3 (semantic-gate hybrids):** FR-SCR-01, FR-SC-13 mapping, FR-IR-06, FR-CP-04, MP/SR attributes.
**Wave 4 (output contract):** OSCAL exporter + KSI emitter over the WORM store.

## Open items
1. Extract the full ODP set from the current SSP into the versioned registry; every value above is provisional until then.
2. Confirm target track (Rev 5 agency ATO vs. 20x) — changes Wave 4 priority and the 3PAO interface.
3. Verify current PMO parameter values (scan cadence, POA&M SLAs, retention) against the live baseline — my values are typical Moderate, stated from memory, not verified.
4. Decide OSCAL model versions to target for the exporter.
