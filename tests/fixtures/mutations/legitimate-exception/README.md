# Poison: legitimate exception

**Provenance:** `docs/PRD-v3.md` §6 — "one legitimate exception" — one of the six
mutation-playbook poison cases seeded into the V1 termination lane.
Headline metric: assurance defect detection rate (`docs/PRD-v3.md` §7).

**Scenario.** A terminated contractor (e.g. `t.contractor@example.com`) retains
narrowly-scoped access past the termination date under a documented, human-ratified
disposition (e.g. a 30-day knowledge-transfer window). The access is real and
post-termination — but it is covered by a disposition record.

**Expected outcome** (`expected_outcome.json`): `VERDICT` with state `EXCEPTION` —
distinct from PASS and from FAIL (D-V1: EXCEPTION requires a `disposition_ref`, see
`src/aegis_sentinel/schema/verdict.py`). The harness treats EXCEPTION as the correct
detection here: this poison tests that the pipeline neither silently passes the
access nor mislabels a dispositioned exception as a failure. Any other state —
including PASS — counts as undetected.

**Placeholder population magnitudes** (pending realistic sizes from the reference
engagement — `[NEED: Owner]`, see `docs/HANDOFF.md` §6): ~200 employees in the HRIS
population, ~15 terminations in the audit period.

`TODO(playbook)`: the mutation playbook document itself is not in this repo —
`[NEED: Owner]`. This fixture is authored from the PRD §6 summary; reconcile against
the playbook when it lands.
