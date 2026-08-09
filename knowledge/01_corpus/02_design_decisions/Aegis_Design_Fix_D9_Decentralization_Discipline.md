# Aegis — Design Fix D-9: Decentralization Discipline (Consensus on Inputs, Determinism on Output)

Status: paste-ready edits (July 16, 2026)
Scope: answers the recurring "should Aegis be more like Chainlink — decentralized validation, multi-agent then deterministic checks?" question by decomposing Chainlink's oracle model into its four separable ideas and routing each to the Aegis layer that can safely absorb it. Three ideas land above or beside the gate (sourcing, planning-tier routing, verification attestation); the fourth — aggregation-as-truth — is rejected at the verdict layer for a structural reason. Lands one new decision (**D-9**) in `Aegis_Investigator_Design_Decisions.md`, extends `Aegis_Design_Fixes.md` Fix 1/§4a (sourcing), `Aegis_Investigator_Design_Decisions.md` D-4 (planning tier) and D-2 (verifier quorum), adds a `§9` honest-ceiling addendum, and one lane note in `API_Constraints_By_Trust_Consequence.md`.

Verdict: **ADOPT the sourcing and verification extensions clean; ADOPT the planning-ensemble tier with conditions (independence must be engineered, never the verdict); REJECT consensus at the verdict layer by construction.**

> **Provenance of this doc.** The Chainlink primitives (DON, two-layer median aggregation, OCR off-chain consensus + quorum-signed attested report, deviation-threshold updates) are **verified this pass** against Chainlink's own architecture docs and FAQ (sources below). Everything about *how those primitives map onto Aegis layers and where the bright line falls* is architectural inference on the corpus's own logic (§4a independence, D-2 verifier, D-4 tiering, §7 re-performance, D-7 rate-as-verdict), not a verified external standard. Tagged `[INFERENCE]` where it matters.

---

## 0. Three precisions that decide whether this is hardening or theater

Read these before the mechanism. Each is a way the fix silently inverts if built carelessly — the same discipline `D-8 §0` applies to second-model reconciliation.

**(a) Chainlink decentralizes because it *cannot recompute*; Aegis *can*.** A Decentralized Oracle Network exists because there is no canonical, re-derivable answer to "the price of ETH" — independent operators observe independent venues and *aggregation is the truth-generation step*. Consensus is what you reach for when deterministic ground truth does not exist. Aegis's verdict layer is the exact inverse: it engineers a deterministic ground truth precisely so an auditor re-runs the pipeline and gets a byte-identical answer (`§7`). **Re-performance strictly dominates consensus** — "an independent party recomputed and derived the identical byte" is a stronger guarantee than "a quorum observed and signed the same value," because Chainlink's nodes can only attest they *observed* alike, while an Aegis verifier proves it *derived* alike. Importing a quorum vote into a layer that already has determinism is a downgrade wearing a decentralization costume. This is the whole reason the fourth idea is rejected while the other three are adopted.

**(b) "Multi-agent" is two unrelated architectures, and the corpus already picked one.** Aegis's Intake/Mapper/Evaluator/Scorer/Documenter pipeline (`Workflow_Theory §1`) is *division of labor* — a bounded-role state machine. Chainlink is *redundant replicas voting for Byzantine fault tolerance*. These solve different problems. Conflating them is exactly how one talks oneself into a voting-based audit verdict. Aegis wants division-of-labor at the pipeline and recompute-redundancy at attestation — **never replica-voting at the gate.** State this explicitly or the analogy re-imports the confidence-score failure mode `D-4` and the invariant exist to forbid.

**(c) Redundant *models/agents* buy methodological independence, not provenance independence — the same distinction `D-8 §0(b)` draws for linkage models.** K planners over one base model, N verifiers over one code path, are not independent in the `§4a` sense (a different *system* that should hold the same population for an independent reason). Redundant reasoners share the base model's blind spots; unanimous agreement among them inflates confidence with *correlated* error, the precise way reconciling a source against a derivative of itself is a lie (`Fix 1`). Independence among reasoners has to be **engineered** (different model families, deliberately disjoint retrieval contexts) — and even engineered it never fully closes, because shared training corpora underspecify the same things. **This is why Mechanism B does not rely on reasoner agreement as its primary signal at all** (see §4): corroboration for a semantic claim is pointed at the *source's own schema* (independent provenance), not at a second planner, and the residual ensemble is calibrated against seeded fixtures rather than trusted. Verifiers are exempt from the whole problem because they *recompute deterministically* rather than reason: N recomputations of the same frozen logic are supposed to be identical, and divergence is a defect, not a vote.

