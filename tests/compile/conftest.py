"""Shared fixtures for the TYP01 compiler tests.

The program under compilation is always the real LANE01 termination
lane (templates/lanes/termination.json) instantiated over a period, and
the registry is always the real on-disk CAP01 store — the compiler is
tested against the artifacts it will ship with, not synthetic doubles.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from aegis_sentinel.capability import Registry, RegistryView
from aegis_sentinel.manifest import instantiate_lane
from aegis_sentinel.schema import Claim, LaneTemplate, Period, Population

ROOT = Path(__file__).resolve().parents[2]

#: The five fixture systems (PRD-v3 §6), keyed by node system_ref.
SYSTEMS = {"hris": "hris", "okta": "okta", "github": "github", "gcp": "gcp", "slack": "slack"}

#: The PRD §6 trap: a six-month audit period (181 days) against Okta's
#: 90-day System Log window.
SIX_MONTHS = Period(start=date(2026, 1, 1), end=date(2026, 6, 30))

#: Inside the Okta window: 60 days — must compile clean.
SIXTY_DAYS = Period(start=date(2026, 5, 1), end=date(2026, 6, 29))

#: Beyond Okta's 90 days but inside GitHub's 180 — the suggestion case.
ONE_TWENTY_DAYS = Period(start=date(2026, 1, 1), end=date(2026, 4, 30))


@pytest.fixture(scope="session")
def usable_view() -> RegistryView:
    return Registry.load(ROOT / "registry" / "capabilities").usable()


@pytest.fixture(scope="session")
def template() -> LaneTemplate:
    path = ROOT / "templates" / "lanes" / "termination.json"
    return LaneTemplate.model_validate_json(path.read_text(encoding="utf-8"))


def lane(template: LaneTemplate, period: Period) -> tuple[list[Population], list[Claim]]:
    return instantiate_lane(template, SYSTEMS, period)
