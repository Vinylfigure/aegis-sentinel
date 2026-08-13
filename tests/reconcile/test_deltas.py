"""REC01 ladder gates: DISCOVERED→RECONCILED only when deltas are
dispositioned; RECONCILED→RATIFIED only with a ratifier identity.

docs/HANDOFF.md §2 locked ruling — ladder states only, never a
coverage percentage against an unratified denominator.
"""

from __future__ import annotations

from datetime import date

import pytest

from aegis_sentinel.reconcile import (
    KeyValue,
    MemberKind,
    OpenDeltasError,
    RatifiedDeltaDisposition,
    SourceMember,
    SourceMembers,
    open_delta_refs,
    reconcile_population,
    to_ratified,
    to_reconciled,
)
from aegis_sentinel.schema import AssuranceState, DispositionValue

from .test_setops import DOMAIN, m, population, src


def _open_delta_result():
    return reconcile_population(
        population(),
        [
            src("auth", m("auth", "w1", signal=True, employee_id="E-1", email="w1@corp.test")),
            src(
                "contrib",
                m("contrib", "w1", email="w1@corp.test"),
                m("contrib", "ghost", active=True, email="ghost@vendor.test"),
            ),
        ],
        identity_domain=DOMAIN,
        delta_owner="owner",
    )


def test_open_deltas_block_reconciled() -> None:
    result = _open_delta_result()
    with pytest.raises(OpenDeltasError, match="undispositioned delta"):
        to_reconciled(result.population, result)
    # The population stays DISCOVERED, carrying the open-delta refs.
    assert result.population.state is AssuranceState.DISCOVERED
    refs = open_delta_refs(result, "owner")
    assert refs and all(r.owner == "owner" for r in refs)


def test_dispositioned_deltas_unblock_reconciled_then_ratified() -> None:
    result = reconcile_population(
        population(),
        [
            src("auth", m("auth", "w1", signal=True, employee_id="E-1", email="w1@corp.test")),
            src(
                "contrib",
                m("contrib", "w1", email="w1@corp.test"),
                m("contrib", "ghost", active=True, email="ghost@vendor.test"),
            ),
        ],
        dispositions=(
            RatifiedDeltaDisposition(
                disposition_ref="DISP-9",
                member_keys=("ghost@vendor.test",),
                value=DispositionValue.VENDOR_MANAGED,
                justification="ratified vendor account",
                owner="owner",
                review_date=date(2026, 12, 31),
                ratified_by="owner (Ratifier)",
            ),
        ),
        identity_domain=DOMAIN,
    )
    reconciled = to_reconciled(result.population, result)
    assert reconciled.state is AssuranceState.RECONCILED
    assert reconciled.open_deltas == ()
    ratified = to_ratified(reconciled, "owner (Ratifier)")
    assert ratified.state is AssuranceState.RATIFIED


def test_ratification_requires_a_named_human() -> None:
    result = reconcile_population(
        population(),
        [
            src("auth", m("auth", "w1", employee_id="E-1", email="w1@corp.test")),
            src("contrib", m("contrib", "w1", email="w1@corp.test")),
        ],
        identity_domain=DOMAIN,
    )
    reconciled = to_reconciled(result.population, result)
    with pytest.raises(ValueError, match="ratifier identity"):
        to_ratified(reconciled, "   ")


def test_wrong_population_is_rejected() -> None:
    result = _open_delta_result()
    other = population(population_id="P.other")
    with pytest.raises(ValueError, match="not population"):
        to_reconciled(other, result)


def test_source_member_reexports_are_usable() -> None:
    member = SourceMember(
        source_id="auth",
        keys=(KeyValue(key="email", value="a@corp.test"),),
        display_name="a",
        kind=MemberKind.HUMAN,
    )
    assert SourceMembers(source_id="auth", complete=True, members=(member,)).members
