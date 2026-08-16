"""COL04 acceptance: deterministic multi-page collection, per-page +
chained raw hashing, pageToken exhaustion recorded with the token chain,
seeded broken-token-chain and wrong-project fixtures DETECTED (refused,
no partial pass), break-glass and disabled rows surfaced with their
disabled flag, and an EQC with all five quality property methods named."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aegis_sentinel.collectors.gcp_service_accounts import (
    chain_hash,
    collect_gcp_service_accounts,
)
from aegis_sentinel.collectors.hris import canonical_contract_hash
from aegis_sentinel.schema import TimeWindow
from aegis_sentinel.schema.enums import AssertionType

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "collectors" / "gcp_service_accounts"
SEEDED = FIXTURES / "seeded"
PERIOD = TimeWindow(start=datetime(2026, 7, 1, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC))
PROJECT = "meridian-prod-fixtures"


def page_map(fixture_dir: Path) -> dict[str | None, bytes]:
    """Chain fixture pages the way the API serves them: page N is keyed
    by page N-1's nextPageToken (None keys the first page). A token no
    page answers to — the seeded broken chain — simply has no entry."""
    mapping: dict[str | None, bytes] = {}
    token: str | None = None
    for path in sorted(fixture_dir.glob("page-*.json")):
        raw = path.read_bytes()
        mapping[token] = raw
        token = json.loads(raw).get("nextPageToken")
    return mapping


def transport_for(fixture_dir: Path):
    mapping = page_map(fixture_dir)
    return lambda token: mapping[token]  # KeyError = token points nowhere


def collect(transport=None, project=PROJECT):
    return collect_gcp_service_accounts(
        transport if transport is not None else transport_for(FIXTURES),
        project=project,
        period=PERIOD,
        population_ref="pop-gcp-service-accounts",
    )


def test_collection_is_deterministic():
    first, second = collect(), collect()
    assert first == second
    assert first.raw_sha256 == second.raw_sha256
    assert first.contract.contract_hash == second.contract.contract_hash


def test_raw_hash_chains_the_per_page_sha256s_in_fetch_order():
    collection = collect()
    expected_pages = tuple(
        hashlib.sha256((FIXTURES / f"page-{n}.json").read_bytes()).hexdigest() for n in (1, 2, 3)
    )
    assert collection.page_sha256s == expected_pages
    assert collection.raw_sha256 == chain_hash(expected_pages)
    assert (
        collection.raw_sha256
        == hashlib.sha256("\n".join(expected_pages).encode("ascii")).hexdigest()
    )


def test_token_chain_exhaustion_is_recorded():
    pagination = collect().pagination
    assert pagination.method == "page"
    assert pagination.exhausted is True
    assert pagination.pages_fetched == 3
    assert pagination.token_chain == ("sa-page-2", "sa-page-3")
    assert "until nextPageToken absent" in pagination.exhaustion_method
    assert "3 pages" in pagination.exhaustion_method
    assert "sa-page-2 -> sa-page-3" in pagination.exhaustion_method


def test_seeded_broken_token_chain_is_detected():
    transport = transport_for(SEEDED / "broken_token_chain")
    with pytest.raises(ValueError, match="token chain broken.*sa-page-ghost.*points nowhere"):
        collect(transport=transport)


def test_seeded_wrong_project_fixture_is_refused():
    transport = transport_for(SEEDED / "wrong_project")
    with pytest.raises(ValueError, match="not under engagement project"):
        collect(transport=transport)


def test_wrong_engagement_project_is_refused_against_the_good_fixture():
    with pytest.raises(ValueError, match="not under engagement project"):
        collect(project="some-other-project")


def test_token_chain_cycle_is_detected():
    mapping = page_map(FIXTURES)
    cycling = json.loads(mapping["sa-page-3"])
    cycling["nextPageToken"] = "sa-page-2"
    mapping["sa-page-3"] = json.dumps(cycling).encode("utf-8")
    with pytest.raises(ValueError, match="token chain cycle"):
        collect(transport=lambda token: mapping[token])


def test_break_glass_and_disabled_rows_are_surfaced_never_filtered():
    records = collect().records
    assert len(records) == 8  # every fixture row across all three pages
    breakglass = [r for r in records if r.email.startswith("breakglass-")]
    assert [r.disabled for r in breakglass] == [False]  # enabled, and flag captured
    assert breakglass[0].name.rpartition("/")[2].startswith("breakglass-")
    disabled = [r for r in records if r.disabled]
    assert [r.email.split("@")[0] for r in disabled] == ["legacy-etl"]
    # absence of the proto3-omitted flag means enabled, still captured as a value
    assert all(r.disabled in (True, False) for r in records)


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


def test_contract_is_state_only():
    contract = collect().contract
    assert contract.supports(AssertionType.STATE)
    assert contract.supports(AssertionType.EXISTENCE)
    assert not contract.supports(AssertionType.EVENT)
    assert not contract.supports(AssertionType.TIMING)


def test_contract_hash_is_the_canonical_self_hash():
    contract = collect().contract
    assert contract.contract_hash == canonical_contract_hash(contract)


def test_transport_must_return_bytes():
    with pytest.raises(TypeError, match="bytes"):
        collect(transport=lambda token: (FIXTURES / "page-1.json").read_text())
