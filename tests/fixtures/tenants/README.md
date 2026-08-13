# Fixture tenants — the demo engagement

Fictional tenant data for the walking-skeleton pipeline and the collector
tests (COL01–05). No live-tenant calls anywhere in tests
(docs/HANDOFF.md §4); `FixtureTransport` reads these page files as
`<system>/page-<n>.json` — or, for systems with two collected surfaces,
`<system>/<surface-subdir>/page-<n>.json` via the transport's `surfaces`
mapping (see `tests/collectors/conftest.py`).

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
  final page carries the trailer record declaring `total_rows`.
- `okta/users/` — the Okta user inventory (`okta.users.api_v1`), 31
  users across 2 cursor-paginated pages (simulated Link rel="next" as
  `link_next`): 15 active employees, 14 DEPROVISIONED terminated
  workers (deactivation timestamp in `statusChanged`), plus CT-2044 and
  the vendor-contractor poison, both ACTIVE.
- `okta/system-log/` — deprovisioning events
  (`okta.system_log.api_v1`), 14 `user.lifecycle.deactivate` events
  across 3 pages; the zero-event page 3 is the exhaustion signal. The
  fixture simulates the full audit period in one feed; the live
  surface's 90-day retention is recorded as the entry's history caveat
  and drives the real E204 elsewhere.
- `github/org-members/` — org members + outside collaborators
  (`github.org_members.rest_v3`), 18 members over 2 pages + 1 outside
  collaborator on its own page; `endpoint` discriminates the two
  endpoints the entry's exhaustion method names. `saml_name_id`
  (`null` = local, non-SSO account) and `last_active` are fixture-side
  enrichment standing in for the SAML external-identity mapping the
  entry's history caveat describes.
- `github/audit-log/` — membership-removal events
  (`github.audit_log.rest_v3`), 14 `org.remove_member` events across 2
  pages (`@timestamp`/`created_at` epoch-ms; fixture is ascending by
  time), actor `mf-okta-scim` (the SSO fan-out).
- `gcp/` — Cloud Asset Inventory `searchAllIamPolicies` results
  (`gcp.iam.cloud_asset_v1`), 3 resources / 5 role bindings across 2
  `nextPageToken` pages.
- `slack/` — `users.list` pages (`slack.users.web_api`), 31 members
  across 2 cursor pages (`response_metadata.next_cursor`; empty =
  exhausted): 14 `deleted` terminated workers, 16 active humans, 1 bot
  (no profile email — `users:read.email` gates the field).

The 15 HRIS-terminated people appear by the same `employee_id`/email
across systems (Okta/Slack by email, GitHub by SSO `saml_name_id`,
GCP principals by email) — except where a poison deliberately breaks
the join. ~36 distinct identities total.

## Poison placements (PRD-v3 §6 — "one lane, made deliberately nasty")

Each poison is seeded coherently across the tenant surfaces so
REC01/EVAL01/VAL02 can detect it downstream. Expected outcomes are the
`tests/fixtures/mutations/*/expected_outcome.json` records.

| Poison (PRD §6) | Identity | Placement | Expected (mutations fixture) |
| --- | --- | --- | --- |
| Contractor absent from HRIS | `ctr.blake.morgan@example-vendor.com` | ACTIVE in `okta/users` (`00uctr9207blake`) and SSO-active GitHub member `blake-morgan-vendor`; **no HRIS feed row anywhere** — the poison is the negative space. (CT-2044 is the distractor: contractor-shaped but properly listed in the feed.) | `contractor-absent-hris`: UNKNOWN / UNKNOWN_POPULATION |
| Dormant GitHub local account | `bm-legacy-bot` (id 88011) | `github/org-members` member with `saml_name_id: null` (LOCAL, non-SSO), `last_active: 2025-11-02`; matches no identity in HRIS/Okta/Slack/GCP | `dormant-github-local-account`: FAIL (NON-EXISTENCE) |
| Break-glass cloud account | `breakglass-admin@example-prod.iam.gserviceaccount.com` | `gcp/` roles/owner binding on `projects/mf-prod-core`; absent from HRIS, Okta, GitHub, Slack. Runtime shadow of the compile-time E117 shape (`breakglass-cloud-account` mutation) | `breakglass-cloud-account`: E117 compile error |
| Failed identity join | E-1033 | HRIS says `dana.whitfield@…`; Okta/system-log/GitHub only know the maiden-name identity `dana.kowalski@…` / `dana-kowalski` — not derivable from the HRIS email; Slack carries `dana.whitfield@…` (deleted) | `failed-identity-join`: UNKNOWN / UNKNOWN_POPULATION |
| Delayed revocation | E-1027 `marcus.webb@…` | terminated Fri 2026-02-13; `okta/system-log` deactivate event and `github/audit-log` removal both 2026-02-26 = **9 business days** later (> 5-business-day window) | `delayed-revocation`: FAIL (TIMING) |
| Legitimate exception | CT-2044 `kai.moreno@…` | terminated 2026-06-19 (in the HRIS feed) yet retains access — Slack `deleted: false`, Okta ACTIVE, GitHub member `kai-moreno`, no deactivate/remove events — under ratified disposition **DISP-2026-114** (contractor-to-advisor conversion; the ratified record lives in `engagement.json` `delta_dispositions`, applied by the REC01 reconciler → excluded bucket) | `legitimate-exception`: EXCEPTION |

Benign non-poison extras: outside collaborator `osprey-design-ext`
(active vendor collaborator, deliberately outside the poison set),
Slack bot `mf-deploybot`, and service account
`ci-deployer@mf-staging.iam.gserviceaccount.com`.

All people and the companies (Meridian Financial; example-vendor.com;
example-prod) are fictional (D-R1 redaction gate:
`scripts/check-redaction.sh`).

Population sizes are placeholders pending the Owner's
reference-engagement numbers (docs/EXECUTION-PLAN.md, Owner's open
items #2): ~15 terminations, ~36 identities. `TODO(playbook)`: poison
seeds derive from PRD §6 until the mutation playbook document lands.
