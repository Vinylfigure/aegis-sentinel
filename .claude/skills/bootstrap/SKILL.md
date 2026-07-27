---
name: bootstrap
description: Specialize this Janus scaffold to a real tech stack - detect or ask for the stack, wire scripts/verify.sh to real lint/test commands, update the project facts in CLAUDE.md, and prove the verification loop closes.
when_to_use: Use when the project facts say NOT BOOTSTRAPPED or when adopting Janus into an existing codebase.
argument-hint: [optional stack hint, e.g. "python uv" or "node pnpm"]
---

Turns the stack-agnostic template into a project that verifies itself. The
hooks and skills only start earning their keep once `verify.sh` runs real
commands — this skill wires that up and proves it.

## Hold in mind

1. Hooks only help if wired to real commands — placeholder checks are worse than none because they teach false confidence.
2. `verify.sh quick` runs after every single edit: it must finish in well under 10 seconds or it will be resented and disabled.
3. `verify.sh full` is the definition of "healthy": if it passes while the project is broken, every loop built on it is lying.
4. CLAUDE.md's concept budget applies to the facts you write: stack, commands, run instructions — one line each.

## Steps

1. Detect the stack: look for manifests (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `Gemfile`, `mix.exs`, `pom.xml`, `build.gradle`, `*.csproj`). Use the argument as a hint. If nothing is found (fresh project), interview the user: language, package manager, test framework, formatter/linter. Scaffold the minimal stack files they choose.
2. Wire `scripts/verify.sh`:
   - Replace the block between `# janus:bootstrap:quick:start` and `:end` with per-file checks keyed on file extension (format check, lint, typecheck of the changed file). Budget: <10s. Keep the template's `*.sh`/`*.json` arms — hook scripts exist in every child and deserve the same loop.
   - Replace the block between `# janus:bootstrap:full:start` and `:end` with the real suite: lint all, typecheck all, tests, build if applicable.
3. Rewrite the block between `<!-- janus:facts:start -->` and `<!-- janus:facts:end -->` in CLAUDE.md: stack + package manager; how to run verify (quick/full); how to run the app.
4. Prove the loop closes, both ways:
   - Run `scripts/verify.sh full` — must exit 0 on the healthy project.
   - Make a deliberately bad edit to a real source file (e.g. introduce a syntax error), confirm `scripts/verify.sh quick <file>` exits nonzero with useful output, then revert the edit.
5. If this project was replicated from a parent, review inherited entries in `.claude/memory/LEARNINGS.md` (`Status: inherited`): any that are stack-relevant here get re-marked `candidate` so `/evolve` can promote them.

## Before finishing

Paste: the passing `verify.sh full` output, and the failing-then-reverted
quick-check output proving the PostToolUse hook will bite. State the new
facts block verbatim and confirm CLAUDE.md is still within its concept budget.
