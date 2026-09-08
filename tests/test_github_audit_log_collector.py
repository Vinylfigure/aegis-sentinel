"""GitHub audit-log collector acceptance (issue #152): deterministic
collection, per-page raw hashing, cursor-chain exhaustion recorded page
by page, refusal on a broken chain (seeded fixture detected), wrong-org
refusal, window honesty (E204 refusal when the asserted period outruns
the 180-day event-history window), null-user rows surfaced not dropped,
and an EQC with all five quality property methods named."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aegis_sentinel.collectors.github_audit_log import (
    canonical_contract_hash,
    collect_github_audit_log,
)
from aegis_sentinel.schema import TimeWindow

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "collectors" / "github_audit_log"
TENANT_DIR = FIXTURES / "tenant"
BROKEN_CHAIN_DIR = FIXTURES / "seeded" / "broken_chain"
WRONG_ORG_DIR = FIXTURES / "wrong_org"
# Within the 180-day window of the fixture extract time (2026-12-31T12:00:00Z,
# floor 2026-07-04T12:00:00Z).
PERIOD = TimeWindow(
    start=datetime(2026, 10, 15, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC)
)
ORG = "meridian-financial-fixtures"


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


def collect(transport=None, org=ORG, period=PERIOD):
    return collect_github_audit_log(
        transport or transport_for(TENANT_DIR),
        org=org,
        period=period,
        population_ref="pop-github-audit-log-events",
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
    assert pagination.pages_fetched == 2
    assert [link.cursor for link in pagination.cursor_chain] == [None, "cur-0002"]
    assert [link.next_cursor for link in pagination.cursor_chain] == ["cur-0002", None]
    assert pagination.cursor_chain[-1].next_cursor is None
    assert "7 events" in pagination.exhaustion_method


def test_seeded_broken_chain_fixture_is_detected():
    # page-001 claims next cursor cur-0002; no such page exists in the
    # seeded fixture — the collector must refuse, never return 1 event.
    with pytest.raises(ValueError, match="cursor chain broken"):
        collect(transport=transport_for(BROKEN_CHAIN_DIR))


def test_repeated_cursor_is_detected():
    def mutate(pages):
        pages["cur-0002"] = dict(pages["cur-0002"], after="cur-0002")  # cycle to self

    with pytest.raises(ValueError, match="does not terminate"):
        collect(transport=transport_for(TENANT_DIR, mutate))


def test_page_answering_the_wrong_cursor_is_detected():
    def mutate(pages):
        pages["cur-0002"] = dict(pages["cur-0002"], cursor="cur-9999")

    with pytest.raises(ValueError, match="requested"):
        collect(transport=transport_for(TENANT_DIR, mutate))


def test_wrong_org_page_is_detected():
    with pytest.raises(ValueError, match="org"):
        collect(transport=transport_for(WRONG_ORG_DIR))


def test_window_honesty_refuses_period_older_than_capability_window():
    # Extract time 2026-12-31T12:00:00Z minus 180 days = 2026-07-04T12:00:00Z;
    # a period asserted from March reaches beyond retained history and must
    # refuse (E204), never silently return a partial event history.
    stale_period = TimeWindow(
        start=datetime(2026, 3, 1, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC)
    )
    with pytest.raises(ValueError, match="E204"):
        collect(period=stale_period)


def test_period_start_on_the_window_floor_is_accepted():
    floor_period = TimeWindow(
        start=datetime(2026, 7, 4, 12, 0, 0, tzinfo=UTC),
        end=datetime(2026, 12, 31, tzinfo=UTC),
    )
    assert len(collect(period=floor_period).records) == 7


def test_all_events_are_collected_no_action_filter():
    # the registry population description is "org audit events incl.
    # member removal" — the whole stream is admitted, not just one action.
    records = collect().records
    assert len(records) == 7
    assert sum(1 for r in records if r.action == "org.remove_member") == 5
    assert any(r.action == "team.add_member" for r in records)


def test_null_user_row_is_surfaced_not_dropped():
    records = collect().records
    repo_create = [r for r in records if r.action == "repo.create"]
    assert len(repo_create) == 1
    # a null user (org-level action, no specific target account) survives
    # collection; the reconciler buckets this identity UNRESOLVABLE and
    # the verdict path ends UNKNOWN_POPULATION (D-7/D-U1), never dropped
    assert repo_create[0].user is None
    assert repo_create[0].actor == "it-admin"


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


def test_eqc_supports_timing():
    supported = collect().contract.supported_assertion_types
    assert "TIMING" in supported
    assert "EVENT" in supported


def test_contract_hash_is_the_canonical_self_hash():
    contract = collect().contract
    assert contract.contract_hash == canonical_contract_hash(contract)


def test_transport_must_return_bytes_or_none():
    with pytest.raises(TypeError, match="bytes"):
        collect(transport=lambda cursor: (TENANT_DIR / "page-001.json").read_text())
