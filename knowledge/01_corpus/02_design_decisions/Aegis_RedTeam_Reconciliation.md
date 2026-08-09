# Aegis — Red-Team Reconciliation

Status: reconciliation pass (July 16, 2026)
Scope: triage of the red-team analysis (pasted doc 9) and the consolidated regulatory matrix (pasted doc 8) against the five Aegis corpus docs — `Constraints.md`, `Decision_Ledger.md`, `Workflow_Theory_Supporting_Information.md`, `Aegis_Investigator_Agentic_Architecture.md`, `Aegis_Investigator_Design_Decisions.md`, plus `Version_Drift_Ledger.md` and `Contradictions.md`.

The plan → freeze → execute split survived the red-team. No structural flaw was found in "LLM plans, deterministic code renders every verdict." What the round produced is three things: a **README pre-emption list** (claims the corpus already answers — cite, don't redesign), a **three-item design backlog** (real gaps the architecture doesn't fully close), and a **matrix cleanup** — because the pasted matrix quietly re-imported the remembering-not-citing failure mode the corpus exists to prevent.

**Headline for this pass:** the artifact we were most eager to cite (the consolidated matrix) is the one that regressed. Four of its retention rows are grounded in `Constraints.md`; the rest — AML/BSA, NARA, SEC 17a-4(f), ISO 42001, and the GDPR-vs-Compliance-Mode conflict alert — appear **nowhere** in the corpus, and its Source Attribution column is empty. Those rows are plausible and some are real-world true, but that is memory, not a corpus citation. They are quarantined below, not deleted, so they can re-enter as *external* citations if and only if someone actually pulls them.

---

## 1. Regulatory matrix — corpus-grounded rows only

Every row here traces to a named corpus doc. This is the version safe to cite.

### Retention

| Framework | Minimum standard | Grounding |
| --- | --- | --- |
| SOX | 366 days (operational logs, = one full audit cycle); 7 years (audit work papers) | `Constraints.md` (Data Retention Standards); `Decision_Ledger.md` (366-day operational floor) |
| HIPAA | 6 years from creation or last effective date | `Constraints.md` |
| EU AI Act (Art. 12) | 6 months (high-risk system logs) | `Constraints.md` |
| PCI DSS v4.0 | 12 months total, 3 months immediately available | `Constraints.md` |

