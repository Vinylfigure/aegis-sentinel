# Janus

*The god of starting anything.*

A self-learning, self-replicating starter template for [Claude Code](https://code.claude.com)
projects. Stack-agnostic: the scaffold *is* the product — hooks, skills,
subagents, and a memory system that make every project it spawns learn from
its own sessions and inherit what its ancestors learned.

Janus has two faces: one looks back (distilling lessons from what happened),
one looks forward (stamping those lessons into the next project).

## Quickstart

1. On GitHub, click **Use this template** (or run `/replicate` from an existing Janus repo).
2. `cd` into the clone and start `claude`.
3. Run `/bootstrap` — it detects (or asks for) your stack, wires
   `scripts/verify.sh` to your real lint/test commands, and proves the
   verification loop closes.
4. Build things. The loops below do the rest.

To make this repo itself a template: `gh repo edit <owner>/janus --template`
(or Settings → check *Template repository*).

## The three loops

```
┌─ Inner loop ──────── every edit ───────────────────────────────┐
│  edit → PostToolUse hook → verify.sh quick → red? → fix → …    │
└─────────────────────────────────────────────────────────────────┘
┌─ Session loop ────── every session ─────────────────────────────┐
│  corrections + failures logged silently → Stop hook nudges      │
│  /reflect → lessons land in LEARNINGS.md → /evolve promotes     │
│  stable lessons into CLAUDE.md rules or new skills              │
└─────────────────────────────────────────────────────────────────┘
┌─ Lineage loop ────── every project ─────────────────────────────┐
│  /replicate stamps a child repo, portable learnings inherited   │
│  → child /bootstrap specializes to its stack → child learns…    │
└─────────────────────────────────────────────────────────────────┘
```

## What's inside

You don't memorize these commands — every skill carries a trigger
description, so Claude proposes the right one when the situation matches,
and side-effect skills confirm with you before acting. Typing the
`/command` is the escape hatch.

| Piece | Purpose |
|---|---|
| `CLAUDE.md` | Always-loaded memory, hard-capped at 20 concepts (see [why](docs/ARCHITECTURE.md#the-capacity-budget-rationale)) |
| `/bootstrap` | Specialize the scaffold to a real stack; wire real verify commands |
| `/replicate` | Stamp a child project; carry portable learnings forward |
| `/reflect` | Distill this session's lessons into the learnings ledger |
| `/evolve` | Promote stable lessons into CLAUDE.md or new skills; enforce the budget |
| `/recalibrate` | Re-verify encoded practices against primary sources; file drift as learnings |
| `/plan-feature` | Plan-first workflow with explicit "done means" criteria |
| `/verify-loop` | Iterate a change to green against a runnable check |
| `/ship` | Verify green, commit, push, PR, then babysit CI and reviews until merged |
| `/worktree-parallel` | Fan out parallel sessions in git worktrees |
| `/add-skill` | Author new skills in the canonical shape |
| `verifier`, `memory-curator` | Subagents: the skeptic and the librarian (scouting and design use Claude Code's native subagents) |
| 4 hooks | SessionStart status, silent correction detector, per-edit verify, stop-time reflect nudge |
| `.claude/memory/LEARNINGS.md` | The append-only learnings ledger — the repo's genome |

## Learn more

- [docs/USAGE.md](docs/USAGE.md) — the operator's guide: day-1 setup, the daily rhythm, session rituals, memory operations, and scaling to parallel sessions.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — component map, hook protocol, and the research this design is built on (Anthropic's Global Workspace findings, Boris Cherny's Claude Code methodology).
- [docs/SELF-IMPROVEMENT.md](docs/SELF-IMPROVEMENT.md) — the lifecycle of a lesson, from signal to inheritance, and how to improve Janus itself.
