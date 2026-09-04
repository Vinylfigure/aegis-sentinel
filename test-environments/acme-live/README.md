# Acme Corp — live validation environment

Scaffold for the smallest realistic external test environment that will
eventually prove aegis-sentinel against live SaaS APIs instead of only
synthetic fixtures (issue #122). This directory currently holds **only the
data and setup documentation** carved out as issue #123 — Deliverables 1, 2,
and 7 of #122, plus this checklist (Deliverable 11).

**Deliberately not here yet:** external source adapters (#122 Deliverable
4), capability-registry entries for the four new surfaces (Deliverable 5),
manifest/scope enforcement changes (Deliverable 6), the
`aegis validate-environment` CLI command (Deliverable 8), the validation
report (Deliverable 9), and tests (Deliverable 13). Those are follow-on
issues once this scaffold exists — see #122 for the full spec. Nothing in
this directory makes a live API call, reads a secret, or touches
`src/aegis_sentinel/`.

## Files

- `ground-truth.yaml` — the scored answer key. Sentinel must never read this
  during evaluation; only a future scoring step compares its independently
  produced verdicts against it.
- `identities.yaml` — the 14-identity roster the scenarios below reference,
  one identity per distinct assurance mechanism under test.
- `scenarios.yaml` — 20 validation scenarios (13 termination-lane, 7
  change-approval-lane) with their expected verdict state.
- `config.example.yaml` — the environment-variable and tenant-identifier
  shape a future adapter layer will expect. No secrets.

## External test tenants to provision

Four lightweight SaaS test accounts, per #122. None of this repo's code
reads them yet — this is what a human operator sets up ahead of that work,
so the adapters (when written) have somewhere real to point.

### Merge (authoritative workforce source)

1. Create a Merge.dev developer account (https://merge.dev) and enable the
   HRIS category in test/sandbox mode.
2. Link a test HRIS account via Merge's linked-account flow to obtain an
   account token; generate an API key from the Merge dashboard.
3. Seed employee records matching `identities.yaml`'s `employee` and
   `contractor` entries — note that `dave` (contractor) and `leo` (board
   advisor) are deliberately **absent** from this source; do not create
   HRIS rows for them.
4. Verify the `/employees` endpoint returns the seeded roster before wiring
   any adapter against it.

### Okta (identity/account state)

1. Create an Okta Integrator Free Plan org
   (https://developer.okta.com/signup).
2. Create the test identities from `identities.yaml` with the `okta_status`
   each row names (`active` / `deactivated` / absent, per `svc_prod` and
   `breakglass_admin`'s machine-credential nature).
3. Reproduce the specific event-history scenarios `ground-truth.yaml`
   describes: `carol`'s late deactivation, `quinn`'s malformed
   `alternate_id` on her deactivation event, and `ivy`'s deactivation dated
   before the tenant's reachable system-log retention window.
4. Record the org's actual system-log retention depth once observed (do not
   assume it matches Okta's documented default) — the capability-registry
   entry that Deliverable 5 will add needs the observed number, the same
   discipline REC10's Surveyor already enforces for the synthetic tenant.

### GitHub (downstream repo/team access)

1. Create a GitHub test organization, separate from this repo's own org.
2. Create the logins from `identities.yaml`, including `grace`'s two logins
   (`grace-oyelaran`, SSO-linked, and `g-oyelaran-legacy`, a local
   pre-SSO account) and `henry-vance` (added directly to the org, with no
   corresponding Merge or Okta identity — the orphan case).
3. Grant `erin-vasquez-halloran` the org-owner role and deliberately leave
   it unrevoked, per `TERM-003`.
4. Establish the intentionally-bad states `scenarios.yaml` names: the
   never-removed org-owner role, the unremoved legacy local login, and the
   orphan member — these must persist, not be cleaned up.

### Atlassian (Jira change tickets and approvals)

1. Create an Atlassian Cloud developer site
   (https://developer.atlassian.com/platform/marketplace/getting-started/#free-developer-instances)
   and a Jira project with key `ACME` (matching `config.example.yaml`).
2. Create a "Change" issue type (or reuse Task/Story if the site's plan
   doesn't support custom issue types) with a status or custom field that
   can represent an approval transition, plus a field to record the
   correlated deployment reference.
3. Seed the seven `ACME-4xx` issues `scenarios.yaml`'s `lane_b_change_approval`
   section names (`CHG-001` through `CHG-007`), each reproducing the
   ordering/field-state its `description` and `known_defect` describe —
   including `CHG-004`'s deliberately-missing ticket (there is nothing to
   seed for it; the GitHub deployment event exists with no Jira
   counterpart) and `CHG-006`'s deliberate deployment-reference mismatch.
4. Document the exact field/workflow convention used (issue type name,
   which field or status value means "approved", which field holds the
   deployment reference) here once chosen, so Deliverable 4's Jira adapter
   and Deliverable 5's capability-registry entry can cite it exactly rather
   than guessing at a generic Jira configuration.

## Keeping this simple

Per #122 Deliverable 12: seed the four tenants by hand. Automating
provisioning is only worth doing later if it turns out to save real
repeated setup time — it is not a goal of this scaffold, and no such
automation exists here.
