"""EVAL01 — typed assertion evaluator: TIMING and NON-EXISTENCE.

Pure and re-performable (D-P3): every identity field — run_id,
collected_at, spec_id/spec_hash, chain_prev — is an explicit input;
there are no clocks, ids, or environment reads in this package (the AST
purity gate enforces it). Same inputs, byte-identical verdict records.

Record emission reuses evaluate.minimal's helpers (canonical_record_hash
and the pinned schema/test-function versions — imported, never copied);
every emitted dict conforms to schemas/verdict-record.schema.json
v0.1.0. Verdict states per D-V1 (EXCLUDED carries ratification_ref,
EXCEPTION carries disposition_ref); UNKNOWN why-codes per D-U1 mapping
the D-7 cause families (knowledge/01_corpus/02_design_decisions/
Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md): a member with no
revocation event inside the covered window is basis_missing →
UNKNOWN_EVIDENCE.

Business-day math per D-P4: Mon–Fri only, no holiday calendar in V1.
The manifest carries an optional holiday_calendar field — empty in V1 —
so adding one later is a manifest change, not a code change here.
"""

from collections.abc import Mapping, Sequence
from datetime import date, timedelta

from pydantic import Field, model_validator

from aegis_sentinel.evaluate.minimal import (
    RECORD_SCHEMA_VERSION,
    TEST_FUNCTION_VERSION,
    canonical_record_hash,
)
from aegis_sentinel.reconcile.minimal import canonical_email
from aegis_sentinel.schema.enums import AssertionType, AssuranceState, UnknownWhy, VerdictState
from aegis_sentinel.schema.models import (
    Base,
    Claim,
    EvidenceQualityContract,
    Population,
    TimingConstraint,
)

SATURDAY = 5  # date.weekday(): Mon=0 .. Sun=6


def business_days_between(start: date, end: date) -> int:
    """Business days elapsed from start to end: the count of Mon–Fri
    days in the half-open interval (start, end].

    Mon–Fri only, no holiday calendar (D-P4): the manifest carries an
    optional holiday_calendar field, empty in V1, so holidays arrive as
    a manifest change, not a change to this function. Fri→Mon is 1
    business day, Fri→next Fri is 5, same-day is 0, and a weekend start
    counts only the business days that follow it (Sat→Mon is 1).
    """
    if end < start:
        raise ValueError(f"end {end} precedes start {start}")
    days = (end - start).days
    full_weeks, remainder = divmod(days, 7)
    count = full_weeks * 5
    for offset in range(full_weeks * 7 + 1, days + 1):
        if (start + timedelta(days=offset)).weekday() < SATURDAY:
            count += 1
    return count


class MemberTimeline(Base):
    """One member's termination-lane timeline as collected: the
    authoritative termination date and the observed revocation date, or
    None when no revocation event was found inside the covered window
    (which is an UNKNOWN_EVIDENCE verdict, never a silent pass)."""

    member: str = Field(min_length=1)
    termination_date: date
    revocation_date: date | None = None

    @model_validator(mode="after")
    def _canonical_member(self):
        if canonical_email(self.member) != self.member:
            raise ValueError(f"member {self.member!r} is not a canonical identity")
        return self


def _base_record(
    *,
    record_id: str,
    control_id: str,
    source: str,
    source_version: str,
    run_id: str,
    collected_at: str,
    chain_prev: str | None,
    population: Population,
    population_count: int,
    completeness_ref: str,
    spec_id: str,
    spec_hash: str,
    evidence_refs: Sequence[str],
    claim_id: str,
    assertion_id: str,
) -> dict:
    """The identity block shared by every emitted verdict record —
    field-for-field the shape evaluate.minimal.evaluate_existence emits,
    finalized by the imported canonical_record_hash (D-P3)."""
    return {
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
        "population_count": population_count,
        "completeness_ref": completeness_ref,
        "spec_id": spec_id,
        "spec_hash": spec_hash,
        "test_function_version": TEST_FUNCTION_VERSION,
        "evidence_refs": list(evidence_refs),
        "severity": "high",
        "claim_id": claim_id,
        "assertion_id": assertion_id,
    }


