"""The type checker (TYP01) — "How the compiler uses the registry", PRD-v3 §3.

For every (claim, assertion, population) triple, :func:`compile_program`
matches required evidence properties against registered capabilities and
either compiles a :class:`CompiledCollectorPlan` or refuses with an
E-code a human can act on (``errors.py``).

Matching rules:

1. **Assertion type → required temporal shape.** TIMING / SEQUENCE /
   EVENT assertions need event history covering the population's period:
   FULL_HISTORY always suffices; EVENT_HISTORY suffices iff its
   ``window_days`` covers the period length. STATE / EXISTENCE /
   NON_EXISTENCE are satisfiable by state snapshots (STATE_ONLY,
   SNAPSHOT_CADENCE, FULL_HISTORY). AGGREGATE needs an enumerable
   population yield — any usable entry yielding one of the population's
   sources enumerates it (every entry names a pagination exhaustion
   method by schema). No adequate candidate → **E204**, with
   ``satisfiable_via`` suggestions drawn ONLY from actually-usable
   registry entries whose temporal shape covers the period; when nothing
   covers it, the suggestion list is empty and the message says so.
2. **Every derivation-rule source must be yielded** by some usable
   capability entry (yield name == source id) → else **E117** naming
   the source.
3. **Schema-version pins.** ``schema_pins`` maps entry_id → the ratified
   ``schema_version``; a consulted entry whose observed version differs
   → **E302** (re-ratify or pin).

Candidates for an assertion are the usable entries yielding one of the
population's *declared* sources, preferred by source role
(AUTHORITATIVE first) then entry_id — fully deterministic. Callers pass
``Registry.usable()``: a Cartographer draft is mechanically invisible
here (SCH02), so an unratified entry can never type-check a claim.

**Compile-integrity guardrail (PRD-v3 §7):** zero collectors execute
for claims with unresolved E-codes — :func:`executable_collectors` is
the only sanctioned way to get plans out of a :class:`CompileResult`,
and it drops every plan of every claim that carries any error.

STRICT purity lane (D-P3): pure functions of their inputs — no clock
reads, no randomness, no environment access, no network.
"""

from __future__ import annotations

from typing import Annotated, Mapping, Sequence, Union

from pydantic import Field

from aegis_sentinel.capability.entry import (
    CapabilityEntry,
    Pagination,
    TemporalShape,
    TemporalShapeKind,
)
from aegis_sentinel.capability.registry import RegistryView
from aegis_sentinel.compile.errors import (
    CompileError,
    E117MissingCapability,
    E204TemporalInsufficiency,
    E302SchemaVersionDrift,
)
from aegis_sentinel.schema.canonical import AegisModel
from aegis_sentinel.schema.claim import Assertion, AssertionType, Claim
from aegis_sentinel.schema.population import (
    Period,
    Population,
    PopulationType,
    SourceRole,
)

MODULE_VERSION = "compile.typecheck@0.1.0"

#: Closed union of every E-code, discriminated on ``code`` so a
#: serialized error round-trips as its concrete class, never the base.
AnyCompileError = Annotated[
    Union[E204TemporalInsufficiency, E117MissingCapability, E302SchemaVersionDrift],
    Field(discriminator="code"),
]

#: Assertion types that require event history over the claim period.
EVENT_FAMILY = frozenset({AssertionType.TIMING, AssertionType.SEQUENCE, AssertionType.EVENT})

#: Assertion types satisfiable by a state snapshot (PRD-v3 §2: "User
#: absent from GitHub today" is STATE and cannot prove TIMING).
STATE_FAMILY = frozenset(
    {AssertionType.STATE, AssertionType.EXISTENCE, AssertionType.NON_EXISTENCE}
)

#: Temporal shapes that can prove current state / enumerate members.
STATE_SHAPES = frozenset(
    {
        TemporalShapeKind.STATE_ONLY,
        TemporalShapeKind.SNAPSHOT_CADENCE,
        TemporalShapeKind.FULL_HISTORY,
    }
)

