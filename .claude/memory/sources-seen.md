# Sources seen

`/recalibrate`'s watermark: what has been read, when, and what it concluded.
Git-tracked for the same reason as `recalibrated-at` — a headless heartbeat
running in a cloud clone must be able to advance it everywhere via its PR.

Two kinds of row, and the distinction is load-bearing:

- **living** — docs pages, changelogs, blog indexes. Re-read *every* run. A
  stable URL says nothing about stable content, and marking one "seen" would
  make all future drift invisible.
- **one-shot** — a dated article. Read once; skip on later runs.

Format: `| date | kind | URL | conclusion |`. Conclusion is `confirmed`,
`drifted:L-NNN`, `new:L-NNN`, or `no-op`. `/replicate` truncates this table for
a child — a fresh repo has verified nothing, and inheriting a parent's
watermark would make it skip sources it has never read.

<!-- rows below this line -->

| date | kind | URL | conclusion |
|---|---|---|---|
| 2026-08-16 | living | https://code.claude.com/docs/en/memory | confirmed — 200-line target + auto-memory locality verbatim; new:L-043 (HTML comments stripped pre-injection) |
| 2026-08-16 | living | https://code.claude.com/docs/en/skills | confirmed — 1,536-char cap + allowed-tools clears at next message verbatim; new:L-045 (disable-model-invocation, disallowed-tools) |
| 2026-08-16 | living | https://code.claude.com/docs/en/hooks | drifted:L-042 — event surface now ~31 events (InstructionsLoaded, WorktreeCreate/Remove, PostCompact…); Stop JSON schema not surfaced this fetch (no data, fixtures still pass) |
| 2026-08-16 | living | https://code.claude.com/docs/en/worktrees.md | confirmed — --worktree/-w, EnterWorktree, subagent isolation: worktree; --tmux not found on this page (no data, not drift per L-004) |
| 2026-08-16 | living | https://code.claude.com/docs/en/commands.md | confirmed — /doctor /goal /security-review /context /memory /init all current |
| 2026-08-16 | living | https://code.claude.com/docs/en/changelog.md | scanned to 2.1.233 (2026-08-14) — subagent forking default, claude.ai-skill hardening, cross-session SendMessage noted |
| 2026-08-16 | living | https://claude.com/blog | index scan — 13 posts since 2026-07-24; scaffold-relevant ones read below |
| 2026-08-16 | living | https://www.anthropic.com/engineering | no-op — nothing published after 2026-07-24 |
| 2026-08-16 | living | https://agentskills.io/specification | drifted:L-041 — spec authority moved off github.com/anthropics/skills; standard fields {name,description,license,compatibility,metadata,allowed-tools} vs Claude Code extensions |
| 2026-08-16 | living | https://transformer-circuits.pub/2026/workspace/index.html | confirmed — "no more than 25" hyperparameter + "an imperfect tool" framing unchanged; still no claims about prompts or harnesses |
| 2026-08-16 | one-shot | https://claude.com/blog/maximizing-the-value-of-your-claude-code-sessions | confirmed — "Keep CLAUDE.md to specific instructions and move workflow-specific ones into skills" backs the CLAUDE.md/skills split |
| 2026-08-16 | one-shot | https://claude.com/blog/auto-mode-default-in-claude-code | new:L-044 — auto mode default 2026-08-14 (Pro/Max/Team); broad allow rules set aside in auto mode |
