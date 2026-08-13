"""Collectors — the deterministic retrieval lane (COL01+; PRD-v3 §4).

Collectors retrieve per evidence contract, hash, and record; they never
interpret, summarize, or decide. No LLM import anywhere in this package
(docs/HANDOFF.md §3); enforced by tests/test_verdict_path_purity.py.
"""

from aegis_sentinel.collectors.base import (
    CollectionSnapshot,
    Collector,
    FixtureTransport,
    PageRequest,
    Transport,
    supported_assertion_types,
)
from aegis_sentinel.collectors.hris import (
    HrisTerminationsCollector,
    TerminationEvent,
)

__all__ = [
    # base
    "PageRequest",
    "Transport",
    "FixtureTransport",
    "CollectionSnapshot",
    "Collector",
    "supported_assertion_types",
    # hris (COL01)
    "HrisTerminationsCollector",
    "TerminationEvent",
]
