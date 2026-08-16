"""Assurance Manifest snapshots, diffs, and the ratification act.

Blocks per PRD-v3 §6 and docs/manifest-reconciliation.md: boundary /
populations / claims / evidence_contracts / capabilities / collectors
(+permissions) / tests — all by id (pointers, never payloads). Clock
values are explicit function inputs (D-P3).
"""

from datetime import datetime

from pydantic import Field, model_validator

from aegis_sentinel.schema.enums import LifecycleState
from aegis_sentinel.schema.models import Base


class CollectorGrant(Base):
    """A collector and the permissions the ratified scope grants it —
    a deployment fact promoted into reviewed data."""

    id: str = Field(min_length=1)
    permissions: tuple[str, ...] = Field(min_length=1)


class ManifestBlocks(Base):
    boundary: tuple[str, ...] = ()
    populations: tuple[str, ...] = ()
    claims: tuple[str, ...] = ()
    evidence_contracts: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    collectors: tuple[CollectorGrant, ...] = ()
    tests: tuple[str, ...] = ()


class ManifestSnapshot(Base):
    version: int = Field(ge=1)
    blocks: ManifestBlocks
    ratified_by: str | None = None
    ratified_at: datetime | None = None
    lifecycle: LifecycleState = LifecycleState.DRAFT

    @model_validator(mode="after")
    def _frozen_requires_ratification(self):
        if self.lifecycle is not LifecycleState.DRAFT and not (
            self.ratified_by and self.ratified_at
        ):
            raise ValueError(
                "a FROZEN or SUPERSEDED snapshot requires ratified_by and ratified_at (D-L1)"
            )
        return self


class ProposedScopeChange(Base):
    """A draft delta against the current frozen snapshot. It cannot become
    scope by itself — only ratify() below turns it into v(N+1)."""

    id: str = Field(min_length=1)
    base_version: int = Field(ge=1)
    description: str = Field(min_length=1)
    proposer: str = Field(min_length=1)
    proposed_blocks: ManifestBlocks


def genesis(blocks: ManifestBlocks, ratifier: str, at: datetime) -> ManifestSnapshot:
    """The first ratified snapshot (v1). Requires a ratifier identity."""
    if not ratifier.strip():
        raise ValueError("ratification requires a ratifier identity")
    return ManifestSnapshot(
        version=1,
        blocks=blocks,
        ratified_by=ratifier,
        ratified_at=at,
        lifecycle=LifecycleState.FROZEN,
    )


def ratify(
    proposal: ProposedScopeChange,
    current: ManifestSnapshot,
    ratifier: str,
    at: datetime,
) -> tuple[ManifestSnapshot, ManifestSnapshot]:
    """The human act: proposal + FROZEN v(N) -> (FROZEN v(N+1), SUPERSEDED v(N)).

    Raises rather than guessing: no ratifier identity, a stale proposal
    (base_version mismatch), or a current snapshot that is not FROZEN.
    """
    if not ratifier.strip():
        raise ValueError("ratification requires a ratifier identity")
    if current.lifecycle is not LifecycleState.FROZEN:
        raise ValueError("only the current FROZEN snapshot can be superseded")
    if proposal.base_version != current.version:
        raise ValueError(
            f"stale proposal: base_version {proposal.base_version} != current {current.version}"
        )
    successor = ManifestSnapshot(
        version=current.version + 1,
        blocks=proposal.proposed_blocks,
        ratified_by=ratifier,
        ratified_at=at,
        lifecycle=LifecycleState.FROZEN,
    )
    superseded = current.model_copy(update={"lifecycle": LifecycleState.SUPERSEDED})
    return successor, superseded


def diff(old: ManifestSnapshot, new: ManifestSnapshot) -> str:
    """Human-readable added/removed per block, for the review surface."""
    lines = [f"manifest v{old.version} -> v{new.version}"]
    for block in ManifestBlocks.model_fields:
        old_items = {
            item.id if isinstance(item, CollectorGrant) else item
            for item in getattr(old.blocks, block)
        }
        new_items = {
            item.id if isinstance(item, CollectorGrant) else item
            for item in getattr(new.blocks, block)
        }
        for item in sorted(new_items - old_items):
            lines.append(f"  + {block}: {item}")
        for item in sorted(old_items - new_items):
            lines.append(f"  - {block}: {item}")
    if len(lines) == 1:
        lines.append("  (no block changes)")
    return "\n".join(lines)
