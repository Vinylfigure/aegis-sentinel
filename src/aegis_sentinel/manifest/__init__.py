"""Ratified scope snapshots + PROPOSED_SCOPE_CHANGE (SCH03).

Invariant 6 in code: discovery proposes, a human ratifies, the manifest
versions. Lifecycle per D-L1 — ratification IS the freeze.
"""

from aegis_sentinel.manifest.snapshot import (
    CollectorGrant,
    ManifestBlocks,
    ManifestSnapshot,
    ProposedScopeChange,
    diff,
    genesis,
    ratify,
)

MANIFEST_MODELS = (ManifestSnapshot, ProposedScopeChange)

__all__ = [
    "CollectorGrant",
    "ManifestBlocks",
    "ManifestSnapshot",
    "ProposedScopeChange",
    "diff",
    "genesis",
    "ratify",
    "MANIFEST_MODELS",
]
