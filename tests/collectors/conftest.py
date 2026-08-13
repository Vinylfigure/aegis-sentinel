"""COL02–05 shared fixtures: transports, surface maps, collector plans.

State-surface plans for GitHub/GCP/Slack come from the REAL lane compile
(the ``TERM.{system}.no-residual-access`` claims match each system's
inventory entry) — never synthetic doubles. The Okta surfaces and the
GitHub audit log get no plan out of the lane compile today (okta.users
is only ever a CONTRIBUTING candidate; the 181-day TIMING claim E204s
against the 90-day System Log window — deliberately), so their plans are
built field-by-field from the ratified registry entry via
:func:`plan_from_entry`, with event windows sized inside each entry's
declared retention (Okta 90d, GitHub 180d).
"""

from __future__ import annotations

from datetime import date

import pytest

from aegis_sentinel.capability.entry import CapabilityEntry
from aegis_sentinel.capability.registry import RegistryView
from aegis_sentinel.collectors import FixtureTransport
from aegis_sentinel.compile import (
    CompiledCollectorPlan,
    CompileResult,
    executable_collectors,
)
from aegis_sentinel.schema import AssertionType, Period
from conftest import REPO_ROOT, TENANTS_DIR

SEEDED_DIR = REPO_ROOT / "tests" / "fixtures" / "seeded"

OKTA_USERS_ENTRY = "okta.users.api_v1"
OKTA_LOG_ENTRY = "okta.system_log.api_v1"
GITHUB_MEMBERS_ENTRY = "github.org_members.rest_v3"
GITHUB_AUDIT_ENTRY = "github.audit_log.rest_v3"
GCP_ENTRY = "gcp.iam.cloud_asset_v1"
SLACK_ENTRY = "slack.users.web_api"


def plan_from_entry(
    entry: CapabilityEntry,
    *,
    claim_ref: str,
    assertion_ref: str,
    assertion_type: AssertionType,
    population_ref: str,
    source_id: str,
    time_window: Period,
) -> CompiledCollectorPlan:
    """A collector plan derived field-by-field from one registry entry."""
    return CompiledCollectorPlan(
        claim_ref=claim_ref,
        assertion_ref=assertion_ref,
        assertion_type=assertion_type,
        population_ref=population_ref,
        source_id=source_id,
        entry_id=entry.entry_id,
        system=entry.system,
        surface=entry.surface,
        auth_scope=entry.auth_scope,
        pagination=entry.pagination,
        temporal=entry.temporal,
        join_keys=entry.join_keys,
        time_window=time_window,
    )


def _lane_plan(compile_result: CompileResult, entry_id: str) -> CompiledCollectorPlan:
    plans = [p for p in executable_collectors(compile_result) if p.entry_id == entry_id]
    assert plans, f"no executable lane plan matched entry {entry_id}"
    return plans[0]


# ---- surface maps (FixtureTransport subdirectories) ----------------------


@pytest.fixture(scope="session")
def okta_surfaces(registry_usable: RegistryView) -> dict[str, str]:
    return {
        registry_usable.get(OKTA_USERS_ENTRY).surface: "users",
        registry_usable.get(OKTA_LOG_ENTRY).surface: "system-log",
    }


@pytest.fixture(scope="session")
def github_surfaces(registry_usable: RegistryView) -> dict[str, str]:
    return {
        registry_usable.get(GITHUB_MEMBERS_ENTRY).surface: "org-members",
        registry_usable.get(GITHUB_AUDIT_ENTRY).surface: "audit-log",
    }


# ---- tenant transports ---------------------------------------------------


@pytest.fixture(scope="session")
def okta_transport(okta_surfaces: dict[str, str]) -> FixtureTransport:
    return FixtureTransport(TENANTS_DIR, surfaces=okta_surfaces)


@pytest.fixture(scope="session")
def github_transport(github_surfaces: dict[str, str]) -> FixtureTransport:
    return FixtureTransport(TENANTS_DIR, surfaces=github_surfaces)


@pytest.fixture(scope="session")
def tenant_transport() -> FixtureTransport:
    """Flat single-surface layout (gcp, slack, hris)."""
    return FixtureTransport(TENANTS_DIR)


# ---- plans ---------------------------------------------------------------


@pytest.fixture(scope="session")
def okta_users_plan(
    registry_usable: RegistryView, engagement_period: Period
) -> CompiledCollectorPlan:
    return plan_from_entry(
        registry_usable.get(OKTA_USERS_ENTRY),
        claim_ref="COL02.okta-users",
        assertion_ref="COL02-USERS-a",
        assertion_type=AssertionType.STATE,
        population_ref="TERM.okta.accounts",
        source_id="okta-users",
        time_window=engagement_period,
    )


@pytest.fixture(scope="session")
def okta_log_plan(registry_usable: RegistryView) -> CompiledCollectorPlan:
    """EVENT plan sized inside the System Log's 90-day retention window."""
    return plan_from_entry(
        registry_usable.get(OKTA_LOG_ENTRY),
        claim_ref="COL02.okta-system-log",
        assertion_ref="COL02-LOG-a",
        assertion_type=AssertionType.EVENT,
        population_ref="TERM.terminations",
        source_id="okta-system-log",
        time_window=Period(start=date(2026, 4, 2), end=date(2026, 6, 30)),
    )


@pytest.fixture(scope="session")
def github_members_plan(compile_result: CompileResult) -> CompiledCollectorPlan:
    return _lane_plan(compile_result, GITHUB_MEMBERS_ENTRY)


@pytest.fixture(scope="session")
def github_audit_plan(registry_usable: RegistryView) -> CompiledCollectorPlan:
    """EVENT plan sized inside the audit log's 180-day query window."""
    return plan_from_entry(
        registry_usable.get(GITHUB_AUDIT_ENTRY),
        claim_ref="COL03.github-audit-log",
        assertion_ref="COL03-AUDIT-a",
        assertion_type=AssertionType.EVENT,
        population_ref="TERM.terminations",
        source_id="github-audit-log",
        time_window=Period(start=date(2026, 1, 2), end=date(2026, 6, 30)),
    )


@pytest.fixture(scope="session")
def gcp_plan(compile_result: CompileResult) -> CompiledCollectorPlan:
    return _lane_plan(compile_result, GCP_ENTRY)


@pytest.fixture(scope="session")
def slack_plan(compile_result: CompileResult) -> CompiledCollectorPlan:
    return _lane_plan(compile_result, SLACK_ENTRY)
