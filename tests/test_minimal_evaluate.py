"""Walking-skeleton evaluator tests: the emitted verdict record dict
validates against schemas/verdict-record.schema.json v0.1.0,
re-performance is byte-identical, the record_hash recomputes (volatile
fields nulled, D-P3), and the UNKNOWN paths carry their why-codes."""

import json
from datetime import date
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from aegis_sentinel.collectors.hris import TerminationRecord
from aegis_sentinel.evaluate.minimal import canonical_record_hash, evaluate_existence
from aegis_sentinel.schema import (
    Assertion,
    AssertionType,
    Claim,
    EvidenceQualityContract,
    Population,
)

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = Draft202012Validator(
    json.loads((ROOT / "schemas" / "verdict-record.schema.json").read_text())
)

MEMBERS = ("ada.grant@example.com", "ben.osei@example.com")
RECORDS = (
    TerminationRecord(
        worker_id="W-1001",
        full_name="Ada Grant",
        email="  ADA.Grant@example.com ",  # canonicalized at evaluation
        worker_type="employee",
        termination_date=date(2026, 7, 10),
    ),
    TerminationRecord(
        worker_id="W-1002",
        full_name="Ben Osei",
        email="ben.osei@example.com",
        worker_type="employee",
        termination_date=date(2026, 7, 24),
    ),
)


def contract(**overrides):
    data = json.loads((ROOT / "tests" / "fixtures" / "ontology" / "eqc_valid.json").read_text())
    data.update(overrides)
    return EvidenceQualityContract.model_validate(data)


def population(state="RECONCILED"):
    return Population.model_validate(
        {
            "id": "pop-termination-events",
            "name": "termination events",
            "type": "event",
            "definition": "terminations effective in the period",
            "authoritative_source": {
                "system": "workday",
                "role": "authoritative",
                "ref": "workday://termination-events",
            },
            "period": {"start": "2026-07-01T00:00:00Z", "end": "2026-12-31T00:00:00Z"},
            "state": state,
        }
    )


def claim(assertion_type=AssertionType.EXISTENCE):
    return Claim(
        id="claim-am06-termination-existence",
        statement="every termination exists in the HRIS feed",
        population_id="pop-termination-events",
        assertions=(
            Assertion(
                id="am06-hris-existence-A",
                attribute="A",
                type=assertion_type,
                description="a termination record exists for every canonical member",
            ),
        ),
    )


def evaluate(**overrides):
    kwargs = dict(
        claim=claim(),
        population=population(),
        canonical_members=MEMBERS,
        records=RECORDS,
        contract=contract(population_ref="pop-termination-events"),
        control_id="AM-06",
        record_id="vr-test-0001",
        run_id="run-test-0001",
        collected_at="2026-12-31T23:59:59Z",
        spec_id="spec-hris-terminations-v1",
        spec_hash="a" * 64,
        source="hris-termination-collector",
        source_version="0.1.0",
        completeness_ref="reconciliations/pop-termination-events.json",
        evidence_refs=("tests/fixtures/collectors/hris_terminations.json",),
        chain_prev=None,
        support_record_hashes=("b" * 64,),
    )
    kwargs.update(overrides)
    return evaluate_existence(**kwargs)


def assert_schema_valid(record):
    errors = list(VALIDATOR.iter_errors(record))
    assert not errors, [e.message for e in errors]


def test_pass_record_is_schema_valid():
    record = evaluate()
    assert record["status"] == "PASS"
    assert record["population_count"] == 2
    assert record["chain_prev"] is None
    assert_schema_valid(record)


def test_reperformance_is_byte_identical():
    first = json.dumps(evaluate(), sort_keys=True)
    second = json.dumps(evaluate(), sort_keys=True)
    assert first == second


def test_record_hash_recomputes_with_volatile_fields_nulled():
    record = evaluate()
    assert record["record_hash"] == canonical_record_hash(record)
    # and it is a hash OVER the content: any field change breaks it
    tampered = dict(record, status="FAIL")
    assert canonical_record_hash(tampered) != record["record_hash"]


def test_missing_member_fails_with_support():
    record = evaluate(canonical_members=(*MEMBERS, "gone.person@example.com"))
    assert record["status"] == "FAIL"
    assert record["support"]["field_values"]["missing_members"] == ["gone.person@example.com"]
    assert record["support"]["record_hashes"] == ["b" * 64]
    assert_schema_valid(record)


def test_unreconciled_population_is_unknown_population():
    record = evaluate(population=population(state="DISCOVERED"))
    assert record["status"] == "UNKNOWN"
    assert record["unknown_cause"] == "UNKNOWN_POPULATION"
    assert_schema_valid(record)


def test_unsupported_assertion_type_is_unknown_testability():
    unfit = contract(
        population_ref="pop-termination-events",
        supported_assertion_types=["STATE"],
    )
    record = evaluate(contract=unfit)
    assert record["status"] == "UNKNOWN"
    assert record["unknown_cause"] == "UNKNOWN_TESTABILITY"
    assert_schema_valid(record)


def test_claim_without_existence_assertion_is_a_usage_error():
    with pytest.raises(ValueError, match="no EXISTENCE assertion"):
        evaluate(claim=claim(assertion_type=AssertionType.STATE))


def test_population_mismatch_is_a_usage_error():
    other = population().model_copy(update={"id": "pop-other"})
    with pytest.raises(ValueError, match="scoped to"):
        evaluate(population=other)
