"""EVAL01 — the typed assertion evaluator (TIMING / NON_EXISTENCE / AGGREGATE).

Generalizes the walking skeleton (``minimal.py``) to the termination
lane's full assertion set (docs/HANDOFF.md §4 EVAL01; the AM-06-derived
matrix in knowledge/01_corpus/03_testing_libraries/
SOC2_Control_Testing_Matrix.md):

- **TIMING** (TA-2): "revoked ≤ N business days" per terminated member,
  business-day math from ``business_days.py`` (D-P4), joined to the
  IdP deactivation event and corroborated by the downstream removal
  event. Late is FAIL with per-member evidence; a member whose events
  were never collected is UNKNOWN(UNKNOWN_EVIDENCE, basis_missing); a
  member whose identity failed the canonical join is
  UNKNOWN(UNKNOWN_POPULATION, identity_fuzzy) — the D-7 families
  (knowledge/01_corpus/02_design_decisions/Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md),
  which route to permission review and the human resolution queue
  respectively and never map to satisfied.
- **NON_EXISTENCE** (TA-3, per downstream system): no terminated worker
  retains an active account. An active unattributable account (no
  identity key joins it to anything) is a FAIL — non-existence cannot
  be proven while an unaccountable account is live. An active account
  covered by a ratified disposition is a member-level EXCEPTION (D-V1:
  the verdict carries its ``disposition_ref``); an active identity
  whose workforce attribution is unproven is a member-level UNKNOWN
  (the negative-space population question, PRD-v3 §2).
- **AGGREGATE over the identity join** (TERM-JOIN.a): the canonical
  join must resolve with zero undispositioned deltas; open deltas —
  negative space included — make the population unprovable:
  UNKNOWN(UNKNOWN_POPULATION).
- **EXCLUDED**: a ratified scope exclusion (F-4: a human ratified it;
  D-V1: the record must carry its ``ratification_ref``) produces one
  EXCLUDED verdict record — exclusion is visible, never silent.

Assertion-level state is the worst member state, in this precedence:
FAIL > UNKNOWN > EXCEPTION > PASS. A verdict is one sealed
:class:`~aegis_sentinel.schema.VerdictRecord` per (claim, assertion,
population) triple (D-S1); per-member evidence rides in the message
deterministically.

STRICT purity lane (D-P3): pure functions; ``evaluated_at`` is an
explicit input; re-performance over the same inputs is byte-identical
(tests/evaluate/test_assertions.py).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Sequence

from pydantic import Field

from aegis_sentinel.evaluate.business_days import business_days_between
from aegis_sentinel.reconcile import ReconciliationResult
from aegis_sentinel.schema import (
    AegisModel,
    Assertion,
    AssertionType,
    Claim,
    D7Family,
    EvidenceQualityContract,
    UnknownWhyCode,
    VerdictRecord,
    VerdictState,
    sha256_canonical,
)

MODULE_VERSION = "evaluate.assertions@0.1.0"

#: Assertion-level aggregation precedence: the worst member wins.
_PRECEDENCE: tuple[VerdictState, ...] = (
    VerdictState.FAIL,
    VerdictState.UNKNOWN,
    VerdictState.EXCEPTION,
    VerdictState.PASS,
)


class TimingCase(AegisModel):
    """One terminated member's revocation-timing evidence (TA-2).

    ``unresolved`` marks a member whose canonical identity join failed —
    the events may exist under an identity this member cannot be
    deterministically linked to (D-8: never guessed).
    """

    member_key: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    termination_date: date
    idp_deactivated_on: date | None = None
    downstream_removed_on: date | None = None
    unresolved: bool = False
    disposition_ref: str | None = None


class AccountCase(AegisModel):
    """One account's residual-access evidence (TA-3 NON_EXISTENCE)."""

    member_key: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    active: bool
    terminated: bool
    #: The account joins to at least one identity key (email/employee_id).
    identity_known: bool
    #: The identity is attributable to the engagement's workforce
    #: (authoritative anchor or in-domain active workforce).
    workforce_attributable: bool
    dormant: bool = False
    disposition_ref: str | None = None


