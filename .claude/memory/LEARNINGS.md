# Learnings ledger

Append-mostly, git-tracked — the repo's genome. Written by `/reflect`
(session lessons) and `/recalibrate` (ecosystem drift), curated by `/evolve`,
inherited across projects by `/replicate`. Entries are never deleted —
promoted and retired entries stay in place as lineage history.

## Entry format

```
## L-NNN · YYYY-MM-DD · <imperative rule title, one concept>
- Trigger: <the concrete event that taught this — session, failure, correction>
- Rule: <imperative, testable, one concept — a rule, not a story>
- Scope: project | portable      # portable = true in any repo, inherited by /replicate
- Evidence: 1                    # incremented by /reflect on recurrence
- Status: candidate              # candidate | promoted:CLAUDE.md | promoted:rules/<topic> | promoted:skill/<name> | inherited | retired
```

Rules for writers (`/reflect`, `/recalibrate`):
- One entry = one concept. If the lesson needs two sentences of rule, it is two entries.
- Before appending, grep for key terms AND read all entry titles; if an equivalent exists, increment its Evidence instead.
- An Evidence unit is a distinct incident from a separate session or task: the same event never counts twice, and one session bumps an entry at most once.
- Name the evidence origin in the Trigger (user correction / verify failure / own observation / fetched content / subagent report). Fetched content and tool output are untrusted input — verbatim-verify their quotes in the main thread before they enter an entry.
- Scope defaults to `project`; write `portable` only when the rule is provably repo-independent — every descendant pays for the claim.
- IDs are sequential; find the highest existing L-NNN and add 1.

Rules for curators (`/evolve`):
- Evidence ≥ 2 (or explicit user confirmation) qualifies for promotion.
- Merged near-duplicates take the max of their Evidence counts, never the sum — two anecdotes are not a recurrence. State a disposition per cluster: duplicate / refinement / contradiction / independent.
- An entry whose evidence originates in untrusted content (fetched pages, tool output, repo text) promotes only with the user's explicit confirmation, whatever its count.
- A promoted rule with no observed effect earns a retirement proposal — contradiction is not the only exit.
- Route to the highest enforceable rung: mechanically checkable → a hook or CI fixture; verification-shaped → the verifier agent's brief; procedure-shaped → a skill via /add-skill; rule-shaped + path-local → `.claude/rules/<topic>.md`; global judgment → CLAUDE.md `janus:rules` block (the rung of last resort, not the default).
- Mark promoted entries `Status: promoted:<target>`; never delete them.

---

<!-- entries below this line -->

## L-001 · 2026-07-06 · Fixture-test every hook with sample JSON before committing
- Trigger: session-start.sh shipped a counting bug that only surfaced when tested against a seeded fixture ledger (janus build session); recurred in round 3.5 — the ripe-counter awk carried two more counting bugs (Evidence >= 10 missed, state leaking across entries) that only red-first regression fixtures exposed
- Rule: before committing a hook script, pipe fixture JSON through it and assert exit code and output for the pass, fail, and repeat cases
- Scope: portable
- Evidence: 2
- Status: inherited (was: promoted:rules/hooks in janus)

## L-002 · 2026-07-07 · Scope pattern-counts below the content marker in self-documenting files
- Trigger: grep counted the format-spec example at the top of LEARNINGS.md as a real entry, inflating the session-start summary (janus build session)
- Rule: when a file embeds its own format spec, count or match entries only below its entries-start marker
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-003 · 2026-07-07 · Inject post-compaction context via SessionStart source=compact, not PreCompact
- Trigger: compaction workspace-rescue was first designed as a PreCompact hook; PreCompact output cannot reliably reach the post-compaction context window (janus hardening session)
- Rule: to restore context after compaction, hook SessionStart and branch on source == "compact"
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-004 · 2026-07-07 · Re-verify encoded practices against primary sources before trusting them
- Trigger: the worktree-parallel skill shipped using a manual script while `claude --worktree` already existed natively; found by re-checking Cherny's own posts (https://x.com/bcherny/status/2017742743125299476) when the user asked if terminal-tab advice was stale (janus refinement session); merged with L-013: a maintenance audit flagged /goal references as drift because the command was absent from the auditing surface, while primary docs confirmed the feature real — the same claim-about-a-moving-target rule, failing in the opposite direction
- Rule: an encoded reference is a claim about a moving target — confirm both staleness and validity against the primary source before relying on it or "fixing" drift
- Scope: portable
- Evidence: 2
- Status: inherited (was: promoted:skill/recalibrate in janus)

## L-005 · 2026-07-06 · Treat aggregator claims and fetch summaries as leads, never evidence
- Trigger: an aggregator site mixed verified practices with unverifiable feature claims — only primary-source-corroborated claims were encoded (janus refinement session); the withheld /goal claim was later confirmed by the official loops post (round-3 research); merged with L-011: a fetch-summary of the workspace paper attributed claims the paper never makes, caught by demanding verbatim quotes; recurred in round 3.5: a subagent report claimed a branch was "up to date with its origin" — the remote had no such branch, and a PR create failed until `git ls-remote` settled it; recurred 2026-07-24 (methodology review): a delegated verifier reported two Anthropic quotes as FABRICATIONS — main-thread raw-HTML fetch showed both sentences real, the refutation itself being the false summary-layer claim (origin: subagent report, falsified by own observation). observed: 2026-08-18 — fired twice in the B2 session: the adversarial verifier's two reported defects were re-run in the main thread before AND after fixing rather than accepted on report, and a probe harness's own numbers were re-measured when they looked wrong (the harness, not the code, was lying). observed: 2026-08-20 — the heartbeat routine's own stored prompt asserted "the unticked boxes are B3, B4, C1, C2, C3" as of 2026-08-19; reading docs/EXECUTION-PLAN.md directly showed all five already ticked (merged via PR #40 the same day). Not trusting the prompt's stale claim and re-deriving from the doc avoided picking already-done work
- Rule: treat aggregator claims and fetch summaries as leads, never evidence — confirm any specific claim verbatim against a primary source before adopting or citing it
- Scope: portable
- Evidence: 5
- Status: inherited (was: promoted:CLAUDE.md in janus)
- observed: 2026-08-20 — fired at issue #43: an Explore agent reported the verdict/E-code data shapes and flagged "no existing id-level join" to ProcessControlPoint; rather than accept its paraphrase of which spec_ids/claim_id belonged where, the exact record contents were read directly from verdicts.json/poisons.json/registry.json before wiring any seed association — the agent's report was directionally right but its own words were never quoted into the implementation unverified

