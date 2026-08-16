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
