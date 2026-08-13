"""COL01 tests — pagination exhaustion, hashing, EQC, seeded detection.

Acceptance (docs/HANDOFF.md §4 COL01–05): enumeration exhausts
pagination; raw responses hashed; EQC produced with all five property
methods named; fixture tenants only; and the seeded failing fixture
(``tests/fixtures/seeded/hris_truncated_feed/``) MUST be detected —
no detection proof, no merge.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import pytest

from aegis_sentinel.collectors import (
    FixtureTransport,
    HrisTerminationsCollector,
    PageRequest,
)
from aegis_sentinel.schema import AssertionType
from conftest import SEEDED_TRUNCATED_DIR, TENANTS_DIR

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class StubTransport:
    """In-memory page list, for shapes the on-disk fixtures don't seed."""

    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self._pages = pages

    def fetch_page(self, request: PageRequest) -> dict[str, Any] | None:
        index = request.page_index - 1
        return self._pages[index] if index < len(self._pages) else None


@pytest.fixture(scope="module")
def collector() -> HrisTerminationsCollector:
    return HrisTerminationsCollector(FixtureTransport(TENANTS_DIR))


@pytest.fixture(scope="module")
def snapshot(collector, feed_plan, retrieved_at):
    return collector.collect(feed_plan, retrieved_at)


def test_pagination_exhausted_at_trailer(snapshot) -> None:
    """All three pages fetched; the trailer on page 3 is the stop signal."""
    assert len(snapshot.pages) == 3
    assert snapshot.complete
    assert snapshot.incompleteness == ()


def test_every_raw_page_and_the_snapshot_are_hashed(snapshot) -> None:
    assert len(snapshot.page_hashes) == 3
    assert all(SHA256_RE.match(h) for h in snapshot.page_hashes)
    assert len(set(snapshot.page_hashes)) == 3  # distinct raw pages
    assert snapshot.snapshot_hash is not None
    assert SHA256_RE.match(snapshot.snapshot_hash)
    assert snapshot.compute_snapshot_hash() == snapshot.snapshot_hash


def test_collection_reperformance_is_byte_identical(collector, feed_plan, retrieved_at) -> None:
    again = collector.collect(feed_plan, retrieved_at)
    assert again.model_dump_json() == collector.collect(feed_plan, retrieved_at).model_dump_json()


def test_events_parse_in_feed_order(snapshot) -> None:
    events = HrisTerminationsCollector.events(snapshot)
    assert len(events) == 15
    assert events[0].employee_id == "E-1004"
    assert events[0].email == "avery.chen@meridianfinancial.example"
    assert events[-1].employee_id == "CT-2044"
    contractors = [e for e in events if e.worker_type == "contractor"]
    assert [c.employee_id for c in contractors] == ["CT-2044"]


def test_seeded_truncated_feed_is_flagged_incomplete(feed_plan, retrieved_at) -> None:
    """The seeded failing fixture: trailer never arrives → incomplete.

    This is the detection proof required for merge: a plausible-looking
    truncated feed may NEVER produce a complete snapshot.
    """
    collector = HrisTerminationsCollector(FixtureTransport(SEEDED_TRUNCATED_DIR))
    snapshot = collector.collect(feed_plan, retrieved_at)
    assert len(snapshot.pages) == 2
    assert not snapshot.complete
    assert any("trailer record missing" in reason for reason in snapshot.incompleteness)


def test_short_row_count_vs_declared_total_is_flagged(feed_plan, retrieved_at) -> None:
    """Trailer present but rows short of the declared total → incomplete."""
    page = {
        "feed": "hris-termination-feed",
        "page": 1,
        "rows": [
            {
                "record_type": "termination",
                "employee_id": "E-9001",
                "work_email": "test.one@meridianfinancial.example",
                "worker_type": "employee",
                "termination_date": "2026-03-02",
                "last_day_worked": "2026-03-02",
                "termination_reason_code": "VOL",
            },
            {"record_type": "trailer", "total_rows": 3},
        ],
    }
    collector = HrisTerminationsCollector(StubTransport([page]))
    snapshot = collector.collect(feed_plan, retrieved_at)
    assert not snapshot.complete
    assert any(
        "1 termination row(s) != trailer-declared total 3" in reason
        for reason in snapshot.incompleteness
    )


def test_plan_for_another_system_is_rejected(compile_result, retrieved_at) -> None:
    from aegis_sentinel.compile import executable_collectors

    github_plan = next(p for p in executable_collectors(compile_result) if p.system == "github")
    collector = HrisTerminationsCollector(FixtureTransport(TENANTS_DIR))
    with pytest.raises(ValueError, match="serves 'hris'"):
        collector.collect(github_plan, retrieved_at)


def test_contract_names_all_five_property_methods(collector, feed_plan, retrieved_at) -> None:
    contract = collector.contract(feed_plan, "meridian-financial", retrieved_at)
    # population: the capability entry's exhaustion method, verbatim.
    assert contract.population.method == feed_plan.pagination.exhaustion_method
    assert "trailer record" in contract.population.method
    assert feed_plan.entry_id in contract.provenance.method
    assert "SHA-256" in contract.integrity.method
    for key in feed_plan.join_keys:
        assert key in contract.semantics.method
    assert "snapshot-cadence" in contract.temporal_validity.method
    assert "2026-01-01..2026-06-30" in contract.temporal_validity.method
    assert contract.auth_context == feed_plan.auth_scope
    assert contract.contract_hash is not None
    assert SHA256_RE.match(contract.contract_hash)


def test_contract_supported_types_follow_temporal_shape(collector, feed_plan, retrieved_at) -> None:
    """A snapshot-cadence feed never claims it can support TIMING (PRD-v3 §2)."""
    contract = collector.contract(feed_plan, "meridian-financial", retrieved_at)
    assert contract.supported_assertion_types == frozenset(
        {
            AssertionType.STATE,
            AssertionType.EXISTENCE,
            AssertionType.NON_EXISTENCE,
            AssertionType.AGGREGATE,
        }
    )


def test_contract_hash_is_authored_before_collection(collector, feed_plan) -> None:
    """retrieved_at is nulled in the hash: contract identity predates the run."""
    day_one = datetime(2026, 7, 1, tzinfo=timezone.utc)
    day_two = datetime(2026, 7, 2, tzinfo=timezone.utc)
    one = collector.contract(feed_plan, "meridian-financial", day_one)
    two = collector.contract(feed_plan, "meridian-financial", day_two)
    assert one.retrieved_at != two.retrieved_at
    assert one.contract_hash == two.contract_hash
