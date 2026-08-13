"""Compile errors — the E-codes (TYP01; PRD-v3 §3).

Compile errors are the product behaving like its name: an assurance
program that cannot prove its claims **fails to compile** instead of
executing and lying (PRD-v3 §3). Each error is a closed, frozen model
(D-P1) carrying enough structure for a human to act on it, and
:meth:`CompileError.render` emits the PRD §3 error style — the code,
two spaces, then the human-actionable sentence:

    E204  TIMING assertion "..." requires historical transition
          timestamps; capability github.org_members.rest_v3 yields
          STATE only. ...

The three V1 codes mirror PRD §3's examples verbatim:

- **E204** temporal insufficiency — the assertion needs history the
  matched capability cannot yield for the required window; carries the
  required window, the insufficient capability's window, and
  ``satisfiable_via`` suggestions (combinations of *usable* registry
  entries that would cover the period — empty when nothing does, never
  a made-up path).
- **E117** missing capability — a population's derivation rule
  references a source with no usable capability entry.
- **E302** schema-version drift — an entry's observed schema_version
  differs from the ratified pin; re-ratify or pin.

STRICT purity lane (D-P3): no clock reads, no randomness, no
environment access — errors are values.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from aegis_sentinel.schema.canonical import AegisModel
from aegis_sentinel.schema.population import Period

MODULE_VERSION = "compile.errors@0.1.0"


class CompileError(AegisModel):
    """Base shape of every E-code.

    ``assertion_ref`` is ``None`` for claim-level errors (E117/E302,
    which attach to the claim through its populations and consulted
    entries) and set for assertion-level errors (E204).
    """

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    claim_ref: str = Field(min_length=1)
    assertion_ref: str | None = None

    def render(self) -> str:
        """PRD §3 error style: ``E204  <human-actionable message>``."""
        return f"{self.code}  {self.message}"


class E204TemporalInsufficiency(CompileError):
    """The assertion needs history the matched capability cannot yield.

    ``required_window`` is the population's period; ``capability_window_days``
    is the best insufficient candidate's event-history window (``None``
    when the best candidate yields no event history at all, e.g. STATE
    only — the PRD §3 github.members case). ``satisfiable_via`` lists
    capability-entry-id combinations, drawn ONLY from actually-usable
    registry entries, that would cover the period; empty means no usable
    combination does, and the message says so honestly.
    """

    code: Literal["E204"] = "E204"
    required_window: Period
    capability_window_days: int | None = Field(default=None, ge=1)
    satisfiable_via: tuple[tuple[str, ...], ...] = ()


class E117MissingCapability(CompileError):
    """A derivation-rule source has no usable capability entry.

    ``missing_source`` names the source exactly as the derivation rule
    references it — the break-glass poison's compile-time detection
    (tests/fixtures/mutations/breakglass-cloud-account/).
    """

    code: Literal["E117"] = "E117"
    missing_source: str = Field(min_length=1)


class E302SchemaVersionDrift(CompileError):
    """A consulted entry's schema_version drifted from the ratified pin."""

    code: Literal["E302"] = "E302"
    entry_id: str = Field(min_length=1)
    observed: str = Field(min_length=1)
    ratified: str = Field(min_length=1)
