#!/usr/bin/env python3
"""Export committed JSON Schemas for every public ontology model.

Writes ``model_json_schema()`` output for each public pydantic model in
``aegis_sentinel.schema`` and ``aegis_sentinel.capability`` (SCH02) to
``schemas/<kebab-name>.schema.json``
(sorted keys, two-space indent, trailing newline). The committed files
are kept honest by tests/schema/test_generated_schemas_current.py
(generated==committed, per D-P1).

Run from the repo venv: ``python scripts/export_schemas.py``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel

import aegis_sentinel.capability as capability_pkg
import aegis_sentinel.schema as schema_pkg

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "schemas"

PACKAGES = (schema_pkg, capability_pkg)


def kebab(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", name).lower()


def generate() -> dict[str, str]:
    """Return {filename: file text} for every public model."""
    out: dict[str, str] = {}
    for pkg in PACKAGES:
        for name in pkg.__all__:
            obj = getattr(pkg, name)
            if not (isinstance(obj, type) and issubclass(obj, BaseModel)):
                continue
            if obj is schema_pkg.AegisModel:  # abstract base, no fields of its own
                continue
            text = json.dumps(obj.model_json_schema(), indent=2, sort_keys=True) + "\n"
            out[f"{kebab(name)}.schema.json"] = text
    return out


def main() -> None:
    SCHEMAS_DIR.mkdir(exist_ok=True)
    generated = generate()
    for fname, text in sorted(generated.items()):
        (SCHEMAS_DIR / fname).write_text(text, encoding="utf-8")
        print(f"wrote schemas/{fname}")
    stale = {p.name for p in SCHEMAS_DIR.glob("*.schema.json")} - set(generated)
    for fname in sorted(stale):
        print(f"WARNING: schemas/{fname} has no generating model (stale?)")


if __name__ == "__main__":
    main()
