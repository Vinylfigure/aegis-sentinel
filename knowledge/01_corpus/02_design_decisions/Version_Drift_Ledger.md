# Aegis — Version-Drift & Contradiction Ledger

Status: verification pass (July 16, 2026)
Scope: each contested technical fact in the corpus — the six in the pasted version-drift analysis plus the two additional items in `Contradictions.md` not covered there — re-checked against a primary or authoritative source, dated, and reconciled. The point is to turn ~100 independent assertions into a self-checking corpus: where sources disagree, this says which one is current and which is stale.

**How to read a verdict.** *Resolved* = one position is now authoritative and the other is stale; *Standing tension* = the disagreement is real and unresolved as of this date; *Both true* = the "conflict" is two different requirements confused for one.

---

## Headline: the correction itself carries drift

The pasted analysis is right on 5 of 6 verdicts, but the self-check caught three precision errors *inside the correction* — the exact failure mode this exercise exists to catch:

1. **UserStatus enum is overstated.** The corpus (and the pasted "authoritative update") says the AWS Identity Store `UserStatus` field returns `ENABLED | DISABLED | UNKNOWN`. The live API reference lists valid values as **`ENABLED | DISABLED` only**. There is no `UNKNOWN`. This is the same overstatement that bit the project before, re-imported into the fix.
2. **The S3 "creation-time only" hedge is itself stale.** The pasted verdict concedes that "the bucket-level default requires creation-time enablement." That has been false since **November 2023** — Object Lock can be enabled on *existing* buckets (versioning required), not just at creation.
3. **The OSCAL "unanimously chose alternatives" line is an embellishment.** FedRAMP's own text says no Phase 1 pilot participant *used OSCAL* to structure the required materials. It does **not** say they "unanimously chose alternative machine-readable formats" — that's a stronger claim the source doesn't support.

Detail below.

---

## 1. Retrofitting S3 Object Lock onto existing data — **RESOLVED (with a stale hedge to drop)**

- **Corpus claim (stale side):** Object Lock "can only be enabled when you create the bucket"; existing buckets "cannot be converted after the fact." (DeepInspect, Jul 2026; Rise of Cloud, Mar 2026.)
- **Verified position (July 2026):** Two things are both routine now. (a) Since **Nov 20, 2023**, Object Lock can be enabled on an *existing* bucket (provided versioning is on) — no AWS Support ticket. (b) Existing *objects* are locked in bulk with **S3 Batch Operations** driven off an S3 Inventory manifest, at billions-of-objects scale, in `COMPLIANCE` or `GOVERNANCE` mode. Sources: AWS "S3 Object Lock" feature page and the Nov 2023 "enabling Object Lock on existing buckets" announcement; AWS docs `S3Retention` (Batch Operations).
- **Verdict:** The "impossible" claim is stale. **Correction to the correction:** drop the pasted analysis's own hedge that "bucket-level default requires creation-time enablement" — the bucket-level enablement restriction was lifted in 2023.
- **Aegis implication:** No architectural blocker to WORM-protecting a pre-existing evidence bucket. The Decision Ledger's separate entry on using Batch Operations to retrofit at scale is correct and stands.

## 2. AWS Identity Store — visibility into account status — **RESOLVED (enum overstated)**

- **Corpus claim:** the Identity Store API had "no way to determine if an account was enabled or disabled"; the fix asserts `UserStatus (ENABLED, DISABLED, UNKNOWN)` is now returned by `ListUsers`/`DescribeUser`.
- **Verified position (July 2026):** The live `DescribeUser` API reference **does** now include a `UserStatus` response element — confirming the field is real and the old "invisible status" limitation is genuinely superseded. **But** its documented valid values are **`ENABLED | DISABLED`**, not three states. `UNKNOWN` does not appear in the reference. (Note: the API examples in AWS's own doc don't even populate the field in their sample responses, so validate against a live call before depending on it in a collector.) Source: AWS IAM Identity Center — Identity Store API Reference, `DescribeUser`.
- **Verdict:** Old limitation is stale; the field exists. The `UNKNOWN` value is an overstatement — remove it from `Contradictions.md` and any collector that switches on it.
- **Aegis implication:** A CC6 deprovisioning collector can key on `UserStatus == DISABLED` deterministically — but write the predicate as a two-value check, and treat a missing/absent field as its own `UNKNOWN` in *your* schema (a null from the API), not as an API-returned enum value.

## 3. FedRAMP deterministic authorization-boundary diagrams — **STANDING TENSION (softening in progress)**

