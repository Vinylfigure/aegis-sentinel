"""Disposition: how every answer resolves — nothing exits silently.

PRD-v3 §1 (thesis): every component's answer to the universal question
set resolves to a disposition — implemented locally, inherited, shared,
vendor-managed, compensating, or N/A with rationale. The
mountain-of-N/As objection dissolves at this layer precisely because
N/A must carry its rationale: never a silent N/A (docs/HANDOFF.md §2).
"""

from __future__ import annotations

from enum import Enum

from pydantic import model_validator

from aegis_sentinel.schema.canonical import AegisModel

MODULE_VERSION = "schema.disposition@0.1.0"


class DispositionValue(str, Enum):
    """The six dispositions (PRD-v3 §1)."""

    IMPLEMENTED_LOCALLY = "IMPLEMENTED_LOCALLY"
    INHERITED = "INHERITED"
    SHARED = "SHARED"
    VENDOR_MANAGED = "VENDOR_MANAGED"
    COMPENSATING = "COMPENSATING"
    NA_WITH_RATIONALE = "NA_WITH_RATIONALE"


class Disposition(AegisModel):
    """A disposition, with rationale mandatory for N/A — never silent."""

    value: DispositionValue
    rationale: str | None = None

    @model_validator(mode="after")
    def _na_needs_rationale(self) -> "Disposition":
        if self.value is DispositionValue.NA_WITH_RATIONALE and not self.rationale:
            raise ValueError("NA_WITH_RATIONALE requires a rationale — never a silent N/A")
        return self
