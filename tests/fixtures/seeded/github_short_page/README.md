# Seeded failing fixture — GitHub short page (COL03)

Members page 1 carries a simulated Link rel="next" header promising page
2 — but page 2 is a 404-shaped REST error body (`status: 404`,
`message: "Not Found"`), not a member page, and the
outside-collaborators endpoint is never reached at all. Ten well-formed
member records make the snapshot look plausible; exhaustion fails on
BOTH clauses of the capability entry's method
(`github.org_members.rest_v3`: *follow the Link rel="next" header until
absent, on both the members and outside_collaborators endpoints*).

**Required detection (no detection proof, no merge — docs/HANDOFF.md §4
COL01–05):** `GithubOrgMembersCollector` must flag the snapshot
incomplete, naming the 404-shaped page AND the missing
outside-collaborators endpoint; the downstream evaluator turns the
population UNKNOWN — never a partial pass. Proven by
`tests/collectors/test_github.py::test_seeded_short_page_is_flagged_incomplete`.

Provenance: the prior scaffold's completeness discipline
(`assert_exhaustive_pagination`); the error-body arm exists because a
plausible HTTP 200 stream that swallows a mid-pagination 404 is exactly
how a truncated roster masquerades as a complete one.
