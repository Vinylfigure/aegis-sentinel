"""Drift gate for the committed demo-engagement artifact: regenerating
via scripts/build_demo_engagement.py must be byte-identical to the
committed artifacts/demo-engagement/verdicts.json, and every record in
it must validate against the verdict-record schema. The compile gate
inside build() also proves the claim compiles before evaluation."""

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


def test_regenerating_matches_committed_byte_for_byte():
    assert ARTIFACT.exists(), "run scripts/build_demo_engagement.py and commit the artifact"
    assert load_builder().build() == ARTIFACT.read_text(), (
        "artifacts/demo-engagement/verdicts.json drifted — "
        "re-run scripts/build_demo_engagement.py and commit"
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
    (record,) = json.loads(ARTIFACT.read_text())
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
