# Evaluation — from knowledge bundle to first build milestone

Written against the corpus landed in `knowledge/` (PR #11). North star: *compliance you can
prove* — an agentic GRC-engineering platform whose test agents automatically exercise and
validate the compliance agents. This repo is currently a thin Janus stamp (`src/aegis_sentinel/`
holds only `__init__.py`); the goal here is a decision document, not a build — no `src/` changes
land in this PR.

## 1. Adopt or rebuild

**Decision: rebuild incrementally against the corpus. Salvage the prior scaffold's static,
line-reviewable artifacts (schemas, harness *shape*) deliberately; do not merge its code or
history wholesale.**

### What exists in the prior scaffold

Per `knowledge/02_repo_knowledge/docs/PLAN.md` §2, a single Cowork session on 2026-07-25
produced, all green: three schemas (`verdict-record`, `collection-spec`, `advisory-record`)
forked from GRCEngClub's `finding.schema.json`; a verdict path (`evidence.py`, `verdict.py`,
`controls/branch_protection.py`, `completeness.py`, `probe.py`, `jit/preconditions.py`,
`oscal/exporter.py`, `db.py`, `agents/`); a 50-test harness across six suites (contract,
seeded-failure, chain-and-ledger, JIT preconditions, verdict-path purity, OSCAL-no-advisory);
CODEOWNERS over the verdict path and CI itself; and Janus vendored at `.janus/`. It exists live
and unpushed on the operator's machine, with no git remote, and is archived (with history) in
`03_archives/aegis-sentinel.zip` — deliberately not committed to this repo
(`knowledge/README.md`).

### What a rebuild loses

- **The 50-test harness**, proven green in one session — re-deriving six suites' worth of
  fixtures (contract triads, a seeded-drift collector, chain-tamper detection, AM-05 deny
  paths, an AST-level import-purity check, an OSCAL-advisory exclusion test) is real,
  non-trivial work that already exists.
- **CODEOWNERS discipline already wired to real paths** — `src/verdict.py`, `src/evidence.py`,
  `src/db.py`, `src/probe.py`, `src/completeness.py`, `src/controls/**`,
  `src/jit/preconditions.py`, `src/oscal/**`, seeded fixtures, and CI itself
  (`Sentinel_Build_Execution_PRD.md` — see `knowledge/01_corpus/04_build_prds/`). Standing this
  up again is mechanical but not free.
- **Day-one velocity** — the schemas are already fork-and-delta'd from a real external
  contract (GRCEngClub's `finding.schema.json`) rather than designed from a blank page, which
  the corpus itself calls the #1 blocker converted "from a design task to an editing task."

### What importing wholesale would carry in unexamined

- **Unratified code, not just unratified docs.** The corpus's own discipline (see
  `knowledge/02_repo_knowledge/docs/corpus-index.md` on `Aegis_RedTeam_Reconciliation.md` §2)
  is that claims must cite a corpus path, never be re-imported from memory — "the one
  regression the red-team round produced was a matrix that quietly re-imported memory as
  citation." The prior scaffold's 3,000+ lines of Python were written in one session against
  the corpus as it stood on 2026-07-25 and have never been reviewed line-by-line in *this*
  repo (that review is precisely what the `verdict-path-review` skill in
  `knowledge/02_repo_knowledge/claude-skills/` exists to do, and it has not run here). Bulk
  import would make that skipped review permanent by fiat.
- **Possible pre-correction facts baked into logic.** The corpus's own
  `Version_Drift_Ledger.md` records that several facts changed underneath earlier corpus
  drafts on the same date the scaffold was built (S3 Object Lock retrofit, the AWS
  `UserStatus` enum, GitHub fine-grained-token read-only access). Whether the scaffold's
  collector logic reflects the corrected or the stale version of any of these is unverified
  from this repo — it can only be checked by reading the scaffold's code against the ledger,
  which is exactly what porting-with-review does and bulk-copying does not.
- **A structural mismatch this repo has already made deliberately.** The prior scaffold uses
  a flat `src/` layout (`src/verdict.py`, `src/controls/branch_protection.py`); this repo is a
  src-layout package, `src/aegis_sentinel/...` (`pyproject.toml`). Every prior-scaffold path
  needs rewriting regardless of adopt-or-rebuild, so "wholesale import" is never actually a
  zero-cost drop-in.
- **A second, possibly stale Janus copy.** The prior scaffold vendors Janus at `.janus/` as
  build-plane-only tooling. This repo *is* a live Janus-based project already (root
  `CLAUDE.md`, `.claude/`). Importing the archive would either silently reintroduce a
  vendored Janus copy alongside the live one or require deleting it — an unexamined merge
  conflict this repo's own instructions warn against carrying in silently.
- **A `CLAUDE.repo-copy.md` that must stay inert.** The bundle already renamed the prior
  scaffold's `CLAUDE.md` files to `.repo-copy.md` specifically so a Claude Code session in
  this repo never loads them as live instructions (`knowledge/README.md`). Importing the
  scaffold's *code* without importing its *CLAUDE.md* is exactly the "adopt the artifact,
  reject the trust model" split this evaluation applies elsewhere (§2) — consistency argues
  for treating the whole scaffold the same way, not exempting the code half.

