"""Shared sample instances: one representative valid instance per model.

Used by the round-trip suite. Fixture JSON on disk
(tests/fixtures/schema/) is the contract-facing twin of these.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from aegis_sentinel.schema import (
    Assertion,
    AssertionType,
    AssuranceState,
    Claim,
    DerivationRule,
    Disposition,
    DispositionValue,
    EvidenceQualityContract,
    Exclusion,
    FrameworkMapping,
    OpenDeltaRef,
    Parameter,
    Period,
    Population,
    PopulationType,
    QualityProperty,
    Source,
    SourceRole,
    UnknownWhyCode,
    VerdictRecord,
    VerdictState,
)

SHA_A = "a" * 64
SHA_B = "b" * 64

PERIOD = Period(start=date(2026, 1, 1), end=date(2026, 6, 30))

SOURCE = Source(source_id="hris-feed", role=SourceRole.AUTHORITATIVE)

DERIVATION = DerivationRule.from_authoritative_source("hris-feed")

POPULATION = Population(
    population_id="pop-terminated-employees",
    name="Terminated employees",
    type=PopulationType.EVENT,
    definition="All employees terminated during the period",
    derivation_rule=DERIVATION,
    sources=(
        SOURCE,
        Source(source_id="idp-deactivations", role=SourceRole.CORROBORATING),
    ),
    period=PERIOD,
    size=42,
    exclusions=(
        Exclusion(member_id="emp-0042", rationale="rehired within period; separate claim"),
    ),
    open_deltas=(OpenDeltaRef(delta_id="delta-001", owner="the Owner"),),
    state=AssuranceState.DEFINED,
)

ASSERTION = Assertion(
    assertion_id="AM-06.a",
    claim_ref="claim-termination-revocation",
    type=AssertionType.TIMING,
    predicate_text="production access revoked within five business days of termination",
    population_ref="pop-terminated-employees",
)

CLAIM = Claim(
    claim_id="claim-termination-revocation",
    statement="Every terminated employee lost production access within five business days",
    population_ref="pop-terminated-employees",
    framework_mappings=(
        FrameworkMapping(framework="SOC2", control_id="CC6.2"),
        FrameworkMapping(framework="internal", control_id="AM-06"),
    ),
    assertions=(ASSERTION,),
)

CONTRACT = EvidenceQualityContract(
    source_system="github",
    tenant="example-org",
    population_ref="pop-terminated-employees",
    endpoint="GET /orgs/{org}/members",
    parameters=(Parameter(name="per_page", value="100"),),
    time_window=PERIOD,
    schema_version="0.1.0",
    collector_version="github-members@0.1.0",
    retrieved_at=None,
    auth_context="app-installation:read:org",
    contract_hash=None,
    provenance=QualityProperty(method="authenticated API origin, app installation token"),
    integrity=QualityProperty(method="sha256-canonical + WORM store"),
    population=QualityProperty(method="exhaustive_pagination"),
    semantics=QualityProperty(method="schema contract + sampled trace"),
    temporal_validity=QualityProperty(method="snapshot window vs asserted period"),
    supported_assertion_types=frozenset({AssertionType.STATE, AssertionType.EXISTENCE}),
)

VERDICT_PASS = VerdictRecord(
    claim_ref="claim-termination-revocation",
    assertion_ref="AM-06.a",
    population_ref="pop-terminated-employees",
    manifest_version="v1",
    snapshot_hash=SHA_A,
    contract_hash=SHA_B,
    state=VerdictState.PASS,
    evaluated_at=datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc),
    evidence_refs=(SHA_A,),
)

VERDICT_UNKNOWN = VerdictRecord(
    claim_ref="claim-termination-revocation",
    assertion_ref="AM-06.a",
    population_ref="pop-terminated-employees",
    manifest_version="v1",
    snapshot_hash=SHA_A,
    contract_hash=SHA_B,
    state=VerdictState.UNKNOWN,
    why_code=UnknownWhyCode.UNKNOWN_EVIDENCE,
    d7_family="basis_missing",
    message="pagination not exhausted; population basis missing",
    evaluated_at=datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc),
)

DISPOSITION = Disposition(
    value=DispositionValue.NA_WITH_RATIONALE,
    rationale="vendor operates the change control; their report covers it",
)

#: One representative instance per public model (round-trip coverage).
SAMPLES = [
    PERIOD,
    SOURCE,
    DERIVATION,
    Exclusion(member_id="emp-0042", rationale="rehired within period"),
    OpenDeltaRef(delta_id="delta-001", owner="the Owner"),
    POPULATION,
    FrameworkMapping(framework="SOC2", control_id="CC6.2"),
    ASSERTION,
    CLAIM,
    QualityProperty(method="exhaustive_pagination"),
    Parameter(name="per_page", value="100"),
    CONTRACT,
    VERDICT_PASS,
    VERDICT_UNKNOWN,
    DISPOSITION,
    Disposition(value=DispositionValue.INHERITED, rationale=None),
]