class RatifiedScopeExclusion(AegisModel):
    """A human-ratified exclusion of one system's claim from scope (F-4)."""

    ratification_ref: str = Field(min_length=1)
    system: str = Field(min_length=1)
    claim_ref: str = Field(min_length=1)
    assertion_ref: str = Field(min_length=1)
    population_ref: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    ratified_by: str = Field(min_length=1)


class _MemberFinding(AegisModel):
    state: VerdictState
    line: str
    why_code: UnknownWhyCode | None = None
    d7_family: D7Family | None = None
    disposition_ref: str | None = None


def _single_assertion(claim: Claim, expected: AssertionType) -> Assertion:
    matches = [a for a in claim.assertions if a.type is expected]
    if len(matches) != 1:
        raise ValueError(
            f"claim {claim.claim_id!r} must carry exactly one {expected.value} "
            f"assertion; found {len(matches)}"
        )
    return matches[0]


def _require_support(assertion: Assertion, contract: EvidenceQualityContract) -> None:
    if assertion.type not in contract.supported_assertion_types:
        raise ValueError(
            f"assertion {assertion.assertion_id} is {assertion.type.value}; the "
            "evidence contract does not declare support for that assertion type"
        )


def _aggregate_findings(
    findings: Sequence[_MemberFinding],
) -> tuple[VerdictState, UnknownWhyCode | None, D7Family | None, str | None]:
    """Worst-state aggregation with deterministic UNKNOWN-why selection.

    When UNKNOWN members mix causes, the population cause wins
    (identity_fuzzy → UNKNOWN_POPULATION) — an unresolvable member is a
    denominator problem before it is an evidence problem (D-7).
    """
    states = {f.state for f in findings}
    for state in _PRECEDENCE:
        if state in states:
            worst = state
            break
    else:
        worst = VerdictState.PASS
    why: UnknownWhyCode | None = None
    family: D7Family | None = None
    disposition_ref: str | None = None
    if worst is VerdictState.UNKNOWN:
        unknowns = [f for f in findings if f.state is VerdictState.UNKNOWN]
        population = [f for f in unknowns if f.why_code is UnknownWhyCode.UNKNOWN_POPULATION]
        chosen = population[0] if population else unknowns[0]
        why, family = chosen.why_code, chosen.d7_family
    if worst is VerdictState.EXCEPTION:
        refs = sorted({f.disposition_ref for f in findings if f.disposition_ref})
        disposition_ref = ", ".join(refs)
    return worst, why, family, disposition_ref


def _seal(
    claim: Claim,
    assertion: Assertion,
    state: VerdictState,
    message: str,
    contract_hash: str,
    manifest_version: str,
    manifest_snapshot_hash: str,
    evaluated_at: datetime,
    evidence_refs: tuple[str, ...],
    why_code: UnknownWhyCode | None = None,
    d7_family: D7Family | None = None,
    disposition_ref: str | None = None,
    ratification_ref: str | None = None,
) -> VerdictRecord:
    return VerdictRecord(
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
        ratification_ref=ratification_ref,
        evidence_refs=evidence_refs,
    ).sealed()


