"""REC10 acceptance (docs/HANDOFF.md §4): the Surveyor executes one
ratified enumeration per entry and diffs observed-vs-documented,
emitting drift as findings — refuses a DRAFT entry (no ratified scope to
probe) and a wrong-tenant response, and never mutates the registry."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aegis_sentinel.capability import (
    CapabilityEntry,
    ObservedCapability,
    ProbeRefusal,
    run_probe,
)

REGISTRY_DIR = Path(__file__).resolve().parent.parent / "registry" / "capabilities"
TENANT = "meridian-financial-fixtures"


def _entry(entry_id: str) -> CapabilityEntry:
    return CapabilityEntry.model_validate_json((REGISTRY_DIR / f"{entry_id}.json").read_text())


def _response(**overrides) -> bytes:
    payload = {
        "tenant": TENANT,
        "extracted_at": "2026-12-31T12:00:00Z",
        "schema_attributes": ["eventType", "published", "actor", "target", "outcome"],
        "pagination_method": "cursor",
        "earliest_record_at": "2026-10-02T12:00:00Z",
    }
    payload.update(overrides)
    return json.dumps(payload).encode("utf-8")


def transport_returning(raw: bytes):
    return lambda entry: raw


def test_probe_is_deterministic():
    entry = _entry("okta.system_log")
    transport = transport_returning(_response())
    first = run_probe(entry, transport, tenant=TENANT)
    second = run_probe(entry, transport, tenant=TENANT)
    assert first == second


def test_probe_hashes_the_raw_response():
    import hashlib

    raw = _response()
    entry = _entry("okta.system_log")
    result = run_probe(entry, transport_returning(raw), tenant=TENANT)
    assert result.raw_sha256 == hashlib.sha256(raw).hexdigest()


def test_matching_response_yields_no_findings():
    entry = _entry("okta.system_log")
    result = run_probe(entry, transport_returning(_response()), tenant=TENANT)
    assert result.findings == ()


def test_refuses_a_draft_entry_no_ratified_scope():
    """okta.users is on-disk as DRAFT — the Surveyor may only execute
    ratified enumerations (HANDOFF §4 REC10)."""
    entry = _entry("okta.users")
    with pytest.raises(ProbeRefusal, match="ratified"):
        run_probe(entry, transport_returning(_response()), tenant=TENANT)


def test_refuses_a_wrong_tenant_response():
    entry = _entry("okta.system_log")
    raw = _response(tenant="some-other-tenant")
    with pytest.raises(ProbeRefusal, match="tenant"):
        run_probe(entry, transport_returning(raw), tenant=TENANT)


def test_temporal_drift_surfaces_the_documented_90_day_gap():
    """The on-disk okta.system_log entry names this exact gap in its own
    history_caveats: '90 days ... is corpus-asserted ... Surveyor
    verification of actual depth required.' A probe reaching only 45
    days back must report the drift, not silently accept it."""
    entry = _entry("okta.system_log")
    raw = _response(earliest_record_at="2026-11-16T12:00:00Z")  # 45 days before extract
    result = run_probe(entry, transport_returning(raw), tenant=TENANT)
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.kind == "temporal_drift"
    assert finding.documented == "90d"
    assert finding.observed == "45d"


def test_schema_drift_reports_missing_and_extra_attributes():
    entry = _entry("okta.system_log")
    raw = _response(schema_attributes=["eventType", "published", "actor", "outcome", "severity"])
    result = run_probe(entry, transport_returning(raw), tenant=TENANT)
    findings = {f.kind: f for f in result.findings}
    assert "schema_drift" in findings
    assert "target" in findings["schema_drift"].detail
    assert "severity" in findings["schema_drift"].detail


def test_pagination_drift_reports_the_mismatch():
    entry = _entry("gcp.service_accounts")  # documented pagination.method == "page"
    raw = _response(
        pagination_method="cursor",
        earliest_record_at=None,
        schema_attributes=["name", "email", "uniqueId", "disabled"],
    )
    result = run_probe(entry, transport_returning(raw), tenant=TENANT)
    findings = {f.kind: f for f in result.findings}
    assert findings["pagination_drift"].documented == "page"
    assert findings["pagination_drift"].observed == "cursor"


def test_state_only_entry_has_no_temporal_drift_even_with_no_earliest_record():
    entry = _entry("gcp.service_accounts")
    raw = _response(
        pagination_method="page",
        earliest_record_at=None,
        schema_attributes=["name", "email", "uniqueId", "disabled"],
    )
    result = run_probe(entry, transport_returning(raw), tenant=TENANT)
    assert result.findings == ()


def test_run_probe_never_mutates_the_entry():
    entry = _entry("okta.system_log")
    before = entry.model_copy(deep=True)
    run_probe(entry, transport_returning(_response()), tenant=TENANT)
    assert entry == before


def test_observed_capability_model_round_trips():
    observed = ObservedCapability.model_validate(json.loads(_response()))
    assert observed.tenant == TENANT
    assert observed.extracted_at == datetime(2026, 12, 31, 12, tzinfo=UTC)
