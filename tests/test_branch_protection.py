"""Verdict tests for the branch-protection control, including the seeded
drift capture — the detection proof this milestone exists to establish."""

import json
from pathlib import Path

from aegis_sentinel.controls.branch_protection import (
    FAIL,
    PASS,
    UNKNOWN,
    UNKNOWN_EVIDENCE,
    Verdict,
    evaluate,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SPEC_REQUIRED_CHECKS = ("verify",)


def load(relpath):
    return json.loads((FIXTURES / relpath).read_text())


def test_compliant_capture_passes():
    capture = load("branch_protection/capture_pass.json")
    verdict = evaluate(capture, required_checks=SPEC_REQUIRED_CHECKS)
    assert verdict == Verdict(status=PASS)


def test_seeded_drift_is_detected():
    """A required status check silently removed MUST turn the control red."""
    capture = load("seeded/branch_protection_missing_required_check.json")
    verdict = evaluate(capture, required_checks=SPEC_REQUIRED_CHECKS)
    assert verdict.status == FAIL
    assert any("'verify'" in reason for reason in verdict.reasons)


def test_unreadable_capture_is_unknown_not_a_guess():
    capture = load("branch_protection/capture_unreadable.json")
    verdict = evaluate(capture, required_checks=SPEC_REQUIRED_CHECKS)
    assert verdict.status == UNKNOWN
    assert verdict.unknown_cause == UNKNOWN_EVIDENCE


def test_missing_reviews_fails_on_a_successful_capture():
    capture = load("branch_protection/capture_pass.json")
    del capture["protection"]["required_pull_request_reviews"]
    verdict = evaluate(capture, required_checks=SPEC_REQUIRED_CHECKS)
    assert verdict.status == FAIL
    assert any("required_pull_request_reviews" in reason for reason in verdict.reasons)


def test_boolean_review_count_fails_not_passes():
    """JSON `true` is a Python bool, and bool is an int subclass — it must
    not satisfy the numeric threshold."""
    capture = load("branch_protection/capture_pass.json")
    capture["protection"]["required_pull_request_reviews"]["required_approving_review_count"] = True
    verdict = evaluate(capture, required_checks=SPEC_REQUIRED_CHECKS)
    assert verdict.status == FAIL


def test_admin_bypass_fails():
    capture = load("branch_protection/capture_pass.json")
    capture["protection"]["enforce_admins"] = {"enabled": False}
    verdict = evaluate(capture, required_checks=SPEC_REQUIRED_CHECKS)
    assert verdict.status == FAIL
    assert any("enforce_admins" in reason for reason in verdict.reasons)


def test_evaluation_is_deterministic():
    capture = load("seeded/branch_protection_missing_required_check.json")
    first = evaluate(capture, required_checks=SPEC_REQUIRED_CHECKS)
    second = evaluate(capture, required_checks=SPEC_REQUIRED_CHECKS)
    assert first == second
