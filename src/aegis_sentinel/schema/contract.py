"""Evidence Quality Contract (spoken: C&A) — PRD-v3 §2.

Full identity (source, tenant, population ref, endpoint, parameters,
time window, schema version, collector version, retrieved-at, auth
context, contract hash) plus five quality properties, each with an
independent named method and independent failure mode: provenance,
integrity, population, semantics, temporal validity. A contract
declares which assertion types it is entitled to support — a
branch-protection snapshot supports STATE assertions and does not
automatically support "all changes were approved".

Prior art: the prior scaffold's collection-spec ``endpoints`` block and
hash discipline, grown up (docs/manifest-reconciliation.md §1). Its
``completeness_basis`` becomes the population property's named method
(D-U1). ``contract_hash`` is the leaf inside the ratified manifest
snapshot per D-S1.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_serializer

from aegis_sentinel.schema.canonical import AegisModel, sha256_canonical
from aegis_sentinel.schema.claim import AssertionType
from aegis_sentinel.schema.population import Period

MODULE_VERSION = "schema.contract@0.1.0"

SHA256_PATTERN = r"^[a-f0-9]{64}$"


class QualityProperty(AegisModel):
    """One quality property with its independently named method.

    Kept to a single named field to stay closed (no free-form params
    dict); method-specific parameters belong in the contract's
    ``parameters`` list, named per parameter.
    """

    method: str = Field(min_length=1)


class Parameter(AegisModel):
    """One named collection parameter (closed alternative to a dict)."""

    name: str = Field(min_length=1)
    value: str


class EvidenceQualityContract(AegisModel):
    """Identity + five quality properties + supported assertion types."""

    source_system: str = Field(min_length=1)
    tenant: str = Field(min_length=1)
    population_ref: str = Field(min_length=1)
    endpoint: str = Field(min_length=1)
    parameters: tuple[Parameter, ...] = ()
    time_window: Period
    schema_version: str = Field(min_length=1)
    collector_version: str = Field(min_length=1)
    retrieved_at: datetime | None = None  # None at authoring time; set at collection
    auth_context: str = Field(min_length=1)
    contract_hash: str | None = Field(default=None, pattern=SHA256_PATTERN)

    provenance: QualityProperty
    integrity: QualityProperty
    population: QualityProperty
    semantics: QualityProperty
    temporal_validity: QualityProperty

    supported_assertion_types: frozenset[AssertionType]

    @field_serializer("supported_assertion_types")
    def _sorted_assertion_types(self, value: frozenset[AssertionType]) -> list[str]:
        """Serialize the set sorted so the canonical form is deterministic."""
        return sorted(t.value for t in value)

    def compute_contract_hash(self) -> str:
        """Canonical hash with the volatile fields nulled.

        ``contract_hash`` nulls itself (prior ``compute_record_hash``
        semantics); ``retrieved_at`` is nulled because the contract's
        identity is authored before collection runs.
        """
        return sha256_canonical(self, ["contract_hash", "retrieved_at"])
