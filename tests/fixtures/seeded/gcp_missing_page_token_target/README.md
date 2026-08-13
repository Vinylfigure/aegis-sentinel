# Seeded failing fixture — GCP missing pageToken target (COL04)

The tenant IAM feed (`tests/fixtures/tenants/gcp/`) minus its final
page: page 1 still carries `nextPageToken`, but the page it addresses
never arrives. Two well-formed `searchAllIamPolicies` results (including
the break-glass roles/owner binding) make the snapshot look plausible;
exhaustion fails per the capability entry's method
(`gcp.iam.cloud_asset_v1`: *pass pageToken from the previous response's
nextPageToken until the response omits it*).

**Required detection (no detection proof, no merge — docs/HANDOFF.md §4
COL01–05):** `GcpIamBindingsCollector` must flag the snapshot incomplete
with the dangling-token reason; the downstream evaluator turns the
population UNKNOWN — never a partial pass. Proven by
`tests/collectors/test_gcp.py::test_seeded_missing_page_token_target_is_flagged`.

Provenance: the prior scaffold's completeness discipline
(`assert_exhaustive_pagination`): a feed without its exhaustion signal
may be truncated; the only honest population-level claim is UNKNOWN.
