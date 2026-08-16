# Aegis Sentinel — Claude Code context

Deterministic GitHub compliance sentinel. Agents plan and investigate;
versioned pure functions decide. Re-performability, not accuracy, is
what auditors buy.

## Knowledge layout — read in this order

1. This file (invariants, commands).
2. `docs/PLAN.md` — the build plan: day-by-day sequence, EngClub
   adoption status, Janus experiment protocol, open [NEED] items.
3. `docs/corpus-index.md` — reading map for the 23-doc authoring corpus
   at `~/PycharmProjects/aegis-corpus/` (hash-manifested; verify with
   `shasum -a 256 -c MANIFEST.sha256`). Cite corpus paths in reviews
   and decisions, never memory.
4. `.claude/memory/LEARNINGS.md` — the learnings genome: append-only,
   evidence-gated environmental facts (API quirks, platform limits).
   Check it BEFORE touching any external API; append to it after.
   CANDIDATE → PROMOTED only via a named passing fixture test.

## Project skills

- `port-collector` — porting gh-ec-audit audits / authoring collectors
- `verdict-path-review` — line-by-line checklist for CODEOWNERS paths
- `ratify` — F-4 ratification workflow (agent drafts, the Owner ratifies)

## Invariants (never negotiate these in code you write or accept)

- Every PASS/FAIL/UNKNOWN is produced by a plain deterministic function
  in src/verdict.py or src/controls/. No AI client import anywhere in
  the verdict path — tests/test_verdict_path_purity.py enforces this
  and MUST stay green. New src modules get registered there and in
  .github/CODEOWNERS, deliberately.
- Agent output is advisory-record only (schemas/advisory-record.schema.json),
  never record_type=result, never in OSCAL export (F-7,
  tests/test_oscal_no_advisory.py).
- Every collector ships with a seeded failing fixture it must detect
  (tests/fixtures/seeded/). No detection proof, no merge.
- Partial collection is UNKNOWN(basis_missing) at population level,
  never a partial pass (src/completeness.py).
- Baselines, specs, rosters, allowlists take effect only via human
  ratification of a hash (F-4). Agent may draft; only the Owner ratifies.
- UNKNOWN always carries a D-7 cause family: basis_missing |
  identity_fuzzy | no_basis_anywhere. UNKNOWN never maps to satisfied.
- schemas/ are closed (additionalProperties:false) and const-pinned;
  invalid/ fixtures must be REJECTED by tests — never "fix" a failing
  invalid-fixture test by loosening the schema.
- .janus/ is the vendored build-plane scaffold. Never import it into
  src/; it never appears in the runtime diagram.

## Commands

- Test: `pip install -e ".[dev]" && pytest` (all suites are CI
  required status checks; green means: contract triads valid,
  invalid fixtures rejected, seeded drift detected, chain tamper
  named, AM-05 deny paths fire, purity holds, F-7 holds)
- Corpus integrity: `cd ~/PycharmProjects/aegis-corpus && shasum -a 256 -c MANIFEST.sha256`

## Current state / next tasks (see docs/PLAN.md §4-§6)

1. Push to private repo vinylfigure/aegis-sentinel; branch protection:
   1 review, required check "contract-tests", CODEOWNERS, no force push.
2. Create vinylfigure-fixtures org; tag fixture repos aegis-fixture.
3. SCF crosswalk intake: fetch SOC2-TSC/FedRAMP/SOX crosswalk JSONs from
   GRCEngClub/scf-api, SHA-256 at intake, pin upstream release, record
   in Version Drift Ledger. CC BY-ND: attribute, never modify.
4. Port collectors per PLAN.md §5 day-by-day (use `port-collector`);
   Janus experiment per §7 with time-per-port recorded.
