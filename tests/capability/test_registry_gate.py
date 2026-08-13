"""The ratification gate is mechanical: drafts never reach usable().

SCH02 acceptance (docs/HANDOFF.md §4): registry versioned on disk;
unratified entries mechanically unusable by the compiler — this file is
the test that proves it.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from aegis_sentinel.capability import Registry

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_FIXTURES = ROOT / "tests" / "fixtures" / "capability" / "registry"

RATIFIED_ID = "github.org_members.rest_v3"
UNRATIFIED_ID = "okta.system_log.api_v1"


@pytest.fixture()
def registry() -> Registry:
    return Registry.load(REGISTRY_FIXTURES)


def test_all_includes_drafts(registry: Registry) -> None:
    ids = set(registry.all().entry_ids())
    assert ids == {RATIFIED_ID, UNRATIFIED_ID}


def test_usable_excludes_unratified(registry: Registry) -> None:
    usable_ids = registry.usable().entry_ids()
    assert RATIFIED_ID in usable_ids
    assert UNRATIFIED_ID not in usable_ids


def test_ratified_entry_in_both_views(registry: Registry) -> None:
    assert registry.all().get(RATIFIED_ID).is_ratified
    assert registry.usable().get(RATIFIED_ID).provenance.ratified_by == "vinylfigure (Ratifier)"


def test_unratified_lookup_raises_through_usable(registry: Registry) -> None:
    registry.all().get(UNRATIFIED_ID)  # visible for review...
    with pytest.raises(KeyError):
        registry.usable().get(UNRATIFIED_ID)  # ...mechanically unusable


def test_for_system_composes_with_usable(registry: Registry) -> None:
    assert registry.all().for_system("okta").entry_ids() == (UNRATIFIED_ID,)
    assert len(registry.usable().for_system("okta")) == 0
    assert registry.usable().for_system("github").entry_ids() == (RATIFIED_ID,)


def test_load_rejects_directory_containing_invalid_entry(tmp_path: Path) -> None:
    for src in REGISTRY_FIXTURES.glob("*.json"):
        shutil.copy(src, tmp_path / src.name)
    invalid = ROOT / "tests" / "fixtures" / "capability" / "invalid"
    shutil.copy(invalid / "capability-entry--extra-field.json", tmp_path / "zz-extra.json")
    with pytest.raises(ValidationError):
        Registry.load(tmp_path)


def test_load_rejects_duplicate_entry_ids(tmp_path: Path) -> None:
    src = REGISTRY_FIXTURES / "github--org-members-rest-v3.json"
    shutil.copy(src, tmp_path / "a.json")
    shutil.copy(src, tmp_path / "b.json")
    with pytest.raises(ValueError, match="duplicate entry_id"):
        Registry.load(tmp_path)


def test_load_missing_directory_raises() -> None:
    with pytest.raises(FileNotFoundError):
        Registry.load(REGISTRY_FIXTURES / "no-such-dir")


def test_ratification_cannot_be_mutated_in_place(registry: Registry) -> None:
    """Frozen models (D-P1): a draft cannot be flipped to ratified at runtime."""
    draft = registry.all().get(UNRATIFIED_ID)
    with pytest.raises(ValidationError):
        draft.provenance.ratified_by = "vinylfigure (Ratifier)"  # type: ignore[misc]


def test_repo_registry_directory_loads() -> None:
    """The real on-disk store (registry/capabilities/) always loads cleanly."""
    registry = Registry.load(ROOT / "registry" / "capabilities")
    for entry in registry.usable():
        assert entry.provenance.ratified_by is not None


def test_fixture_files_are_registry_shaped() -> None:
    """Fixtures stay honest JSON (D-P2) with one entry object per file."""
    for path in REGISTRY_FIXTURES.glob("*.json"):
        assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)
