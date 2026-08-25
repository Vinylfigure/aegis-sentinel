# Using the scaffold (Aegis Sentinel's Janus operations guide)

The operator's guide to the Janus scaffold this repo runs on.
[ARCHITECTURE.md](ARCHITECTURE.md) explains *why* the pieces exist;
[SELF-IMPROVEMENT.md](SELF-IMPROVEMENT.md) specs the memory system;
[MEMORY-SKILLS-EVAL.md](MEMORY-SKILLS-EVAL.md) records how this repo's loop
went dead and was revived; this document is *how you drive it* — though
mostly, it drives.

**You never need to memorize the command vocabulary.** Every skill carries a
trigger description, so Claude proposes the right one when the situation
matches, and each side-effect skill confirms with you before doing anything
irreversible. Every `/command` in this doc is an escape hatch, not a
prerequisite.

## Session zero: starting a project

1. **Create the repo.** Either click **Use this template** on GitHub, or — from
   any existing Janus project — say you want to start a new project and let
   `/replicate` interview you (it confirms name, visibility, and location
   before creating anything). Replication is better once you have history:
   portable learnings are inherited, so each generation starts smarter.
2. **Open a session.** `cd` into the clone, run `claude`. The session-start
   status says the scaffold is not bootstrapped, and Claude proposes
   `/bootstrap`.
3. **Bootstrap.** It detects your stack (or interviews you for one), wires
   `scripts/verify.sh` to your real formatter/linter/tests, and *proves* the
   loop closes — you'll see a passing full run and a deliberately-broken
   edit get caught. From this moment every edit is checked automatically.
4. **State your first goal in plain words.** Tell Claude what you want to
   build — and say how experienced you are with the domain while you're at
   it; fuzzy requirements are its cue to interview you rather than assume.
   For anything non-trivial it will propose the plan-first flow
   (`/plan-feature`): explore, plan with explicit "done means" and unknowns,
   sign-off, build, verify. The Stop hook closes the day by asking for
   `/reflect` if the session logged lessons.

## How the scaffold drives

CLAUDE.md's conductor directive makes Claude act on the session-start status
and propose the route — skills, order, and *modality* — whenever you state a
goal. What fires when:

| Skill | Claude reaches for it when… | Nudged by | Confirms before |
|---|---|---|---|
| `/bootstrap` | the facts block says NOT BOOTSTRAPPED | session-start line | — |
| `/plan-feature` | a non-trivial change is requested | — | plan sign-off |
| `/verify-loop` | any "done" claim is near | per-edit hook runs the quick check anyway | — |
| `/reflect` | a correction happened or the session ends | **Stop hook blocks once** when signals exist · leftover signals resurface at session start | — |
| `/evolve` | between tasks with ripe learnings | session-start ripe count · heartbeat | **CLAUDE.md edits** (headless: PR) |
| `/recalibrate` | the status says recalibration is stale, or a documented practice misbehaves | session-start stale line · heartbeat | — (writes candidates + stamp only) |
| `/work-loop` | the build-heartbeat's execution plan has no ready box left this firing | heartbeat step 2b (fallback arm) | — |
| `/ship` | a verified change is ready to leave the machine | — | **branch + remote** before first push (headless: PR only) |
| `/worktree-parallel` | work splits into independent tracks | — | **track table** before any worktree |
| `/replicate` | you want a new project from this scaffold | — | **name/visibility/path** before creation |
| `/add-skill` | a procedure got repeated or explained twice | `/evolve` promotes procedure-shaped lessons | — (retire before adding) |

**The modality ladder** — Claude proposes the level that fits the observable
shape of the work, and escalation is always proposed, never silent:

- answerable in this session → just do it inline (inner loop has your back)
- multi-file or risky → plan mode / `/plan-feature`
- genuinely independent tracks → `/worktree-parallel` sessions
- long-running and pollable (CI, a flaky migration) → a `/loop` or `/goal` loop
- calendar cadence, no session open → the heartbeat routine (below)

## The daily rhythm

- **Non-trivial work starts in plan mode** (Shift+Tab twice) or with
  `/plan-feature`. Trivial one-file changes: just ask; the inner loop has
  your back.
- **Let the inner loop work.** After every edit, the PostToolUse hook runs the
  quick check and feeds failures straight back to Claude. You don't need to
  paste lint errors — they arrive automatically.
- **When requirements are fuzzy, say so and let Claude interview you.**
  Disclosing your experience level ("I've never touched OAuth") changes what
  it explains vs. assumes. Plans name their unknowns and how each resolves.
- **Before accepting "done", demand the loop be closed**: `/verify-loop`
  (iterates to green against a runnable check, max 5 rounds) or the
  `verifier` agent (adversarial: runs the suite *plus* probes the change
  directly, and only passes on pasted evidence).
- **Ship when ready**: `/ship` verifies, commits, confirms branch and remote,
  pushes, opens the PR, and babysits CI and reviews until merged.

## Session rituals (the self-learning loop)

You mostly don't have to think about this — the hooks do:

- Every prompt that *looks like a correction* ("no, that's wrong…") is
  silently logged. Every verification failure is silently logged.
- **When you stop a session that logged signals, the Stop hook blocks once**
  and asks Claude to run `/reflect`. That's not an error — it's the system
  refusing to waste an expensive lesson. Let it run; it takes seconds and
  writes one-concept rules to `.claude/memory/LEARNINGS.md` (or states why
  there was no lesson).