- **Corpus claim:** RFC-0024 (Jan 13, 2026) says providers SHOULD use machine-generated deterministic telemetry to generate diagrams incl. the Authorization Boundary Diagram; industry (CrowdStrike/Salesforce/Wiz, Mar 2026) calls fully-deterministic boundary generation not technically feasible for complex multi-cloud/SaaS.
- **Verified position (July 2026):** Both halves check out. RFC-0024 is real, Rev5-only (explicitly *not* 20x), released Jan 13, 2026, using "SHOULD" (not "MUST") for deterministic telemetry, with compliance dates Sept 30, 2026 (initial) → Sept 30, 2027 (final). Crucially, FedRAMP's **March 2026 "Initial Outcome" notice (0009)** already walked toward the industry position: it states there is *no expectation* of a single traditional boundary diagram containing every service and flow, and grants providers flexibility to present the boundary "across multiple levels of abstraction and grouping" — the exact "human-guided abstraction" point the vendors raised. Sources: fedramp.gov/rfcs/0024, fedramp.gov/notices/0009, FedRAMP community discussion #114.
- **Verdict:** Standing tension, but narrowing — the government has already conceded the abstraction point. The pasted analysis frames this as a harder mandate than it now is; it's a "SHOULD… where feasible" with an explicit abstraction escape hatch.
- **Aegis implication:** This is the honest ceiling from `Aegis_Investigator_Agentic_Architecture.md §9` and the Workflow-Theory "boundary mapping" risk, confirmed by regulator behavior: don't promise deterministic boundary-diagram generation. Aegis should emit deterministic *asset/interconnection inventory* as OSCAL and let a human compose the abstracted diagram — which is now exactly what FedRAMP's own softened language contemplates.

## 4. OSCAL — mandated "lingua franca" vs. near-zero production adoption — **BOTH TRUE (adoption embellished)**

- **Corpus claim:** OSCAL is the standard that makes compliance-as-code possible; simultaneously, "not a single submission" used it.
- **Verified position (July 2026):** The zero-adoption figure is real and traces directly to **FedRAMP's own RFC-0024 text**: in 2025 FedRAMP processed 100+ Rev5 authorizations with no submission using OSCAL, and no formal Phase 1 20x pilot participant used it to structure the required machine-readable materials. OSCAL remains the mandated format for the Sept 30, 2026 machine-readable requirement. Sources: RFC-0024 (via community #114); corroborated by Elevate, Platform28, Knox Systems (Feb–May 2026).
- **Verdict:** Both true — a mandated standard with almost no production footprint as of early 2026. **Correction:** the pasted claim that pilots "unanimously chose alternative machine-readable formats over OSCAL" overshoots the source, which says only that no participant *used* OSCAL. Don't assert a positive choice of alternatives that the record doesn't establish.
- **Aegis implication:** Emitting OSCAL is still the right call (D-3 in Design Decisions), but the "minimal valid AR first" scope fence is vindicated by reality — near-nobody has full-fidelity OSCAL in production, so a minimal valid Assessment Results package is genuinely ahead of the field, not behind it. Expect agency-side ingest tooling to lag (the "dual-format burden" risk in Workflow Theory §4 is live).

## 5. GitHub read-only access to private repositories — **RESOLVED (scope-specific)**

- **Corpus claim:** GitHub provides no OAuth scope for read-only access to private repos; the `repo` scope bundles write.
- **Verified position (July 2026):** True *for the OAuth flow* — confirmed against GitHub's own scopes doc and a Sept 2025 community thread: no read-only OAuth scope for private repos exists; `repo` grants read+write. But true read-only private access **is** routine via **fine-grained PATs** and **GitHub Apps** with `Repository contents: Read-only`. GitHub's docs explicitly steer integrators to GitHub Apps (fine-grained permissions) over OAuth apps (blunt scopes). Sources: GitHub Docs "Scopes for OAuth apps"; community discussions #174347, #160535.
- **Verdict:** "Impossible" is scope-specific to legacy OAuth; read-only is the norm via GitHub Apps / fine-grained PATs.
- **Aegis implication:** For audit-grade CC8 (change) evidence, the correct pattern is a **GitHub App with fine-grained read-only permissions** (Contents: read, plus Metadata; add Pull requests / Administration read as the control requires) — not an OAuth app carrying the `repo` scope, which over-grants write and is itself an ITGC finding waiting to happen. Update any collector spec that still assumes `repo`.

## 6. SOX retention — 366 days vs. 7 years — **BOTH TRUE (and the 7 is a rule, not the statute)**

