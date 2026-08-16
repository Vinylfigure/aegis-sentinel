"""Core ontology as typed models (SCH01, per D-P1: pydantic v2,
extra="forbid", frozen=True — the closed-schema invariant as code).

Pure data layer: no I/O, no clocks, no network — the verdict-path purity
test sweeps this package like every other. Conditional requirements the
generated JSON schemas cannot express (pydantic emits structure, not
allOf/if/then) are enforced here by validators; docs/invariants.md
records which invariant each one carries.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aegis_sentinel.schema.enums import (
    AssertionType,
    AssuranceState,
    DeltaBucket,
    DispositionValue,
    PopulationType,
    SourceRole,
    UnknownWhy,
    VerdictState,
)

SHA256 = r"^[0-9a-f]{64}$"


class Base(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class TimeWindow(Base):
    """Temporal semantics are part of evidence identity (invariant: no
    evidence without provenance and temporal semantics)."""

    start: datetime
    end: datetime

    @model_validator(mode="after")
    def _ordered(self):
        if self.end <= self.start:
            raise ValueError("time window must end after it starts")
        return self


class SourceRef(Base):
    system: str = Field(min_length=1)
    role: SourceRole
    ref: str = Field(min_length=1)


class DerivationRule(Base):
    description: str = Field(min_length=1)
    sources: tuple[SourceRef, ...] = Field(min_length=1)


class DispositionRecord(Base):
    """Nothing exits silently: NOT_APPLICABLE demands a rationale."""

    value: DispositionValue
    owner: str = Field(min_length=1)
    rationale: str | None = None

    @model_validator(mode="after")
    def _na_needs_rationale(self):
        if self.value is DispositionValue.NOT_APPLICABLE and not self.rationale:
            raise ValueError("NOT_APPLICABLE requires a rationale — no silent N/A")
        return self


class Delta(Base):
    """A reconciliation difference as a first-class object with an owner
    and a disposition — never just a count."""

    bucket: DeltaBucket
    member_ref: str = Field(min_length=1)
    owner: str | None = None
    disposition: DispositionRecord | None = None

    @property
    def dispositioned(self) -> bool:
        return self.disposition is not None


class Population(Base):
    """Invariant: no population without a derivation rule (general case)
    or an authoritative source (degenerate case) — exactly one."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: PopulationType
    definition: str = Field(min_length=1)
    derivation_rule: DerivationRule | None = None
    authoritative_source: SourceRef | None = None
    period: TimeWindow
    size: int | None = Field(default=None, ge=0)
    exclusions: tuple[str, ...] = ()
    deltas: tuple[Delta, ...] = ()
    state: AssuranceState = AssuranceState.UNDEFINED

    @model_validator(mode="after")
    def _exactly_one_derivation(self):
        if (self.derivation_rule is None) == (self.authoritative_source is None):
            raise ValueError(
                "a population carries exactly one of derivation_rule or authoritative_source"
            )
        return self


# The ladder's legal transitions. Forward only, staleness from RATIFIED,
# and re-discovery from STALE. DISCOVERED→RECONCILED additionally demands
# every delta dispositioned (checked in advance()).
LADDER_TRANSITIONS: dict[AssuranceState, frozenset[AssuranceState]] = {
    AssuranceState.UNDEFINED: frozenset({AssuranceState.DEFINED}),
    AssuranceState.DEFINED: frozenset({AssuranceState.DISCOVERED}),
    AssuranceState.DISCOVERED: frozenset({AssuranceState.RECONCILED}),
    AssuranceState.RECONCILED: frozenset({AssuranceState.RATIFIED}),
    AssuranceState.RATIFIED: frozenset({AssuranceState.STALE}),
    AssuranceState.STALE: frozenset({AssuranceState.DISCOVERED}),
}


def advance(population: Population, to: AssuranceState) -> Population:
    """Pure ladder transition: returns a new Population or raises."""
    allowed = LADDER_TRANSITIONS[population.state]
    if to not in allowed:
        raise ValueError(f"illegal ladder transition {population.state} -> {to}")
    if to is AssuranceState.RECONCILED and any(not d.dispositioned for d in population.deltas):
        raise ValueError("DISCOVERED -> RECONCILED is blocked while any delta is undispositioned")
    return population.model_copy(update={"state": to})


class TimingConstraint(Base):
    days: int = Field(ge=1)
    business_days: bool = True


class Assertion(Base):
    """A lettered, typed, testable attribute of a claim. The type
    constrains admissible evidence; TIMING must say its window."""

    id: str = Field(min_length=1)
    attribute: str | None = None
    type: AssertionType
    description: str = Field(min_length=1)
    timing: TimingConstraint | None = None

    @model_validator(mode="after")
    def _timing_paired_with_type(self):
        if (self.type is AssertionType.TIMING) != (self.timing is not None):
            raise ValueError(
                "timing constraint is required for TIMING assertions and forbidden otherwise"
            )
        return self


class Claim(Base):
    """Invariants: no verdict without a claim; no claim without a defined
    population (structural: population_id is required)."""

    id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    population_id: str = Field(min_length=1)
    assertions: tuple[Assertion, ...] = Field(min_length=1)
    framework_refs: tuple[str, ...] = ()


class QualityProperty(Base):
    """One of the five EQC properties: an independent named method with an
    independent failure mode."""

    method: str = Field(min_length=1)
    failure_mode: str = Field(min_length=1)


class EvidenceQuality(Base):
    provenance: QualityProperty
    integrity: QualityProperty
    population: QualityProperty
    semantics: QualityProperty
    temporal_validity: QualityProperty


class EvidenceQualityContract(Base):
    """Full identity plus the five properties; a contract declares which
    assertion types it is entitled to support (invariant: no PASS unless
    the evidence is fit to prove the claim)."""

    id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    tenant: str = Field(min_length=1)
    population_ref: str = Field(min_length=1)
    endpoint: str = Field(min_length=1)
    parameters: dict[str, str] = Field(default_factory=dict)
    time_window: TimeWindow
    schema_version: str = Field(min_length=1)
    collector_version: str = Field(min_length=1)
    auth_context: str = Field(min_length=1)
    contract_hash: str = Field(pattern=SHA256)
    quality: EvidenceQuality
    supported_assertion_types: tuple[AssertionType, ...] = Field(min_length=1)

    def supports(self, assertion_type: AssertionType) -> bool:
        return assertion_type in self.supported_assertion_types


class Verdict(Base):
    """The five ratified states (D-V1), never interchangeable. UNKNOWN
    carries a why-code (D-U1); EXCLUDED carries its ratification;
    EXCEPTION carries its disposition."""

    state: VerdictState
    unknown_why: UnknownWhy | None = None
    ratification_ref: str | None = None
    exception_disposition_ref: str | None = None
    message: str | None = None

    @model_validator(mode="after")
    def _conditionals(self):
        if (self.state is VerdictState.UNKNOWN) != (self.unknown_why is not None):
            raise ValueError("unknown_why is required for UNKNOWN and forbidden otherwise (D-U1)")
        if self.state is VerdictState.EXCLUDED and not self.ratification_ref:
            raise ValueError("EXCLUDED requires ratification_ref (D-V1)")
        if self.state is VerdictState.EXCEPTION and not self.exception_disposition_ref:
            raise ValueError("EXCEPTION requires exception_disposition_ref (D-V1)")
        return self
