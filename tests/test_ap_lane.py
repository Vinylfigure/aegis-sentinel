"""LANE02 acceptance: the AP-automation lane instantiates from the same
template schema, unchanged. Where AP controls did not fit the schema, they
are absent here by design and recorded in docs/lane-fit-notes.md
(FIT-001..FIT-005) — the honesty-boundary tests below pin that outcome."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from aegis_sentinel.lanes import LaneTemplate, instantiate, load_template
from aegis_sentinel.schema import AssertionType, PopulationType, TimeWindow

TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent / "templates" / "lanes" / "ap_automation.json"
)
PERIOD = TimeWindow(start=datetime(2026, 1, 1, tzinfo=UTC), end=datetime(2026, 6, 30, tzinfo=UTC))
BINDINGS = {
    "source-of-truth": "netsuite",
    "approval-workflow": "approval-tool",
    "payment-execution": "banking",
    "vendor-master": "vendor-hub",
}


def test_template_is_valid_closed_data():
    template = load_template(TEMPLATE_PATH)
    assert template.id == "ap-automation"
    assert template.event_role == "source-of-truth"
    assert len(template.downstream_roles) == 3
    assert len(template.control_points) == 6


def test_template_rejects_dangling_graph_refs():
    raw = load_template(TEMPLATE_PATH).model_dump()
    raw["edges"] = [*raw["edges"], {"source": "ghost", "target": "vendor-master", "trigger": "x"}]
    with pytest.raises(ValidationError, match="unknown role"):
        LaneTemplate.model_validate(raw)


def test_instantiation_yields_populations_and_claims():
    instance = instantiate(load_template(TEMPLATE_PATH), BINDINGS, PERIOD)
    assert len(instance.populations) == 4  # 1 event + 3 downstream entity
    event = instance.populations[0]
    assert event.type is PopulationType.EVENT
    assert event.authoritative_source.system == "netsuite"
    for pop in instance.populations[1:]:
        assert pop.type is PopulationType.ENTITY
        assert pop.derivation_rule is not None  # exactly-one invariant holds by model
    # 3 control points at source-of-truth + 3 per-role access control points
    assert len(instance.claims) == 6
    population_ids = {p.id for p in instance.populations}
    for claim in instance.claims:
        assert claim.population_id in population_ids


def test_assertion_vocabulary_is_the_intended_slice():
    instance = instantiate(load_template(TEMPLATE_PATH), BINDINGS, PERIOD)
    types = {a.type for c in instance.claims for a in c.assertions}
    assert types == {
        AssertionType.EVENT,
        AssertionType.SEQUENCE,
        AssertionType.TIMING,
        AssertionType.EXISTENCE,
        AssertionType.NON_EXISTENCE,
    }


def test_timing_assertion_carries_the_ten_business_day_window():
    instance = instantiate(load_template(TEMPLATE_PATH), BINDINGS, PERIOD)
    timing = [a for c in instance.claims for a in c.assertions if a.type is AssertionType.TIMING]
    assert timing, "the lane lost its TIMING assertion"
    assert all(a.timing.days == 10 and a.timing.business_days for a in timing)


def test_access_claims_bind_to_their_own_access_populations():
    """The three unrolled access control points (FIT-004) each land on the
    matching downstream system's access-holder population."""
    instance = instantiate(load_template(TEMPLATE_PATH), BINDINGS, PERIOD)
    non_existence = {
        c.id: c.population_id
        for c in instance.claims
        if any(a.type is AssertionType.NON_EXISTENCE for a in c.assertions)
    }
    assert non_existence == {
        "claim-cp-approval-access-approval-tool": "pop-ap-automation-approval-tool-access",
        "claim-cp-payment-access-banking": "pop-ap-automation-banking-access",
        "claim-cp-vendor-master-access-vendor-hub": "pop-ap-automation-vendor-hub-access",
    }


def test_misfit_boundary_no_payment_event_population():
    """FIT-001 honesty boundary: the lane does not pretend to a payments
    population — the only EVENT population is the approved-invoice feed, so
    'no payment without approved invoice' stays recorded, not inverted."""
    instance = instantiate(load_template(TEMPLATE_PATH), BINDINGS, PERIOD)
    events = [p for p in instance.populations if p.type is PopulationType.EVENT]
    assert [p.id for p in events] == ["pop-ap-automation-events"]
    sequence_claims = [
        c for c in instance.claims if any(a.type is AssertionType.SEQUENCE for a in c.assertions)
    ]
    # FIT-002: the SEQUENCE claim is formally grounded in the approved-invoice
    # population only; its payment leg exists in prose alone.
    assert all(c.population_id == "pop-ap-automation-events" for c in sequence_claims)


def test_unbound_role_never_shrinks_scope_silently():
    partial = {k: v for k, v in BINDINGS.items() if k != "payment-execution"}
    with pytest.raises(ValueError, match="unbound lane roles"):
        instantiate(load_template(TEMPLATE_PATH), partial, PERIOD)


def test_instantiation_is_deterministic():
    template = load_template(TEMPLATE_PATH)
    first = instantiate(template, BINDINGS, PERIOD)
    second = instantiate(template, BINDINGS, PERIOD)
    assert first == second
