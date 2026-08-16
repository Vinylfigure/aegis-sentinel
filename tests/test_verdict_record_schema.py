"""Contract tests for schemas/verdict-record.schema.json.

The closed schema is the guarantee: it accepts a well-formed PASS, FAIL,
and UNKNOWN record, enforces each status's conditional requirements, and
rejects any record carrying a field it does not know about.
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schemas" / "verdict-record.schema.json").read_text())
FIXTURES = ROOT / "tests" / "fixtures" / "verdict_records"

VALIDATOR = Draft202012Validator(SCHEMA)


def load(name):
    return json.loads((FIXTURES / name).read_text())


def test_schema_itself_is_valid():
    Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("name", ["pass.json", "fail.json", "unknown.json"])
def test_valid_fixture_is_accepted(name):
    errors = list(VALIDATOR.iter_errors(load(name)))
    assert not errors, [e.message for e in errors]


def test_extra_property_is_rejected():
    errors = list(VALIDATOR.iter_errors(load("invalid_extra_property.json")))
    assert errors, "closed schema accepted an unknown field — additionalProperties broke"
    assert any("auditor_note" in e.message for e in errors)


def test_unknown_without_cause_is_rejected():
    record = load("unknown.json")
    del record["unknown_cause"]
    assert not VALIDATOR.is_valid(record)


def test_fail_without_support_is_rejected():
    record = load("fail.json")
    del record["support"]
    assert not VALIDATOR.is_valid(record)


def test_excluded_requires_ratification_ref():
    record = load("pass.json")
    record["status"] = "EXCLUDED"
    assert not VALIDATOR.is_valid(record)
    record["ratification_ref"] = "ratifications/2026-08-scope.json"
    assert VALIDATOR.is_valid(record)


def test_exception_requires_disposition_ref():
    record = load("pass.json")
    record["status"] = "EXCEPTION"
    record["message"] = "legitimate exception: documented break-glass account"
    assert not VALIDATOR.is_valid(record)
    record["disposition_ref"] = "dispositions/2026-08-break-glass.json"
    assert VALIDATOR.is_valid(record)


def test_retired_statuses_are_rejected():
    for status in ("skipped", "NOT_APPLICABLE", "basis_missing"):
        record = load("pass.json")
        record["status"] = status
        assert not VALIDATOR.is_valid(record), f"{status} accepted"


def test_garbage_collected_at_is_rejected():
    record = load("pass.json")
    record["collected_at"] = "not-a-date"
    assert not VALIDATOR.is_valid(record)
