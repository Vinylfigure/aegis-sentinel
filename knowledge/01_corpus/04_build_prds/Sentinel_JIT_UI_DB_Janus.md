# Sentinel — JIT Access, UI, Database & Janus

**Date:** 2026-07-24 · Companion to `PRD_Aegis_GitHub_Sentinel.md` and `Sentinel_Audit_And_Replit_Execution.md`
**Status:** F-1/F-2/F-3 implemented and tested; this document specifies the remaining open design.

---

## 1. The JIT module is not a new design problem — it's AM-05

Your instinct ("popup in GitHub, log the action, approval triggers, access level changes, PR, Slack notification") is circling a control that is already fully specified in the corpus. **AM-05 — Access Approval**: *"Requests for new access, or modifications to existing access... are submitted and approved prior to granting access."* Its testing attributes are the JIT module's acceptance criteria, verbatim:

| AM-05 attribute | JIT implementation | Enforced where |
|---|---|---|
| A. Ticket/request present | GitHub Issue created from an issue form; issue number is the request ID | Intake — no issue, no grant path exists |
| B. Approval obtained **before** provisioning | `approved_at < granted_at` asserted in code before the write call | Deterministic precondition |
| C. Granted access matches approved request | Requested role, repo, and TTL are hashed at request time; grant re-reads the hash | Ledger-anchored |
| D. Assignee is not the same as approver | `approver != requester`, hard block | Deterministic precondition |
| E. Scope covers new **and modified** access | `prior_permission` captured pre-grant; restoration targets it, not a default | State machine |

And **AM-04 — Privileged Access Restriction**, attribute C: *"Grants during period tie to approved requests."* That is exactly the reconciliation the monitor performs against its own JIT table — which is why this module is not a bolt-on. **The JIT module manufactures the evidence population that AM-04 and AM-05 are tested against, and the monitor then tests it independently.** Say that sentence in the interview.

Emergency framing is available too: **CM-04 — Emergency Changes** requires approval *within 24 hours* with evidence retained. Elevated repo admin obtained out-of-hours is precisely an emergency change, and the CM-04 attributes (designated emergency, implementation timestamp evidenced, approval within window, evidence retained) drop straight onto the same records.

### There is no "popup" in GitHub — use Issue Forms

GitHub has no modal-dialog surface a third party can inject. The native equivalent, and it's better than a popup for your purposes, is a **GitHub Issue Form** (`.github/ISSUE_TEMPLATE/jit-admin-request.yml`): structured typed fields, rendered as a real form, producing a permanent, timestamped, attributable artifact **inside GitHub itself**. That artifact *is* AM-05 attribute A. A custom web popup would have produced a record only your database knows about; the issue produces one the auditor can see without trusting your tool at all.

### Flow

1. **Request** — engineer opens an issue from the form: target repo, duration (≤8h), reason, emergency flag. Labels applied automatically.
2. **Intake** — webhook fires; the handler validates the form fields deterministically, writes a `PENDING` row plus a ledger record, and posts to Slack `#aegis-approvals` with Approve/Deny buttons. Invalid requests are closed with a comment stating why — a rejection is also evidence.
3. **Approve** — Slack interaction handler checks, in order and all required: signature valid with timestamp inside 5 minutes (replay defense), approver ∈ ratified roster, approver ≠ requester, repo ∈ JIT-eligible allowlist, TTL ≤ cap. Any failure = deny + ledger record.
4. **Grant** — read current permission first (`prior_permission` — needed for correct restoration and for AM-05 attribute E), then elevate via the collaborator API using Token B. Grant record hashed with approver identity, TTL, reason, issue number. Bot comments the grant and expiry onto the issue.
5. **Revoke** — independent cron every 5 minutes restores `prior_permission` (not a hardcoded default) at expiry. It reads only the database and Token B; a Slack outage cannot extend a grant. Failure retries ×3 then raises CRITICAL and writes a FAIL finding.
6. **Reconcile** — the next monitor run observes actual repo admins and joins them against active JIT grants. An admin with no matching active grant is a FAIL. This is AM-04 attribute C, mechanized, and it means **the tool audits its own privilege-granting module**.

The PR variant you floated (approval via pull request rather than Slack button) is worth knowing about but not worth building: it gives you CODEOWNERS-based approval routing for free, but adds latency to what is by definition an urgent path. Slack button for approval; the *issue* carries the durable record. Best of both.

---

## 2. Yes, there's a UI — and it should be small

Build **one page**, not five. FastAPI + HTMX + Tailwind, server-rendered, no build step, no SPA. Replit serves it fine and there is nothing to compile.

The single dashboard shows: run header (spec hash, ledger head, storage class, completeness summary), findings table filterable by control/severity/repo with the deviation triplet expected/actual/severity, the JIT queue with live countdowns, and a Verify Ledger button that re-runs the chain check in front of the viewer. Advisory agent text renders in a visually distinct block labelled **"AI-generated — not evidence"** (F-7).

