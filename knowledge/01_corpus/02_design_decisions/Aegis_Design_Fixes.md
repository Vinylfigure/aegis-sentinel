# Aegis — Design Fixes (Outstanding Items Closed)

Status: paste-ready edits (July 16, 2026)
Scope: closes the three-item design backlog from `Aegis_RedTeam_Reconciliation.md §4` and the one flagged legal verification. Each fix is anchored to an exact file + section with replacement text ready to drop into the canonical docs. Two edits land in `Aegis_Investigator_Agentic_Architecture.md`, one new decision (D-6) lands in `Aegis_Investigator_Design_Decisions.md`, and the invariant gets a one-line addendum.

---

## 0. Legal verification (closes the flagged item)

The SOX 7-year matrix row rested on `Version_Drift_Ledger.md §6` without independent re-check. Now verified against primary sources, text in effect mid-July 2026:

| Claim | Instrument | Verified value | Primary source |
| --- | --- | --- | --- |
| Workpaper retention (rule) | 17 CFR 210.2-06(a) (Reg S-X, Rule 2-06) | **7 years** after audit/review concluded | law.cornell.edu/cfr/text/17/210.2-06; ecfr.gov (2026-06-01 ed.); SEC adopting release |
| Workpaper retention (statute) | 18 U.S.C. §1520(a)(1) | **5 years** from end of fiscal period | uscode.house.gov (in effect 2026-07-15); law.cornell.edu/uscode/text/18/1520 |
| Destruction penalty | 18 U.S.C. §1520(b) | up to **10 years** imprisonment | thefederalcriminalattorneys.com / statute text |

**Verdict:** `Version_Drift_Ledger §6` is precisely correct — statute sets 5, SEC Rule 2-06 (promulgated under the §1520(a)(2) mandate) extends it to 7, destruction penalty is 10. **Action:** upgrade the `Aegis_RedTeam_Reconciliation.md §1` SOX row grounding from *carried* to **VERIFIED (primary source)** and set WORM retention for SOX-relevant evidence to the **7-year** rule figure. The 366-day testing window is unaffected.

---

## Fix 1 — Independent reconciliation source *(blocking — touches the completeness assertion)*

**File:** `Aegis_Investigator_Agentic_Architecture.md`
**Why:** §3's two-source reconciliation never requires the second source to be independent of the first. Reconciling a source against a derivative of itself proves internal consistency, not completeness, and cannot detect the corpus's own named failure (`Workflow_Theory §Contradicting Info.2`: deterministic-but-incomplete telemetry that omits the inconvenient records). This is the only backlog item that touches Completeness — the assertion the whole substrate exists to defend — so it ships first.

### 1a. Edit §3, the runner step

**Replace:**
> **Deterministic runner executes the frozen spec:** pulls the full population from the declared source, counts, reconciles two-source, hashes, writes WORM. **Completeness asserted here.**

**With:**
> **Deterministic runner executes the frozen spec:** pulls the full population from the declared source, counts, reconciles against an **independent corroborating source** (§4a), hashes, writes WORM. **Completeness asserted here — and only as strongly as the corroborating source is independent.**

### 1b. Insert new subsection §4a (after §4)

> ### 4a. Reconciliation independence — completeness is only as good as the second source
>
> Two-source reconciliation proves completeness *only* if the second source has **different provenance** from the first. A report and the API behind the same system, an export and the log the same service emitted — these reconcile to internal consistency, not to completeness. They cannot catch a source that emits deterministic-but-incomplete telemetry: a run that succeeds, hashes clean, and quietly omits the records that would reveal the control failure (`Workflow_Theory §Contradicting Info.2`).
>
> **Requirement.** Every collection spec must name a corroborating source whose provenance is independent of the authoritative source — a different system that should hold the same population for an independent reason. Reconcile IdP-provisioned accounts against the *target system's own* account list, not a second IdP report; reconcile HR leavers against directory last-activity, not another HR export.
>
> **When no independent corroborator exists,** completeness does not fail silently. It **degrades explicitly** to "complete relative to what {source} chose to emit," and that degradation is written into the workpaper as a stated scope limitation — never hidden behind a clean count. The independent deterministic verifier (`Design_Decisions D-2`) checks that reconciliation ran against a source *flagged independent*, not merely that two numbers matched.

---

## Fix 2 — Positioned for engagement-level validation, not firm tool approval *(new — no prior home in the docs)*

