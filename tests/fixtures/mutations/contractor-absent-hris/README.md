# Poison: contractor absent from HRIS

**Provenance:** `docs/PRD-v3.md` §6 — "one contractor absent from Workday" — one of
the six mutation-playbook poison cases seeded into the V1 termination lane.
Headline metric: assurance defect detection rate (`docs/PRD-v3.md` §7).

**Scenario.** A contractor (e.g. `t.contractor@example.com`) holds active access in
downstream systems (GitHub, GCP, Slack) but has no record in the HRIS feed. The
termination-lane population derived from HRIS therefore cannot account for this
identity: the population basis is incomplete at the source.

**Expected outcome** (`expected_outcome.json`): `VERDICT` with state `UNKNOWN`,
why-code `UNKNOWN_POPULATION` — the population cannot be shown complete, and an
incomplete basis is never a partial pass.

> **Open ruling:** a `FAIL` alternative (treating the absent contractor as a control
> failure rather than a population-completeness gap) is pending an Owner ruling. Until
> ruled, this fixture encodes `UNKNOWN`/`UNKNOWN_POPULATION`. If the ruling lands as
> FAIL, update `expected_outcome.json` and this README in the same commit.

**Placeholder population magnitudes** (pending realistic sizes from the reference
engagement — `[NEED: Owner]`, see `docs/HANDOFF.md` §6): ~200 employees in the HRIS
population, ~15 terminations in the audit period.

`TODO(playbook)`: the mutation playbook document itself is not in this repo —
`[NEED: Owner]`. This fixture is authored from the PRD §6 summary; reconcile against
the playbook when it lands.
