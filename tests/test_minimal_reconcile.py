"""Walking-skeleton reconciler tests: canonical identity by email, delta
buckets for members missing from one side, and the dispositioned-delta
gate on DISCOVERED→RECONCILED (via schema.models.advance)."""

import json
from pathlib import Path

import pytest

from aegis_sentinel.reconcile.minimal import (
    Member,
    apply_dispositions,
    canonical_email,
    reconcile_population,
)
from aegis_sentinel.schema import (
    AssuranceState,
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


LEFT = (
    Member(ref="worker:W-1", email="ada@example.com"),
    Member(ref="worker:W-2", email="  BEN@Example.COM "),  # canonicalized
    Member(ref="worker:W-3", email="cleo@example.com"),
    Member(ref="worker:W-3b", email="cleo@example.com"),  # rehire duplicate, dedupes
    Member(ref="worker:W-4", email=None),  # unresolvable
)
RIGHT = (
    Member(ref="ticket:T-1", email="ada@example.com"),
    Member(ref="ticket:T-2", email="ben@example.com"),
    Member(ref="ticket:T-9", email="mira@example.com"),  # right-only
)


def test_canonical_email_normalizes_and_rejects_empty():
    assert canonical_email("  BEN@Example.COM ") == "ben@example.com"
    assert canonical_email(None) is None
    assert canonical_email("   ") is None


def test_buckets_for_members_missing_from_one_side():
    result = reconcile_population(population(), LEFT, RIGHT)
    assert result.canonical_members == ("ada@example.com", "ben@example.com")
    by_bucket = {}
    for delta in result.population.deltas:
        by_bucket.setdefault(delta.bucket, []).append(delta.member_ref)
    assert by_bucket == {
        DeltaBucket.LEFT_ONLY: ["email:cleo@example.com"],
        DeltaBucket.RIGHT_ONLY: ["email:mira@example.com"],
        DeltaBucket.UNRESOLVABLE: ["worker:W-4"],
    }
    # size is the canonical intersection count — a diagnostic, never evidence
    assert result.population.size == 2


def test_reconcile_does_not_touch_ladder_state():
    result = reconcile_population(population(), LEFT, RIGHT)
    assert result.population.state is AssuranceState.DISCOVERED


def dispositions():
    return {
        ref: DispositionRecord(value="compensating", owner="vinylfigure", rationale="fixture")
        for ref in ("email:cleo@example.com", "email:mira@example.com", "worker:W-4")
    }


def test_advance_to_reconciled_blocked_until_every_delta_dispositioned():
    result = reconcile_population(population(), LEFT, RIGHT)
    with pytest.raises(ValueError, match="undispositioned"):
        advance(result.population, AssuranceState.RECONCILED)
    partial = dict(dispositions())
    del partial["worker:W-4"]
    still_open = apply_dispositions(result.population, partial)
    with pytest.raises(ValueError, match="undispositioned"):
        advance(still_open, AssuranceState.RECONCILED)


def test_advance_passes_once_dispositioned_from_fixture_records():
    result = reconcile_population(population(), LEFT, RIGHT)
    dispositioned = apply_dispositions(result.population, dispositions())
    assert all(d.dispositioned for d in dispositioned.deltas)
    assert all(d.owner == "vinylfigure" for d in dispositioned.deltas)
    reconciled = advance(dispositioned, AssuranceState.RECONCILED)
    assert reconciled.state is AssuranceState.RECONCILED


def test_disposition_for_unknown_delta_is_rejected():
    result = reconcile_population(population(), LEFT, RIGHT)
    bogus = {
        "email:nobody@example.com": DispositionRecord(
            value="compensating", owner="vinylfigure", rationale="fixture"
        )
    }
    with pytest.raises(ValueError, match="unknown deltas"):
        apply_dispositions(result.population, bogus)


def test_committed_disposition_fixture_covers_the_demo_deltas():
    """The checked-in DispositionRecord fixtures parse and match the demo
    engagement's delta refs one-to-one."""
    raw = json.loads((FIXTURES / "collectors" / "dispositions.json").read_text())
    parsed = {ref: DispositionRecord.model_validate(data) for ref, data in raw.items()}
    assert set(parsed) == {
        "email:rowan.ellis@example.com",
        "email:mira.chen@example.com",
        "worker:W-1012",
    }