---

## 0a. Coverage principle — 100% population, full period, no sampling (this fix must honor it)

A correction that governs the whole doc, because the first draft of the §3a probe quietly violated it. **Aegis tests the entire population, never a sample of it** — that is the project's core thesis and the reason it beats screenshot-and-sample audit, and it is what the `§7` re-performance property is *for* (an auditor re-runs and gets the identical answer over every record, not a re-drawn sample). The old-audit move this project rejects is *sample + confidence*: run a model over many records, emit a high confidence score, let a human spot-check a few. The corpus already bans that three times — statistical confidence scores are not audit evidence (`Constraints.md` audit-trail schema; `Decision_Ledger.md` human-readable-reasoning-over-confidence; Glossary *Confidence Score*). A sample plus a confidence threshold is the pre-automation world wearing an AI hat; it does not enter Aegis at any layer.

**The human still looks at "a few" — and that is correct — but the few are a different object.** They are the **deterministically-surfaced exception residual**: UNKNOWNs, drift alerts, and the agent-resolved records `§9` flags for auditors to sample *specifically*. Never a statistical sample of the clean population. Same small number of human eyeballs as a sampling audit; opposite epistemology — the human reviews what the deterministic test *couldn't close*, not a random slice of what it did.

**100% and 80–90% are not in tension** (do not blend the denominators, per `Aegis_RedTeam_Reconciliation.md §5`): **100% is what gets tested**; **80–90% is what resolves cleanly without a human**. The population coverage is total; the clean-resolution rate is partial; the gap is the exception residual, surfaced, not sampled away.

**Coverage over time is total too.** Continuous monitoring = the scheduler (`§6`) runs the deterministic pipeline over the **full population on every scheduled run**, catching drift between runs — this is the CCM model (Glossary), 24/7 validation replacing point-in-time snapshots. Testing **between two periods** (a SOC 2 Type II window) = the full population across the **entire period** — every account change, every PR, every access event from period-start to period-end — not a sample of dates within it. This is strictly stronger than both Type I (single point in time) and traditional Type II (a sample over the period), and it is the actual competitive claim: total population, total period.

**Consequence for the §3a probe (applied below):** characterizing a field by a *drawn sample* of its values is the same probabilistic shortcut, one layer down, and is equally forbidden. The probe reads the **declared schema/enum** (deterministic), or characterizes the **entire column** where the domain is only observable in data (deterministic, amortized), or **escalates to a human** where neither is possible — it never samples.

**Lift this into the canonical invariant (paste into `Aegis_Investigator_Agentic_Architecture.md §10`, appended to the invariant):**

> Aegis tests the **full population, never a sample** — across the full monitoring period, on every scheduled run — and surfaces the residual the deterministic test cannot close as reviewable exceptions; it never substitutes a statistical sample plus a confidence score for total deterministic coverage. Human review is spent on the deterministically-surfaced exception residual, not on a sample of the clean population.

---

## 1. The reframe: decentralize the inputs and the checking, keep the decision singular

Chainlink's design has four separable ideas. The error is collapsing them into "consensus, which Aegis doesn't need." Only the third is forbidden, and only at one layer.

| Chainlink idea | Verified mechanism | Aegis home | Gate side |
| --- | --- | --- | --- |
| **Independent sourcing** | Each node sources from multiple data firms and takes the median; no node relies on one source | Fix 1 / §4a reconciliation, pushed from 2-source to **N-source median** (Mechanism A) | Deterministic runner — **below** gate, but non-verdict |
| **Redundant observation** | N nodes observe *independent sources*; a node that relies on one source is the anti-pattern | **Spec-validation probe** confronts the planner's map with the source's own schema (Mechanism B); calibrated ensemble only for the residual | Probe: deterministic, pre-freeze. Ensemble: agent/planning — **above** gate |
| **Aggregation-as-truth** | Median/quorum *produces* the canonical value | **Rejected at the verdict layer** — Aegis recomputes, it does not vote | Verdict — **forbidden** |
| **Cryptographic attestation** | Quorum-signed report validated on-chain | **N-verifier recompute quorum** extending D-2 (Mechanism C) | Independent verifier — **beside** gate |

