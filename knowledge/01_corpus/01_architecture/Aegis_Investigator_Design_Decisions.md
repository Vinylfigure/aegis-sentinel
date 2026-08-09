# Aegis Investigator — Design Decisions (Agentic Refinements)

Status: working decision capture
Format: each refinement carries a **verdict** (Adopt / Adopt with conditions / Reject to investigation lane), rationale, and the correction applied. Sourced from the five-point refinement proposal, pressure-tested against the architecture in `Aegis_Investigator_Agentic_Architecture.md`.

Verdict summary: two adopt clean, two adopt with conditions, one stays on the wrong-side-of-the-line trap and is redirected.

---

## D-1. Hash chains for chain-of-custody — **ADOPT (clean)**

- **Decision:** Every new audit record includes the content hash of the previous record, forming a cryptographically linked list; any historical modification breaks every subsequent hash.
- **Rationale:** Correct CC7.3 (capture and preserve security events) chain-of-custody. Already aligned with Aegis's per-record SHA-256 model — this links what was already hashed.
- **Design note:** A linear chain needs (a) a defined ordering key and (b) a per-run genesis anchor, or concurrent collectors race the tail. Specify both.

---

## D-2. Independent verification of the runner — **ADOPT (with correction: not an "agent")**

- **Decision:** A separate component recomputes hashes and verifies the data-lineage trace of every run. On any missing segment or signature mismatch, it invalidates the run and flags a compliance exception.
- **Correction:** The source calls this a "Scorer Agent." It must **not** be an LLM agent — it is the most deterministic component in the system (recompute, verify links, check counts, pass or halt). Calling it an agent invites exactly the confusion the architecture exists to prevent. Name it **independent deterministic verifier**.
- **Design note:** Runs under a **separate identity** writing to a **separate location**, so it cannot be suppressed by whatever it verifies (separation of duties, CC7.3).

---

## D-3. Emit machine-readable OSCAL — **ADOPT (with scope fence)**

- **Decision:** The deterministic runner formats every finding, observation, and asset description into a schema-valid OSCAL **Assessment Results (AR)** package, not just status flags.
- **Rationale:** Correct emission format; FedRAMP-literate; validates under compliance-trestle ("validates under trestle" is the reviewer-facing one-liner). Enables programmatic ingest by agency GRC tooling.
- **Condition:** OSCAL AR is a deep schema; full fidelity is a project of its own. First build = **minimal valid AR** (results, observations, findings, subjects). Complete fidelity is a later milestone. Do not let the schema swallow the sprint.

---

## D-4. Semantic Review gate at the trust boundary — **ADOPT (with two honest caveats)**

- **Decision:** Insert an explicit human semantic-validation gate on the agent's drafted collection spec **before** it is versioned and frozen. Named failure mode: semantic hallucination (mapping to a generic "Windows" endpoint instead of "Windows Server 2012 R2" — genuine-but-irrelevant evidence; contextual false positives).
- **This is the ratification step already in the plan → freeze → execute pattern, made explicit.**
- **Caveat 1 — do not overclaim.** It closes the **design-time semantic gap**. It does **not** "concentrate the entire error surface into a single control point" (source optimism). It does nothing for runtime semantic drift (API changes meaning after the spec was blessed — see D-6/drift detection) or the UNKNOWN-funnel judgment leak. Write it as "closes the design-time semantic gap," not "closes the error surface."
- **Caveat 2 — tier it, don't universalize.** Human-review-every-spec doesn't scale to continuous monitoring. Policy: **mandatory** human semantic sign-off for high-impact controls and first-time specs; lighter review for low-risk re-plans; **never optional** on anything touching the population definition.

---

## D-5. Computer-use / UI verification for the "20% manual gap" — **REJECT from verdict path → redirect to investigation/human-attest lane**

- **Proposal:** The agent's mechanical-wiring draft includes computer-use AI agents navigating UIs to record workflows; recorded UI sessions carry DOM snapshots + cryptographic timestamps to satisfy application-level evidence needs.
- **Verdict:** This is the same trap already rejected earlier — a non-deterministic agent in the **evidence-capture path** for exactly the controls hardest to make reliable. The nicer suit (DOM snapshots, hashed recordings) does not change the substance.
- **Why the hash doesn't rescue it:** Hashing a screen recording makes the *artifact* tamper-evident (pixels didn't change post-capture). It does **not** make the *act of collection* deterministic or complete. Computer-use navigation is non-reproducible (DOM differs next run, modals appear, elements move), can silently miss the row that matters, and "I clicked through and it looked approved" is an **LLM assertion about state** — the exact category the invariant forbids from the verdict path.
- **Redirect (correct side of the line):** Computer-use is an **investigation and human-workpaper-assist** tool. It may drive a UI to help a **human** capture evidence they then **attest** to; the hash makes that captured artifact tamper-evident. Its output is **never** an autonomous PASS and it **never** enters the deterministic population or verdict. The 20% gap is real; the answer is human-attested evidence with agent assistance, not agent-autonomous UI evidence.

---

## Corrected invariant

> The agent can iteratively discover assets and propose collection mechanics, but a human ratifies the semantic mapping **and the authoritative population** at the trust boundary, and only deterministic, versioned, hash-chained code — **independently verified (deterministic verifier, not an agent)** and emitting OSCAL — executes the test and decides what passes. UI / computer-use assists human-attested evidence; it never autonomously judges. Nothing the agent learns shortcuts that line.

Changes from the proposed invariant: "Scorer agent" → "independent deterministic verifier"; added the **authoritative population** clause (the assertion that actually matters); added the explicit UI/computer-use boundary.
