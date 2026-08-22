"""Drift gate for the committed demo-engagement artifact.

verdicts.json is now the consolidated roster (Q17, issue #58): the
walking-skeleton record build()/main() alone would write, plus the ten
poison records build_poison_artifacts() adds — whole-file byte-identity
against the committed artifact is pinned by
tests/test_poison_suite.py's parametrized drift test (which regenerates
via build_poison_artifacts(), and that function calls build() itself),
since running main() alone no longer reproduces the committed file
byte-for-byte. This module instead pins that the walking-skeleton
record itself survives into the merged artifact unchanged, and that
every record in it validates against the verdict-record schema. The
compile gate inside build() also proves the claim compiles before
evaluation."""

import importlib.util
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT = ROOT / "artifacts" / "demo-engagement" / "verdicts.json"


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_demo_engagement", ROOT / "scripts" / "build_demo_engagement.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_demo_engagement"] = module
    spec.loader.exec_module(module)
    return module


def test_walking_skeleton_record_survives_into_the_merged_artifact():
    """verdicts.json is the consolidated roster (Q17, issue #58) written by
    the poisons entrypoint, not build()'s bare output — but build()'s one
    walking-skeleton record must still appear inside it, byte-for-byte
    (as a value, not as the whole file's literal bytes)."""
    assert ARTIFACT.exists(), "run scripts/build_demo_engagement.py and commit the artifact"
    (skeleton_record,) = json.loads(load_builder().build())
    committed = json.loads(ARTIFACT.read_text())
    match = next((r for r in committed if r["record_id"] == skeleton_record["record_id"]), None)
    assert match is not None, (
        f"{skeleton_record['record_id']} missing from artifacts/demo-engagement/verdicts.json — "
        "re-run scripts/build_demo_engagement.py poisons and commit"
    )
    assert match == skeleton_record, (
        "the walking-skeleton record inside artifacts/demo-engagement/verdicts.json drifted — "
        "re-run scripts/build_demo_engagement.py poisons and commit"
    )


def test_committed_artifact_records_are_schema_valid():
    validator = Draft202012Validator(
        json.loads((ROOT / "schemas" / "verdict-record.schema.json").read_text())
    )
    records = json.loads(ARTIFACT.read_text())
    assert records, "the demo engagement must carry at least one real verdict record"
    for record in records:
        errors = list(validator.iter_errors(record))
        assert not errors, [e.message for e in errors]


def test_demo_verdict_is_a_real_pass_over_the_reconciled_population():
    """verdicts.json now carries the full 11-record roster (Q17, issue #58);
    pick out the walking-skeleton record by its fixed id rather than
    assuming it's the file's only entry."""
    records = json.loads(ARTIFACT.read_text())
    record = next(r for r in records if r["record_id"] == load_builder().RECORD_ID)
    assert record["status"] == "PASS"
    assert record["population_id"] == "pop-termination-events"
    assert record["population_count"] == 12
    assert record["chain_prev"] is None  # first record in the chain
    assert record["control_id"] == "AM-06"
    assert record["claim_id"] == "claim-am06-termination-existence"
    assert record["assertion_id"] == "am06-hris-existence-A"


def test_on_disk_workday_entry_is_still_draft():
    """The demo build ratifies a COPY in memory only — the committed
    registry entry must remain DRAFT until the Owner's real act."""
    entry = json.loads(
        (ROOT / "registry" / "capabilities" / "workday.terminated_workers.json").read_text()
    )
    assert entry["lifecycle"] == "draft"
    assert entry["ratified_by"] is None
