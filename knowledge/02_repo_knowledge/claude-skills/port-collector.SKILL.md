---
name: port-collector
description: Port a gh-ec-audit audit (or author a new collector) into src/controls/ with completeness envelope, seeded-failure fixture, and evidence-gated learning capture. Use when porting audits 1-9, adding any new control evaluation, or when the user says "port", "new collector", or "add a control".
---

# Port a collector

Each port is the same shape. Follow it exactly; the repetition is the point — deviations are where fail-silent bugs live. Record wall-clock start/end per port in `.claude/memory/PORT_TIMINGS.md` (the Janus time-per-port curve is the honest answer to whether the genome accelerates anything).

## Procedure

1. **Read the source behaviour.** For gh-ec-audit ports: read the Rust module (`obelisk/gh-ec-audit`, vendored or cloned read-only) and state in one paragraph what population it tests, which attributes, and what PASS means. Do not port code idioms; port behaviour.
2. **Check the genome first.** Read `.claude/memory/LEARNINGS.md` for every endpoint you are about to touch. If a PROMOTED entry covers it (pagination basis, 404 semantics, count endpoints), apply it without re-deriving.
3. **Draft the collection spec** as JSON conforming to `schemas/collection-spec.schema.json`, status `draft`. Triage every endpoint into its failure lane:
   - lane1_fail_loud (endpoint paths, params — wrong = throws; safe to iterate on)
   - lane2_runner_assert (pagination truncation, 404-for-403, count mismatches — wrong = plausible wrong answer; must be a deterministic runner assertion)
   - lane3_human_owned (tolerance semantics, approver definitions, authoritative source)
   The spec takes effect only when the Owner ratifies its hash (use the `ratify` skill). Never execute a draft spec against a real org.
4. **Write the evaluation** in `src/controls/<name>.py`: pure function `evaluate(observed, baseline, evidence_hash) -> list[Verdict]`, with `TEST_FUNCTION_VERSION` bumped on every behaviour change. Rules that are not negotiable:
   - `observed is None` → UNKNOWN(basis_missing), never PASS, never guessed FAIL
   - partial population → the caller raises via `src/completeness.py`; never emit per-record verdicts over an unproven population
   - no AI client import (tests/test_verdict_path_purity.py will block the merge; also register the new file in its VERDICT_PATH_FILES list and in .github/CODEOWNERS)
5. **Write the seeded-failure fixture** in `tests/fixtures/seeded/`: a drifted state this collector MUST turn red on, plus a clean state, plus the None/missing case. Add the triad to `tests/fixtures/verdict-record/` (pass/fail/unknown) and at least one `invalid/` rejection case if the control introduces new schema surface.
6. **Run `pytest`.** Green includes: your seeded drift detected, invalid fixtures rejected, purity suite passing with your file registered.
7. **Capture learnings.** Anything the port taught about the API (a lying count field, an undocumented 404, a pagination quirk) is appended to `.claude/memory/LEARNINGS.md` as CANDIDATE. It becomes PROMOTED only by naming the passing fixture test that demonstrates it — plausible-sounding folklore stays CANDIDATE forever.
8. **PR.** One collector per PR. The PR description states: population, completeness basis, failure-lane table, seeded fixture name, and any genome entries added.

## Hard fences

- Janus/`.janus/` and this skill operate in the build plane only. Nothing here runs in the verdict path at runtime.
- The agent (you) drafts specs and code; the Owner ratifies specs and reviews verdict-path PRs. Do not merge your own verdict-path change, and do not mark a spec ratified yourself.
