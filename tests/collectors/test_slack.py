"""COL05 tests — Slack users.list: exhaustion, parse, EQC, seeded.

Acceptance (docs/HANDOFF.md §4 COL01–05): pagination exhausted, raw
responses hashed, EQC with all five property methods named, fixture
tenants only, and the seeded failing fixture
(``tests/fixtures/seeded/slack_truncated_cursor/``) MUST be detected —
no detection proof, no merge.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

import pytest

from aegis_sentinel.collectors import FixtureTransport, SlackUsersCollector
from aegis_sentinel.schema import AssertionType
from collectors.conftest import SEEDED_DIR

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


@pytest.fixture(scope="module")
def snapshot(tenant_transport, slack_plan, retrieved_at):
    return SlackUsersCollector(tenant_transport).collect(slack_plan, retrieved_at)


# ---- pagination exhaustion ----------------------------------------------


def test_pagination_exhausted_at_empty_cursor(snapshot) -> None:
    assert len(snapshot.pages) == 2
    assert snapshot.pages[0]["response_metadata"]["next_cursor"] != ""
    assert snapshot.pages[1]["response_metadata"]["next_cursor"] == ""
    assert snapshot.complete
    assert snapshot.incompleteness == ()


# ---- parse correctness ---------------------------------------------------


def test_users_parse_counts_and_deleted_flags(snapshot) -> None:
    users = SlackUsersCollector.users(snapshot)
    assert len(users) == 31
    deleted = [u for u in users if u.deleted]
    assert len(deleted) == 14
    bots = [u for u in users if u.is_bot]
    assert [b.name for b in bots] == ["mf-deploybot"]
    assert bots[0].email is None  # profile email gated by users:read.email


def test_legitimate_exception_retains_slack_access(snapshot) -> None:
    """CT-2044 (kai.moreno): terminated 2026-06-19 yet NOT deleted —
    covered by disposition DISP-2026-114 (contractor-to-advisor
    conversion; tests/fixtures/tenants/README.md). EVAL01 must resolve
    this to EXCEPTION, never PASS and never FAIL."""
    kai = next(
        u
        for u in SlackUsersCollector.users(snapshot)
        if u.email == "kai.moreno@meridianfinancial.example"
    )
    assert not kai.deleted


def test_other_terminated_workers_are_deleted(snapshot) -> None:
    users = {u.email: u for u in SlackUsersCollector.users(snapshot) if u.email}
    for email in (
        "avery.chen@meridianfinancial.example",
        "marcus.webb@meridianfinancial.example",
        "dana.whitfield@meridianfinancial.example",
        "devon.ellis@meridianfinancial.example",
    ):
        assert users[email].deleted, email


# ---- hashing + EQC -------------------------------------------------------


def test_pages_and_snapshot_hashed(snapshot) -> None:
    assert all(SHA256_RE.match(h) for h in snapshot.page_hashes)
    assert len(snapshot.page_hashes) == 2
    assert SHA256_RE.match(snapshot.snapshot_hash)
    assert snapshot.compute_snapshot_hash() == snapshot.snapshot_hash


def test_contract_names_all_five_property_methods(
    tenant_transport, slack_plan, retrieved_at
) -> None:
    contract = SlackUsersCollector(tenant_transport).contract(
        slack_plan, "meridian-financial", retrieved_at
    )
    assert contract.population.method == slack_plan.pagination.exhaustion_method
    assert "next_cursor" in contract.population.method
    assert slack_plan.entry_id in contract.provenance.method
    assert "SHA-256" in contract.integrity.method
    for key in slack_plan.join_keys:
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


def test_contract_hash_deterministic_across_retrieved_at(tenant_transport, slack_plan) -> None:
    collector = SlackUsersCollector(tenant_transport)
    one = collector.contract(
        slack_plan, "meridian-financial", datetime(2026, 7, 1, tzinfo=timezone.utc)
    )
    two = collector.contract(
        slack_plan, "meridian-financial", datetime(2026, 7, 2, tzinfo=timezone.utc)
    )
    assert one.contract_hash == two.contract_hash


# ---- re-collection determinism ------------------------------------------


def test_recollection_is_byte_identical(tenant_transport, slack_plan, retrieved_at) -> None:
    collector = SlackUsersCollector(tenant_transport)
    one = collector.collect(slack_plan, retrieved_at)
    two = collector.collect(slack_plan, retrieved_at)
    assert one.model_dump_json() == two.model_dump_json()
    assert one.snapshot_hash == two.snapshot_hash


# ---- seeded failing fixture ----------------------------------------------


def test_seeded_truncated_cursor_is_flagged(slack_plan, retrieved_at) -> None:
    """Detection proof: non-empty next_cursor but the next page is missing
    → the snapshot may NEVER read complete."""
    transport = FixtureTransport(SEEDED_DIR / "slack_truncated_cursor")
    snapshot = SlackUsersCollector(transport).collect(slack_plan, retrieved_at)
    assert len(snapshot.pages) == 1
    assert not snapshot.complete
    assert any("next_cursor non-empty" in reason for reason in snapshot.incompleteness)
