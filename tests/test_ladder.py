"""Assurance-ladder transition tests (SCH01)."""

import json
from pathlib import Path

import pytest

from aegis_sentinel.schema import AssuranceState, Population, advance

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ontology"


def population(**overrides):
    data = json.loads((FIXTURES / "population_valid.json").read_text())
    data.update(overrides)
    return Population.model_validate(data)


def test_full_forward_chain_is_legal():
    p = population()
    for state in (
        AssuranceState.DEFINED,
        AssuranceState.DISCOVERED,
        AssuranceState.RECONCILED,
        AssuranceState.RATIFIED,
        AssuranceState.STALE,
        AssuranceState.DISCOVERED,
    ):
        p = advance(p, state)
    assert p.state is AssuranceState.DISCOVERED


def test_skipping_a_rung_is_illegal():
    with pytest.raises(ValueError, match="illegal ladder transition"):
        advance(population(), AssuranceState.RATIFIED)


def test_reconciled_blocked_while_deltas_undispositioned():
    p = population(
        state="DISCOVERED",
        deltas=[{"bucket": "left_only", "member_ref": "user:jdoe"}],
    )
    with pytest.raises(ValueError, match="undispositioned"):
        advance(p, AssuranceState.RECONCILED)
    p = population(
        state="DISCOVERED",
        deltas=[
            {
                "bucket": "left_only",
                "member_ref": "user:jdoe",
                "owner": "vinylfigure",
                "disposition": {
                    "value": "not_applicable",
                    "owner": "vinylfigure",
                    "rationale": "contractor, out of scope per ratified boundary",
                },
            }
        ],
    )
    assert advance(p, AssuranceState.RECONCILED).state is AssuranceState.RECONCILED


def test_advance_is_pure():
    p = population()
    advance(p, AssuranceState.DEFINED)
    assert p.state is AssuranceState.UNDEFINED


def test_ratified_stale_discovered_cycle_reaches_the_wire():
    """RATIFIED -> STALE -> DISCOVERED is legal in LADDER_TRANSITIONS, but
    (per web/README.md Q11b) nothing in the real pipeline ever exercises it —
    build_demo_engagement.py's own `ladder` wire block only ever emits
    at_first_verdict/after_dispositions, both <= RECONCILED, and STALE's only
    prior call site was the isolated loop in test_full_forward_chain_is_legal.
    This disposes a real delta to legally clear the RECONCILED gate, then
    walks RATIFIED -> STALE -> DISCOVERED, capturing `.state.value` — the
    same field the real artifact serializes — into a dict shaped like
    reconciliation_artifact['ladder'], proving the off-strip re-entry
    survives onto the wire through a realistic sequence.
    """
    p = population(
        state="DISCOVERED",
        deltas=[
            {
                "bucket": "left_only",
                "member_ref": "user:jdoe",
                "owner": "vinylfigure",
                "disposition": {
                    "value": "not_applicable",
                    "owner": "vinylfigure",
                    "rationale": "contractor, out of scope per ratified boundary",
                },
            }
        ],
    )
    wire_ladder = {}
    p = advance(p, AssuranceState.RECONCILED)
    wire_ladder["after_dispositions"] = p.state.value
    p = advance(p, AssuranceState.RATIFIED)
    wire_ladder["after_ratification"] = p.state.value
    p = advance(p, AssuranceState.STALE)
    wire_ladder["after_staleness"] = p.state.value
    p = advance(p, AssuranceState.DISCOVERED)
    wire_ladder["after_rediscovery"] = p.state.value

    assert wire_ladder == {
        "after_dispositions": "RECONCILED",
        "after_ratification": "RATIFIED",
        "after_staleness": "STALE",
        "after_rediscovery": "DISCOVERED",
    }
