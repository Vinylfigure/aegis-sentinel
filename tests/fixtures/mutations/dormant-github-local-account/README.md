# Poison: dormant GitHub local account

**Provenance:** `docs/PRD-v3.md` §6 — "one dormant GitHub local account" — one of
the six mutation-playbook poison cases seeded into the V1 termination lane.
Headline metric: assurance defect detection rate (`docs/PRD-v3.md` §7).

**Scenario.** A GitHub account provisioned outside the IdP (a local/outside
collaborator account, e.g. handle `arivera-contractor` for the terminated identity
`alex.rivera`) survives the termination fan-out because Okta deprovisioning never
touched it. It remains a member of the org after the owner's termination date.

**Expected outcome** (`expected_outcome.json`): `VERDICT` with state `FAIL` — a
NON-EXISTENCE assertion over post-termination access finds the account still
present. This is a detected control failure, not an unknown.

**Placeholder population magnitudes** (pending realistic sizes from the reference
engagement — `[NEED: Owner]`, see `docs/HANDOFF.md` §6): ~200 employees in the HRIS
population, ~15 terminations in the audit period.

`TODO(playbook)`: the mutation playbook document itself is not in this repo —
`[NEED: Owner]`. This fixture is authored from the PRD §6 summary; reconcile against
the playbook when it lands.
