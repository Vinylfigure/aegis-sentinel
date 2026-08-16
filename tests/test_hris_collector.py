"""COL01 acceptance: deterministic collection, raw-payload hashing,
pagination exhaustion recorded even for a single-page extract, EQC with
all five quality property methods named, and detection of truncated or
wrong-tenant extracts."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aegis_sentinel.collectors.hris import (
    canonical_contract_hash,
    collect_hris_terminations,
)
from aegis_sentinel.schema import TimeWindow

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "collectors" / "hris_terminations.json"
PERIOD = TimeWindow(start=datetime(2026, 7, 1, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC))
TENANT = "meridian-financial-fixtures"


def collect(transport=FIXTURE.read_bytes, tenant=TENANT):
    return collect_hris_terminations(
        transport, tenant=tenant, period=PERIOD, population_ref="pop-termination-events"
    )


def test_collection_is_deterministic():
    first, second = collect(), collect()
    assert first == second
    assert first.raw_sha256 == second.raw_sha256
    assert first.contract.contract_hash == second.contract.contract_hash


def test_raw_payload_hash_is_sha256_of_the_bytes():
    assert collect().raw_sha256 == hashlib.sha256(FIXTURE.read_bytes()).hexdigest()


def test_pagination_exhaustion_recorded_even_for_single_page():
    pagination = collect().pagination
    assert pagination.exhausted is True
    assert pagination.pages_fetched == 1
    assert "row_count=15" in pagination.exhaustion_method
    assert "page 1/1" in pagination.exhaustion_method


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


def test_edge_rows_survive_typed_parsing():
    records = collect().records
    assert len(records) == 15
    # missing email stays None (reconciler's problem, not the collector's)
    assert [r.worker_id for r in records if r.email is None] == ["W-1012"]
    # contractor row keeps its worker_type
    assert any(r.worker_type == "contractor" for r in records)
    # the rehire's second termination event is kept, not deduplicated
    assert sum(1 for r in records if r.worker_id == "W-1003") == 2
    # raw email casing/whitespace is preserved at collection
    assert any(r.email == "  Blair.QUINN@Example.COM " for r in records)


def tampered(mutate):
    payload = json.loads(FIXTURE.read_text())
    mutate(payload)
    return lambda: json.dumps(payload).encode("utf-8")


def test_truncated_extract_is_detected():
    transport = tampered(lambda p: p["rows"].pop())  # metadata still says 15
    with pytest.raises(ValueError, match="row_count"):
        collect(transport=transport)


def test_unexhausted_pagination_is_detected():
    transport = tampered(lambda p: p["report_metadata"].update(total_pages=2))
    with pytest.raises(ValueError, match="pagination not exhausted"):
        collect(transport=transport)


def test_wrong_tenant_extract_is_detected():
    with pytest.raises(ValueError, match="tenant"):
        collect(tenant="some-other-tenant")


def test_transport_must_return_bytes():
    with pytest.raises(TypeError, match="bytes"):
        collect(transport=FIXTURE.read_text)
