"""REC01 engine tests: three named sources (hris authoritative + two
contributing) join on canonical email, all six delta buckets come out
as first-class schema.Delta objects, boundary exclusions record their
ratified refs (D-9), and the DISCOVERED→RECONCILED gate still runs only
through schema.models.advance — open-question buckets block until
dispositioned, resolved buckets (intersection/excluded) never do."""

import json
from pathlib import Path

import pytest

from aegis_sentinel.reconcile.engine import (
    BoundaryExclusion,
    SourceMember,
    SourceSet,
    load_boundary_exclusions,
    load_source_sets,
    reconcile_sets,
)
from aegis_sentinel.reconcile.minimal import apply_dispositions
from aegis_sentinel.schema import (
    AssuranceState,
    D7Family,
    DeltaBucket,
    DispositionRecord,
    Population,
    advance,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def population(state="DISCOVERED"):
    data = json.loads((FIXTURES / "ontology" / "population_valid.json").read_text())
    data["state"] = state
    return Population.model_validate(data)


def sources():
    raw = json.loads((FIXTURES / "reconcile_engine" / "sources.json").read_text())
    return load_source_sets(raw["sources"])


def exclusions():
    raw = json.loads((FIXTURES / "reconcile_engine" / "boundary_exclusions.json").read_text())
    return load_boundary_exclusions(raw["exclusions"])


def reconcile(**overrides):
    kwargs = dict(
        population=population(),
        sources=sources(),
        boundary_exclusions=exclusions(),
    )
    kwargs.update(overrides)
    return reconcile_sets(kwargs.pop("population"), kwargs.pop("sources"), **kwargs)


def refs(deltas):
    return [d.member_ref for d in deltas]


def test_all_six_buckets_as_first_class_deltas():
    """Every bucket carries member refs (D-8 set reconciliation);
    canonicalization is reused from minimal (BEN@Example.COM variants
    join as one identity)."""
    result = reconcile()
    b = result.buckets
    assert refs(b.intersection) == ["email:ada@example.com", "email:ben@example.com"]
    assert refs(b.left_only) == ["email:cleo@example.com", "email:ed@example.com"]
    assert refs(b.right_only) == ["email:mira@example.com"]
    assert refs(b.conflict) == ["email:dora@example.com"]
    assert refs(b.unresolvable) == ["okta:00u7", "worker:W-1099"]
    assert refs(b.excluded) == ["email:svc-deploy@example.com"]
    assert all(d.bucket is bucket for bucket in DeltaBucket for d in getattr(b, bucket.value))
    assert result.canonical_members == ("ada@example.com", "ben@example.com")


def test_delta_cause_mirrors_d7_family_per_bucket():
    """D-7 cause (issue #69) is a pure function of bucket, computed once
    on schema.models.Delta — mirrors web/src/data/reconciliation.ts's
    (retired) D7_BY_BUCKET table exactly. conflict/intersection/excluded
    carry no cause: a conflict is a successful join with disagreeing
    attributes (D-8), not a join failure."""
    result = reconcile()
    b = result.buckets
    assert {d.cause for d in b.left_only} == {D7Family.BASIS_MISSING}
    assert {d.cause for d in b.unresolvable} == {D7Family.IDENTITY_FUZZY}
    assert {d.cause for d in b.right_only} == {D7Family.NO_BASIS_ANYWHERE}
    assert all(d.cause is None for d in b.conflict)
    assert all(d.cause is None for d in b.intersection)
    assert all(d.cause is None for d in b.excluded)


def test_counts_are_diagnostics_only():
    result = reconcile()
    assert result.buckets.counts == {
        "intersection": 2,
        "left_only": 2,
        "right_only": 1,
        "conflict": 1,
        "unresolvable": 2,
        "excluded": 1,
    }
    # population.size is the canonical intersection count — a
    # diagnostic, never evidence
    assert result.population.size == 2


def test_absence_dominates_attribute_mismatch():
    """ed@ is in hris+okta with mismatched status but missing from
    github: LEFT_ONLY, not CONFLICT — a member cannot be adjudicated as
    conflicting with a source it is absent from."""
    result = reconcile()
    assert "email:ed@example.com" in refs(result.buckets.left_only)
    assert "email:ed@example.com" not in refs(result.buckets.conflict)


def test_excluded_delta_records_the_ratified_exclusion_ref():
    """D-9: the exclusion enters only as a ratified ref; the delta
    records ref and ratifier, and arrives already dispositioned."""
    result = reconcile()
    (excluded,) = result.buckets.excluded
    assert excluded.owner == "vinylfigure (Ratifier)"
    assert excluded.dispositioned
    assert "boundary/v3#service-accounts" in excluded.disposition.rationale


def test_reconcile_does_not_touch_ladder_state():
    assert reconcile().population.state is AssuranceState.DISCOVERED


def test_open_buckets_block_reconciled_until_each_is_dispositioned():
    """DISCOVERED→RECONCILED goes only through schema.models.advance;
    an undispositioned left_only, conflict, or unresolvable delta each
    keeps blocking on its own."""
    result = reconcile()
    open_refs = [
        d.member_ref for d in result.population.deltas if d.bucket is not DeltaBucket.EXCLUDED
    ]
    assert len(open_refs) == 6
    with pytest.raises(ValueError, match="undispositioned"):
        advance(result.population, AssuranceState.RECONCILED)
    # disposition all but one, once per open bucket kind: still blocked
    for hold_back in (
        "email:cleo@example.com",  # left_only
        "email:dora@example.com",  # conflict
        "worker:W-1099",  # unresolvable
    ):
        dispositions = {
            ref: DispositionRecord(value="compensating", owner="vinylfigure", rationale="fixture")
            for ref in open_refs
            if ref != hold_back
        }
        partial = apply_dispositions(result.population, dispositions)
        with pytest.raises(ValueError, match="undispositioned"):
            advance(partial, AssuranceState.RECONCILED)


def test_advance_passes_once_every_open_delta_is_dispositioned():
    result = reconcile()
    dispositions = {
        d.member_ref: DispositionRecord(
            value="compensating", owner="vinylfigure", rationale="fixture"
        )
        for d in result.population.deltas
        if d.bucket is not DeltaBucket.EXCLUDED
    }
    reconciled = advance(
        apply_dispositions(result.population, dispositions), AssuranceState.RECONCILED
    )
    assert reconciled.state is AssuranceState.RECONCILED


def test_intersection_and_excluded_need_no_dispositions():
    """Resolved states, not open questions: presence everywhere is the
    canonical membership itself, and an EXCLUDED delta's ratified
    boundary exclusion (D-9) already is its human resolution — so a run
    with only these two buckets advances with no disposition act."""
    agreed = tuple(
        SourceSet(
            name=name,
            role=role,
            members=(
                SourceMember(ref=f"{name}:ada", email="ada@example.com"),
                SourceMember(ref=f"{name}:svc", email="svc-deploy@example.com"),
            ),
        )
        for name, role in (
            ("hris", "authoritative"),
            ("okta", "contributing"),
            ("github", "contributing"),
        )
    )
    result = reconcile(sources=agreed)
    assert refs(result.buckets.intersection) == ["email:ada@example.com"]
    assert refs(result.buckets.excluded) == ["email:svc-deploy@example.com"]
    assert refs(result.population.deltas) == ["email:svc-deploy@example.com"]
    reconciled = advance(result.population, AssuranceState.RECONCILED)
    assert reconciled.state is AssuranceState.RECONCILED


def test_exactly_one_authoritative_source_required():
    two_contributing = tuple(s for s in sources() if s.name != "hris")
    with pytest.raises(ValueError, match="exactly one authoritative"):
        reconcile(sources=two_contributing)
    doubled = (*sources(), SourceSet(name="hris2", role="authoritative"))
    with pytest.raises(ValueError, match="exactly one authoritative"):
        reconcile(sources=doubled)


def test_duplicate_source_names_rejected():
    doubled = (*sources(), SourceSet(name="hris", role="contributing"))
    with pytest.raises(ValueError, match="unique"):
        reconcile(sources=doubled)


def test_at_least_two_sources_required():
    with pytest.raises(ValueError, match="at least two"):
        reconcile(sources=sources()[:1])


def test_boundary_exclusion_without_canonical_member_rejected():
    bogus = (BoundaryExclusion(member="   ", ref="boundary/v3#x", ratified_by="vinylfigure"),)
    with pytest.raises(ValueError, match="no canonical member"):
        reconcile(boundary_exclusions=bogus)
