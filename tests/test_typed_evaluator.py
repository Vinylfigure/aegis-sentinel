"""EVAL01 typed-evaluator tests: D-P4 business-day math at week
boundaries, all five verdict states emitted distinctly from one crafted
fixture set, byte-identical re-performance (D-P3), hash-chained
schema-valid records, and NON-EXISTENCE residual-access detection."""

import json
from datetime import date
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from aegis_sentinel.evaluate.minimal import canonical_record_hash
from aegis_sentinel.evaluate.typed import (
    MemberTimeline,
    business_days_between,
    evaluate_non_existence,
    evaluate_timing,
)
from aegis_sentinel.schema import (
    Assertion,
    AssertionType,
    Claim,
    EvidenceQualityContract,
    Population,
    TimingConstraint,
)

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = Draft202012Validator(
    json.loads((ROOT / "schemas" / "verdict-record.schema.json").read_text())
)

CONSTRAINT = TimingConstraint(days=5, business_days=True)

# 2026-07-10 is a Friday; 2026-07-13 the following Monday.
EVENTS = (
    # Fri → Mon = 1 business day → PASS
    MemberTimeline(
        member="ada@example.com",
        termination_date=date(2026, 7, 10),
        revocation_date=date(2026, 7, 13),
    ),
    # Fri → Wed week after next = 8 business days → FAIL
    MemberTimeline(
        member="ben@example.com",
        termination_date=date(2026, 7, 10),
        revocation_date=date(2026, 7, 22),
    ),
    # no revocation event in the covered window → UNKNOWN(UNKNOWN_EVIDENCE)
    MemberTimeline(member="cleo@example.com", termination_date=date(2026, 7, 10)),
    # late, but carries a dispositioned exception → EXCEPTION
    MemberTimeline(
        member="dora@example.com",
        termination_date=date(2026, 7, 10),
        revocation_date=date(2026, 8, 14),
    ),
    # boundary-excluded service account → EXCLUDED
    MemberTimeline(
        member="svc-deploy@example.com",
        termination_date=date(2026, 7, 10),
    ),
)
EXCEPTIONS = {"dora@example.com": "dispositions/dora-break-glass.json"}
EXCLUSIONS = {"svc-deploy@example.com": "boundary/v3#service-accounts"}


def contract(**overrides):
    data = json.loads((ROOT / "tests" / "fixtures" / "ontology" / "eqc_valid.json").read_text())
    data["population_ref"] = "pop-termination-events"
    data["supported_assertion_types"] = ["TIMING", "NON-EXISTENCE", "EXISTENCE"]
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


def claim(assertion_type=AssertionType.TIMING):
    timing = CONSTRAINT if assertion_type is AssertionType.TIMING else None
    return Claim(
        id="claim-am06-revocation-timing",
        statement="access is revoked within 5 business days of termination",
        population_id="pop-termination-events",
        assertions=(
            Assertion(
                id="am06-timing-A",
                attribute="A",
                type=assertion_type,
                description="revocation within the constraint window",
                timing=timing,
            ),
        ),
    )


def evaluate(**overrides):
    kwargs = dict(
        events=EVENTS,
        constraint=CONSTRAINT,
        claim=claim(),
        population=population(),
        contract=contract(),
        exception_dispositions=EXCEPTIONS,
        boundary_exclusions=EXCLUSIONS,
        control_id="AM-06",
        record_id_prefix="vr-timing-0001",
        run_id="run-test-0001",
        collected_at="2026-12-31T23:59:59Z",
        spec_id="spec-am06-timing-v1",
        spec_hash="a" * 64,
        source="typed-evaluator",
        source_version="0.1.0",
        completeness_ref="reconciliations/pop-termination-events.json",
        evidence_refs=("tests/fixtures/reconcile_engine/sources.json",),
        chain_prev=None,
        support_record_hashes=("b" * 64,),
    )
    kwargs.update(overrides)
    return evaluate_timing(kwargs.pop("events"), kwargs.pop("constraint"), **kwargs)


def assert_schema_valid(record):
    errors = list(VALIDATOR.iter_errors(record))
    assert not errors, [e.message for e in errors]


# --- business-day math (D-P4: Mon-Fri, no holiday calendar in V1) ---


def test_friday_to_monday_is_one_business_day():
    assert business_days_between(date(2026, 7, 10), date(2026, 7, 13)) == 1


def test_friday_to_next_friday_is_five_business_days():
    assert business_days_between(date(2026, 7, 10), date(2026, 7, 17)) == 5


def test_same_day_is_zero_business_days():
    assert business_days_between(date(2026, 7, 10), date(2026, 7, 10)) == 0


def test_weekend_start_counts_only_following_business_days():
    # Sat → Mon: only Monday counts
    assert business_days_between(date(2026, 7, 11), date(2026, 7, 13)) == 1
    # Sat → Sun: nothing counts
    assert business_days_between(date(2026, 7, 11), date(2026, 7, 12)) == 0
    # Sun → next Fri: Mon..Fri
    assert business_days_between(date(2026, 7, 12), date(2026, 7, 17)) == 5


def test_friday_into_weekend_is_zero_business_days():
    assert business_days_between(date(2026, 7, 10), date(2026, 7, 12)) == 0


def test_reversed_interval_is_an_error():
    with pytest.raises(ValueError, match="precedes"):
        business_days_between(date(2026, 7, 13), date(2026, 7, 10))


