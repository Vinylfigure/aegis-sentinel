# Aegis — Design Fix D-8: Second-Model Reconciliation for the Identity-Fuzzy Branch (Dormant — Rate-Gated)

Status: paste-ready edits (July 16, 2026) — **staged, not applied on this pass**
Scope: hardens the one residual D-7 explicitly left open (`Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md §7.1`): correlated blind spots in a single comparison design survive a single frozen linkage model. Adds a **second, independently-designed linkage model** reconciled against the first under a **monotonic-toward-human** rule. **D-8 is dormant by construction** — it does not instantiate on the next pass. It becomes a live decision only when the §5-C identity-fuzzy clerical-review rate crosses a ratified per-control threshold. Lands one new decision (**D-8**) in `Aegis_Investigator_Design_Decisions.md`, a conditional subsection **§4c** + a §5-C sub-diagnostic + a §9 addendum in `Aegis_Investigator_Agentic_Architecture.md`, and one lane placement in `API_Constraints_By_Trust_Consequence.md`.

Verdict: **ADOPT (dormant; activated by the §5-C rate trigger via a human-ratified decision, not applied standing).**

> **Provenance of this doc.** The record-linkage primitives (Fellegi-Sunter, Splink, seedable EM, model serialization) are the same established facts D-7 already verified and cites. Everything about *how D-8 should reconcile two models and when it should exist* is architectural inference on top of the corpus's own logic (§4a independence, §5/D-2 fixture discipline, §7 anti-shortcut fence, D-7 rate-as-verdict), not a verified external standard. Tagged as such throughout.

---

## 0. Three precisions that decide whether D-8 is hardening or theater

Read these before the mechanism. Each is a way the fix silently inverts if built carelessly.

**(a) It is staged because the residual is unmeasured.** Building a second model before the identity-fuzzy volume materializes is speculative hardening against a rate you have not observed — the exact posture `D-3` ("minimal valid AR first") and the whole red-team discipline reject. D-7's frozen single model is the minimal correct floor. D-8 earns its cost only against measured fuzzy volume, so its activation condition *is* a §5-C rate crossing, not a design preference. A standing second model is over-engineering ahead of data.

**(b) A second model buys *methodological* independence, not *provenance* independence — and those are not the same strength.** `§4a` independence is "a different **system** that should hold the same population for an independent reason" — two provenances. Two linkage models score the **same** soft-keyed record pairs; they share one provenance (the records themselves). What D-8 engineers is *design diversity* — disjoint blocking keys, a different comparison family (e.g. Jaro-Winkler vs. token-set), different term-frequency choices, ideally a different linkage family entirely for the second. That diversity catches **model-design-induced error**: the systematic false match/non-match one comparison design produces because of how it weights a feature. It does **not** catch **data-induced ambiguity** — a contractor cohort provisioned with no employee ID, three real people sharing a common name. Both models correctly dump those in clerical-review, and that is not a shared blind spot — it is the honest UNKNOWN the branch exists to surface. **State D-8's reach as "hardens against comparison-design error," never "achieves §4a-grade independence."** Mislabeling it as the latter re-imports the remembering-not-citing failure the corpus exists to prevent.

