"""SCH02 acceptance: unratified entries are mechanically unusable, and the
lifecycle validator holds (FROZEN requires a ratifier — D-L1)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from aegis_sentinel.capability import CapabilityEntry, Registry

REGISTRY_DIR = Path(__file__).resolve().parent.parent / "registry" / "capabilities"


def test_on_disk_registry_loads():
    registry = Registry.load(REGISTRY_DIR)
    assert {e.id for e in registry.all()} == {"github.members", "okta.system_log"}


def test_unratified_entries_are_mechanically_unusable():
    registry = Registry.load(REGISTRY_DIR)
    usable_ids = {e.id for e in registry.usable()}
    assert usable_ids == {"github.members"}
    assert registry.get_usable("okta.system_log") is None
    assert registry.get_usable("github.members") is not None


def test_frozen_without_ratifier_is_rejected():
    entry = (REGISTRY_DIR / "okta.system_log.json").read_text()
    with pytest.raises(ValidationError, match="ratified_by"):
        CapabilityEntry.model_validate_json(entry.replace('"draft"', '"frozen"'))


def test_temporal_kind_conditionals():
    frozen = CapabilityEntry.model_validate_json((REGISTRY_DIR / "github.members.json").read_text())
    with pytest.raises(ValidationError, match="window_days"):
        CapabilityEntry.model_validate(
            frozen.model_dump() | {"temporal": {"kind": "event-history"}}
        )


def test_okta_history_caveat_recorded():
    registry = Registry.load(REGISTRY_DIR)
    okta = next(e for e in registry.all() if e.id == "okta.system_log")
    assert okta.temporal.window_days == 90
    assert any("90 days" in caveat for caveat in okta.history_caveats)


def test_duplicate_ids_rejected():
    entry = CapabilityEntry.model_validate_json((REGISTRY_DIR / "github.members.json").read_text())
    with pytest.raises(ValueError, match="duplicate"):
        Registry((entry, entry))
