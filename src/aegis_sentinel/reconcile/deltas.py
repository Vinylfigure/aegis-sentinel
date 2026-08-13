"""REC01 — ladder transitions gated on delta dispositions.

docs/HANDOFF.md §2 (locked ruling): DISCOVERED→RECONCILED only when the
reconciliation's deltas are dispositioned; never a coverage percentage
against an unratified denominator — ladder states only. RECONCILED→
RATIFIED is a *human* act and requires a ratifier identity (PRD-v3
invariant 6 / F-4 discipline: the agent may draft, only a human
ratifies; docs/HANDOFF.md §3 manual-by-design steps).

The transitions themselves are the one-step ladder moves enforced by
``schema.population.transition`` — this module adds the evidence gate
(no open deltas) and the accountability gate (a named ratifier) in
front of them.

STRICT-adjacent purity: pure functions of their inputs.
"""

from __future__ import annotations

from aegis_sentinel.reconcile.minimal import ReconciliationResult
from aegis_sentinel.schema import AssuranceState, OpenDeltaRef, Population, transition

MODULE_VERSION = "reconcile.deltas@0.1.0"


class OpenDeltasError(ValueError):
    """DISCOVERED→RECONCILED refused: undispositioned deltas remain."""


def open_delta_refs(result: ReconciliationResult, owner: str) -> tuple[OpenDeltaRef, ...]:
    """Undispositioned deltas as population ``open_deltas`` refs.

    Every open delta carries an owner (PRD-v3 §2: "open deltas with
    owners") — the caller names who is on the hook to disposition it.
    """
    return tuple(
        OpenDeltaRef(delta_id=d.delta_id, owner=d.owner or owner) for d in result.deltas if d.open
    )


def to_reconciled(population: Population, result: ReconciliationResult) -> Population:
    """DISCOVERED→RECONCILED, refused while any delta lacks a disposition.

    The refusal is loud (raises), never silent: a population with open
    deltas stays DISCOVERED and blocks ratification (docs/HANDOFF.md §2).
    """
    if result.population_ref != population.population_id:
        raise ValueError(
            f"reconciliation is for {result.population_ref!r}, "
            f"not population {population.population_id!r}"
        )
    open_deltas = [d.delta_id for d in result.deltas if d.open]
    if open_deltas:
        raise OpenDeltasError(
            f"population {population.population_id!r} has {len(open_deltas)} "
            f"undispositioned delta(s): {', '.join(sorted(open_deltas))}; "
            "DISCOVERED→RECONCILED requires every delta dispositioned"
        )
    return population.model_copy(
        update={
            "state": transition(population.state, AssuranceState.RECONCILED),
            "open_deltas": (),
        }
    )


def to_ratified(population: Population, ratified_by: str) -> Population:
    """RECONCILED→RATIFIED — only with a named human ratifier.

    The ratifier identity is mandatory and non-blank; ratification is a
    manual-by-design step this code merely records (docs/HANDOFF.md §3).
    """
    if not ratified_by or not ratified_by.strip():
        raise ValueError(
            "RECONCILED→RATIFIED requires a ratifier identity; "
            "ratification is a human act (PRD-v3 invariant 6)"
        )
    return population.model_copy(
        update={"state": transition(population.state, AssuranceState.RATIFIED)}
    )
