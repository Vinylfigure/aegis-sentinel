"""Capability registry (SCH02) — entry schema + versioned store, PRD-v3 §3.

Each entry describes one evidence surface of one system; the registry
is the compiler's map of what evidence each system can yield. Entries
are drafts until a human ratifies them (``provenance.ratified_by``);
``Registry.usable()`` is the only compiler-facing view and excludes
drafts mechanically.

Pydantic v2, closed and frozen everywhere (D-P1); registry artifacts
are JSON on disk (D-P2). No LLM, no network, no clock reads.
"""

from aegis_sentinel.capability.entry import (
    SCHEMA_VERSION,
    AccessMode,
    CapabilityEntry,
    Pagination,
    PaginationMethod,
    PopulationAttributes,
    PopulationYield,
    Provenance,
    SourceCitation,
    TemporalShape,
    TemporalShapeKind,
)
from aegis_sentinel.capability.registry import Registry, RegistryView

__all__ = [
    # entry
    "SCHEMA_VERSION",
    "AccessMode",
    "TemporalShapeKind",
    "TemporalShape",
    "PopulationYield",
    "PopulationAttributes",
    "SourceCitation",
    "Provenance",
    "PaginationMethod",
    "Pagination",
    "CapabilityEntry",
    # registry
    "Registry",
    "RegistryView",
]