The one-liner that replaces the earlier "import independence, not consensus": **decentralize the inputs and the checking, keep the decision deterministic — the system Chainlink would build if it could recompute its own price, and can't.**

---

## 2. D-9 decision entry (paste into `Aegis_Investigator_Design_Decisions.md`)

> ## D-9. Decentralization discipline — consensus on inputs, determinism on output — **ADOPT (tiered; verdict-layer consensus rejected by construction)**
>
> - **Decision:** Adopt Chainlink's independent-sourcing and attestation disciplines at the layers that already tolerate or demand them, and reject its aggregation-as-truth model at the verdict layer. Concretely: (1) extend Fix 1 two-source reconciliation to **N-source median reconciliation** where independent-provenance corroborators exist, treating the *disagreement pattern* as a per-cause finding (Mechanism A); (2) validate a drafted spec's semantic mappings against the **source system's own schema/value distribution** with a deterministic pre-freeze probe (Mechanism B), so the dominant hallucination class is adjudicated reasoner-vs-source (independent provenance), not reasoner-vs-reasoner; a **calibrated, monotonic-toward-human ensemble** handles only the un-probeable residual and never sets spec content; (3) extend the D-2 independent verifier to an **N-verifier recompute quorum** under N separate identities, required to produce byte-identical output (Mechanism C). No aggregation of any kind produces a verdict.
> - **Rationale:** Chainlink decentralizes because it cannot recompute a canonical truth; Aegis's verdict layer can, and re-performance strictly dominates consensus (`§0(a)`). The three adopted mechanisms all feed layers already permitted to be non-deterministic (sourcing feeds a completeness assertion the runner still makes; planning feeds a tier a human still acts on; attestation is a recompute, not a judgment). Only the truth-layer vote is forbidden, and it is forbidden because a deterministic recompute is available and stronger.
> - **The bright line (load-bearing, inverts D-9 if crossed):** the moment any "M of N agreed" decides a PASS/FAIL, the confidence score `D-4`/the invariant forbid is rebuilt in quorum costume. **Planner consensus decides routing, never content. Verifier quorum decides attestation, never judgment. The evaluator predicate stays singular-deterministic (or N-identical-recompute, which is the same thing).**
> - **Independence honesty (do not overstate):** redundant *reasoners* (planners) are methodologically independent only if engineered across model families / retrieval contexts; two instances of one base model share blind spots and their agreement is correlated error, not corroboration (`§0(c)`, mirroring `D-8 §0(b)` and `Fix 1`). Verifiers are exempt because they recompute rather than reason. Neither ensemble achieves `§4a` provenance independence, and must never be documented as if it did.
> - **Conditions:**
>   1. **N-source reconciliation stays deterministic per cell.** Each pairwise/N-way count comparison is a count match/mismatch the runner computes; only the *interpretation of the mismatch shape* is new, and it maps to a declared per-cause finding (Mechanism A). Never a median-of-counts that smooths a real gap away.
>   2. **Semantic corroboration comes from the source, not a second reasoner.** The dominant hallucination class (endpoint/field granularity) is adjudicated by the deterministic §3a probe against the source's own schema/value distribution — independent provenance in the `§4a` sense. Judgment semantics stay human-ratified (`§5`). Only the un-probeable residual uses an ensemble, and there agreement lowers the tier **only** through seeded-fixture calibration (a measured discount, not asserted independence), disagreement always raises it (monotonic-toward-human, `D-8 §1`), and a red planner supplies objective diversity where model-family diversity is unavailable. The mandatory human sign-off on anything touching the population definition is never removed (`D-4` non-negotiable).
>   3. **Verifier quorum is recompute-and-match, not sign-and-vote.** N verifiers each recompute the hash chain and count reconciliation under a separate IAM identity in a separate account; the run is valid only if all N produce byte-identical output. Divergence invalidates the run (a defect), it does not trigger a majority rule.
>   4. **All three are cost-gated like `D-8`.** K planners cost K× planning tokens; N verifiers cost N× verification compute. Default N for verifiers is the existing single D-2 verifier plus one; default K for planners is 1 (single planner) until a control's D-4 tier or drift history justifies the ensemble. Speculative fan-out ahead of measured need is the `D-3` posture this corpus rejects.
> - **Design note:** No change to plan → freeze → execute. Mechanism A is more declared sources in the `§4/§4a` sense; Mechanism B is a tier input feeding the existing `D-4` gate; Mechanism C is more of the existing D-2 verifier. D-9 reuses existing gates rather than adding one.

