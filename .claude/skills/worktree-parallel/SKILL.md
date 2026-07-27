---
name: worktree-parallel
description: Fan a task out into parallel Claude Code sessions, each in its own git worktree, then merge tracks after each verifies green. Confirms the track plan before creating worktrees.
when_to_use: Use when work splits into genuinely independent tracks (refactor + feature + bugfix) or the user asks to parallelize.
argument-hint: [task to parallelize]
---

Parallel sessions multiply throughput only when the tracks are genuinely
independent and each track closes its own verification loop before merging.
Worktrees share the repo's `.claude/` (it's in-tree), so every parallel
session gets the same skills, hooks, and memory for free.

## Hold in mind

1. Tracks must be independent: no two tracks editing the same files, or the merge eats the savings.
2. One task per session: a session's context is one workspace — never multiplex tracks in one conversation; 3–5 concurrent sessions is the practical sweet spot.
3. Each track verifies green in its own worktree before any merge.
4. Worktrees are disposable; branches carry the work. Clean up after merging.

## Steps

1. Split the task into independent tracks. For each, write one paragraph: scope, files it will touch, its "done means" check. If two tracks overlap on files, merge them into one track. Gate: show the user the track table and wait for a yes before creating any worktree.
2. Launch each track in its own worktree: `claude --worktree <slug>` — Claude Code creates and manages the worktree itself (add `--tmux` to give each its own tmux session/pane). For delegated parallel edits inside one session, a subagent with worktree isolation is the equivalent.
3. Give each session its kickoff prompt: the track's scope paragraph, its "done means" check, and the instruction to run `/verify-loop` before declaring done.
4. Monitor the fleet: number your terminal tabs per track and enable system notifications so you know when a session needs input; `claude agents` from the root directory shows all concurrent sessions grouped by status.
5. Merge protocol, once tracks report green:
   - In the main checkout, merge each track's branch one at a time, running `scripts/verify.sh full` after each merge.
   - On conflict or post-merge red: fix in the main checkout before merging the next track.
   - Ledger reconciliation: if more than one track appended `LEARNINGS.md` entries, colliding L-NNN ids are guaranteed — renumber the later entries sequentially above the merged maximum, bump Evidence on true duplicates instead of keeping twins, and land the result as one consolidated commit.
6. Cleanup: remove each merged track's worktree (`git worktree remove` + branch delete).

## Before finishing

List each track, its branch, and its verification evidence. Confirm
`verify.sh full` is green on the merged result and all worktrees are cleaned.