## L-007 · 2026-07-06 · When changing a convention, sweep every mention of it, not just planned edit sites
- Trigger: the adversarial verifier failed the refinement diff because docs/USAGE.md's day-1 section still said "optional Graphify" after the convention changed to default-on; the planned edit list had missed that mention (janus refinement session); recurred in round 3.5 — removing new-worktree.sh missed ARCHITECTURE's component-map row, caught by the docs-consistency fixture rather than a manual sweep. observed: 2026-08-18 — credited by name in L-049's own Trigger ("caught by own L-007 sweep"); fired again at B2 sweeping README question numbers and the EXECUTION-PLAN tick
- Rule: after changing a convention, grep the whole repo for the old wording and reconcile every hit before claiming consistency
- Scope: portable
- Evidence: 2
- Status: inherited (was: promoted:CLAUDE.md in janus)

## L-008 · 2026-07-06 · Stress-test a plan against scale, concurrency, and headless modes before presenting it
- Trigger: user rejected the round-3 plan approval asking "will this perform under stress and scaling?"; the resulting review found 4 real design bugs the plan had missed — ledger cap deadlock, worktree ID collisions, headless gates with no user, mtime loss across clones (janus round-3 session)
- Rule: before presenting a plan, run an adversarial pass over its behavior at scale, under concurrent use, and with no user present — and pair every failure found with a fix, not just a risk note
- observed: 2026-08-18 — FAILED TO HELP on B2: the plan carried a seven-probe verification section and still shipped two defects, because the rule's adversarial axes (scale / concurrency / headless) do not include "what would survive every check I planned and still be false". The verification plan itself needs an adversarial pass, not just the design — see L-056
- Scope: portable
- Evidence: 1
- Status: inherited (was: promoted:CLAUDE.md (Evidence 1 — promoted on explicit user confirmation) in janus)

## L-009 · 2026-07-06 · Seed behavioral fixtures with controlled data, never the repo's live content
- Trigger: bumping L-005 to Evidence 2 broke two session-start fixtures that asserted against the shipped ledger's real entry counts (janus round-3 session)
- Rule: a behavioral fixture must create the data it asserts against (truncate and seed in the sandbox); asserting against live repo content couples tests to unrelated edits
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-010 · 2026-07-06 · Store cross-clone state in file content, never in file mtimes
- Trigger: the recalibration staleness design first used a gitignored marker checked via find -mtime; gitignored files never sync between clones, and git does not preserve mtimes on committed files either — both halves were broken (janus round-3 session)
- Rule: any timestamp or state that must survive a git clone boundary goes in the file's content (e.g. epoch seconds) and is committed; mtimes are per-checkout artifacts
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-012 · 2026-07-06 · Propose the maintenance heartbeat at the end of /bootstrap
- Trigger: user asked why the weekly heartbeat isn't on by default for every project; auto-creating a billed cloud routine silently would violate the escalation-is-proposed rule, but the end of session zero is the natural moment to offer it (janus round-3 evolve session)
- Rule: when a project finishes bootstrapping, propose creating the maintenance heartbeat (one yes, PR-delivery only) instead of waiting for the user to discover it
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-014 · 2026-07-06 · Mechanisms enter the template only after dogfooding evidence demonstrates the need
- Trigger: round-3.5 subtraction removed Graphify (never built here), the ARCHIVE.md + ≤25 cap (ledger held 12 entries), and staged expiry policies — all machinery added for problems no session had hit, against the repo's own Evidence >= 2 discipline (janus round-3.5 session)
- Rule: disciplines can be designed up front, but a mechanism (tool, file, cap, fallback) enters the scaffold only after real use demonstrates the need it serves
- observed: 2026-08-18 — fired twice in one /evolve: it cleared L-052's write-side hook (Evidence 5, need demonstrated) and refused an L-049 `integrate-worktree.sh` helper (Evidence 1, premature)
- Scope: portable
- Evidence: 3
- Status: inherited (was: promoted:CLAUDE.md in janus)

## L-015 · 2026-07-06 · Platform owns mechanisms; the template keeps only the disciplines it adds
- Trigger: the explorer/planner agents duplicated native exploration/planning subagents, and scripts/new-worktree.sh duplicated native claude --worktree; both were removed with their embedded disciplines consolidated into plan-feature and worktree-parallel (janus round-3.5 session)
- Rule: before encoding a mechanism, check whether the platform provides it natively; encode only the discipline the scaffold adds on top, and let the platform's mechanism carry it
- observed: 2026-08-18 — L-045's Rule is literally this rule applied to skill invocation control; at B2 it kept the cwd-drift check inside the existing hook rather than minting a new one
- Scope: portable
- Evidence: 2
- Status: inherited (was: promoted:CLAUDE.md in janus)

