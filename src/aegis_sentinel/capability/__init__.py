"""Capability Registry (SCH02, PRD-v3 §3): what evidence each system can
yield, as ratified data. Cartographer proposes drafts; a human ratifies
(lifecycle per D-L1); the Surveyor verifies; the compiler consumes only
what is FROZEN — unratified entries are mechanically unusable."""

from aegis_sentinel.capability.entry import (
    AccessMode,
    CapabilityEntry,
    Pagination,
    PaginationMethod,
    Provenance,
    TemporalCoverage,
    TemporalKind,
    YieldedPopulation,
)
from aegis_sentinel.capability.registry import Registry

REGISTRY_MODELS = (CapabilityEntry,)

__all__ = [
    "AccessMode",
    "CapabilityEntry",
    "Pagination",
    "PaginationMethod",
    "Provenance",
    "Registry",
    "REGISTRY_MODELS",
    "TemporalCoverage",
    "TemporalKind",
    "YieldedPopulation",
]
