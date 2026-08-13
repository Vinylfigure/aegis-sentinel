"""E302 — schema-version drift against a ratified pin.

``schema_pins`` carries the schema_version each entry was ratified at.
A consulted entry whose observed version differs must refuse to compile
(re-ratify or pin); a matching pin is silent; a pin for an entry absent
from the usable view is inert (nothing observed, nothing drifts).
"""

from __future__ import annotations

from aegis_sentinel.compile import (
    E302SchemaVersionDrift,
    compile_program,
    executable_collectors,
)

from .conftest import SIXTY_DAYS, lane

OKTA_LOG = "okta.system_log.api_v1"
CURRENT = "capability-entry@0.1.0"
STALE = "capability-entry@0.0.9"

#: Claims whose populations consult okta.system_log (it yields the
#: okta-system-log source declared on TERM.terminations and on
#: TERM.identity-join).
CONSULTING_CLAIMS = {
    "TERM.feed-completeness",
    "TERM.timely-revocation",
    "TERM.attributability",
}


def _compile(template, usable_view, pins):
    populations, claims = lane(template, SIXTY_DAYS)
    return compile_program(claims, populations, usable_view, schema_pins=pins)


def test_matching_pin_is_silent(template, usable_view) -> None:
    result = _compile(template, usable_view, {OKTA_LOG: CURRENT})
    assert result.ok
    assert result.errors == ()


def test_drifted_pin_fails_with_e302(template, usable_view) -> None:
    result = _compile(template, usable_view, {OKTA_LOG: STALE})
    consulting = [c for c in result.claims if c.claim_ref in CONSULTING_CLAIMS]
    assert {c.claim_ref for c in consulting} == CONSULTING_CLAIMS
    for compilation in consulting:
        assert len(compilation.errors) == 1
        error = compilation.errors[0]
        assert isinstance(error, E302SchemaVersionDrift)
        assert error.code == "E302"
        assert error.entry_id == OKTA_LOG
        assert error.observed == CURRENT
        assert error.ratified == STALE
        assert error.assertion_ref is None
        assert "re-ratify or pin" in error.message
        assert error.render().startswith("E302  ")


def test_drift_gates_only_the_consulting_claims(template, usable_view) -> None:
    result = _compile(template, usable_view, {OKTA_LOG: STALE})
    for compilation in result.claims:
        assert compilation.ok == (compilation.claim_ref not in CONSULTING_CLAIMS), (
            compilation.claim_ref
        )
    plans = executable_collectors(result)
    assert plans  # the no-residual-access claims still compile
    assert all(p.claim_ref not in CONSULTING_CLAIMS for p in plans)


def test_pin_for_absent_entry_is_inert(template, usable_view) -> None:
    """A pinned entry the usable view does not hold observes nothing —
    no drift, no error (its absence surfaces as E117 if a derivation
    rule actually needs it)."""
    result = _compile(template, usable_view, {"siem.archive.v1": "capability-entry@0.0.1"})
    assert result.ok