- **When the session-start line says learnings are ripe** ("N with
  Evidence ≥ 2"), Claude proposes `/evolve` between tasks. It promotes stable
  lessons into `CLAUDE.md` rules or new skills, retires contradicted rules,
  and enforces the budgets — asking you before it touches CLAUDE.md. This is
  how corrections compound instead of repeating.

You can also run `/reflect` manually any time something surprising happened —
don't wait for the nudge.

## Memory operations

- **Read the ledger** at `.claude/memory/LEARNINGS.md`. Entries are
  append-only and marked, never deleted: `candidate` → `promoted:*` /
  `retired`, plus `inherited` in children.
- **Auto memory is the ambient tier**: Claude Code natively keeps
  machine-local notes per repo — browse or toggle them with `/memory`.
  `/reflect` harvests the shareable repo-truths from there into the
  git-shared ledger; machine-local trivia stays local.
- **Nothing promotes on one occurrence.** Evidence ≥ 2 (or your explicit
  confirmation) is the bar. If you *know* a lesson is right after one
  occurrence, say so and `/evolve` will take your word as evidence.
- **`Scope: portable` is a promise** — true in any repository. These entries
  are what `/replicate` carries into children. Judge harshly.
- **The budgets are load-bearing**: CLAUDE.md ≤20 concepts, ≤12 learned
  rules, and skills retired before new ones are added. When `/evolve` refuses to add without retiring, that's
  the design working, not a limitation to remove (rationale in
  [ARCHITECTURE.md](ARCHITECTURE.md#the-capacity-budget-rationale)).
- **Recalibration keeps encoded practices honest**: `/recalibrate` re-verifies
  the scaffold's conventions against primary sources — the Claude Code docs
  and changelog, `claude.com/blog`, Anthropic's engineering blog, the
  agent-skills spec — and files drift as candidate ledger entries; `/evolve`
  still decides what changes. The gate is method, not publisher: a claim
  counts when you have read the verbatim quote, and a fetch summary never
  does. `.claude/memory/sources-seen.md` records what was read and when, so
  dated articles are read once while docs pages are re-read every run. You
  don't schedule it in your head: the session-start line nudges when the last
  run (`.claude/memory/recalibrated-at`, committed) is more than 30 days old,
  and the heartbeat can run it for you.

## The heartbeat (autonomous maintenance)

For calendar-cadence upkeep with no session open, create a weekly cloud
routine once — just ask Claude: *"schedule a weekly maintenance heartbeat"*
(`/schedule` creates it conversationally; routines run headless in
Anthropic's cloud and survive your laptop being closed). The prompt that
works:

> Run /recalibrate. If the ledger then reports entries at Evidence >= 2, run
> /evolve. Deliver every change as a PR — never commit to the default branch.

Two design points make this safe:

- **Headless gates degrade to PRs.** `/evolve` and `/ship` never touch the
  default branch without a user; the PR review *is* the confirmation.
- **Loops trigger; skills encode quality** (the official loops guidance).
  The heartbeat only decides *when* — what "verified" and "promotable" mean
  live in the skills, same as in interactive sessions.

## Scaling up

- **Parallel workstreams**: `/worktree-parallel` splits a task into
  independent tracks and launches each with native worktrees:
  `claude --worktree <name>` (add `--tmux` for its own tmux session).
  Run 3–5 sessions, **one task per session** — never multiplex tracks in one
  conversation. Number your terminal tabs, enable system notifications, and
  use `claude agents` from the root directory as the fleet view. Every
  worktree carries the full scaffold (`.claude/` is in-tree). Merge only
  tracks that verified green; reconcile ledger IDs at merge time (the skill
  covers this); clean worktrees after.
- **Delegate to subagents by habit**: a native exploration subagent to scout
  before you plan, `verifier` before you believe "done", `memory-curator`
  inside `/evolve`. Delegation keeps the main thread's context clean for
  actual decisions.
- **New procedures become skills**: when you catch yourself giving the same
  multi-step instructions twice, Claude should propose `/add-skill` — paying
  for it by retiring something. Rules go to CLAUDE.md; procedures become skills.

## Replication and lineage

- `/replicate <name>` stamps a child repo (GitHub template path or local
  fallback), copies portable rules and ledger entries in as
  `Status: inherited`, rewrites identity, resets the child's recalibration
  clock, and hands off to the child's `/bootstrap`.
- Children **re-earn** promotion: inherited entries need fresh evidence in
  the child before `/evolve` promotes them there. The parent's
  already-promoted rules are the one exception — they arrive active in the
  child's rules block, and for exactly that reason each one needs your
  explicit yes during `/replicate`: the generation boundary is a review
  gate against inheriting a bad (or poisoned) rule unreviewed.
- Children do **not** auto-update from the template. To backport a template
  improvement into an existing child, cherry-pick the commit.
- Improving Janus itself is just feature work — the template runs its own
  loops (see the dogfooding rules in
  [SELF-IMPROVEMENT.md](SELF-IMPROVEMENT.md#improving-janus-itself-dogfooding)),
  and `scripts/test-hooks.sh` keeps the hook plumbing honest in CI.

## Troubleshooting

- **Hook didn't fire?** Hooks need the workspace trusted (accept the trust
  dialog) and `jq` installed — without `jq` they degrade to silent no-ops.
  `claude --debug` shows hook execution.
- **Skill didn't auto-fire?** State the situation in plain words ("this is
  ready to go out", "these three fixes are independent") and Claude should
  propose the skill; if not, the slash command always works — and the
  description probably needs sharper trigger wording, which is itself a
  `/reflect` lesson.
- **Quick check too slow?** It runs on *every* edit; keep it under ~10s. Move
  anything slower into the `full` arm.
- **Stop nudge felt wrong?** It fires at most once per session and only when
  signals exist. If the signal was a false positive (the correction regex is
  deliberately loose), Claude just states "no lesson" and stops — cost: one
  sentence.
