---
name: verify-loop
description: Close the feedback loop on a change - define a runnable success check, run it, articulate each failure before fixing, iterate to green (max 5 rounds).
when_to_use: Use before claiming any work is done.
argument-hint: [success command or observable criterion]
---

Boris's rule: if the agent can close the feedback loop on its own, it will
iterate until the output is right. This skill is that loop, with two
workspace disciplines added: articulate the criterion before running, and
articulate the failure before fixing. Goal-shaped loops (`/goal`) can drive
this skill natively — the loop decides *when* to retry; this skill encodes
*how* to verify.

## Hold in mind

1. An unverifiable claim of success is a failure.
2. Diagnose before patching: one sentence on *why* it failed, then the fix — reflexive patching compounds errors.
3. Five rounds is the cap: a loop that isn't converging is itself a signal.
4. Evidence is pasted output, not summaries of output.
5. Green output is not proof — articulate what would falsify success before you believe it.

## Steps

1. Verbalize the success criterion as a runnable check. Use the argument if given; default to `scripts/verify.sh full`. For UI or behavioral criteria, define the observation precisely (what command, what expected output).
2. Run the check.
3. On failure: state in one sentence why it failed (hypothesis, not narration), then make the smallest fix that addresses that hypothesis. Return to step 2.
4. On green: before declaring done, state one concrete way this check could pass while the work is still wrong (stale cache, check too narrow, happy path only). If the scenario is plausible, run one probe to close it; if the probe fails, that is a failure — return to step 3.
5. Track rounds. On the 5th consecutive red:
   - Stop editing.
   - Summarize the failure trajectory: each hypothesis, each fix, each result.
   - Append a line to `.claude/memory/.session-signals` (`verify-fail:loop-exhausted`) so the Stop-hook reflect nudge is guaranteed to fire.
   - Ask the user how to proceed.

## Before finishing

Paste the final green output verbatim, plus the counterfactual you stated and
how it was closed. State how many rounds it took and, if more than 2, whether
there is a lesson for `/reflect`.
