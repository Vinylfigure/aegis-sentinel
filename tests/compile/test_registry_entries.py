"""CAP01 — the seven hand-authored capability entries load, are
ratified, and carry the facts the compiler depends on (docs/HANDOFF.md
§4 CAP01; docs/EXECUTION-PLAN.md Phase 1).
"""

from __future__ import annotations

from aegis_sentinel.capability import Registry, TemporalShapeKind

from .conftest import ROOT

EXPECTED_IDS = {
    "hris.terminations_feed.export_v1",
    "okta.users.api_v1",
    "okta.system_log.api_v1",
    "github.org_members.rest_v3",
    "github.audit_log.rest_v3",
    "gcp.iam.cloud_asset_v1",
    "slack.users.web_api",
}

OKTA_CAVEAT = (
    "Okta System Log retains 90 days — TIMING assertions beyond window need exported archive"
)

#: Every source the instantiated termination lane declares must be
#: yielded by some entry (otherwise the lane cannot even E117-cleanly
#: compile).
LANE_SOURCES = {
    "hris-termination-feed",
    "okta-system-log",
    "okta-group-assignments",
    "github-account-inventory",
    "gcp-account-inventory",
    "slack-account-inventory",
}


def _registry() -> Registry:
    return Registry.load(ROOT / "registry" / "capabilities")


def test_all_seven_entries_load_and_are_ratified() -> None:
    registry = _registry()
    assert set(registry.all().entry_ids()) == EXPECTED_IDS
    for entry in registry.all():
        assert entry.is_ratified, entry.entry_id
        assert entry.provenance.ratified_by == "vinylfigure (Ratifier)"


def test_all_seven_appear_in_usable() -> None:
    assert set(_registry().usable().entry_ids()) == EXPECTED_IDS


def test_okta_system_log_carries_the_90_day_caveat() -> None:
    entry = _registry().usable().get("okta.system_log.api_v1")
    assert entry.temporal.kind is TemporalShapeKind.EVENT_HISTORY
    assert entry.temporal.window_days == 90
    assert OKTA_CAVEAT in entry.history_caveats


def test_github_audit_log_window_and_caveat() -> None:
    entry = _registry().usable().get("github.audit_log.rest_v3")
    assert entry.temporal.kind is TemporalShapeKind.EVENT_HISTORY
    assert entry.temporal.window_days == 180
    assert any("180 days" in caveat for caveat in entry.history_caveats)


def test_state_only_surfaces_say_so() -> None:
    """The three downstream inventories and okta.users are STATE_ONLY,
    and each carries a caveat admitting state cannot prove timing."""
    view = _registry().usable()
    for entry_id in (
        "okta.users.api_v1",
        "github.org_members.rest_v3",
        "gcp.iam.cloud_asset_v1",
        "slack.users.web_api",
    ):
        entry = view.get(entry_id)
        assert entry.temporal.kind is TemporalShapeKind.STATE_ONLY, entry_id
        assert any("STATE only" in caveat for caveat in entry.history_caveats), entry_id


def test_every_entry_carries_vendor_doc_citations() -> None:
    for entry in _registry().all():
        assert entry.provenance.source_citations, entry.entry_id
        for citation in entry.provenance.source_citations:
            assert citation.url.startswith("https://"), entry.entry_id
            assert citation.title


def test_every_entry_names_least_privilege_scope_and_exhaustion() -> None:
    for entry in _registry().all():
        assert "read" in entry.auth_scope.lower(), entry.entry_id
        assert entry.pagination.exhaustion_method, entry.entry_id


def test_join_keys_support_the_identity_join() -> None:
    view = _registry().usable()
    assert view.get("hris.terminations_feed.export_v1").join_keys == ("employee_id", "email")
    assert view.get("okta.users.api_v1").join_keys == ("email", "login")
    assert "login" in view.get("github.org_members.rest_v3").join_keys


def test_lane_sources_all_covered_by_yields() -> None:
    yields = {y.name for entry in _registry().usable() for y in entry.populations_yielded}
    assert LANE_SOURCES <= yields
