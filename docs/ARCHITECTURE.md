# Aegis Sentinel architecture (Janus scaffold)

How the pieces connect, the exact hook protocol, and the research the design
choices come from. Read this before changing hooks, caps, or skill shapes —
several "arbitrary" numbers here are load-bearing.

## Component map

```
CLAUDE.md                     always-on memory (≤20 concepts; sentinel-marked blocks)
.claude/
  settings.json               hook wiring + safe-command permissions
  hooks/                      4 shell hooks (protocol below)
  skills/                     10 skills — load on demand (progressive disclosure)
  agents/                     2 subagents — run in their own context windows
  memory/LEARNINGS.md         append-only learnings ledger (git-tracked)
  memory/sources-seen.md      committed watermark of what /recalibrate has read
src/aegis_sentinel/           the product package (src layout; controls land here)
schemas/                      closed JSON Schemas — hand-authored verdict-record v0.1.0 + ontology/ generated from the pydantic models (drift-tested)
tests/                        pytest suite + fixtures (incl. seeded-drift captures under fixtures/seeded/)
knowledge/                    hash-manifested corpus + prior-scaffold knowledge (read-only inputs)
docs/EVALUATION.md            adopt-vs-rebuild decisions and the first build milestone
pyproject.toml                Python ≥3.12 packaging; dev extras: ruff, pytest, pyyaml
.github/ISSUE_TEMPLATE/       work-order form (objective, done-means, allowed-paths, effort-budget)
scripts/
  verify.sh                   quick|full dispatcher; /bootstrap fills the case arms
  test-hooks.sh               fixture suite for the scaffold plumbing — hooks + docs cross-refs (first step of verify.sh full)
.github/workflows/verify.yml  CI: runs verify.sh full on every push/PR
```

Sentinel markers give skills deterministic edit targets:

| Marker | File | Written by |
|---|---|---|
| `<!-- janus:facts:start/end -->` | CLAUDE.md | `/bootstrap`, `/replicate` |
| `<!-- janus:rules:start/end -->` | CLAUDE.md | `/evolve`, `/replicate` |
| `# janus:bootstrap:quick|full:start/end` | scripts/verify.sh | `/bootstrap` |

## Hook data flow

All hooks receive JSON on stdin, degrade to no-ops without `jq`, and emit as
little as possible — hook output lands in always-on context, which is a
budgeted resource (see rationale below).

```
SessionStart      session-start.sh      → ≤3 short lines: bootstrap status, leftover
                                          unprocessed signals (→ consider /reflect), ripe-learnings
                                          count, recalibration staleness (only once
                                          bootstrapped; stale = recalibrated-at missing or
                                          >30 days — epoch lives in the file's CONTENT
                                          because git does not preserve mtimes across clones);
                                          when source == "compact": one extra line telling the
                                          agent to re-verbalize its working set (invariants +
                                          "done means") — compaction is exactly when the
                                          workspace was disrupted
UserPromptSubmit  prompt-signal.sh      → silent; correction-looking prompts append
                                          "correction:<ts>" to .claude/memory/.session-signals
PostToolUse       post-edit-verify.sh   → runs `verify.sh quick <file>`; on failure appends
(Edit|Write)                              "verify-fail:<file>" to .session-signals and exits 2
                                          with the output on stderr → Claude iterates
Stop              stop-reflect-nudge.sh → if .session-signals is non-empty AND no
                                          .nudged-<session_id> marker exists: touch the marker
                                          and emit {"decision":"block","reason":"…run /reflect…"}
                                          — blocks at most once per session by construction
```

Marker files (both gitignored): `.session-signals` is the per-session event
log, deleted by `/reflect`; `.nudged-<session_id>` is the once-per-session
guard, so an ignored nudge never becomes an infinite loop. By contrast,
`memory/recalibrated-at` is **committed** when it exists: it is provenance,
not runtime state — a headless heartbeat recalibrating in a cloud clone must
be able to reset the staleness signal everywhere via its PR. It is written
ONLY by a completed `/recalibrate` run, so a fresh clone (and this repo,
until its first full run) has no stamp and the staleness nudge fires — the
prior stamp was written by a design commit, never a run, and read as a false
green for weeks (L-020).

Deliberately unused events: `PreToolUse`, `PreCompact`, `Notification`,
`SubagentStop` — nothing in the template earns them yet. Add hooks only with
a purpose, and keep their output inside the budget.

## The capacity-budget rationale

The caps — ≤20 concepts in CLAUDE.md, ≤12 learned rules, ≤50-word skill
descriptions, ≤3 hook lines — are operational discipline, grounded in
Anthropic's product guidance and this repo's own dogfooding, not derived
from interpretability research:

