"""CapabilityEntry validation: closed, const-pinned, iff-constrained.

Invalid fixtures MUST be rejected — never "fix" a failing test here by
loosening the schema (docs/invariants.md).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from aegis_sentinel.capability import (
    AccessMode,
    CapabilityEntry,
    Pagination,
    PaginationMethod,
    PopulationAttributes,
    PopulationYield,
    Provenance,
    SourceCitation,
    TemporalShape,
    TemporalShapeKind,
)
from aegis_sentinel.schema import PopulationType, canonical_json, sha256_canonical

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "capability"

VALID = sorted((FIXTURES / "registry").glob("*.json"))
INVALID = sorted((FIXTURES / "invalid").glob("*.json"))


def _sample_entry(ratified_by: str | None = "vinylfigure (Ratifier)") -> CapabilityEntry:
    return CapabilityEntry(
        entry_id="slack.admin_users.api",
        system="slack",
        surface="admin.users.list",
        access_modes=(AccessMode.DIRECT_API, AccessMode.COMMUNITY_MCP),
        populations_yielded=(PopulationYield(type=PopulationType.ENTITY, name="workspace users"),),
        attributes=(
            PopulationAttributes(
                population_name="workspace users", fields_exposed=("id", "email", "deleted")
            ),
        ),
        temporal=TemporalShape(kind=TemporalShapeKind.STATE_ONLY),
        join_keys=("email",),
        auth_scope="admin.users:read",
        pagination=Pagination(
            method=PaginationMethod.CURSOR,
            exhaustion_method="follow response_metadata.next_cursor until empty",
        ),
        rate_limits="Tier 2 (~20 req/min)",
        provenance=Provenance(
            researched_by="vinylfigure (Cartographer draft, hand-authored)",
            researched_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
            source_citations=(
                SourceCitation(
                    url="https://api.slack.com/methods/admin.users.list",
                    title="Slack admin.users.list",
                ),
            ),
            doc_version="slack-api 2026-06",
            ratified_by=ratified_by,
        ),
    )


@pytest.mark.parametrize("path", VALID, ids=[p.name for p in VALID])
def test_valid_fixture_validates(path: Path) -> None:
    entry = CapabilityEntry.model_validate_json(path.read_text(encoding="utf-8"))
    assert entry.schema_version == "capability-entry@0.1.0"


@pytest.mark.parametrize("path", INVALID, ids=[p.name for p in INVALID])
def test_invalid_fixture_rejected(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        CapabilityEntry.model_validate(data)


def test_schema_version_is_const_pinned() -> None:
    data = json.loads(VALID[0].read_text(encoding="utf-8"))
    data["schema_version"] = "capability-entry@9.9.9"
    with pytest.raises(ValidationError):
        CapabilityEntry.model_validate(data)


def test_event_history_requires_window_days() -> None:
    with pytest.raises(ValidationError, match="window_days"):
        TemporalShape(kind=TemporalShapeKind.EVENT_HISTORY)
    assert TemporalShape(kind=TemporalShapeKind.EVENT_HISTORY, window_days=90).window_days == 90


@pytest.mark.parametrize(
    "kind",
    [k for k in TemporalShapeKind if k is not TemporalShapeKind.EVENT_HISTORY],
    ids=lambda k: k.value,
)
def test_window_days_forbidden_off_event_history(kind: TemporalShapeKind) -> None:
    with pytest.raises(ValidationError, match="EVENT_HISTORY"):
        TemporalShape(kind=kind, window_days=90)


def test_attributes_must_reference_yielded_population() -> None:
    data = json.loads((FIXTURES / "registry" / "okta--system-log-api.json").read_text())
    data["attributes"] = [{"population_name": "phantom population", "fields_exposed": ["id"]}]
    with pytest.raises(ValidationError, match="phantom population"):
        CapabilityEntry.model_validate(data)


def test_is_ratified_tracks_provenance() -> None:
    assert _sample_entry().is_ratified
    assert not _sample_entry(ratified_by=None).is_ratified


def test_empty_ratifier_string_rejected() -> None:
    with pytest.raises(ValidationError):
        _sample_entry(ratified_by="")


@pytest.mark.parametrize("path", VALID, ids=[p.name for p in VALID])
def test_fixture_roundtrip_canonical_identical(path: Path) -> None:
    entry = CapabilityEntry.model_validate_json(path.read_text(encoding="utf-8"))
    revived = CapabilityEntry.model_validate_json(entry.model_dump_json())
    assert revived == entry
    assert canonical_json(entry.model_dump(mode="json")) == canonical_json(
        revived.model_dump(mode="json")
    )
    assert sha256_canonical(entry) == sha256_canonical(revived)


def test_constructed_roundtrip_canonical_identical() -> None:
    entry = _sample_entry()
    revived = CapabilityEntry.model_validate_json(entry.model_dump_json())
    assert revived == entry
    assert sha256_canonical(entry) == sha256_canonical(revived)
