# Aegis Investigator — Agentic Evidence Workflow Architecture

Status: working design capture
Scope: the agentic layer that sits on top of Aegis's deterministic collectors. Captures the planning/execution split, the trust boundary, agent roles, the self-learning fence, and the honest ceiling.

---

## 1. The core principle

Two verbs, split cleanly and permanently:

- **The agent *plans*.** Non-deterministic reasoning is allowed here because nothing at this layer is evidence.
- **Deterministic code *executes and verifies*.** Completeness and accuracy (C&A) are asserted here and nowhere else.

The boundary between them is non-negotiable. "Agent determines what it needs" must never bleed one inch into "agent obtains and judges it."

---

## 2. The five layers

1. **Deterministic substrate (owns C&A entirely).** Population pulled from the declared authoritative source; every record SHA-256-hashed at intake and written to WORM under a separate writer identity; attribute tests run as pure functions emitting PASS / FAIL / UNKNOWN. The auditor's assertion is satisfied here or nowhere.
2. **MCP server on the evidence store (not on source systems).** Deterministic collectors and tests exposed as typed, read-only tools querying the WORM-backed index. A smaller second tool class allows read-only *source* lookups for investigating UNKNOWNs — but anything retrieved that way re-enters through deterministic intake (hash, store, re-test) before it can influence a verdict. The agent never holds evidence that skipped the front door.
3. **Agent loop (Agent SDK) — retrieval and investigation only.** Locates the join key; deterministic code performs the join. Output is a *pointer to where evidence deterministically resides*, never evidence itself.
4. **Skills — the audit-procedure library.** One Skill per control: control ID, authoritative population source, attribute list, tolerance semantics, which MCP tools, what constitutes support. Encodes *procedure*, never *judgment about outcomes*.
5. **Hooks — deterministic guardrails on the agent.** PreToolUse hooks hard-block: allowlist read-only MCP tools, deny writes outside scratch, deny egress beyond approved endpoints, log every tool call into the hashed trail. Belt-and-suspenders with IAM (agent identity has zero write on the evidence store).

---

## 3. The plan → freeze → execute pattern (the hinge)

Given a control + a source API, there are four questions. The agent owns the first two; deterministic code owns the last two.

- **Agent decides (planning):** which endpoints/fields carry the attributes, the join key, pagination, tenant-local custom-field mappings. Output is a **structured collection spec (JSON)** — a plan, not data.
- **The spec is schema-validated, human-ratified at the trust boundary, then frozen and versioned.**
- **Deterministic runner executes the frozen spec:** pulls the full population from the declared source, counts, reconciles two-source, hashes, writes WORM. **Completeness asserted here.**
- **Deterministic tests execute:** pure functions over hashed records → per-attribute PASS/FAIL/UNKNOWN with field values + record hashes as support; each test carries a seeded fixture proving it can fail. **Accuracy asserted here.**

The agentic step is **amortized** — once per control-per-system, or on drift — not once per record. That is how "agentic" (plan discovered, not hand-coded) and "deterministic" (every execution byte-identical, auditor-re-runnable) coexist without contradiction.

---

## 4. Source of truth: declared in the Skill, enforced at intake

