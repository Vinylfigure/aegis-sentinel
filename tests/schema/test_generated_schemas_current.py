"""generated==committed: schemas/ must match a fresh in-memory export.

A mismatch means someone changed a model without re-running
scripts/export_schemas.py (or hand-edited a committed schema). Either
way the build fails until the two agree (D-P1 drift test).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = ROOT / "schemas"


def _load_export_module():
    spec = importlib.util.spec_from_file_location(
        "export_schemas", ROOT / "scripts" / "export_schemas.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GENERATED: dict[str, str] = _load_export_module().generate()


def test_no_missing_or_stale_files() -> None:
    committed = {p.name for p in SCHEMAS_DIR.glob("*.schema.json")}
    assert committed == set(GENERATED), (
        f"missing on disk: {sorted(set(GENERATED) - committed)}; "
        f"stale on disk: {sorted(committed - set(GENERATED))} "
        "(run scripts/export_schemas.py and commit)"
    )


@pytest.mark.parametrize("fname", sorted(GENERATED), ids=sorted(GENERATED))
def test_committed_schema_matches_generated(fname: str) -> None:
    committed = (SCHEMAS_DIR / fname).read_text(encoding="utf-8")
    assert committed == GENERATED[fname], (
        f"schemas/{fname} drifted from the models (run scripts/export_schemas.py and commit)"
    )
