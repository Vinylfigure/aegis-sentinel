"""Minimal EXISTENCE evaluator — the walking-skeleton slice of EVAL01.

Pure and re-performable (D-P3): every identity field — run_id,
collected_at, spec_id/spec_hash, chain_prev — is an explicit input;
there are no clocks, ids, or environment reads in this package (the AST
purity gate enforces it). Same inputs, byte-identical verdict record.

The emitted dict conforms to schemas/verdict-record.schema.json v0.1.0:
verdict states per D-V1, UNKNOWN why-codes per D-U1 (D-7 cause families,
knowledge/01_corpus/02_design_decisions/Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md:
identity_fuzzy → UNKNOWN_POPULATION, no_basis_anywhere →
UNKNOWN_TESTABILITY). record_hash is the SHA-256 of the canonical record
with volatile fields nulled.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence

from aegis_sentinel.collectors.hris import TerminationRecord
from aegis_sentinel.reconcile.minimal import canonical_email
from aegis_sentinel.schema.enums import AssertionType, AssuranceState, UnknownWhy, VerdictState
from aegis_sentinel.schema.models import Claim, EvidenceQualityContract, Population

RECORD_SCHEMA_VERSION = "0.1.0"
TEST_FUNCTION_VERSION = "0.1.0"

# D-P3: fields excluded from the canonical hash because they cannot be
# part of their own preimage. chain_prev is NOT volatile — the chain link
# is identity, and the first record carries an explicit null.
VOLATILE_FIELDS = ("record_hash",)


def canonical_record_hash(record: Mapping) -> str:
    """SHA-256 of the canonical (sorted-key, compact) JSON of the record
    with volatile fields nulled (D-P3)."""
    canonical = {key: (None if key in VOLATILE_FIELDS else value) for key, value in record.items()}
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def evaluate_existence(
    *,
    claim: Claim,
    population: Population,
    canonical_members: Sequence[str],
    records: Sequence[TerminationRecord],
    contract: EvidenceQualityContract,
    control_id: str,
    record_id: str,
    run_id: str,
    collected_at: str,
    spec_id: str,
    spec_hash: str,
    source: str,
    source_version: str,
    completeness_ref: str,
    evidence_refs: Sequence[str],
    chain_prev: str | None = None,
    support_record_hashes: Sequence[str] = (),
) -> dict:
    """Evaluate one claim's EXISTENCE assertion over collected records.

    PASS when every canonical member of the reconciled population has a
    termination record in the feed; FAIL (with support) when any member
    lacks one; UNKNOWN(UNKNOWN_POPULATION) when the denominator has not
    reached RECONCILED — no verdict against an unreconciled population;
    UNKNOWN(UNKNOWN_TESTABILITY) when the evidence contract does not
    declare EXISTENCE among its supported assertion types.
    """
    if claim.population_id != population.id:
        raise ValueError(
            f"claim {claim.id} is scoped to {claim.population_id}, got {population.id}"
        )
    assertion = next((a for a in claim.assertions if a.type is AssertionType.EXISTENCE), None)
    if assertion is None:
        raise ValueError(f"claim {claim.id} carries no EXISTENCE assertion")

    record: dict = {
        "schema_version": RECORD_SCHEMA_VERSION,
        "record_id": record_id,
        "control_id": control_id,
        "source": source,
        "source_version": source_version,
        "run_id": run_id,
        "collected_at": collected_at,
        "record_hash": None,
        "chain_prev": chain_prev,
        "population_id": population.id,
        "population_count": len(canonical_members),
        "completeness_ref": completeness_ref,
        "spec_id": spec_id,
        "spec_hash": spec_hash,
        "test_function_version": TEST_FUNCTION_VERSION,
        "evidence_refs": list(evidence_refs),
        "severity": "high",
    }

    if population.state not in (AssuranceState.RECONCILED, AssuranceState.RATIFIED):
        record["status"] = VerdictState.UNKNOWN.value
        record["unknown_cause"] = UnknownWhy.UNKNOWN_POPULATION.value
        record["message"] = (
            f"population {population.id} is {population.state.value}; no verdict "
            "against a denominator left of RECONCILED (assurance-state ladder)"
        )
        record["support"] = {
            "field_values": {"population_state": population.state.value},
            "record_hashes": list(support_record_hashes),
        }
    elif not contract.supports(AssertionType.EXISTENCE):
        record["status"] = VerdictState.UNKNOWN.value
        record["unknown_cause"] = UnknownWhy.UNKNOWN_TESTABILITY.value
        record["message"] = (
            f"contract {contract.id} does not declare EXISTENCE among its "
            "supported assertion types — the evidence is not fit to prove this claim"
        )
        record["support"] = {
            "field_values": {
                "contract_id": contract.id,
                "supported_assertion_types": [t.value for t in contract.supported_assertion_types],
            },
            "record_hashes": list(support_record_hashes),
        }
    else:
        record_emails = {e for r in records if (e := canonical_email(r.email)) is not None}
        missing = sorted(m for m in canonical_members if m not in record_emails)
        if missing:
            record["status"] = VerdictState.FAIL.value
            record["message"] = (
                f"{len(missing)} of {len(canonical_members)} canonical members have "
                f"no termination record in the {contract.source} feed"
            )
            record["support"] = {
                "field_values": {"missing_members": missing},
                "record_hashes": list(support_record_hashes),
            }
        else:
            record["status"] = VerdictState.PASS.value
            record["message"] = (
                f"assertion {assertion.id}: all {len(canonical_members)} canonical "
                f"members have a termination record in the {contract.source} feed"
            )

    record["record_hash"] = canonical_record_hash(record)
    return record
