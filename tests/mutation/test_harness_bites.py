"""VAL01 — proof that the harness bites (docs/HANDOFF.md §4).

A deliberately broken always-PASS runner is injected for a poison whose
expected outcome is FAIL. The harness must score it undetected, compute
a detection rate < 100%, and its build gate must raise — i.e. this
exact condition would turn the build red. These tests pass forever:
they prove the harness *can* fail, not that the pipeline works.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aegis_sentinel.schema.verdict import VerdictState

from .conftest import (
    MutationDetectionFailure,
    Outcome,
    assert_suite_detects,
    discover_fixtures,
    evaluate_suite,
)


class AlwaysPassStub:
    """Deliberately broken PipelineRunner: silent PASS for any fixture."""

    def run(self, fixture_dir: Path) -> Outcome:
        return Outcome(
            detection="VERDICT",
            verdict_state=VerdictState.PASS,
            why_code=None,
            e_code=None,
        )


def _report_with_silent_pass_stub():
    fixtures = discover_fixtures()
    # dormant-github-local-account expects VERDICT FAIL — the stub's
    # silent PASS against it is exactly the bug the harness exists for.
    registry = {"dormant-github-local-account": AlwaysPassStub()}
    return evaluate_suite(fixtures, registry)


def test_silent_pass_is_marked_undetected():
    report = _report_with_silent_pass_stub()
    result = next(r for r in report.results if r.poison == "dormant-github-local-account")
    assert result.runnable is True
    assert result.detected is False
    assert result.observed is not None and result.observed.is_silent_pass
    assert result.expected.verdict_state is VerdictState.FAIL


def test_silent_pass_drives_rate_below_100_percent():
    report = _report_with_silent_pass_stub()
    assert len(report.runnable) == 1
    assert report.detection_rate is not None
    assert report.detection_rate < 1.0


def test_silent_pass_fails_the_build():
    """The gate raises on the stub — this condition turns the build red."""
    report = _report_with_silent_pass_stub()
    with pytest.raises(MutationDetectionFailure, match="dormant-github-local-account"):
        assert_suite_detects(report)


def test_all_poisons_silently_passing_scores_zero():
    """Even a runner registered for every poison cannot fake detection:
    an all-PASS pipeline scores 0%, never 100%."""
    fixtures = discover_fixtures()
    registry = {f.poison: AlwaysPassStub() for f in fixtures}
    report = evaluate_suite(fixtures, registry)
    assert len(report.runnable) == report.total == 6
    assert report.detection_rate == 0.0
    with pytest.raises(MutationDetectionFailure):
        assert_suite_detects(report)