## L-016 · 2026-07-06 · Weigh subtraction as seriously as addition when reviewing for improvement
- Trigger: asked "any enhancements?", the audit proposed only fixes and additions; the owner's redirect ("consider features we should remove") produced the round's highest-value changes — four feature removals (janus round-3.5 session)
- Rule: when reviewing a system for improvement, audit what fails to earn its place with the same rigor as what is broken or missing, and propose removals alongside fixes
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-017 · 2026-07-06 · Design from first principles; cite existing implementations as evidence, not as the template
- Trigger: the J-brain memory design was framed "from how contextual memory actually works in current harnesses"; the owner rejected it — "I want to build a harness... what should be designed" — and the first-principles redesign (prediction machine + memory pipeline) superseded it (janus round-3.5 session)
- Rule: when asked to design a system, derive the design from the problem's own invariants; use existing implementations as evidence for or against choices, never as the starting shape
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-018 · 2026-07-06 · Preserve foreign uncommitted changes in their own labeled commit before starting your own
- Trigger: the working tree carried uncommitted docs-consistency fixtures written outside the session (the start-of-session snapshot said clean); committing them unmodified, clearly labeled, before any session work kept authorship legible and the changes safe — they caught a real bug two commits later (janus round-3.5 session)
- Rule: treat uncommitted working-tree changes you did not make as someone else's work — verify what they are, then commit or stash them separately with a label stating their origin, before your own commits touch the tree
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-019 · 2026-07-24 · Name concrete source URLs in an encoded source list, never a category
- Trigger: five new Anthropic posts (claude.com/blog, 2026-07-16..24) had to be hand-delivered by the user because /recalibrate never reached them; the skill names "Anthropic's engineering blog" at SKILL.md:22 but its Hold-in-mind #1 at :14 says "Aggregator and blog claims are leads to verify, never evidence" — the skill contradicts itself, and line 14 silently downgraded L-005's *method* rule (confirm verbatim against a primary source) into a *source-class* rule (blogs are second-class)
- Rule: a source list is executable only if it names concrete URLs; gate credibility on method (verbatim confirmation) rather than on the publisher's format, or whole publications go unread
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-020 · 2026-07-24 · A provenance stamp written by anything but a real run is a false green
- Trigger: .claude/memory/recalibrated-at holds 1783394187 (2026-07-07) written by design commit 539a12e, not by a run — `git log` on the file shows exactly one commit, so /recalibrate has never actually completed in this repo, yet the 30-day staleness nudge reads as satisfied (janus claude-5 realignment session)
- Rule: write a run stamp only from the run it certifies; a stamp set by the commit that designed the mechanism records provenance that never happened and suppresses the very nudge meant to catch it
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-021 · 2026-07-24 · Verify which memory tiers survive the environments you actually run in
- Trigger: code.claude.com/docs/en/memory states verbatim "Auto memory is machine-local. All worktrees and subdirectories within the same git repository share one auto memory directory. Files are not shared across machines or cloud environments" — so this scaffold's headless heartbeat routine and every cloud session start with an empty ambient tier, a consequence the memory-pipeline design never accounted for (janus claude-5 realignment session)
- Rule: for each memory tier a design depends on, confirm which execution environments it actually reaches; a tier that is absent headless or in the cloud cannot carry anything the automation relies on
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-022 · 2026-07-24 · Keep volatile platform facts out of inherited memory, or state their expiry
- Trigger: the claude-5 findings include vendor state that will rot (auto-memory locality, a 1,536-char listing truncation, the current frontmatter field set); /replicate copies every `Scope: portable` entry into every child forever and entries are never deleted, so filing them portable would breed claims with no expiry and no deletion path (janus claude-5 realignment session)
- Rule: file the durable discipline as the portable rule and keep the vendor fact in the Trigger line as dated evidence — an inherited entry must stay true when the platform changes under it
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-023 · 2026-07-24 · A platform's truncation ceiling is not a budget — don't swap a binding discipline for it
- Trigger: this session's own plan proposed replacing the repo's ≤50-word skill-description cap with the docs' "truncated at 1,536 characters in the skill listing"; an adversarial pass caught that the ceiling is where rendering stops, not a target — adopting it would license ~15,360 chars of always-loaded description against ~2,816 today, a 5.5x increase, while quoting "every token added depletes Claude's attention budget" as the warrant (janus claude-5 realignment session)
- Rule: when replacing a scaffold cap with a native limit, check whether the native number is a target or a failure threshold; substituting a ceiling for a binding discipline loosens the constraint while appearing to modernize it
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-024 · 2026-07-24 · Aim a recalibration at the conventions it would be most costly to lose
- Trigger: the claude-5 context-engineering post ("Give Claude rules" -> "Let Claude use judgement", "Repeat yourself" -> "Simple tool descriptions", "Memory in CLAUDE.md files" -> "Auto-memory") challenges this scaffold's own signature mechanisms — the Hold-in-mind ritual, the prime directives, and the manual reflect/evolve pipeline — and the first draft of the realignment plan proposed changes everywhere except there (janus claude-5 realignment session)
- Rule: a recalibration that returns only comfortable findings has not recalibrated — enumerate the conventions the scaffold is proudest of and file the evidence against them by name
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-025 · 2026-07-24 · Spend always-loaded memory on gotchas, not on what the codebase already shows
- Trigger: claude.com/blog's claude-5 context-engineering post says verbatim "Keep your CLAUDE.md lightweight and briefly describe what your repo is for, but spend most of the tokens on gotchas inside of the codebase", and the /doctor trim check "cuts content Claude can derive from the codebase, such as directory layouts, dependency lists, and architecture overviews"; this repo's CLAUDE.md carried a ## Map section of exactly that derivable content and no gotchas at all (janus claude-5 realignment session)
- Rule: in an always-loaded memory file, a line that restates the directory tree is paying permanent rent for something a single `ls` recovers — spend the budget on traps that bite and are invisible from the code
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-026 · 2026-07-24 · Derive a validator's allowlist from the primary source, not from what you just read
- Trigger: the new frontmatter fixture's field sets were written from the fields this session happened to have quoted — it then rejected documented-valid input (`shell:` on a skill; `color:`/`skills:`/`isolation:` on an agent, where 5 of 16 documented fields were known) and its lowercase-only regex made every camelCase field invisible to validation, including misspellings; the adversarial verifier caught all of it against the docs (janus claude-5 realignment session)
- Rule: when a check encodes a set of valid values, build the set by enumerating the primary source in that moment — a validator written from recall is a claim about a moving target that fails in both directions, rejecting what is valid and silently passing what is not
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-027 · 2026-07-24 · Refresh remote-tracking refs before reasoning about what has already landed
- Trigger: `git log --oneline origin/main..HEAD` ran without a prior fetch and reported 12 unmerged commits; all 12 were already on main via PRs #4-#6. A scope decision was put to the user on that count, and the resulting PR opened CONFLICTING against a main that had since landed its own /evolve round, forcing the PR to be closed and rebuilt (janus doctor+evolve session). Distinct from L-005's round-3.5 branch incident: there the remote branch never existed and a report asserted it unverified (a trust-the-summary failure); here the ref existed but the local cache was stale — the primary-source command itself lied
- Rule: run `git fetch` before any command that reads a remote-tracking ref — `origin/*` is a local cache, and a comparison against an unfetched one returns a confidently stale answer, not a visibly wrong one
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-028 · 2026-07-24 · Audit a delegated report's premises, not only its citations
- Trigger: the memory-curator agent's promotion proposal was checked line by line against LEARNINGS.md and every Evidence count held — yet four of its five proposed promotions were already merged on main, because its unstated premise (that the working tree reflected the shared branch) was never tested; the agent was scoped to the local tree and could not have known (janus doctor+evolve session)
- Rule: when auditing a subagent's report, name and test its unstated premises and the scope it could actually observe — correctly verified citations under a false premise still yield a wrong conclusion
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-029 · 2026-07-24 · Pass multi-line command bodies through a file, never inline command substitution
- Trigger: `gh pr create --body "$(cat <<'BODY' ...)"` failed with `unexpected EOF while looking for matching quote`; writing the identical body to a file and passing `--body-file` succeeded unchanged. A heredoc piped directly to stdin (`git commit -F -`) was unaffected — only the nesting inside command substitution broke (janus doctor+evolve session)
- Rule: write multi-line text — PR and issue bodies, JSON payloads, config blocks — to a file and pass it by path; never nest a heredoc inside command substitution inside a quoted argument
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-030 · 2026-07-24 · Derive budgets from operational guidance and dogfooding, never from a lens hyperparameter
- Trigger: ARCHITECTURE claimed the workspace paper "found ~10–25 simultaneously active concepts" and derived the ≤20 cap from it; main-thread verbatim read (methodology review) showed the paper *chooses* "no more than 25" as a J-lens hyperparameter, calls the lens "an imperfect tool", and contains no such range and no claims about instruction files — the external reviewer who praised the derivation had taken the repo's framing at face value (origin: fetched content, main-thread verified; prompted by user-supplied critiques)
- Rule: ground every encoded budget in operational guidance or dogfooded evidence; an interpretability measurement choice is convergent context at most, and citing it as a derivation is numerology
- Scope: portable
- Evidence: 1
- Status: inherited (was: promoted:docs/ARCHITECTURE (Evidence 1 — applied on explicit user confirmation, methodology review) in janus)

