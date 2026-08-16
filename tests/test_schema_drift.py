"""D-P1 drift gate: the committed schemas/ontology/*.schema.json must be
byte-identical to what the models generate right now. Fails until
scripts/generate_schemas.py is re-run after a model change."""

import importlib.util
import sys
from pathlib import Path

from aegis_sentinel.capability import REGISTRY_MODELS
from aegis_sentinel.lanes import LANE_MODELS
from aegis_sentinel.manifest import MANIFEST_MODELS
from aegis_sentinel.schema import ONTOLOGY_MODELS

ROOT = Path(__file__).resolve().parent.parent


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generate_schemas", ROOT / "scripts" / "generate_schemas.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_schemas"] = module
    spec.loader.exec_module(module)
    return module


def test_generated_matches_committed():
    gen = load_generator()
    stale = []
    for model in ONTOLOGY_MODELS + REGISTRY_MODELS + MANIFEST_MODELS + LANE_MODELS:
        path = gen.OUT / f"{gen.snake(model.__name__)}.schema.json"
        if not path.exists() or path.read_text() != gen.render(model):
            stale.append(path.name)
    assert not stale, f"run scripts/generate_schemas.py — drifted: {stale}"


def test_no_orphan_committed_schemas():
    gen = load_generator()
    expected = {
        f"{gen.snake(m.__name__)}.schema.json"
        for m in ONTOLOGY_MODELS + REGISTRY_MODELS + MANIFEST_MODELS + LANE_MODELS
    }
    actual = {p.name for p in gen.OUT.glob("*.schema.json")}
    assert actual == expected
