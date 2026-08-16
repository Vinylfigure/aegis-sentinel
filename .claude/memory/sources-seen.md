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
