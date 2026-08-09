# Aegis Sentinel — Knowledge Bundle

Everything collected for the deterministic agentic compliance build, in one archive. Assembled 2026-08-05.

## 01_corpus/ — the ratified authoring record (23 docs)

Exported verbatim from the claude.ai "Compliance agents" project on 2026-07-25, hash-manifested. Verify integrity any time with:

```
cd 01_corpus && shasum -a 256 -c MANIFEST.sha256
```

- `01_architecture/` — the investigator architecture (two-verb split, five layers, plan→freeze→execute), design decisions, workflow theory, glossary
- `02_design_decisions/` — decision ledger, constraints, contradictions, design fixes D7 (UNKNOWN decomposition) / D8 (model reconciliation) / D9 (decentralization discipline), red-team reconciliation, API constraints by trust consequence, verified control-evidence API chains, version drift ledger
- `03_testing_libraries/` — SOC 2 control testing matrix, SOC 2 TSC / FedRAMP / SOX agent testing libraries
- `04_build_prds/` — Sentinel Build Execution PRD v2, Sentinel v0.2 event-driven/agentic/OSCAL spec, JIT+UI+DB+Janus companion
- `05_prior_art/` — GRCEngClub toolkit review (quarantined external source; adopt the contracts, reject the trust model)

## 02_repo_knowledge/ — what Claude Code loads

Loose copies of the knowledge files that live inside the `aegis-sentinel` repo, for reading outside a checkout:

- `CLAUDE.md` — entry point: read order, the eight invariants, commands, next tasks
- `docs/PLAN.md` — comprehensive build plan (decisions, scaffold inventory, day-by-day to 7/30, EngClub adoption status, Janus protocol, four levels of validation)
- `docs/corpus-index.md` — reading map for all 23 corpus docs with "read when" triggers
- `claude-memory/LEARNINGS.md` — 49-entry learnings genome (append-only, evidence-gated; CANDIDATE → PROMOTED only via a named passing test)
- `claude-skills/` — the three project skills: port-collector, verdict-path-review, ratify

## 03_archives/ — the zips

- `aegis-sentinel.zip` — the full scaffolded repo including git history (schemas, verdict path, 50-test validation harness, CODEOWNERS, CI, Janus vendored at `.janus/`)
- `aegis-corpus.zip` — the 23-doc corpus as its own archive
- `knowledge-pack.zip` — just the knowledge layer (CLAUDE.md, corpus index, genome, skills)

## 04_reference/ — prior art, not canon

- `janus/` — the Janus scaffold's own docs (architecture, self-improvement, usage, methodology review). Build plane only; never a runtime component.
- `aegis-gcp/` — the existing `vinylfigure/aegis` GCP-scoped evidence platform docs (PRD, control coverage matrix, demo runbook, build log). Architectural prior art for the WORM/verdict pattern; its GCP specifics were deliberately not imported into Sentinel.

## Restoring on a Mac

```
unzip aegis-knowledge-bundle.zip
cd aegis-knowledge-bundle/03_archives
unzip aegis-sentinel.zip -d ~/PycharmProjects/
unzip aegis-corpus.zip -d ~/PycharmProjects/
cd ~/PycharmProjects/aegis-sentinel && claude
```
