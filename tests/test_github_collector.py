"""COL03 acceptance: deterministic collection, raw-payload hashing,
Link-chain (link_next) exhaustion recorded with page count, seeded
truncated-page and wrong-org fixtures DETECTED and refused, dormant
local account surfaced (not filtered), and an EQC with all five quality
property methods named — STATE-only, so no TIMING support."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aegis_sentinel.collectors.github_members import collect_github_members
from aegis_sentinel.collectors.hris import canonical_contract_hash
from aegis_sentinel.schema import TimeWindow
from aegis_sentinel.schema.enums import AssertionType

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "collectors" / "github_members"
SEEDED = FIXTURES / "seeded"
PERIOD = TimeWindow(start=datetime(2026, 7, 1, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC))
ORG = "meridian-financial-fixtures"


def fixture_transport(overrides: dict[str, Path] | None = None):
    """Page-keyed transport over the fixture tenant; seeded fixtures are
    swapped in per page key to simulate a tampered chain."""
    overrides = overrides or {}

    def transport(page_key: str) -> bytes:
        return (overrides.get(page_key) or FIXTURES / f"{page_key}.json").read_bytes()

    return transport


def collect(transport=None, org=ORG, first_page="page_1"):
    return collect_github_members(
        transport or fixture_transport(),
        org=org,
        period=PERIOD,
        population_ref="pop-github-org-members",
        first_page=first_page,
    )


def test_collection_is_deterministic():
    first, second = collect(), collect()
    assert first == second
    assert first.raw_sha256 == second.raw_sha256
    assert first.contract.contract_hash == second.contract.contract_hash


def test_raw_hashes_are_sha256_of_the_page_bytes():
    collection = collect()
    pages = [(FIXTURES / f"page_{n}.json").read_bytes() for n in (1, 2, 3)]
    assert collection.page_sha256s == tuple(hashlib.sha256(p).hexdigest() for p in pages)
    assert collection.raw_sha256 == hashlib.sha256(b"".join(pages)).hexdigest()


def test_link_chain_exhaustion_is_recorded():
    pagination = collect().pagination
    assert pagination.method == "page"
    assert pagination.exhausted is True
    assert pagination.pages_fetched == 3
    assert "link_next" in pagination.exhaustion_method
    assert "3 pages" in pagination.exhaustion_method
    assert "8 rows" in pagination.exhaustion_method


def test_seeded_truncated_page_is_detected():
    # page 2 claims per_page=3 but returns 2 rows while link_next says
    # more pages follow — a mid-chain truncation must refuse, not pass.
    transport = fixture_transport({"page_2": SEEDED / "truncated_page_2.json"})
    with pytest.raises(ValueError, match="truncated page"):
        collect(transport=transport)


def test_seeded_wrong_org_page_is_refused():
    transport = fixture_transport({"page_1": SEEDED / "wrong_org_page_1.json"})
    with pytest.raises(ValueError, match="org"):
        collect(transport=transport)


def test_wrong_engagement_org_is_refused_against_tenant_fixture():
    with pytest.raises(ValueError, match="engagement org"):
        collect(org="some-other-org")


def test_link_next_cycle_is_refused():
    # a chain that points back at an already-fetched page never loops
    # forever headless — it refuses.
    transport = fixture_transport({"page_3": FIXTURES / "page_1.json"})
    with pytest.raises(ValueError, match="cycle|sequence"):
        collect(transport=transport)


def test_dormant_local_account_is_surfaced_not_filtered():
    records = collect().records
    dormant = [r for r in records if r.sso_identity is None and r.type == "User"]
    assert [r.login for r in dormant] == ["gh-legacy-onboarder"]
    assert dormant[0].site_admin is False
    # it rode in on the last page and is still the last record — the
    # collector reorders and drops nothing.
    assert records[-1].login == "gh-legacy-onboarder"


def test_machine_account_is_surfaced_not_filtered():
    records = collect().records
    assert any(r.login == "meridian-deploy[bot]" and r.type == "Bot" for r in records)
    assert len(records) == 8


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


def test_state_only_source_supports_no_timing():
    # registry github.members: temporal.kind state-only — no TIMING by
    # itself; STATE/EXISTENCE/NON-EXISTENCE only.
    supported = collect().contract.supported_assertion_types
    assert AssertionType.TIMING not in supported
    assert AssertionType.STATE in supported


def test_transport_must_return_bytes():
    with pytest.raises(TypeError, match="bytes"):
        collect(transport=lambda key: (FIXTURES / f"{key}.json").read_text())
