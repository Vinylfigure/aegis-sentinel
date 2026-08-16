"""SCH01 acceptance: round-trip serialization, conditional validators,
and fixture triads (invalid fixtures REJECTED — never loosen the model
to make a failing invalid-fixture test pass)."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from aegis_sentinel.schema import (
    ONTOLOGY_MODELS,
    Assertion,
    AssertionType,
    Claim,
    EvidenceQualityContract,
    Population,
    Verdict,
    VerdictState,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ontology"


def load(name):
    return (FIXTURES / name).read_text()


VALID = {
    Population: "population_valid.json",
    EvidenceQualityContract: "eqc_valid.json",
    Verdict: "verdict_unknown_valid.json",
}

INVALID = [
    (Population, "population_invalid_extra_field.json", "extra"),
    (Population, "population_invalid_two_derivations.json", "exactly one"),
    (EvidenceQualityContract, "eqc_invalid_missing_property.json", "temporal_validity"),
    (Verdict, "verdict_invalid_unknown_missing_why.json", "unknown_why"),
]


@pytest.mark.parametrize("model", VALID)
def test_roundtrip_is_byte_identical(model):
    first = model.model_validate_json(load(VALID[model]))
    dumped = first.model_dump_json()
    second = model.model_validate_json(dumped)
    assert second.model_dump_json() == dumped
    assert second == first


@pytest.mark.parametrize(("model", "name", "needle"), INVALID)
def test_invalid_fixture_is_rejected(model, name, needle):
    with pytest.raises(ValidationError) as err:
        model.model_validate_json(load(name))
    assert needle in str(err.value)


def test_all_models_are_frozen_and_closed():
    for model in ONTOLOGY_MODELS:
        assert model.model_config.get("frozen") is True, model.__name__
        assert model.model_config.get("extra") == "forbid", model.__name__


def test_timing_assertion_requires_constraint():
    base = {"id": "a1", "type": "TIMING", "description": "revoked within 5 business days"}
    with pytest.raises(ValidationError):
        Assertion.model_validate(base)
    ok = Assertion.model_validate(base | {"timing": {"days": 5, "business_days": True}})
    assert ok.timing.days == 5
    with pytest.raises(ValidationError):
        Assertion.model_validate(
            {"id": "a2", "type": "STATE", "description": "x", "timing": {"days": 5}}
        )


def test_claim_requires_population_and_assertions():
    with pytest.raises(ValidationError):
        Claim.model_validate(
            {"id": "c1", "statement": "s", "population_id": "p1", "assertions": []}
        )


def test_verdict_excluded_and_exception_conditionals():
    with pytest.raises(ValidationError):
        Verdict.model_validate({"state": "EXCLUDED"})
    ok = Verdict.model_validate({"state": "EXCLUDED", "ratification_ref": "ratifications/r1.json"})
    assert ok.state is VerdictState.EXCLUDED
    with pytest.raises(ValidationError):
        Verdict.model_validate({"state": "EXCEPTION"})
    ok = Verdict.model_validate(
        {"state": "EXCEPTION", "exception_disposition_ref": "dispositions/d1.json"}
    )
    assert ok.state is VerdictState.EXCEPTION
    with pytest.raises(ValidationError):
        Verdict.model_validate({"state": "PASS", "unknown_why": "UNKNOWN_EVIDENCE"})


def test_eqc_declares_supported_assertion_types():
    eqc = EvidenceQualityContract.model_validate_json(load("eqc_valid.json"))
    assert eqc.supports(AssertionType.STATE)
    assert not eqc.supports(AssertionType.TIMING)


def test_fixture_files_are_valid_json():
    for path in FIXTURES.glob("*.json"):
        json.loads(path.read_text())
