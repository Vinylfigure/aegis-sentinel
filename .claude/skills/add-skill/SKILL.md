---
name: add-skill
description: Author a new skill for this repository using the canonical Janus SKILL.md shape (Hold in mind, Steps, Before finishing) and workspace-priming rules.
when_to_use: Use when a procedure has been repeated or explained more than once, when the user describes a workflow worth keeping, or when /evolve promotes a procedure-shaped learning.
argument-hint: [skill name and purpose]
---

The meta-skill: it makes the repository's skill-authoring standard executable.
Used by humans adding capabilities and by `/evolve` when a learning is
procedure-shaped.

## Hold in mind

1. Skill bodies load on demand and may be long (the platform's own guidance: keep `SKILL.md` under 500 lines). Priming blocks may not — a handful of invariants, not a syllabus.
2. `description` + `when_to_use` are the only always-loaded parts and the model's trigger surface: action first, then the "Use when …" situations — ≤50 words total. The platform truncates the listing at 1,536 characters, but that is where rendering stops, not a target: every description taxes every future session.
3. Write for a model with judgment. Encode what this repo does differently — its gotchas, conventions, and irreversible steps — and leave general competence alone; an instruction that describes how to think is the first thing to cut.
4. Don't shadow built-ins (`init`, `review`, `verify`, `run`, `code-review`, `security-review`) or existing janus skills — the platform owns those mechanisms.
5. A skill is a permanent tax on every future session. Retire before adding; `/context`'s Skills row reports what the listing actually costs.

## Steps

1. Confirm the skill deserves to exist: it's a *procedure* (multi-step, repeatable), not a *fact* (belongs in CLAUDE.md), not a *path-local rule* (belongs in `.claude/rules/<topic>.md` with `paths:` frontmatter), and not a one-off. Check the public agent-skills library (github.com/anthropics/skills) before authoring from scratch — adapt rather than reinvent; its `spec/agent-skills-spec.md` and the Claude Code skills docs are the authority on frontmatter fields, and `scripts/test-hooks.sh` enforces the field set this repo knows about.
2. Choose the name (kebab-case directory under `.claude/skills/<name>/SKILL.md`) after checking existing skills and built-ins.
3. Write frontmatter:
   - `description`: what it does, in one action-first line. Put the "Use when …" triggers in `when_to_use` — the platform has a field for them, so stop crowding one string. ≤50 words across both; this is the only part always in context.
   - Side-effect skills get an **in-body gate**: one step that confirms with the user immediately before the irreversible action (push, repo creation, CLAUDE.md edit), degrading to PR delivery when headless. Reach for `disable-model-invocation` only to stop Claude triggering the skill at all — it controls *who invokes*, which is not the same as *confirm before acting*.
   - `argument-hint` if it takes arguments; `allowed-tools` only for read-only skills, since it clears at the next user message and a writer skill silently loses the tools its later steps need.
4. Write the body in the canonical shape:

   ```markdown
   ## Hold in mind
   The few invariants worth restating before step 1 — the ones that are
   costly to violate and not obvious from the task. Not background info.

   ## Steps
   Numbered, imperative. Irreversible or repo-specific steps get explicit
   checks; anything the model would do correctly anyway stays terse or goes.

   ## Before finishing
   Forced articulation: what was verified, what evidence was seen. The agent
   must state this, not just think it.
   ```

5. Dry-run it: read the finished SKILL.md and simulate the first two steps mentally. If a step is ambiguous to you now, it will be ambiguous to a fresh session — tighten it.

## Before finishing

State: the new skill's name, its description and `when_to_use` (≤50 words
together), where its gate sits if it has side effects, what you retired or why
nothing needed retiring, and confirm the body follows the canonical shape.