def _guard(
    claim: Claim,
    population: Population,
    contract: EvidenceQualityContract,
    assertion_type: AssertionType,
) -> tuple[UnknownWhy, str, dict] | None:
    """The two evidence-fitness gates shared with evaluate.minimal:
    no verdict against a denominator left of RECONCILED
    (UNKNOWN_POPULATION), and no verdict from a contract that does not
    declare the assertion type (UNKNOWN_TESTABILITY)."""
    if claim.population_id != population.id:
        raise ValueError(
            f"claim {claim.id} is scoped to {claim.population_id}, got {population.id}"
        )
    if not any(a.type is assertion_type for a in claim.assertions):
        raise ValueError(f"claim {claim.id} carries no {assertion_type.value} assertion")
    if population.state not in (AssuranceState.RECONCILED, AssuranceState.RATIFIED):
        return (
            UnknownWhy.UNKNOWN_POPULATION,
            f"population {population.id} is {population.state.value}; no verdict "
            "against a denominator left of RECONCILED (assurance-state ladder)",
            {"population_state": population.state.value},
        )
    if not contract.supports(assertion_type):
        return (
            UnknownWhy.UNKNOWN_TESTABILITY,
            f"contract {contract.id} does not declare {assertion_type.value} among its "
            "supported assertion types — the evidence is not fit to prove this claim",
            {
                "contract_id": contract.id,
                "supported_assertion_types": [t.value for t in contract.supported_assertion_types],
            },
        )
    return None


def evaluate_timing(
    events: Sequence[MemberTimeline],
    constraint: TimingConstraint,
    *,
    claim: Claim,
    population: Population,
    contract: EvidenceQualityContract,
    exception_dispositions: Mapping[str, str] = {},
    boundary_exclusions: Mapping[str, str] = {},
    control_id: str,
    record_id_prefix: str,
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
) -> tuple[dict, ...]:
    """Evaluate one claim's TIMING assertion, one verdict record per
    member, hash-chained in canonical member order.

    Per member (D-V1 states, never interchangeable):
    - EXCLUDED with its ratification_ref when the member is boundary-
      excluded (the ratified exclusion travels with the verdict, D-V1);
    - EXCEPTION with its disposition_ref when the member ref carries a
      disposition (a legitimate, dispositioned exception, D-V1);
    - UNKNOWN(UNKNOWN_EVIDENCE) when no revocation event exists inside
      the covered window — D-7 basis_missing per D-U1: absence of
      evidence is an UNKNOWN with a why-code, never a silent pass;
    - FAIL when revocation exceeded constraint.days business days after
      termination (D-P4 business-day math);
    - PASS otherwise.
    """
    if not constraint.business_days:
        raise ValueError("only business-day timing constraints are implemented (D-P4)")
    guard = _guard(claim, population, contract, AssertionType.TIMING)
    assertion = next(a for a in claim.assertions if a.type is AssertionType.TIMING)
    window = contract.time_window

    records: list[dict] = []
    prev = chain_prev
    for timeline in sorted(events, key=lambda t: t.member):
        member = timeline.member
        record = _base_record(
            record_id=f"{record_id_prefix}-{member}",
            control_id=control_id,
            source=source,
            source_version=source_version,
            run_id=run_id,
            collected_at=collected_at,
            chain_prev=prev,
            population=population,
            population_count=len(events),
            completeness_ref=completeness_ref,
            spec_id=spec_id,
            spec_hash=spec_hash,
            evidence_refs=evidence_refs,
            claim_id=claim.id,
            assertion_id=assertion.id,
        )
        if guard is not None:
            why, message, field_values = guard
            record["status"] = VerdictState.UNKNOWN.value
            record["unknown_cause"] = why.value
            record["message"] = message
            record["support"] = {
                "field_values": field_values,
                "record_hashes": list(support_record_hashes),
            }
        elif member in boundary_exclusions:
            record["status"] = VerdictState.EXCLUDED.value
            record["ratification_ref"] = boundary_exclusions[member]
            record["message"] = (
                f"{member} is outside the ratified boundary "
                f"({boundary_exclusions[member]}); no timing verdict owed (D-V1)"
            )
        elif member in exception_dispositions:
            record["status"] = VerdictState.EXCEPTION.value
            record["disposition_ref"] = exception_dispositions[member]
            record["message"] = (
                f"{member} carries dispositioned exception "
                f"{exception_dispositions[member]} (D-V1: EXCEPTION, never a silent PASS)"
            )
        elif timeline.revocation_date is None:
            record["status"] = VerdictState.UNKNOWN.value
            record["unknown_cause"] = UnknownWhy.UNKNOWN_EVIDENCE.value
            record["message"] = (
                f"no revocation event for {member} inside the covered window "
                f"{window.start.isoformat()}..{window.end.isoformat()} — "
                "D-7 basis_missing → UNKNOWN_EVIDENCE (D-U1)"
            )
            record["support"] = {
                "field_values": {
                    "member": member,
                    "termination_date": timeline.termination_date.isoformat(),
                },
                "record_hashes": list(support_record_hashes),
            }
        else:
            if timeline.revocation_date <= timeline.termination_date:
                elapsed = 0
            else:
                elapsed = business_days_between(timeline.termination_date, timeline.revocation_date)
            if elapsed > constraint.days:
                record["status"] = VerdictState.FAIL.value
                record["message"] = (
                    f"revocation for {member} took {elapsed} business days, "
                    f"exceeding the {constraint.days}-business-day constraint (D-P4)"
                )
                record["support"] = {
                    "field_values": {
                        "member": member,
                        "termination_date": timeline.termination_date.isoformat(),
                        "revocation_date": timeline.revocation_date.isoformat(),
                        "elapsed_business_days": elapsed,
                        "constraint_business_days": constraint.days,
                    },
                    "record_hashes": list(support_record_hashes),
                }
            else:
                record["status"] = VerdictState.PASS.value
                record["message"] = (
                    f"revocation for {member} within {elapsed} business days "
                    f"(constraint: {constraint.days}, D-P4)"
                )
        record["record_hash"] = canonical_record_hash(record)
        prev = record["record_hash"]
        records.append(record)
    return tuple(records)


