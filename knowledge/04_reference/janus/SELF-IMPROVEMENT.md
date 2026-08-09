# How Janus improves itself

The scaffold treats every session as training data and every project as a
generation. This document is the lifecycle spec — what counts as a lesson,
how a lesson earns promotion, and how knowledge crosses repositories.

## Lifecycle of a lesson

```
signal ─────────► entry ──► evidence ──► promotion ──► inheritance
(hooks + ambient  (/reflect)  (recurrence)  (/evolve)    (/replicate)
 auto memory)
```

**1. Signal.** Hooks log learning-shaped events silently as they happen:
`prompt-signal.sh` flags correction-looking prompts, `post-edit-verify.sh`
flags verification failures. Both append one line to
`.claude/memory/.session-signals` and say nothing — signals are cheap and
false positives are harmless.

**2. Entry.** At stop time, if signals exist, the Stop hook blocks once and
asks for `/reflect`. If a session ends without reflecting (or dies), the
leftover signals surface at the next session start instead of being lost. Reflect reads the transcript plus the signal log and
writes *rules* to the ledger — imperative, one-concept, testable. Noise
(typos, flaky network) is explicitly dismissed, not recorded. An equivalent
existing entry gets its `Evidence` count bumped instead of a duplicate.
A second writer feeds the same ledger from outside: `/recalibrate`
re-verifies the scaffold's encoded conventions against primary sources and
files ecosystem drift as candidates — the signal source is the world
changing rather than a session event, but the discipline is identical.
A third source is ambient: Claude Code's native auto memory accumulates
machine-local notes as work happens, and `/reflect` harvests the shareable
repo-truths among them into the git-shared ledger.

**3. Evidence.** Nothing promotes on one occurrence — one occurrence is an
anecdote. `Evidence: 2` (or explicit user confirmation) is the threshold.
The session-start hook surfaces ripe entries so they don't rot.

**4. Promotion.** `/evolve` (analysis delegated to the `memory-curator`
agent) moves qualifying lessons up:
- Rule-shaped, global → a bullet in CLAUDE.md's `janus:rules` block, citing its id.
- Rule-shaped, path-local → `.claude/rules/<topic>.md` with `paths:` glob
  frontmatter — it loads only when Claude touches matching files, so it
  spends no CLAUDE.md budget.
- Procedure-shaped → a skill, via `/add-skill` (procedures and path-local
  rules load on demand; global rules must not grow past the cap).
- It is also the garbage collector: rules contradicted by newer entries are
  retired, and the CLAUDE.md caps (≤20 concepts, ≤12 rules) are asserted at
  the end of every run. **Adding requires room; room comes from merging or
  retiring.** The budget rationale is in
  [ARCHITECTURE.md](ARCHITECTURE.md#the-capacity-budget-rationale).
- Editing CLAUDE.md is gated: in an interactive session `/evolve` asks the
  user first; in a headless run (the heartbeat) it delivers via PR — the
  review is the confirmation. This is the general convention for every
  side-effect skill: no invocation lock, an in-body gate immediately before
  the irreversible action, degrading to PR-delivery when no user is present.

**5. Inheritance.** `/replicate` copies `Scope: portable` entries (and their
promoted rules) into child repositories, re-marked `Status: inherited`.
Children re-earn promotion with their own evidence; promoted rules are the
one exception — they land active in the child's CLAUDE.md, so each needs the
user's explicit yes at replicate time. The generation boundary is a review
gate: persisted rules files are an injection channel, and a bad rule would
otherwise propagate to every descendant unreviewed. Ledger entries are never
deleted — `promoted`/`retired`/`inherited` markings keep the full lineage
history, which is what makes the ledger a genome rather than a notebook.

## Ledger integrity rules

- One entry = one concept. Two-sentence rules are two entries.
- `Scope: portable` is a promise: true in *any* repository. Judge harshly —
  a wrongly-portable entry pollutes every descendant.
- Never delete; mark. History is data.
- IDs are sequential; parallel worktree sessions reconcile colliding IDs at
  merge time (see the worktree-parallel skill).

## Improving Janus itself (dogfooding)

The template repository runs its own loops. Working *on* Janus — editing
hooks, skills, agents — generates signals, reflections, and promotions
exactly like feature work in a child project, and improvements committed
here flow to every future child. Two rules keep that safe:

1. A change to a cap, hook protocol, or skill shape must update
   [ARCHITECTURE.md](ARCHITECTURE.md) in the same commit — the rationale doc
   is what stops future sessions from "simplifying" load-bearing constraints.
2. Prove loop changes with the fixture tests before committing: run
   `scripts/test-hooks.sh` — the same suite CI runs on every push — and give
   new behavior a new fixture in the same commit. Each hook's header comment
   documents its stdin/exit-code contract; the fixtures are the executable
   form of those contracts.

Existing children do not auto-update; they inherit at replication time only.
To backport an improvement to a child, cherry-pick the commit or re-run the
relevant part of `/replicate` by hand.