#: Deterministic candidate preference: collect from the population's
#: AUTHORITATIVE surface before contributing/corroborating ones.
_ROLE_RANK: dict[SourceRole, int] = {
    SourceRole.AUTHORITATIVE: 0,
    SourceRole.CONTRIBUTING: 1,
    SourceRole.CORROBORATING: 2,
    SourceRole.DISCOVERY: 3,
    SourceRole.EXCLUSION: 4,
}


def period_days(period: Period) -> int:
    """Closed-interval length in days (start == end → 1)."""
    return (period.end - period.start).days + 1


class CompiledCollectorPlan(AegisModel):
    """One capability entry serving one assertion.

    Threads the EQC-relevant fields (PRD-v3 §2 contract identity) from
    the matched entry: surface/endpoint, least-privilege auth scope,
    pagination + exhaustion method (the population quality property),
    temporal shape (temporal validity), join keys (identity), and the
    time window the evidence must represent.
    """

    claim_ref: str = Field(min_length=1)
    assertion_ref: str = Field(min_length=1)
    assertion_type: AssertionType
    population_ref: str = Field(min_length=1)
    source_id: str = Field(min_length=1)  # the population source this entry yields
    entry_id: str = Field(min_length=1)
    system: str = Field(min_length=1)
    surface: str = Field(min_length=1)
    auth_scope: str = Field(min_length=1)
    pagination: Pagination
    temporal: TemporalShape
    join_keys: tuple[str, ...] = Field(min_length=1)
    time_window: Period


class ClaimCompilation(AegisModel):
    """Per-claim result: matched plans and/or the errors that block them."""

    claim_ref: str = Field(min_length=1)
    plans: tuple[CompiledCollectorPlan, ...] = ()
    errors: tuple[AnyCompileError, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors


class CompileResult(AegisModel):
    """The whole program's compilation, claim by claim."""

    claims: tuple[ClaimCompilation, ...] = ()

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.claims)

    @property
    def errors(self) -> tuple[CompileError, ...]:
        return tuple(e for c in self.claims for e in c.errors)

    def for_claim(self, claim_ref: str) -> ClaimCompilation:
        for compilation in self.claims:
            if compilation.claim_ref == claim_ref:
                return compilation
        raise KeyError(f"no compilation for claim {claim_ref!r}")

    def render_errors(self) -> str:
        """Every error in PRD §3 style, one per line."""
        return "\n".join(e.render() for e in self.errors)


def executable_collectors(result: CompileResult) -> tuple[CompiledCollectorPlan, ...]:
    """The compile-integrity gate (PRD-v3 §7).

    Returns plans ONLY for claims with zero errors. A claim carrying any
    unresolved E-code contributes nothing — even assertions of that
    claim that matched cleanly — because executing half a claim's
    collectors would be the product lying about what it can prove.
    """
    return tuple(plan for c in result.claims if c.ok for plan in c.plans)


class _Candidate:
    """One usable entry reachable through one of the population's sources."""

    __slots__ = ("rank", "source_id", "entry")

    def __init__(self, rank: int, source_id: str, entry: CapabilityEntry) -> None:
        self.rank = rank
        self.source_id = source_id
        self.entry = entry


def _yield_index(view: RegistryView) -> dict[str, list[CapabilityEntry]]:
    """population-yield name → usable entries yielding it (load order)."""
    index: dict[str, list[CapabilityEntry]] = {}
    for entry in view:
        for pop_yield in entry.populations_yielded:
            index.setdefault(pop_yield.name, []).append(entry)
    return index


def _candidates(
    population: Population, yield_index: Mapping[str, list[CapabilityEntry]]
) -> list[_Candidate]:
    """Usable entries yielding any declared source, best role first."""
    best: dict[str, _Candidate] = {}
    for source in population.sources:
        for entry in yield_index.get(source.source_id, []):
            rank = _ROLE_RANK[source.role]
            seen = best.get(entry.entry_id)
            if seen is None or (rank, source.source_id) < (seen.rank, seen.source_id):
                best[entry.entry_id] = _Candidate(rank, source.source_id, entry)
    return sorted(best.values(), key=lambda c: (c.rank, c.entry.entry_id))


def _event_adequate(temporal: TemporalShape, days: int) -> bool:
    if temporal.kind is TemporalShapeKind.FULL_HISTORY:
        return True
    if temporal.kind is TemporalShapeKind.EVENT_HISTORY:
        return temporal.window_days is not None and temporal.window_days >= days
    return False


