"""COL02 acceptance: deterministic collection, per-page raw hashing,
cursor-chain exhaustion recorded page by page, refusal on a broken or
cyclic chain (seeded fixture detected), wrong-tenant refusal, window
honesty (E204 refusal when the asserted period outruns the 90-day
event-history window), null-email target surfaced not dropped, and an
EQC with all five quality property methods named."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aegis_sentinel.collectors.okta_system_log import (
    canonical_contract_hash,
    collect_okta_deactivations,
)
from aegis_sentinel.schema import TimeWindow

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "collectors" / "okta_system_log"
TENANT_DIR = FIXTURES / "tenant"
BROKEN_CHAIN_DIR = FIXTURES / "seeded" / "broken_chain"
WRONG_TENANT_DIR = FIXTURES / "wrong_tenant"
# Within the 90-day window of the fixture extract time (2026-12-31T12:00:00Z,
# floor 2026-10-02T12:00:00Z).
PERIOD = TimeWindow(
    start=datetime(2026, 10, 15, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC)
)
TENANT = "meridian-financial-fixtures"


def transport_for(directory: Path, mutate=None):
    """Cursor transport over a fixture directory: pages keyed by their
    'cursor' field; an unknown cursor returns None (no such page)."""
    pages = {}
    for path in sorted(directory.glob("page-*.json")):
        payload = json.loads(path.read_text())
        pages[payload["cursor"]] = payload
    if mutate:
        mutate(pages)
    return lambda cursor: json.dumps(pages[cursor]).encode("utf-8") if cursor in pages else None


def collect(transport=None, tenant=TENANT, period=PERIOD):
    return collect_okta_deactivations(
        transport or transport_for(TENANT_DIR),
        tenant=tenant,
        period=period,
        population_ref="pop-okta-deactivation-events",
    )


def test_collection_is_deterministic():
    first, second = collect(), collect()
    assert first == second
    assert first.raw_sha256 == second.raw_sha256
    assert first.contract.contract_hash == second.contract.contract_hash


def test_per_page_hashes_and_collection_hash_cover_the_raw_bytes():
    transport = transport_for(TENANT_DIR)
    collection = collect(transport=transport)
    combined = hashlib.sha256()
    for link in collection.pagination.cursor_chain:
        raw = transport(link.cursor)
        assert link.raw_sha256 == hashlib.sha256(raw).hexdigest()
        combined.update(raw)
    assert collection.raw_sha256 == combined.hexdigest()


def test_cursor_chain_exhaustion_recorded_page_by_page():
    pagination = collect().pagination
    assert pagination.method == "cursor"
    assert pagination.exhausted is True
    assert pagination.pages_fetched == 3
    assert [link.cursor for link in pagination.cursor_chain] == [None, "cur-0002", "cur-0003"]
    assert [link.next_cursor for link in pagination.cursor_chain] == ["cur-0002", "cur-0003", None]
    assert pagination.cursor_chain[-1].next_cursor is None
    assert "13 events seen" in pagination.exhaustion_method
    assert "12 user.lifecycle.deactivate" in pagination.exhaustion_method


def test_seeded_broken_chain_fixture_is_detected():
    # page-002 claims next cursor cur-0003; no such page exists in the
    # seeded fixture — the collector must refuse, never return 3 events.
    with pytest.raises(ValueError, match="cursor chain broken"):
        collect(transport=transport_for(BROKEN_CHAIN_DIR))


def test_repeated_cursor_is_detected():
    def mutate(pages):
        pages["cur-0003"] = dict(pages["cur-0003"], after="cur-0002")  # cycle back

    with pytest.raises(ValueError, match="does not terminate"):
        collect(transport=transport_for(TENANT_DIR, mutate))


def test_page_answering_the_wrong_cursor_is_detected():
    def mutate(pages):
        pages["cur-0002"] = dict(pages["cur-0002"], cursor="cur-9999")

    with pytest.raises(ValueError, match="requested"):
        collect(transport=transport_for(TENANT_DIR, mutate))


def test_wrong_tenant_extract_is_detected():
    with pytest.raises(ValueError, match="tenant"):
        collect(transport=transport_for(WRONG_TENANT_DIR))


def test_window_honesty_refuses_period_older_than_capability_window():
    # Extract time 2026-12-31T12:00:00Z minus 90 days = 2026-10-02T12:00:00Z;
    # a period asserted from July reaches beyond retained history and must
    # refuse (E204), never silently return a partial event history.
    stale_period = TimeWindow(
        start=datetime(2026, 7, 1, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC)
    )
    with pytest.raises(ValueError, match="E204"):
        collect(period=stale_period)


def test_period_start_on_the_window_floor_is_accepted():
    floor_period = TimeWindow(
        start=datetime(2026, 10, 2, 12, 0, 0, tzinfo=UTC),
        end=datetime(2026, 12, 31, tzinfo=UTC),
    )
    assert len(collect(period=floor_period).records) == 12


def test_only_deactivation_events_are_collected():
    records = collect().records
    assert len(records) == 12
    assert all(r.event_type == "user.lifecycle.deactivate" for r in records)
    # the suspend event was seen (counted in page evidence) but not admitted
    assert not any(r.uuid == "evt-1000" for r in records)


def test_null_email_target_is_surfaced_not_dropped():
    records = collect().records
    kai = [r for r in records if r.uuid == "evt-0008"]
    assert len(kai) == 1
    # null email survives collection; the reconciler buckets this identity
    # UNRESOLVABLE and the verdict path ends UNKNOWN_POPULATION (D-7/D-U1)
    assert kai[0].target[0].alternate_id is None
    assert kai[0].target[0].display_name == "Kai Moss"


def test_duplicate_event_id_is_kept_not_deduplicated():
    # evt-0006 is replayed at the cur-0003 page boundary; dedup is
    # reconciliation's job, not collection's
    records = collect().records
    assert sum(1 for r in records if r.uuid == "evt-0006") == 2


def test_eqc_names_all_five_quality_property_methods():
    quality = collect().contract.quality
    for prop in (
        quality.provenance,
        quality.integrity,
        quality.population,
        quality.semantics,
        quality.temporal_validity,
    ):
        assert prop.method and prop.failure_mode


def test_contract_hash_is_the_canonical_self_hash():
    contract = collect().contract
    assert contract.contract_hash == canonical_contract_hash(contract)


def test_transport_must_return_bytes_or_none():
    with pytest.raises(TypeError, match="bytes"):
        collect(transport=lambda cursor: (TENANT_DIR / "page-001.json").read_text())
