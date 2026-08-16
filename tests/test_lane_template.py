"""LANE01 acceptance: the termination lane is data; instantiating it with
the five fixture systems yields the populations and claims the compiler
consumes."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from aegis_sentinel.lanes import LaneTemplate, instantiate, load_template
from aegis_sentinel.schema import AssertionType, PopulationType, TimeWindow

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "lanes" / "termination.json"
PERIOD = TimeWindow(start=datetime(2026, 7, 1, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC))
BINDINGS = {
    "source-of-truth": "workday",
    "identity-provider": "okta",
    "code-hosting": "github",
    "cloud": "gcp",
    "messaging": "slack",
}


def test_template_is_valid_closed_data():
    template = load_template(TEMPLATE_PATH)
    assert template.id == "termination"
    assert len(template.downstream_roles) == 4


def test_template_rejects_dangling_graph_refs():
    raw = load_template(TEMPLATE_PATH).model_dump()
    raw["edges"] = [*raw["edges"], {"source": "ghost", "target": "cloud", "trigger": "x"}]
    with pytest.raises(ValidationError, match="unknown role"):
        LaneTemplate.model_validate(raw)


def test_instantiation_yields_populations_and_claims():
    instance = instantiate(load_template(TEMPLATE_PATH), BINDINGS, PERIOD)
    assert len(instance.populations) == 5  # 1 event + 4 downstream entity
    event = instance.populations[0]
    assert event.type is PopulationType.EVENT
    assert event.authoritative_source.system == "workday"
    for pop in instance.populations[1:]:
        assert pop.type is PopulationType.ENTITY
        assert pop.derivation_rule is not None  # exactly-one invariant holds by model
    # cp-idp-deactivation (1 claim) + cp-no-residual-access per downstream (4)
    assert len(instance.claims) == 5
    population_ids = {p.id for p in instance.populations}
    for claim in instance.claims:
        assert claim.population_id in population_ids


def test_timing_assertions_carry_the_five_day_constraint():
    instance = instantiate(load_template(TEMPLATE_PATH), BINDINGS, PERIOD)
    timing = [a for c in instance.claims for a in c.assertions if a.type is AssertionType.TIMING]
    assert timing, "the lane lost its TIMING assertions"
    assert all(a.timing.days == 5 and a.timing.business_days for a in timing)


def test_unbound_role_never_shrinks_scope_silently():
    partial = {k: v for k, v in BINDINGS.items() if k != "cloud"}
    with pytest.raises(ValueError, match="unbound lane roles"):
        instantiate(load_template(TEMPLATE_PATH), partial, PERIOD)


def test_instantiation_is_deterministic():
    template = load_template(TEMPLATE_PATH)
    first = instantiate(template, BINDINGS, PERIOD)
    second = instantiate(template, BINDINGS, PERIOD)
    assert first == second
