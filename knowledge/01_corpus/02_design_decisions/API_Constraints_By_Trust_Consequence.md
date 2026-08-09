# API Constraints by Trust-Consequence

Status: working artifact (July 16, 2026)
Scope: re-sorts the consolidated API-reality catalog into three lanes by **what happens to the C&A assertion when the agent gets the constraint wrong**. That failure mode — not the API surface — decides which side of the `plan → freeze → execute` gate a constraint lives on. Feeds collection-spec planning (`Aegis_Investigator_Agentic_Architecture.md §3`), the self-learning fence (`§7`), and the semantic-review gate (`Design_Decisions D-4`).

---

## The organizing principle

A flat "known gotchas" list is the wrong final form because it hides the only distinction that matters to the architecture: some constraints **fail loud** (get them wrong, the pull throws — it can never manufacture a false PASS) and some **fail silent** (get them wrong, you get a well-formed but truncated or mis-scoped population — a run that succeeds and lies). A third, smaller set fails **semantically** (the evidence is genuine but irrelevant). Each failure mode lands on a different side of the gate:

| Lane | Failure mode | Owner | Where it lives |
| --- | --- | --- | --- |
| 1 — Mechanics | Throws at execution | Agent (may learn/refine) | Skill tool-declaration hints; self-learning fence, `§7` |
| 2 — Completeness traps | Silent truncation / mis-scope | Deterministic runner + verifier | Runner assertions + independent verifier count checks (`D-2`) + Skill population declaration (`§4`) |
| 3 — Semantic traps | Genuine-but-irrelevant evidence | Human ratifier | Mandatory `D-4` semantic sign-off before freeze |

The rule of thumb: **if a wrong value produces a visible error, the agent may own it; if a wrong value produces a plausible-looking answer, the runner or a human must own it.**

---

## Lane 1 — Fail-loud mechanics (agent self-learning lane)

These are safe above the gate. A bad learned heuristic here yields a proposal that fails the check — it cannot produce a false PASS (`§7`). Encode as planning hints; let the agent discover and refine them once per control-per-system (amortized, `§3`).