# --- evaluate_timing ---


def test_all_five_verdict_states_emitted_distinctly():
    """One crafted fixture set → PASS, FAIL, UNKNOWN, EXCEPTION and
    EXCLUDED, each on the right member, each schema-valid (D-V1: the
    states are never interchangeable)."""
    records = evaluate()
    by_member = {r["record_id"].removeprefix("vr-timing-0001-"): r for r in records}
    statuses = {member: r["status"] for member, r in by_member.items()}
    assert statuses == {
        "ada@example.com": "PASS",
        "ben@example.com": "FAIL",
        "cleo@example.com": "UNKNOWN",
        "dora@example.com": "EXCEPTION",
        "svc-deploy@example.com": "EXCLUDED",
    }
    assert len({r["status"] for r in records}) == 5
    for record in records:
        assert_schema_valid(record)
    assert by_member["ben@example.com"]["support"]["field_values"]["elapsed_business_days"] == 8
    assert by_member["cleo@example.com"]["unknown_cause"] == "UNKNOWN_EVIDENCE"
    assert by_member["dora@example.com"]["disposition_ref"] == EXCEPTIONS["dora@example.com"]
    assert (
        by_member["svc-deploy@example.com"]["ratification_ref"]
        == (EXCLUSIONS["svc-deploy@example.com"])
    )


def test_reperformance_is_byte_identical():
    first = json.dumps(evaluate(), sort_keys=True)
    second = json.dumps(evaluate(), sort_keys=True)
    assert first == second


def test_records_are_hash_chained_in_member_order():
    records = evaluate(chain_prev="c" * 64)
    assert records[0]["chain_prev"] == "c" * 64
    for prev, record in zip(records, records[1:]):
        assert record["chain_prev"] == prev["record_hash"]
    for record in records:
        assert record["record_hash"] == canonical_record_hash(record)


def test_revocation_on_or_before_termination_passes_with_zero_elapsed():
    early = (
        MemberTimeline(
            member="ada@example.com",
            termination_date=date(2026, 7, 10),
            revocation_date=date(2026, 7, 9),
        ),
    )
    (record,) = evaluate(events=early)
    assert record["status"] == "PASS"


def test_unreconciled_population_is_unknown_population_per_member():
    records = evaluate(population=population(state="DISCOVERED"))
    assert {r["status"] for r in records} == {"UNKNOWN"}
    assert {r["unknown_cause"] for r in records} == {"UNKNOWN_POPULATION"}
    for record in records:
        assert_schema_valid(record)


def test_contract_without_timing_support_is_unknown_testability():
    unfit = contract(supported_assertion_types=["STATE"])
    records = evaluate(contract=unfit)
    assert {r["unknown_cause"] for r in records} == {"UNKNOWN_TESTABILITY"}
    for record in records:
        assert_schema_valid(record)


def test_claim_without_timing_assertion_is_a_usage_error():
    with pytest.raises(ValueError, match="no TIMING assertion"):
        evaluate(claim=claim(assertion_type=AssertionType.STATE))


def test_population_mismatch_is_a_usage_error():
    other = population().model_copy(update={"id": "pop-other"})
    with pytest.raises(ValueError, match="scoped to"):
        evaluate(population=other)


def test_calendar_day_constraint_is_not_implemented_in_v1():
    with pytest.raises(ValueError, match="business-day"):
        evaluate(constraint=TimingConstraint(days=5, business_days=False))


def test_non_canonical_member_identity_is_rejected():
    with pytest.raises(ValueError, match="canonical"):
        MemberTimeline(member="  ADA@Example.com ", termination_date=date(2026, 7, 10))


# --- evaluate_non_existence ---


def evaluate_residual(**overrides):
    kwargs = dict(
        access_holders=("ada@example.com", "  BEN.left@Example.COM ", "mira@example.com"),
        terminated=("ben.left@example.com", "cleo@example.com"),
        claim=claim(assertion_type=AssertionType.NON_EXISTENCE),
        population=population(),
        contract=contract(),
        control_id="AM-06",
        record_id="vr-nonexist-0001",
        run_id="run-test-0001",
        collected_at="2026-12-31T23:59:59Z",
        spec_id="spec-am06-nonexistence-v1",
        spec_hash="a" * 64,
        source="typed-evaluator",
        source_version="0.1.0",
        completeness_ref="reconciliations/pop-termination-events.json",
        evidence_refs=("tests/fixtures/reconcile_engine/sources.json",),
        chain_prev=None,
        support_record_hashes=("b" * 64,),
    )
    kwargs.update(overrides)
    return evaluate_non_existence(kwargs.pop("access_holders"), kwargs.pop("terminated"), **kwargs)


def test_residual_access_fails_naming_members():
    record = evaluate_residual()
    assert record["status"] == "FAIL"
    assert record["support"]["field_values"]["residual_access_members"] == ["ben.left@example.com"]
    assert_schema_valid(record)


def test_no_residual_access_passes():
    record = evaluate_residual(access_holders=("ada@example.com", "mira@example.com"))
    assert record["status"] == "PASS"
    assert record["record_hash"] == canonical_record_hash(record)
    assert_schema_valid(record)


def test_non_existence_reperformance_is_byte_identical():
    first = json.dumps(evaluate_residual(), sort_keys=True)
    second = json.dumps(evaluate_residual(), sort_keys=True)
    assert first == second
