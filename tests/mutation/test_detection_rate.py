"""VAL01 — assurance defect detection rate over the poison suite.

Headline metric per docs/PRD-v3.md §7: detected / runnable, target 100%
on the playbook suite; any silent PASS is a build-stopping bug. While
the pipeline is unbuilt (no runners registered) the suite passes but
says so out loud — it never reports 100% over zero runnable fixtures.
"""

from __future__ import annotations

from aegis_sentinel.schema.verdict import UnknownWhyCode, VerdictState

from .conftest import (
    EXPECTED_POISONS,
    RUNNER_REGISTRY,
    Outcome,
    assert_suite_detects,
    discover_fixtures,
    evaluate_suite,
)


def test_expected_outcomes_match_prd_encoding():
    """The six fixtures encode exactly the PRD §6 poison outcomes."""
    by_poison = {f.poison: f.expected for f in discover_fixtures()}
    assert set(by_poison) == EXPECTED_POISONS
    assert by_poison["contractor-absent-hris"] == Outcome(
        "VERDICT", VerdictState.UNKNOWN, UnknownWhyCode.UNKNOWN_POPULATION, None
    )
    assert by_poison["dormant-github-local-account"] == Outcome(
        "VERDICT", VerdictState.FAIL, None, None
    )
    assert by_poison["breakglass-cloud-account"] == Outcome("COMPILE_ERROR", None, None, "E117")
    assert by_poison["failed-identity-join"] == Outcome(
        "VERDICT", VerdictState.UNKNOWN, UnknownWhyCode.UNKNOWN_POPULATION, None
    )
    assert by_poison["delayed-revocation"] == Outcome("VERDICT", VerdictState.FAIL, None, None)
    assert by_poison["legitimate-exception"] == Outcome(
        "VERDICT", VerdictState.EXCEPTION, None, None
    )


def test_every_fixture_carries_provenance_readme():
    for fixture in discover_fixtures():
        readme = (fixture.path / "README.md").read_text(encoding="utf-8")
        assert "docs/PRD-v3.md" in readme, f"{fixture.poison}: README must cite PRD §6"
        assert "TODO(playbook)" in readme, f"{fixture.poison}: README must carry playbook marker"


def test_assurance_defect_detection_rate():
    """The suite gate: 100% detection over runnable poisons, honestly.

    VAL02 is landed: the REAL pipeline runs behind every poison, so all
    six fixtures must be runnable and every one must be detected —
    assurance defect detection rate = 6/6 = 100% (docs/PRD-v3.md §7).
    """
    fixtures = discover_fixtures()
    report = evaluate_suite(fixtures, RUNNER_REGISTRY)
    print()
    print(report.table())

    assert len(report.runnable) == 6, (
        f"VAL02 requires all six poisons runnable against the real pipeline; "
        f"only {len(report.runnable)}/{report.total} have runners"
    )
    assert_suite_detects(report)
    assert report.detection_rate == 1.0
    assert report.detected_count == 6


def test_zero_runnable_never_reports_100_percent():
    """Empty registry -> rate is None; the 100% claim is unavailable."""
    report = evaluate_suite(discover_fixtures(), registry={})
    assert not report.runnable
    assert report.detection_rate is None
    assert report.detected_count == 0
    assert "not yet meaningful" in report.table()
    assert "100%" not in report.table()