def evaluate_non_existence(
    access_holders: Sequence[str],
    terminated: Sequence[str],
    *,
    claim: Claim,
    population: Population,
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
    """Evaluate one claim's NON-EXISTENCE assertion: no terminated
    member may still exist in the access-holder set.

    FAIL names every residual-access member (the support carries refs,
    not counts — counts are diagnostics, never evidence); PASS when the
    intersection is empty; the shared gates emit UNKNOWN_POPULATION /
    UNKNOWN_TESTABILITY as in evaluate.minimal.evaluate_existence.
    """
    guard = _guard(claim, population, contract, AssertionType.NON_EXISTENCE)
    assertion = next(a for a in claim.assertions if a.type is AssertionType.NON_EXISTENCE)
    terminated_keys = {e for m in terminated if (e := canonical_email(m)) is not None}
    holder_keys = {e for m in access_holders if (e := canonical_email(m)) is not None}
    residual = sorted(terminated_keys & holder_keys)

    record = _base_record(
        record_id=record_id,
        control_id=control_id,
        source=source,
        source_version=source_version,
        run_id=run_id,
        collected_at=collected_at,
        chain_prev=chain_prev,
        population=population,
        population_count=len(terminated_keys),
        completeness_ref=completeness_ref,
        spec_id=spec_id,
        spec_hash=spec_hash,
        evidence_refs=evidence_refs,
        claim_id=claim.id,
        assertion_id=assertion.id,
    )
    if guard is not None:
        why, message, field_values = guard
        record["status"] = VerdictState.UNKNOWN.value
        record["unknown_cause"] = why.value
        record["message"] = message
        record["support"] = {
            "field_values": field_values,
            "record_hashes": list(support_record_hashes),
        }
    elif residual:
        record["status"] = VerdictState.FAIL.value
        record["message"] = (
            f"{len(residual)} terminated member(s) still hold access in "
            f"{contract.source} — residual access is a NON-EXISTENCE failure"
        )
        record["support"] = {
            "field_values": {"residual_access_members": residual},
            "record_hashes": list(support_record_hashes),
        }
    else:
        record["status"] = VerdictState.PASS.value
        record["message"] = (
            f"no terminated member exists in the {contract.source} access-holder set "
            f"({len(terminated_keys)} terminated members checked)"
        )
    record["record_hash"] = canonical_record_hash(record)
    return record
