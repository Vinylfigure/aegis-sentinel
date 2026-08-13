# Poison: failed identity join

**Provenance:** `docs/PRD-v3.md` §6 — "one failed identity join" — one of the six
mutation-playbook poison cases seeded into the V1 termination lane.
Headline metric: assurance defect detection rate (`docs/PRD-v3.md` §7).

**Scenario.** The canonical-identity join cannot resolve a record across sources:
the HRIS feed carries `alex.rivera`, Okta carries `arivera@example.com`, and a Slack
account `a.rivera.ext@example.com` matches neither deterministically. The record
lands in the reconciler's *unresolvable* delta bucket, so the joined population
cannot be shown complete.

**Expected outcome** (`expected_outcome.json`): `VERDICT` with state `UNKNOWN`,
why-code `UNKNOWN_POPULATION` — an unresolvable identity is a population-level
unknown (the prior scaffold's `identity_fuzzy` D-7 family, which maps to
`UNKNOWN_POPULATION` per D-U1 in `src/aegis_sentinel/schema/verdict.py`). It routes
to a human resolution queue; it never maps to satisfied.

**Placeholder population magnitudes** (pending realistic sizes from the reference
engagement — `[NEED: Owner]`, see `docs/HANDOFF.md` §6): ~200 employees in the HRIS
population, ~15 terminations in the audit period.

`TODO(playbook)`: the mutation playbook document itself is not in this repo —
`[NEED: Owner]`. This fixture is authored from the PRD §6 summary; reconcile against
the playbook when it lands.
