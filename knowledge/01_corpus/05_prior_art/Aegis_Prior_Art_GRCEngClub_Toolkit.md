# Aegis — External Prior Art: GRC Engineering Club `claude-grc-engineering`

**Status:** Reviewed 2026-07-24 · quarantined external source, verified against live repo at commit depth-1 clone (main, 795 files, 65 registered plugins)
**Source:** `github.com/GRCEngClub/claude-grc-engineering` (flagship open-source project of grcengclub.com) + `github.com/GRCEngClub/scf-api`
**Purpose:** What the toolkit contributes to the Aegis build PRD, what it must not contribute, and the execution sequence for adoption. All claims below are read directly from repo files; nothing is recalled from memory. External rows are quarantined per corpus source discipline — none of this enters a design document as a corpus citation until ratified.

---

## 1. Verdict

The toolkit is the closest public prior art to Aegis's plan-and-investigate lane, and its **Finding schema v1.0.0 is a direct, forkable answer to Aegis's single highest-leverage blocker** — the absence of machine-readable schemas. It is *not* prior art for the verdict path: it has no hashing, no WORM, no freeze, no completeness assertion, and its persona skills put LLM judgment inside audit conclusions in exactly the pattern D-5 prohibits. Adopt the contracts, the CI harness, and the crosswalk infrastructure; reject the trust model wholesale.

The structural finding that matters most: **their collectors and gap-assessment are deterministic Node scripts with zero LLM calls** (verified by grep across `plugins/connectors/*/scripts/collect.js` and `plugins/grc-engineer/scripts/gap-assessment.js`). The LLM lives in the command/skill markdown layer that orchestrates the scripts. So the toolkit independently arrived at Aegis's two-verb split — agent orchestrates, code executes — but with no trust boundary between the layers: nothing is frozen, ratified, or hashed, and the orchestration can silently change what the deterministic layer is pointed at between runs. This is Aegis's architecture minus the property that makes it survive hostile re-performance. That gap is both the reason not to depend on their runtime and the exact shape of the public contribution Aegis can make back (§6).

---

## 2. What the repo is

A Claude Code **plugin marketplace** (65 plugins in `marketplace.json`) in five categories, per `docs/ARCHITECTURE.md`:

- **Engineering hub** (`grc-engineer`): cross-cutting commands — `gap-assessment`, `test-control`, `collect-evidence`, `monitor-continuous`, `map-controls-unified`, `scaffold-framework` — backed by deterministic JS in `scripts/` and `src/`.
- **Framework plugins** (~30): `soc2`, `us-sox`, `fedramp-rev5`, `fedramp-20x`, `nist-800-53`, `iso27001`, plus regional coverage. Each is commands + a `SKILL.md` carrying paraphrased domain knowledge (deliberately never verbatim standard text).
- **Connector plugins** (14+): `aws-`, `gcp-`, `azure-`, `okta-`, `github-`, `wiz-`, `snowflake-inspector`, etc. Deterministic collect scripts emitting schema-conformant Findings.
- **Persona plugins**: `grc-auditor`, `grc-internal`, `grc-tprm` — LLM workflow orchestration.
- **OSCAL/FedRAMP plugins**: wrap `oscal-cli`; `gap-assessment` can emit `oscal-ar` output natively.

The **data contract** is `schemas/finding.schema.json` v1.0.0: every connector emits Findings; `gap-assessment` is a validated join of Findings × SCF crosswalk → report. CI (`contract-test.yml`) validates fixture files against every schema on any PR touching `schemas/` or `plugins/connectors/` — a required-status-check gate structurally identical to the one the Sentinel Build Execution PRD v2 specifies.

The **crosswalk layer** is the Secure Controls Framework via `GRCEngClub/scf-api`: a static JSON API (GitHub Pages, auto-synced weekly from the official SCF workbook) exposing 1,468 controls × 33 families × 249 framework crosswalks, plus 5,776 assessment objectives, 303 evidence-request entries, and 1,305 compensating-control mappings. Licensing is CC BY-ND — fetch, attribute, never modify (`docs/SCF-ATTRIBUTION.md`).

---

## 3. Adopt: five artifacts, in priority order

### 3.1 Finding schema → seed for the Aegis verdict-record schema (unblocks the #1 blocker)

The corpus audit identified the verdict-record and collection-spec schemas as the highest-leverage missing artifacts. `finding.schema.json` is a mature, CI-enforced JSON Schema (draft 2020-12) whose *conventions* transfer even where its *semantics* don't:

**Steal the conventions:**
- `schema_version` as a `const`-pinned semver with the stated rule "consumers pin a major version" — solves verdict-record versioning discipline in one field.
- `additionalProperties: false` everywhere — closed schemas, no silent field drift.
- Conditional requirements via `allOf`/`if`/`then`: `status=fail` → `message` + `severity` required; `status=inconclusive` → `message` required. This is exactly the mechanism to encode Aegis's rule that FAIL and UNKNOWN verdicts must carry support (field values + record hashes) while PASS may be terse.
- `source` + `source_version` + `run_id` + `collected_at` as the minimum reproducibility tuple.
- `severity` independent of `status` — their rationale ("a passing critical-severity control still tells the consumer what the stakes are if it regresses") maps cleanly onto Aegis severity caps in the human-attest lane.
- `evidence_refs` as typed pointers to backing artifacts — the same pointer-not-payload discipline as Aegis's agent-returns-pointers rule, though theirs point at a mutable cache (see §4).