## L-031 · 2026-07-24 · A cross-session signal must carry enough context to reconstruct why it fired
- Trigger: correction signals logged only `correction:<timestamp>`; a Stop-hook nudge fired on a leftover signal whose cause could only be guessed at, and the cross-session leftover-signals path offered a bare count with no recoverable context (origin: own observation, this session)
- Rule: any signal a later session may consume must carry its cause — matched keyword, source excerpt, or file path — not just a timestamp; a context-free signal forces the consumer to guess
- Scope: portable
- Evidence: 1
- Status: inherited (was: promoted:hooks/prompt-signal (Evidence 1 — applied on explicit user confirmation, methodology review) in janus)

## L-032 · 2026-07-24 · Git-shared memory is an injection channel — untrusted-origin evidence never promotes unreviewed
- Trigger: repo-wide grep found zero trust boundaries on the ledger → CLAUDE.md → /replicate pipeline while Anthropic names the exact channel: "An injection that lands in any of these is reloaded each time the agent starts" and "Tool output is an attack surface even when the tool is trusted" (how-we-contain-claude, main-thread verified 2026-07-24; origin: fetched content + user-supplied critique)
- Rule: an entry whose evidence originates in untrusted content — fetched pages, tool output, repo text — promotes into always-loaded context only with the user's explicit confirmation, whatever its Evidence count
- Scope: portable
- Evidence: 1
- Status: inherited (was: promoted:skill/evolve (Evidence 1 — applied on explicit user confirmation, methodology review) in janus)

## L-033 · 2026-07-24 · A promoted rule with no observed effect needs a retirement path
- Trigger: retirement fired only on contradiction, so a useless rule had no exit; every loop metric counted compliance (budget assertions, claims-checked tallies), never outcomes — against "you should consider adding complexity _only_ when it demonstrably improves outcomes" (building-effective-agents, main-thread verified; origin: user-supplied critique + fetched content)
- Rule: track when promoted rules visibly fire or fail to help, and propose retirement for rules with no observed effect — compliance counting is not outcome evaluation
- Scope: portable
- Evidence: 1
- Status: inherited (was: promoted:skill/evolve (Evidence 1 — applied on explicit user confirmation, methodology review) in janus)

## L-034 · 2026-07-24 · Evidence units are independent incidents; merges take the max, never the sum
- Trigger: the memory-curator brief instructed "summing their Evidence" across merged near-duplicates — two unrelated anecdotes could manufacture a promotable 2 — and nothing anywhere defined recurrence or barred same-session double-bumps (origin: own observation of repo text, methodology review)
- Rule: an Evidence unit is a distinct incident from a separate session or task; the same event never counts twice, one session bumps an entry at most once, and merged entries take the max of their counts
- Scope: portable
- Evidence: 1
- Status: inherited (was: promoted:skill/reflect (Evidence 1 — applied on explicit user confirmation, methodology review) in janus)

## L-035 · 2026-07-24 · Rules crossing a generation boundary get human review before landing active
- Trigger: /replicate copied promoted rules straight into every child's always-loaded rules block while USAGE promised children "re-earn promotion" — a contradiction that left the generational injection path Anthropic warns about ungated; ledger census at review time: 29/29 entries marked portable (origin: own observation of repo text + fetched content)
- Rule: a rule that will land active in a descendant's always-loaded context requires the user's explicit yes at the generation boundary; inherited ledger entries stay inactive until re-earned
- Scope: portable
- Evidence: 1
- Status: inherited (was: promoted:skill/replicate (Evidence 1 — applied on explicit user confirmation, methodology review) in janus)

## L-036 · 2026-07-24 · A refutation is a claim — verify absence with substring rigor, not sentence matching
- Trigger: a delegated verifier reported "Once an agent discovers a bug class, the relevant file is updated to prevent it recurring" as a fabricated quote because its exact-string check matched a punctuation-terminated sentence against text that continues "…in future code."; a raw-HTML substring fetch proved the sentence real (origin: subagent report, falsified by own observation, methodology review)
- Rule: verify a claimed absence with the same rigor as a claimed presence — match substrings against raw source, never full sentences with terminal punctuation, and treat a delegate's refutation as unverified until reproduced
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-037 · 2026-07-24 · The self-learning claim is unproven until a bootstrapped child measures outcomes
- Trigger: methodology review adopted the critique that nothing measures whether promoted rules reduce failures; the full baseline-vs-scaffold evaluation was deliberately deferred — the template has no real coding tasks to measure (origin: user-supplied critique, user decision 2026-07-24). Re-open trigger: the first bootstrapped child with real task history. Protocol sketch preserved: fixed task set; arms = plain Claude Code / verify-only / memory-only / full scaffold; measure task success, repeated-error rate, interventions, tokens; test longitudinally (task N benefits from lessons of tasks 1..N-1)
- Rule: before claiming a learning loop improves outcomes, run the deferred baseline comparison in a bootstrapped child — efficacy notes on promoted rules are the interim signal, not the proof
- Scope: portable
- Evidence: 1
- Status: inherited (was: candidate in janus)

## L-038 · 2026-07-24 · Gate the commit on the verifier's exit in the same command chain
- Trigger: a commit ran as an unconditional statement after the verify invocation in one compound command; the suite was red (a component-map fixture) and the red commit landed, needing an amend after the fix (origin: verify failure, own observation, this session)
- Rule: never pipe a gating command's output before using its exit status — run the gate bare (redirect to a file if output is needed) or set pipefail in the same shell — then chain the commit with && on that status; sequential statements commit red results, and a pipe makes the status the last stage's, not the gate's
- Scope: portable
- Evidence: 2 (the red commit that landed as a sequential statement, janus 2026-07-24; `verify.sh full 2>&1 | tail -4 && git commit` laundering the exit code through tail, aegis 2026-08-16 — two independent incidents in separate sessions, merged from L-050 whose own title recorded it as "evidence of L-038 recurring")
- observed: 2026-08-18 — fired throughout the B2 session: every gate ran bare into a log file with `echo EXIT=$?`, and no exit code was laundered
- Status: candidate — RIPE, absorbed L-050's wording 2026-08-18 on user confirmation

