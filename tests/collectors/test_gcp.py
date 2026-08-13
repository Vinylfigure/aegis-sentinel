"""COL04 tests — GCP IAM bindings: exhaustion, parse, EQC, seeded.

Acceptance (docs/HANDOFF.md §4 COL01–05): pagination exhausted, raw
responses hashed, EQC with all five property methods named, fixture
tenants only, and the seeded failing fixture
(``tests/fixtures/seeded/gcp_missing_page_token_target/``) MUST be
detected — no detection proof, no merge.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

import pytest

from aegis_sentinel.collectors import FixtureTransport, GcpIamBindingsCollector
from aegis_sentinel.schema import AssertionType
from collectors.conftest import SEEDED_DIR

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

#: The break-glass poison's runtime shadow (tests/fixtures/tenants/README.md).
BREAKGLASS = "serviceAccount:breakglass-admin@example-prod.iam.gserviceaccount.com"


@pytest.fixture(scope="module")
def snapshot(tenant_transport, gcp_plan, retrieved_at):
    return GcpIamBindingsCollector(tenant_transport).collect(gcp_plan, retrieved_at)


# ---- pagination exhaustion ----------------------------------------------


def test_pagination_exhausted_when_next_page_token_omitted(snapshot) -> None:
    assert len(snapshot.pages) == 2
    assert "nextPageToken" in snapshot.pages[0]
    assert "nextPageToken" not in snapshot.pages[1]
    assert snapshot.complete
    assert snapshot.incompleteness == ()


# ---- parse correctness ---------------------------------------------------


def test_bindings_parse_counts(snapshot) -> None:
    bindings = GcpIamBindingsCollector.bindings(snapshot)
    assert len(bindings) == 5
    projects = {b.project for b in bindings}
    assert projects == {"projects/mf-prod-core", "projects/mf-prod-data", "projects/mf-staging"}


def test_breakglass_principal_holds_owner(snapshot) -> None:
    """The break-glass poison's runtime shadow: a roles/owner principal
    that joins to no HRIS or Okta identity anywhere (compile-time shape
    is E117 — tests/fixtures/mutations/breakglass-cloud-account/)."""
    owner = next(b for b in GcpIamBindingsCollector.bindings(snapshot) if b.role == "roles/owner")
    assert BREAKGLASS in owner.members
    assert owner.project == "projects/mf-prod-core"
    assert BREAKGLASS in GcpIamBindingsCollector.principals(snapshot)


def test_no_terminated_identity_holds_a_binding(snapshot) -> None:
    """Terminated workers' bindings were revoked; only active identities,
    groups, and service accounts remain."""
    principals = GcpIamBindingsCollector.principals(snapshot)
    terminated_locals = {"avery.chen", "marcus.webb", "dana.whitfield", "kai.moreno"}
    for principal in principals:
        local = principal.split(":", 1)[-1].split("@", 1)[0]
        assert local not in terminated_locals, principal


# ---- hashing + EQC -------------------------------------------------------


def test_pages_and_snapshot_hashed(snapshot) -> None:
    assert all(SHA256_RE.match(h) for h in snapshot.page_hashes)
    assert len(snapshot.page_hashes) == 2
    assert SHA256_RE.match(snapshot.snapshot_hash)
    assert snapshot.compute_snapshot_hash() == snapshot.snapshot_hash


def test_contract_names_all_five_property_methods(tenant_transport, gcp_plan, retrieved_at) -> None:
    contract = GcpIamBindingsCollector(tenant_transport).contract(
        gcp_plan, "meridian-financial", retrieved_at
    )
    assert contract.population.method == gcp_plan.pagination.exhaustion_method
    assert "nextPageToken" in contract.population.method
    assert gcp_plan.entry_id in contract.provenance.method
    assert "SHA-256" in contract.integrity.method
    for key in gcp_plan.join_keys:
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


def test_contract_hash_deterministic_across_retrieved_at(tenant_transport, gcp_plan) -> None:
    collector = GcpIamBindingsCollector(tenant_transport)
    one = collector.contract(
        gcp_plan, "meridian-financial", datetime(2026, 7, 1, tzinfo=timezone.utc)
    )
    two = collector.contract(
        gcp_plan, "meridian-financial", datetime(2026, 7, 2, tzinfo=timezone.utc)
    )
    assert one.contract_hash == two.contract_hash


# ---- re-collection determinism ------------------------------------------


def test_recollection_is_byte_identical(tenant_transport, gcp_plan, retrieved_at) -> None:
    collector = GcpIamBindingsCollector(tenant_transport)
    one = collector.collect(gcp_plan, retrieved_at)
    two = collector.collect(gcp_plan, retrieved_at)
    assert one.model_dump_json() == two.model_dump_json()
    assert one.snapshot_hash == two.snapshot_hash


# ---- seeded failing fixture ----------------------------------------------


def test_seeded_missing_page_token_target_is_flagged(gcp_plan, retrieved_at) -> None:
    """Detection proof: nextPageToken present but its target page missing
    → the snapshot may NEVER read complete."""
    transport = FixtureTransport(SEEDED_DIR / "gcp_missing_page_token_target")
    snapshot = GcpIamBindingsCollector(transport).collect(gcp_plan, retrieved_at)
    assert len(snapshot.pages) == 1
    assert not snapshot.complete
    assert any("nextPageToken present" in reason for reason in snapshot.incompleteness)
