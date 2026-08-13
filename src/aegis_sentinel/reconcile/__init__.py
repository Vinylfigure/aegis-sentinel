"""Reconcile — set-based population reconciliation (REC01 lane).

Canonical-identity join (``identity.py``), six-bucket set operations
with first-class delta objects (``setops.py``), disposition-gated
ladder transitions (``deltas.py``), and the population-level entry
point (``minimal.py``). The Reconciler may never disposition deltas —
that is a human act it only records (PRD-v3 §4). No LLM import
anywhere in this package (docs/HANDOFF.md §3).
"""

from aegis_sentinel.reconcile.deltas import (
    OpenDeltasError,
    open_delta_refs,
    to_ratified,
    to_reconciled,
)
from aegis_sentinel.reconcile.identity import (
    GLOBAL_KEYS,
    KEY_PRECEDENCE,
    WORKFORCE_KINDS,
    IdentityCluster,
    KeyValue,
    MemberKind,
    SourceMember,
    build_clusters,
    email_domain,
)
from aegis_sentinel.reconcile.minimal import (
    ReconciliationResult,
    SourceMembers,
    reconcile_population,
)
from aegis_sentinel.reconcile.setops import (
    BUCKETS,
    DELTA_BUCKETS,
    ClassifiedSets,
    DeltaDisposition,
    DeltaObject,
    RatifiedDeltaDisposition,
    classify,
)

__all__ = [
    # identity (REC01)
    "KEY_PRECEDENCE",
    "GLOBAL_KEYS",
    "WORKFORCE_KINDS",
    "MemberKind",
    "KeyValue",
    "SourceMember",
    "IdentityCluster",
    "build_clusters",
    "email_domain",
    # setops (REC01)
    "BUCKETS",
    "DELTA_BUCKETS",
    "DeltaDisposition",
    "DeltaObject",
    "RatifiedDeltaDisposition",
    "ClassifiedSets",
    "classify",
    # entry point
    "SourceMembers",
    "ReconciliationResult",
    "reconcile_population",
    # ladder transitions (REC01)
    "OpenDeltasError",
    "open_delta_refs",
    "to_reconciled",
    "to_ratified",
]