## L-039 · 2026-08-16 · A work order's done-means check must be executable inside the agent's allowlist
- Trigger: the WO-C2 issue-template run (6d0d805) needed a YAML parse to verify its own output, no allowlisted command could do one, and the dispatched agent burned ~50 turns on 35 permission denials before dying on max-turns; the fix (64b13c5) put the YAML check inside scripts/verify.sh. The lesson was written as prose comments in verify.sh and tests/test_issue_templates.py but never entered this ledger — backfilled by the 2026-08-16 memory audit (origin: verify failure, own observation)
- Rule: before dispatching a work order, confirm every done-means check is runnable via an allowlisted command — verification that needs an unlisted tool becomes a denial loop, not a closed loop
- Scope: project
- Evidence: 1
- Status: promoted:skill/recalibrate — resolved; SKILL.md now reads \"The gate is method, not publisher: any source can be primary\" (ledger status was stale)

## L-040 · 2026-08-16 · A mechanical template copy leaves the memory loop wired but dead — run the provisioning ritual
- Trigger: this repo was stamped from janus on 2026-07-27 by template copy, not /replicate; every heredity transform was skipped (parent statuses and retired entries crossed, sources-seen watermark intact, identity unrewritten), and in 3 weeks of real work no session ran /reflect, /evolve, or /recalibrate despite the Stop hook and session-start nudging every session — real lessons were routed into code comments instead of the ledger (origin: own observation, 2026-08-16 memory audit; retroactive fix in this branch)
- Rule: when adopting a scaffold whose skills assume a provisioning ritual, run the ritual's transforms — or apply them retroactively before real work continues; nudges alone do not revive a loop that provisioning left dead
- Scope: project
- Evidence: 1
- Status: candidate