---

## 3. Mechanism A — N-source median reconciliation (sourcing tier)

**File:** `Aegis_Design_Fixes.md` Fix 1 / `Aegis_Investigator_Agentic_Architecture.md §4a`
**Why:** Fix 1 requires *one* independent corroborator. Chainlink's verified discipline is stronger: it medianizes N independent sources *and treats the outlier as signal* — a feed updates only when deviation crosses a threshold, and the median rejects the manipulated venue. Where a population has three-plus independent-provenance sources, Aegis is not doing pair reconciliation, it is doing an **N-source reconciliation matrix** whose disagreement *shape* is diagnostic in exactly the way the `D-7` per-cause UNKNOWN table is. `[INFERENCE — mapping; Chainlink median/deviation mechanism verified]`

### 3a. Append to Fix 1 §4a (after the two-source requirement)

> **N-source extension (where independent-provenance corroborators exist).** When a population is claimed by three or more sources of genuinely independent provenance, reconcile all N, and treat the *pattern* of disagreement — not a median of counts — as the output. Example (CC6 logical access): an IdP provisioning report, the target system's own account list, and CloudTrail access events. The counts are compared deterministically pairwise; the mismatch shape is the finding:
>
> - All N agree → completeness corroborated at N-source strength (state the N).
> - IdP and target-system agree, CloudTrail shows an account neither lists → **shadow access** — a specific CC6 exception, not a count to average away.
> - Target-system and CloudTrail agree, IdP omits the account → provisioning-outside-IdP (a process finding), distinct from the above.
>
> **Never medianize the counts themselves.** Chainlink medianizes because it wants one number and the outlier is noise; Aegis wants the outlier *because it is the finding*. The runner records every source's count and the disagreement topology; the independent verifier (`D-2`) re-checks that reconciliation ran against sources *flagged independent* (`Fix 1` rule), now across all N. Where fewer than two independent-provenance sources exist, completeness degrades explicitly per the existing `§4a` rule — Chainlink's own "not every feed is equally decentralized" honesty applies directly: not every control has N independent sources, and the doc must say which do.

---

## 4. Mechanism B — Deterministic spec-validation against the source, with a calibrated ensemble residual (planning tier — the highest-value application)

**File:** `Aegis_Investigator_Agentic_Architecture.md` (new §3a probe) + `Aegis_Investigator_Design_Decisions.md` D-4
**Why:** The single most-cited weakness in the corpus is the semantic-hallucination cascade — the **8.5% contextual-false-positive rate** (`Workflow_Theory §Contradicting Info.1`), "Windows" instead of "Windows Server 2012 R2," genuine-but-irrelevant evidence. The first draft of this mechanism sought corroboration for that semantic claim from a **second reasoner** (K planners voting). That is the `§4a` trap one layer up: two planners over one base model are a *source reconciled against its own derivative*, so their agreement is correlated error reported as corroboration. Model-family diversity narrows but never closes the correlation (shared training corpora underspecify the same things), and "engineer diversity or discount" is a punt, not a fix. **The fix: point corroboration at the source, not at another planner** — the independent-provenance referent for a semantic claim is the *source system's own schema and value distribution*, which is checkable deterministically. This is Mechanism A's discipline (independent-provenance corroboration for a **count**) applied one layer up to a **meaning**. `[INFERENCE — mapping; the §4a-independence principle it invokes is corpus-native]`

### 4a. The reframe — decompose the semantic-error surface (the D-7 move, applied to hallucination)

"Semantic error" is an undifferentiated bucket, and undifferentiated buckets are where the correlated-reasoner trap hides. Decompose by *what kind of thing is mismapped*; each class wants a different adjudicator, and only the smallest residual is a reasoner-consensus problem at all.