def _shape_text(temporal: TemporalShape) -> str:
    if temporal.kind is TemporalShapeKind.EVENT_HISTORY:
        return f"event-history(window={temporal.window_days}d)"
    if temporal.kind is TemporalShapeKind.FULL_HISTORY:
        return "full-history"
    if temporal.kind is TemporalShapeKind.SNAPSHOT_CADENCE:
        return "snapshot-cadence"
    return "STATE only"


def _plan(
    assertion: Assertion, population: Population, candidate: _Candidate
) -> CompiledCollectorPlan:
    entry = candidate.entry
    return CompiledCollectorPlan(
        claim_ref=assertion.claim_ref,
        assertion_ref=assertion.assertion_id,
        assertion_type=assertion.type,
        population_ref=population.population_id,
        source_id=candidate.source_id,
        entry_id=entry.entry_id,
        system=entry.system,
        surface=entry.surface,
        auth_scope=entry.auth_scope,
        pagination=entry.pagination,
        temporal=entry.temporal,
        join_keys=entry.join_keys,
        time_window=population.period,
    )


def _suggestions(view: RegistryView, days: int) -> tuple[tuple[str, ...], ...]:
    """Usable-entry combinations whose event history covers the period.

    V1 suggests single-entry combinations: every usable entry yielding
    an EVENT population whose temporal shape covers the period. Drawn
    only from the usable view — never a draft, never an invented
    archive. Empty means no usable combination covers the period.
    """
    combos = [
        (entry.entry_id,)
        for entry in sorted(view, key=lambda e: e.entry_id)
        if _event_adequate(entry.temporal, days)
        and any(y.type is PopulationType.EVENT for y in entry.populations_yielded)
    ]
    return tuple(combos)


def _e204(
    assertion: Assertion,
    population: Population,
    candidates: Sequence[_Candidate],
    view: RegistryView,
    needs_history: bool,
) -> E204TemporalInsufficiency:
    days = period_days(population.period)
    window = f"{population.period.start.isoformat()}..{population.period.end.isoformat()}"
    if needs_history:
        need = f"requires historical transition timestamps covering {window} ({days} days)"
    else:
        need = f"requires a state snapshot of the population over {window}"

    event_candidates = [
        c
        for c in candidates
        if needs_history and c.entry.temporal.kind is TemporalShapeKind.EVENT_HISTORY
    ]
    named = max(event_candidates, key=lambda c: c.entry.temporal.window_days or 0, default=None)
    window_days: int | None = None
    if named is not None:
        window_days = named.entry.temporal.window_days
        assert window_days is not None  # EVENT_HISTORY always carries its bound
        shortfall = (
            f"capability {named.entry.entry_id} ({named.entry.surface}) yields "
            f"{_shape_text(named.entry.temporal)} — {window_days} days short of {days}"
        )
    elif candidates:
        first = candidates[0]
        shortfall = (
            f"capability {first.entry.entry_id} ({first.entry.surface}) yields "
            f"{_shape_text(first.entry.temporal)}"
        )
    else:
        shortfall = (
            f'no usable capability among population "{population.population_id}" sources '
            "yields the required shape"
        )

    suggestions = _suggestions(view, days) if needs_history else ()
    if suggestions:
        via = " | ".join(
            " + ".join(f"{eid} ({_shape_text(view.get(eid).temporal)})" for eid in combo)
            for combo in suggestions
        )
        tail = f"Satisfiable via: {via}. Amend manifest?"
    else:
        tail = "No usable capability combination covers the period."

    message = (
        f'{assertion.type.value} assertion "{assertion.predicate_text}" '
        f"({assertion.assertion_id}) {need}; {shortfall}. {tail}"
    )
    return E204TemporalInsufficiency(
        message=message,
        claim_ref=assertion.claim_ref,
        assertion_ref=assertion.assertion_id,
        required_window=population.period,
        capability_window_days=window_days,
        satisfiable_via=suggestions,
    )


