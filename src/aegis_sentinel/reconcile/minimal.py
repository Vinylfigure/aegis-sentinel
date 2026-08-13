"""The set reconciler (REC01) — grown from the walking-skeleton slice.

Reconciliation is set-based (docs/HANDOFF.md §2; prior art:
knowledge/01_corpus/02_design_decisions/Aegis_Design_Fix_D8_Model_Reconciliation.md):
canonical identity (``identity.py``), then six buckets — intersection /
left-only / right-only / conflicts / unresolvable / excluded — as
first-class :class:`~aegis_sentinel.reconcile.setops.DeltaObject`
records (``setops.py``). Counts are diagnostics, never evidence — the
``source_counts`` field is labeled a smell test for exactly that reason.

Two paths through :func:`reconcile_population`, one API shape:

- **Single source** (the original walking-skeleton contract, preserved):
  the authoritative enumeration IS the membership; the canonical member
  list is the sorted de-duplicated identity set and the delta buckets
  are empty by construction.
- **N sources** (REC01): every provided source supplies typed
  :class:`~aegis_sentinel.reconcile.identity.SourceMember` records; the
  canonical-identity join clusters them and ``setops.classify`` fills
  the six buckets — including the negative space (identities present in
  contributing sources that the authoritative source cannot account
  for), the signature capability (PRD-v3 §2).

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

from aegis_sentinel.reconcile.identity import KEY_PRECEDENCE, SourceMember
from aegis_sentinel.reconcile.setops import (
    DELTA_BUCKETS,
    DeltaObject,
    RatifiedDeltaDisposition,
    classify,
)
from aegis_sentinel.schema import (
    AegisModel,
    AssuranceState,
    OpenDeltaRef,
    Population,
    transition,
)

MODULE_VERSION = "reconcile.minimal@0.2.0"


class SourceMembers(AegisModel):
    """One source's enumerated members, with its completeness verdict.

    Built by the caller from a collector's ``CollectionSnapshot`` (the
    ``complete`` flag and reasons carry over) plus the parsed member
    identities: ``member_ids`` for the single-source identity pass
    (canonical join key values, e.g. ``employee_id``), or typed
    ``members`` for the N-source set reconciliation (REC01).
    """

    source_id: str = Field(min_length=1)
    complete: bool
    notes: tuple[str, ...] = ()
    member_ids: tuple[str, ...] = ()
    members: tuple[SourceMember, ...] = ()


class ReconciliationResult(AegisModel):
    """One population's reconciliation: members, basis, six buckets.

    All six bucket lists are always present (empty where not
    applicable) so downstream consumers never branch on shape. The four
    delta buckets (left-only / right-only / conflicts / unresolvable)
    feed the disposition workflow; ``excluded`` is deliberate,
    disposition-backed exclusion, not a delta.

    Frontend-contract alignment (web/src/lib/types/artifacts.ts):
    ``population_ref`` / ``canonical_identity_keys`` / ``source_counts``
    / ``deltas`` carry the frontend's field names and semantics.
    ``source_counts`` is DIAGNOSTIC ONLY — per-source member counts are
    a smell test, never evidence (docs/HANDOFF.md §2).
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
    canonical_identity_keys: tuple[str, ...] = ()
    source_counts: dict[str, int] = {}
    deltas: tuple[DeltaObject, ...] = ()
    diagnostics: tuple[str, ...] = ()

    @property
    def population_ref(self) -> str:
        """Frontend-contract accessor for the reconciled population id."""
        return self.population.population_id

    @property
    def open_deltas(self) -> tuple[str, ...]:
        """Undispositioned delta members (blocks DISCOVERED→RECONCILED)."""
        return self.left_only + self.right_only + self.conflicts + self.unresolvable

    @property
    def open_delta_objects(self) -> tuple[DeltaObject, ...]:
        return tuple(d for d in self.deltas if d.open)


def _validate_sources(population: Population, sources: Sequence[SourceMembers]) -> None:
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


def _incomplete_result(
    population: Population, sources: Sequence[SourceMembers]
) -> ReconciliationResult:
    """Truncated basis: no member list, no size, no ladder step."""
    notes = tuple(
        f"{source.source_id}: {note}"
        for source in sources
        if not source.complete
        for note in (source.notes or ("collection incomplete",))
    )
    return ReconciliationResult(
        population=population,
        members=(),
        basis_complete=False,
        basis_notes=notes,
    )


def reconcile_population(
    population: Population,
    sources: Sequence[SourceMembers],
    dispositions: Sequence[RatifiedDeltaDisposition] = (),
    identity_domain: str | None = None,
    delta_owner: str = "unassigned",
) -> ReconciliationResult:
    """Deterministic set reconciliation over one population's source sets.

    Validates that every provided source is declared on the population
    and that every derivation-rule source is provided (membership cannot
    be built from a basis the rule does not name, and a named basis
    cannot be silently skipped). Same sources, same result, always.

    ``dispositions`` are pre-ratified, human-made disposition records
    (F-4): the reconciler applies them to matching deltas (→ excluded
    bucket) and never manufactures one. ``identity_domain`` drives the
    workforce scope rule (setops.py). ``delta_owner`` names who is on
    the hook for deltas no human has claimed yet.
    """
    _validate_sources(population, sources)

    if any(not source.complete for source in sources):
        return _incomplete_result(population, sources)

    if len(sources) == 1 and not sources[0].members:
        # The walking-skeleton single-source identity pass, unchanged.
        members = tuple(sorted(set(sources[0].member_ids)))
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
            # Single source: the intersection over one set is the set
            # itself; every delta bucket is empty by construction.
            intersection=members,
            canonical_identity_keys=KEY_PRECEDENCE,
            source_counts={sources[0].source_id: len(members)},
        )

    untyped = sorted(s.source_id for s in sources if not s.members and s.member_ids)
    if untyped:
        raise ValueError(
            f"N-source reconciliation requires typed members; source(s) {untyped} "
            "provided only bare member_ids"
        )

    members_by_source = {s.source_id: s.members for s in sources}
    classified = classify(
        population,
        members_by_source,
        dispositions=dispositions,
        identity_domain=identity_domain,
    )

    delta_keys = {d.member_key for d in classified.deltas}
    intersection = tuple(k for k in classified.members if k not in delta_keys)
    buckets = {
        bucket: tuple(d.member_key for d in classified.deltas if d.bucket == bucket)
        for bucket in DELTA_BUCKETS + ("excluded",)
    }
    open_refs = tuple(
        OpenDeltaRef(delta_id=d.delta_id, owner=d.owner or delta_owner)
        for d in classified.deltas
        if d.open
    )
    discovered = population.model_copy(
        update={
            "size": len(classified.members),
            "state": transition(population.state, AssuranceState.DISCOVERED),
            "open_deltas": open_refs,
        }
    )
    return ReconciliationResult(
        population=discovered,
        members=classified.members,
        basis_complete=True,
        intersection=intersection,
        left_only=buckets["left_only"],
        right_only=buckets["right_only"],
        conflicts=buckets["conflicts"],
        unresolvable=buckets["unresolvable"],
        excluded=buckets["excluded"],
        canonical_identity_keys=KEY_PRECEDENCE,
        source_counts={
            s.source_id: len(s.members) for s in sorted(sources, key=lambda s: s.source_id)
        },
        deltas=classified.deltas,
        diagnostics=classified.diagnostics,
    )
