"""Capability entry — one evidence surface of one system (PRD-v3 §3).

The compiler needs to know, per system, what evidence the system is
capable of yielding before it can judge fitness. Each entry describes
one surface: access modes, populations yielded, attributes exposed,
temporal shape, join keys, least-privilege auth scope, pagination and
its exhaustion method, rate limits, history caveats, and provenance.

Provenance carries the ratification gate: a Cartographer (LLM lane)
proposal is a draft until a human ratifies it — ``ratified_by`` is
``None`` until then, and :meth:`Registry.usable
<aegis_sentinel.capability.registry.Registry.usable>` mechanically
excludes drafts from the compiler-facing view. The agent maps the
territory; it does not annex it (PRD-v3 §3).

Pure stdlib + pydantic (D-P1/D-P3): no LLM, no network, no clock reads.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from aegis_sentinel.schema.canonical import AegisModel
from aegis_sentinel.schema.population import PopulationType

MODULE_VERSION = "capability.entry@0.1.0"

#: Const-pinned on every entry (E302-class drift is detectable, PRD-v3 §3).
SCHEMA_VERSION = "capability-entry@0.1.0"

URL_PATTERN = r"^https?://\S+$"


class AccessMode(str, Enum):
    """How a surface can be reached (PRD-v3 §3 access_modes).

    Third-party MCP servers are an access mode *recorded* here —
    verdict-path collection defaults to DIRECT_API; MCP modes are for
    the LLM lane, or verdict-path only when pinned (PRD-v3 §3, "MCP,
    precisely positioned").
    """

    DIRECT_API = "DIRECT_API"
    OFFICIAL_MCP = "OFFICIAL_MCP"
    COMMUNITY_MCP = "COMMUNITY_MCP"
    CUSTOM_ADAPTER = "CUSTOM_ADAPTER"
    PLAYWRIGHT = "PLAYWRIGHT"


class TemporalShapeKind(str, Enum):
    """What history a surface can yield — the E204 axis (PRD-v3 §3)."""

    STATE_ONLY = "STATE_ONLY"
    EVENT_HISTORY = "EVENT_HISTORY"
    FULL_HISTORY = "FULL_HISTORY"
    SNAPSHOT_CADENCE = "SNAPSHOT_CADENCE"


class TemporalShape(AegisModel):
    """Temporal shape with its window: ``event-history(window=90d)``.

    Constructor-enforced iff: EVENT_HISTORY carries ``window_days``
    (a bounded log is only meaningful with its bound — Okta's 90-day
    System Log is the canonical trap); every other kind must leave it
    unset (a window on STATE_ONLY would be a claim the shape cannot
    honor).
    """

    kind: TemporalShapeKind
    window_days: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _window_iff_event_history(self) -> "TemporalShape":
        if self.kind is TemporalShapeKind.EVENT_HISTORY and self.window_days is None:
            raise ValueError("EVENT_HISTORY requires window_days (the retention bound)")
        if self.kind is not TemporalShapeKind.EVENT_HISTORY and self.window_days is not None:
            raise ValueError(
                f"window_days is only meaningful for EVENT_HISTORY, not {self.kind.value}"
            )
        return self


class PopulationYield(AegisModel):
    """One population a surface can yield: its type and name (PRD-v3 §3)."""

    type: PopulationType
    name: str = Field(min_length=1)


class PopulationAttributes(AegisModel):
    """Fields the surface exposes for one yielded population."""

    population_name: str = Field(min_length=1)
    fields_exposed: tuple[str, ...] = Field(min_length=1)


class SourceCitation(AegisModel):
    """One vendor-doc citation grounding the entry (Cartographer output)."""

    url: str = Field(pattern=URL_PATTERN)
    title: str = Field(min_length=1)


class Provenance(AegisModel):
    """Who researched the entry, from what, and who ratified it.

    ``ratified_by`` is the mechanical gate: ``None`` means draft, and
    drafts never reach the compiler (Registry.usable). Cartographer
    proposals arrive with citations and ``ratified_by=None``; only a
    human sets the field.
    """

    researched_by: str = Field(min_length=1)
    researched_at: datetime
    source_citations: tuple[SourceCitation, ...] = Field(min_length=1)
    doc_version: str = Field(min_length=1)
    ratified_by: str | None = Field(default=None, min_length=1)


class PaginationMethod(str, Enum):
    """Pagination mechanics of the surface (PRD-v3 §3)."""

    CURSOR = "CURSOR"
    PAGE = "PAGE"
    NONE = "NONE"


class Pagination(AegisModel):
    """Pagination method plus how a collector proves exhaustion.

    Exhaustion is named even for NONE (e.g. "single response carries
    the full set; compare returned count to reported total") — the
    population quality property depends on it (PRD-v3 §2).
    """

    method: PaginationMethod
    exhaustion_method: str = Field(min_length=1)


class CapabilityEntry(AegisModel):
    """One evidence surface of one system, fully described (PRD-v3 §3).

    Constructor-enforced: every ``attributes`` block must name a
    declared yielded population (attributes cannot be smuggled onto a
    population the surface does not yield).
    """

    entry_id: str = Field(min_length=1)
    system: str = Field(min_length=1)
    surface: str = Field(min_length=1)
    access_modes: tuple[AccessMode, ...] = Field(min_length=1)
    populations_yielded: tuple[PopulationYield, ...] = Field(min_length=1)
    attributes: tuple[PopulationAttributes, ...] = ()
    temporal: TemporalShape
    join_keys: tuple[str, ...] = Field(min_length=1)
    auth_scope: str = Field(min_length=1)  # minimum read scope, least-privilege, named
    pagination: Pagination
    rate_limits: str = Field(min_length=1)
    history_caveats: tuple[str, ...] = ()
    provenance: Provenance
    schema_version: Literal["capability-entry@0.1.0"] = SCHEMA_VERSION

    @property
    def is_ratified(self) -> bool:
        """True iff a human has ratified this entry (compiler-usable)."""
        return self.provenance.ratified_by is not None

    @model_validator(mode="after")
    def _attributes_reference_yielded_populations(self) -> "CapabilityEntry":
        yielded = {p.name for p in self.populations_yielded}
        strays = [a.population_name for a in self.attributes if a.population_name not in yielded]
        if strays:
            raise ValueError(
                "attributes reference population(s) this surface does not yield: "
                + ", ".join(strays)
            )
        return self
