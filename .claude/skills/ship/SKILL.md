---
name: ship
description: Close the delivery loop - verify green, commit, push, open a PR, then babysit CI and review feedback until merged or closed. Confirms branch and remote before the first push.
when_to_use: Use when a verified change is ready to leave the machine or the user asks to ship, land, or PR.
argument-hint: [optional PR title]
---

Shipping is a loop, not an event: the work isn't delivered when the PR opens,
it's delivered when the PR merges with green checks.

## Hold in mind

1. Nothing ships red: verification passes locally *before* the commit, not hopefully-in-CI.
2. "Shipped" means a PR URL plus green CI evidence — anything less is "pushed".
3. CI failures and review comments are the loop continuing, not the loop failing: diagnose, fix, push, repeat.
4. Never push to a branch you weren't asked to ship from; never force-push shared history.

## Steps

1. Verify: run `/verify-loop` (or the `verifier` agent for non-trivial changes) and get green evidence. Red stops the ship.
2. Commit: clear, descriptive message — what and why, present tense. Group unrelated changes into separate commits rather than one blob.
3. Push — gated: confirm the branch and remote with the user before the first push of this run (headless runs skip the question but must push a feature branch and deliver via PR, never the default branch). Then `git push -u origin <branch>`. On network failure retry up to 4 times with backoff (2s/4s/8s/16s).
4. Open the PR against the default branch using whatever this environment provides (`gh pr create`, or the GitHub MCP tools in remote sessions). Honor the repo's PR template if one exists. Body: what changed, why, how it was verified.
5. Babysit until terminal state:
   - **Remote/web sessions**: subscribe to PR activity if the environment exposes a subscription tool, so CI results and review comments arrive as events; also schedule a periodic self check-in if the environment supports it, since CI-success events aren't always delivered.
   - **CLI sessions**: `gh pr checks <url> --watch`, and re-check reviews when they land. A later session resumes the babysit with `claude --from-pr <number>` — PR-linked sessions survive the terminal closing.
   - On CI failure: read the failing job's log, state the diagnosis in one sentence, fix, push. Each failure is also a `/reflect` signal if it reveals a gap in `verify.sh`.
   - On review comments: apply clear fixes directly; for ambiguous or architectural asks, check with the user before acting.
6. Terminal: merged or closed. If several fix rounds go nowhere or a failure is out of scope, stop and report where it's stuck instead of going quiet.

## Before finishing

State: the PR URL, the CI status with evidence (check names + conclusions),
and any review threads still open. If not merged yet, state what you are
watching and how you will be woken when it changes.