**(c) D-8 *adds* human volume — that is the real reason to defer.** The disagreement band is work that did not exist before. D-8 trades an **unmeasured, silent** single-model false-match rate for **measured, visible** clerical review. That is a good trade for audit integrity and a bad trade for throughput if the false-match rate was in fact low. The observable trigger (clerical-band rate) is a *proxy* for the unobservable quantity that actually justifies D-8 (the single model's false-match rate inside its Match band): a model uncertain on many records is likely also wrong on some it is falsely confident about. State the proxy relationship honestly; do not claim the clerical rate *measures* false matches.

---

## 1. The reframe: reconcile toward the human, never toward the match

The load-bearing rule, and the one that inverts D-8 if reversed: **disagreement resolves toward the more conservative outcome, never toward Match.** Reconciling by union — *either* model says Match → resolved — loosens the predicate and uses the second model to rescue records the first correctly left for a human. That is `§7`'s "a system learning to hide findings" in a second suit. The only autonomous outcomes are **unanimity**: both models Match (and agree on cluster) → resolve; both No-match → FAIL. Every disagreement routes to a human.

**Reconciliation matrix** (A = model 1 band, B = model 2 band):

| A ↓ / B → | Match | Clerical | No-match |
|---|---|---|---|
| **Match** | Resolve (fuzzy-flagged) ¹ | Clerical | Clerical + log sharp |
| **Clerical** | Clerical | Clerical | Clerical |
| **No-match** | Clerical + log sharp | Clerical | No-basis → FAIL |

¹ **Only if both models assign the same cluster.** Two models can both say "match" and still split the identity across different clusters, so cluster assignment enters the agreement test — not just the pairwise band. Agree-on-Match-but-different-cluster → Clerical.

Two properties of this matrix matter downstream:

- **Only the two diagonal-corner-of-agreement cells are autonomous** (unanimous Match+cluster → Resolve; unanimous No-match → FAIL). Everything else is human. Simple, auditable, re-performable — no special-casing that a re-run could diverge on.
- **The sharp corners (Match↔No-match) are logged separately.** A cluster of sharp disagreements points straight at a feature one comparison design is mishandling — the highest-signal diagnostic the reconciliation produces.

---

## 2. D-8 decision entry (paste into `Aegis_Investigator_Design_Decisions.md`)

> ## D-8. Second-model reconciliation for the identity-fuzzy branch — **ADOPT (dormant; rate-gated activation)**
>
> - **Decision:** When — and only when — a control's identity-fuzzy **clerical-review rate** crosses its ratified per-control threshold (§5-C), a human may ratify standing up a **second, independently-designed linkage model** over the same soft-keyed population. The two frozen models are reconciled by a **monotonic-toward-human** rule: autonomous resolution requires **both** models to return `match` **and** agree on cluster; autonomous FAIL requires both to return `no-match`; **every disagreement routes to clerical review**. The model-disagreement rate — and specifically the sharp-disagreement (match↔no-match) rate — is itself a verdict input.
> - **Rationale:** D-7 `§7.1` closes the identity-fuzzy tie-break substantially but names two live residuals: the clerical-review band, and **correlated blind spots in a single comparison design**. A second model with deliberate design diversity (disjoint blocking, different comparison family, different TF handling, ideally a different linkage family) catches the systematic false match/non-match one design produces. It does **not** catch data-induced ambiguity — both models correctly route that to clerical. So D-8 hardens against *comparison-design error*, not against irreducible ambiguity, and must be scoped as such.
> - **Why dormant, not standing:** the second model *adds* the disagreement band — new human volume traded for a tighter (previously silent) false-match rate. Below a real fuzzy volume that trade is not worth paying; building it early is speculative hardening against an unmeasured residual, the posture `D-3` rejects. The §5-C rate is the activation gate.
> - **Why it cannot self-activate:** the rate crossing **surfaces** the option; a human **ratifies** the build. A system that instantiated a second resolution model in response to its own outcome rates would be adapting its own resolution machinery to its own findings — the exact `§7` poison. Rate-triggered ≠ rate-caused.
> - **Independence honesty (do not overstate):** two models over the same records are **methodologically** independent, not **provenance**-independent in the `§4a` sense (that requires a second *system* holding the same population). D-8 is design-diversity hardening; it is not a `§4a` corroborating source and must never be documented as one.
> - **Conditions:**
>   1. **Reconcile monotonic-toward-human.** Union resolution (either-model-match → resolve) is forbidden — it loosens the predicate and hides findings (`§7`). Only unanimity yields an autonomous conclusion; cluster agreement is part of the Match test (§1 matrix).
>   2. **Design diversity must be *proven*, not asserted** — via cross-seeded failing fixtures (§4): pairs engineered to exploit model 1's known weakness that model 2 must resolve, and vice versa. Both models failing the same fixture = shared blind spot = the reconciliation is theater; the fixture is the proof and is hashed into the freeze bundle beside both `model.json`s and both TF tables.
>   3. **Disagreement rate is a ratified verdict input**, tiered like `D-4`. A high sharp-disagreement rate for a control is an ITGC/data-quality finding (the comparison design is unstable for that population), not a number to average away.
>   4. **Degrade explicitly when no independent design exists.** If the ambiguity is data-induced and no genuinely diverse second design can be built, resolution confidence degrades — per the `§4a` rule — to "resolved relative to the single comparison design," written into the workpaper as a stated scope limitation, never hidden behind a clean fuzzy-resolved flag.
> - **Design note:** No change to plan → freeze → execute. The second model is another frozen §3 spec; the reconciliation matrix is deterministic verdict logic re-checked by the independent verifier (`D-2`); the disagreement rate folds into D-7 Mechanism C. D-8 reuses existing gates rather than adding one.

---

## 3. Activation trigger (paste into `Aegis_Investigator_Agentic_Architecture.md §5-C` — extends D-7 Mechanism C)

> **D-8 activation (dormant until fired).** The identity-fuzzy clerical-review rate is not only a finding input (D-7 Mechanism C) — above a ratified per-control threshold it also **surfaces D-8 as a ratifiable option**: stand up a second, independently-designed linkage model for this control. The threshold is itself ratified judgment (D-4 tier). Crossing it does not instantiate anything; it opens a human decision. Rationale for the gate: the clerical rate is a *proxy* for the single model's unobservable in-band false-match rate (a model uncertain on many records is likely also wrong on some it is falsely confident about), and D-8's disagreement band is net-positive only when that false-match rate is the real concern. Below threshold, the single frozen model (D-7 §4b) stands; the residual stays surfaced as bounded clerical volume, not engineered away.

---

## 4. Reconciliation mechanism (paste into `Aegis_Investigator_Agentic_Architecture.md` — new subsection §4c, after §4b, *conditional on D-8 activation*)

> ### 4c. Second-model reconciliation — active only when D-8 is ratified for this control
>
> When D-8 is active (§5-C trigger, human-ratified), the identity-fuzzy Stage-2 residual (§4b) is scored by **two** frozen linkage models of deliberately diverse design, and their outputs are reconciled deterministically. When D-8 is dormant — the default — §4b's single frozen model stands unchanged and this subsection is inert.
>
> **Design diversity requirement.** The second model must differ from the first in ways that decorrelate design-induced error, not merely reseed the same design: **disjoint blocking keys**, a **different comparison family** (e.g. Jaro-Winkler vs. token-set/Jaccard), **different TF-adjustment choices**, and where feasible a **different linkage family**. Two seeds of one settings object are *not* two models — they share every blind spot. Diversity is proven by cross-seeded fixtures (below), never assumed from configuration alone.
>
> **Reconciliation is monotonic toward the human.** Per candidate resolution, each model returns a band (`match` / `clerical` / `no-match`) and, for `match`, a cluster. The deterministic reconciler applies the §1 matrix: **unanimous `match` with matching cluster → resolve (fuzzy-flagged); unanimous `no-match` → no-basis/FAIL; every other combination → clerical.** Union resolution is prohibited — the second model may only ever *withhold* an autonomous resolution the first would have made, never *manufacture* one. Cluster agreement is part of the match test: agree-on-match / disagree-on-cluster → clerical.
>
> **Disagreement is a first-class output.** The reconciler records, per control: the overall disagreement rate and the **sharp-disagreement rate** (`match`↔`no-match`), both hashed into the run output. These feed §5-C: a high sharp-disagreement rate is an ITGC/data-quality finding on the population, not noise to smooth over. Sharp disagreements clustering on one comparison column localize the mishandled feature.
>
> **Determinism (inherits §4b, one addition).** Both `model.json`s, both TF-table sets, both Splink (or alternative-family) versions, and the **reconciliation-matrix version** are pinned and hashed into the freeze bundle (Fix 3 discipline). Given the same two frozen models and the same input, both scores and the reconciled outcome are byte-identical on re-run — the `D-2` property. The reconciler is pure deterministic code (two bands + two clusters → one outcome); it is **not** an agent, and like the independent verifier it must never be called one.
>
> **Agent role is unchanged and stays above the gate.** At authoring the agent may *draft* the second model's blocking rules and comparison-column design (Lane 1 mechanics — wrong values fail loud). It does **not** decide either model's m/u weights, thresholds, comparison mappings, or the reconciliation rule. Those are frozen, ratified artifacts.

### 4c-note. Substrate placement (append to §2, layer 1, alongside the §4b note)

> When D-8 is active, both linkage models and the reconciliation matrix run here in the deterministic substrate, not the agent loop. Each is a versioned artifact under drift detection; a change to either model, either TF set, or the matrix flows through the same freeze-validate-approve gate as any test-predicate change (`§7`).

---

## 5. Cross-seeded failing fixtures — the proof that "independent" is real (paste into `Aegis_Investigator_Design_Decisions.md` D-8 design note, and enforce in the freeze bundle)

The claim "two independently-designed models" is auditable only if it is *tested*, reusing the seeded-failing-fixture discipline `§5`/`D-2` already demand of every predicate:

> **Cross-seeded fixtures.** Construct record pairs engineered to exploit model 1's known comparison weakness and require model 2 to resolve them correctly — and a symmetric set exploiting model 2's weakness that model 1 must resolve. If **both** models fail the **same** fixture, they share a blind spot and the reconciliation is theater; that outcome is a build-time failure, not a runtime surprise. The passing cross-seeded fixture set is hashed into the freeze bundle beside both `model.json`s and both TF tables. Without it, "two independent models" is a claim that cannot be re-performed — which fails the `D-2` re-performance property the whole branch rests on.

---

## 6. Architecture §9 honest-ceiling addendum (paste into `Aegis_Investigator_Agentic_Architecture.md §9`, extending the D-7 rewrite)

> - **Identity-fuzzy correlated blind spots — hardenable but not eliminable (D-8, dormant).** D-7's single frozen linkage model leaves two residuals: the bounded clerical band, and correlated blind spots in one comparison design. Where a control's fuzzy clerical rate crosses its ratified threshold (§5-C), a human may ratify a **second, independently-designed** model reconciled monotonic-toward-human (§4c): unanimity resolves, disagreement goes to a human, and the disagreement rate is itself a per-control finding. This hardens against **comparison-design-induced** error. It does **not** reach data-induced ambiguity (both models correctly route that to clerical) and does **not** achieve `§4a` provenance independence (two models, one provenance — the records). The clerical band, now the *disagreement* band, is **larger, not zero** — D-8 buys a tighter, previously-silent false-match rate at the cost of measured human review, which is why it stays dormant below a fuzzy volume that justifies the trade. Judgment is relocated once more to versioned, fixture-tested artifacts (two frozen models, the reconciliation matrix, the disagreement thresholds); it is not removed.

---

## 7. API-lane placement (paste into `API_Constraints_By_Trust_Consequence.md`)

The second model's constraints inherit D-7's placements; the reconciliation logic is verdict code, not a collection-spec input:

- **Second model's blocking / cascade rules → Lane 1 (fail-loud mechanics).** A bad blocking rule produces a visible error or an obviously wrong candidate count; the agent may draft/refine under the `§7` fence.
- **Second model's m/u weights, thresholds, comparison design, TF tables → Lane 3 (semantic, mandatory D-4 sign-off before freeze).** A wrong threshold or comparison mapping produces a plausible-but-wrong match — the semantic-trap failure mode. Never agent-owned.
- **Reconciliation matrix + disagreement thresholds → deterministic runner/verifier (D-2 neighborhood), not a collection-spec lane.** Like OSCAL emission and the S3 storage config, this is verdict/substrate logic, parked outside the three-lane collection taxonomy against the layer that owns it. Version it and put it under drift detection (`§6.2`) on the same cadence as the frozen models.

---

## 8. Residual, stated honestly (post-D-8 status)

1. **Comparison-design-induced false matches** — *hardenable when D-8 is active.* Two diverse designs decorrelate design-induced error; unanimity is required to resolve. Residual: the disagreement band is real human work (larger than D-7's clerical band), and diversity is only as good as the cross-seeded fixtures prove it to be.
2. **Data-induced ambiguity** — *unchanged and correct.* No-employee-ID cohorts, genuine name collisions: both models route to clerical. This is the honest UNKNOWN the branch exists to surface, not a gap D-8 closes.
3. **Provenance independence** — *not achieved, by construction.* D-8 is methodological diversity over one provenance. True `§4a`-grade corroboration would require a second *system* holding the same identity population — a different, heavier fix if a control ever needs it.
4. **Throughput cost** — *accepted, gated.* D-8 nets positive only above a fuzzy volume where the silent false-match rate outweighs added clerical review. The §5-C trigger enforces that; dormant is the default.

Net: D-8 upgrades the identity-fuzzy honest-ceiling from *"one frozen model, correlated blind spots surfaced as review volume"* to *"where volume justifies it, two diverse frozen models resolve only on unanimity, disagreement is a human decision and a per-control finding, and the design diversity is fixture-proven and re-performable"* — a stronger claim, backed by a byte-identical re-run, that still does not pretend the fuzzy branch reaches zero human involvement.

---

## Sources

- **Corpus anchors:** `Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md` §4b (frozen linkage), §5 Mechanism C (rate-as-verdict), §7.1 (identity-fuzzy residual: clerical band + correlated blind spots), §8 (API lanes); `Aegis_Investigator_Agentic_Architecture.md` §2/§4a/§5/§6.2/§7/§9; `Aegis_Investigator_Design_Decisions.md` D-2 (independent deterministic verifier), D-4 (semantic sign-off, tiering), D-5 (human-attest lane); `Aegis_Design_Fixes.md` Fix 1/§4a (reconciliation independence, explicit degradation), Fix 3 (freeze-bundle hashing); `Workflow_Theory_Supporting_Information.md` Contradicting Info §1 (contextual false positives), §2 (deterministic ≠ truthful).
- **Record linkage / determinism (carried from D-7's verified set, not re-verified this pass):** Splink (MoJ Analytical Services) — Fellegi-Sunter probabilistic linkage, seedable EM, `model.json` serialization + predict-from-frozen, match/clerical/no-match banding, connected-components clustering; Linacre et al., *Splink*, IJPDS 7(3), 2022. Comparison-family diversity (Jaro-Winkler, token-set/Jaccard) and disjoint-blocking decorrelation are standard record-linkage practice.
- **Inference tag:** the reconciliation matrix, the methodological-vs-provenance independence distinction, the dormant-until-rate-triggered activation model, and the cross-seeded-fixture proof requirement are architectural reasoning on the corpus's own logic — not a verified external standard. Treat as design proposal, ratify before canonical.