| Semantic-error class | What it is | Adjudicator | Reasoner-consensus role |
| --- | --- | --- | --- |
| **Endpoint/field granularity** | The proposed field is valid but lacks the specificity the criterion needs ("Windows" field vs. the OS-version field that returns "Windows Server 2012 R2"). **This is what the 8.5% example actually is.** | **Deterministic source-schema/value probe** (§4c below) — reasoner-vs-source, independent provenance | **None at the adjudication step** (drafts the candidate mapping only) |
| **Judgment semantics** | Approver definition, tolerance semantics, "authorized," "high-privilege" — no field carries the answer; it is a management designation | **Human ratification** (`§5`, the `D-4` non-negotiable floor) — unchanged | None — never was an ensemble's to resolve |
| **Residual un-probeable mapping** | A semantic claim with no schema referent and no declared judgment owner (rare, and itself a finding) | **Calibrated ensemble, monotonic-toward-human** (§4d) | Routing only, discounted by measured factor |

The dominant volume — the granularity class that produces the contextual false positives — moves entirely off reasoner consensus and onto a deterministic confrontation with the source. Judgment semantics were always human. Only the un-probeable remainder is where an ensemble signal survives at all, and there it is calibrated, not trusted.

### 4b. Why the probe is the clean fix (and not just a better vote)

The probe escapes the `§4a` trap because it is not reasoner-vs-reasoner: it confronts the planner's proposed mapping with the source's **declared schema and full value domain** — a referent of genuinely different provenance from the reasoner that produced the claim, exactly what `§4a` demands. The planner proposes "attribute *OS version* lives in field `F`"; the probe reads `F`'s declared schema/enum (and, where the domain is only observable in data, characterizes the *entire* column — never a sample) and asks a deterministic question: **does `F`'s domain actually carry the granularity the criterion requires?** A field whose declared domain is only `Windows` with no version tokens is deterministically insufficient for an OS-version criterion *regardless of how many planners, of how many families, agreed on it*. That is the whole point — it makes agreement irrelevant where a fact is available. (No sampling: characterizing a field by a drawn sample is the probabilistic shortcut this project rejects at the population layer, and it is no more acceptable at the schema layer — see §0a.)

### 4c. Insert new subsection §3a (deterministic spec-validation probe, before freeze)

> ### 3a. Spec-validation probe — confront the plan with the source before freezing it
>
> Before a drafted collection spec (§3) is frozen, each attribute→endpoint/field mapping it claims is validated by a **deterministic, read-only probe** against the declared source, using the §2 second tool class (read-only source lookups that re-enter through deterministic intake — hash, store). The probe is design-time tooling for the human ratifier, not evidence and not a verdict; it produces a per-attribute **specificity report**, hashed into the freeze bundle beside the spec (Fix 3 discipline).
>
> **What it checks (the granularity class, deterministically — no sampling).** For each mapped field, read the **declared schema/enum** — the authoritative value domain — and evaluate whether that domain carries the attribute granularity the criterion names. Three cases, all deterministic:
> - *Declared enum / typed domain* → pure deterministic read. Domain includes the required distinction → **PASS specificity**; it doesn't → **FAIL specificity**. Examples: an OS-version criterion mapped to a field whose declared domain is `{Windows, Linux}` with no version tokens → FAIL; a "privileged role" criterion mapped to a field whose enum is the full role list with no privileged flag → FAIL; a domain that does carry the distinction → PASS (survives to human ratification with the probe evidence attached).
> - *Domain observable only in data* (unconstrained but structured) → the probe characterizes the **entire column** — every distinct value, hashed — never a drawn sample. A full scan run once per control-per-system is amortized (§3) and deterministic; a sample is neither and is forbidden (§0a).
> - *Free-text / no declared or enumerable domain* → the probe cannot deterministically guarantee granularity, so the mapping is a **specificity-UNKNOWN that escalates to human ratification** — never a probabilistic guess that the field "probably" carries the attribute.
>
> **Where it re-enters the gate:** the probe read is a source lookup, so its output re-enters through deterministic intake exactly as §2 requires; nothing the probe retrieves reaches a verdict. It informs *ratification of the plan*, not the population or the pass/fail. A spec whose mappings fail the specificity probe cannot be frozen until re-planned or explicitly ratified as a known limitation.
>
> **What it does not check (stated honestly):** the probe adjudicates only mappings with a schema/value referent. Judgment semantics (approver, tolerance) have no such referent and stay human-ratified (`§5`). This is the same reach limit as `D-8 §0(b)`: it hardens the *field-granularity* class, not irreducible judgment — and that is exactly the class the 8.5% cascade lives in.

