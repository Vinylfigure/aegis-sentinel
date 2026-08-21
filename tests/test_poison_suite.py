"""VAL02 acceptance: the six poison fixtures (PRD-v3 §6) through the
real pipeline — assurance defect detection rate == 100%, each case's
outcome class asserted individually, the five verdict states plus E117
all visibly distinct across the set, and the committed
artifacts/demo-engagement/{poisons,reconciliation,registry}.json pinned
byte-for-byte (same idiom as tests/test_demo_engagement_drift.py)."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts" / "demo-engagement"
ARTIFACT_NAMES = ("poisons.json", "reconciliation.json", "registry.json")
VALIDATOR = Draft202012Validator(
    json.loads((ROOT / "schemas" / "verdict-record.schema.json").read_text())
)


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_demo_engagement_val02", ROOT / "scripts" / "build_demo_engagement.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_demo_engagement_val02"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def regenerated() -> dict[str, str]:
    return load_builder().build_poison_artifacts()


@pytest.fixture(scope="module")
def poisons(regenerated) -> dict:
    return json.loads(regenerated["poisons.json"])


def case(poisons: dict, case_id: str) -> dict:
    return next(c for c in poisons["cases"] if c["id"] == case_id)


# --- artifact drift: regenerate == committed, byte for byte ---


@pytest.mark.parametrize("name", ARTIFACT_NAMES)
def test_regenerating_matches_committed_byte_for_byte(regenerated, name):
    committed = ARTIFACTS / name
    assert committed.exists(), f"run scripts/build_demo_engagement.py poisons and commit {name}"
    assert regenerated[name] == committed.read_text(), (
        f"artifacts/demo-engagement/{name} drifted — "
        "re-run scripts/build_demo_engagement.py poisons and commit"
    )


# --- the headline number ---


def test_assurance_defect_detection_rate_is_100_percent(poisons):
    detection = poisons["detection"]
    assert detection["total"] == 6
    assert detection["detected"] == 6
    assert detection["detection_rate"] == 1.0
    assert detection["misses"] == []
    # Recompute from the cases themselves — the summary can never drift
    # from the per-case records it claims to summarize.
    assert all(c["detected"] for c in poisons["cases"])
    assert all(c["actual_class"] == c["expected"] for c in poisons["cases"])
    # A silent PASS is a miss by construction: no case may expect PASS.
    assert all(c["expected"] != "PASS" for c in poisons["cases"])


# --- the six cases, each asserted individually ---


def test_case_1_contractor_absent_from_hris_is_unknown_population(poisons):
    c = case(poisons, "contractor-absent-from-hris")
    record = c["actual"]["record"]
    assert record["status"] == "UNKNOWN"
    assert record["unknown_cause"] == "UNKNOWN_POPULATION"
    assert c["evidence"] == {"bucket": "right_only", "member_ref": "email:mira.chen@example.com"}
    # The reconciler's bucket fed the evaluator: the verdict was recorded
    # against the blocked denominator, left of RECONCILED.
    assert record["support"]["field_values"]["population_state"] == "DISCOVERED"


def test_case_2_dormant_github_local_account_fails_naming_the_member(poisons):
    c = case(poisons, "dormant-github-local-account")
    record = c["actual"]["record"]
    assert record["status"] == "FAIL"
    assert record["support"]["field_values"]["residual_access_members"] == ["rhea.bell@example.com"]
    assert record["spec_id"] == "spec-poison-github-nonexistence-v1"


def test_case_3_breakglass_claim_is_an_e117_compile_error_before_collection(poisons):
    c = case(poisons, "breakglass-capability-missing")
    assert c["stage"] == "compile"
    assert c["actual"]["kind"] == "compile_error"
    (error,) = c["actual"]["errors"]
    assert error["code"] == "E117"
    assert "breakglass.config" in error["message"]
    assert "no usable capability entry" in error["message"]
    # Caught before collection: no verdict record exists for this claim.
    all_records = [r for group in poisons["verdict_records"].values() for r in group]
    assert not any(r["spec_id"].startswith("spec-poison-breakglass") for r in all_records)


def test_case_4_garbled_identity_join_is_unresolvable_then_unknown(poisons, regenerated):
    c = case(poisons, "garbled-identity-join")
    record = c["actual"]["record"]
    assert record["status"] == "UNKNOWN"
    assert record["unknown_cause"] == "UNKNOWN_EVIDENCE"
    assert record["record_id"].endswith("quinn.ash@example.com")
    # The reconciler surfaced the garbled source member as UNRESOLVABLE.
    board = json.loads(regenerated["reconciliation.json"])
    unresolvable_refs = [d["member_ref"] for d in board["buckets"]["unresolvable"]]
    assert unresolvable_refs == ["okta:00u9104"]


def test_case_5_delayed_revocation_is_a_timing_fail(poisons):
    c = case(poisons, "delayed-revocation")
    record = c["actual"]["record"]
    assert record["status"] == "FAIL"
    assert record["record_id"].endswith("omar.diaz@example.com")
    values = record["support"]["field_values"]
    assert values["constraint_business_days"] == 5
    assert values["elapsed_business_days"] >= 8  # the 8+ business-day poison
    assert values["elapsed_business_days"] == 9


def test_case_6_legitimate_exception_is_exception_never_a_silent_pass(poisons):
    c = case(poisons, "legitimate-exception")
    record = c["actual"]["record"]
    assert record["status"] == "EXCEPTION"
    assert record["record_id"].endswith("pia.voss@example.com")
    assert record["disposition_ref"] == "dispositions/poisons/pia-voss-phased-offboarding.json"


# --- distinctness and record hygiene across the whole set ---


def test_five_verdict_states_and_e117_all_visibly_distinct(poisons):
    all_records = [r for group in poisons["verdict_records"].values() for r in group]
    assert {r["status"] for r in all_records} == {
        "PASS",
        "FAIL",
        "UNKNOWN",
        "EXCLUDED",
        "EXCEPTION",
    }
    assert case(poisons, "breakglass-capability-missing")["actual_class"] == "E117"
    # Two distinct UNKNOWN why-codes across the poisons, never one blur.
    assert {c["actual_class"] for c in poisons["cases"]} == {
        "UNKNOWN:UNKNOWN_POPULATION",
        "FAIL",
        "E117",
        "UNKNOWN:UNKNOWN_EVIDENCE",
        "EXCEPTION",
    }


def test_every_emitted_verdict_record_is_schema_valid(poisons):
    all_records = [r for group in poisons["verdict_records"].values() for r in group]
    assert len(all_records) == 10  # 1 existence + 1 non-existence + 8 timing
    for record in all_records:
        errors = list(VALIDATOR.iter_errors(record))
        assert not errors, [e.message for e in errors]


# The claim/assertion each verdict_records group's evaluator was actually
# passed (scripts/build_demo_engagement.py's existence_claim/nonexistence_claim
# literals and the template-instantiated timing_claim: Assertion.id is
# f"{control_point_id}-{system}-{attribute}" per
# src/aegis_sentinel/lanes/template.py's instantiate()).
GROUP_TO_ASSERTION_TYPE = {
    "existence": "EXISTENCE",
    "non_existence": "NON-EXISTENCE",
    "timing": "TIMING",
}
CLAIM_ASSERTIONS = {
    "claim-poison-hris-existence": {"poison-am06-existence-A": "EXISTENCE"},
    "claim-poison-github-nonexistence": {"poison-am06-nonexistence-A": "NON-EXISTENCE"},
    "claim-cp-idp-deactivation-workday": {"cp-idp-deactivation-workday-B": "TIMING"},
}


def test_verdict_record_claim_and_assertion_ids_join_to_a_real_claim(poisons):
    """Q15/issue #53: claim_id/assertion_id are proven, not assumed — a
    dangling claim_id, an assertion_id absent from that claim, or an
    assertion of the wrong type for the group it was evaluated under all
    fail this test (same join-exactness pattern as PR #50's contract
    test)."""
    for group, records in poisons["verdict_records"].items():
        expected_type = GROUP_TO_ASSERTION_TYPE[group]
        for record in records:
            claim_id = record["claim_id"]
            assert claim_id in CLAIM_ASSERTIONS, (
                f"{record['record_id']}: dangling claim_id {claim_id}"
            )
            assertions = CLAIM_ASSERTIONS[claim_id]
            assertion_id = record["assertion_id"]
            assert assertion_id in assertions, (
                f"{record['record_id']}: assertion_id {assertion_id} is not among "
                f"claim {claim_id}'s assertions"
            )
            assert assertions[assertion_id] == expected_type, (
                f"{record['record_id']}: assertion {assertion_id} is "
                f"{assertions[assertion_id]}, not the evaluated {expected_type}"
            )


def test_excluded_and_exception_records_carry_their_refs(poisons):
    timing = poisons["verdict_records"]["timing"]
    excluded = next(r for r in timing if r["status"] == "EXCLUDED")
    assert excluded["ratification_ref"] == "boundary/poisons-v1#break-glass"
    exception = next(r for r in timing if r["status"] == "EXCEPTION")
    assert exception["disposition_ref"]


# --- the six-bucket board ---


def test_reconciliation_board_populates_all_six_buckets(regenerated):
    board = json.loads(regenerated["reconciliation.json"])
    buckets = board["buckets"]
    assert set(buckets) == {
        "intersection",
        "left_only",
        "right_only",
        "conflict",
        "unresolvable",
        "excluded",
    }
    assert all(len(deltas) >= 1 for deltas in buckets.values()), board["counts"]
    assert board["counts"] == {name: len(deltas) for name, deltas in buckets.items()}
    assert len(board["canonical_members"]) == 6
    # The ladder story: blocked at the first verdict, RECONCILED only
    # after every open delta carries a human disposition.
    assert board["ladder"]["at_first_verdict"] == "DISCOVERED"
    assert board["ladder"]["after_dispositions"] == "RECONCILED"
    assert set(board["ladder"]["blocked_by_open_deltas"]) == set(board["dispositions"])


def test_reconciliation_excluded_delta_is_born_dispositioned(regenerated):
    board = json.loads(regenerated["reconciliation.json"])
    (excluded,) = board["buckets"]["excluded"]
    assert excluded["member_ref"] == "email:vik.rao@example.com"
    assert excluded["disposition"] is not None  # D-9: the ratified exclusion IS the sign-off


# --- the registry artifact ---


def test_registry_artifact_carries_lifecycles_and_the_e117(regenerated):
    registry = json.loads(regenerated["registry.json"])
    lifecycles = {e["id"]: e["lifecycle"] for e in registry["entries"]}
    assert len(lifecycles) == 7
    assert lifecycles["okta.system_log"] == "frozen"
    assert lifecycles["slack.scim_users"] == "draft"
    # The demo ratifies workday in memory only; the artifact says so, and
    # the on-disk entry stays DRAFT (test_demo_engagement_drift pins it).
    assert lifecycles["workday.terminated_workers"] == "frozen"
    assert "DEMO-ONLY" in registry["note"]
    assert [e["code"] for e in registry["compile_errors"]] == ["E117"]
