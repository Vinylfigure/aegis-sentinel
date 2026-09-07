"""COL06 acceptance: deterministic collection, per-page raw hashing,
cursor-chain exhaustion recorded page by page, refusal on a broken or
cyclic chain (seeded fixture detected), wrong-account-token refusal, a
page's own claimed row count exceeding its actual rows (truncation),
null join-key rows surfaced not dropped, and an EQC with all five
quality property methods named."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aegis_sentinel.collectors.merge_hris import (
    canonical_contract_hash,
    collect_merge_employees,
)
from aegis_sentinel.schema import TimeWindow

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "collectors" / "merge_hris"
TENANT_DIR = FIXTURES / "tenant"
BROKEN_CHAIN_DIR = FIXTURES / "seeded" / "broken_chain"
TRUNCATED_DIR = FIXTURES / "seeded" / "truncated"
WRONG_ACCOUNT_TOKEN_DIR = FIXTURES / "wrong_account_token"
PERIOD = TimeWindow(
    start=datetime(2026, 10, 15, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC)
)
ACCOUNT_TOKEN = "acme-fixtures-account-token"


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


def collect(transport=None, account_token=ACCOUNT_TOKEN, period=PERIOD):
    return collect_merge_employees(
        transport or transport_for(TENANT_DIR),
        account_token=account_token,
        period=period,
        population_ref="pop-merge-hris-employees",
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
    assert "13 employees" in pagination.exhaustion_method


def test_seeded_broken_chain_fixture_is_detected():
    # page-001 claims next cursor cur-0002; no such page exists in the
    # seeded fixture — the collector must refuse, never return 5 rows.
    with pytest.raises(ValueError, match="cursor chain broken"):
        collect(transport=transport_for(BROKEN_CHAIN_DIR))


def test_repeated_cursor_is_detected():
    def mutate(pages):
        pages["cur-0003"] = dict(pages["cur-0003"], next="cur-0002")  # cycle back

    with pytest.raises(ValueError, match="does not terminate"):
        collect(transport=transport_for(TENANT_DIR, mutate))


def test_page_answering_the_wrong_cursor_is_detected():
    def mutate(pages):
        pages["cur-0002"] = dict(pages["cur-0002"], cursor="cur-9999")

    with pytest.raises(ValueError, match="requested"):
        collect(transport=transport_for(TENANT_DIR, mutate))


def test_wrong_account_token_page_is_detected():
    with pytest.raises(ValueError, match="account_token"):
        collect(transport=transport_for(WRONG_ACCOUNT_TOKEN_DIR))


def test_truncated_page_is_detected():
    # page-001 claims count=6 but carries only 5 rows — refused as a
    # truncated page, never silently accepted as 5 employees.
    with pytest.raises(ValueError, match="truncated page"):
        collect(transport=transport_for(TRUNCATED_DIR))


def test_all_employees_are_collected():
    records = collect().records
    assert len(records) == 13
    assert sum(1 for r in records if r.employment_status == "terminated") == 7
    assert sum(1 for r in records if r.employment_status == "active") == 6


def test_null_join_key_rows_are_surfaced_not_dropped():
    records = collect().records
    no_employee_id = [r for r in records if r.id == "emp-0004"]
    assert len(no_employee_id) == 1
    # a null employee_id survives collection; the reconciler buckets this
    # identity UNRESOLVABLE and the verdict path ends UNKNOWN_POPULATION
    # (D-7/D-U1), never a silently dropped row
    assert no_employee_id[0].employee_id is None
    assert no_employee_id[0].email == "omar.saleh@example.com"

    no_email = [r for r in records if r.id == "emp-0007"]
    assert len(no_email) == 1
    assert no_email[0].email is None
    assert no_email[0].employee_id == "E-1007"


def test_active_employees_have_no_termination_date():
    records = collect().records
    priya = [r for r in records if r.id == "emp-0001"][0]
    assert priya.employment_status == "active"
    assert priya.termination_date is None


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


def test_eqc_supports_state_not_timing():
    supported = collect().contract.supported_assertion_types
    assert "STATE" in supported
    assert "TIMING" not in supported


def test_contract_hash_is_the_canonical_self_hash():
    contract = collect().contract
    assert contract.contract_hash == canonical_contract_hash(contract)


def test_transport_must_return_bytes_or_none():
    with pytest.raises(TypeError, match="bytes"):
        collect(transport=lambda cursor: (TENANT_DIR / "page-001.json").read_text())
