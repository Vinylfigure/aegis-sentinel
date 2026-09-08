# Merge policy — pinned to the fleet contract

Policy-version: 2
Engine-sha256: 76cd849946753d86d68118330daf5e37004bf9161e24800384ea2993d3bc8a5a

The boundary is stated in Vinylfigure/overlord `docs/MERGE-POLICY.md`: maintenance-
grade work builds and merges itself; only work that needs a human decision waits
for one. This file pins the engine body this repo's `scripts/auto-merge.sh` carries.
Everything below the `# janus:merge-config:end` sentinel in `scripts/auto-merge.sh`
is the shared engine — the sha above is
`sed -n '/^# janus:merge-config:end/,$p' scripts/auto-merge.sh | shasum -a 256` —
and `scripts/test-hooks.sh` recomputes it: a copy that drifts from it is drift, not
a local policy, and the fixture suite goes red.

## This repo's configuration block

- Merge method `merge` (this repo's history is merge commits, never squashes).
- Eligible head prefixes: `claude/ fix/` — 58 of the 59 heads ever merged here are
  `claude/<issue>-<slug>` (dispatched task work) or `claude/<date>-heartbeat-reflect`
  (ledger notes, which the fleet policy says self-merge). `intent/` and `heartbeat/`
  are never eligible; an unknown prefix is skipped loudly.
- A linked issue is optional: dispatched PRs cite their task as `Closes #N`,
  heartbeat reflects close nothing. When one is linked it must be open, not
  Intent-tier, and free of gating labels.

## The ready step

`scripts/ready-drafts.sh` (byte-identical to janus's) runs before the engine in the
same firing and marks ready for review only a draft the engine would merge next — a
head in this repo's `ELIGIBLE_PREFIXES` (read from the engine's own config block, so
the two never disagree), base on `main`, green, `MERGEABLE`, no gating label, quiet
for `READY_QUIET_HOURS` (default 2), and carrying no recorded ask (`janus:ask:v1`),
held-for-operator marker or engine hold. Dispatched runs open every PR as a draft
first (L-097); this step is that draft's exit. **The recorded ask is the hold
signal, never the draft flag.**

## What stays the operator's here

Everything the fleet policy names (a draft with a recorded hold, a red or invisible
check, a gating label, a grant-widening or gate-loosening diff, a read the engine
could not complete), plus two settings this arm depends on and cannot see:

- **Branch protection (issue #20) must not require an approving review.** GitHub
  forbids self-review on a single-owner repository, so a required approval
  deadlocks every PR the arm serves (L-116). Require checks, not approvals.
- **`web-verify` must not be a required check as-is.** Its workflow carries a
  `paths:` filter (`web/**`, `artifacts/**`, `schemas/**`); a PR outside those
  paths never produces the check, GitHub reports the merge state `BLOCKED`, and the
  engine holds it forever under rule 5. Either drop it from the required set or
  give it a paths-ignore stub job that reports success.

Arming this file was the operator's act (the workflow is a machinery file); the
first armed run is the proof that this stream's PRs land without a hand merge.