### 4d. Append to D-4 (residual ensemble — calibrated, monotonic, adversarial)

> **Residual ensemble signal — only where no probe referent exists, and only ever toward the human.** For the small remainder of semantic claims that the §3a probe cannot adjudicate (no schema/value referent) and that are not declared judgment semantics, an ensemble of planners may still inform the review tier — under three hard conditions that convert it from a trust signal into a bounded, earned one:
>
> - **Monotonic toward the human (the `D-8 §1` rule, applied to planning).** Planner **disagreement** may only ever *raise* the tier / escalate to mandatory human semantic review — this direction is always valid, correlated or not, because if even correlated reasoners disagree the mapping is genuinely ambiguous. Planner **agreement** may *lower* the tier only through the calibration gate below. Union-style "any planner's confident map wins" is forbidden for the same reason `D-8` forbids union reconciliation: it loosens the predicate and uses agreement to rescue a map a human should have seen.
> - **Agreement is calibrated, not trusted (the seeded-fixture discipline, `D-8 §5`).** The tier-lowering weight of ensemble agreement is set by its measured performance on **seeded specificity fixtures** — planning cases where the correct specific mapping is known (the "must resolve to Windows Server 2012 R2, not Windows" class). If the ensemble agrees-and-is-wrong on the fixtures, its agreement is calibrated to a **measured discount factor** (down to zero tier-credit), hashed into the freeze bundle. This replaces "relabel as single-model stability and discount by hand-wave" with a number you can re-perform. No fixture calibration → agreement earns no tier credit.
> - **Adversarial diversity where model-family diversity is unavailable.** At least one ensemble member runs as a **red planner**: its objective is not to produce the best map but to *find the more specific defensible reading and argue the generic mapping is wrong*. This decorrelates against the precise failure mode (over-generalization) through **objective** diversity rather than model diversity, so it works even on a single base model. A red planner that cannot find a more specific reading is (weak) evidence for the candidate; one that can is an escalation. The red-planner protocol is a ratified authoring artifact (Lane 3), versioned like any predicate.
>
> **Bright line (unchanged):** every branch of this modulates *what a human reviews and in what order* — never spec content, never a verdict. The mandatory human sign-off on anything touching the population definition remains non-negotiable (`D-4`). Agreement lowers the tier; it never lowers the gate. The probe (§3a) does the heavy lifting deterministically; the ensemble is a calibrated, monotonic residual for what the probe cannot reach — not the primary signal it was in the first draft.

---

## 5. Mechanism C — N-verifier recompute quorum (verification tier)

**File:** `Aegis_Investigator_Design_Decisions.md` D-2
**Why:** The D-2 independent deterministic verifier under a separate identity is *already* Chainlink-shaped — a second node that independently attests to the run. The correct way to "add decentralization" here is **more of them**, and to be precise about why it stays deterministic: verifiers *recompute and must match*, they do not *vote*. `[INFERENCE — mapping; D-2 mechanism is corpus-native]`

### 5a. Append to D-2 (design note)

> **N-verifier recompute quorum (optional hardening, cost-gated).** The single independent verifier may be extended to **N verifiers, each under a separate IAM identity in a separate account**, each recomputing the hash chain, count reconciliation, and lineage trace. The run is valid **only if all N produce byte-identical output**; any divergence invalidates the run and flags a compliance exception. This raises the Byzantine tolerance of the *attestation* — an attacker must now compromise every write-path simultaneously — with **zero** added non-determinism, because the verifiers recompute rather than observe.
>
> **Why this is strictly stronger than a Chainlink signing quorum:** Chainlink's quorum can only attest that its nodes *observed* the same value; a recompute-and-match quorum proves the nodes *derived* the identical value from the frozen inputs. Re-performance dominates consensus (`D-9 §0(a)`), so the right move is to **decentralize the re-performance, not replace it with a vote**. A verifier quorum is not an "M of N agreed" rule — it is an "all N recomputed identically" invariant; the distinction is the whole point, and calling it a vote (or calling any verifier an "agent") re-imports the confusion the architecture exists to prevent (`D-2` naming correction).

