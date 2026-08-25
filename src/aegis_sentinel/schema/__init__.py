"""SCH01 ontology surface. ONTOLOGY_MODELS drives schema generation
(scripts/generate_schemas.py) and the drift test."""

from aegis_sentinel.schema.enums import (
    AssertionType,
    AssuranceState,
    D7Family,
    DeltaBucket,
    DispositionValue,
    LifecycleState,
    PopulationType,
    SourceRole,
    UnknownWhy,
    VerdictState,
)
from aegis_sentinel.schema.models import (
    Assertion,
    Claim,
    Delta,
    DerivationRule,
    DispositionRecord,
    EvidenceQuality,
    EvidenceQualityContract,
    Population,
    QualityProperty,
    SourceRef,
    TimeWindow,
    TimingConstraint,
    Verdict,
    advance,
)

ONTOLOGY_MODELS = (
    Population,
    Claim,
    Assertion,
    EvidenceQualityContract,
    Verdict,
    Delta,
    DispositionRecord,
)

__all__ = [
    "AssertionType",
    "AssuranceState",
    "D7Family",
    "DeltaBucket",
    "DispositionValue",
    "LifecycleState",
    "PopulationType",
    "SourceRole",
    "UnknownWhy",
    "VerdictState",
    "Assertion",
    "Claim",
    "Delta",
    "DerivationRule",
    "DispositionRecord",
    "EvidenceQuality",
    "EvidenceQualityContract",
    "Population",
    "QualityProperty",
    "SourceRef",
    "TimeWindow",
    "TimingConstraint",
    "Verdict",
    "advance",
    "ONTOLOGY_MODELS",
]
