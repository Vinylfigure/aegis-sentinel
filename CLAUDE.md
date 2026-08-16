# Aegis Sentinel

Concept budget: 1 bullet = 1 concept, ≤20 concepts in this file — a workspace
heuristic well inside the platform's own <200-line target, not a substitute for
it. `/evolve` must merge or retire a rule before adding past the cap; `/doctor`
rightsizes independently. Details live in skills — they load on demand; this
file is always in context, so every line must earn it, and a line the codebase
already shows earns nothing.

## Prime directives

- Plan before code: for non-trivial work, use plan mode or `/plan-feature`.
- Never claim done without a closed loop: run `/verify-loop` or the `verifier` agent.
- When corrected, or when verification fails, a lesson exists — run `/reflect` before the session ends.
- Before any complex task, verbalize the invariants at stake and the most likely failure mode — a wrong prediction is `/reflect` material.
- Delegate exploration and verification to subagents; keep this thread's workspace clean.
- One task per session: parallel work goes to separate worktree sessions (`/worktree-parallel`), never the main checkout.
- Conduct, don't wait: act on the session-start status; when the user states a goal, propose the route — skills, order, and modality (inline / plan / worktrees / loop / heartbeat). Escalation is proposed, never silent; slash commands are shortcuts, never prerequisites.

## Project facts

<!-- janus:facts:start -->
- App stack: Python 3.12, pip, ruff (lint+format), pytest; src-layout package `aegis_sentinel` under `src/`.
- Verify: `scripts/verify.sh quick <file>` (ruff check+format on the file) or `full` (fixture suite + ruff + pytest project-wide); CI runs `scripts/verify.sh full` on every push/PR.
- Setup: `pip install -e '.[dev]'` (editable install, pulls in ruff + pytest for dev).
<!-- janus:facts:end -->

## Learned rules

<!-- janus:rules:start -->
<!-- Populated only by /evolve. Cap: 12 rules. Each cites a LEARNINGS.md id. -->
- Aggregator claims, fetch summaries, and subagent reports are leads, never evidence — confirm claims verbatim against a primary source before adopting or citing. (L-005)
- After changing a convention, grep the whole repo for the old wording and reconcile every hit before claiming consistency. (L-007)
- Disciplines may be designed up front, but a mechanism — tool, file, cap, fallback — enters the scaffold only after dogfooded use demonstrates the need. (L-014)
- Before encoding a mechanism, check whether the platform provides it natively; encode only the discipline the scaffold adds on top. (L-015)
- Before presenting a plan, run an adversarial pass over scale, concurrency, and headless/no-user behavior, and pair every failure found with a fix, not a risk note. (L-008)
<!-- janus:rules:end -->

## Gotchas

- `scripts/test-hooks.sh` asserts *literal* component-map counts in `docs/ARCHITECTURE.md` and that every `*.sh` named anywhere in `docs/*.md` exists — adding a skill, hook, or agent, or naming a hypothetical script in prose, fails CI unless the docs change in the same commit.
- Auto memory never leaves the machine that wrote it, so the headless heartbeat and every cloud session start with an empty ambient tier — only the git-tracked ledger travels.
