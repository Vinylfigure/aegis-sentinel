"""COL03 tests — GitHub org roster + audit log: exhaustion, parse, EQC, seeded.

Acceptance (docs/HANDOFF.md §4 COL01–05): pagination exhausted on BOTH
roster endpoints, raw responses hashed, EQC with all five property
methods named, fixture tenants only, and the seeded failing fixture
(``tests/fixtures/seeded/github_short_page/``) MUST be detected —
no detection proof, no merge.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

import pytest

from aegis_sentinel.collectors import (
    FixtureTransport,
    GithubAuditLogCollector,
    GithubOrgMembersCollector,
)
from aegis_sentinel.collectors.github import ACTION_REMOVE_MEMBER
from aegis_sentinel.schema import AssertionType
from collectors.conftest import SEEDED_DIR

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

#: The dormant-local-account poison (tests/fixtures/tenants/README.md).
DORMANT_LOCAL = "bm-legacy-bot"
#: The contractor-absent-from-HRIS poison's GitHub identity.
POISON_CONTRACTOR_LOGIN = "blake-morgan-vendor"


@pytest.fixture(scope="module")
def roster_snapshot(github_transport, github_members_plan, retrieved_at):
    return GithubOrgMembersCollector(github_transport).collect(github_members_plan, retrieved_at)


@pytest.fixture(scope="module")
def audit_snapshot(github_transport, github_audit_plan, retrieved_at):
    return GithubAuditLogCollector(github_transport).collect(github_audit_plan, retrieved_at)


# ---- pagination exhaustion ----------------------------------------------


def test_roster_exhausts_both_endpoints(roster_snapshot) -> None:
    """Members pages 1–2 plus the outside-collaborators page all consumed."""
    assert len(roster_snapshot.pages) == 3
    assert roster_snapshot.complete
    endpoints = {page["endpoint"].rsplit("/", 1)[-1] for page in roster_snapshot.pages}
    assert endpoints == {"members", "outside_collaborators"}


def test_audit_pagination_exhausted_at_absent_cursor(audit_snapshot) -> None:
    assert len(audit_snapshot.pages) == 2
    assert audit_snapshot.complete


# ---- parse correctness ---------------------------------------------------


def test_roster_parse_counts(roster_snapshot) -> None:
    accounts = GithubOrgMembersCollector.accounts(roster_snapshot)
    assert len(accounts) == 19
    members = [a for a in accounts if a.membership == "member"]
    outside = [a for a in accounts if a.membership == "outside_collaborator"]
    assert len(members) == 18
    assert [a.login for a in outside] == ["osprey-design-ext"]


def test_dormant_local_account_poison_present(roster_snapshot) -> None:
    """The LOCAL (non-SSO) dormant member: no SAML identity, old last_active."""
    dormant = next(
        a for a in GithubOrgMembersCollector.accounts(roster_snapshot) if a.login == DORMANT_LOCAL
    )
    assert dormant.is_local
    assert dormant.saml_name_id is None
    assert dormant.membership == "member"
    assert dormant.last_active == date(2025, 11, 2)


def test_poison_contractor_member_present(roster_snapshot) -> None:
    """The HRIS-absent contractor is an SSO-active org member."""
    blake = next(
        a
        for a in GithubOrgMembersCollector.accounts(roster_snapshot)
        if a.login == POISON_CONTRACTOR_LOGIN
    )
    assert blake.saml_name_id == "ctr.blake.morgan@example-vendor.com"
    assert blake.membership == "member"


def test_terminated_members_are_gone_but_kai_remains(roster_snapshot) -> None:
    """Deprovisioned handles are out of the roster; CT-2044 (kai-moreno)
    remains under disposition DISP-2026-114 (legitimate exception)."""
    logins = {a.login for a in GithubOrgMembersCollector.accounts(roster_snapshot)}
    assert "kai-moreno" in logins
    assert {"avery-chen", "marcus-webb", "dana-kowalski"}.isdisjoint(logins)


def test_audit_parse_removal_events(audit_snapshot) -> None:
    events = GithubAuditLogCollector.events(audit_snapshot)
    assert len(events) == 14
    assert all(e.action == ACTION_REMOVE_MEMBER for e in events)
    assert all(e.org == "meridian-financial" for e in events)
    assert GithubAuditLogCollector.removals(audit_snapshot) == events
    removed = {e.user for e in events}
    assert "marcus-webb" in removed  # late (delayed-revocation poison), but removed
    assert "kai-moreno" not in removed  # exception: never removed
    assert POISON_CONTRACTOR_LOGIN not in removed  # not in HRIS: never deprovisioned


# ---- hashing + EQC -------------------------------------------------------


def test_pages_and_snapshots_hashed(roster_snapshot, audit_snapshot) -> None:
    for snapshot in (roster_snapshot, audit_snapshot):
        assert all(SHA256_RE.match(h) for h in snapshot.page_hashes)
        assert len(snapshot.page_hashes) == len(snapshot.pages)
        assert SHA256_RE.match(snapshot.snapshot_hash)
        assert snapshot.compute_snapshot_hash() == snapshot.snapshot_hash


def test_roster_contract_names_all_five_property_methods(
    github_transport, github_members_plan, retrieved_at
) -> None:
    contract = GithubOrgMembersCollector(github_transport).contract(
        github_members_plan, "meridian-financial", retrieved_at
    )
    assert contract.population.method == github_members_plan.pagination.exhaustion_method
    assert "outside_collaborators" in contract.population.method
    assert github_members_plan.entry_id in contract.provenance.method
    assert "SHA-256" in contract.integrity.method
    for key in github_members_plan.join_keys:
        assert key in contract.semantics.method
    assert contract.supported_assertion_types == frozenset(
        {
            AssertionType.STATE,
            AssertionType.EXISTENCE,
            AssertionType.NON_EXISTENCE,
            AssertionType.AGGREGATE,
        }
    )


def test_audit_contract_supports_the_event_family(
    github_transport, github_audit_plan, retrieved_at
) -> None:
    contract = GithubAuditLogCollector(github_transport).contract(
        github_audit_plan, "meridian-financial", retrieved_at
    )
    assert "event-history(window=180d)" in contract.temporal_validity.method
    assert AssertionType.TIMING in contract.supported_assertion_types
    assert AssertionType.STATE not in contract.supported_assertion_types


def test_contract_hash_deterministic_across_retrieved_at(
    github_transport, github_members_plan
) -> None:
    collector = GithubOrgMembersCollector(github_transport)
    one = collector.contract(
        github_members_plan, "meridian-financial", datetime(2026, 7, 1, tzinfo=timezone.utc)
    )
    two = collector.contract(
        github_members_plan, "meridian-financial", datetime(2026, 7, 2, tzinfo=timezone.utc)
    )
    assert one.contract_hash == two.contract_hash


# ---- re-collection determinism ------------------------------------------


def test_recollection_is_byte_identical(
    github_transport, github_members_plan, retrieved_at
) -> None:
    collector = GithubOrgMembersCollector(github_transport)
    one = collector.collect(github_members_plan, retrieved_at)
    two = collector.collect(github_members_plan, retrieved_at)
    assert one.model_dump_json() == two.model_dump_json()
    assert one.snapshot_hash == two.snapshot_hash


# ---- seeded failing fixture ----------------------------------------------


def test_seeded_short_page_is_flagged_incomplete(
    github_surfaces, github_members_plan, retrieved_at
) -> None:
    """Detection proof: Link promised a next page; a 404-shaped body
    arrived instead → the snapshot may NEVER read complete."""
    transport = FixtureTransport(SEEDED_DIR / "github_short_page", surfaces=github_surfaces)
    snapshot = GithubOrgMembersCollector(transport).collect(github_members_plan, retrieved_at)
    assert not snapshot.complete
    joined = "\n".join(snapshot.incompleteness)
    assert "404" in joined
    assert "outside_collaborators" in joined  # the second endpoint never arrived either
