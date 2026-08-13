# Poison: delayed revocation

**Provenance:** `docs/PRD-v3.md` §6 — "one delayed revocation" — one of the six
mutation-playbook poison cases seeded into the V1 termination lane.
Headline metric: assurance defect detection rate (`docs/PRD-v3.md` §7).

**Scenario.** A terminated employee's access (e.g. `alex.rivera`'s GCP IAM binding)
is revoked, but only after the TIMING assertion's window (≤ 5 business days from the
termination event, business-day math per EVAL01) has elapsed. Revocation happened —
but not on time, and timeliness is what the assertion tests.

**Expected outcome** (`expected_outcome.json`): `VERDICT` with state `FAIL` — the
TIMING assertion computes the interval from the termination event to the revocation
record and finds it outside the window. Late is a failure, never a pass.

**Placeholder population magnitudes** (pending realistic sizes from the reference
engagement — `[NEED: Owner]`, see `docs/HANDOFF.md` §6): ~200 employees in the HRIS
population, ~15 terminations in the audit period.

`TODO(playbook)`: the mutation playbook document itself is not in this repo —
`[NEED: Owner]`. This fixture is authored from the PRD §6 summary; reconcile against
the playbook when it lands.