---

## 6. The bright line — no aggregation ever produces a verdict

The steelman dies the instant it crosses this line, so state it as an invariant, not a guideline:

- **Sourcing (Mechanism A):** N-source *disagreement shape* feeds a completeness assertion the runner still makes deterministically. Never a median-of-counts.
- **Planning (Mechanism B):** a deterministic *source-schema probe* adjudicates the dominant hallucination class before freeze; the calibrated ensemble residual feeds a review tier a human still acts on. Never spec content, never a verdict.
- **Verification (Mechanism C):** N-verifier *recompute* feeds an attestation that is still a byte-identical match. Never a majority rule.
- **Verdict:** the evaluator predicate stays singular and deterministic — or N-identical-recompute, which is the same thing. **The moment "3 of 5 evaluators said PASS" decides anything, D-9 has failed and rebuilt the confidence score in a quorum costume.**

Every adopted tier feeds a layer that was already allowed to be non-deterministic. That is precisely why Chainlink's architecture cannot be copied wholesale: it puts consensus at the truth layer because it has *no deterministic truth layer to protect*. Aegis does.

---

## 7. Architecture §9 honest-ceiling addendum (paste into `Aegis_Investigator_Agentic_Architecture.md §9`)

> - **Decentralization is imported at the inputs and the checking, never at the verdict (D-9).** Chainlink's oracle model — independent sourcing, redundant observation, quorum attestation — maps onto Aegis's sourcing (N-source median reconciliation, `Fix 1/§4a`), planning-tier validation (a deterministic probe confronting the planner's semantic map with the source's own schema, `§3a`, plus a calibrated ensemble residual feeding `D-4`), and attestation (N-verifier recompute quorum, `D-2`). Its fourth idea, aggregation-as-truth, is rejected at the verdict layer because Aegis can recompute a canonical answer and re-performance strictly dominates consensus. **Residual, stated honestly:** the semantic probe hardens the field-granularity class only — the class the 8.5% cascade actually lives in — and does nothing for judgment semantics (approver, tolerance), which stay human-ratified (`§5`), nor for the rare un-probeable mapping, where a *calibrated* ensemble (measured against seeded fixtures, monotonic-toward-human) is a bounded routing aid, not a trusted signal. Pointing corroboration at the source rather than a second reasoner closes the correlated-agreement trap `Fix 1`/`D-8 §0(b)` name — where a schema referent exists; where none does, the residual is surfaced as review volume, not resolved. The N-verifier quorum hardens attestation but not judgment; a wrong-but-deterministic predicate is recomputed identically by all N (that is a `D-4`/human problem, not something more verifiers catch). Decentralization raises the cost of tampering and mis-collection; it does not touch the UNKNOWN-funnel or tolerance/approver semantics, which stay human-ratified.

---

## 8. API-lane placement (paste into `API_Constraints_By_Trust_Consequence.md`)

- **N-source reconciliation → Lane 2 (fail-silent completeness traps).** It is a completeness mechanism owned by the deterministic runner + independent verifier; the disagreement-shape interpretation is a declared per-cause finding, never agent-owned. Sits alongside the existing count-reconciliation assertions.
- **Spec-validation probe (§3a) → Lane 3 adjudicated deterministically.** The probe *targets* the Lane 3 semantic-trap class (field-granularity mismaps) but resolves the probeable part of it with a deterministic source read rather than human judgment — it is the one Lane 3 mechanism that produces a machine-checkable specificity PASS/FAIL. The probe read itself is a §2 source lookup that re-enters through intake; the specificity predicates are ratified (seeded fixtures), not agent-owned.
- **Residual ensemble (composition, red-planner protocol, fixture-calibrated discount) → Lane 3 (semantic, mandatory D-4 sign-off).** Only for mappings the probe cannot reach. The ensemble *composition and calibration* are ratified judgment; the tier modulation it feeds is verdict-adjacent routing, not collection-spec content. Agreement earns tier credit only via the hashed calibration fixtures.
- **Verifier quorum (identities, accounts, recompute-match rule) → deterministic runner/verifier neighborhood (D-2), not a collection-spec lane.** Like OSCAL emission and the S3 storage config, this is substrate/attestation logic parked outside the three-lane collection taxonomy. Version it and put it under drift detection (`§6.2`).