The reason to keep it one page is that the UI is not the artifact. The ledger and the OSCAL export are the artifacts; the UI is a window onto them. Every hour spent on a five-view app is an hour not spent on the collectors that produce the evidence. If you have spare time at the end, spend it on the ledger record inspector, because "click any finding, see its hash, verify the chain" is the demo moment.

---

## 3. Database: yes, and Replit provides one

You need a database for three things the filesystem cannot do: the ledger (F-1 — the web app and the scheduled monitor are separate processes with separate disks), JIT grant state (must survive between the granting request and the revoking cron), and ratification records (F-4).

**Replit has a built-in PostgreSQL offering** (Neon-backed as of my knowledge cutoff), provisioned from the workspace and exposed as `DATABASE_URL`. That's what to use. They also have a simpler key-value Replit DB and an Object Storage product — neither is right here: the key-value store gives you no ordering guarantees or transactional insert for a chain, and object storage adds latency to what is a small, high-integrity, relational workload. *Verify the current Postgres offering and free-tier limits in-product; my product knowledge ends January 2026.*

The schema is in `src/db.py`, along with the point that matters: append-only is enforced by `REVOKE UPDATE, DELETE, TRUNCATE` on the ledger table and having the app connect as a role holding only `INSERT, SELECT`. Convention doesn't make a ledger append-only; a grant does. And even that is tamper-*evidence*, not immutability — an owner-role connection can still rewrite rows, and the hash chain is what makes it detectable. Keep saying it precisely.

---

## 4. Janus — the use case you've been looking for

Porting nine gh-ec-audit audits is the ideal Janus test case, and it's the first task in this project genuinely shaped like what Janus is for: **repetitive, structurally identical work with a growing body of hard-won environmental knowledge, where each unit produces verifiable evidence of success.**

Each port is the same shape — read the Rust module's behaviour, express it as `evaluate(gh, target, baseline) -> ControlResult`, wire the completeness envelope and visibility probe, write a fixture test. Nine iterations. And each iteration teaches something that generalizes: which endpoints paginate, which lie about counts, which return 404-for-403, which need a second call to establish an independent count. That is precisely a **learnings genome** — append-only, evidence-gated, promoted only when a fixture test proves the learning was real.

Concretely, Janus's three loops map onto the port:

- **Inner loop** — port one audit, run its fixture test, iterate until green.
- **Middle loop (evidence-gated promotion)** — a candidate learning ("`/orgs/{org}/outside_collaborators` has no independent count endpoint; basis must be `exhaustive_pagination`") is promoted to the genome only when a passing fixture test demonstrates it. This is the discipline that stops the scaffold accumulating plausible-sounding folklore.
- **Outer loop (recalibrate)** — scheduled heartbeat re-verifies GitHub API facts in the genome against live behaviour, because the corpus already records two GitHub/AWS facts that changed underneath you. Drift detection on your own learnings.

Critically, this keeps Janus strictly in the **build plane**, which is its stated boundary: Janus writes and refines collector code; it never runs in the verdict path, and the code it produces is human-reviewed before it can decide a PASS. If Janus works here, you have an honest answer to "does Janus actually accelerate anything?" — measured as time-per-audit-port across nine iterations, which should decline if the genome is doing its job. That's a real experiment with a real metric, not a vibe.

**One caution:** don't put Janus on the critical path for the interview build. Run it as the parallel experiment — port audits 5 and 1 by hand first (they're the marquee demos), then hand audits 2, 4, 6, 7, 8, 9 to Janus and measure. If Janus stalls, you've lost nothing; if it flies, you have a second story to tell.

---

## 5. What the corpus says that changes the build

Three learnings from the docs that apply directly and would otherwise be re-derived the hard way:

**Fail-silent beats fail-loud in danger ranking.** The `API_Constraints_By_Trust_Consequence` three-lane model says a constraint whose violation throws is safe for an agent to own, and a constraint whose violation produces a plausible-looking wrong answer must be owned by the runner or a human. Every collector you port should be triaged that way before it's written: pagination limits and the 404 ambiguity are Lane 2 (runner assertions — now implemented), while endpoint paths and parameter names are Lane 1 (agent may learn them, because getting them wrong throws).

**Human-ratified ≠ human-originated.** The admin allowlist, the approver roster, the JIT-eligible repo set, and the severity caps may all be *drafted* by an agent — but they take effect only when a human ratifies the hash. `DbLedger.ratify()` implements this; the baseline hash is checked against the ratification table at run start, so an unratified edit fails the run rather than quietly loosening the standard.

**Decentralize inputs and checking; keep the decision singular.** Multiple agents may propose scope, investigate findings, and cross-check counts. Exactly one deterministic function decides each verdict. Resist every instinct to let an agent aggregate or arbitrate — that's the D-9 line, and it's the one that makes the whole thing defensible.
