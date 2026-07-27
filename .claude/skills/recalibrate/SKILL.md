---
name: recalibrate
description: Re-verify this repo's encoded conventions (skills, CLAUDE.md directives, ARCHITECTURE.md claims) against primary sources and file drift as candidate LEARNINGS.md entries.
when_to_use: Use when the session-start status says recalibration is stale, a documented practice misbehaves, or on the maintenance heartbeat.
---

The ecosystem-learning loop. `/reflect` learns from what happened in sessions;
this skill learns from what changed in the world. The scaffold's encoded
practices are claims about tools and methods that keep evolving — claims rot.
Founding example: this repo's worktree skill shipped with a manual script two
weeks after `claude --worktree` made it the fallback rather than the path.

## Hold in mind

1. The gate is method, not publisher: any source can be primary, and the test is a verbatim quote you read yourself. A fetch summary is never evidence — not from an aggregator, and not from a subagent.
2. Propose, never edit: your only outputs are `Status: candidate` ledger entries and the run stamp — `/evolve` keeps promotion authority, and the evidence discipline survives.
3. Verify drift in both directions: absence of confirmation is not deprecation — flag a convention only when a primary source contradicts or supersedes it — and presence in the scaffold is not currency — an encoded practice is a claim about a moving target, so re-verify it against primary sources before relying on it or "fixing" it.
4. Aim at what would cost the most to lose: the conventions this repo is proudest of are the ones a comfortable audit skips. Name them first.
5. Ledger rules apply: one concept per entry, dedupe by Evidence-bump, entries below the marker, source URL in the Trigger line. Durable discipline goes in the Rule; the dated vendor fact stays in the Trigger.

## Steps

1. Enumerate the conventions this repo encodes: read each `.claude/skills/*/SKILL.md` (the practices its steps assume), the CLAUDE.md prime directives, and the claims in `docs/ARCHITECTURE.md`'s methodology and workspace tables. Include the load-bearing ones by name: the concept and skill budgets and their operational grounding (the docs' 200-line guidance; the workspace paper is convergent context only, never the derivation), the `Hold in mind` shape itself, the hook protocol's "deliberately unused events" list, and the manual reflect → evolve pipeline. List them as short checkable claims.
2. Read `.claude/memory/sources-seen.md` and split the work: **living** sources (docs pages, changelog, blog index) are re-read every run — a stable URL says nothing about stable content; **one-shot** sources (dated articles already logged) are skipped.
3. Fetch, starting from the indexes so new material surfaces without being named in advance:
   - `code.claude.com/docs` — `llms.txt` index and the changelog
   - `claude.com/blog` — the post index, then anything dated after the newest entry in the manifest
   - `anthropic.com/engineering`
   - `github.com/anthropics/skills` — `spec/agent-skills-spec.md`, the authority on frontmatter fields
   - `transformer-circuits.pub/2026/workspace/index.html` — convergent context for the budgets; if its framing shifts, the honesty note in ARCHITECTURE must follow

   If a source is unreachable, record nothing for the claims it covers — a failed fetch is "no data", never a confirmation.
4. Diff and classify each claim: **confirmed** (still current), **drifted** (a primary source contradicts or supersedes it — cite where), or **newly-available** (a capability the scaffold predates and could use). For a native limit, check whether the number is a target or a failure threshold before treating it as a budget.
5. For each drift or new capability, append a candidate entry to `.claude/memory/LEARNINGS.md` per its format spec: `Evidence: 1`, verbatim quote and source URL in the Trigger. If an equivalent entry exists, bump its Evidence instead.
6. Append every source you actually read to `.claude/memory/sources-seen.md`, one row each, with its conclusion.
7. Record the run: `date +%s > .claude/memory/recalibrated-at` (epoch in content — mtimes don't survive clones). Stamp **only** if step 1's enumeration was completed — a stamp from a partial run is a false green that suppresses the very nudge meant to catch it. Commit it alongside any drift entries.
8. Summarize: N claims checked, N confirmed, N drifted, N new — and if any entry is now at Evidence >= 2, recommend `/evolve`.

## Before finishing

State the counts from step 8 and read back each entry you wrote. Say whether
step 1's enumeration was complete, and therefore whether you stamped. Assert
explicitly that you edited no convention file — no skill, not CLAUDE.md, not
ARCHITECTURE.md — only the ledger and the run stamp. If you caught yourself
wanting to "just fix" a stale skill directly, that impulse goes in the
summary too: it is exactly what the evidence discipline exists to stop.
