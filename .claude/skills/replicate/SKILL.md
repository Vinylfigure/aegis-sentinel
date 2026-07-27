---
name: replicate
description: Stamp a new project from this Janus template - create the child repo, carry portable learnings forward as inheritance, rewrite identity, and hand off to /bootstrap. Confirms name, visibility, and location before creating anything.
when_to_use: Use when the user wants to start a new project from this scaffold.
argument-hint: [new project name]
---

The lineage loop. Children start with the scaffold *plus* everything this
repository has learned that is true anywhere — heredity, not just copying.

## Hold in mind

1. Only `Scope: portable` knowledge crosses repositories — project-specific rules in a child are noise that erodes trust in the whole memory system.
2. Knowledge is inherited; verification state is not. Ledger entries cross; run stamps and source watermarks reset.
3. Inherited entries arrive as `Status: inherited`, not `candidate`: the child re-earns promotion with its own evidence. Rules entering the child's CLAUDE.md are the one exception — they arrive active, so each one is gated on the user's explicit yes at replicate time: the generation boundary is a review gate, because persisted rules files are an injection channel and a poisoned rule would otherwise propagate to every descendant unreviewed.
4. The child must not keep the template's identity: name, facts block, and README head must be rewritten before first commit.
5. The child's first session should run `/bootstrap` — say so explicitly in the handoff.

## Steps

1. Interview the user (skip anything already given in the argument): project name, one-line purpose, expected stack (or unknown), GitHub visibility (public/private) or local-only. Gate: restate name, visibility, and destination path, and wait for an explicit yes before creating anything.
2. Create the child:
   - **GitHub path** (preferred): `gh repo create <name> --template <owner>/<template-repo> --<visibility> --clone`
   - **Local fallback**: `git clone --depth 1 <template> <name> && rm -rf <name>/.git && git -C <name> init -b main`
3. Apply heredity, in the child:
   - From the parent's CLAUDE.md `janus:rules` block, present each rule whose ledger entry is `Scope: portable` and copy it into the child's rules block only on the user's explicit yes (keep the `(L-NNN)` citations). A declined rule is not lost — its ledger entry still crosses as `inherited` below.
   - From the parent's `LEARNINGS.md`, copy every `Scope: portable` entry (any Status except `retired`) into the child's ledger, re-marking each `Status: inherited`.
   - Copy nothing project-scoped. When in doubt, leave it behind — heredity is selective.
   - Reset the child's recalibration clock: `date +%s > .claude/memory/recalibrated-at` in the child.
   - Truncate the child's `.claude/memory/sources-seen.md` to its header and marker. A fresh repo has verified nothing; inheriting the parent's watermark would make it skip sources it has never read.
4. Rewrite identity in the child: CLAUDE.md title + facts block (project name, purpose, `Stack: NOT BOOTSTRAPPED — run /bootstrap`), README title and first paragraph.
5. Commit in the child: `chore: replicate from janus template (N learnings inherited)`.
6. Hand off: tell the user to open a session in the child and run `/bootstrap`, and list what was inherited.

## Before finishing

List each inherited learning id with a one-line justification of why it is
portable. Confirm the child's CLAUDE.md carries the child's name (not
"Janus (template)") and that its rules block is within the cap of 12.
