"""Set reconciliation (REC01): canonical-identity joins producing
first-class delta objects, never bare counts. The walking skeleton ships
the minimal one-population reconciler; the full six-bucket reconciler
lands with REC01."""

from aegis_sentinel.reconcile.minimal import (
    Member,
    ReconcileResult,
    apply_dispositions,
    canonical_email,
    reconcile_population,
)

__all__ = [
    "Member",
    "ReconcileResult",
    "apply_dispositions",
    "canonical_email",
    "reconcile_population",
]
