# PRD v3 — Aegis: Assurance as Compiled Proof

**Author:** `vinylfigure` (drafted with Claude)
**Date:** 2026-08-12
**Status:** Draft v3 — Build Spec for `vinylfigure/aegis-sentinel` (product: **Aegis**; the agents are **Sentinels**) · supersedes v2 · incorporates adjudicated rulings from external reviews (docs 28–31)
**Canonical diagram:** the Owner's hand sketch (2026-08-12). **Canonical prior art:** the Aegis corpus (investigator architecture, D7/D8/D9, SOC 2 testing matrix, Build Execution PRD v2), the Aegis GCP control matrix, the Demo Mutation Playbook (`docs/MUTATION-PLAYBOOK.md` — per the Owner's ruling on issue #51, no standalone source document exists; this PRD's own §6 was promoted into that file directly).

---

## 0. North star

**Assurance as a compiled proof.** Not "here's my control and here's a screenshot," but: *here is the claim, the universe over which it applies, how that universe was constructed and challenged, what observations were collected, why those observations are capable of proving the claim, exactly what deterministic evaluation ran, and the immutable artifact the verdict derives from.* The denominator is the breakthrough: every competing product shows you what it evaluated; Sentinel proves why that was the right universe. Vanta shows 73 evaluated, 4 excluded. Aegis answers why 77 is correct. Process-first is a *technique* inside that proof — the authoring plane and the agent's map — not the foundational truth.

## 1. Thesis (adjudicated form)

**The technical control substrate is a universal question set, not an invariant implementation.** Every component in scope gets asked the same questions — who can touch it, how does it change, does it come back, can you see what happened — and every answer resolves to a **disposition**: implemented locally · inherited · shared · vendor-managed (their report + your tenant-config evidence) · compensating · N/A with rationale. Workday's application-change control exists; Workday operates it. Nothing exits silently; the mountain-of-N/As objection dissolves at the disposition layer.

**Frameworks are projections, mechanized through CLAIMs.** A claim is a testable proposition — *every terminated employee lost production access within five business days* — with a subject population, required attributes, and evidence contracts. SOC 2 CC6.x, ISO A.5.x, PCI 7.x, and internal IAM-04 map onto the same claim. Derivation coverage is **instrumented, never published as conjecture**: the product reports "N claims derived from the substrate, M authored residual (governance, privacy, application controls)" per engagement, and the number becomes a research result.

**The six invariants** (the constitution; everything else is negotiable):
1. No verdict without a claim.
2. No claim without a defined population.
3. No population without a derivation rule or authoritative source.
4. No evidence without provenance and temporal semantics.
5. No PASS unless the evidence is *fit* to prove the claim.
6. **No agent may expand its own boundary.** Discovery emits `PROPOSED_SCOPE_CHANGE`; a human ratifies; the manifest versions; deterministic execution resumes.

## 2. Ontology (the type system)

**Commitment** — contract / regulation / audit / internal standard → obligation → implicated products, processes, data → boundary implication. Scope provenance reads as a chain ("in scope because Product A processes CHD under Commitment PCI-004"), never as a data-tag reflex.

