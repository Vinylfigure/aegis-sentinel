"""SCH02 acceptance: unratified entries are mechanically unusable, and the
lifecycle validator holds (FROZEN requires a ratifier — D-L1)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from aegis_sentinel.capability import CapabilityEntry, Registry
from aegis_sentinel.capability.allowlist import is_allowed_citation

REGISTRY_DIR = Path(__file__).resolve().parent.parent / "registry" / "capabilities"


CAP01_IDS = {
    "github.members",
    "github.audit_log",
    "okta.system_log",
    "okta.users",
    "gcp.service_accounts",
    "slack.scim_users",
    "workday.terminated_workers",
}
FROZEN_IDS = {"github.members", "okta.system_log", "gcp.service_accounts"}


def test_on_disk_registry_loads_cap01_seven():
    registry = Registry.load(REGISTRY_DIR)
    # Superset, not equality: CAP01 was the walking-skeleton's original
    # seven; later work (e.g. #128's Merge/Jira acme-live entries) grows
    # the registry without displacing them.
    assert CAP01_IDS <= {e.id for e in registry.all()}


def test_unratified_entries_are_mechanically_unusable():
    registry = Registry.load(REGISTRY_DIR)
    assert {e.id for e in registry.usable()} == FROZEN_IDS
    assert registry.get_usable("slack.scim_users") is None
    assert registry.get_usable("github.members") is not None


def test_every_draft_names_why_it_is_not_ratified():
    """A draft without a recorded blocker is indistinguishable from
    forgotten work — each must say what verification it awaits."""
    registry = Registry.load(REGISTRY_DIR)
    for entry in registry.all():
        if entry.lifecycle.value == "draft":
            assert any("DRAFT:" in caveat for caveat in entry.history_caveats), entry.id


def test_frozen_entries_carry_citations_and_ratifier():
    registry = Registry.load(REGISTRY_DIR)
    for entry in registry.usable():
        assert entry.provenance.citations, entry.id
        assert entry.ratified_by == "vinylfigure (Ratifier)", entry.id


def test_frozen_without_ratifier_is_rejected():
    entry = (REGISTRY_DIR / "slack.scim_users.json").read_text()
    assert '"draft"' in entry, "fixture premise: slack.scim_users is a draft"
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


ACME_LIVE_NEW_IDS = {"merge.hris.employees", "jira.issues", "jira.issue_changelog"}


def test_acme_live_registry_entries_load_as_drafts_with_allowed_citations():
    """#128 (acme-live Deliverable 5): the two new vendors' entries are
    present, mechanically DRAFT/unratified, and every citation they carry
    passes the same D7 allowlist test as the pre-existing entries."""
    registry = Registry.load(REGISTRY_DIR)
    entries = {e.id: e for e in registry.all() if e.id in ACME_LIVE_NEW_IDS}
    assert entries.keys() == ACME_LIVE_NEW_IDS
    for entry in entries.values():
        assert entry.lifecycle.value == "draft", entry.id
        assert entry.ratified_by is None, entry.id
        for citation in entry.provenance.citations:
            assert is_allowed_citation(entry.system, citation), (entry.id, citation)