**Add what Aegis requires and they lack** (this delta *is* the verdict-record spec, and drafting it enumerates most of the missing 12-field audit-trail schema in the same pass):
1. `record_hash` (SHA-256 of the evidence record at intake) and `chain_prev` (hash-chain link per D-1).
2. `population_id`, `population_count`, `completeness_ref` — their schema is **resource-centric** (one resource, N evaluations) with no population concept at all; Aegis verdicts are population-scoped assertions and cannot omit this.
3. `spec_id` + `spec_hash` — the frozen collection spec that produced the record. Their `run_id` says *when*; it cannot say *under what ratified plan*.
4. `test_function_version` — the versioned pure function that emitted the verdict, with its seeded-fixture reference.
5. `ratification_ref` — pointer to the hashed human sign-off (feeds the ratification-workflow design).

**Status-enum reconciliation:** their `pass | fail | not_applicable | inconclusive | skipped` vs Aegis `PASS | FAIL | UNKNOWN`. Their `inconclusive` is explicitly scoped ("the tool *tried* and *couldn't determine*: dropped API call, missing permission, rate-limited") — that is precisely and *only* D-7's basis-missing family. It does not cover identity-fuzzy or no-basis-anywhere. Adopting their enum as-is would recreate the single-queue judgment-funnel risk D-7 exists to prevent. Correct move: keep the Aegis triad, add `unknown_cause ∈ {basis_missing, identity_fuzzy, no_basis_anywhere}` as a required companion field when `status=UNKNOWN`, and adopt their `not_applicable` (scoped out by ratified judgment, with `ratification_ref` required) — a state the corpus currently leaves implicit. Reject `skipped` ("intentionally skipped by user config"): a population-testing system has no legitimate skip state that isn't either `not_applicable` or a completeness failure.

### 3.2 Contract-test CI harness → seeded-failure fixture harness skeleton

`tests/` contains a working ajv harness (`validate-json-schema.cjs`, `validate-contract-fixtures.sh`, `schema-validator.test.mjs`) plus **per-connector fixture triads** — most connectors ship `001-*-pass.json`, `002-*-fail.json`, `003-*-inconclusive.json` — wired as a required status check on any schema- or connector-touching PR. This is a lighter cousin of Aegis's seeded-failure discipline (their fixtures prove the *schema* accepts the shape; Aegis's must prove the *test function* detects the seeded defect), but the CI wiring, fixture layout, and validation scripts are directly liftable. Standing this up against Aegis's own schemas is roughly a day of work once 3.1 exists, and it delivers the fixture-harness backlog item with the enforcement mechanism already the one Sentinel PRD v2 ratified (fixture tests as required status checks).

### 3.3 SCF static API → the cross-framework crosswalk, frozen at intake

Aegis's delta-library approach (FedRAMP and SOX libraries referencing SOC 2 IDs) currently has no machine-readable mapping layer. The scf-api gives one for free, and — critically — it is **compatible with the deterministic lane**: static JSON files, versioned by upstream quarterly releases, fetchable once, hashable at intake, and frozen for the audit period. Consume it as a WORM-intaken artifact with a pinned hash, never as a live runtime dependency; that keeps a moving external mapping out of the verdict path while still eliminating the homegrown-crosswalk maintenance burden. Their own SOX plugin documents that the SCF→SOX crosswalk is deliberately thin (4 SCF controls) because SOX's control substance lives in COSO/COBIT/TSC — which independently confirms the Aegis decision to build SOX as a delta on SOC 2 rather than a standalone library. Secondary win: the 303 evidence-request entries and 5,776 assessment objectives are high-quality seed material for drafting Wave 1 Skills (AM-06/AM-03/AM-02), subject to the agent-drafts/human-ratifies rule.

### 3.4 Connector quality bar → constraint-ledger rows

Their ten-requirement connector bar (`docs/ARCHITECTURE.md`) is a good operational floor and maps directly onto the fail-loud/fail-silent sort in `API_Constraints_By_Trust_Consequence.md`. The structured exit codes (`0` success, `2` auth, `3` rate-limited, `4` partial, `5` not installed) make auth and rate-limit failures fail-loud by construction — adopt. But **exit `4` (partial) is the fail-silent trap in their model**: a partial collection surfaced as an exit code with the run continuing is exactly the completeness leak Aegis's intake runner must convert into a hard UNKNOWN(basis_missing) at population level, never a partial-pass. Write that as a deterministic runner assertion, not a convention.

### 3.5 fedramp-20x update hook → Janus recalibrate implementation