**Process** — the authoring and planning plane. ITGC lanes ship as **templates** (access, change, termination, backup) instantiated per stack; freeform editing is out of V1; agent-proposed lanes are V2. Lanes carry direction, actors, triggers, and control points (the sketch's diamonds). The connectivity/boundary graph is a distinct artifact feeding discovery.

**Population** — first-class, three types:
- **Entity** (state): things that exist — repos, projects, service accounts, vendors, employees. Born from inventories; *process assigns scope-relevance* (a repo is in scope because it sits on the change lane of a committed product).
- **Event**: things that happened — terminations, changes, grants, incidents. Born from process edges; where all Type-II operating-effectiveness testing lives.
- **Relationship**: joins — user→group, repo→deployment, employee→privileged account.

Each population carries: definition, **derivation rule** (general case) or authoritative source (degenerate case), **source roles** (authoritative / contributing / corroborating / discovery / exclusion), period, size, exclusions, open deltas with owners, and an **assurance state**: `UNDEFINED → DEFINED → DISCOVERED → RECONCILED → RATIFIED → STALE`. Coverage percentages are never computed against an unratified denominator. Reconciliation is **set-based** (canonical identity, membership, intersection, left-only/right-only, conflicts, unresolvable, excluded) — counts are a smell test, not evidence. Negative-space discovery — expected sources that failed to reconcile — is the signature capability.

**Claim** — the semantic unit (above). Assertions decompose claims into lettered testable attributes (the testing-matrix structure: approval before grant; approver ≠ requester; granted = approved). Every assertion is typed: `STATE · EVENT · SEQUENCE · AGGREGATE · EXISTENCE · NON-EXISTENCE · TIMING` — the type determines what evidence *can* prove it. "User absent from GitHub today" (STATE) cannot prove "removed within five days" (TIMING); AM-06's Splunk requirement encoded this years before this PRD named it.

**Evidence Quality Contract** — identity: source, tenant/org, population ref, endpoint/query, parameters, time window, schema version, collector version, retrieved-at, auth context, contract hash. Five quality properties, each with an independent named method and independent failure mode: **provenance** (authenticated origin) · **integrity** (SHA-256 + WORM) · **population** (enumeration + pagination exhaustion + set reconciliation) · **semantics** (schema contract + sampled trace) · **temporal validity** (period represented vs. period asserted). A contract declares which assertion types it is entitled to support; a branch-protection snapshot supports configuration STATE assertions and does not automatically support "all changes were approved." Collect-once-assert-many: one snapshot feeds N assertions. (Spoken term stays **C&A** — audit-native vocabulary; the contract is its formalization.)

**Verdict vocabulary** — `PASS · FAIL · UNKNOWN · EXCLUDED · EXCEPTION`, never interchangeable. UNKNOWN carries a *why* (`UNKNOWN_DISCOVERY / _OWNER / _POPULATION / _EVIDENCE / _TESTABILITY`…), propagates, and blocks ratification unless dispositioned through the residual-acceptance path (the REI, mechanized: justification + owner + review date).

## 3. NEW — the Capability Registry (what this version adds)

The compiler needs to know, per system, **what evidence the system is capable of yielding** before it can judge fitness. That knowledge is the Capability Registry: a versioned, inspectable catalog where each entry describes one evidence surface of one system.

**Capability entry schema:**
```
system:            github | okta | workday | gcp | slack | …
surface:           REST v3 /orgs/{org}/members | SCIM | System Log API | audit-log export | UI-only
access_modes:      [direct-api, official-mcp, community-mcp, custom-adapter, playwright]
populations_yielded: entity: org members | event: audit events | relationship: team membership
attributes:        fields exposed, per population
temporal:          state-only | event-history(window=90d) | full-history | snapshot-cadence
join_keys:         email | employee_id | login | resource-id
auth_scope:        minimum read scope required (least-privilege named)
pagination:        cursor | page | none — exhaustion method
rate_limits:       …
history_caveats:   e.g., "Okta System Log retains 90 days — TIMING assertions beyond window need exported archive"
provenance:        who researched this, when, from what doc version, ratified_by
```

**How entries get made — the Cartographer agent.** An LLM-lane Sentinel agent whose job is capability research: read the vendor's API documentation and the MCP registry, enumerate surfaces, and **propose** capability entries with citations. It never probes live systems (probing is an action; actions require ratified permissions) and its proposals are drafts until a human ratifies them into the registry. This is invariant 6 applied to knowledge: *the agent maps the territory; it does not annex it.*

**How entries get verified — the Surveyor.** Once a capability entry is ratified and a read scope is granted through the manifest, a deterministic probe (not the LLM) executes the entry's enumeration once against the real tenant, records actual schema, pagination behavior, and history depth, and diffs observed-vs-documented. Drift between docs and reality is itself a finding.

**How the compiler uses the registry — the type checker.** For every (claim, assertion, population) triple, the compiler matches required evidence properties against registered capabilities and either compiles a collector or refuses with an error a human can act on:

```
E204  TIMING assertion "revoked ≤5 business days" requires historical
      transition timestamps; capability github.members (REST v3) yields
      STATE only. Satisfiable via: okta.system_log (event-history, 90d)
      + siem.github_audit (full-history). Amend manifest?
E117  Population "everyone capable of modifying production" derivation
      rule references gcp.iam + google.groups + ci.service_accounts +
      breakglass.config; capability entry missing for breakglass.config.
E302  Contract schema_version v3.1 ≠ ratified v3.0 — re-ratify or pin.
```

Compile errors are the product behaving like its name. An assurance program that cannot prove its claims **fails to compile** instead of executing and lying.

**MCP, precisely positioned.** Two directions, one rule. *Inbound:* third-party MCP servers are an access mode recorded in the registry — legitimate for the **LLM lane** (investigation, triage, capability research) and acceptable for verdict-path collection **only when pinned** (server version + tool schema hashed into the evidence contract); default verdict-path collectors are native code against versioned APIs, because an MCP tool that changes underneath you breaks reproducibility. *Outbound:* Aegis exposes its **own MCP server** — collectors as tools, evidence store as queryable resources — which is how the Overlord plans, how auditors self-serve samples, and how the Investigator build already works. MCP is in the loop, never in the verdict.

## 4. Agent architecture (the Sentinels)

| Agent | Lane | May do | May never do |
|---|---|---|---|
| **Cartographer** | LLM | research API/MCP surfaces, propose capability entries with citations | probe live systems, ratify entries |
| **Surveyor** | Deterministic | execute ratified enumeration probes, record observed capability | exceed granted read scopes |
| **Collectors** | Deterministic | retrieve per evidence contract, hash, write WORM | interpret, summarize, decide |
| **Reconciler** | Deterministic | set reconciliation, delta objects, assurance-state transitions | disposition deltas (human) |
| **Evaluator** | Deterministic | run typed assertions, emit verdicts | anything non-pure (hook-enforced at build: verdict functions must pass purity + re-performance tests) |
| **Overlord** | LLM | plan investigations over the process graph + registry via Aegis's MCP, triage UNKNOWNs, draft narratives grounded in named records, emit `PROPOSED_SCOPE_CHANGE` | record verdicts, expand boundary, grant scopes |

The process graph is the Overlord's map: which upstream system generates this population, which control point should have caught this exception, which contract sits on that edge, which collector it may ask to re-run — all within the frozen manifest.

## 5. Non-goals (guarded)

Unchanged: not a GRC platform; not a scanner; no LLM in the verdict path; not multi-tenant SaaS. Added: **not a framework-content product** (mapping tables versioned and inspectable; interpreting frameworks for customers is consulting, not product); **not an MCP aggregator** (the registry catalogs surfaces; it does not proxy them); **no freeform lane editor in V1** (templates only — if the substrate is universal, the lanes are templates by definition); **no published derivation percentage** (instrumented only).

## 6. V1 — one lane, made deliberately nasty

**The termination lane, end to end, with real populations**, per the adjudicated demo script: Workday → termination event → Okta → fan-out to GitHub, GCP, Slack — including local accounts and group-derived access — seeded with the mutation playbook's poison: one contractor absent from Workday, one dormant GitHub local account, one break-glass cloud account, one failed identity join, one delayed revocation, one legitimate exception. Acceptance = a practitioner looks at the set-reconciliation screen and says *"now I know why the population is complete,"* **and** the five verdict states render distinctly, **and** the mutation suite scores.

**V1 capability registry scope:** exactly the five systems on the lane (HRIS/Workday, Okta, GitHub, GCP, Slack), Cartographer-proposed, human-ratified, Surveyor-verified. This is the registry's own acceptance test: does E204-class checking catch the Okta 90-day log window against a six-month TIMING assertion? (It must — that's a real trap on a real lane.)

