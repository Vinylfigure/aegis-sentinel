# Aegis Corpus — Reading Map

The corpus at `~/PycharmProjects/aegis-corpus/` is the **ratified authoring record** for the Aegis / Sentinel system: 23 documents exported verbatim from the claude.ai "Compliance agents" project on 2026-07-25 and hash-manifested (`MANIFEST.md` / `MANIFEST.sha256` carry a SHA-256 per file). It is the source of truth for architecture, design decisions, verified API facts, and testing procedure. The corpus's own discipline (see `02_design_decisions/Aegis_RedTeam_Reconciliation.md` §2) is that claims must be **cited to a corpus path, never remembered** — the one regression the red-team round produced was a matrix that quietly re-imported memory as citation. Apply the same rule in code reviews on this repo: a claim like "GitHub returns 404 for 403" or "SOX retention is 7 years" must cite the corpus doc that establishes it, and any fact about an external API should be checked against `02_design_decisions/Version_Drift_Ledger.md` before it is relied on, because the corpus records several facts that changed underneath it.

All paths below are relative to the corpus root.

---

## 01_architecture/ — the invariant and its rationale

### 01_architecture/Aegis_Investigator_Agentic_Architecture.md
The canonical architecture document. Establishes the two-verb split (the agent *plans*, deterministic code *executes and verifies*), the five layers (deterministic substrate owning C&A, MCP server on the evidence store, agent loop for retrieval/investigation only, Skills as the audit-procedure library, hooks as guardrails), and the plan → freeze → execute pattern in which the agent's output is a structured collection spec that is schema-validated, human-ratified, frozen, and versioned. Defines the human-ratified judgment set (§5: authoritative population source, tolerance semantics, valid-approver definition, pass/fail predicate), the self-learning fence (§7: mechanics may be learned; the verdict layer never learns), the Janus build-plane-only fence (§8), and the honest agentic ceiling (§9: claim 80–90% clean deterministic coverage, not autonomy). Ends with the canonical invariant (§10).
**Read when:** any question about where the agent/deterministic boundary sits, or before writing anything that touches a verdict.

### 01_architecture/Aegis_Investigator_Design_Decisions.md
The D-1 through D-5 decision record. D-1 adopts hash chains for chain-of-custody (with ordering-key and genesis-anchor requirements); D-2 adopts an independent verifier with the correction that it is an **independent deterministic verifier, never an "agent"**, running under a separate identity; D-3 adopts OSCAL Assessment Results emission with the "minimal valid AR first" scope fence; D-4 adopts the human semantic-review gate at the trust boundary, tiered by control impact and honest that it closes only the design-time semantic gap; D-5 **rejects** computer-use/UI capture from the verdict path and redirects it to the investigation/human-attest lane. Ends with the corrected invariant.
**Read when:** implementing the verifier, the OSCAL exporter, the ratification gate, or anything tempted to put UI capture in the evidence path.

### 01_architecture/Workflow_Theory_Supporting_Information.md
The research substrate behind the design, in two halves. Supporting: the five-role multi-agent division of labor (Intake/Mapper/Evaluator/Scorer/Documenter), deterministic telemetry as the only audit-reliable record, hash-based C&A under PCAOB AS 1105.10A, and the "20% manual gap" computer-use idea (later constrained by D-5). Contradicting: the semantic-hallucination cascade with the observed **8.5% contextual false-positive rate**, "deterministic ≠ truthful" (a source can emit deterministic-but-incomplete telemetry), human judgment as non-negotiable, OSCAL agency-readiness gaps, and the infeasibility of fully deterministic FedRAMP boundary diagrams.
**Read when:** you need the cited evidence and figures behind a design rationale (especially the 8.5% figure and the deterministic-≠-truthful warning).

### 01_architecture/Glossary.rtf
A–Z domain glossary grounding the corpus's terms of art: ISU/ISSG, IPE/IUC, WORM, OSCAL, S3 Compliance vs Governance Mode, Confidence Score (rejected as audit evidence), pseudo-pagination, RaaS, SuiteQL, `BUILTIN.DF()`, model provenance, CCM, hash chain, content-addressable pointer, NHI, POA&M, 3PAO/C3PAO, and the EU AI Act article set.
**Read when:** an unfamiliar acronym or term appears in any other corpus doc.

