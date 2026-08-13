"""Minimal typed evaluator — the walking-skeleton slice of EVAL01.

Evaluates the TA-1 feed-completeness claim's EXISTENCE/AGGREGATE
assertion pair (templates/lanes/termination.json, TERM.feed-completeness)
over a reconciled terminations population, emitting fully populated,
sealed :class:`~aegis_sentinel.schema.VerdictRecord` objects. EVAL01
generalizes this to the full typed-assertion vocabulary (TIMING via
``business_days.py`` once Okta events land with COL02).

Verdict identity is the D-S1 triple: ``(manifest_version,
snapshot_hash, contract_hash)`` — the ratified-manifest snapshot hash is
a caller-supplied constant until SCH03 lands real manifest snapshots,
and ``contract_hash`` comes from the collector's EvidenceQualityContract.

UNKNOWN taxonomy (D-U1, docs/DECISIONS.md; prior art:
knowledge/01_corpus/02_design_decisions/Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md):

- A truncated population basis (partial collection) is the prior
  scaffold's population-level UNKNOWN (``src/completeness.py``): the
  denominator itself cannot be asserted, so the why-code is
  ``UNKNOWN_POPULATION``. D-U1's ratified family mapping pins
  ``basis_missing → UNKNOWN_EVIDENCE`` and ``identity_fuzzy →
  UNKNOWN_POPULATION``, and the VerdictRecord constructor enforces it —
  so the population-level record carries no ``d7_family`` rather than an
  illegal ``(UNKNOWN_POPULATION, basis_missing)`` pair.
- Required corroborating evidence not collected (the Okta
  deprovisioning events, COL02) IS the ``basis_missing`` family:
  ``UNKNOWN(UNKNOWN_EVIDENCE, d7_family=basis_missing)``.

UNKNOWN never maps to satisfied, in either shape.

STRICT purity lane (D-P3): pure functions; ``evaluated_at`` is an
explicit input; re-performance over the same inputs is byte-identical
(tested in tests/evaluate/test_minimal.py).
"""

from __future__ import annotations

from datetime import datetime

from aegis_sentinel.reconcile import ReconciliationResult
from aegis_sentinel.schema import (
    AssertionType,
    Claim,
    D7Family,
    EvidenceQualityContract,
    UnknownWhyCode,
    VerdictRecord,
    VerdictState,
)

MODULE_VERSION = "evaluate.minimal@0.1.0"

_Outcome = tuple[
    VerdictState, str | None, UnknownWhyCode | None, D7Family | None, str | None
]  # (state, message, why_code, d7_family, disposition_ref)


def _population_unknown(reconciliation: ReconciliationResult) -> _Outcome:
    """Partial collection ⇒ population-level UNKNOWN, never a partial pass."""
    message = "population basis incomplete: " + "; ".join(reconciliation.basis_notes)
    return VerdictState.UNKNOWN, message, UnknownWhyCode.UNKNOWN_POPULATION, None, None


def _aggregate_outcome(reconciliation: ReconciliationResult) -> _Outcome:
    """TERM-FEED.a: feed membership reconciles with zero undispositioned deltas."""
    if not reconciliation.basis_complete:
        return _population_unknown(reconciliation)
    deltas = reconciliation.open_deltas
    if deltas:
        return (
            VerdictState.FAIL,
            f"{len(deltas)} undispositioned reconciliation delta(s): {', '.join(deltas)}",
            None,
            None,
            None,
        )
    return (
        VerdictState.PASS,
        (
            f"population of {reconciliation.population.size} reconciled "
            "with zero undispositioned deltas"
        ),
        None,
        None,
        None,
    )