- The memory docs: "target under 200 lines per CLAUDE.md file. Longer
  files consume more context and reduce adherence", and "shorter files
  produce better adherence" (code.claude.com/docs/en/memory, verbatim,
  read 2026-07-24). The concept budget keeps this file an order of
  magnitude inside that line, where adherence is best.
- The Claude 5 context-engineering post: "over 80% of Claude Code's
  system prompt" removed "with no measurable loss on our coding
  evaluations" — instruction budgets earn their keep under deletion
  tested against outcomes, not by accumulation.
- Dogfooding: `/evolve` must merge or retire before adding past the cap,
  and the constraint has bound in practice — the forced merges and
  retirements are in the ledger, which is the evidence the cap does work.

Convergent context, nothing more: Anthropic's interpretability paper on a
[global workspace in language models](https://transformer-circuits.pub/2026/workspace/index.html)
reports that a small subset of verbalizable representations behaves
workspace-like. Its number is not a measured capacity: the researchers
"typically choose it to be no more than 25" — a hyperparameter of a lens
the paper itself calls "an imperfect tool", covering under 10% of
activation variance and single-token concepts only. The paper makes no
claims about prompts, instruction files, or agent harnesses. It is
suggestive company for small-budget discipline; it cannot justify any
particular number, and the cap must never be cited as derived from it.

The practices the old research-mapping table credited to the paper stand
on their own operational grounding:

| Practice | Actual grounding |
|---|---|
| **Hold in mind** (restate invariants before acting) and **Before finishing** (evidence before done) | Kept because they observably catch failures here — L-008's trigger records one stress pass finding 4 real design bugs; the verifier must articulate a counterfactual before any PASS. Dogfooding, not neuroscience |
| 1 bullet = 1 concept rule format | Dedup and transfer ergonomics: one-concept entries can be grepped, merged, and evidence-counted; narratives cannot |
| Cross-repo portability of rules | An earned property, judged per rule and confirmed at `/replicate`'s review gate — not a consequence of any research claim about internal representations generalizing |
| Progressive disclosure (skill bodies on demand, subagents return conclusions) | "Context, therefore, must be treated as a finite resource with diminishing marginal returns" (effective-context-engineering) — product guidance |

Treat ≤20 as a tunable heuristic, not a constant of nature. If evidence
ever shows a different number works better, change the number — the
discipline worth keeping is that *some* budget binds, so adding requires
retiring.

## The memory pipeline (J-brain)

Learning crosses sessions through three tiers, all native Claude Code
mechanisms — no external dependency. Retrieval is just-in-time at every
tier: indexes load, bodies are pulled when relevant.

| Tier | Mechanism | Scope | Loads |
|---|---|---|---|
| Rules | `CLAUDE.md` (≤20 concepts) + path-scoped `.claude/rules/*.md` | git-shared | always / when matching files are touched |
| Genome | `LEARNINGS.md` ledger (reflect → evolve → replicate) | git-shared | only by the memory skills |
| Ambient | native auto memory (`MEMORY.md` index + topic files) | machine-local | index each session; topic files on demand |

The ambient tier does not cross machines: auto-memory files are "not shared
across machines or cloud environments". So the headless heartbeat, cloud
sessions, and a teammate's clone all start with it empty — anything the
automation depends on has to live in the git-tracked tiers above it.

Capture is ambient (auto memory notes things as work happens, zero
ceremony), consolidation is deliberate (`/reflect` harvests shareable
repo-truths from auto memory and the session into evidence-gated ledger
entries), promotion is curated (`/evolve` routes: global rule → CLAUDE.md;
path-local rule → `.claude/rules/<topic>.md` with `paths:` frontmatter;
procedure → skill).

**The adapter slot.** The ambient tier is replaceable without touching the
reflect → evolve → replicate loop: `autoMemoryDirectory` relocates the
store, `autoMemoryEnabled` toggles it, and an MCP memory server can augment
retrieval. An external memory backend plugs in there — the pipeline's
interfaces (harvest at `/reflect`, promote at `/evolve`) do not change.
Dogfooding note: subagent persistent memory is docs-supported and a future
option for the verifier — observe the need first, encode later.

## Context-budget accounting

Always-loaded context = CLAUDE.md (≤20 concepts) + every skill's
`description` + ≤3 hook status lines. Everything else is on-demand: skill
bodies load on invocation, the ledger is opened by exactly three skills,
exploration and verification run in subagents that return conclusions. This
is why skill descriptions are capped at ≤50 words (with `when_to_use`
counted in): since the model-invocation flip, every skill's description rides
in every session forever — a skill is a permanent tax, so the budget mirrors
CLAUDE.md's.

The platform truncates the combined `description` + `when_to_use` listing at
1,536 characters and reports the post-budget size in `/context`'s Skills row.
That number is a *failure threshold*, not a target — adopting it as the budget
would license roughly five times today's always-loaded description text. The
≤50-word rule is the discipline this scaffold adds on top; the count cap was
retired in favour of "retire before adding", because it never once bound.

## The methodology mapping (Boris Cherny / Anthropic practice)

| Practice | Where it lives in Janus |
|---|---|
| Plan mode before code | `/plan-feature` (and prime directive #1) |
| Ship as a loop — babysit CI and reviews to merged | `/ship`, plus `.github/workflows/verify.yml` running `scripts/verify.sh full` as the remote closed loop |
| CLAUDE.md as compounding memory — "any time Claude does something wrong, add a note" | The session loop: signals → `/reflect` → ledger → `/evolve` → CLAUDE.md, with evidence thresholds so notes compound instead of accumulating |
| Closed feedback loops — "if Claude can close the loop on its own, it will iterate until the output is right" | PostToolUse hook (inner loop) + `/verify-loop` + the verifier agent |
| Subagents for focused work | Custom: verifier (evidence-bound judge) and memory-curator (proposal-only librarian). Scouting and independent design use Claude Code's native exploration/planning subagents — the platform owns the mechanism; the template keeps only the disciplines it adds |
| Parallel sessions in worktrees — 3–5 at once, one task per session | `/worktree-parallel`: native `claude --worktree`, `claude agents` as the fleet view; `.claude/` is in-tree so every worktree gets the full scaffold |
| Team-shared configuration | `.claude/settings.json` is committed; `settings.local.json` is gitignored |
| Encoded practices drift as tools evolve | `/recalibrate` re-verifies conventions against primary sources and files drift as candidate learnings; `/evolve` keeps promotion authority; `memory/sources-seen.md` separates living sources (always re-read) from dated ones (read once); the session-start staleness nudge and the heartbeat routine keep it running |
| Loops trigger; skills encode quality | Skills auto-invoke from their trigger descriptions (the conductor directive routes goals to skills + modality); side-effect skills carry in-body gates that degrade to PR-delivery when headless; `/goal`-style loops and the weekly heartbeat only decide *when* |

## Claude 5 context-engineering alignment (sources read 2026-07-24)

This was a targeted read of one batch of sources, not a full `/recalibrate`
run: step 1's enumeration of every encoded convention was not performed, so
`recalibrated-at` was deliberately **not** stamped and the 30-day nudge still
stands. The next full run starts from `memory/sources-seen.md`.

Anthropic's [new rules of context engineering](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models)
reports removing "over 80% of Claude Code's system prompt" for Claude 5
generation models "with no measurable loss on our coding evaluations", and
[Agent Harness Design](https://claude.com/blog/harnessing-claudes-intelligence)
makes stripping the harness down a first-class pattern. Both are subtraction
arguments, and a scaffold whose response is to grow has misread them. Where
Janus landed:

| Shift | Janus position |
|---|---|
| Give rules → **let Claude use judgement** | Skill bodies encode what *this repo* does differently — gotchas, sentinels, irreversible steps — and leave general competence alone. Ceremony counts (`3-5 items, hard cap`) retired; the practice kept |
| Give examples → **design interfaces** | Skills carry `when_to_use` rather than cramming triggers into `description`; `allowed-tools` is reserved for read-only skills, since the grant clears at the next user message |
| Upfront → **progressive disclosure** | Already the design: skill bodies load on invocation, the ledger opens for three skills, subagents return conclusions |
| Repeat yourself → **simple descriptions** | ≤50 words per skill, `when_to_use` counted in |
| CLAUDE.md memory → **auto-memory** | Both, deliberately: auto memory captures ambiently, but it never leaves the machine, so the git-tracked ledger remains the tier automation depends on |
| Simple specs → **rich references** | Open. The ledger is prose; nothing yet earns a richer reference format |

Two native limits are cited above and neither is adopted as a budget: the
1,536-character listing truncation is a failure threshold, and `/doctor`
rightsizes independently of `/evolve`'s counts. The distinction matters —
substituting a platform's ceiling for a scaffold's discipline loosens the
constraint while looking like modernisation.

Rejected on the repo's own evidence rules: pinning `model:` into a
stack-agnostic template (L-004 — a moving target the scaffold would then
babysit), an adversarial reviewer trio (L-017 — copying an org chart as a
starting shape, when propose/dispose separation already exists in
`memory-curator` and `/recalibrate` → `/evolve`), and a `/security-review`
step (L-015 — a platform built-in, and this template has no stack to review
until `/bootstrap` runs).
