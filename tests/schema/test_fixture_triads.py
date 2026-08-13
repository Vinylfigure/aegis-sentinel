"""Fixture triads: valid fixtures validate; invalid/ fixtures are REJECTED.

Harness shape lifted from the prior scaffold's tests/test_contract.py
(fixture triads; invalid fixtures MUST be rejected). A failing
invalid-fixture test must never be fixed by loosening a schema —
that inverts the invariant (docs/invariants.md).

Fixture naming: tests/fixtures/schema/<kebab-model>--<case>.json and
tests/fixtures/schema/invalid/<kebab-model>--<case>.json; the kebab
model name before "--" selects the pydantic model.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

import aegis_sentinel.schema as schema_pkg

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "schema"


def _kebab(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", name).lower()


MODEL_BY_KEBAB: dict[str, type[BaseModel]] = {
    _kebab(name): obj
    for name in schema_pkg.__all__
    if isinstance(obj := getattr(schema_pkg, name), type)
    and issubclass(obj, BaseModel)
    and obj is not schema_pkg.AegisModel  # abstract base; no fixtures of its own
}


def _model_for(path: Path) -> type[BaseModel]:
    key = path.name.split("--")[0].removesuffix(".json")
    assert key in MODEL_BY_KEBAB, f"fixture {path.name} names no known model {key!r}"
    return MODEL_BY_KEBAB[key]


VALID = sorted(FIXTURES.glob("*.json"))
INVALID = sorted((FIXTURES / "invalid").glob("*.json"))


def test_fixture_dirs_populated() -> None:
    assert VALID, "no valid fixtures found"
    assert INVALID, "no invalid fixtures found"


def test_every_model_has_a_valid_fixture() -> None:
    covered = {p.name.split("--")[0].removesuffix(".json") for p in VALID}
    missing = set(MODEL_BY_KEBAB) - covered
    assert not missing, f"models without a valid fixture: {sorted(missing)}"


@pytest.mark.parametrize("path", VALID, ids=[p.name for p in VALID])
def test_valid_fixture_validates(path: Path) -> None:
    model = _model_for(path)
    instance = model.model_validate_json(path.read_text())
    assert isinstance(instance, model)


@pytest.mark.parametrize("path", INVALID, ids=[p.name for p in INVALID])
def test_invalid_fixture_rejected(path: Path) -> None:
    model = _model_for(path)
    data = json.loads(path.read_text())
    with pytest.raises(ValidationError):
        model.model_validate(data)