---

## 02_design_decisions/ — decisions, fixes, and the self-checking fact base

### 02_design_decisions/API_Constraints_By_Trust_Consequence.md
The three-lane constraint taxonomy that governs collector design: Lane 1 fail-loud mechanics (agent may learn — Workday timeouts, NetSuite headers, GitHub token limits, AWS throttling), Lane 2 fail-silent completeness traps (deterministic runner + verifier must own — no server-side filtering, pseudo-pagination drops, offset paging over mutating tables, Doris lineage gaps), Lane 3 semantic traps (mandatory D-4 human sign-off — `BUILTIN.DF()` labels vs IDs, the `UserStatus` enum). The rule of thumb: a wrong value that produces a visible error may be agent-owned; a wrong value that produces a plausible answer must be runner- or human-owned. Also bakes in three corrections to its own catalog (S3 Object Lock retrofit, `UserStatus` two-value enum, GitHub fine-grained read-only) and parks OSCAL/S3-config/token-posture items outside the collection taxonomy.
**Read when:** writing or triaging any collector constraint — every ported audit gets lane-sorted against this doc before it is written.

### 02_design_decisions/Aegis_Design_Fixes.md
Closes the red-team backlog. Fix 1 (blocking): two-source reconciliation must use an **independent-provenance** corroborating source, else completeness degrades explicitly to "complete relative to what {source} chose to emit" (new §4a). D-6: Aegis is positioned for engagement-level validation, not firm tool approval — re-performability, not correctness, is the assurance. Fix 3: the freeze bundle must bind the planning prompt and model provenance under one content hash (COSO 2026). Also carries the primary-source legal verification of the SOX retention stack: SEC Rule 2-06 (17 CFR 210.2-06) = 7 years; 18 U.S.C. §1520(a)(1) = 5 years; destruction penalty up to 10 years.
**Read when:** touching completeness reconciliation, the freeze bundle's contents, or citing SOX retention figures.

### 02_design_decisions/Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md
Closes the UNKNOWN-funnel judgment leak. Decomposes UNKNOWN by join-failure cause: **basis-missing** (deterministic join against declared exception-source registries), **identity-fuzzy** (frozen Fellegi-Sunter/Splink linkage model with four determinism pins: seed, frozen `model.json`, frozen TF tables, pinned version), **no-basis-anywhere** (deterministic FAIL). The agent exits the runtime resolution path entirely; only a bounded clerical-review band reaches a human. Per-cause UNKNOWN rates become verdict inputs (high no-basis = CC6.2 exception; high identity-fuzzy = ITGC/data-quality finding).
**Read when:** designing UNKNOWN handling, triage cause families, or any identity-join logic.

### 02_design_decisions/Aegis_Design_Fix_D8_Model_Reconciliation.md
A deliberately **dormant, rate-gated** hardening: when a control's identity-fuzzy clerical-review rate crosses a ratified threshold, a human may ratify a second, independently-designed linkage model reconciled **monotonic-toward-human** (only unanimity resolves; every disagreement goes to a human; union resolution is forbidden). Establishes the methodological-vs-provenance independence distinction (two models over one record set are not §4a-independent), the cross-seeded-fixture proof that design diversity is real, and the rule that the system cannot self-activate D-8 (rate-triggered ≠ rate-caused).
**Read when:** the fuzzy clerical rate crosses threshold, or anyone proposes adding a second model/reviewer "for safety."

### 02_design_decisions/Aegis_Design_Fix_D9_Decentralization_Discipline.md
Answers "should this be more like the DON protocol?" by splitting the oracle model into four ideas and rejecting exactly one: aggregation-as-truth at the verdict layer (re-performance strictly dominates consensus; Aegis can recompute, the DON protocol cannot). Adopts N-source reconciliation where independent-provenance sources exist (disagreement *shape* is the finding — never medianize counts), the deterministic §3a spec-validation probe that confronts a planner's field mapping with the source's own schema (attacking the 8.5% cascade), and the N-verifier recompute quorum (all N must be byte-identical; divergence is a defect, not a vote). Also §0a: the **100%-population, full-period, no-sampling** coverage principle, and the 100% vs 80–90% denominator distinction.
**Read when:** tempted by multi-agent voting, ensembles, or sampling anywhere — and for the canonical statement that exactly one deterministic function decides each verdict.

