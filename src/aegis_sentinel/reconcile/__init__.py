"""Reconcile — set-based population reconciliation (REC01 lane).

The walking skeleton ships the deterministic single-source identity
pass; REC01 generalizes to N-source canonical-identity join with the
six delta buckets as first-class objects. No LLM import anywhere in
this package (docs/HANDOFF.md §3).
"""

from aegis_sentinel.reconcile.minimal import (
    ReconciliationResult,
    SourceMembers,
    reconcile_population,
)

__all__ = [
    "SourceMembers",
    "ReconciliationResult",
    "reconcile_population",
]
