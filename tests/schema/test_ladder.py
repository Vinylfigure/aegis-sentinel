"""Assurance-state ladder: legal transitions pass; everything else raises."""

from __future__ import annotations

import pytest

from aegis_sentinel.schema import AssuranceState, transition

S = AssuranceState

LEGAL = [
    (S.UNDEFINED, S.DEFINED),
    (S.DEFINED, S.DISCOVERED),
    (S.DISCOVERED, S.RECONCILED),
    (S.RECONCILED, S.RATIFIED),
    (S.RATIFIED, S.STALE),
    (S.STALE, S.DISCOVERED),  # re-entry
]

ILLEGAL = [
    (S.UNDEFINED, S.DISCOVERED),  # skip
    (S.UNDEFINED, S.RATIFIED),  # skip to top
    (S.DEFINED, S.RECONCILED),  # skip
    (S.RECONCILED, S.DEFINED),  # backward
    (S.RATIFIED, S.RECONCILED),  # backward
    (S.RATIFIED, S.DEFINED),  # backward from top
    (S.RATIFIED, S.RATIFIED),  # self
    (S.STALE, S.RATIFIED),  # STALE only re-enters at DISCOVERED
    (S.STALE, S.STALE),  # self at terminal rung
    (S.DISCOVERED, S.DISCOVERED),  # self
]


@pytest.mark.parametrize("state,to", LEGAL, ids=[f"{a.value}->{b.value}" for a, b in LEGAL])
def test_legal_transition(state: S, to: S) -> None:
    assert transition(state, to) is to


@pytest.mark.parametrize("state,to", ILLEGAL, ids=[f"{a.value}->{b.value}" for a, b in ILLEGAL])
def test_illegal_transition_raises(state: S, to: S) -> None:
    with pytest.raises(ValueError):
        transition(state, to)


def test_every_state_has_exactly_one_successor() -> None:
    for state in S:
        successors = [to for to in S if _legal(state, to)]
        assert len(successors) == 1, f"{state.value} has successors {successors}"


def _legal(state: S, to: S) -> bool:
    try:
        transition(state, to)
        return True
    except ValueError:
        return False
