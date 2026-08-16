# Memory & skills evaluation — 2026-08-16

An audit of whether this repo actually uses the Janus scaffold it was stamped
from: the learnings ledger, the reflect → evolve promotion loop, and the
skills. Verdict first: **the loop was wired but dead**, and this branch applies
the retroactive fixes. Companion to [EVALUATION.md](EVALUATION.md), which
covers the product side.

## Findings

### 1. The memory loop never ran

Between the initial commit (2026-07-27) and this audit, `.claude/memory/` and
`.claude/skills/` had exactly one commit each — the initial one. No commit in
the history mentions `/reflect`, `/evolve`, or `/recalibrate`. Every entry in
the ledger was authored by the janus parent; this repo had written none.

The plumbing itself was live the whole time: the Stop hook
(`stop-reflect-nudge.sh`) nudged for `/reflect` whenever signals existed, and
session-start (`session-start.sh`) reported recalibration stale on every
session — for three weeks, with no effect. Meanwhile the inner loop
(`post-edit-verify.sh` → `verify.sh quick`) demonstrably worked. Conclusion:
per-edit enforcement survives on its own; the session-level rituals do not —
they need either a provisioning ritual that seeds the habit or an operator who
answers the nudge.

### 2. Real lessons were learned — and routed around the ledger

The WO-C2 dispatch run (6d0d805 → fixed in 64b13c5) burned ~50 turns on
permission denials because its work order's verification needed a YAML parse
no allowlist entry could run. That is a textbook `/reflect` trigger
(verification failure + wasted path). The lesson was captured — but as prose
comments in `scripts/verify.sh` and `tests/test_issue_templates.py`, invisible
to the evidence-counting, promotion, and inheritance machinery. Backfilled as
L-039.

### 3. The stamp skipped every heredity transform

This repo was created by GitHub template copy, not `/replicate`, so the
transforms in `.claude/skills/replicate/SKILL.md` step 3–4 never ran:

- All 38 parent entries arrived with parent statuses (`candidate`,
  `promoted:*`) instead of `Status: inherited` — so nothing signaled that this
  repo must re-earn promotion with its own evidence.
- Three `retired` entries crossed the boundary, which the skill explicitly
  forbids.
- `sources-seen.md` kept the parent's full watermark — a `/recalibrate` here
  would have skipped living sources this repo has never read.
- The identity was never rewritten: CLAUDE.md was still titled
  "Janus (template)", the README still described the template.
- The five learned rules in CLAUDE.md arrived active without the per-rule
  user confirmation the generation gate (L-035) requires. They are kept —
  removing them now would silently change session behavior — but the gate was
  skipped, and that is recorded here rather than papered over.

### 4. Doc drift accumulated with no ledger trace

CI switched to `verify.sh full` in b46cc6b, but CLAUDE.md, ARCHITECTURE.md's
component map, and SELF-IMPROVEMENT.md still claimed CI ran the fixture suite
directly — a live violation of promoted rule L-007 (sweep every mention of a
changed convention). The component map also omitted `src/`, `tests/`,
`knowledge/`, and `pyproject.toml` entirely. `test-hooks.sh` checks names,
paths, and counts only, so CI stayed green while the prose rotted.

## What this branch fixes

1. **Retroactive heredity pass** — all surviving entries re-marked
   `Status: inherited` (parent status preserved as annotation), retired
   entries dropped, `sources-seen.md` truncated to header + marker.
2. **Identity rewrite** — CLAUDE.md, README, ARCHITECTURE.md now name
   Aegis Sentinel.
3. **Drift reconciled** — CI claims corrected everywhere, component map
   completed.
4. **Ledger backfill** — L-039 (allowlist-executable done-means) and L-040
   (template copy leaves the loop dead) authored by this repo.

## What is deliberately NOT done here

- **`recalibrated-at` is not stamped.** A stamp certifies a completed
  `/recalibrate` run (L-020: a stamp written by anything but a real run is a
  false green). No full run has happened here, so the session-start staleness
  nudge is legitimate and stays. First full `/recalibrate` is a named next
  step — it starts from the now-truncated `sources-seen.md`.
- **The five CLAUDE.md rules are not re-gated.** Flagged above; retire or
  re-confirm them through `/evolve` with the operator, not unilaterally.

## Next steps for the loop

1. Answer the nudges: run `/reflect` at session end when signals exist, and a
   first full `/recalibrate`.
2. Let `/evolve` fire naturally once a child-authored entry reaches
   Evidence ≥ 2 — no candidate qualifies today, which is correct, not a bug.
3. Feed the parent: janus's L-037 defers the self-learning efficacy question
   to "the first bootstrapped child with real task history" — this repo is
   that child. Once real build milestones accumulate (see EVALUATION.md §3),
   run the deferred baseline comparison and report observations back to the
   janus ledger.