- **Corpus claim:** one source says 366 days of operational logs; another says SOX §802 mandates 7 years.
- **Verified position (July 2026):** These don't conflict — they're different obligations confused for one. The 366-day figure is an **operating-effectiveness testing window** (one full audit cycle), a practitioner convention, not a statutory retention minimum. The 7-year figure is the legal records-retention mandate — but precisely: it comes from the **SEC's implementing rule, 17 CFR 210.2-06 (Rule 2-06 of Regulation S-X)**, adopted under SOX §802. The bare criminal statute **18 U.S.C. §1520(a)(1)** actually says **5 years**; the SEC rule extends it to **7**. (Sources that attribute "7 years" directly to the §802 statutory text — and sources that cite "5 years" as the operative period — are both imprecise; the operative requirement is 7, sourced to the SEC rule.) Penalty precision: §1520 destruction carries up to 10 years; §1519 (obstruction) up to 20 — sources conflate these. Sources: SEC "Retention of Records Relevant to Audits and Reviews"; uscode.house.gov 18 U.S.C. §1520 (text in effect July 15, 2026).
- **Verdict:** Both true; the pasted analysis's "operational floor vs. legal ceiling" framing is correct. The refinement is *which instrument* sets 7 years (SEC Rule 2-06, not the statute).
- **Aegis implication:** A collector's evidence bucket that expires at 366 days passes a testing-window sample but violates the 7-year retention rule. Set WORM retention to the **7-year** obligation for SOX-relevant audit evidence; treat 366 days only as the minimum window over which operating-effectiveness *tests* run.

---

## Additional items from `Contradictions.md` (not in the pasted analysis)

## 7. PCAOB AS 1105.10A — mandatory testing vs. the "remote possibility" carve-out — **RESOLVED (high Aegis relevance)**

- **Corpus claim:** a literal read of AS 1105.10A requires auditors to both understand the source *and* test the external electronic information/controls; a Sept 2025 policy statement softens this.
- **Verified position (July 2026):** Confirmed and precisely dated. Paragraph .10A was added by the June 2024 amendments (PCAOB Rel. 2024-007), effective for fiscal years beginning **on or after Dec 15, 2025**. The **Board Policy Statement of Sept 18, 2025 (Rel. 2025-004)** states that where the auditor concludes there is no more than a remote possibility the information was modified in a way that renders it unreliable, the PCAOB will not treat the absence of separate .10A(b) testing as noncompliance. Staff examples followed Oct 1, 2025. Sources: pcaobus.org AS 1105; PCAOB Rel. 2025-004; CAQ Audit Insider (Sep 2025).
- **Verdict:** The Sept 2025 policy statement is the current interpretive authority; the rigid "must always test" reading is superseded.
- **Aegis implication:** This is arguably the single most important regulatory hook for the whole architecture. The **"remote possibility of modification" standard is exactly what SHA-256-at-intake + WORM + hash-chain provenance is engineered to establish.** Aegis's immutability stack isn't just defensive hygiene — under Rel. 2025-004 it is the specific condition that lets an auditor *skip* separate .10A(b) testing of the evidence. Frame the reviewer-facing story around this: the storage-layer contract satisfies the carve-out.

## 8. FedRAMP 20x — the 3PAO's evolving role — **DIRECTIONAL, CONFIRMED**

- **Corpus claim:** 3PAOs historically reviewed static outputs (screenshots, log exports); under 20x they shift toward validating automation scripts, control logic (Terraform, OPA/Rego), and continuous-monitoring fidelity.
- **Verified position (July 2026):** Confirmed as direction of travel across multiple 2026 sources: under 20x the 3PAO moves from control-by-control point-in-time audit toward assessing continuous security posture and the automation that produces evidence; specific Phase 3 requirements are still being finalized. Sources: Diogenes Club, Platform28, Knox Systems (2026). Treat as directional, not a fixed published standard.
- **Verdict:** Real trend, requirements still settling — re-verify against the FedRAMP roadmap before relying on specifics.
- **Aegis implication:** Aegis is built for the world this trend implies — an assessor re-running deterministic, versioned, hash-chained tests rather than eyeballing screenshots. The `§7 self-learning fence` (re-performance yields byte-identical results; every test change is versioned/dated/reviewed) is precisely what an automation-validating 3PAO will want to inspect.

---

## Method note — what to re-verify on a cadence

Most of these are stable now, but four are pinned to moving deadlines or unsettled guidance and should be re-checked before any external-facing claim:

- **RFC-0024 timelines** (Sept 30, 2026 initial / Sept 30, 2027 final) and any further boundary-diagram softening — regulatory, still in comment/outcome cycles.
- **OSCAL adoption footprint** — the "zero submissions" figure is a 2025 snapshot; adoption is expected to move fast once the Sept 2026 requirement bites.
- **PCAOB .10A staff guidance** — the Office of the Chief Auditor is still issuing illustrative examples; the practical bar for "remote possibility" will sharpen.
- **FedRAMP 20x 3PAO requirements** — Phase 3 specifics not yet fixed.

Everything else (S3 Object Lock mechanics, Identity Store `UserStatus`, GitHub Apps read-only, SOX 7-year rule, 18 U.S.C. §1520 text) is settled technical/legal fact and only needs re-checking if the underlying API or rule changes.