`plugins/frameworks/fedramp-20x/` ships `hooks/hooks.json` + `scripts/check-fedramp-updates.js` — an auto-sync hook that checks the official FedRAMP docs repo for drift against the plugin's cached policy data. This is a concrete, working implementation of exactly what the corpus specifies as Janus's recalibrate heartbeat for drift-sensitive authoring documents (and the Version_Drift_Ledger's moving-target problem: RFC-0024 softening, 20x KSI evolution). Port the pattern, point it at the Aegis authoring corpus.

---

## 4. Reject or quarantine

**The trust model.** Their reproducibility claim is `run_id` + `source_version` + cache paths. `evidence_refs` point into `~/.cache/claude-grc/` — a mutable, user-writable directory with no integrity protection. No hash at intake, no WORM, no chain, no frozen spec, no ratification. None of this survives a hostile assessor re-performing independently. Adopt the fields; do not import the claim that they constitute reproducibility.

**`evidence-validator` and the persona-skill judgment pattern.** `plugins/grc-auditor/skills/evidence-validator/SKILL.md` has the LLM assessing evidence "completeness, timeliness, relevance, and authenticity" and emitting review memos with validation results. This is LLM judgment inside an audit conclusion — the pattern the Aegis verdict boundary exists to exclude, and a cousin of the computer-use-for-ITGC contradiction already flagged in `Contradictions.md`. In Aegis, this activity is legal only as investigation-lane narrative attached to an UNKNOWN, never as an assertion. Same disposition for `finding-generator`.

**Sampling.** `control-tester` recommends "appropriate sample sizes and selection methods." Aegis is 100% population by construction; sampling language must not leak into any Skill drafted from their material.

**`--fix-failures`.** `test-control` offers auto-remediation inside the testing tool. Segregation-of-duties failure: the thing that asserts cannot be the thing that remediates. Aegis/Sentinel already has this right — remediation is a drafted PR that passes through the change-management control the tool itself audits. Keep it that way.

**Their architecture-v2 direction (dashboards, reporting, meetings, programs).** Fine for their audience; out of scope for Aegis's PRD. The one exception: their `exception.schema.json` and `grc-data/` user-owned-state conventions are worth a look when designing the clerical-review queue and human-attest lane records.

---

## 5. Execution sequence

Ordered to preserve the corpus-audit unblocking sequence (schemas → ratification → fixtures → Wave 1), with this source slotted in as accelerant rather than new scope:

1. **Now — verdict-record schema (fork-and-delta).** Copy `finding.schema.json` into the Aegis repo as `schemas/verdict-record.schema.json` @ 0.1.0, apply the §3.1 deltas, mark provenance in the header. Do collection-spec and freeze-bundle schemas in the same conventions (const-pinned version, closed objects, if/then conditionals). This converts the #1 blocker from a design task into an editing task and forces enumeration of the 12-field audit-trail schema as a side effect.
2. **Same pass — resolve the status-enum decision as a D-ledger entry.** PASS/FAIL/UNKNOWN(+cause)/NOT_APPLICABLE(+ratification_ref); `skipped` rejected with rationale. Small, ratifiable, and it locks D-7 semantics into the schema layer where they can't drift.
3. **Next — lift the CI harness.** Port `validate-json-schema.cjs` + fixture-triad layout; write the first Aegis fixture triads for the Wave 1 controls; wire as required status checks. This is the seeded-failure harness skeleton, upgraded from schema-conformance to detection-proof as the test functions land.
4. **Intake the SCF crosswalk as a frozen artifact.** One-time fetch of the relevant crosswalk JSONs (SOC2-TSC, FedRAMP baselines, SOX), SHA-256 at intake, pinned upstream release recorded in the Version Drift Ledger. Use evidence-requests/assessment-objectives as Skill-draft seeds for AM-06/AM-03/AM-02 under agent-drafts/human-ratifies.
5. **Port the update-hook pattern into Janus** as the recalibrate heartbeat against the pinned SCF release and FedRAMP docs.
6. **Add the exit-code/partial-collection rule** to `API_Constraints_By_Trust_Consequence.md` as a fail-silent row with its deterministic-assertion resolution.

## 6. The strategic angle (portfolio, not architecture)

The club's connector quality bar has **no integrity requirement** — nothing about hashing, immutability, chain of custody, or completeness assertion. That is the precise gap between "GRC engineering toolkit" and "audit-reliable evidence system," and it is the gap Aegis exists to close. A contribution back — a documented "verdict-grade connector" profile, or an integrity-extensions RFC against their Finding schema (hash, population, spec-reference fields as an optional conformance tier) — would be a public, reviewable artifact placed directly in front of the exact community and hiring audience the project targets, and their `CONTRIBUTING.md` names connectors and schema work as the primary contribution paths. Their contract-test CI means any such PR gets validated by the same mechanism Aegis uses internally. This is the highest-leverage portfolio move the source offers; it costs almost nothing beyond work already sequenced in §5.

Secondary: the club's CGE-AUD Auditor Specialty credential and the Academy exist; not evaluated here, flagged only as career-adjacent.

---

*Source caveat: all repo claims verified against a live clone on 2026-07-24. The repo is pre-1.0 and moving (v2 RFC accepted 2026-04-30; directory restructure pending) — pin any adopted artifact by commit hash at intake, not by branch. SCF data is CC BY-ND: attribute, never modify.*
