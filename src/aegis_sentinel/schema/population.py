"""Population: first-class universe over which claims apply.

PRD-v3 §2 (Ontology): three population types, derivation rules with
source roles, the assurance-state ladder, periods, exclusions, and open
deltas with owners. Authoritative source is the degenerate case of a
derivation rule (PRD §8 D5; docs/manifest-reconciliation.md §1).

Prior art: the prior scaffold's collection-spec ``population`` /
``authoritative_source`` / ``join_key`` fields survive here as the
simplest case of a derivation rule. Set-reconciliation deltas
(knowledge/01_corpus/02_design_decisions/Aegis_Design_Fix_D8_Model_Reconciliation.md)
appear as ``open_deltas`` refs; the reconciler itself is REC01.

No coverage percentage is ever computed against an unratified
denominator — ladder states only (docs/HANDOFF.md §2).
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import Field, model_validator

from aegis_sentinel.schema.canonical import AegisModel

MODULE_VERSION = "schema.population@0.1.0"


class PopulationType(str, Enum):
    """PRD-v3 §2: entity (state), event (happened), relationship (join)."""

    ENTITY = "ENTITY"
    EVENT = "EVENT"
    RELATIONSHIP = "RELATIONSHIP"


class AssuranceState(str, Enum):
    """The assurance-state ladder (PRD-v3 §2)."""

    UNDEFINED = "UNDEFINED"
    DEFINED = "DEFINED"
    DISCOVERED = "DISCOVERED"
    RECONCILED = "RECONCILED"
    RATIFIED = "RATIFIED"
    STALE = "STALE"


#: Each state has exactly one legal successor: one step up the ladder,
#: RATIFIED decays to STALE, and STALE re-enters at DISCOVERED
#: (re-discovery against the previously ratified denominator).
_LEGAL_TRANSITIONS: dict[AssuranceState, AssuranceState] = {
    AssuranceState.UNDEFINED: AssuranceState.DEFINED,
    AssuranceState.DEFINED: AssuranceState.DISCOVERED,
    AssuranceState.DISCOVERED: AssuranceState.RECONCILED,
    AssuranceState.RECONCILED: AssuranceState.RATIFIED,
    AssuranceState.RATIFIED: AssuranceState.STALE,
    AssuranceState.STALE: AssuranceState.DISCOVERED,
}


def transition(state: AssuranceState, to: AssuranceState) -> AssuranceState:
    """Return ``to`` iff the move is legal; raise ``ValueError`` otherwise.

    Legal moves: forward one step; RATIFIED→STALE; STALE→DISCOVERED
    re-entry. Skips, backward moves, and self-transitions all raise —
    ladder discipline is enforced here, not by convention.
    """
    if _LEGAL_TRANSITIONS.get(state) is to:
        return to
    raise ValueError(
        f"illegal assurance-state transition {state.value} -> {to.value}; "
        f"only {state.value} -> {_LEGAL_TRANSITIONS[state].value} is legal"
    )


class SourceRole(str, Enum):
    """Source roles a population's derivation may lean on (PRD-v3 §2)."""

    AUTHORITATIVE = "AUTHORITATIVE"
    CONTRIBUTING = "CONTRIBUTING"
    CORROBORATING = "CORROBORATING"
    DISCOVERY = "DISCOVERY"
    EXCLUSION = "EXCLUSION"


class Source(AegisModel):
    """A named evidence source with its role in the population's derivation."""

    source_id: str = Field(min_length=1)
    role: SourceRole


class DerivationRule(AegisModel):
    """How the population's membership is constructed (the general case).

    The degenerate case — a single AUTHORITATIVE source — is what the
    prior scaffold called ``authoritative_source`` (PRD §8 D5). Use
    :meth:`from_authoritative_source` for that case; ``source_refs``
    name ``Source.source_id`` values declared on the owning Population.
    """

    rule_text: str = Field(min_length=1)
    source_refs: tuple[str, ...] = Field(min_length=1)

    @classmethod
    def from_authoritative_source(cls, source_id: str) -> "DerivationRule":
        """The degenerate case: membership is exactly the authoritative enumeration."""
        return cls(
            rule_text=f"all members enumerated by authoritative source {source_id}",
            source_refs=(source_id,),
        )


class Period(AegisModel):
    """Closed date interval a population (or evidence window) covers."""

    start: date
    end: date

    @model_validator(mode="after")
    def _end_not_before_start(self) -> "Period":
        if self.end < self.start:
            raise ValueError(f"period end {self.end} precedes start {self.start}")
        return self


class Exclusion(AegisModel):
    """A member deliberately excluded from the population — never silent."""

    member_id: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class OpenDeltaRef(AegisModel):
    """Reference to an undispositioned reconciliation delta and its owner."""

    delta_id: str = Field(min_length=1)
    owner: str = Field(min_length=1)


class Population(AegisModel):
    """A defined universe: definition, derivation, sources, period, state.

    Constructor-enforced: every ``source_refs`` entry in the derivation
    rule must name a declared source (PRD invariant 3 — no population
    without a derivation rule or authoritative source, and that rule
    must be groundable in the declared sources).
    """

    population_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: PopulationType
    definition: str = Field(min_length=1)
    derivation_rule: DerivationRule
    sources: tuple[Source, ...] = Field(min_length=1)
    period: Period
    size: int | None = Field(default=None, ge=0)
    exclusions: tuple[Exclusion, ...] = ()
    open_deltas: tuple[OpenDeltaRef, ...] = ()
    state: AssuranceState = AssuranceState.UNDEFINED

    @model_validator(mode="after")
    def _derivation_refs_declared(self) -> "Population":
        declared = {s.source_id for s in self.sources}
        missing = [ref for ref in self.derivation_rule.source_refs if ref not in declared]
        if missing:
            raise ValueError(
                "derivation rule references undeclared source(s): " + ", ".join(missing)
            )
        return self
