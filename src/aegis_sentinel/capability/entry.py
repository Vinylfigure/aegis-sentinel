"""Capability entry schema per PRD-v3 §3 — one evidence surface of one
system, with provenance and a D-L1 lifecycle."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from aegis_sentinel.schema.enums import LifecycleState, PopulationType
from aegis_sentinel.schema.models import Base


class AccessMode(StrEnum):
    DIRECT_API = "direct-api"
    OFFICIAL_MCP = "official-mcp"
    COMMUNITY_MCP = "community-mcp"
    CUSTOM_ADAPTER = "custom-adapter"
    PLAYWRIGHT = "playwright"


class TemporalKind(StrEnum):
    STATE_ONLY = "state-only"
    EVENT_HISTORY = "event-history"
    FULL_HISTORY = "full-history"
    SNAPSHOT_CADENCE = "snapshot-cadence"


class PaginationMethod(StrEnum):
    CURSOR = "cursor"
    PAGE = "page"
    NONE = "none"


class YieldedPopulation(Base):
    type: PopulationType
    description: str = Field(min_length=1)
    attributes: tuple[str, ...] = Field(min_length=1)


class TemporalCoverage(Base):
    kind: TemporalKind
    window_days: int | None = Field(default=None, ge=1)
    cadence: str | None = None

    @model_validator(mode="after")
    def _kind_specifics(self):
        if (self.kind is TemporalKind.EVENT_HISTORY) != (self.window_days is not None):
            raise ValueError("window_days is required for event-history and forbidden otherwise")
        if (self.kind is TemporalKind.SNAPSHOT_CADENCE) != (self.cadence is not None):
            raise ValueError("cadence is required for snapshot-cadence and forbidden otherwise")
        return self


class Pagination(Base):
    method: PaginationMethod
    exhaustion_method: str = Field(min_length=1)


class Provenance(Base):
    """Who researched this, when, from what documentation — citations are
    the Cartographer's whole authority (it maps, never annexes)."""

    researched_by: str = Field(min_length=1)
    researched_at: datetime
    citations: tuple[str, ...] = Field(min_length=1)
    doc_version: str | None = None


class CapabilityEntry(Base):
    id: str = Field(min_length=1, pattern=r"^[a-z0-9_-]+\.[a-z0-9_.-]+$")
    system: str = Field(min_length=1)
    surface: str = Field(min_length=1)
    access_modes: tuple[AccessMode, ...] = Field(min_length=1)
    populations_yielded: tuple[YieldedPopulation, ...] = Field(min_length=1)
    temporal: TemporalCoverage
    join_keys: tuple[str, ...] = Field(min_length=1)
    auth_scope: str = Field(min_length=1)
    pagination: Pagination
    rate_limits: str | None = None
    history_caveats: tuple[str, ...] = ()
    provenance: Provenance
    ratified_by: str | None = None
    lifecycle: LifecycleState = LifecycleState.DRAFT

    @model_validator(mode="after")
    def _frozen_requires_ratifier(self):
        if self.lifecycle is not LifecycleState.DRAFT and not self.ratified_by:
            raise ValueError(
                "a FROZEN or SUPERSEDED entry requires ratified_by — "
                "ratification IS the freeze (D-L1)"
            )
        return self
