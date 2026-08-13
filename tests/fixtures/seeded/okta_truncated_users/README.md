# Seeded failing fixture — truncated Okta user enumeration (COL02)

The tenant users feed (`tests/fixtures/tenants/okta/users/`) minus its
final page: page 1 still carries the simulated Link rel="next" cursor
(`link_next`), but the page it points at never arrives. 16 well-formed
user records make the snapshot look plausible; exhaustion cannot be
asserted per the capability entry's method (`okta.users.api_v1`:
*follow the after cursor until the header is absent*).

**Required detection (no detection proof, no merge — docs/HANDOFF.md §4
COL01–05):** `OktaUsersCollector` must flag the snapshot incomplete with
the dangling-cursor reason; the downstream evaluator turns the
population UNKNOWN — never a partial pass. Proven by
`tests/collectors/test_okta.py::test_seeded_truncated_users_is_flagged_incomplete`.

Provenance: the prior scaffold's completeness discipline
(`assert_exhaustive_pagination`): a feed without its exhaustion signal
may be truncated; the only honest population-level claim is UNKNOWN.
