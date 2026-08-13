"""THE acceptance test (docs/HANDOFF.md §4 TYP01; docs/PRD-v3.md §6).

Does E204-class checking catch the Okta 90-day log window against a
six-month TIMING assertion? The termination lane's TA-2 assertion
(TERM-TIMING.a) over a six-month period must fail compilation with
E204, the message must name the 90-day window, and the suggestion must
degrade honestly: with nothing usable covering 181 days,
``satisfiable_via`` is empty and the message says so. At 60 days the
same assertion compiles clean against okta.system_log; at 120 days the
failure suggests github.audit_log (180d) — a suggestion drawn only from
actually-usable registry entries.
"""

from __future__ import annotations

from aegis_sentinel.compile import (
    E204TemporalInsufficiency,
    compile_program,
    executable_collectors,
    period_days,
)

from .conftest import ONE_TWENTY_DAYS, SIX_MONTHS, SIXTY_DAYS, lane

TIMING_CLAIM = "TERM.timely-revocation"
TIMING_ASSERTION = "TERM-TIMING.a"
OKTA_LOG = "okta.system_log.api_v1"
GITHUB_AUDIT = "github.audit_log.rest_v3"


def _compile(template, usable_view, period):
    populations, claims = lane(template, period)
    return compile_program(claims, populations, usable_view)


def test_six_month_timing_assertion_fails_with_e204(template, usable_view) -> None:
    assert period_days(SIX_MONTHS) == 181
    result = _compile(template, usable_view, SIX_MONTHS)
    compilation = result.for_claim(TIMING_CLAIM)

    assert not compilation.ok
    assert len(compilation.errors) == 1
    error = compilation.errors[0]
    assert isinstance(error, E204TemporalInsufficiency)
    assert error.code == "E204"
    assert error.claim_ref == TIMING_CLAIM
    assert error.assertion_ref == TIMING_ASSERTION


def test_six_month_e204_names_the_90_day_window(template, usable_view) -> None:
    error = _compile(template, usable_view, SIX_MONTHS).for_claim(TIMING_CLAIM).errors[0]
    assert error.capability_window_days == 90
    assert error.required_window == SIX_MONTHS
    assert OKTA_LOG in error.message
    assert "window=90d" in error.message
    assert "90 days short of 181" in error.message
    assert error.render().startswith("E204  ")


def test_six_month_suggestion_degrades_honestly(template, usable_view) -> None:
    """Nothing usable covers 181 days (GitHub's 180 included) — so the
    compiler suggests nothing rather than something that would lie."""
    error = _compile(template, usable_view, SIX_MONTHS).for_claim(TIMING_CLAIM).errors[0]
    assert error.satisfiable_via == ()
    assert "No usable capability combination covers the period." in error.message
    assert GITHUB_AUDIT not in error.message  # 180d must not be offered for 181 days


def test_six_month_only_the_timing_claim_fails(template, usable_view) -> None:
    result = _compile(template, usable_view, SIX_MONTHS)
    for compilation in result.claims:
        if compilation.claim_ref == TIMING_CLAIM:
            assert not compilation.ok
        else:
            assert compilation.ok, compilation.errors
    plans = executable_collectors(result)
    assert plans and all(p.claim_ref != TIMING_CLAIM for p in plans)


def test_sixty_day_period_compiles_clean(template, usable_view) -> None:
    """Inside the Okta window the same assertion compiles against
    okta.system_log — the trap is the period, not the assertion."""
    assert period_days(SIXTY_DAYS) == 60
    result = _compile(template, usable_view, SIXTY_DAYS)
    assert result.ok
    assert result.errors == ()

    plans = executable_collectors(result)
    assert len(plans) == 6  # one plan per lane assertion
    timing_plan = next(p for p in plans if p.assertion_ref == TIMING_ASSERTION)
    assert timing_plan.entry_id == OKTA_LOG
    assert timing_plan.temporal.window_days == 90
    assert timing_plan.time_window == SIXTY_DAYS
    assert timing_plan.auth_scope.startswith("okta.logs.read")


def test_120_day_period_suggests_github_audit_log(template, usable_view) -> None:
    """Beyond Okta's 90 but inside GitHub's 180: E204 with a real,
    usable suggestion — satisfiable_via names the github.audit_log
    entry, never an entry the registry does not hold."""
    assert period_days(ONE_TWENTY_DAYS) == 120
    error = _compile(template, usable_view, ONE_TWENTY_DAYS).for_claim(TIMING_CLAIM).errors[0]
    assert isinstance(error, E204TemporalInsufficiency)
    assert error.capability_window_days == 90
    assert error.satisfiable_via == ((GITHUB_AUDIT,),)
    assert f"Satisfiable via: {GITHUB_AUDIT}" in error.message
    assert "Amend manifest?" in error.message


def test_suggestions_come_only_from_usable_entries(template, usable_view) -> None:
    """Every suggested entry id resolves through the usable view."""
    error = _compile(template, usable_view, ONE_TWENTY_DAYS).for_claim(TIMING_CLAIM).errors[0]
    for combo in error.satisfiable_via:
        for entry_id in combo:
            usable_view.get(entry_id)  # KeyError would fail the test
