# Fixture tenants — the demo engagement

Fictional tenant data for the walking-skeleton pipeline and the collector
tests (COL01+). No live-tenant calls anywhere in tests (docs/HANDOFF.md §4);
`FixtureTransport` reads these page files as `<system>/page-<n>.json`.

- `engagement.json` — the fixture engagement's constants: tenant name,
  manifest version, the **stub** ratified-manifest snapshot hash (D-S1 —
  a fixed constant until SCH03 lands real manifest snapshots; it is the
  SHA-256 of the canonical JSON
  `{"manifest_version":"v1-skeleton","stub":"ratified-manifest-snapshot"}`),
  the audit period, and the FIXED `retrieved_at` / `evaluated_at`
  timestamps (D-P3: never wall clock — explicit inputs so artifact
  emission is deterministic).
- `hris/` — the daily terminations export
  (`hris.terminations_feed.export_v1`), 15 terminations across 3 pages,
  final page carries the trailer record declaring `total_rows`. Includes
  one contractor-shaped worker (`CT-2044`, `worker_type: "contractor"`)
  that the contractor-absent-hris poison (VAL02) builds on later.

All people and the company (Meridian Financial) are fictional
(D-R1 redaction gate: `scripts/check-redaction.sh`).

Population sizes are placeholders pending the Owner's
reference-engagement numbers (docs/EXECUTION-PLAN.md, Owner's open
items #2): ~15 terminations. `TODO(playbook)`: poison seeds derive from
PRD §6 until the mutation playbook document lands.