**File:** `Aegis_Investigator_Design_Decisions.md` — add as **D-6**.
**Why:** PCAOB guidance (per the red-team, consistent with AS 1000 / AS 1105) holds that firm-level vendor diligence does **not** satisfy evidence requirements — validation must occur per-engagement, per-objective, with experienced personnel shown to have supervised and challenged results. The docs previously implied architectural *correctness* was the assurance, which is exactly the automation-bias posture PCAOB flags. The fix is positioning, reusing mechanisms already built (§7 re-performance, D-3 OSCAL AR).

### 2a. New decision entry

> ## D-6. Positioned for engagement-level validation, not firm-level tool approval — **ADOPT (positioning)**
>
> - **Decision:** Aegis is documented and built to be **validated per engagement, per audit objective** — not trusted because a firm approved the vendor. Every run emits a re-runnable, versioned, hash-chained record plus OSCAL AR, so an engagement team can independently re-perform and challenge outputs for their specific objectives.
> - **Rationale:** PCAOB guidance holds firm-level tool diligence insufficient for evidence; validation is an engagement-level act. A correct tool is *necessary, not sufficient*. The architecture's §7 re-performance property is precisely what makes engagement-level validation cheap — but only if the framing stops selling correctness as the guarantee.
> - **Correction applied:** The deliverable is not "trust this output." It is "here is a byte-identical re-run and a versioned, seeded-fixture test you can challenge." Re-performability, not correctness, is the assurance offered to the engagement team.
> - **Design note:** No new mechanism — reuses §7 and D-3. It changes the README's reviewer-facing framing and the invariant, nothing in the runtime.

### 2b. Append one sentence to the invariant (§10 Architecture / "Corrected invariant" in Design Decisions)

> Aegis is built to be **re-performed and challenged at the engagement level**, not trusted because a firm approved the tool: correctness is necessary, re-performability is the assurance.

---

## Fix 3 — Bind planning prompts + model provenance into the hashed trail *(COSO 2026)*

**File:** `Aegis_Investigator_Agentic_Architecture.md`
**Why:** COSO 2026 requires that monitoring of AI-driven processes capture prompts and configurations *in* the audit trail, not adjacent to it. §2 hooks currently hash tool calls and §3 freezes the spec, but the **planning prompt** and **model provenance** (already a glossary term: model version, config, params) that *generated* the spec aren't bound into the chain of custody. Small edit, real requirement.

### 3a. Edit §3, the freeze step

**Replace:**
> **The spec is schema-validated, human-ratified at the trust boundary, then frozen and versioned.**

**With:**
> **The spec is schema-validated, human-ratified at the trust boundary, then frozen and versioned — together with the artifacts that produced it.** The freeze bundle binds under one content hash: the frozen spec, the **planning prompt(s)** that generated it, and the **model provenance** (model ID/version, decoding params, tool set, timestamp) of the planning run. Prompts and configurations are captured *inside* the hashed chain of custody, not stored beside it (COSO 2026: prompts and configurations are part of the audit trail itself). A ratified spec whose generating prompt and config are not in the hash is not considered frozen.

### 3b. Append to §2, layer 5 (Hooks)

**After:**
> PreToolUse hooks hard-block: allowlist read-only MCP tools, deny writes outside scratch, deny egress beyond approved endpoints, log every tool call into the hashed trail.

**Add:**
> For agent-planning runs, the hook additionally captures the planning prompt and the model-provenance record into the hashed trail (feeding the §3 freeze bundle), so the generative step that produced a spec is itself reconstructable — closing the COSO 2026 prompt/config-capture requirement.

---

## Apply order & residual

1. **Fix 1 first** — it is the only change to the Completeness assertion; everything else is additive. Until it lands, any "two-source reconciled" claim in the docs overstates what the substrate proves.
2. **Fix 3** next — mechanical, low-risk, closes a named framework requirement.
3. **Fix 2** last — pure positioning; it changes README/invariant language, not runtime, so it can trail the two mechanism edits.

**What these do not close (stated honestly, per the red-team's own discipline):** none of the three touches the UNKNOWN-funnel judgment leak (`Architecture §9`) or tolerance/approver semantics — those remain human-ratified and are correctly *outside* what a design fix can neutralize. Fix 1 hardens completeness; it does not make the agent's UNKNOWN resolutions deterministic. That residual stays surfaced as reviewable exception volume, not engineered away.