def _existence_outcome(
    reconciliation: ReconciliationResult,
    deprovisioned_member_ids: tuple[str, ...] | None,
    unresolved_member_ids: tuple[str, ...] = (),
    excepted_members: tuple[tuple[str, str], ...] = (),
) -> _Outcome:
    """TERM-FEED.b: every termination has a corresponding IdP deprovisioning event.

    ``deprovisioned_member_ids`` is the corroborating evidence set (Okta
    System Log deactivations, keyed by the population's canonical member
    id). ``None`` means that evidence was never collected — which is
    exactly the ``basis_missing`` cause family: the assertion has no
    evidence basis, so it is ``UNKNOWN(UNKNOWN_EVIDENCE)``, never a pass
    by omission.

    EVAL01 member-level extensions:

    - ``unresolved_member_ids`` — members whose canonical identity join
      failed (REC01 unresolvable bucket): their events cannot be
      attributed, so a missing event for them is the D-7
      ``identity_fuzzy`` family → ``UNKNOWN(UNKNOWN_POPULATION)``,
      routed to the human resolution queue, never guessed (D-8).
    - ``excepted_members`` — ``(member_id, disposition_ref)`` pairs
      covered by a pre-ratified disposition: a missing event for them is
      a member-level EXCEPTION, distinct from PASS and from FAIL (D-V1).

    Precedence: any hard-missing member → FAIL; else any unresolved →
    UNKNOWN; else excepted-only → EXCEPTION; else PASS.
    """
    if not reconciliation.basis_complete:
        return _population_unknown(reconciliation)
    if deprovisioned_member_ids is None:
        return (
            VerdictState.UNKNOWN,
            (
                "corroborating identity-provider deprovisioning events not "
                "collected in this slice (COL02); evidence basis missing"
            ),
            UnknownWhyCode.UNKNOWN_EVIDENCE,
            D7Family.BASIS_MISSING,
            None,
        )
    deprovisioned = set(deprovisioned_member_ids)
    unresolved = set(unresolved_member_ids)
    excepted = dict(excepted_members)
    missing = tuple(m for m in reconciliation.members if m not in deprovisioned)
    hard_missing = tuple(m for m in missing if m not in unresolved and m not in excepted)
    if hard_missing:
        return (
            VerdictState.FAIL,
            (
                f"{len(hard_missing)} terminated worker(s) with no identity-provider "
                f"deprovisioning event: {', '.join(hard_missing)}"
            ),
            None,
            None,
            None,
        )
    fuzzy = tuple(m for m in missing if m in unresolved)
    if fuzzy:
        return (
            VerdictState.UNKNOWN,
            (
                f"{len(fuzzy)} terminated worker(s) whose identity join failed; "
                "deprovisioning events cannot be attributed to them "
                f"(human resolution queue): {', '.join(fuzzy)}"
            ),
            UnknownWhyCode.UNKNOWN_POPULATION,
            D7Family.IDENTITY_FUZZY,
            None,
        )
    covered = tuple(m for m in missing if m in excepted)
    if covered:
        refs = sorted({excepted[m] for m in covered})
        return (
            VerdictState.EXCEPTION,
            (
                f"{len(covered)} terminated worker(s) without a deprovisioning event, "
                f"each covered by a ratified disposition: "
                + ", ".join(f"{m} ({excepted[m]})" for m in covered)
            ),
            None,
            None,
            ", ".join(refs),
        )
    return (
        VerdictState.PASS,
        (
            f"all {len(reconciliation.members)} terminated workers have a "
            "corresponding identity-provider deprovisioning event"
        ),
        None,
        None,
        None,
    )


def evaluate_feed_claim(
    claim: Claim,
    reconciliation: ReconciliationResult,
    contract: EvidenceQualityContract,
    manifest_version: str,
    manifest_snapshot_hash: str,
    collection_snapshot_hash: str,
    evaluated_at: datetime,
    deprovisioned_member_ids: tuple[str, ...] | None = None,
    unresolved_member_ids: tuple[str, ...] = (),
    excepted_members: tuple[tuple[str, str], ...] = (),
    extra_evidence_refs: tuple[str, ...] = (),
) -> tuple[VerdictRecord, ...]:
    """Evaluate the feed-completeness claim's assertions; seal every record.

    Pure function of its inputs: ``evaluated_at`` is explicit, the
    D-S1 triple is threaded onto every record, ``evidence_refs`` names
    the collection snapshot hash, and each record is sealed
    (``record_hash`` computed) so re-performance over the same inputs
    is byte-identical.
    """
    contract_hash = contract.contract_hash or contract.compute_contract_hash()
    records: list[VerdictRecord] = []
    for assertion in claim.assertions:
        if assertion.type not in contract.supported_assertion_types:
            raise ValueError(
                f"assertion {assertion.assertion_id} is {assertion.type.value}; the "
                "evidence contract does not declare support for that assertion type"
            )
        if assertion.type is AssertionType.AGGREGATE:
            state, message, why_code, d7_family, disposition_ref = _aggregate_outcome(
                reconciliation
            )
        elif assertion.type is AssertionType.EXISTENCE:
            state, message, why_code, d7_family, disposition_ref = _existence_outcome(
                reconciliation,
                deprovisioned_member_ids,
                unresolved_member_ids,
                excepted_members,
            )
        else:
            raise ValueError(
                f"assertion {assertion.assertion_id} is {assertion.type.value}; the "
                "walking skeleton evaluates the TA-1 EXISTENCE/AGGREGATE pair only "
                "(EVAL01 generalizes)"
            )
        records.append(
            VerdictRecord(
                claim_ref=claim.claim_id,
                assertion_ref=assertion.assertion_id,
                population_ref=assertion.population_ref,
                manifest_version=manifest_version,
                snapshot_hash=manifest_snapshot_hash,
                contract_hash=contract_hash,
                state=state,
                evaluated_at=evaluated_at,
                message=message,
                why_code=why_code,
                d7_family=d7_family,
                disposition_ref=disposition_ref,
                evidence_refs=(
                    f"collection-snapshot:sha256:{collection_snapshot_hash}",
                    *extra_evidence_refs,
                ),
            ).sealed()
        )
    return tuple(records)