### Why rebuild wins here

This repo's own learned rules already answer the general form of this question:
"a mechanism — tool, file, cap, fallback — enters the scaffold only after dogfooded use
demonstrates the need" and "before encoding a mechanism, check whether the platform provides
it natively" (root `CLAUDE.md`, L-014/L-015). Importing a fully-built verdict path before this
repo has run a single fixture against it is the mechanism-before-need pattern those rules exist
to block, just applied to product code instead of scaffold code. The corpus's own review of
GRCEngClub (§2 below) models the right posture: treat *any* prior implementation — theirs or
this project's own prior session — as prior art to consult and selectively fork, not a base to
merge. Concretely: pull `finding.schema.json`-derived schemas and the fixture-triad CI *shape*
into this repo as freshly-authored, line-reviewed files citing their corpus and scaffold
provenance; re-author the verdict path itself inside `src/aegis_sentinel/` control-by-control,
each port checked against the current (post-correction) corpus and proven by its own seeded
fixture — which is what §3's milestone below does for exactly one control.

## 2. External prior art stance

### GRCEngClub `claude-grc-engineering` — evaluable from the corpus; network read blocked, corpus read is sufficient

`knowledge/01_corpus/05_prior_art/Aegis_Prior_Art_GRCEngClub_Toolkit.md` is itself a verified
review (a live clone at commit depth-1, dated 2026-07-24, with claims traced to specific files —
`plugins/connectors/*/scripts/collect.js`, `schemas/finding.schema.json`,
`docs/ARCHITECTURE.md`, `docs/SCF-ATTRIBUTION.md`) rather than a secondhand summary, so this
evaluation adopts its findings directly instead of re-deriving them. A live re-fetch was
attempted for currency (see the AI-SAFE2 subsection below for why it failed) and is unnecessary
here regardless: the corpus document is pinned to a commit, which is the correct posture for a
pre-1.0, moving repository (`L-044`) — a fresher network read would only be a *different*
snapshot, not a more authoritative one, unless this repo is re-adopting from it, which is out of
scope for this evaluation.

**Adopt** (priority order, per the corpus doc §3 and §5):

1. **Finding schema conventions**, forked into this repo's own `verdict-record.schema.json`:
   `const`-pinned `schema_version`, `additionalProperties: false` everywhere, `allOf`/`if`/`then`
   conditional requirements (status=fail → message+severity required), the
   `source`+`source_version`+`run_id`+`collected_at` reproducibility tuple, `severity`
   independent of `status`. Add the Aegis-specific deltas the corpus already specifies:
   `record_hash`+`chain_prev` (D-1), `population_id`/`population_count`/`completeness_ref`,
   `spec_id`+`spec_hash`, `test_function_version`, `ratification_ref`.
2. **Status-enum handling, not the enum itself.** Their `inconclusive` maps only to D-7's
   basis-missing family — adopting it as-is would recreate the single-queue judgment funnel
   D-7 exists to prevent. Keep PASS/FAIL/UNKNOWN with a required `unknown_cause`; adopt their
   `not_applicable` (with a required `ratification_ref`); reject `skipped` outright — a
   population-testing system has no legitimate skip that isn't `not_applicable` or a
   completeness failure.
3. **The ajv contract-test CI harness and fixture-triad layout**
   (`validate-json-schema.cjs`, their fixture-validation shell entry point, per-connector
   `001-*-pass.json`/`002-*-fail.json`/`003-*-inconclusive.json`) as the skeleton for this
   repo's own seeded-failure harness — lighter than what Aegis needs (their fixtures prove the
   schema accepts a shape; this repo's must prove the test *function* detects a seeded defect),
   but the CI wiring and validation scripts transfer directly.
4. **The SCF crosswalk (`GRCEngClub/scf-api`)**, consumed as a one-time-fetched, SHA-256'd,
   pinned-release artifact — never a live runtime dependency in the verdict path. CC BY-ND:
   attribute, never modify.
5. **The connector exit-code bar**, with exit `4` ("partial") explicitly flagged as their
   fail-silent trap: a partial collection must become a hard `UNKNOWN(basis_missing)` at
   population level here, never a partial pass.
6. **The `fedramp-20x` update-hook pattern** (`hooks/hooks.json` +
   `scripts/check-fedramp-updates.js`) as a working template for this repo's own recalibrate
   heartbeat against the pinned SCF release and the authoring corpus.

