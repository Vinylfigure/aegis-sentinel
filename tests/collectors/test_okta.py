"""COL02 tests — Okta users + System Log: exhaustion, parse, EQC, seeded.

Acceptance (docs/HANDOFF.md §4 COL01–05): pagination exhausted, raw
responses hashed, EQC with all five property methods named, fixture
tenants only, and the seeded failing fixture
(``tests/fixtures/seeded/okta_truncated_users/``) MUST be detected —
no detection proof, no merge.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

import pytest

from aegis_sentinel.collectors import (
    FixtureTransport,
    HrisTerminationsCollector,
    OktaSystemLogCollector,
    OktaUsersCollector,
)
from aegis_sentinel.collectors.okta import EVENT_DEACTIVATE, STATUS_DEPROVISIONED
from aegis_sentinel.evaluate.business_days import business_days_between
from aegis_sentinel.schema import AssertionType
from collectors.conftest import SEEDED_DIR
from conftest import TENANTS_DIR

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

#: The contractor-absent-from-HRIS poison (tests/fixtures/tenants/README.md).
POISON_CONTRACTOR = "ctr.blake.morgan@example-vendor.com"


@pytest.fixture(scope="module")
def users_snapshot(okta_transport, okta_users_plan, retrieved_at):
    return OktaUsersCollector(okta_transport).collect(okta_users_plan, retrieved_at)


@pytest.fixture(scope="module")
def log_snapshot(okta_transport, okta_log_plan, retrieved_at):
    return OktaSystemLogCollector(okta_transport).collect(okta_log_plan, retrieved_at)


@pytest.fixture(scope="module")
def hris_emails(feed_plan, retrieved_at) -> frozenset[str]:
    snapshot = HrisTerminationsCollector(FixtureTransport(TENANTS_DIR)).collect(
        feed_plan, retrieved_at
    )
    return frozenset(e.email for e in HrisTerminationsCollector.events(snapshot))


# ---- pagination exhaustion ----------------------------------------------


def test_users_pagination_exhausted_at_absent_cursor(users_snapshot) -> None:
    """Both user pages consumed; page 2 carries no Link rel="next"."""
    assert len(users_snapshot.pages) == 2
    assert users_snapshot.complete
    assert users_snapshot.incompleteness == ()


def test_log_pagination_exhausted_at_zero_event_page(log_snapshot) -> None:
    """All three log pages consumed; the zero-event page 3 is the signal."""
    assert len(log_snapshot.pages) == 3
    assert log_snapshot.pages[-1]["items"] == []
    assert log_snapshot.complete


# ---- parse correctness ---------------------------------------------------


def test_users_parse_counts_and_statuses(users_snapshot) -> None:
    users = OktaUsersCollector.users(users_snapshot)
    assert len(users) == 31
    deprovisioned = [u for u in users if u.status == STATUS_DEPROVISIONED]
    assert len(deprovisioned) == 14
    # deactivation timestamps present exactly on the deprovisioned set
    assert all(u.deactivated_at is not None for u in deprovisioned)
    assert all(u.deactivated_at is None for u in users if u.status == "ACTIVE")


def test_poison_contractor_is_active_and_absent_from_hris(users_snapshot, hris_emails) -> None:
    """Negative-space poison: an ACTIVE Okta contractor the HRIS never lists."""
    users = OktaUsersCollector.users(users_snapshot)
    blake = next(u for u in users if u.email == POISON_CONTRACTOR)
    assert blake.status == "ACTIVE"
    assert POISON_CONTRACTOR not in hris_emails


def test_failed_identity_join_email_is_not_the_hris_email(users_snapshot, hris_emails) -> None:
    """E-1033: HRIS says dana.whitfield@…, Okta only knows dana.kowalski@…."""
    emails = {u.email for u in OktaUsersCollector.users(users_snapshot)}
    assert "dana.kowalski@meridianfinancial.example" in emails
    assert "dana.whitfield@meridianfinancial.example" not in emails
    assert "dana.whitfield@meridianfinancial.example" in hris_emails


def test_legitimate_exception_contractor_still_active(users_snapshot) -> None:
    """CT-2044 (kai.moreno) stays ACTIVE under disposition DISP-2026-114."""
    kai = next(
        u
        for u in OktaUsersCollector.users(users_snapshot)
        if u.email == "kai.moreno@meridianfinancial.example"
    )
    assert kai.status == "ACTIVE"


def test_log_parse_deactivations(log_snapshot) -> None:
    events = OktaSystemLogCollector.events(log_snapshot)
    assert len(events) == 14
    assert all(e.event_type == EVENT_DEACTIVATE for e in events)
    assert all(e.outcome == "SUCCESS" for e in events)
    deactivations = OktaSystemLogCollector.deactivations(log_snapshot)
    assert deactivations == events


def test_delayed_revocation_event_is_nine_business_days_late(log_snapshot) -> None:
    """E-1027 (marcus.webb): terminated 2026-02-13, deactivated 2026-02-26 —
    9 business days, past the 5-business-day window (delayed-revocation
    poison; EVAL01 will FAIL the TIMING assertion)."""
    marcus = next(
        e
        for e in OktaSystemLogCollector.events(log_snapshot)
        if e.target_alternate_id == "marcus.webb@meridianfinancial.example"
    )
    published_day = marcus.published.date()
    assert published_day == date(2026, 2, 26)
    assert business_days_between(date(2026, 2, 13), published_day) == 9


def test_no_deactivation_event_for_the_exception_or_the_poison(log_snapshot) -> None:
    targets = {e.target_alternate_id for e in OktaSystemLogCollector.events(log_snapshot)}
    assert "kai.moreno@meridianfinancial.example" not in targets  # DISP-2026-114
    assert POISON_CONTRACTOR not in targets  # never deprovisioned: not in HRIS


# ---- hashing + EQC -------------------------------------------------------


def test_pages_and_snapshots_hashed(users_snapshot, log_snapshot) -> None:
    for snapshot in (users_snapshot, log_snapshot):
        assert all(SHA256_RE.match(h) for h in snapshot.page_hashes)
        assert len(snapshot.page_hashes) == len(snapshot.pages)
        assert SHA256_RE.match(snapshot.snapshot_hash)
        assert snapshot.compute_snapshot_hash() == snapshot.snapshot_hash


def test_users_contract_names_all_five_property_methods(
    okta_transport, okta_users_plan, retrieved_at
) -> None:
    contract = OktaUsersCollector(okta_transport).contract(
        okta_users_plan, "meridian-financial", retrieved_at
    )
    assert contract.population.method == okta_users_plan.pagination.exhaustion_method
    assert okta_users_plan.entry_id in contract.provenance.method
    assert "SHA-256" in contract.integrity.method
    for key in okta_users_plan.join_keys:
        assert key in contract.semantics.method
    assert "state-only" in contract.temporal_validity.method
    assert contract.supported_assertion_types == frozenset(
        {
            AssertionType.STATE,
            AssertionType.EXISTENCE,
            AssertionType.NON_EXISTENCE,
            AssertionType.AGGREGATE,
        }
    )


def test_log_contract_supports_the_event_family(
    okta_transport, okta_log_plan, retrieved_at
) -> None:
    contract = OktaSystemLogCollector(okta_transport).contract(
        okta_log_plan, "meridian-financial", retrieved_at
    )
    assert "event-history(window=90d)" in contract.temporal_validity.method
    assert contract.supported_assertion_types == frozenset(
        {
            AssertionType.TIMING,
            AssertionType.SEQUENCE,
            AssertionType.EVENT,
            AssertionType.AGGREGATE,
        }
    )


def test_contract_hash_deterministic_across_retrieved_at(okta_transport, okta_users_plan) -> None:
    collector = OktaUsersCollector(okta_transport)
    one = collector.contract(
        okta_users_plan, "meridian-financial", datetime(2026, 7, 1, tzinfo=timezone.utc)
    )
    two = collector.contract(
        okta_users_plan, "meridian-financial", datetime(2026, 7, 2, tzinfo=timezone.utc)
    )
    assert one.contract_hash == two.contract_hash


# ---- re-collection determinism ------------------------------------------


def test_recollection_is_byte_identical(okta_transport, okta_users_plan, retrieved_at) -> None:
    collector = OktaUsersCollector(okta_transport)
    one = collector.collect(okta_users_plan, retrieved_at)
    two = collector.collect(okta_users_plan, retrieved_at)
    assert one.model_dump_json() == two.model_dump_json()
    assert one.snapshot_hash == two.snapshot_hash


# ---- seeded failing fixture ----------------------------------------------


def test_seeded_truncated_users_is_flagged_incomplete(
    okta_surfaces, okta_users_plan, retrieved_at
) -> None:
    """Detection proof: cursor present but the page is missing → the
    snapshot may NEVER read complete."""
    transport = FixtureTransport(SEEDED_DIR / "okta_truncated_users", surfaces=okta_surfaces)
    snapshot = OktaUsersCollector(transport).collect(okta_users_plan, retrieved_at)
    assert len(snapshot.pages) == 1
    assert not snapshot.complete
    assert any("never retrieved" in reason for reason in snapshot.incompleteness)
