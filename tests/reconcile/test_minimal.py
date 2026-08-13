"""Walking-skeleton reconciler tests — the single-source identity pass.

REC01 will generalize to N-source set reconciliation; these tests pin
the skeleton contract: canonical member list, one legal ladder step,
all six bucket lists present, and a truncated basis never discovering
a population.
"""

from __future__ import annotations

import pytest

from aegis_sentinel.reconcile import SourceMembers, reconcile_population
from aegis_sentinel.schema import AssuranceState

FEED_SOURCE = "hris-termination-feed"


def complete_source(member_ids: tuple[str, ...]) -> SourceMembers:
    return SourceMembers(source_id=FEED_SOURCE, complete=True, member_ids=member_ids)


def test_single_source_builds_population_and_canonical_members(terminations_population) -> None:
    result = reconcile_population(
        terminations_population,
        [complete_source(("E-1019", "E-1004", "CT-2044", "E-1019"))],  # unsorted + dup
    )
    assert result.members == ("CT-2044", "E-1004", "E-1019")  # sorted, de-duplicated
    assert result.population.size == 3
    assert result.population.state is AssuranceState.DISCOVERED
    assert result.basis_complete


def test_single_source_intersection_is_the_set_and_deltas_are_empty(
    terminations_population,
) -> None:
    result = reconcile_population(terminations_population, [complete_source(("E-1004",))])
    assert result.intersection == result.members
    assert result.left_only == ()
    assert result.right_only == ()
    assert result.conflicts == ()
    assert result.unresolvable == ()
    assert result.excluded == ()
    assert result.open_deltas == ()


def test_incomplete_basis_never_discovers_the_population(terminations_population) -> None:
    """Partial collection: no member list, no size, no ladder step."""
    truncated = SourceMembers(
        source_id=FEED_SOURCE,
        complete=False,
        notes=("trailer record missing after 2 page(s)",),
        member_ids=("E-1004", "E-1019"),
    )
    result = reconcile_population(terminations_population, [truncated])
    assert not result.basis_complete
    assert result.basis_notes == (f"{FEED_SOURCE}: trailer record missing after 2 page(s)",)
    assert result.members == ()
    assert result.population.size is None
    assert result.population.state is AssuranceState.DEFINED
    assert result.open_deltas == ()


def test_undeclared_source_is_rejected(terminations_population) -> None:
    stray = SourceMembers(source_id="github-account-inventory", complete=True)
    with pytest.raises(ValueError, match="not declared"):
        reconcile_population(terminations_population, [stray])


def test_missing_derivation_source_is_rejected(terminations_population) -> None:
    corroborating_only = SourceMembers(source_id="okta-system-log", complete=True)
    with pytest.raises(ValueError, match="derivation-rule source"):
        reconcile_population(terminations_population, [corroborating_only])


def test_duplicate_sources_are_rejected(terminations_population) -> None:
    with pytest.raises(ValueError, match="duplicate"):
        reconcile_population(
            terminations_population,
            [complete_source(("E-1004",)), complete_source(("E-1019",))],
        )


def test_multi_source_without_typed_members_refuses(terminations_population) -> None:
    """REC01 landed: N sources are joined — but only over typed members.

    Bare member_ids carry no join keys, so pretending to set-reconcile
    them would be a fake join; the reconciler refuses loudly instead.
    """
    with pytest.raises(ValueError, match="typed members"):
        reconcile_population(
            terminations_population,
            [
                complete_source(("E-1004",)),
                SourceMembers(source_id="okta-system-log", complete=True),
            ],
        )


def test_reperformance_is_identical(terminations_population) -> None:
    sources = [complete_source(("E-1019", "E-1004"))]
    one = reconcile_population(terminations_population, sources)
    two = reconcile_population(terminations_population, sources)
    assert one.model_dump_json() == two.model_dump_json()
