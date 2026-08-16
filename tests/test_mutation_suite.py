"""VAL01 acceptance: the seeded-mutation suite detects 100% of its
assurance defects, and the harness itself provably turns red on a
silent PASS (the deliberately-compliant stub)."""

import json
from pathlib import Path

from mutation.harness import FIXTURES, MutationCase, load_cases, run_suite

PASS_CAPTURE = json.loads(
    (
        Path(__file__).resolve().parent / "fixtures" / "branch_protection" / "capture_pass.json"
    ).read_text()
)


def test_detection_rate_is_100_percent():
    cases = load_cases()
    assert len(cases) >= 5, "the playbook suite shrank — mutations were removed"
    report = run_suite(cases)
    assert report.detection_rate == 1.0, (
        f"assurance defect detection rate {report.detection_rate:.0%}; misses: {report.misses}"
    )


def test_harness_turns_red_on_a_silent_pass():
    """A compliant capture labeled as a defect MUST show up as a miss —
    proving the harness can fail the build, not just decorate it."""
    stub = MutationCase(
        name="silent-pass-stub",
        capture=PASS_CAPTURE,
        required_checks=("verify",),
        expected_status="FAIL",
    )
    report = run_suite(load_cases() + (stub,))
    assert report.detection_rate < 1.0
    assert any("silent-pass-stub" in miss for miss in report.misses)


def test_every_fixture_names_a_non_pass_expectation():
    for case in load_cases(FIXTURES):
        assert case.expected_status in {"FAIL", "UNKNOWN"}, case.name
