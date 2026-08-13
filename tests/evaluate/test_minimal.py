"""Walking-skeleton evaluator tests — PASS path, UNKNOWN paths, re-performance.

The pipeline under test is the real end-to-end slice: fixture tenant →
HRIS collector → single-source reconcile → evaluator, with the D-S1
triple threaded from the fixture engagement. UNKNOWN taxonomy per D-U1
(docs/DECISIONS.md): a truncated population basis is a population-level
``UNKNOWN(UNKNOWN_POPULATION)``; uncollected corroborating evidence is
``UNKNOWN(UNKNOWN_EVIDENCE, d7_family=basis_missing)``. UNKNOWN never
maps to satisfied.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aegis_sentinel.collectors import FixtureTransport, HrisTerminationsCollector
from aegis_sentinel.evaluate import evaluate_feed_claim
from aegis_sentinel.reconcile import SourceMembers, reconcile_population
from aegis_sentinel.schema import (
    Assertion,
    AssertionType,
    Claim,
    D7Family,
    UnknownWhyCode,
    VerdictRecord,
    VerdictState,
)
from conftest import SEEDED_TRUNCATED_DIR, TENANTS_DIR

ALL_MEMBER_IDS = (
    "CT-2044",
    "E-1004",
    "E-1019",
    "E-1027",
    "E-1033",
    "E-1041",
    "E-1048",
    "E-1052",
    "E-1060",
    "E-1066",
    "E-1073",
    "E-1080",
    "E-1088",
    "E-1091",
    "E-1095",
)


def run_pipeline(
    tenant_root: Path,
    feed_plan,
    feed_claim,
    terminations_population,
    engagement,
    retrieved_at,
    evaluated_at,
    deprovisioned_member_ids: tuple[str, ...] | None = None,
) -> tuple[VerdictRecord, ...]:
    collector = HrisTerminationsCollector(FixtureTransport(tenant_root))
    snapshot = collector.collect(feed_plan, retrieved_at)
    contract = collector.contract(feed_plan, engagement["tenant"], retrieved_at)
    events = collector.events(snapshot)
    reconciliation = reconcile_population(
        terminations_population,
        [
            SourceMembers(
                source_id=feed_plan.source_id,
                complete=snapshot.complete,
                notes=snapshot.incompleteness,
                member_ids=tuple(e.employee_id for e in events),
            )
        ],
    )
    assert snapshot.snapshot_hash is not None
    return evaluate_feed_claim(
        feed_claim,
        reconciliation,
        contract,
        manifest_version=engagement["manifest_version"],
        manifest_snapshot_hash=engagement["ratified_manifest_snapshot_hash"],
        collection_snapshot_hash=snapshot.snapshot_hash,
        evaluated_at=evaluated_at,
        deprovisioned_member_ids=deprovisioned_member_ids,
    )


@pytest.fixture()
def pipeline(
    feed_plan, feed_claim, terminations_population, engagement, retrieved_at, evaluated_at
):
    def run(tenant_root: Path, deprovisioned: tuple[str, ...] | None = None):
        return run_pipeline(
            tenant_root,
            feed_plan,
            feed_claim,
            terminations_population,
            engagement,
            retrieved_at,
            evaluated_at,
            deprovisioned,
        )

    return run


def test_complete_snapshot_aggregate_passes(pipeline, engagement, evaluated_at) -> None:
    aggregate, existence = pipeline(TENANTS_DIR)
    assert aggregate.assertion_ref == "TERM-FEED.a"
    assert aggregate.state is VerdictState.PASS
    assert aggregate.why_code is None and aggregate.d7_family is None
    # D-S1 triple, fully populated.
    assert aggregate.manifest_version == engagement["manifest_version"]
    assert aggregate.snapshot_hash == engagement["ratified_manifest_snapshot_hash"]
    assert aggregate.contract_hash is not None
    assert aggregate.evaluated_at == evaluated_at
    assert aggregate.evidence_refs[0].startswith("collection-snapshot:sha256:")
    # Sealed: the stored hash re-computes identically.
    assert aggregate.record_hash == aggregate.compute_record_hash()
    assert existence.record_hash == existence.compute_record_hash()


def test_uncollected_corroborating_evidence_is_unknown_evidence(pipeline) -> None:
    """TERM-FEED.b without Okta events (COL02): basis_missing, never a pass."""
    _, existence = pipeline(TENANTS_DIR)
    assert existence.assertion_ref == "TERM-FEED.b"
    assert existence.state is VerdictState.UNKNOWN
    assert existence.why_code is UnknownWhyCode.UNKNOWN_EVIDENCE
    assert existence.d7_family is D7Family.BASIS_MISSING


def test_truncated_feed_turns_the_population_unknown(pipeline) -> None:
    """The seeded fixture end to end: both assertions go UNKNOWN(UNKNOWN_POPULATION).

    Population-level UNKNOWN carries no d7_family: D-U1 pins
    basis_missing → UNKNOWN_EVIDENCE, so an (UNKNOWN_POPULATION,
    basis_missing) pair is unconstructible by design (schema/verdict.py).
    """
    records = pipeline(SEEDED_TRUNCATED_DIR)
    assert len(records) == 2
    for record in records:
        assert record.state is VerdictState.UNKNOWN
        assert record.why_code is UnknownWhyCode.UNKNOWN_POPULATION
        assert record.d7_family is None
        assert record.message is not None and "trailer record missing" in record.message


def test_existence_passes_with_full_deprovisioning_evidence(pipeline) -> None:
    _, existence = pipeline(TENANTS_DIR, ALL_MEMBER_IDS)
    assert existence.state is VerdictState.PASS


def test_existence_fails_naming_the_unrevoked_member(pipeline) -> None:
    partial = tuple(m for m in ALL_MEMBER_IDS if m != "E-1073")
    _, existence = pipeline(TENANTS_DIR, partial)
    assert existence.state is VerdictState.FAIL
    assert existence.message is not None and "E-1073" in existence.message


def test_reperformance_is_byte_identical(pipeline) -> None:
    """Same inputs, twice → byte-identical serialized records (D-P3)."""
    first = [r.model_dump_json() for r in pipeline(TENANTS_DIR)]
    second = [r.model_dump_json() for r in pipeline(TENANTS_DIR)]
    assert first == second


def _claim_with_extra_assertion(feed_claim: Claim, assertion_type: AssertionType) -> Claim:
    extra = Assertion(
        assertion_id="TERM-FEED.z",
        claim_ref=feed_claim.claim_id,
        type=assertion_type,
        predicate_text="hypothetical",
        population_ref=feed_claim.population_ref,
    )
    return feed_claim.model_copy(update={"assertions": feed_claim.assertions + (extra,)})


def test_unsupported_assertion_type_is_refused_by_the_contract(
    pipeline, feed_plan, feed_claim, terminations_population, engagement, retrieved_at, evaluated_at
) -> None:
    """A TIMING assertion against a snapshot-cadence contract must refuse."""
    claim = _claim_with_extra_assertion(feed_claim, AssertionType.TIMING)
    with pytest.raises(ValueError, match="does not declare support"):
        run_pipeline(
            TENANTS_DIR,
            feed_plan,
            claim,
            terminations_population,
            engagement,
            retrieved_at,
            evaluated_at,
        )


def test_supported_but_unimplemented_type_is_refused_loudly(
    feed_plan, feed_claim, terminations_population, engagement, retrieved_at, evaluated_at
) -> None:
    """STATE is contract-supported but outside the skeleton's pair: loud refusal."""
    claim = _claim_with_extra_assertion(feed_claim, AssertionType.STATE)
    with pytest.raises(ValueError, match="EXISTENCE/AGGREGATE pair only"):
        run_pipeline(
            TENANTS_DIR,
            feed_plan,
            claim,
            terminations_population,
            engagement,
            retrieved_at,
            evaluated_at,
        )