---

## Apply order & residual

1. **Mechanism C (verifier quorum) first** — lowest risk, pure additive hardening of an existing deterministic component, no independence-engineering problem to solve (recompute-match is self-proving).
2. **Mechanism A (N-source reconciliation)** next — extends Fix 1, which is already the completeness-load-bearing edit; only applies where independent-provenance sources actually exist, degrades explicitly where they don't.
3. **Mechanism B** last, and in two stages: the **§3a source-schema probe** is the load-bearing part — build it first (it is deterministic and needs no ensemble), because it is what actually attacks the 8.5% cascade. The **calibrated ensemble residual** is optional and only earns its cost where a control has un-probeable semantic mappings *and* a seeded-fixture calibration exists; below that it is a single planner plus the probe, exactly as `D-8` stays dormant until its rate trigger fires.

**What this does not close (per the corpus's own discipline):** none of the three touches the verdict layer, the UNKNOWN-funnel judgment leak (`§9`, addressed by `D-7`), or tolerance/approver semantics (human-ratified). Mechanism B's probe hardens only the *field-granularity* semantic class (where a schema referent exists); judgment semantics and un-probeable mappings stay human-ratified, and the ensemble residual is a calibrated routing aid, never a trusted signal — the correlated-agreement trap is escaped by pointing corroboration at the source, not by trusting reasoners more. Mechanism C hardens attestation, not judgment: N verifiers recompute a wrong-but-deterministic predicate identically. Decentralization here raises tampering and mis-collection cost; it buys nothing at the layer where audit is a judgment profession.

---

## Sources

- **Chainlink primitives (verified this pass, July 16 2026):** Decentralized Data Model — each feed updated by multiple independent oracle operators, on-chain aggregation (Chainlink Docs, `architecture-overview/architecture-decentralized-model`). Off-Chain Reporting — nodes aggregate observations off-chain over P2P, lightweight consensus, single quorum-signed attested report validated on-chain (Chainlink Docs, `architecture-overview/off-chain-reporting`; Chainlink 2.0 whitepaper characterization via Cube Exchange). **Two-layer median aggregation** — node level (each node takes the median across multiple data firms, mitigating outliers/one-source reliance) and network level (median across nodes, so no single node controls the result) (Chainlink FAQs). Deviation-threshold updates — a new round transmits only when the median deviates from the on-chain value by the predefined threshold (Coinmonks / Oracle Labs OCR node logs). "Not every feed is equally decentralized" honesty (Cube Exchange, quoting Chainlink's own warning).
- **Aegis corpus anchors:** `Aegis_Investigator_Agentic_Architecture.md` §2/§3/§4/§4a/§6.2/§7/§9; `Aegis_Investigator_Design_Decisions.md` D-2 (independent deterministic verifier, not an agent), D-4 (semantic sign-off, tiering); `Aegis_Design_Fixes.md` Fix 1/§4a (reconciliation-independence, explicit degradation), Fix 3 (freeze-bundle hashing); `Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md` §5 Mechanism C (rate-as-verdict, per-cause findings); `Aegis_Design_Fix_D8_Model_Reconciliation.md` §0(b) (methodological-vs-provenance independence), §1 (monotonic-toward-human); `Workflow_Theory_Supporting_Information.md` §1 (five-agent division of labor), §Contradicting Info.1 (8.5% contextual false-positive rate), §Contradicting Info.2 (deterministic ≠ truthful); `API_Constraints_By_Trust_Consequence.md` Lanes 1–3.
- **Inference tag:** the mapping of Chainlink's four ideas onto Aegis layers, the "decentralize inputs and checking, keep the decision singular" reframe, the N-source disagreement-shape-as-finding extension, the **§3a source-schema spec-validation probe** and the semantic-error-class decomposition it rests on, the calibrated/monotonic/red-planner residual ensemble, and the recompute-quorum-dominates-signing-quorum argument are architectural reasoning on the corpus's own logic — not a verified external standard. The probe reuses the §2 second tool class (read-only source lookups re-entering through intake), a corpus-native mechanism. Treat as design proposal, ratify before canonical.
