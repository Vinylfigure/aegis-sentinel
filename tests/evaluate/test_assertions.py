"""EVAL01 typed evaluators over the REAL engagement run: five states,
per-member evidence, D-S1 triples, byte-identical re-performance.

The engagement run is the genuine pipeline (compile → collect →
reconcile → evaluate over the fixture tenants) — never synthetic
doubles — so these tests double as the poison-detection proof at the
verdict level (docs/PRD-v3.md §6 acceptance).
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from aegis_sentinel.engagement import run_demo_engagement
from aegis_sentinel.evaluate import (
    TimingCase,
    evaluate_ratified_exclusion,
    evaluate_timing_claim,
)
from aegis_sentinel.evaluate.assertions import RatifiedScopeExclusion
from aegis_sentinel.schema import (
    D7Family,
    UnknownWhyCode,
    VerdictState,
)
from conftest import REPO_ROOT


@pytest.fixture(scope="module")
def run():
    return run_demo_engagement(REPO_ROOT)


def test_all_five_verdict_states_emitted_distinctly(run) -> None:
    states = {v.state for v in run.verdicts}
    assert states == set(VerdictState), "PRD §6: the five verdict states render distinctly"


def test_every_verdict_is_sealed_with_the_ds1_triple(run) -> None:
    engagement = run.engagement
    for verdict in run.verdicts:
        assert verdict.manifest_version == engagement["manifest_version"]
        assert verdict.snapshot_hash == engagement["ratified_manifest_snapshot_hash"]
        assert verdict.contract_hash is not None
        assert verdict.evaluated_at == datetime.fromisoformat(engagement["evaluated_at"])
        assert verdict.record_hash == verdict.compute_record_hash()


def test_timing_fail_names_the_delayed_member_with_evidence(run) -> None:
    """Delayed-revocation poison: marcus.webb, 9 business days > 5."""
    verdict = run.verdict_for("TERM-TIMING.a")
    assert verdict.state is VerdictState.FAIL
    assert verdict.message is not None
    assert "marcus.webb" in verdict.message
    assert "9 business day(s) (> 5)" in verdict.message
    assert "2026-02-13" in verdict.message and "2026-02-26" in verdict.message
    # The clean members' evidence rides along too.
    assert "tomas.rivera" in verdict.message and "ingrid.solberg" in verdict.message


def test_timing_unknown_member_is_identity_fuzzy_never_guessed(run) -> None:
    verdict = run.verdict_for("TERM-TIMING.a")
    assert verdict.message is not None
    assert "dana.whitfield" in verdict.message
    assert "cannot be attributed" in verdict.message


def test_github_non_existence_fails_on_the_dormant_local_account(run) -> None:
    """Dormant-github poison: bm-legacy-bot, active, unjoinable, dormant."""
    verdict = run.verdict_for("TERM-GITHUB.a")
    assert verdict.state is VerdictState.FAIL
    assert verdict.message is not None
    assert "bm-legacy-bot" in verdict.message
    assert "dormant" in verdict.message


def test_slack_non_existence_is_exception_with_disposition_ref(run) -> None:
    """Legitimate-exception poison: kai.moreno under DISP-2026-114."""
    verdict = run.verdict_for("TERM-SLACK.a")
    assert verdict.state is VerdictState.EXCEPTION
    assert verdict.disposition_ref == "DISP-2026-114"


def test_feed_existence_is_unknown_population_identity_fuzzy(run) -> None:
    """Failed-identity-join poison: E-1033 (dana), maiden-name orphan."""
    verdict = run.verdict_for("TERM-FEED.b")
    assert verdict.state is VerdictState.UNKNOWN
    assert verdict.why_code is UnknownWhyCode.UNKNOWN_POPULATION
    assert verdict.d7_family is D7Family.IDENTITY_FUZZY
    assert verdict.message is not None and "E-1033" in verdict.message


def test_join_claim_is_unknown_population_from_negative_space(run) -> None:
    """Contractor-absent poison: the negative-space delta drives it."""
    verdict = run.verdict_for("TERM-JOIN.a")
    assert verdict.state is VerdictState.UNKNOWN
    assert verdict.why_code is UnknownWhyCode.UNKNOWN_POPULATION
    assert verdict.message is not None
    assert "blake-morgan-vendor" in verdict.message
    assert "absent from hris-termination-feed" in verdict.message


def test_excluded_record_carries_the_ratification(run) -> None:
    verdict = run.verdict_for("TERM-CORP-IT.a")
    assert verdict.state is VerdictState.EXCLUDED
    assert verdict.ratification_ref == "RAT-2026-031"


def test_gcp_claim_has_no_verdict_because_it_failed_to_compile(run) -> None:
    """Compile integrity (PRD-v3 §7): the E117-blocked claim executed
    nothing and judged nothing — the compile error is the detection."""
    assert not any(v.claim_ref == "TERM.gcp.no-residual-access" for v in run.verdicts)
    assert any(e.code == "E117" for e in run.compile_errors)
    assert any(e.code == "E204" for e in run.compile_errors)


def test_reperformance_is_byte_identical() -> None:
    """Same fixtures, two full runs → byte-identical verdict records (D-P3)."""
    one = [v.model_dump_json() for v in run_demo_engagement(REPO_ROOT).verdicts]
    two = [v.model_dump_json() for v in run_demo_engagement(REPO_ROOT).verdicts]
    assert one == two


# ---- unit-level: the evaluators are pure functions of typed inputs -----


def _timing_claim(run):
    # The re-scoped claim the engagement evaluated (60-day honest window).
    from aegis_sentinel.engagement import SYSTEMS
    from aegis_sentinel.manifest import instantiate_lane

    _, claims = instantiate_lane(run.template, SYSTEMS, run.timing_window)
    return next(c for c in claims if c.claim_id == "TERM.timely-revocation")


def test_timing_evaluator_business_day_math(run) -> None:
    claim = _timing_claim(run)
    contract = run.contracts["okta-system-log"]
    verdict = evaluate_timing_claim(
        claim,
        [
            TimingCase(
                member_key="E-1",
                display_name="fri.term@x.test",
                termination_date=date(2026, 2, 13),  # Friday
                idp_deactivated_on=date(2026, 2, 20),  # next Friday = 5 bd
            )
        ],
        contract,
        manifest_version="v1",
        manifest_snapshot_hash="0" * 64,
        evidence_refs=(),
        evaluated_at=datetime.fromisoformat("2026-07-01T06:05:00+00:00"),
    )
    assert verdict.state is VerdictState.PASS
    assert verdict.message is not None and "5 business day(s)" in verdict.message


def test_timing_evaluator_missing_events_is_basis_missing(run) -> None:
    claim = _timing_claim(run)
    verdict = evaluate_timing_claim(
        claim,
        [
            TimingCase(
                member_key="E-1",
                display_name="no.events@x.test",
                termination_date=date(2026, 2, 13),
            )
        ],
        run.contracts["okta-system-log"],
        manifest_version="v1",
        manifest_snapshot_hash="0" * 64,
        evidence_refs=(),
        evaluated_at=datetime.fromisoformat("2026-07-01T06:05:00+00:00"),
    )
    assert verdict.state is VerdictState.UNKNOWN
    assert verdict.why_code is UnknownWhyCode.UNKNOWN_EVIDENCE
    assert verdict.d7_family is D7Family.BASIS_MISSING


def test_exclusion_evaluator_requires_ratification_shape() -> None:
    record = evaluate_ratified_exclusion(
        RatifiedScopeExclusion(
            ratification_ref="RAT-1",
            system="corp-it",
            claim_ref="C",
            assertion_ref="C-X.a",
            population_ref="P",
            rationale="ratified out of scope",
            ratified_by="owner (Ratifier)",
        ),
        manifest_version="v1",
        manifest_snapshot_hash="0" * 64,
        evaluated_at=datetime.fromisoformat("2026-07-01T06:05:00+00:00"),
    )
    assert record.state is VerdictState.EXCLUDED
    assert record.ratification_ref == "RAT-1"
    assert record.record_hash == record.compute_record_hash()
