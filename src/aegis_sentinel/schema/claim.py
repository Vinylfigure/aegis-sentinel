"""Claim and Assertion: the semantic unit and its typed decomposition.

PRD-v3 §2: a claim is a testable proposition with a subject population;
frameworks are projections mapped onto claims (``framework_mappings``),
never the other way round. Assertions decompose claims into lettered
testable attributes — the SOC 2 testing-matrix structure
(knowledge/01_corpus/03_testing_libraries/SOC2_Control_Testing_Matrix.md;
AM-06 is the canonical termination-lane control). Every assertion is
typed, and the type determines what evidence *can* prove it: a STATE
snapshot cannot prove a TIMING assertion.
"""

from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from aegis_sentinel.schema.canonical import AegisModel

MODULE_VERSION = "schema.claim@0.1.0"

#: Lettered assertion ids in the testing-matrix style, e.g. "AM-06.a".
ASSERTION_ID_PATTERN = r"^[A-Z0-9][A-Z0-9-]*\.[a-z]+$"


class AssertionType(str, Enum):
    """The seven assertion types (PRD-v3 §2); type constrains evidence."""

    STATE = "STATE"
    EVENT = "EVENT"
    SEQUENCE = "SEQUENCE"
    AGGREGATE = "AGGREGATE"
    EXISTENCE = "EXISTENCE"
    NON_EXISTENCE = "NON_EXISTENCE"
    TIMING = "TIMING"


class FrameworkMapping(AegisModel):
    """A framework control projected onto a claim (frameworks are projections)."""

    framework: str = Field(min_length=1)
    control_id: str = Field(min_length=1)


class Assertion(AegisModel):
    """One lettered, typed, testable attribute of a claim."""

    assertion_id: str = Field(pattern=ASSERTION_ID_PATTERN)
    claim_ref: str = Field(min_length=1)
    type: AssertionType
    predicate_text: str = Field(min_length=1)
    population_ref: str = Field(min_length=1)


class Claim(AegisModel):
    """The semantic unit: a testable proposition over a subject population.

    Constructor-enforced: every attached assertion's ``claim_ref`` must
    name this claim — an assertion cannot be smuggled onto a claim it
    does not decompose.
    """

    claim_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    population_ref: str = Field(min_length=1)
    framework_mappings: tuple[FrameworkMapping, ...] = ()
    assertions: tuple[Assertion, ...] = ()

    @model_validator(mode="after")
    def _assertions_reference_this_claim(self) -> "Claim":
        strays = [a.assertion_id for a in self.assertions if a.claim_ref != self.claim_id]
        if strays:
            raise ValueError(f"assertions {strays} carry claim_ref != {self.claim_id!r}")
        return self
