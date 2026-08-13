"""Shared walking-skeleton pipeline fixtures.

The pipeline under test is always the real thing: the LANE01 template
instantiated over the fixture engagement's period, compiled against the
real on-disk CAP01 registry, collected from the fixture tenant
(``tests/fixtures/tenants/``) — never synthetic doubles
(same discipline as tests/compile/conftest.py).
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from aegis_sentinel.capability import Registry, RegistryView
from aegis_sentinel.compile import (
    CompiledCollectorPlan,
    CompileResult,
    compile_program,
    executable_collectors,
)
from aegis_sentinel.manifest import instantiate_lane
from aegis_sentinel.schema import Claim, LaneTemplate, Period, Population

REPO_ROOT = Path(__file__).resolve().parents[1]
TENANTS_DIR = REPO_ROOT / "tests" / "fixtures" / "tenants"
SEEDED_TRUNCATED_DIR = REPO_ROOT / "tests" / "fixtures" / "seeded" / "hris_truncated_feed"

#: The five fixture systems (PRD-v3 §6), keyed by lane node system_ref.
SYSTEMS = {"hris": "hris", "okta": "okta", "github": "github", "gcp": "gcp", "slack": "slack"}

FEED_CLAIM = "TERM.feed-completeness"
TERMINATIONS_POPULATION = "TERM.terminations"


@pytest.fixture(scope="session")
def engagement() -> dict[str, Any]:
    return json.loads((TENANTS_DIR / "engagement.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def retrieved_at(engagement: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(engagement["retrieved_at"])


@pytest.fixture(scope="session")
def evaluated_at(engagement: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(engagement["evaluated_at"])


@pytest.fixture(scope="session")
def engagement_period(engagement: dict[str, Any]) -> Period:
    return Period(
        start=date.fromisoformat(engagement["period"]["start"]),
        end=date.fromisoformat(engagement["period"]["end"]),
    )


@pytest.fixture(scope="session")
def registry_usable() -> RegistryView:
    return Registry.load(REPO_ROOT / "registry" / "capabilities").usable()


@pytest.fixture(scope="session")
def lane_objects(engagement_period: Period) -> tuple[list[Population], list[Claim]]:
    template = LaneTemplate.model_validate_json(
        (REPO_ROOT / "templates" / "lanes" / "termination.json").read_text(encoding="utf-8")
    )
    return instantiate_lane(template, SYSTEMS, engagement_period)


@pytest.fixture(scope="session")
def compile_result(
    lane_objects: tuple[list[Population], list[Claim]], registry_usable: RegistryView
) -> CompileResult:
    populations, claims = lane_objects
    return compile_program(claims, populations, registry_usable)


@pytest.fixture(scope="session")
def feed_plan(compile_result: CompileResult) -> CompiledCollectorPlan:
    """The TA-1 collector plan (both assertions matched the same entry)."""
    plans = [p for p in executable_collectors(compile_result) if p.claim_ref == FEED_CLAIM]
    assert plans, "TA-1 feed-completeness claim failed to compile"
    return plans[0]


@pytest.fixture(scope="session")
def feed_claim(lane_objects: tuple[list[Population], list[Claim]]) -> Claim:
    _, claims = lane_objects
    return next(c for c in claims if c.claim_id == FEED_CLAIM)


@pytest.fixture(scope="session")
def terminations_population(
    lane_objects: tuple[list[Population], list[Claim]],
) -> Population:
    populations, _ = lane_objects
    return next(p for p in populations if p.population_id == TERMINATIONS_POPULATION)
