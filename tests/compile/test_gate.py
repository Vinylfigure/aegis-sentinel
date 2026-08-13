"""Compile integrity (PRD-v3 §7 guardrail): zero collectors execute for
claims with unresolved E-codes; clean claims yield plans.

``executable_collectors`` is the gate — a claim with any error
contributes nothing, even for its assertions that matched cleanly.
"""

from __future__ import annotations

from aegis_sentinel.compile import compile_program, executable_collectors

from .conftest import SIX_MONTHS, SIXTY_DAYS, lane

TIMING_CLAIM = "TERM.timely-revocation"


def _compile(template, usable_view, period):
    populations, claims = lane(template, period)
    return compile_program(claims, populations, usable_view)


def test_erroring_claim_yields_zero_executable_collectors(template, usable_view) -> None:
    result = _compile(template, usable_view, SIX_MONTHS)
    compilation = result.for_claim(TIMING_CLAIM)
    assert not compilation.ok
    assert all(p.claim_ref != TIMING_CLAIM for p in executable_collectors(result))


def test_clean_claims_yield_plans(template, usable_view) -> None:
    result = _compile(template, usable_view, SIXTY_DAYS)
    assert result.ok
    plans = executable_collectors(result)
    assert {p.claim_ref for p in plans} == {
        "TERM.feed-completeness",
        "TERM.timely-revocation",
        "TERM.github.no-residual-access",
        "TERM.gcp.no-residual-access",
        "TERM.slack.no-residual-access",
    }
    # Every plan threads the EQC-relevant identity fields.
    for plan in plans:
        assert plan.auth_scope and plan.surface and plan.join_keys
        assert plan.pagination.exhaustion_method
        assert plan.time_window == SIXTY_DAYS


def test_gate_is_per_claim_not_per_program(template, usable_view) -> None:
    """One claim failing must not suppress the others' plans — and the
    failing claim must contribute nothing (all five other assertions
    survive: 6 total minus TA-2's)."""
    result = _compile(template, usable_view, SIX_MONTHS)
    plans = executable_collectors(result)
    assert len(plans) == 5
    assert {p.claim_ref for p in plans} == {
        "TERM.feed-completeness",
        "TERM.github.no-residual-access",
        "TERM.gcp.no-residual-access",
        "TERM.slack.no-residual-access",
    }


def test_authoritative_source_preferred_for_plans(template, usable_view) -> None:
    """Deterministic candidate choice: the entity claims collect from
    each system's AUTHORITATIVE account inventory, not the contributing
    Okta group assignments."""
    result = _compile(template, usable_view, SIXTY_DAYS)
    by_assertion = {p.assertion_ref: p for p in executable_collectors(result)}
    assert by_assertion["TERM-GITHUB.a"].entry_id == "github.org_members.rest_v3"
    assert by_assertion["TERM-GCP.a"].entry_id == "gcp.iam.cloud_asset_v1"
    assert by_assertion["TERM-SLACK.a"].entry_id == "slack.users.web_api"
    assert by_assertion["TERM-FEED.a"].entry_id == "hris.terminations_feed.export_v1"