**SOX refinement (from `Version_Drift_Ledger.md` #6, do not lose this precision):** the 366-day and 7-year figures are *different obligations confused for one*. 366 days is an operating-effectiveness **testing window** (a practitioner convention, not a statutory minimum). The 7-year figure is the legal records-retention mandate — sourced precisely to the **SEC's Rule 2-06, 17 CFR 210.2-06**, adopted under SOX §802. The bare criminal statute **18 U.S.C. §1520(a)(1) says 5 years**; the SEC rule extends it to 7. Attributing "7 years" directly to the §802 statutory text is imprecise.
**Aegis implication:** set WORM retention to the **7-year** obligation for SOX-relevant evidence. Treat 366 days *only* as the window over which operating-effectiveness tests run. A bucket that expires at 366 days passes a testing-window sample but violates the 7-year rule.

### Immutability

| Framework | Requirement | Grounding |
| --- | --- | --- |
| S3 Compliance Mode | Irreversible; objects cannot be deleted or overwritten by any user, including the AWS root account, for the retention period | `Constraints.md`; `Decision_Ledger.md` (Object Lock Compliance Mode decision) |
| EU AI Act (Art. 12) | Reconstruction requirement assumes storage-layer immutability | `Constraints.md` (Explicit Assumptions) |

**Stale-hedge warning (from `Version_Drift_Ledger.md` #1):** do **not** carry the "Object Lock only at bucket creation" claim into any new doc. Since **Nov 20, 2023**, Object Lock can be enabled on an *existing* bucket (versioning required), and existing objects are locked in bulk via S3 Batch Operations. The corpus's own "cannot be retrofitted" language is stale.

### Attribution

| Framework | Requirement | Grounding |
| --- | --- | --- |
| HIPAA | Unique user identification; service-account logging is insufficient | `Decision_Ledger.md` (Authenticated Human Identity Over Service Accounts) |
| GDPR | Accountability principle; decisions tied to an identifiable person | `Decision_Ledger.md` |
| SOX | Individual attribution to an authenticated human, not an API key | `Decision_Ledger.md`; `Constraints.md` |

### Integrity proof

| Framework | Requirement | Grounding |
| --- | --- | --- |
| PCAOB AS 1105.10A | Evaluate reliability of external electronic information; cryptographic hash chains mitigate modification risk | `Workflow_Theory_Supporting_Information.md` §3; `Constraints.md` |

**The load-bearing hook (from `Version_Drift_Ledger.md` #7):** PCAOB **Rel. 2025-004 (Sept 18, 2025)** says that where the auditor concludes there is *no more than a remote possibility* the information was modified in a way rendering it unreliable, the absence of separate .10A(b) testing is **not** treated as noncompliance. SHA-256-at-intake + WORM + hash-chain provenance is engineered to establish exactly that "remote possibility" standard. This is the single strongest regulatory argument the architecture has — the storage-layer contract *is* the carve-out condition. Lead the reviewer-facing story with it.

---

## 2. Quarantine — NOT in the corpus (do not cite as corpus)

These rows and claims come from the pasted analysis (doc 8/9), not from any Aegis source doc. They may be true; they are not *ours* until pulled and tagged as external citations. Kept here so they aren't silently laundered into a corpus artifact.

- **Retention:** AML/BSA 5 years; NARA (federal IT records) 3–7 years. Neither appears in `Constraints.md` or anywhere in the corpus.
- **Immutability:** SEC 17a-4(f) WORM (optical/digital). Not in the corpus.
- **Integrity proof:** ISO 42001 tamper-resistance / chain-of-custody. Not in the corpus.
- **Conflict alert — GDPR "Right to be Forgotten" vs S3 Compliance Mode.** A genuinely sharp tension (Compliance Mode blocks deletion until retention expires, so an erasure request may be technically unfulfillable under a multi-year lock). **But `Contradictions.md` never states it** — it is not one of the corpus's tracked contradictions. Real catch, external provenance. If it goes into a design doc it enters as new analysis, not as a corpus citation.

**Rule for re-entry:** any quarantined row that earns a place in the matrix must arrive with a real external source, tagged `[EXTERNAL]`, never as an unmarked corpus row.

---

## 3. README pre-emption list — already answered by the corpus

These four red-team "vulnerabilities" are already handled in the design docs. The move is **citation, not redesign** — pre-empt each in the README next to the doc that answers it.

1. **Upstream semantic-hallucination cascade / 8.5% contextual false-positive rate** ("Windows" vs "Windows Server 2012 R2" — genuine-but-irrelevant evidence). This is precisely the failure mode **D-4** names, and D-4 is already honest that the Semantic Review gate "closes the design-time semantic gap" and does nothing for runtime drift or the UNKNOWN funnel. The 8.5% figure (`Workflow_Theory` Contradicting Info §1) is the citation that *justifies the gate's existence* — cite it, don't treat it as a hole.

2. **Adjudication of risk — break-glass vs unauthorized access.** Verbatim `Aegis_Investigator_Agentic_Architecture.md` §9: "break-glass provisioning approved out-of-band; policy-exempt service account… each is an UNKNOWN or FAIL for a human." Already the honest ceiling.

3. **Anti-shortcut mandate — "reproduce the outputs," "supervised and challenged the results."** This is the re-performance invariant in §7 (auditor re-runs the pipeline, gets a byte-identical answer; every test change is versioned/dated/reviewed). PCAOB's requirement and Aegis's core discipline are the same requirement.

4. **Automation bias / reduced professional skepticism.** Directly *mitigated* by §9's rule that agent-resolved records carry a flag into the workpaper so auditors sample *them specifically*. This is a selling point, not a vulnerability — frame it as one.

---

## 4. Design backlog — genuine gaps, in priority order

Three things the architecture does not fully close. These are design changes, not README lines.

1. **Independent reconciliation source (deterministic ≠ truthful).** *Highest priority.* The completeness assertion in §3 rests on the declared authoritative source plus two-source reconciliation, but nothing requires the second source to be *independent in provenance* from the first. The corpus's own warning (`Workflow_Theory`, Contradicting Info §2) is the CSP-emits-deterministic-but-incomplete-telemetry attack: reconciling a source against a derivative of itself proves nothing. **Fix:** the reconciliation step must name a corroborating source of *different provenance*, or the completeness claim honestly degrades to "complete relative to what the source chose to emit." Belongs in `Aegis_Investigator_Agentic_Architecture.md` §3 and §4.

2. **Engagement-level validation ≠ firm tool approval.** *New — not in any doc.* PCAOB's point that vendor diligence doesn't satisfy evidence requirements (validation must occur per-engagement, per-objective) actually cuts *for* Aegis: OSCAL AR emission + a re-runnable pipeline is exactly what lets an engagement team validate outputs themselves rather than trust the tool. But the docs currently imply the architecture's *correctness* is the guarantee, and PCAOB says correct-tool is necessary-not-sufficient. **Fix:** add a positioning line — Aegis is built *to be validated per-engagement*, not to be trusted because it was approved.

3. **COSO 2026 prompt/config capture.** The requirement is that prompts and configurations live *in* the audit trail, not adjacent to it. Aegis hashes tool calls (§2 hooks) and versions the frozen spec, but the **planning-phase prompts** and the **model provenance** (version, params — already defined in the glossary as *Model Provenance*) that produced the spec don't appear to be bound into the hashed trail. **Fix (small, real):** hash the planning prompt + model config alongside the frozen spec so the thing that generated the plan is itself in the chain of custody.

---

## 5. Precision correction — do not blend 60/40 with 80–90%

The README must not merge doc 9's "automated tools find ~60% of issues, 40% they never will" with §9's "80–90%." **Different denominators:**

- **80–90%** = coverage of a *control population under clean mechanical test* (`Aegis_Investigator_Agentic_Architecture.md` §9).
- **60/40** = *issue-discovery rate in architectural review* (pasted doc 9).

Blending them invites an auditor to read the 80–90% as a *detection* claim, which it is not. Keep them as separate metrics with their denominators stated.

---

## 6. Net effect on the goal

The red-team confirmed the plan/execute split rather than breaking it. Concrete outputs of this pass:

- **Cite, don't redesign:** four pre-empted claims (§3 above), each mapped to the corpus doc that already answers it.
- **Build:** three backlog items (§4) — independent reconciliation source, engagement-level positioning, prompt/config hashing.
- **Clean:** a corpus-grounded matrix (§1) with the four external row-clusters quarantined (§2), reversing the one regression this round introduced.

**Highest-leverage next step is not more red-teaming** — it is verifying every prospective matrix row against a real source before it becomes a citation, because §2 is exactly where the pasted analysis slipped back into remembering. The corpus-grounded matrix above is that verified core; the quarantine is the honest holding pen for everything that still needs a source.