**Hard gate (unchanged, absolute):** the Assurance Manifest schema — now `boundary / populations(+derivation rules, states) / claims(+typed assertions) / evidence_contracts(+quality properties, capability refs) / capabilities / collectors(+permissions) / tests` — reconciles against the Build Execution PRD v2's plan→freeze→execute contract before any V1 persistence code. The manifest is versioned as ratified scope snapshots (v14, approver, diff), and post-freeze drift enters PROPOSED.

**Build phases on `aegis-sentinel`:**
- **P0 (now → post-Kikoff-loop):** manifest schema reconciliation; ontology as typed schemas (`src/schema/`); capability-entry format; the three HTML prototypes preserved as `docs/prototypes/` design references.
- **P1 (pre-Rudd, wk of 8/17):** termination lane — five capability entries, collectors for the lane, set reconciler, typed evaluator, lineage view (proof graph: commitment → requirement → claim → population → sources → reconciliation → contract → snapshot → assertion → verdict, every arrow typed). Mutation suite from the playbook wired into CI (`scripts/verify.sh` — the Janus loop makes the mutation suite the verify step).
- **P1.5 (post-lane-proof only):** Rudd AP lane instantiation from the template — the template thesis's first external validation; if AP doesn't fit the lane model, that's recorded as evidence, not bent around.
- **P2:** discovery feeds (CAI, GitHub org, IdP app catalog) as Surveyor inputs → PROPOSED flows; scope-delta mode for year-two engagements; Overlord planning over Sentinel-MCP.

