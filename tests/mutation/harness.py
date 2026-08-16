"""VAL01 mutation harness: seeded assurance defects in, detection rate out.

A mutation case pairs a poisoned capture with the verdict the control MUST
emit. The suite's headline number — the assurance defect detection rate —
is computed here and asserted at 100% by tests/test_mutation_suite.py; a
case the control waves through (a silent PASS) is a miss, and one miss
turns the build red.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from aegis_sentinel.controls.branch_protection import PASS, evaluate

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@dataclass(frozen=True)
class MutationCase:
    name: str
    capture: dict
    required_checks: tuple[str, ...]
    expected_status: str  # the non-PASS verdict the control must emit


@dataclass(frozen=True)
class MutationReport:
    total: int
    detected: int
    misses: tuple[str, ...]

    @property
    def detection_rate(self) -> float:
        return 1.0 if self.total == 0 else self.detected / self.total


def load_cases(path: Path = FIXTURES) -> tuple[MutationCase, ...]:
    cases = []
    for file in sorted(path.glob("*.json")):
        raw = json.loads(file.read_text())
        cases.append(
            MutationCase(
                name=raw["name"],
                capture=raw["capture"],
                required_checks=tuple(raw["required_checks"]),
                expected_status=raw["expected_status"],
            )
        )
    return tuple(cases)


def run_suite(cases: tuple[MutationCase, ...]) -> MutationReport:
    misses = []
    for case in cases:
        verdict = evaluate(case.capture, required_checks=case.required_checks)
        if verdict.status == PASS or verdict.status != case.expected_status:
            misses.append(f"{case.name}: expected {case.expected_status}, got {verdict.status}")
    return MutationReport(total=len(cases), detected=len(cases) - len(misses), misses=tuple(misses))
