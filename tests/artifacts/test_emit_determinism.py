"""Demo-artifact emission: deterministic bytes, committed copies current.

``scripts/emit_demo_artifacts.py`` must produce byte-identical output on
every run (fixed engagement timestamps, sorted keys — D-P3: no wall
clock anywhere in the pipeline), and the committed
``artifacts/demo-engagement/`` files must match a fresh emission — the
same generated==committed discipline as the schema drift test.
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
FILENAMES = ("verdicts.json", "populations.json", "capability_registry.json")


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


def test_verdicts_artifact_shows_real_pass_unknown_and_compile_error() -> None:
    """The demo artifact carries a real PASS, a real UNKNOWN, and the E204."""
    payload = json.loads((COMMITTED / "verdicts.json").read_text(encoding="utf-8"))
    states = {v["assertion_ref"]: v["state"] for v in payload["verdicts"]}
    assert states == {"TERM-FEED.a": "PASS", "TERM-FEED.b": "UNKNOWN"}
    codes = [e["code"] for e in payload["compile_errors"]]
    assert codes == ["E204"]
    assert all(e["rendered"].startswith(e["code"]) for e in payload["compile_errors"])
    for verdict in payload["verdicts"]:
        assert verdict["record_hash"], "every emitted verdict record is sealed"


def test_populations_artifact_shows_discovered_ladder_state() -> None:
    payload = json.loads((COMMITTED / "populations.json").read_text(encoding="utf-8"))
    (entry,) = payload["populations"]
    assert entry["population"]["population_id"] == "TERM.terminations"
    assert entry["population"]["state"] == "DISCOVERED"
    assert entry["population"]["size"] == 15
    assert len(entry["members"]) == 15
    assert entry["basis_complete"] is True


def test_capability_registry_artifact_dumps_the_ratified_entries() -> None:
    payload = json.loads((COMMITTED / "capability_registry.json").read_text(encoding="utf-8"))
    entries = payload["entries"]
    assert len(entries) == 7
    assert all(e["provenance"]["ratified_by"] for e in entries)
    assert [e["entry_id"] for e in entries] == sorted(e["entry_id"] for e in entries)
