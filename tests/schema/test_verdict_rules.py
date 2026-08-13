"""Verdict cross-field rules: invalid verdicts must be unconstructible.

Each of the five states is distinctly constructible; each rule
violation raises at construction (salvaged discipline from the prior
scaffold's src/verdict.py: the schema conditionals mirrored in code).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from aegis_sentinel.schema import (
    D7_FAMILY,
    D7Family,
    UnknownWhyCode,
    VerdictRecord,
    VerdictState,
)

SHA_A = "a" * 64
SHA_B = "b" * 64

BASE = dict(
    claim_ref="claim-termination-revocation",
    assertion_ref="AM-06.a",
    population_ref="pop-terminated-employees",
    manifest_version="v1",
    snapshot_hash=SHA_A,
    contract_hash=SHA_B,
    evaluated_at=datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc),
)


def make(**overrides) -> VerdictRecord:
    return VerdictRecord(**{**BASE, **overrides})


# --- all five states distinctly constructible -------------------------------


def test_pass_constructible() -> None:
    v = make(state=VerdictState.PASS)
    assert v.state is VerdictState.PASS


def test_fail_constructible() -> None:
    v = make(state=VerdictState.FAIL, message="one revocation exceeded five business days")
    assert v.state is VerdictState.FAIL


def test_unknown_constructible() -> None:
    v = make(
        state=VerdictState.UNKNOWN,
        why_code=UnknownWhyCode.UNKNOWN_EVIDENCE,
        d7_family=D7Family.BASIS_MISSING,
    )
    assert v.state is VerdictState.UNKNOWN


def test_excluded_constructible() -> None:
    v = make(state=VerdictState.EXCLUDED, ratification_ref="ratification/0001")
    assert v.state is VerdictState.EXCLUDED


def test_exception_constructible() -> None:
    v = make(state=VerdictState.EXCEPTION, disposition_ref="disposition/0001")
    assert v.state is VerdictState.EXCEPTION


def test_five_states_are_five() -> None:
    assert {s.value for s in VerdictState} == {"PASS", "FAIL", "UNKNOWN", "EXCLUDED", "EXCEPTION"}


# --- each violating construction raises -------------------------------------


def test_unknown_without_why_code_raises() -> None:
    with pytest.raises(ValidationError, match="why_code"):
        make(state=VerdictState.UNKNOWN)


def test_unknown_with_inconsistent_d7_family_raises() -> None:
    with pytest.raises(ValidationError, match="d7_family"):
        make(
            state=VerdictState.UNKNOWN,
            why_code=UnknownWhyCode.UNKNOWN_OWNER,
            d7_family=D7Family.BASIS_MISSING,
        )


def test_excluded_without_ratification_ref_raises() -> None:
    with pytest.raises(ValidationError, match="ratification_ref"):
        make(state=VerdictState.EXCLUDED)


def test_exception_without_disposition_ref_raises() -> None:
    with pytest.raises(ValidationError, match="disposition_ref"):
        make(state=VerdictState.EXCEPTION)


def test_fail_without_message_raises() -> None:
    with pytest.raises(ValidationError, match="message"):
        make(state=VerdictState.FAIL)


def test_pass_with_why_code_raises() -> None:
    with pytest.raises(ValidationError):
        make(state=VerdictState.PASS, why_code=UnknownWhyCode.UNKNOWN_EVIDENCE)


def test_pass_with_ratification_ref_raises() -> None:
    with pytest.raises(ValidationError):
        make(state=VerdictState.PASS, ratification_ref="ratification/0001")


def test_pass_with_disposition_ref_raises() -> None:
    with pytest.raises(ValidationError):
        make(state=VerdictState.PASS, disposition_ref="disposition/0001")


# --- D-U1 mapping and sealing ------------------------------------------------


def test_d7_family_mapping_is_du1() -> None:
    assert D7_FAMILY == {
        D7Family.BASIS_MISSING: UnknownWhyCode.UNKNOWN_EVIDENCE,
        D7Family.IDENTITY_FUZZY: UnknownWhyCode.UNKNOWN_POPULATION,
        D7Family.NO_BASIS_ANYWHERE: UnknownWhyCode.UNKNOWN_TESTABILITY,
    }


def test_sealed_record_hash_reproducible() -> None:
    v = make(state=VerdictState.PASS).sealed()
    assert v.record_hash == v.compute_record_hash()
    # Sealing is deterministic: same inputs, same hash.
    assert v.record_hash == make(state=VerdictState.PASS).sealed().record_hash
