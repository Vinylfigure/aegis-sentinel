# Seeded failing fixture — truncated Slack cursor (COL05)

The tenant users feed (`tests/fixtures/tenants/slack/`) minus its final
page: page 1 still carries a non-empty
`response_metadata.next_cursor`, but the page it addresses never
arrives. 16 well-formed member records make the snapshot look plausible;
exhaustion fails per the capability entry's method
(`slack.users.web_api`: *follow response_metadata.next_cursor until it
is empty*).

**Required detection (no detection proof, no merge — docs/HANDOFF.md §4
COL01–05):** `SlackUsersCollector` must flag the snapshot incomplete
with the dangling-cursor reason; the downstream evaluator turns the
population UNKNOWN — never a partial pass. Proven by
`tests/collectors/test_slack.py::test_seeded_truncated_cursor_is_flagged`.

Provenance: the prior scaffold's completeness discipline
(`assert_exhaustive_pagination`): a feed without its exhaustion signal
may be truncated; the only honest population-level claim is UNKNOWN.
