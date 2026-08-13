"""Round-trip: construct -> dump JSON -> validate -> identical canonical form.

Byte-identical via canonical.py, so the canonical form (and therefore
every hash derived from it) survives serialization.
"""

from __future__ import annotations

import pytest

from aegis_sentinel.schema import canonical_json, sha256_canonical

from .samples import SAMPLES


@pytest.mark.parametrize(
    "sample", SAMPLES, ids=[f"{type(s).__name__}-{i}" for i, s in enumerate(SAMPLES)]
)
def test_roundtrip_canonical_identical(sample) -> None:
    dumped = sample.model_dump_json()
    revived = type(sample).model_validate_json(dumped)
    assert canonical_json(sample.model_dump(mode="json")) == canonical_json(
        revived.model_dump(mode="json")
    )
    assert sha256_canonical(sample) == sha256_canonical(revived)


@pytest.mark.parametrize(
    "sample", SAMPLES, ids=[f"{type(s).__name__}-{i}" for i, s in enumerate(SAMPLES)]
)
def test_roundtrip_equality(sample) -> None:
    revived = type(sample).model_validate_json(sample.model_dump_json())
    assert revived == sample
