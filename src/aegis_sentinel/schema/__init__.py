"""Aegis core ontology (SCH01) — typed models per PRD-v3 §2.

Pydantic v2, closed (``extra="forbid"``) and frozen everywhere (D-P1).
Pure stdlib + pydantic: no LLM, no network, no clock reads. Generated
JSON Schemas are committed under ``schemas/`` and kept current by a
generated==committed drift test.
"""

from aegis_sentinel.schema.canonical import (
    AegisModel,
    canonical_json,
    sha256_canonical,
)
from aegis_sentinel.schema.claim import (
    ASSERTION_ID_PATTERN,
    Assertion,
    AssertionType,
    Claim,
    FrameworkMapping,
)
from aegis_sentinel.schema.contract import (
    EvidenceQualityContract,
    Parameter,
    QualityProperty,
)
from aegis_sentinel.schema.disposition import (
    Disposition,
    DispositionValue,
)
from aegis_sentinel.schema.lane import (
    SYSTEM_PLACEHOLDER,
    AssertionTemplate,
    ClaimTemplate,
    ControlFunction,
    ControlNature,
    ControlPoint,
    LaneEdge,
    LaneNode,
    LaneNodeKind,
    LaneTemplate,
    PopulationTemplate,
    SourceTemplate,
)
from aegis_sentinel.schema.population import (
    AssuranceState,
    DerivationRule,
    Exclusion,
    OpenDeltaRef,
    Period,
    Population,
    PopulationType,
    Source,
    SourceRole,
    transition,
)
from aegis_sentinel.schema.verdict import (
    D7_FAMILY,
    D7Family,
    UnknownWhyCode,
    VerdictRecord,
    VerdictState,
)

__all__ = [
    # canonical
    "AegisModel",
    "canonical_json",
    "sha256_canonical",
    # population
    "PopulationType",
    "AssuranceState",
    "transition",
    "SourceRole",
    "Source",
    "DerivationRule",
    "Period",
    "Exclusion",
    "OpenDeltaRef",
    "Population",
    # claim
    "ASSERTION_ID_PATTERN",
    "AssertionType",
    "FrameworkMapping",
    "Assertion",
    "Claim",
    # contract
    "QualityProperty",
    "Parameter",
    "EvidenceQualityContract",
    # verdict
    "VerdictState",
    "UnknownWhyCode",
    "D7Family",
    "D7_FAMILY",
    "VerdictRecord",
    # disposition
    "DispositionValue",
    "Disposition",
    # lane
    "SYSTEM_PLACEHOLDER",
    "LaneNodeKind",
    "ControlNature",
    "ControlFunction",
    "LaneNode",
    "LaneEdge",
    "ControlPoint",
    "SourceTemplate",
    "PopulationTemplate",
    "AssertionTemplate",
    "ClaimTemplate",
    "LaneTemplate",
]