## 7. Metrics

| Metric | Type | Definition |
|---|---|---|
| **Assurance defect detection rate** | **Headline** | mutated defects that produce compile-error / UNKNOWN / FAIL ÷ defects introduced (target: 100% on the playbook suite; any silent PASS is a build-stopping bug) |
| Population assurance states | Primary | count by ladder state; ratification blocked while any lane population < RECONCILED without dispositioned deltas |
| Evidence coverage | Primary | assertions backed by a *fit* contract ÷ testable assertions (compile-error assertions counted honestly as unfit, not hidden) |
| Compile integrity | Guardrail | zero collectors executed for claims with unresolved E-codes |
| Derivation coverage | Instrumented | derived vs. authored-residual claims, reported per engagement, never pre-published |
| Registry health | Secondary | ratified capability entries with Surveyor verification ÷ total; doc-vs-observed drift findings |

Baselines: `[NEED: hours + incompleteness findings from the last two greenfield scoping exercises — owner: the Owner; also the reference-engagement termination-population sizes for realistic V1 seed data]`.

## 8. Decisions — resolved and open

**Resolved by adjudication:** D1 bounded claim, instrumented (no percentage). D3 templates only. D5 derivation rules + source roles (authoritative source = degenerate case). D6 shallow OSCAL — serialization boundary, never the ontology; Aegis-native concepts (derivation rules, reconciliation deltas, evidence fitness, UNKNOWN provenance, ratification, drift) stay Aegis's. **D7** (Cartographer documentation-source allowlist): ruled — allowlist by rule (vendor first-party doc domains only), with a Workday unreachable-source exception; see `docs/DECISIONS.md` D7.

**Open, deliberately deferred until the lane is proven:** D2 (open schema + curated proprietary rule library is the leading option — the format wants adoption, the rules are where expertise compounds); D4 (Rudd lane instantiation — call happens regardless; lane is conditional).

---

*Invariants carried whole from the corpus: human-ratified scope, deterministic verdicts, UNKNOWN first-class — now joined by the boundary invariant. The one-sentence version of this entire document, suitable for saying out loud in a room: the agent can map the territory, propose the scope, plan the investigation, and draft the story — it cannot record a verdict, and it cannot expand its own boundary; a human ratifies, the manifest versions, and deterministic code does the proving.*