def evaluate_timing_claim(
    claim: Claim,
    cases: Sequence[TimingCase],
    contract: EvidenceQualityContract,
    manifest_version: str,
    manifest_snapshot_hash: str,
    evidence_refs: tuple[str, ...],
    evaluated_at: datetime,
    limit_business_days: int = 5,
) -> VerdictRecord:
    """TA-2: every termination revoked within the business-day limit."""
    assertion = _single_assertion(claim, AssertionType.TIMING)
    _require_support(assertion, contract)
    contract_hash = contract.contract_hash or contract.compute_contract_hash()

    findings: list[_MemberFinding] = []
    for case in sorted(cases, key=lambda c: c.member_key.casefold()):
        if case.disposition_ref is not None:
            findings.append(
                _MemberFinding(
                    state=VerdictState.EXCEPTION,
                    line=(
                        f"{case.display_name}: covered by ratified disposition "
                        f"{case.disposition_ref}"
                    ),
                    disposition_ref=case.disposition_ref,
                )
            )
            continue
        if case.unresolved:
            findings.append(
                _MemberFinding(
                    state=VerdictState.UNKNOWN,
                    line=(
                        f"{case.display_name}: canonical identity join failed; "
                        "revocation events cannot be attributed (human resolution queue)"
                    ),
                    why_code=UnknownWhyCode.UNKNOWN_POPULATION,
                    d7_family=D7Family.IDENTITY_FUZZY,
                )
            )
            continue
        if case.idp_deactivated_on is None:
            findings.append(
                _MemberFinding(
                    state=VerdictState.UNKNOWN,
                    line=(
                        f"{case.display_name}: no IdP deactivation event collected "
                        "for the tested window; evidence basis missing"
                    ),
                    why_code=UnknownWhyCode.UNKNOWN_EVIDENCE,
                    d7_family=D7Family.BASIS_MISSING,
                )
            )
            continue
        elapsed = business_days_between(case.termination_date, case.idp_deactivated_on)
        removal = (
            f", downstream removal {case.downstream_removed_on.isoformat()}"
            if case.downstream_removed_on is not None
            else ""
        )
        line = (
            f"{case.display_name}: terminated {case.termination_date.isoformat()}, "
            f"IdP deactivation {case.idp_deactivated_on.isoformat()}{removal} = "
            f"{elapsed} business day(s)"
        )
        if elapsed > limit_business_days:
            findings.append(
                _MemberFinding(
                    state=VerdictState.FAIL,
                    line=f"{line} (> {limit_business_days})",
                )
            )
        else:
            findings.append(_MemberFinding(state=VerdictState.PASS, line=line))

    state, why, family, disposition_ref = _aggregate_findings(findings)
    window = contract.time_window
    header = (
        f"{len(findings)} termination(s) tested over "
        f"{window.start.isoformat()}..{window.end.isoformat()} against the "
        f"{limit_business_days}-business-day limit"
    )
    message = "; ".join([header, *(f.line for f in findings)])
    return _seal(
        claim,
        assertion,
        state,
        message,
        contract_hash,
        manifest_version,
        manifest_snapshot_hash,
        evaluated_at,
        evidence_refs,
        why_code=why,
        d7_family=family,
        disposition_ref=disposition_ref,
    )


def evaluate_non_existence_claim(
    claim: Claim,
    cases: Sequence[AccountCase],
    contract: EvidenceQualityContract,
    manifest_version: str,
    manifest_snapshot_hash: str,
    evidence_refs: tuple[str, ...],
    evaluated_at: datetime,
) -> VerdictRecord:
    """TA-3: no terminated worker retains an active account (per system)."""
    assertion = _single_assertion(claim, AssertionType.NON_EXISTENCE)
    _require_support(assertion, contract)
    contract_hash = contract.contract_hash or contract.compute_contract_hash()

    findings: list[_MemberFinding] = []
    clean = 0
    for case in sorted(cases, key=lambda c: c.member_key.casefold()):
        if not case.active:
            clean += 1  # deprovisioned/absent: exactly what NON_EXISTENCE wants
            continue
        if case.disposition_ref is not None:
            anomaly = (
                "active despite termination"
                if case.terminated
                else "active account outside the workforce join"
            )
            findings.append(
                _MemberFinding(
                    state=VerdictState.EXCEPTION,
                    line=(
                        f"{case.display_name}: {anomaly}, covered by "
                        f"ratified disposition {case.disposition_ref}"
                    ),
                    disposition_ref=case.disposition_ref,
                )
            )
            continue
        if case.terminated:
            findings.append(
                _MemberFinding(
                    state=VerdictState.FAIL,
                    line=f"{case.display_name}: terminated worker with an active account",
                )
            )
            continue
        if not case.identity_known:
            dormancy = " (dormant)" if case.dormant else ""
            findings.append(
                _MemberFinding(
                    state=VerdictState.FAIL,
                    line=(
                        f"{case.display_name}: active local account{dormancy} joins to no "
                        "identity in any source; non-existence cannot be asserted while "
                        "an unaccountable account is live"
                    ),
                )
            )
            continue
        if not case.workforce_attributable:
            findings.append(
                _MemberFinding(
                    state=VerdictState.UNKNOWN,
                    line=(
                        f"{case.display_name}: active account with a known identity the "
                        "authoritative workforce source cannot account for (negative "
                        "space — population question)"
                    ),
                    why_code=UnknownWhyCode.UNKNOWN_POPULATION,
                    d7_family=None,
                )
            )
            continue
        clean += 1  # active, attributable, not terminated: in-scope workforce

    state, why, family, disposition_ref = _aggregate_findings(findings)
    header = f"{len(cases)} account(s) tested; {clean} clean"
    message = (
        "; ".join([header, *(f.line for f in findings)])
        if findings
        else (f"{header}; no terminated worker retains an active account")
    )
    return _seal(
        claim,
        assertion,
        state,
        message,
        contract_hash,
        manifest_version,
        manifest_snapshot_hash,
        evaluated_at,
        evidence_refs,
        why_code=why,
        d7_family=family,
        disposition_ref=disposition_ref,
    )


