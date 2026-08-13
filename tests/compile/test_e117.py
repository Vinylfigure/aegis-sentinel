"""E117 — missing capability for a derivation-rule source.

The break-glass poison's compile-time detection (docs/PRD-v3.md §6,
tests/fixtures/mutations/breakglass-cloud-account/): the GCP accounts
population's derivation rule references ``breakglass.config``, a source
with no capability entry anywhere in the registry, so the claim over
that population must refuse to compile — before any collector could
run. The error payload aligns with the poison fixture's
``expected_outcome.json``.
"""

from __future__ import annotations

import json

from aegis_sentinel.compile import (
    E117MissingCapability,
    compile_program,
    executable_collectors,
)
from aegis_sentinel.schema import DerivationRule, Source, SourceRole

from .conftest import ROOT, SIXTY_DAYS, lane

POISONED_POPULATION = "TERM.gcp.accounts"
POISONED_CLAIM = "TERM.gcp.no-residual-access"
MISSING_SOURCE = "breakglass.config"
FIXTURE = ROOT / "tests" / "fixtures" / "mutations" / "breakglass-cloud-account"


def _poison(populations):
    """Seed the break-glass mutation: the GCP accounts population's
    derivation rule gains a breakglass.config source no capability
    entry yields."""
    out = []
    for population in populations:
        if population.population_id == POISONED_POPULATION:
            rule = population.derivation_rule
            population = population.model_copy(
                update={
                    "sources": population.sources
                    + (Source(source_id=MISSING_SOURCE, role=SourceRole.CONTRIBUTING),),
                    "derivation_rule": DerivationRule(
                        rule_text=rule.rule_text
                        + "; union break-glass accounts enumerated by breakglass.config",
                        source_refs=rule.source_refs + (MISSING_SOURCE,),
                    ),
                }
            )
        out.append(population)
    return out


def _compile_poisoned(template, usable_view):
    populations, claims = lane(template, SIXTY_DAYS)
    return compile_program(claims, _poison(populations), usable_view)


def test_e117_names_the_missing_source(template, usable_view) -> None:
    result = _compile_poisoned(template, usable_view)
    compilation = result.for_claim(POISONED_CLAIM)
    assert len(compilation.errors) == 1
    error = compilation.errors[0]
    assert isinstance(error, E117MissingCapability)
    assert error.code == "E117"
    assert error.missing_source == MISSING_SOURCE
    assert error.claim_ref == POISONED_CLAIM
    assert error.assertion_ref is None  # population-level, not assertion-level
    assert POISONED_POPULATION in error.message
    assert f"capability entry missing for {MISSING_SOURCE}" in error.message
    assert error.render().startswith("E117  ")


def test_e117_fires_only_on_the_poisoned_claim(template, usable_view) -> None:
    result = _compile_poisoned(template, usable_view)
    for compilation in result.claims:
        if compilation.claim_ref == POISONED_CLAIM:
            assert not compilation.ok
        else:
            assert compilation.ok, compilation.errors


def test_e117_gates_the_poisoned_claim_entirely(template, usable_view) -> None:
    """The claim's NON_EXISTENCE assertion matches a capability just
    fine — and still executes nothing, because the claim carries an
    unresolved E-code (compile integrity, PRD-v3 §7)."""
    result = _compile_poisoned(template, usable_view)
    compilation = result.for_claim(POISONED_CLAIM)
    assert compilation.plans  # matched...
    assert not compilation.ok  # ...but blocked
    plans = executable_collectors(result)
    assert all(p.claim_ref != POISONED_CLAIM for p in plans)
    assert len(plans) == 6  # the other five claims' assertions still compile


def test_error_payload_aligns_with_poison_fixture(template, usable_view) -> None:
    """The mutation fixture's expected outcome is exactly what the real
    compiler produces: COMPILE_ERROR / E117."""
    expected = json.loads((FIXTURE / "expected_outcome.json").read_text(encoding="utf-8"))
    error = _compile_poisoned(template, usable_view).for_claim(POISONED_CLAIM).errors[0]
    assert expected["detection"] == "COMPILE_ERROR"
    assert error.code == expected["e_code"]
    assert expected["verdict_state"] is None and expected["why_code"] is None
