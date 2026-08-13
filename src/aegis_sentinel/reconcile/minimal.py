"""Minimal reconciler — the walking-skeleton slice of REC01.

Reconciliation is set-based (docs/HANDOFF.md §2; prior art:
knowledge/01_corpus/02_design_decisions/Aegis_Design_Fix_D8_Model_Reconciliation.md):
canonical identity, then six buckets — intersection / left-only /
right-only / conflicts / unresolvable / excluded — as first-class
objects. Counts are diagnostics, never evidence.

This module ships the deterministic single-source identity pass the
skeleton needs: one authoritative source enumerates the population, the
canonical member list is built, the population takes one legal ladder
step (DEFINED → DISCOVERED via ``schema.population.transition``), and
the delta set is empty by construction. The API is shaped for growth —
:func:`reconcile_population` takes N sources and returns all six bucket
lists — but N > 1 refuses loudly until REC01 lands the real set
reconciler, rather than pretending a join happened.

A source flagged incomplete never yields a DISCOVERED population:
discovery over a truncated basis would be the partial-pass trap the
prior scaffold's completeness module exists to prevent
(``aegis-sentinel/src/completeness.py``). The population stays DEFINED,
``size`` stays unset (no count against an unasserted denominator), and
the evaluator turns the population UNKNOWN.
"""

from __future__ import annotations

from typing import Sequence

from pydantic import Field

from aegis_sentinel.schema import (
    AegisModel,
    AssuranceState,
    Population,
    transition,
)

MODULE_VERSION = "reconcile.minimal@0.1.0"


class SourceMembers(AegisModel):
    """One source's enumerated members, with its completeness verdict.

    Built by the caller from a collector's ``CollectionSnapshot`` (the
    ``complete`` flag and reasons carry over) plus the parsed member
    identities (canonical join key values, e.g. ``employee_id``).
    """

    source_id: str = Field(min_length=1)
    complete: bool
    notes: tuple[str, ...] = ()
    member_ids: tuple[str, ...] = ()


class ReconciliationResult(AegisModel):
    """One population's reconciliation: members, basis, six buckets.

    All six bucket lists are always present (empty where not
    applicable) so downstream consumers never branch on shape. The four
    delta buckets (left-only / right-only / conflicts / unresolvable)
    feed REC01's disposition workflow; ``excluded`` is deliberate
    exclusion, not a delta.
    """

    population: Population
    members: tuple[str, ...] = ()
    basis_complete: bool
    basis_notes: tuple[str, ...] = ()
    intersection: tuple[str, ...] = ()
    left_only: tuple[str, ...] = ()
    right_only: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    unresolvable: tuple[str, ...] = ()
    excluded: tuple[str, ...] = ()

    @property
    def open_deltas(self) -> tuple[str, ...]:
        """Undispositioned delta members (blocks DISCOVERED→RECONCILED)."""
        return self.left_only + self.right_only + self.conflicts + self.unresolvable


def reconcile_population(
    population: Population, sources: Sequence[SourceMembers]
) -> ReconciliationResult:
    """Deterministic identity pass over one population's source sets.

    Validates that every provided source is declared on the population
    and that every derivation-rule source is provided (membership cannot
    be built from a basis the rule does not name, and a named basis
    cannot be silently skipped). The canonical member list is the sorted
    de-duplicated identity set — same sources, same result, always.
    """
    declared = {s.source_id for s in population.sources}
    provided = [s.source_id for s in sources]
    strays = [sid for sid in provided if sid not in declared]
    if strays:
        raise ValueError(
            f"source(s) {strays} are not declared on population {population.population_id!r}"
        )
    if len(set(provided)) != len(provided):
        raise ValueError(f"duplicate source(s) provided: {sorted(provided)}")
    missing = [ref for ref in population.derivation_rule.source_refs if ref not in provided]
    if missing:
        raise ValueError(
            f"derivation-rule source(s) {missing} not provided for population "
            f"{population.population_id!r}"
        )
    if len(sources) != 1:
        raise ValueError(
            "multi-source set reconciliation lands with REC01; "
            "the skeleton reconciles the single-source identity case"
        )

    source = sources[0]
    if not source.complete:
        # Truncated basis: no member list, no size, no ladder step.
        return ReconciliationResult(
            population=population,
            members=(),
            basis_complete=False,
            basis_notes=source.notes,
        )

    members = tuple(sorted(set(source.member_ids)))
    discovered = population.model_copy(
        update={
            "size": len(members),
            "state": transition(population.state, AssuranceState.DISCOVERED),
        }
    )
    return ReconciliationResult(
        population=discovered,
        members=members,
        basis_complete=True,
        # Single source: the intersection over one set is the set itself;
        # every delta bucket is empty by construction (nothing to join).
        intersection=members,
    )
