"""Minimal set reconciler for ONE population — the walking-skeleton
slice of REC01.

Set-based reconciliation per the locked ruling (HANDOFF §2) and D-8
model reconciliation (knowledge/01_corpus/02_design_decisions/
Aegis_Design_Fix_D8_Model_Reconciliation.md): canonical identity is the
normalized email; members missing from one side become first-class
schema.Delta objects (left_only / right_only), members with no email
become UNRESOLVABLE deltas, and the intersection is returned as the
canonical member set. Counts are diagnostics, never evidence.

The ladder gate is not re-implemented here: DISCOVERED→RECONCILED goes
through schema.models.advance, which refuses while any delta is
undispositioned. This module only attaches deltas and dispositions.
"""

from collections.abc import Iterable, Mapping

from pydantic import Field

from aegis_sentinel.schema.enums import DeltaBucket
from aegis_sentinel.schema.models import Base, Delta, DispositionRecord, Population


class Member(Base):
    """One side's view of a member: a stable ref plus the join email."""

    ref: str = Field(min_length=1)
    email: str | None = None


class ReconcileResult(Base):
    population: Population
    canonical_members: tuple[str, ...]


def canonical_email(raw: str | None) -> str | None:
    """Canonical identity: trimmed, lower-cased email; None if absent."""
    if raw is None:
        return None
    email = raw.strip().lower()
    return email or None


def reconcile_population(
    population: Population,
    left: Iterable[Member],
    right: Iterable[Member],
) -> ReconcileResult:
    """Join two member sets by canonical email against one population.

    Returns the population with deltas attached (and size set to the
    canonical intersection count — a diagnostic, not evidence) plus the
    sorted canonical member set. Ladder state is untouched: advancing is
    the caller's explicit act via schema.models.advance.
    """
    left = tuple(left)
    right = tuple(right)
    unresolvable = tuple(m for m in (*left, *right) if canonical_email(m.email) is None)
    left_emails = {e for m in left if (e := canonical_email(m.email)) is not None}
    right_emails = {e for m in right if (e := canonical_email(m.email)) is not None}

    intersection = tuple(sorted(left_emails & right_emails))
    deltas = [
        Delta(bucket=DeltaBucket.LEFT_ONLY, member_ref=f"email:{email}")
        for email in sorted(left_emails - right_emails)
    ]
    deltas += [
        Delta(bucket=DeltaBucket.RIGHT_ONLY, member_ref=f"email:{email}")
        for email in sorted(right_emails - left_emails)
    ]
    deltas += [
        Delta(bucket=DeltaBucket.UNRESOLVABLE, member_ref=member.ref)
        for member in sorted(unresolvable, key=lambda m: m.ref)
    ]
    reconciled = population.model_copy(update={"deltas": tuple(deltas), "size": len(intersection)})
    return ReconcileResult(population=reconciled, canonical_members=intersection)


def apply_dispositions(
    population: Population,
    dispositions: Mapping[str, DispositionRecord],
) -> Population:
    """Attach human dispositions to deltas by member_ref.

    A disposition that names no existing delta is an error — a sign-off
    against nothing must never look like progress. Deltas left without a
    disposition stay open, and schema.models.advance keeps blocking
    DISCOVERED→RECONCILED until every one is dispositioned.
    """
    known = {d.member_ref for d in population.deltas}
    unknown = sorted(set(dispositions) - known)
    if unknown:
        raise ValueError(f"dispositions reference unknown deltas: {unknown}")
    updated = tuple(
        d.model_copy(
            update={
                "disposition": dispositions[d.member_ref],
                "owner": dispositions[d.member_ref].owner,
            }
        )
        if d.member_ref in dispositions
        else d
        for d in population.deltas
    )
    return population.model_copy(update={"deltas": updated})