### 02_design_decisions/Aegis_RedTeam_Reconciliation.md
The reconciliation pass that confirmed the plan/freeze/execute split and produced three outputs: a corpus-grounded regulatory matrix (retention, immutability, attribution, integrity-proof rows, each traced to a named corpus doc), a **quarantine** of plausible-but-uncited rows (AML/BSA, NARA, SEC 17a-4(f), ISO 42001, the GDPR-vs-Compliance-Mode conflict) with the re-entry rule that external claims must arrive tagged `[EXTERNAL]` with a real source, a README pre-emption list (four "vulnerabilities" the corpus already answers — cite, don't redesign), and the 60/40-vs-80–90% denominator warning.
**Read when:** citing any regulatory number, or answering a critique that the corpus may already have answered.

### 02_design_decisions/Constraints.md
The raw extracted requirement/constraint/assumption set: WORM three-property storage, hash chains, content-addressable pointers, write-path separation, the 12-field audit-trail schema, human-readable reasoning over confidence scores, retention standards (SOX 366d/7y, HIPAA 6y, EU AI Act 6mo, PCI DSS 12mo), agent identity discovery and inactivity-triggered offboarding, lineage granularity, CI/CD gates-vs-warnings and expiring exceptions, microVM isolation, plus Workday/NetSuite/Doris technical constraints and a stated-conflicts table. **Caution:** its S3 "Object Lock only at bucket creation" claim is stale — corrected in `Version_Drift_Ledger.md` §1.
**Read when:** you need the base requirement set — always cross-check any moving fact against the Version Drift Ledger.

### 02_design_decisions/Contradictions.md
The five tracked source contradictions, each with a which-source-wins flag: AWS Identity Store `UserStatus` (old limitation vs new field — the three-value enum stated here is itself corrected by the drift ledger), PCAOB AS 1105.10A strict reading vs the Sept 2025 "remote possibility" policy statement, FedRAMP 3PAO role shift under 20x, SOX 366-day vs 7-year retention (both true, different obligations), and GitHub OAuth scopes vs the read-only gap (stale for fine-grained tokens).
**Read when:** a source disagreement surfaces, or before propagating any of these five claims.

### 02_design_decisions/Control_Evidence_API_Chain_Verified.md
The six-domain control→evidence→API spine (provisioning, termination/deprovisioning, key management, backup, change management, monitoring), pressure-tested July 2026 with per-claim tags (VERIFIED / CORRECTED / UNVERIFIED / CARRIED). Key results: AWS Identity Store `UserStatus`/`CreatedAt` added 2025-11-06 (collectors need a Nov-2025+ SDK); the Domain-2 computer-use claim violates D-5 and is corrected; GitHub read-only via fine-grained PAT/App is the right posture; Lula vs Lula2 naming trap; DataZone lineage constraints (300 KB event cap, column-lineage flag, SageMaker absorption); and the FedRAMP "within one month" tolerance **did not verify** — do not encode it. Each domain also lists its human-judgment gaps (the §5 set).
**Read when:** authoring a Skill or collector for any of the six evidence domains.

### 02_design_decisions/Decision_Ledger.md
Roughly forty ratified operational decisions with rationale, alternatives, and sources: S3 Object Lock Compliance Mode, content hashes and hash chains, content-addressable storage for prompts, write-path separation, scoped auditor read roles, the 12-field schema, human-identity attribution over service accounts, human-readable reasoning over confidence scores, 366-day SOX floor, Workday RaaS/ISU/ISSG/pseudo-pagination, NetSuite SuiteQL and `Prefer: transient`, gates-vs-warnings, time-boxed exceptions, policy-as-code, Glacier Deep Archive, agent identity discovery, microVM isolation, perpetual sandboxes, dedicated audit accounts, delta-based access reviews, and lineage decisions. Note: the Workday/NetSuite rows describe **future-scope systems** for Sentinel (which is GitHub-first), and the "computer-use for SOX ITGC" entry was later corrected by D-5.
**Read when:** checking whether an operational choice was already made before re-deciding it.

### 02_design_decisions/Version_Drift_Ledger.md
The self-checking fact base: eight contested facts re-verified against primary sources (July 2026) with dated verdicts — S3 Object Lock retrofit (stale claim dropped; possible since Nov 20, 2023), `UserStatus` enum (`ENABLED|DISABLED` only, no `UNKNOWN`), FedRAMP RFC-0024 boundary-diagram softening, OSCAL mandated-but-zero-adoption, GitHub read-only via fine-grained tokens/Apps, SOX 366d-vs-7y (Rule 2-06 vs §1520), the PCAOB Rel. 2025-004 "remote possibility" carve-out (the single strongest regulatory hook for the architecture), and the FedRAMP 20x 3PAO shift. The headline: the correction itself carried drift — three precision errors were found inside the fix. Ends with the re-verification cadence method note.
**Read when:** about to rely on, or ship, any external API or regulatory fact — this doc decides which version is current.

---

## 03_testing_libraries/ — the control universe and test procedures

### 03_testing_libraries/SOC2_Control_Testing_Matrix.md
The 22 controls transcribed from the auditor's workpaper spreadsheet: control descriptions, verbatim SOC 2 test-procedure language, population and sample requests, the AM-01 C&A attributes, and draft testing attributes (AM, ASM, BR, CAP, CFG, DP, ELC, IM, CM, TVM series). Includes the structural schema every control follows (population → C&A → sample → lettered attributes → reviewer notes) and known data-quality issues: the BR-03/BR-04 attribute row shift, `[RED]` proposed edits, and partial ELC-03/TVM-01 transcriptions.
**Read when:** implementing any of the 22 original controls or needing exact auditor-facing procedure language (AM-05 is the JIT module's spec).

### 03_testing_libraries/SOC2_TSC_Agent_Testing_Library.md
Extends the matrix to the full SOC 2 TSC universe. Establishes the three agent-testability tiers (Tier 1 pure-function testable, Tier 2 hybrid via the D-4 gate, Tier 3 governance-anchor only), the standard C&A template every population pull inherits (C1 count match, C2 pagination exhaustion, C3 period boundary, C4 independent two-source reconciliation; A1/A2 bidirectional trace, A3 hash-at-intake/WORM), the TSC coverage map, per-control Agent Methodology blocks, and the build order — including the five attribute archetypes that cover ~80% of the library as shared skill primitives.
**Read when:** building any SOC 2 skill file, assigning a tier, or wiring the C&A template.

### 03_testing_libraries/FedRAMP_Agent_Testing_Library.md
Delta library on the SOC 2 base: why FedRAMP is the most agent-native framework (machine-validated 20x KSIs, OSCAL direction, monthly ConMon populations), the Org-Defined Parameter registry (every ODP is a §5 human-ratified constant; the seeded Moderate values are provisional and stated from memory — verify before freezing), the Rev 5 family map, and full specs for FedRAMP-unique mechanisms (FR-RA-05 scanning, FR-CA-05 POA&M with the silently-rebaselined-dates trap, FR-CM-08 inventory, FR-SCR-01, FR-SC-13 FIPS, FR-IR-06 1-hour reporting, FR-CP-04, FR-KSI-01 emission).
**Read when:** anything FedRAMP-scoped, or when designing the OSCAL/KSI output contract.

### 03_testing_libraries/SOX_Agent_Testing_Library.md
Delta library for SOX/ICFR: where the agent boundary sits (ITGCs/IPE/SOD/JE fully testable; materiality, scoping, key-control designation, and **deficiency severity classification never agent-owned** — encode as a hook-level output constraint), the two structural facts (IPE/IUC validation *is* the C&A template mechanized; benchmarking makes AM/CM ITGCs the reliance foundation), full specs (SOX-SOD-01, SOX-IPE-01, SOX-JE-01, SOX-OPS-01 with the missing-run fail-silent classic, SOX-AAC-01, SOX-EUC-01), and the cross-framework rationalization table (one skill run → SOC 2 + FedRAMP + SOX evidence).
**Read when:** anything SOX-scoped, the deficiency-output constraint, or cross-framework skill metadata.

---

## 04_build_prds/ — what Sentinel actually builds

### 04_build_prds/Sentinel_Build_Execution_PRD.md
The v2 execution plan. Withdraws v1's authorship-based trust split (provenance is not independence — the D-8 lesson) and protects the verdict path mechanically: CODEOWNERS over `src/verdict.py`, `src/evidence.py`, `src/db.py`, `src/probe.py`, `src/completeness.py`, `src/controls/**`, `src/jit/preconditions.py`, `src/oscal/**`; fixture tests as required status checks; the Troublemaker seed→assert→restore harness (never deployed, never cut); and the baseline-ratification hash check. Sets build planes (Replit Agent builds, Claude Code reviews/tests, Janus as measured side experiment), repo topology including the fixtures **org** (org-level audits need an org), Replit provisions (Postgres, two deployments, secrets), the day-by-day schedule, cut line, and open questions (including the fine-grained PAT `created_at` unknown).
**Read when:** any question about the build process, repo layout, gates, or what is in/out of scope for the demo.

### 04_build_prds/Sentinel_JIT_UI_DB_Janus.md
Specifies the remaining open design. The JIT module is AM-05/AM-04 mechanized (GitHub Issue Forms as the request artifact — there is no injectable "popup"; Slack-button approval with deterministic preconditions; 5-minute revoker cron restoring `prior_permission`; monitor reconciliation so the tool audits its own privilege granting). One-page FastAPI+HTMX UI (the ledger and OSCAL export are the artifacts; the UI is a window). Postgres over Replit KV/object storage, with append-only enforced by grant and stated precisely as tamper-evidence, not immutability. Janus section defines the learnings-genome discipline this repo's `LEARNINGS.md` implements: inner loop (port + fixture), middle loop (evidence-gated promotion), outer loop (scheduled recalibration against live API behaviour).
**Read when:** JIT, UI, database, or Janus/genome work — this doc is the genome's charter.

### 04_build_prds/Sentinel_v0.2_Event_Driven_Agentic_OSCAL.md
The event-driven build spec. Webhook receiver with HMAC-SHA256 verification over raw body bytes (constant-time compare; ledger the rejections), immediate 200-ack with async processing, the event-type set, `X-GitHub-Delivery` GUID dedup, and — "the part that matters" — delivery completeness: hourly reconciliation via the org-hook deliveries endpoint (with redelivery) plus full state re-verification, recording every evaluation as `event` or `reconciliation` mode. Adds the four advisory agent roles (Investigator, Triage, Scope discovery, Remediation — all `advisory`, never `result`, ten-tool-call cap) and the OSCAL AR export rules: evidence `href` to ledger record hash, UNKNOWN → `not-satisfied` + `unknown-cause` (never `satisfied`), advisory records excluded with a test enforcing it. Part B: org-level hook registration, warm deployment, and the org-administration-read token requirement.
**Read when:** implementing or reviewing webhooks, event evaluation, completeness reconciliation, the agent layer, or the OSCAL exporter.

---

## 05_prior_art/ — external material, quarantined

### 05_prior_art/Aegis_Prior_Art_GRCEngClub_Toolkit.md
Verified review (live clone, 2026-07-24) of GRC Engineering Club's `claude-grc-engineering` marketplace and `scf-api`. Adopt: the Finding schema v1.0.0 conventions (const-pinned semver, closed objects, if/then conditional requirements) plus the Aegis deltas that turn it into the verdict-record schema (record_hash, chain_prev, population fields, spec_hash, test_function_version, ratification_ref); the ajv contract-test CI harness with fixture triads; the SCF crosswalk consumed as a frozen, hashed, WORM-intaken artifact (CC BY-ND — attribute, never modify); the connector exit-code bar (with exit 4 "partial" flagged as their fail-silent trap → hard UNKNOWN in Aegis); and the fedramp-20x update hook as the Janus recalibrate implementation. Reject wholesale: their trust model (mutable cache, no hashing/WORM/freeze), persona-skill LLM judgment inside audit conclusions, sampling language, and `--fix-failures` auto-remediation. Pin everything adopted by commit hash, not branch.
**Read when:** forking their schema or CI harness, touching the SCF crosswalk, or evaluating any external GRC tooling for adoption.