**Reject wholesale:** their trust model (`evidence_refs` resolve into a mutable,
user-writable `~/.cache/claude-grc/` — no hash at intake, no WORM, no chain, no frozen spec, no
ratification); the persona-skill judgment pattern (`grc-auditor`'s `evidence-validator` has an
LLM assess evidence "completeness, timeliness, relevance, and authenticity" and emit a
conclusion — exactly the LLM-judgment-inside-a-verdict pattern this project's verdict boundary
exists to exclude); sampling language (`control-tester`'s "appropriate sample sizes" contradicts
this project's 100%-population-by-construction stance); and `--fix-failures` auto-remediation
(segregation-of-duties failure — the thing that asserts cannot be the thing that remediates).
Pin any adopted artifact by commit hash, not branch — the repo is pre-1.0 and moving (v2 RFC
accepted 2026-04-30, directory restructure pending).

### AI-SAFE2 framework (`CyberStrategyInstitute/ai-safe2-framework`) — gap, recorded honestly

The corpus contains **zero references** to AI-SAFE2 or CyberStrategyInstitute — not in the
23-doc corpus, `INDEX.md`, `PLAN.md`, the corpus index, or the 49-entry learnings genome
(verified by grepping the entire `knowledge/` tree for `AI-SAFE2`, `ai-safe2`, `SAFE2`, and
`CyberStrategyInstitute`: no hits). This evaluation attempted a live read of
`github.com/CyberStrategyInstitute/ai-safe2-framework` twice — once via `WebFetch` (denied:
permission not granted in this sandboxed run) and once via a direct `curl` from `Bash` (blocked:
required approval this environment does not grant to network calls). Both attempts failed before
retrieving any content.

**No stance is taken on AI-SAFE2 here, by design — per this evaluation's own instructions, a
repo that could not be read must not be summarized.** This is an honest gap, not a decision this
evaluation is positioned to make: the operator has network access this sandbox does not, and can
either point Claude Code at it in a follow-up session or paste the relevant excerpts into a
future work order. Flagging this rather than fabricating a "GRCEngClub-style" review is itself
an application of the corpus's own citation discipline (§2's opening paragraph, above) — the
mistake the red-team round already caught once was exactly memory standing in for citation.

## 3. First build milestone

**Milestone: one control, ported and provably tested end-to-end — the smallest slice where a
deterministic test proves a compliance verdict is real, not vibes.**

### Why this is the smallest testable slice

The north star is agents that test the compliance agents. At the scale of a first milestone,
before any LLM investigator layer exists to test, the smallest faithful instance of that idea is
the corpus's own **Troublemaker** pattern in miniature (`04_build_prds/Sentinel_Build_Execution_PRD.md`
§8, level 4): seed a drift, assert the system turns red, restore. A single control with a single
seeded-failure fixture *is* one full plan→verdict cycle with automated proof of detection — the
deterministic seeded-fixture test is the test agent at this milestone's size, honestly named as
such rather than inflated into an LLM claim this milestone doesn't yet make. This also matches
the corpus's own recommended entry point: `branch_protection` is named as "the first ported
evaluation" in `PLAN.md` §2, and its schema and constraint lane are already fully specified
(`API_Constraints_By_Trust_Consequence.md`, `SOC2_Control_Testing_Matrix.md`'s AM-01 attributes).

### Scope

1. `schemas/verdict-record.schema.json` (v0.1.0) — freshly authored in this repo, citing
   `knowledge/01_corpus/05_prior_art/Aegis_Prior_Art_GRCEngClub_Toolkit.md` §3.1 for the forked
   conventions and this evaluation's §2 for the adopted deltas (`record_hash`, `chain_prev`,
   `population_id`/`population_count`/`completeness_ref`, `spec_id`/`spec_hash`,
   `test_function_version`, `ratification_ref`, `unknown_cause`).
2. `src/aegis_sentinel/controls/branch_protection.py` — one pure deterministic function
   returning `PASS`/`FAIL`/`UNKNOWN(+cause)`, no AI-client import anywhere in its module or its
   callers.
3. One seeded-failure fixture under `tests/fixtures/seeded/` reproducing a real branch-protection
   drift (e.g. a required status check silently removed), plus a test that fails if the control
   does *not* detect it — the collector proving it can turn red.
4. An AST-level purity test (this repo's analogue of `test_verdict_path_purity.py`) asserting no
   AI-client import anywhere in the verdict path, wired as a required check.
5. CODEOWNERS entries over the new schema, control module, and seeded fixtures — the discipline
   from §1, applied to exactly the files this milestone creates, not pre-emptively over files
   that don't exist yet.

### Done means (for the future work order that carries this milestone)

- `schemas/verdict-record.schema.json` validates a PASS, a FAIL, and an UNKNOWN fixture for
  branch protection, and rejects at least one deliberately invalid fixture (closed schema,
  `additionalProperties: false` holds).
- `src/aegis_sentinel/controls/branch_protection.py` is a pure function: given a fixed input
  (a captured branch-protection API response), it returns the same verdict every time, with no
  network or AI-client call inside it.
- The seeded-failure fixture test fails (i.e., correctly reports the injected drift) before any
  fix is applied to the fixture, and passes once the fixture is restored — the detection proof
  the corpus requires before any collector merges.
- The purity test and the schema-contract test are both wired into `scripts/verify.sh full` and
  green.
- CODEOWNERS covers the new files.
- `scripts/verify.sh full` is green on the PR that carries this milestone.

Everything past this — the second control, the LLM investigator/advisory lane, the JIT module,
webhooks, OSCAL export — is explicitly out of scope for the milestone itself; it is the next
work order, not this one.
