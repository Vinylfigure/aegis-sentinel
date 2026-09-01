"""Capability Registry (SCH02, PRD-v3 §3): what evidence each system can
yield, as ratified data. Cartographer proposes drafts; a human ratifies
(lifecycle per D-L1); the Surveyor verifies; the compiler consumes only
what is FROZEN — unratified entries are mechanically unusable."""

from aegis_sentinel.capability.allowlist import SOURCE_UNREACHABLE, is_allowed_citation
from aegis_sentinel.capability.cartographer import CartographerRefusal, propose_entry
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
from aegis_sentinel.capability.surveyor import (
    Finding,
    ObservedCapability,
    ProbeRefusal,
    ProbeResult,
    run_probe,
)

REGISTRY_MODELS = (CapabilityEntry,)

__all__ = [
    "AccessMode",
    "CapabilityEntry",
    "CartographerRefusal",
    "Finding",
    "ObservedCapability",
    "Pagination",
    "PaginationMethod",
    "ProbeRefusal",
    "ProbeResult",
    "Provenance",
    "Registry",
    "REGISTRY_MODELS",
    "SOURCE_UNREACHABLE",
    "TemporalCoverage",
    "TemporalKind",
    "YieldedPopulation",
    "is_allowed_citation",
    "propose_entry",
    "run_probe",
]