## L-041 · 2026-08-16 · The skill-frontmatter authority is the Agent Skills spec at agentskills.io, with Claude Code extensions on top
- Trigger: /recalibrate 2026-08-16 — github.com/anthropics/skills spec/agent-skills-spec.md (the authority add-skill and recalibrate encode) now redirects to agentskills.io/specification; the standard defines only {name, description, license, compatibility, metadata, allowed-tools} while the Claude Code docs state verbatim "Claude Code extends the standard with additional features" and document when_to_use, argument-hint, disable-model-invocation, disallowed-tools etc. as product fields (https://agentskills.io/specification, https://code.claude.com/docs/en/skills)
- Rule: when validating or citing skill frontmatter, name the standard and the product extension separately — a field valid in Claude Code may be rejected by spec-side tooling, and the spec's location is itself a moving target
- Scope: portable
- Evidence: 1
- Status: candidate

## L-042 · 2026-08-16 · Encode "unused by policy" as a discipline with a doc pointer, never a frozen enumeration of a growing surface
- Trigger: /recalibrate 2026-08-16 — ARCHITECTURE's "Deliberately unused events: PreToolUse, PreCompact, Notification, SubagentStop" reads as the full set, but the hooks reference now lists ~31 events including InstructionsLoaded ("When a CLAUDE.md or .claude/rules/*.md file is loaded into context"), WorktreeCreate/Remove, PostCompact, SubagentStart (https://code.claude.com/docs/en/hooks)
- Rule: when a convention names the members of a platform surface, it rots as the surface grows — encode the policy ("only these events are used, add hooks only with a purpose") and point at the platform's list instead of copying it
- Scope: portable
- Evidence: 1
- Status: candidate

## L-043 · 2026-08-16 · Block-level HTML comments in CLAUDE.md are stripped before injection — sentinel markers cost zero context
- Trigger: /recalibrate 2026-08-16 — memory docs state verbatim "Block-level HTML comments (`<!-- maintainer notes -->`) in CLAUDE.md files are stripped before the content is injected into Claude's context" (https://code.claude.com/docs/en/memory); the scaffold's janus:facts/janus:rules sentinels are exactly such comments, so the budget accounting can stop treating them as spent lines
- Rule: in an always-loaded memory file, machine markers and maintainer notes are free when written as block-level HTML comments — spend visible lines only on content the model must read
- Scope: portable
- Evidence: 1
- Status: candidate

## L-044 · 2026-08-16 · Auto mode is the platform default — broad allow rules are set aside, so guarantees must ride on narrow runner-shaped rules
- Trigger: /recalibrate 2026-08-16 — claude.com/blog states verbatim "Starting on August 14, new sessions on Pro, Max, and Team plans will run in auto mode" and "Permission rules still fire before the classifier in auto mode, except for allow rules broad enough to grant arbitrary code execution" (https://claude.com/blog/auto-mode-default-in-claude-code); this session itself hit the auto-mode classifier, and the repo's single narrow allow rule (Bash(scripts/verify.sh *)) kept working
- Rule: design committed allowlists as narrow, runner-shaped rules — in auto mode a broad allow rule is suspended, so any workflow guarantee that depends on one silently stops holding
- Scope: portable
- Evidence: 1
- Status: candidate

## L-045 · 2026-08-16 · Side-effect skills can declare disable-model-invocation — the platform now carries the operator-timing gate
- Trigger: /recalibrate 2026-08-16 — skills docs document verbatim a `disable-model-invocation` field ("Set to `true` to prevent Claude from automatically loading this skill... for workflows with side effects or that you want to control timing, like /commit, /deploy") plus `disallowed-tools` (https://code.claude.com/docs/en/skills); the scaffold's side-effect skills (ship, replicate, evolve) encode that timing discipline only as in-body confirm gates
- Rule: where the platform grows a native mechanism for an encoded discipline, propose migrating the mechanism and keep only the judgment the scaffold adds (L-015 applied to skill invocation control) — adoption is an /evolve decision, not a silent edit
- Scope: portable
- Evidence: 1
- Status: candidate

## L-046 · 2026-08-16 · /evolve routes each lesson to the highest enforceable rung, not to prose by default
- Trigger: user correction 2026-08-16 during this repo's memory audit — "why would CLAUDE.md just track these but not build a solution to fix these?"; this repo is the dogfooded case: it already builds mechanisms where a core is checkable (docs-consistency fixtures, redaction gate, purity tests) while /evolve's routing knew only prose targets (origin: user correction; canonical entry janus L-040, applied to the shared skills here the same day)
- Rule: route every promotion up an enforcement ladder — hook/fixture, then verifier check, then skill, then path rule, then CLAUDE.md prose as last resort — and re-ask on recurrence whether a promoted prose rule has revealed a checkable core
- Scope: portable
- Evidence: 1
- Status: promoted:skill/evolve (Evidence 1 — applied on explicit user confirmation, 2026-08-16)

## L-047 · 2026-08-16 · Make judgment disciplines auditable: document the ritual, presence-check mechanically, judge substance independently
- Trigger: user correction 2026-08-16 re inherited L-008 — "can't there be an agent log … so an independent verify can confirm this happened?"; plan-feature required the Predicted-failure-modes artifact but nothing independent confirmed the ritual ran (origin: user correction; canonical entry janus L-041). observed: 2026-08-16 — the verifier's WALKING SKELETON audit flagged the absent failure-modes trail unprompted (roadmap-driven change, no /plan-feature run), correctly stopping short of a process FAIL while naming the gap — the rule fires as designed
- Rule: for a judgment discipline, require a named artifact of the ritual, then split enforcement — mechanical presence-check where possible, verifier-agent judgment of substance always — so compliance stops depending on the actor's own report
- Scope: portable
- Evidence: 1
- Status: promoted:skill/plan-feature+agent/verifier (Evidence 1 — applied on explicit user confirmation, 2026-08-16)

## L-048 · 2026-08-16 · A merged milestone is a trigger, not a stopping point — surface the next task mechanically
- Trigger: user correction 2026-08-16 — after SCH01 merged the session reported "say the word" while docs/EXECUTION-PLAN.md named SCH02 as next; the Conduct-don't-wait directive was prose with no mechanism (origin: user correction; canonical entry janus L-042, hook mirrored here the same day)
- Rule: when a repo carries an execution plan, the harness surfaces the first unticked task at session start and the session continues it — continuation is the harness's job, not the user's prompt
- Scope: portable
- Evidence: 1
- Status: promoted:hooks/session-start (Evidence 1 — applied on explicit user confirmation, 2026-08-16)

## L-049 · 2026-08-16 · Mirroring a shared scaffold file between repos by blind copy clobbers repo-specific divergence
- Trigger: two incidents this session — copying janus's SELF-IMPROVEMENT.md over aegis-sentinel's reverted the corrected CI wording (caught by own L-007 sweep), and copying janus's test-hooks.sh deleted this repo's *.yml quick-arm fixtures undisclosed (caught by the adversarial verifier post-commit); both from `cp` of a diverged file (origin: verify failure + verifier report, confirmed against git history)
- Rule: before mirroring a scaffold file across repos, diff it against the destination and port the change as a patch — a diverged file is never safely replaced whole
- Scope: portable
- Evidence: 1
- Status: candidate

## L-050 · 2026-08-16 · Piping verify output through tail launders the exit code — evidence of L-038 recurring [RETIRED — merged into L-038]
- Trigger: `verify.sh full 2>&1 | tail -4 && git commit` committed and pushed a red suite this session — the pipeline's exit status is tail's, not verify's, so the && gate held a door that was already open; caught one command later and amended (origin: verify failure, own observation). observed: 2026-08-16 — L-038 ("gate the commit on the verifier's exit in the same command chain") fired in spirit but its rule assumed the exit code reaches the chain; a pipe breaks that assumption
- Rule: (superseded — this wording now lives in L-038, which this entry's evidence bumped to 2)
- Scope: portable
- Evidence: 1
- Status: retired — merged into L-038 (same rule, refined wording); /reflect should have bumped L-038 rather than appending a twin

## L-051 · 2026-08-16 · Worktree subagents deliver untracked files — integrate by clobber-checked copy, never by branch merge
- Trigger: the first collector-wave integration ran `git merge worktree-agent-...` and got a silently empty merge — worktree subagents are told not to commit, so their branches carry no commits and the deliverables sit untracked in the worktree directory; the working pattern (repeated 6x this session) is: list the worktree's `git status --porcelain` untracked paths, refuse any path that already exists in the destination (L-049's clobber guard), copy the rest, re-verify in the main checkout (origin: own observation, verify failure)
- Rule: instruct worktree subagents to commit in their worktree and integrate by merging their branch (gitignore then filters node_modules-style noise); for a subagent that did not commit, fall back to copying its untracked files with a per-path exists-check — merging an uncommitted worktree's branch integrates nothing. Either way, re-run the full suite in the destination
- Scope: portable
- Evidence: 2 (empty-merge failure at the collector wave; instruct-commit-then-merge worked cleanly for A1, MCP01, and A2+B1)
- Status: promoted:skill/worktree-parallel — step 3 now instructs each track to commit in its worktree, step 5 carries the empty-merge check and the clobber-checked-copy fallback

## L-052 · 2026-08-16 · The shell's working directory between tool calls is undefined — anchor every path
- Trigger: four separate commands this session failed with "not a git repository" / "No such file or directory" because the session cwd had silently reverted to the home directory between calls (worker restarts and environment reconnects reset it); each failure cost a retry with an explicit cd (origin: own observation, repeated)
- Rule: treat the working directory between tool calls as undefined — it may reset OR persist, and believing it always resets is itself how `web/web/src/...` gets written. Start every compound shell command with an absolute-path cd (or use absolute paths throughout), and never assume the previous call's working directory either survived or did not; and within one compound command, every segment after a `cd` inherits it, so re-anchor before each phase that needs a different directory (web gates in `web/`, repo scripts at the root)
- Scope: portable
- Evidence: 5 (four cwd-reset failures early in that session; three conductor passes then ran `scripts/verify.sh` from `web/` inside a compound command — exit 127 each time, twice AFTER this rule was written; recurred 2026-08-18 in the B2 session in the OTHER direction — cwd PERSISTED from a prior `cd web`, so two heredoc writes landed at `web/web/src/...` and one `cat > web/src/app/...` failed outright. The promoted mechanism covers gate RUNS, not file WRITES: `verify-web.sh` self-anchors, but a heredoc path does not)
- Status: promoted:hooks/post-edit-verify + scripts/verify-web.sh — two halves, because one mechanism cannot see both. RUN side: `verify-web.sh` self-anchors and runs all frontend gates + redaction from any cwd. WRITE side (added 2026-08-18 after the B2 recurrence): `post-edit-verify.sh` rejects a written path that repeats an adjacent directory segment — the fingerprint of a relative path resolved from a drifted cwd — with six fixtures in `scripts/test-hooks.sh` including a `Dir/Dir.ext` false-positive guard. A self-anchoring script cannot anchor a heredoc path, which is why prose alone kept failing. The re-anchor rule stays as the judgment neither mechanism carries: the hook never sees a `cd` inside a Bash command.

## L-053 · 2026-08-16 · `as T` on JSON imports is a vacuous per-record check — wire JSON through an assignability position and prove it with a falsifier
- Trigger: the A2+B1 adversarial verifier renamed a required key inside a verdict record of an imported JSON array and `tsc --noEmit` stayed green — `index.ts` wired every JSON file through `as T` casts, and TypeScript `as` checks only top-level bidirectional comparability, so a broken record inside any array is swallowed; the doc comment and commit message both claimed "tsc checks every JSON file" (origin: verifier FAIL, prescribed falsifier). observed: 2026-08-18 — fired as designed at B2: after `ReconciliationReport` gained four fields and a sibling array export was added, the prescribed falsifier (rename `member_ref` in one delta) still failed tsc with TS2345, confirming the assignability position survived the edit
- Rule: never claim the compiler checks imported JSON unless the JSON flows through an assignability position — a plain annotation or a generic parameter (`checked<T>(json: Widen<T>)`, literal unions widened to primitives since JSON inference widens strings) — and prove the wiring by making a representative deep mutation fail the build before shipping the claim
- Scope: portable
- Evidence: 1
- Status: candidate

## L-054 · 2026-08-18 · Commit the baseline before running revert-based falsifier probes
- Trigger: the B2 deletion-falsifier run reverted each probe with `git checkout -- <mock>.json`, which discarded the SAME task's uncommitted edits to that file (four keys the emitter change had just added); probes 2–5 then ran against a half-reverted mock and all failed the build with a type error that read like a real defect, costing a full diagnostic detour before the cause — my own revert — was spotted. Committing the verified baseline first made all seven probes pass unchanged (origin: own observation, verify failure). Recurred at C1 (separate task, same session): falsifier F1 mutated types.ts and reverted with `git checkout -- types.ts` BEFORE the C1 commit existed, silently discarding the uncommitted Severity/Q8/optionality alignment; caught because the file vanished from `git status` rather than by any failure — the quiet variant is worse than B2's loud one
- Rule: a falsifier probe whose undo is `git checkout --` can only restore committed state, so commit (or stash) the work under test before the first probe — and when a probe fails in a way the mutation cannot explain, suspect the harness before the code
- Scope: portable
- Evidence: 2 (B2 probe run; C1 falsifier F1 — independent tasks)
- Status: candidate — RIPE

## L-055 · 2026-08-18 · Prerendered HTML is one line — `grep -c` cannot count occurrences in it
- Trigger: the B2 probe harness measured rendered signals with `grep -c`, which counts matching LINES; Next.js prerenders each route as a single-line HTML file, so every signal reported 0 or 1 regardless of how many times it appeared — two probes (source deletion, exclusion deletion) looked like no-ops until re-measured with `grep -o … | wc -l`, which showed the real 5→0 and 1→0 transitions (origin: own observation during falsifier verification)
- Rule: when asserting against minified or prerendered single-line output, count occurrences with `grep -o <pattern> | wc -l`, never `grep -c`; and rebuild before measuring, since a stale artifact from the previous probe reads as the current baseline
- Scope: portable
- Evidence: 1
- Status: candidate

## L-056 · 2026-08-18 · Deletion falsifiers cannot catch authored prose about state — mutate the enum too
- Trigger: B2 shipped seven passing deletion probes, and the adversarial verifier still found two real defects by mutating a state VALUE instead of removing data: `after_dispositions: "RATIFIED"` made the page render "RATIFIED holds" and "RATIFIED not reached" simultaneously (the second hardcoded inside the sentence advertised as computed), and the legal state `STALE` made every rung read "not reached" and silently dropped the `aria-current` landmark, with tsc and the build green. Deleting data can never flip a hardcoded claim about a state the data never takes (origin: verifier report, confirmed by own re-run)
- Rule: pair every deletion falsifier with a value falsifier — set each enum-valued field to every other member its schema permits, not just the one the fixture emits — and where a rendered sentence asserts a state, derive it from that field or make the unhandled case a compile error (an exhaustive `switch` with a `never` arm), never a literal
- Scope: portable
- Evidence: 1
- Status: promoted:agent/verifier + CLAUDE.md (Evidence 1 — applied on explicit user confirmation, 2026-08-18); the probe procedure lives in the verifier's step 2, its plan-time half is the fourth adversarial axis on the L-008 bullet

## L-057 · 2026-08-18 · Manual falsifier probes prove a page once; only a committed test keeps it proven
- Trigger: five consecutive frontend rounds (A3, A4, A5, B2 twice over, in two independent sessions) were verified by an adversarial subagent deleting a seed/artifact row, rebuilding, and diffing the built HTML — every round PASSed and every round's verifier closed with the same uncovered finding: nothing automated guards the result, because `verify.sh full` is Python-only and `verify-web.sh` is tsc + build + redaction (origin: verifier reports, four rounds running). Recurred 2026-08-20 (separate session, issue #43's verdict-tinted-process-graph): the verifier proved the new tint/gate join live (flip a record's status, delete the one compile error, rebuild, diff the static HTML, restore) and closed with the identical uncovered finding — no committed re-runnable script, so a future regression here is caught only if another human/agent repeats the manual probe
- Rule: when the same manual verification is re-performed every round, the repetition is the evidence it belongs in the suite — promote the probe to a committed test (parse the seed/artifact, assert every row and computed count appears in the built HTML) rather than re-running it by hand
- Scope: portable
- Evidence: 5 (A3, A4, A5, B2, and issue #43 verifier reports each flag it independently)
- Status: candidate — the ladder rung is a build-output assertion test wired into `verify-web.sh` and web-verify CI

## L-058 · 2026-08-18 · Two sessions picking "the next unticked box" will build the same box — claim it visibly before starting
- Trigger: the daily heartbeat Routine fired into a fresh session that read the same plan, picked B2, built it, and merged it as PR #37 while this long-running session was independently building B2 for PR #38; the duplicate surfaced only as `mergeable_state: dirty` at merge time, after a full build + adversarial-verify cycle had been spent on the losing implementation, and both sessions had already appended a colliding `L-054` to the ledger (origin: own observation, merge conflict)
- Rule: before starting a plan box, check for an in-flight claim on it (open PRs and unmerged remote branches) — and when starting, make the claim visible on the remote; a plan read from `main` is a snapshot, not a lock, and local memory does not travel between machines
- Scope: portable
- Evidence: 1
- Status: promoted:hook — `session-start.sh` now pairs the next-box line with unmerged-remote-branch detection (bounded `ls-remote`, offline-safe), so the collision is announced at session start instead of at merge. observed: 2026-08-20 — fired as designed: the hook's unmerged-branch line sent this firing to inspect `claude/next-build-priorities-nqfzg0` and `claude/janus-memory-skills-eval-vtnp3y` before picking work, which is what surfaced the stranded-branch problem in L-059 rather than a silent B3 duplicate

## L-059 · 2026-08-20 · A branch reused after its PR merges stops being visible to the claim-check — cut a fresh branch per task, always
- Trigger: own observation during the claim-check step — `claude/next-build-priorities-nqfzg0` and `claude/janus-memory-skills-eval-vtnp3y` each had their PR (#37, #39 respectively) merged, then MORE task commits (B3, B3-hardening, B4, C1, C2, C3) were pushed onto the same branch names afterward instead of cutting new branches per step 1; those later commits were never included in any PR and sat unmerged for over a day across multiple 4h heartbeat firings — correctly not duplicated (L-058's claim-check held), but also never delivered, since "open PR" and "claimed unmerged branch" are the only two states the protocol checks for, and "unmerged branch with no open PR, containing real finished work" is a third state nothing was watching for. Recovered this firing only by treating the stray branch as archaeology: diffing it against every already-merged PR to determine which commits were genuinely undelivered, merging main, independently verifying, and shipping it as PR #40
- Rule: never push a new task's commits onto a branch whose PR has already merged or closed — step 1's `git checkout -B claude/<task-id>-<slug> origin/main` is per-task, not per-session, so re-run it fresh even when continuing work that feels related. And when the claim-check finds an unmerged `claude/*` branch with no corresponding open PR, don't just skip it as "claimed" — check whether its PR already merged for earlier content and it was silently reused: if so it's stranded finished work to recover (merge base, verify, PR), not live in-flight work to avoid
- Scope: portable
- Evidence: 1
- Status: candidate

## L-060 · 2026-08-20 · A red check on a PR may be an undocumented third-party integration, not the repo's own CI gate — verify which before reacting
- Trigger: own observation — PR #40 showed a failing `Vercel` commit status while the repo's actual documented CI contract (`scripts/verify.sh full` + `scripts/verify-web.sh`, mirrored by GitHub Actions `verify`/`web-verify` per CLAUDE.md) was fully green; grepping the repo found no `vercel.json` and no docs mentioning Vercel, and the check didn't exist on either of the two prior merged PRs (#37, #39), confirming it was a newly-installed GitHub App integration whose config lives in a dashboard this session has no token for
- Rule: before treating a red PR check as work to fix, confirm it's part of the repo's own documented CI contract (grep `CLAUDE.md`/`docs/` for the tool, check for its config file in-repo) — an undocumented third-party status with no in-repo config is very likely an Owner-side dashboard setting; don't guess at a fix by adding speculative config files, and don't hold the PR on it. File an Owner-action issue naming the specific setting suspected, note it on the PR, and let the documented gate be the delivery bar
- Scope: portable
- Evidence: 1
- Status: candidate

## L-062 · 2026-08-20 · A background verifier gates the PR, not the commit — commit once local checks are green
- Trigger: this heartbeat session ran local verify (`scripts/verify.sh full`, `verify-web.sh`) green, then launched a background adversarial `verifier` agent and intended to wait for its report before touching git; the environment's Stop-hook (`stop-hook-git-check.sh`) fired mid-wait demanding uncommitted changes be committed and pushed, forcing a decision before the agent had returned (origin: own observation, this session)
- Rule: once your own manual verify commands are green, commit and push immediately rather than blocking indefinitely on a background verifier agent — the commit is cheap to follow up with a fix commit if the verifier finds something; gate the real "claim done" moment (opening the PR, per CLAUDE.md's prime directive on closed loops) on the verifier's findings instead, not the commit
- Scope: project — assumes an environment stop hook that forces action on uncommitted changes; the underlying principle (don't let an in-flight async check block a cheap, reversible local step) is portable but not yet proven outside this harness
## L-061 · 2026-08-12 (harvested 2026-08-20) · Verify editable installs resolve outside pytest on macOS
- Trigger: walking-skeleton build on the stranded `feat/web-flow-redesign` branch (never merged) — pip's `__editable__.*.pth` got UF_HIDDEN re-applied within seconds on macOS, and Python 3.14's `site` skips hidden `.pth`, so `import aegis_sentinel` silently failed outside pytest while the suite stayed green (pytest `pythonpath` masked it). Harvested into main's ledger per issue #31 (the branch's own PR never landed, so this entry never reached main until now)
- Rule: after `pip install -e .` on macOS, run a bare `python -c "import <pkg>"` outside pytest; if it fails with the package present, check the venv's `.pth` for the hidden flag and symlink the package into site-packages as the workaround
- Scope: portable
- Evidence: 1
- Status: candidate

## L-062 · 2026-08-20 · The heartbeat prompt's fallback skill path (.claude/skills/work-loop/SKILL.md) doesn't exist in this repo
- Trigger: own observation — the scheduled build-heartbeat prompt's step 2b says "fall back to ONE ready `task:` issue per `.claude/skills/work-loop/SKILL.md`" when every EXECUTION-PLAN box is ticked/claimed/blocked; `Glob .claude/skills/**/SKILL.md` lists ten real skills and no `work-loop` among them, so the referenced readiness definition has to be reconstructed from the prompt's own inline gloss ("carries a done-means, is inside this environment's tool grant, and is not blocked by an unanswered `question:` or a `loop:hold` label") rather than read from a file
- Rule: when a routine's stored prompt names a skill/doc path as the source of a rule, verify the path exists before relying on it — if it's missing, apply the routine prompt's own inline restatement of the rule instead of stalling on the Read, and flag the drift (this entry) rather than silently re-deriving it every firing unremarked
- Scope: project
- Evidence: 1
- Status: candidate

## L-063 · 2026-08-20 · This container's default python3 is 3.11; the project needs 3.12 — a venv must be created and activated before verify.sh
- Trigger: own observation — `pip install -e '.[dev]'` against the ambient `python3`/`pip` failed with "Package 'aegis-sentinel' requires a different Python: 3.11.15 not in '>=3.12'" even though `/usr/bin/python3.12` was already present on the image; `scripts/verify.sh` shells out to bare `python3`/`pip`/`pytest`/`ruff` with no venv logic of its own, so `full` silently collected zero real tests (21 `ModuleNotFoundError` collection errors for pydantic/jsonschema, read at first as a broken repo) until a `python3.12 -m venv .venv` was created and activated ahead of the install
- Rule: in this repo's remote container, before running `pip install -e '.[dev]'` or `scripts/verify.sh full`, create (or reuse) a `.venv` via `python3.12 -m venv .venv` and `source .venv/bin/activate` first — never assume ambient `python3` already satisfies the `>=3.12` requirement, and read a wall of `ModuleNotFoundError` collection errors as a missing-install signal before assuming the suite itself is broken
- Scope: project
- Evidence: 1
- Status: candidate
