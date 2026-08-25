---
name: work-loop
description: Pick and dispatch the next ready GitHub task issue when no EXECUTION-PLAN.md box is available.
when_to_use: Use from the build-heartbeat routine's step 2b, when every plan box is ticked, claimed, or blocked.
---

The build heartbeat's fallback arm: this file is the readiness definition it
falls back to, not a summary of one. It exists because five-plus days of
firings kept reconstructing the same definition from an inline gloss instead
of reading it from a named file (issue #73).

## Hold in mind

1. Ready means all three: the issue carries a concrete done-means, the work
   fits inside this session's actual tool grant (no op the permission
   classifier will refuse, no missing MCP tool), and it is not blocked by an
   unanswered `question:` issue or a `loop:hold` label.
2. One task per firing — pick the single oldest ready `task:` issue, never
   several.
3. A task blocked only by tool grant (e.g. it needs a destructive git op with
   no available MCP equivalent) stays open with a status comment; don't
   re-attempt it every firing without new evidence that the blocker changed.
4. An issue explicitly marked Owner-only, or gated behind a different
   dispatch mechanism ("captured work, not a work order"), is never ready
   regardless of its label.

## Steps

1. List open issues; keep only `task:`-labeled ones (or otherwise clearly
   actionable — vague research asks with no stated done-means don't count).
2. For each candidate, check in order: does it state a done-means? Is it free
   of an open `question:` dependency or `loop:hold` label? Can this session's
   tool grant actually execute it (repo edits and non-destructive git/GitHub
   MCP calls only — no branch deletion, no Owner GitHub-settings actions)?
3. Drop anything explicitly Owner-only or routed through a separate dispatch
   step.
4. Pick the oldest surviving candidate. If none survive, this arm is
   exhausted — fall through to the heartbeat's step 2c (file at most two
   grounded proposal issues, then stop).
5. If the chosen issue already carries a comment from a prior firing that
   found it tool-grant-blocked, re-verify the blocking condition before
   redoing the work it already did. If the blocker is unchanged, leave a
   short comment noting the re-check and treat this arm as exhausted rather
   than repeating the same failed attempt.

## Before finishing

State which issue was picked (or that none were ready, and why each
candidate was rejected), and name the done-means the resulting PR will be
judged against.
