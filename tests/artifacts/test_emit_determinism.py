"""Demo-artifact emission: deterministic bytes, committed copies current.

``scripts/emit_demo_artifacts.py`` must produce byte-identical output on
every run (fixed engagement timestamps, sorted keys — D-P3: no wall
clock anywhere in the pipeline), and the committed
``artifacts/demo-engagement/`` files must match a fresh emission — the
same generated==committed discipline as the schema drift test.

Content gates (VAL02 acceptance, docs/HANDOFF.md §4): all FIVE verdict
states present and distinct; the compile-error exhibits (six-month E204
and break-glass E117); the negative-space delta; the ladder states
including the identity-join population blocked at DISCOVERED with open
deltas; the ten-stage proof graph in the frontend's shape.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "scripts" / "emit_demo_artifacts.py"
COMMITTED = REPO_ROOT / "artifacts" / "demo-engagement"
FILENAMES = (
    "verdicts.json",
    "populations.json",
    "reconciliation.json",
    "capability_registry.json",
    "manifest.json",
    "proof_graph.json",
)

#: The frontend contract's node kinds (web/src/lib/types/artifacts.ts
#: PROOF_NODE_KINDS) — the ten lineage stages.
PROOF_NODE_KINDS = {
    "commitment",
    "requirement",
    "claim",
    "population",
    "source",
    "reconciliation",
    "contract",
    "snapshot",
    "assertion",
    "verdict",
}


def emit_to(out_dir: Path) -> None:
    subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out_dir)],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="module")
def emitted(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    one = tmp_path_factory.mktemp("emit-one")
    two = tmp_path_factory.mktemp("emit-two")
    emit_to(one)
    emit_to(two)
    return one, two


def _load(name: str) -> dict | list:
    return json.loads((COMMITTED / name).read_text(encoding="utf-8"))


def test_emitting_twice_is_byte_identical(emitted: tuple[Path, Path]) -> None:
    one, two = emitted
    for name in FILENAMES:
        assert (one / name).read_bytes() == (two / name).read_bytes(), name


def test_committed_artifacts_are_current(emitted: tuple[Path, Path]) -> None:
    one, _ = emitted
    for name in FILENAMES:
        assert (COMMITTED / name).read_bytes() == (one / name).read_bytes(), (
            f"artifacts/demo-engagement/{name} is stale; "
            "re-run scripts/emit_demo_artifacts.py and commit the result"
        )


def test_verdicts_artifact_carries_all_five_states_and_both_exhibits() -> None:
    """VAL02: five states distinct; E204 + E117 exhibits; every record sealed."""
    payload = _load("verdicts.json")
    states = {v["assertion_ref"]: v["state"] for v in payload["verdicts"]}
    assert states == {
        "TERM-FEED.a": "PASS",
        "TERM-FEED.b": "UNKNOWN",
        "TERM-TIMING.a": "FAIL",
        "TERM-JOIN.a": "UNKNOWN",
        "TERM-GITHUB.a": "FAIL",
        "TERM-SLACK.a": "EXCEPTION",
        "TERM-CORP-IT.a": "EXCLUDED",
    }
    assert set(states.values()) == {"PASS", "FAIL", "UNKNOWN", "EXCLUDED", "EXCEPTION"}
    codes = [e["code"] for e in payload["compile_errors"]]
    assert codes == ["E204", "E117"]
    assert all(e["rendered"].startswith(e["code"]) for e in payload["compile_errors"])
    for verdict in payload["verdicts"]:
        assert verdict["record_hash"], "every emitted verdict record is sealed"
    by_ref = {v["assertion_ref"]: v for v in payload["verdicts"]}
    assert by_ref["TERM-SLACK.a"]["disposition_ref"] == "DISP-2026-114"
    assert by_ref["TERM-CORP-IT.a"]["ratification_ref"] == "RAT-2026-031"
    assert "marcus.webb" in by_ref["TERM-TIMING.a"]["message"]
    assert "9 business day" in by_ref["TERM-TIMING.a"]["message"]
    assert "bm-legacy-bot" in by_ref["TERM-GITHUB.a"]["message"]


def test_populations_artifact_shows_the_ladder() -> None:
    payload = _load("populations.json")
    states = {p["population_id"]: p["state"] for p in payload["populations"]}
    assert states == {
        "TERM.terminations": "RATIFIED",
        "TERM.github.accounts": "DISCOVERED",
        "TERM.gcp.accounts": "DEFINED",  # blocked behind its E117
        "TERM.slack.accounts": "DISCOVERED",
        "TERM.identity-join": "DISCOVERED",
    }
    join = next(p for p in payload["populations"] if p["population_id"] == "TERM.identity-join")
    assert join["open_deltas"], "identity-join is blocked at DISCOVERED by open deltas"
    assert all(d["owner"] for d in join["open_deltas"])


def test_reconciliation_artifact_carries_negative_space_and_dispositions() -> None:
    payload = _load("reconciliation.json")
    by_ref = {r["population_ref"]: r for r in payload["reconciliations"]}
    join = by_ref["TERM.identity-join"]
    deltas = {d["member_key"]: d for d in join["deltas"]}
    # The contractor poison: present downstream, absent from the
    # authoritative source — the negative-space delta.
    blake = deltas["ctr.blake.morgan@example-vendor.com"]
    assert blake["bucket"] == "left_only"
    assert "hris-termination-feed" in blake["sources_absent"]
    assert blake["disposition"] is None
    # The failed identity join: the maiden-name orphan is unresolvable.
    assert any(
        d["bucket"] == "unresolvable" and "dana.kowalski" in d["member_key"] for d in join["deltas"]
    )
    # The legitimate exception: pre-ratified disposition → excluded bucket.
    kai = deltas["CT-2044"]
    assert kai["bucket"] == "excluded"
    assert kai["disposition_ref"] == "DISP-2026-114"
    assert kai["disposition"]["owner"] and kai["disposition"]["review_date"]
    # Counts are diagnostic, never evidence — but they must be present.
    assert join["source_counts"] and join["canonical_identity_keys"]


def test_manifest_artifact_is_the_ratified_snapshot_summary() -> None:
    payload = _load("manifest.json")
    assert payload["ratified_by"] == "vinylfigure (Ratifier)"
    assert payload["manifest_version"] == "v1-skeleton"
    assert payload["snapshot_hash"]
    assert payload["summary"]["verdict_states_present"] == [
        "EXCEPTION",
        "EXCLUDED",
        "FAIL",
        "PASS",
        "UNKNOWN",
    ]
    assert payload["summary"]["compile_error_codes"] == ["E204", "E117"]


def test_proof_graph_is_the_ten_stage_lineage_in_frontend_shape() -> None:
    payload = _load("proof_graph.json")
    assert isinstance(payload, list) and len(payload) == 1
    graph = payload[0]
    assert set(graph) == {"verdict_ref", "nodes", "edges"}
    kinds = [n["kind"] for n in graph["nodes"]]
    assert set(kinds) == PROOF_NODE_KINDS, "all ten lineage stages present"
    node_ids = {n["node_id"] for n in graph["nodes"]}
    for edge in graph["edges"]:
        assert set(edge) == {"from", "to", "relation"}
        assert edge["from"] in node_ids and edge["to"] in node_ids
    verdict_node = next(n for n in graph["nodes"] if n["kind"] == "verdict")
    assert graph["verdict_ref"] == verdict_node["ref"]
    assert verdict_node["label"].startswith("FAIL")


def test_capability_registry_artifact_dumps_the_ratified_entries() -> None:
    payload = _load("capability_registry.json")
    entries = payload["entries"]
    assert len(entries) == 7
    assert all(e["provenance"]["ratified_by"] for e in entries)
    assert [e["entry_id"] for e in entries] == sorted(e["entry_id"] for e in entries)
