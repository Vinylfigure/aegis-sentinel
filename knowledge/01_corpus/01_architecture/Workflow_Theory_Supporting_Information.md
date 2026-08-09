# Supporting Information for the Workflow Theory

## 1. Specialized Multi-Agent Architectures for Auditor Reliance

Sources suggest that for an agentic workflow to survive Big Four inspection, it must be architected as a decoupled, multi-agent state machine. This design prevents non-deterministic drift by assigning single, bounded roles to specialized agents:

- **Intake Agent:** Functions as the exclusive gateway, retrieving logs and applying SHA-256 hashing at the millisecond of acquisition to establish a verifiable chain of custody.
- **Mapper Agent:** Cross-maps evidence to multiple frameworks concurrently (e.g., mapping a config dump to SOC 2 CC6.1, FedRAMP AC-2, and SOX ITGC Access Controls).
- **Evaluator Agent:** Performs purely deterministic checks against defined logic rules rather than probabilistic judgments.
- **Scorer Agent:** Recalculates hashes and verifies the integrity of the data lineage to ensure zero-drift during the run.
- **Documenter Agent:** Compiles verified execution history into machine-readable OSCAL (Open Security Controls Assessment Language) packages.

## 2. Deterministic Telemetry Over Generative AI

Regulatory bodies and industry experts emphasize that "deterministic telemetry"—verifiable data collected directly from authoritative sources representing factual system states—is the only acceptable record for audit reliance. Generative AI outputs and probabilistic inferences are explicitly rejected as factual records of system state. Using "English-as-Code" or neurosymbolic AI allows for human-readable reasoning that matches the deterministic logic an auditor expects.

## 3. Enforcing Completeness & Accuracy (C&A)

To satisfy PCAOB AS 1105.10A, the workflow can use OSCAL hash chains to mitigate modification risks. The tool calculates a cryptographic digest (e.g., SHA-512) of the raw evidence and embeds it in the metadata. Auditors can then recalculate the hash of the stored file; a match provides mathematical proof that the evidence has not been modified since capture.

## 4. Closing the "20% Manual Gap"

While APIs can automate many checks, roughly 20% of SOX and SOC 2 evidence (e.g., UI-level user permission screens) typically remains manual. Modern agentic workflows use "computer-use" verification—AI agents that navigate application interfaces to record workflows, highlighting statuses like "Approved" in GitHub or specific roles in NetSuite—to provide timestamped evidence packs for these otherwise opaque controls.

---

# Contradicting Information and Operational Risks

## 1. The Upstream "Semantic Hallucination" Cascade

Research indicates that while deterministic retrieval prevents fabricated identifiers (Factual Hallucination Rate of 0%), the workflow remains highly susceptible to contextual or semantic hallucinations in the initial asset extraction phase. If an LLM incorrectly extracts a generic system identity (e.g., "Windows") instead of a specific version, the downstream pipeline will deterministically retrieve valid but irrelevant data, leading to a "Contextual False Positive Rate" (observed at 8.5% in study).

## 2. Deterministic != Truthful

Industry feedback warns that a system can meet the "deterministic" requirement while producing incomplete or misleading telemetry. For example, a CSP could generate deterministic logs that technically meet the requirement but omit inconvenient evidence that would reveal a control failure.

## 3. Human Judgment Is Non-Negotiable

Big Four auditors and regulators like the PCAOB maintain that AI is an assistant, not a replacement for accountability. AI lacks the ability to determine which controls are "audit-relevant" or to interpret nuanced business contexts. Validation must still occur at the engagement level, where a human auditor applies professional skepticism to AI-generated results.

## 4. Tooling and Agency Readiness Gaps

Despite the FedRAMP mandate for machine-readable OSCAL packages by September 2026, many agencies currently lack the capacity or tooling to ingest this data. Mandating machine-readable submissions before agencies can consume them risks creating a "dual-format maintenance" burden for organizations without providing immediate audit relief.

## 5. Complexity of Deterministic Boundary Mapping

While host-level configuration checks are mature, the source material notes that no current software can reliably pull all possible cloud-native assets, interconnections, and serverless functions into a code-based, deterministically generated boundary diagram that meets the high level of detail required for FedRAMP. Manually created, human-guided abstracted diagrams are often considered more reliable and communicative than raw topological maps.
