# Knowledge bundle — landed 2026-08-08

The extracted contents of `aegis-knowledge-bundle.zip` (assembled 2026-08-05,
attached to issue #10), landed by the operator so dispatched runs can read it —
a sandboxed Actions run cannot be assumed able to fetch GitHub attachment URLs.

Read `INDEX.md` first. Layout follows the bundle: `01_corpus/` (the ratified
23-doc authoring record, hash-manifested — verify with
`cd 01_corpus && shasum -a 256 -c MANIFEST.sha256`), `02_repo_knowledge/`
(the knowledge files from the prior scaffold), `04_reference/` (Janus and
aegis-gcp prior art).

Deliberate deviations from the raw bundle:

- `03_archives/` (three nested zips) is **not** committed. Two are byte-level
  duplicates of the extracted text here (`aegis-corpus.zip`,
  `knowledge-pack.zip`). The third, `aegis-sentinel.zip`, is a full snapshot
  of the **prior scaffolded repo** — which also exists live and unpushed at
  `~/Documents/👾CODE/aegis-sentinel` on the operator's machine (no git
  remote; its history ends at "Consolidate: corpus in-repo"). Whether this
  repo adopts that scaffold or rebuilds against it is the first question the
  evaluation (`docs/EVALUATION.md`) must answer — a decision, not an archive
  to bury in git.
- The three `CLAUDE.md` files inside the bundle are renamed
  `CLAUDE.repo-copy.md` so Claude Code sessions working in this repo never
  load them as live instructions. Their content is untouched.
