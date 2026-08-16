"""COL05 acceptance: deterministic multi-page collection, raw-payload
hashing, startIndex/count exhaustion recorded with indices, EQC with all
five quality property methods named (provenance naming the DRAFT
capability status), refusal of the seeded totalResults-mismatch and
wrong-workspace fixtures, and LOCAL non-SSO plus inactive edge rows
surfaced with flags, never filtered."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aegis_sentinel.collectors.slack_scim_users import (
    canonical_contract_hash,
    collect_slack_scim_users,
)
from aegis_sentinel.schema import TimeWindow

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "collectors" / "slack_scim_users"
PERIOD = TimeWindow(start=datetime(2026, 7, 1, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC))
WORKSPACE = "T-MERIDIAN-FIX"


def page_transport(directory: Path):
    def transport(start_index: int) -> bytes:
        return (directory / f"page_{start_index}.json").read_bytes()

    return transport


def collect(transport=page_transport(FIXTURES), workspace=WORKSPACE):
    return collect_slack_scim_users(
        transport, workspace=workspace, period=PERIOD, population_ref="pop-workspace-users"
    )


def test_collection_is_deterministic():
    first, second = collect(), collect()
    assert first == second
    assert first.raw_sha256 == second.raw_sha256
    assert first.contract.contract_hash == second.contract.contract_hash


def test_raw_hashes_are_sha256_of_the_page_bytes():
    collection = collect()
    pages = [FIXTURES / f"page_{i}.json" for i in (1, 4, 7)]
    assert collection.page_sha256 == tuple(
        hashlib.sha256(p.read_bytes()).hexdigest() for p in pages
    )
    assert (
        collection.raw_sha256 == hashlib.sha256(b"".join(p.read_bytes() for p in pages)).hexdigest()
    )


def test_startindex_exhaustion_recorded_with_indices():
    pagination = collect().pagination
    assert pagination.method == "startIndex/count"
    assert pagination.exhausted is True
    assert pagination.pages_fetched == 3
    assert pagination.start_indices == (1, 4, 7)
    assert "totalResults=7" in pagination.exhaustion_method
    assert "[1, 4, 7]" in pagination.exhaustion_method


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


def test_eqc_provenance_names_the_draft_capability_status():
    assert "DRAFT" in collect().contract.quality.provenance.method


def test_contract_hash_is_the_canonical_self_hash():
    contract = collect().contract
    assert contract.contract_hash == canonical_contract_hash(contract)


def test_local_and_inactive_edge_rows_surface_with_flags():
    records = collect().records
    assert len(records) == 7  # nothing filtered
    by_id = {r.id: r for r in records}
    # LOCAL non-SSO account (no SAML identity marker) is kept and flagged
    local = by_id["U-2005"]
    assert local.local_account is True
    assert local.active is True
    assert local.email == "emory.blake@example.com"  # primary email wins
    # inactive user is kept and flagged, not filtered
    inactive = by_id["U-2003"]
    assert inactive.active is False
    assert inactive.local_account is False
    # everyone else is an active SSO-linked account
    assert all(not r.local_account for r in records if r.id != "U-2005")


def test_seeded_totalresults_mismatch_is_detected():
    with pytest.raises(ValueError, match="totalResults mismatch"):
        collect(transport=page_transport(FIXTURES / "seeded" / "mismatch"))


def test_seeded_wrong_workspace_is_refused():
    with pytest.raises(ValueError, match="workspace"):
        collect(transport=page_transport(FIXTURES / "seeded" / "wrong_workspace"))


def tampered(start_index_to_mutate, mutate):
    def transport(start_index: int) -> bytes:
        payload = json.loads((FIXTURES / f"page_{start_index}.json").read_text())
        if start_index == start_index_to_mutate:
            mutate(payload)
        return json.dumps(payload).encode("utf-8")

    return transport


def test_short_page_is_detected():
    transport = tampered(4, lambda p: p["Resources"].pop())  # still asserts itemsPerPage=3
    with pytest.raises(ValueError, match="itemsPerPage"):
        collect(transport=transport)


def test_totalresults_drift_between_pages_is_detected():
    transport = tampered(4, lambda p: p.update(totalResults=9))
    with pytest.raises(ValueError, match="drifted"):
        collect(transport=transport)


def test_transport_must_return_bytes():
    with pytest.raises(TypeError, match="bytes"):
        collect(transport=lambda start: (FIXTURES / f"page_{start}.json").read_text())