def _match_assertion(
    assertion: Assertion,
    population: Population,
    candidates: Sequence[_Candidate],
    view: RegistryView,
) -> CompiledCollectorPlan | E204TemporalInsufficiency:
    if assertion.type in EVENT_FAMILY:
        days = period_days(population.period)
        adequate = [c for c in candidates if _event_adequate(c.entry.temporal, days)]
        needs_history = True
    elif assertion.type in STATE_FAMILY:
        adequate = [c for c in candidates if c.entry.temporal.kind in STATE_SHAPES]
        needs_history = False
    else:  # AGGREGATE: any candidate enumerates its yield (exhaustion is schema-required)
        adequate = list(candidates)
        needs_history = False
    if adequate:
        return _plan(assertion, population, adequate[0])
    return _e204(assertion, population, candidates, view, needs_history)


def compile_program(
    claims: Sequence[Claim],
    populations: Sequence[Population],
    registry_usable_view: RegistryView,
    schema_pins: Mapping[str, str] | None = None,
) -> CompileResult:
    """Type-check every claim against the usable capability registry.

    ``registry_usable_view`` must be ``Registry.usable()`` — the sole
    compiler-facing view (SCH02); drafts are mechanically absent from
    it. ``schema_pins`` maps entry_id → the ratified schema_version
    (E302 drift check); a pin for an entry absent from the view is
    inert — nothing is observed, so nothing can drift.

    Raises ``ValueError`` if a claim or assertion references a
    population that was never provided — that is a malformed program,
    not a compile error the manifest can be amended around.
    """
    pins = dict(schema_pins or {})
    by_id = {p.population_id: p for p in populations}
    yield_index = _yield_index(registry_usable_view)

    compilations: list[ClaimCompilation] = []
    for claim in claims:
        refs = [claim.population_ref]
        refs += [a.population_ref for a in claim.assertions if a.population_ref not in refs]
        missing_refs = [r for r in refs if r not in by_id]
        if missing_refs:
            raise ValueError(
                f"claim {claim.claim_id!r} references unknown population(s): {missing_refs}"
            )
        claim_pops = [by_id[r] for r in refs]

        errors: list[E204TemporalInsufficiency | E117MissingCapability | E302SchemaVersionDrift]
        errors = []

        # Rule 2 — every derivation-rule source has a usable capability entry.
        for population in claim_pops:
            for source_ref in population.derivation_rule.source_refs:
                if source_ref not in yield_index:
                    rule_refs = " + ".join(population.derivation_rule.source_refs)
                    errors.append(
                        E117MissingCapability(
                            message=(
                                f'Population "{population.population_id}" derivation rule '
                                f"references {rule_refs}; capability entry missing for "
                                f"{source_ref}."
                            ),
                            claim_ref=claim.claim_id,
                            missing_source=source_ref,
                        )
                    )

        # Rule 3 — consulted entries must match their ratified pins.
        consulted: dict[str, CapabilityEntry] = {}
        for population in claim_pops:
            for source in population.sources:
                for entry in yield_index.get(source.source_id, []):
                    consulted[entry.entry_id] = entry
        for entry_id in sorted(consulted):
            entry = consulted[entry_id]
            pinned = pins.get(entry_id)
            if pinned is not None and pinned != entry.schema_version:
                errors.append(
                    E302SchemaVersionDrift(
                        message=(
                            f"Capability entry {entry_id} schema_version "
                            f"{entry.schema_version} ≠ ratified {pinned} — re-ratify or pin."
                        ),
                        claim_ref=claim.claim_id,
                        entry_id=entry_id,
                        observed=entry.schema_version,
                        ratified=pinned,
                    )
                )

        # Rule 1 — per assertion: temporal shape must support the type.
        plans: list[CompiledCollectorPlan] = []
        for assertion in claim.assertions:
            population = by_id[assertion.population_ref]
            outcome = _match_assertion(
                assertion, population, _candidates(population, yield_index), registry_usable_view
            )
            if isinstance(outcome, CompiledCollectorPlan):
                plans.append(outcome)
            else:
                errors.append(outcome)

        compilations.append(
            ClaimCompilation(claim_ref=claim.claim_id, plans=tuple(plans), errors=tuple(errors))
        )
    return CompileResult(claims=tuple(compilations))
