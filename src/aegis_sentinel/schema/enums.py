"""Ontology enums (SCH01), exactly as ratified.

Verdict states per docs/DECISIONS.md D-V1; UNKNOWN why-codes per D-U1
(D-7 cause families map in: basis-missing → UNKNOWN_EVIDENCE,
identity-fuzzy → UNKNOWN_POPULATION, no-basis-anywhere →
UNKNOWN_POPULATION; see
knowledge/01_corpus/02_design_decisions/Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md).
Lifecycle per D-L1: ratification IS the freeze. Vocabulary follows
docs/HANDOFF.md §5 — no invented synonyms.
"""

from enum import StrEnum


class PopulationType(StrEnum):
    ENTITY = "entity"
    EVENT = "event"
    RELATIONSHIP = "relationship"


class AssuranceState(StrEnum):
    """The assurance-state ladder. Coverage is never computed against a
    denominator left of RATIFIED."""

    UNDEFINED = "UNDEFINED"
    DEFINED = "DEFINED"
    DISCOVERED = "DISCOVERED"
    RECONCILED = "RECONCILED"
    RATIFIED = "RATIFIED"
    STALE = "STALE"


class SourceRole(StrEnum):
    AUTHORITATIVE = "authoritative"
    CONTRIBUTING = "contributing"
    CORROBORATING = "corroborating"
    DISCOVERY = "discovery"
    EXCLUSION = "exclusion"


class AssertionType(StrEnum):
    """The assertion type determines what evidence *can* prove it."""

    STATE = "STATE"
    EVENT = "EVENT"
    SEQUENCE = "SEQUENCE"
    AGGREGATE = "AGGREGATE"
    EXISTENCE = "EXISTENCE"
    NON_EXISTENCE = "NON-EXISTENCE"
    TIMING = "TIMING"


class VerdictState(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    EXCLUDED = "EXCLUDED"
    EXCEPTION = "EXCEPTION"


class UnknownWhy(StrEnum):
    UNKNOWN_DISCOVERY = "UNKNOWN_DISCOVERY"
    UNKNOWN_OWNER = "UNKNOWN_OWNER"
    UNKNOWN_POPULATION = "UNKNOWN_POPULATION"
    UNKNOWN_EVIDENCE = "UNKNOWN_EVIDENCE"
    UNKNOWN_TESTABILITY = "UNKNOWN_TESTABILITY"


class DispositionValue(StrEnum):
    """Every substrate answer resolves to one of these; nothing exits
    silently — N/A demands a rationale (enforced on DispositionRecord)."""

    IMPLEMENTED = "implemented"
    INHERITED = "inherited"
    SHARED = "shared"
    VENDOR_MANAGED = "vendor_managed"
    COMPENSATING = "compensating"
    NOT_APPLICABLE = "not_applicable"


class DeltaBucket(StrEnum):
    """Set-based reconciliation buckets — counts are diagnostics, never
    evidence."""

    INTERSECTION = "intersection"
    LEFT_ONLY = "left_only"
    RIGHT_ONLY = "right_only"
    CONFLICT = "conflict"
    UNRESOLVABLE = "unresolvable"
    EXCLUDED = "excluded"


class D7Family(StrEnum):
    """Join-failure cause families (D-7) — a pure function of
    `DeltaBucket`, never independently chosen. `conflict` has no family:
    it is a successful join with disagreeing attributes (D-8), not a
    join failure. See knowledge/01_corpus/02_design_decisions/
    Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md §1."""

    BASIS_MISSING = "basis-missing"
    IDENTITY_FUZZY = "identity-fuzzy"
    NO_BASIS_ANYWHERE = "no-basis-anywhere"


class LifecycleState(StrEnum):
    """D-L1 (RATIFIED): ratification IS the freeze — one lifecycle for
    collection specs, capability entries, and manifest snapshots."""

    DRAFT = "draft"
    FROZEN = "frozen"
    SUPERSEDED = "superseded"