def evaluate_attributability_claim(
    claim: Claim,
    reconciliation: ReconciliationResult,
    contract: EvidenceQualityContract,
    manifest_version: str,
    manifest_snapshot_hash: str,
    evidence_refs: tuple[str, ...],
    evaluated_at: datetime,
) -> VerdictRecord:
    """TERM-JOIN.a: the canonical join resolves with zero open deltas.

    Open deltas — the negative space included — mean the population
    cannot be shown complete: UNKNOWN(UNKNOWN_POPULATION), never a
    partial pass (docs/HANDOFF.md §2).
    """
    assertion = _single_assertion(claim, AssertionType.AGGREGATE)
    _require_support(assertion, contract)
    contract_hash = contract.contract_hash or contract.compute_contract_hash()

    if not reconciliation.basis_complete:
        message = "population basis incomplete: " + "; ".join(reconciliation.basis_notes)
        state: VerdictState = VerdictState.UNKNOWN
        why: UnknownWhyCode | None = UnknownWhyCode.UNKNOWN_POPULATION
    else:
        open_deltas = reconciliation.open_delta_objects
        if open_deltas:
            lines = [
                (
                    f"{d.bucket}: {d.display_name or d.member_key} "
                    f"(present in {', '.join(d.sources_present)}; "
                    f"absent from {', '.join(d.sources_absent) or 'n/a'})"
                )
                for d in open_deltas
            ]
            message = (
                f"{len(open_deltas)} undispositioned identity-join delta(s) — the "
                "population cannot be shown complete: " + "; ".join(lines)
            )
            state = VerdictState.UNKNOWN
            why = UnknownWhyCode.UNKNOWN_POPULATION
        else:
            message = (
                f"canonical identity join over {len(reconciliation.members)} member(s) "
                "resolved with zero undispositioned deltas"
            )
            state = VerdictState.PASS
            why = None
    return _seal(
        claim,
        assertion,
        state,
        message,
        contract_hash,
        manifest_version,
        manifest_snapshot_hash,
        evaluated_at,
        evidence_refs,
        why_code=why,
    )


def evaluate_ratified_exclusion(
    exclusion: RatifiedScopeExclusion,
    manifest_version: str,
    manifest_snapshot_hash: str,
    evaluated_at: datetime,
) -> VerdictRecord:
    """One EXCLUDED verdict record for a ratified scope exclusion.

    Nothing exits silently (PRD-v3 §1): the excluded system's claim gets
    a record carrying the human ratification reference. No evidence
    contract exists for an excluded system, so the D-S1 ``contract_hash``
    slot is filled with the canonical hash of the ratified exclusion
    record itself — the artifact that authorized the exclusion IS the
    record's basis.
    """
    return VerdictRecord(
        claim_ref=exclusion.claim_ref,
        assertion_ref=exclusion.assertion_ref,
        population_ref=exclusion.population_ref,
        manifest_version=manifest_version,
        snapshot_hash=manifest_snapshot_hash,
        contract_hash=sha256_canonical(exclusion),
        state=VerdictState.EXCLUDED,
        evaluated_at=evaluated_at,
        message=(
            f"system {exclusion.system!r} excluded from scope by "
            f"{exclusion.ratified_by}: {exclusion.rationale}"
        ),
        ratification_ref=exclusion.ratification_ref,
        evidence_refs=(f"ratification:{exclusion.ratification_ref}",),
    ).sealed()