| Source | Constraint | Why it fails loud |
| --- | --- | --- |
| Workday RaaS | 30-minute execution timeout | Request dies; no partial-success masquerade |
| Workday RaaS | ISU username must not contain `\` | 401/403 on the call |
| Workday RaaS | Report must be "Advanced" + "Enable As Web Service" checked | No endpoint / error until configured |
| Workday RaaS | Report owner + name hardcoded in URL (only connection-level fields like `{tenant_id}` templatable) | Wrong URL → request fails |
| NetSuite | Mandatory header `Prefer: transient` on every SuiteQL REST call | Query rejected without it |
| NetSuite | `FETCH FIRST N ROWS ONLY` (Oracle SQL), not `LIMIT` | Syntax error |
| NetSuite | TBA with HMAC-SHA256 signatures | Auth failure |
| NetSuite | Role needs Reports → SuiteAnalytics Workbook permission to run SuiteQL | 403 on execute |
| GitHub | 10 tokens per user/app/scope; 10-token/hour creation limit | Throttled request, visible |
| GitHub | Scope normalization (`user, user:email` collapses to `user`) | Token has fewer scopes than asked — surfaces in `X-OAuth-Scopes` |
| GitHub | `X-OAuth-Scopes` / `X-Accepted-OAuth-Scopes` mismatch debugging | Diagnostic, not a silent path |
| AWS Identity Store | Token-bucket throttling → `ThrottlingException` / 429 under high-concurrency scans | Explicit error; retry with backoff |
| AWS Identity Store | `Extensions` map uses a `Document` type unsupported by old CLI / Java·Go V1 SDKs | SDK-level failure |
| Amazon S3 | Versioning is a mandatory prerequisite for Object Lock | Enable-Object-Lock call fails without it |

---

## Lane 2 — Fail-silent completeness traps (deterministic runner + verifier)

These bear directly on the **Completeness** half of C&A, which the deterministic substrate owns and nowhere else (`§2`, `§4`). They must **not** live in the agent's memory as hints — they become assertions the deterministic runner enforces and the independent verifier (`D-2`) re-checks by count. Getting one wrong returns a plausible population that is quietly incomplete.

| Source | Constraint | What fails silently | Required deterministic check |
| --- | --- | --- | --- |
| AWS Identity Store | No server-side filtering by status | Agent assumes a server-side `status` filter → API ignores/omits it → truncated population | Pull the **full** population, filter client-side; verifier asserts `count(retrieved) == count(authoritative source)` |
| Workday RaaS | 50,000-row execution boundary + no native pagination → pseudo-pagination by date-entered prompts | Records with null date fields, or falling between chunk boundaries, silently dropped (*note: whether the 50k ceiling truncates or errors, treat it as a completeness risk — the safe stance is invariant to which*) | Sum of chunk counts reconciled against an independent total count; explicit null-date sweep; overlapping/verified chunk boundaries |
| NetSuite | Manual `limit`/`offset` pagination | Offset paging over a mutating table skips or double-counts rows | Stable sort key (keyset pagination preferred); verifier dedups on primary key and reconciles total |
| NetSuite | Boolean parameters as strings `'T'`/`'F'` | Wrong coercion can silently mis-filter the population rather than error | Treat as completeness-affecting: reconcile returned count against an independent count for the filtered predicate |
| Apache Doris | Column-level lineage fires only on `INSERT` / `INSERT OVERWRITE` / `CTAS` | `SELECT`-derived transforms produce **no** lineage event → silent gap in the read path | Do not infer read-path column lineage from Doris events; declare the gap in the Skill; instrument at the query layer if the control needs it |
| Apache Doris | `__internal_schema` targets and VALUES-only inserts filtered out by design | No lineage event emitted → absence read as "no data movement" | Declare the exclusion explicitly; never treat event-absence as proof of completeness |

**One API, two lanes.** AWS Identity Store appears here (filtering → completeness) *and* in Lane 3 (the status enum → predicate correctness). Keep them separate: the filtering trap is a count problem, the enum trap is a meaning problem.

---

## Lane 3 — Semantic traps (mandatory D-4 human review)

Getting one of these wrong returns evidence that is valid and tamper-evident but **tests the wrong thing** — the "Windows" vs. "Windows Server 2012 R2" contextual false positive from `D-4`. The gate here is human semantic sign-off before the spec is frozen, tiered by control impact (mandatory for high-impact and first-time specs; never optional on anything touching the population or predicate).

| Source | Constraint | How it goes semantically wrong | Gate |
| --- | --- | --- | --- |
| NetSuite | `BUILTIN.DF()` returns display labels; bare fields return internal numeric IDs | Test maps to the internal ID while the criterion is written against the human-readable label (or vice versa) → genuine-but-irrelevant match | `D-4` semantic sign-off on the field mapping before freeze |
| AWS Identity Store | `UserStatus` predicate | Live API returns **two** values (`ENABLED` / `DISABLED`) — see correction below. A predicate written as a three-value switch silently mishandles legacy/absent-field records | Semantic review of the predicate + drift watch; write it two-value, treat a *missing* field as your-own-schema `UNKNOWN`, not an API enum |

---

## Outside the collection-spec taxonomy (kept, not miscategorized)

Three catalog items are real constraints but not inputs to *collection-spec planning*. Forcing them into the three lanes would distort the taxonomy, so they're parked here against the layer that actually owns them.

- **OSCAL all-or-nothing SSP complexity + vocabulary rigor** (`responsible-party`, `system-component`, `implemented-requirement`, `inventory-item`, `set-parameter`) → **emission-side** constraint on the Documenter, not on collection. Governed by the `D-3` "minimal valid Assessment Results first" scope fence.
- **S3 Object Lock enablement / versioning / Compliance-mode retention floor** → **storage-layer config** for the evidence bucket itself, not a source-collection gotcha. (Note the stale claim corrected below.)
- **GitHub read-only-scope gap** → **identity-posture / least-privilege** for the agent's *own* credential (`§5`, `D-2`), not a spec-completeness input. It changes which token the agent holds, not what population it retrieves.

---

## Corrections baked in (self-checking corpus)

The catalog as pasted repeats three claims that are stale or overstated. Shipping them into a spec would propagate the exact drift the `Version_Drift_Ledger` exists to catch. Corrected here:

1. **S3 "creation-time only" is STALE.** The catalog says bucket-level Object Lock can only be enabled at bucket creation. Since **November 20, 2023**, Object Lock can be enabled on an *existing* versioning-enabled bucket, and existing objects are locked in bulk via S3 Batch Operations off an Inventory manifest. (`Version_Drift_Ledger §1`.) **Action:** drop the creation-time blocker from any spec precondition; there is no architectural obstacle to WORM-protecting a pre-existing evidence bucket.

2. **Identity Store `UserStatus` enum is OVERSTATED.** The catalog says the field may return `UNKNOWN`. The live `DescribeUser` / `ListUsers` reference lists valid values as **`ENABLED | DISABLED` only** — no API-returned `UNKNOWN`. (`Version_Drift_Ledger §2`.) **Action:** write the deprovisioning predicate as a two-value check; model a *missing/absent* field as `UNKNOWN` in your own schema, and validate against a live call since AWS's own sample responses don't populate the field.

3. **GitHub read-only private access is scope-specific, not absolute.** True that no read-only **classic OAuth scope** exists — `repo` bundles full write. But a **fine-grained PAT** or **GitHub App** with `Repository contents: Read-only` reads private repository contents; fine-grained tokens draw from 50+ granular permissions, each grantable no-access / read / read-and-write. Residual: a small set of endpoints still lack fine-grained support and force a classic PAT/OAuth app. (GitHub Docs; GitHub fine-grained PAT announcement — verified current.) **Action:** for CC8 change evidence, use a fine-grained PAT/App with `Contents: read` + `Metadata: read`; never carry the write-bearing `repo` scope on the evidence-read path — that over-grant is itself an ITGC finding.

---

## How to use this

- **Lane 1** → Skill tool-declaration hints. The agent may learn and refine these; the self-learning fence (`§7`) makes that safe because errors surface loudly.
- **Lane 2** → deterministic runner assertions + independent-verifier count reconciliation (`D-2`) + Skill population declaration (`§4`). Never agent-owned. This is where "the spec runs" becomes "the spec runs and doesn't lie."
- **Lane 3** → mandatory `D-4` semantic sign-off before freeze, tiered by control impact.
- **Version this file and put it under drift detection (`§6.2`).** It is a point-in-time snapshot of moving targets — at least one entry (Identity Store `UserStatus`) has already changed once, and three needed correcting on first pass. Re-verify on the same cadence as the `Version_Drift_Ledger` method note (GitHub app-model gaps, RFC-0024 timelines, and any API that adds server-side filtering are the likeliest to move).

The split turns a flat gotchas list into three streams that each land on the correct side of the gate: **mechanics the agent may learn, completeness the runner must enforce, semantics a human must ratify.** It hardens the mechanical floor of the 80–90% deterministic coverage; it does nothing for the residual judgment surface (the UNKNOWN funnel, tolerance semantics, approver definitions), and shouldn't be claimed to.
