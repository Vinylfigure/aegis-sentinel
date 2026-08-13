# Poison: break-glass cloud account

**Provenance:** `docs/PRD-v3.md` §6 — "one break-glass cloud account" — one of the
six mutation-playbook poison cases seeded into the V1 termination lane.
Headline metric: assurance defect detection rate (`docs/PRD-v3.md` §7).

**Scenario.** A GCP break-glass account (e.g. `breakglass-admin@example.com`) exists
outside every identity-provider-derived population. The termination-lane claim's
derivation rule names a source for which no ratified capability entry exists, so the
claim cannot even compile: there is no capability through which the population
containing this account could be enumerated.

**Expected outcome** (`expected_outcome.json`): `COMPILE_ERROR` with E-code `E117`
(missing capability for a derivation-rule source — see TYP01 in
`docs/EXECUTION-PLAN.md`). Detection happens before any collector runs; zero
collectors are executable for claims with unresolved E-codes (`docs/PRD-v3.md` §7,
compile integrity guardrail).

**Placeholder population magnitudes** (pending realistic sizes from the reference
engagement — `[NEED: Owner]`, see `docs/HANDOFF.md` §6): ~200 employees in the HRIS
population, ~15 terminations in the audit period.

`TODO(playbook)`: the mutation playbook document itself is not in this repo —
`[NEED: Owner]`. This fixture is authored from the PRD §6 summary; reconcile against
the playbook when it lands.
