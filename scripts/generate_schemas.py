"""Regenerate schemas/ontology/*.schema.json from the pydantic models.

D-P1: generated model_json_schema() output is committed, with a
generated==committed drift test (tests/test_schema_drift.py). Run me
after any model change; the test fails until you do.
"""

import json
import sys
from pathlib import Path

from aegis_sentinel.capability import REGISTRY_MODELS
from aegis_sentinel.manifest import MANIFEST_MODELS
from aegis_sentinel.schema import ONTOLOGY_MODELS

ALL_MODELS = ONTOLOGY_MODELS + REGISTRY_MODELS + MANIFEST_MODELS
OUT = Path(__file__).resolve().parent.parent / "schemas" / "ontology"


def snake(name: str) -> str:
    return "".join(f"_{c.lower()}" if c.isupper() else c for c in name).lstrip("_")


def render(model) -> str:
    return json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for model in ALL_MODELS:
        path = OUT / f"{snake(model.__name__)}.schema.json"
        path.write_text(render(model))
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
