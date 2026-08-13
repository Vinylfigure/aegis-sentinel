"""Canonical serialization and hashing for Aegis ontology objects.

Salvaged from the prior scaffold's ``src/evidence.py`` (canonical_json +
compute_record_hash semantics: SHA-256 over the canonical JSON form with
the record's own volatile fields nulled, computed before any
interpretation). The prior module also carried the D-1 hash-chain
(seal/verify_chain); chain mechanics land with the evidence store, not
here — this module keeps only the canonical-form contract that every
hash in the system derives from (docs/DECISIONS.md D-P3).

Pure stdlib + pydantic. No LLM, no network, no clock reads.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict

MODULE_VERSION = "schema.canonical@0.1.0"


class AegisModel(BaseModel):
    """Base class for every Aegis ontology model.

    Closed and immutable per docs/DECISIONS.md D-P1: ``extra="forbid"``
    mirrors the prior scaffold's ``additionalProperties: false``
    convention (an invalid record must be rejected, never absorbed);
    ``frozen=True`` makes constructed records immutable so a validated
    object cannot drift from its hash.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")


def canonical_json(obj: Any) -> bytes:
    """Deterministic serialization: sorted keys, compact separators, UTF-8.

    Same canonical form as the prior scaffold's ``evidence.canonical_json``
    (sorted keys, no whitespace drift), emitted as UTF-8 bytes.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sha256_canonical(
    model_or_dict: BaseModel | dict[str, Any],
    volatile_fields_nulled: list[str] | None = None,
) -> str:
    """SHA-256 hex digest of the canonical JSON form.

    ``volatile_fields_nulled`` lists top-level fields set to ``None``
    before hashing — the prior scaffold's ``compute_record_hash`` nulled
    ``record_hash`` so a record's hash never depends on itself; callers
    here name their volatile fields explicitly.
    """
    if isinstance(model_or_dict, BaseModel):
        body: dict[str, Any] = model_or_dict.model_dump(mode="json")
    else:
        body = dict(model_or_dict)
    for field in volatile_fields_nulled or []:
        body[field] = None
    return hashlib.sha256(canonical_json(body)).hexdigest()