- **Declaration = audit judgment.** The domain Skill (CC6 logical access, CC7 monitoring, CC8 change, A1 availability) names the authoritative population source.
- **Enforcement = code.** The intake runner reads the declaration and pulls population only from there, refusing any other origin.
- **Two-tier with override.** Authoritative source declared at domain level, specialized at control level where the population differs (CC6 provisioning → Workday new-hires; privileged-access review → the target system's current privileged accounts, not HR).

---

## 5. The human-authored (human-ratified) judgment set

These stay human-owned. If any leaks into the agent's autonomous control, the assertion leaks with it.

- **Authoritative population source** (per §4).
- **Tolerance semantics** — e.g. "5 business days": whose calendar, which timezone, clock starts on termination date or next business day. *Where these tests silently break.*
- **Definition of a valid approval** — who is an authorized approver. "Unauthorized" is defined by management designation, not model inference.
- **The pass/fail predicate** — tested, versioned code with a seeded failing fixture. Never generated fresh at runtime.

Refinement: the agent may **draft** any of these (read the criterion + existing audit program, propose the attribute list / tolerance interpretation / candidate approver population). The line is *decide* vs *touch* — the agent must not **decide** the judgment, but it may **propose** it for explicit, versioned human ratification. Human-**ratified**, not necessarily human-**originated**.

---

## 6. Agent roles (all above the gate)

1. **Planning** — draft the collection spec (§3).
2. **Drift detection** — continuously compare a run's shape against history and against a semantic model of the control; raise "this looks wrong" even when nothing technically broke (e.g. a new `add_member` SSO event subtype that schema-validates but silently drops half the grants). This is the agent as *continuous auditor of the collector*. Output is an alert to a human, never a silent re-freeze.
3. **UNKNOWN investigation** — propose candidate resolutions for records the deterministic join couldn't key. Re-enters through the gate.
4. **Skill drafting** — author-assist the procedure library (§5), human-ratified before canonical.

The continuous loop is a **scheduler**, not an agent loop: cron invokes the deterministic pipeline (collect → hash → WORM → test → verdict → alert on transitions). The agent loop runs only on UNKNOWN residue or drift, and it terminates.

---

## 7. The self-learning fence

- **Safe above the gate.** Learning API pagination shapes, tenant custom-field locations, throttle limits, identity-match heuristics — fine, because each lesson still yields a *draft* that is schema-validated and frozen, or a *candidate* that re-enters through deterministic re-test. A bad learned heuristic produces a proposal that fails the check; it cannot produce a false PASS.
- **Poison at the verdict layer.** The test predicate, tolerance, authoritative source, approver definition never learn. A control that adapts its own pass criteria in response to its own outcomes is not a control — it is a system learning to hide findings.
- **Re-performance is the concrete reason.** An auditor must re-run the pipeline and get the identical answer, and see a versioned, dated, reviewed record of any test change. Silent runtime learning breaks reproducibility: record #5,000 judged by a test that quietly differs from the one that judged record #1.
- **Learned improvements flow through the same freeze-validate-approve gate as human changes** — proposed diffs in version control, never live mutations.

---

## 8. Janus — build plane only

Janus is a Claude Code scaffold (hooks, skills, subagents, an append-only learnings ledger). Its lane is **build-time and cross-project authoring memory**: it makes *collector and spec authoring* faster and lets a second control domain inherit what the first taught (Jira changelog quirks, GitHub audit pagination). Its discipline is already correct — `/reflect` distills, `/evolve` *deliberately promotes* stable lessons through review; it never auto-applies.

Hard fence: drift detection, UNKNOWN investigation, and Skill drafting are runtime/design-time reasoning on a specific tenant's data — that is the Agent SDK plane, **not** Janus's genome. The verdict, Janus must never learn about by construction. **Janus is the workshop, not a component of the running system. It appears in the "how this was built" section, never in the runtime diagram.**

---

## 9. The honest agentic ceiling

- **UNKNOWN is doing suspicious work.** If the agent investigates UNKNOWNs and proposes resolutions, at high volume it is *shaping the tested population one candidate at a time*, and the deterministic gate only ever confirms/denies the agent's framing — it never generates the alternative the agent didn't propose. The gate does not fully close this.
  - Mitigations (partial, and stated as such): cap the UNKNOWN-resolution rate; treat high UNKNOWN volume as itself a **finding** (undocumented provisioning process = a true CC6.2 exception, not a data-cleanliness problem to agent away); every agent resolution is a logged, reviewable proposal with its evidence trail; agent-resolved records carry a flag into the workpaper so auditors sample *them specifically*.
  - Residual, stated honestly: agent investigation of ambiguity is where judgment leaks back in. The answer is to **surface it as reviewable exception volume**, not to claim the gate neutralizes it.
- **Cannot generalize judgment across controls unsupervised.** It cannot decide a control is satisfied *in spirit* when the mechanical test fails for a legitimate reason (break-glass provisioning approved out-of-band; policy-exempt service account). Those are the cases that make audit a judgment profession — each is an UNKNOWN or FAIL for a human.
- **Claim the 80–90%, not autonomy.** Realistic target: deterministic tests cover 80–90% of the population cleanly, the drift monitor watches the collectors, the exception queue is small, well-evidenced, and correctly *surfaced* rather than hidden — a genuinely better audit than screenshot-and-sample. A design that claims zero human judgment is the one that fails an audit of itself.

---

## 10. The invariant

> The agent can iteratively discover assets and propose collection mechanics, but a human ratifies the semantic mapping **and the authoritative population** at the trust boundary, and only deterministic, versioned, hash-chained code — independently verified and emitting OSCAL — executes the test and decides what passes. UI / computer-use assists human-attested evidence; it never autonomously judges. Nothing the agent learns shortcuts that line.
