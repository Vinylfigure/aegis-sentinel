# Seeded failing fixture — truncated HRIS terminations feed (COL01)

The tenant feed (`tests/fixtures/tenants/hris/`) minus its final page:
the trailer record that declares `total_rows` never arrives, so the
export looks plausible (12 well-formed termination rows) but its
exhaustion cannot be asserted.

**Required detection (no detection proof, no merge — docs/HANDOFF.md §4
COL01–05):** `HrisTerminationsCollector` must flag the snapshot
incomplete with the trailer-missing reason, and the downstream
evaluator must emit a population-level
`UNKNOWN(UNKNOWN_POPULATION)` — never a partial pass. Proven by
`tests/collectors/test_hris_collector.py` and
`tests/evaluate/test_minimal.py`.

Provenance: the prior scaffold's completeness discipline
(`aegis-sentinel/src/completeness.py`, `assert_exhaustive_pagination`):
a feed without its exhaustion signal may be truncated; the only honest
population-level claim is UNKNOWN.
