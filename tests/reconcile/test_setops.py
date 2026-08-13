"""REC01 set reconciliation: six buckets, negative space, dispositions.

Synthetic populations exercising every bucket, plus the fixture-tenant
engagement shapes (the poison table in tests/fixtures/tenants/README.md)
via the identity-join population. Dispositions applied here are always
pre-ratified human records — the reconciler never manufactures one
(PRD-v3 §4).
"""

from __future__ import annotations

from datetime import date

import pytest

from aegis_sentinel.reconcile import (
    DeltaObject,
    KeyValue,
    MemberKind,
    RatifiedDeltaDisposition,
    SourceMember,
    SourceMembers,
    reconcile_population,
)
from aegis_sentinel.schema import (
    AssuranceState,
    DerivationRule,
    DispositionValue,
    Period,
    Population,
    PopulationType,
    Source,
    SourceRole,
)

DOMAIN = "corp.test"


def population(
    *,
    population_id: str = "P.join",
    type_: PopulationType = PopulationType.RELATIONSHIP,
    sources: tuple[tuple[str, SourceRole], ...] = (
        ("auth", SourceRole.AUTHORITATIVE),
        ("contrib", SourceRole.CONTRIBUTING),
    ),
    derivation_refs: tuple[str, ...] | None = None,
) -> Population:
    refs = derivation_refs or tuple(s for s, _ in sources)
    return Population(
        population_id=population_id,
        name=population_id,
        type=type_,
        definition="synthetic",
        derivation_rule=DerivationRule(rule_text="synthetic", source_refs=refs),
        sources=tuple(Source(source_id=s, role=r) for s, r in sources),
        period=Period(start=date(2026, 1, 1), end=date(2026, 6, 30)),
        state=AssuranceState.DEFINED,
    )


def m(
    source: str,
    display: str,
    *,
    active: bool = False,
    signal: bool = False,
    kind: MemberKind = MemberKind.HUMAN,
    **keys: str,
) -> SourceMember:
    return SourceMember(
        source_id=source,
        keys=tuple(KeyValue(key=k, value=v) for k, v in keys.items()),
        display_name=display,
        kind=kind,
        active=active,
        termination_signal=signal,
    )


def src(source_id: str, *members: SourceMember) -> SourceMembers:
    return SourceMembers(source_id=source_id, complete=True, members=members)


def disposition(ref: str, *member_keys: str) -> RatifiedDeltaDisposition:
    return RatifiedDeltaDisposition(
        disposition_ref=ref,
        member_keys=member_keys,
        value=DispositionValue.NA_WITH_RATIONALE,
        justification="ratified for the test engagement",
        owner="owner",
        review_date=date(2026, 9, 30),
        ratified_by="owner (Ratifier)",
    )


def test_anchored_clusters_are_intersection_members() -> None:
    result = reconcile_population(
        population(),
        [
            src("auth", m("auth", "w1", signal=True, employee_id="E-1", email="w1@corp.test")),
            src("contrib", m("contrib", "w1", email="w1@corp.test")),
        ],
        identity_domain=DOMAIN,
    )
    assert result.members == ("E-1",)
    assert result.intersection == ("E-1",)
    assert result.deltas == ()
    assert result.population.state is AssuranceState.DISCOVERED
    assert result.canonical_identity_keys == ("employee_id", "email", "login")


def test_negative_space_active_identity_is_left_only_with_sources_absent() -> None:
    """The contractor shape: active downstream, unknown to the
    authoritative source → left_only, sources_absent names the
    authoritative source (PRD-v3 §2 negative-space discovery)."""
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
        identity_domain=DOMAIN,
    )
    (delta,) = result.deltas
    assert delta.bucket == "left_only"
    assert delta.member_key == "ghost@vendor.test"
    assert delta.sources_present == ("contrib",)
    assert delta.sources_absent == ("auth",)
    assert delta.owner is None and delta.disposition is None  # human-filled, never auto
    assert result.left_only == ("ghost@vendor.test",)
    assert result.open_deltas == ("ghost@vendor.test",)


def test_in_domain_active_workforce_is_scope_diagnostic_not_delta() -> None:
    result = reconcile_population(
        population(),
        [
            src("auth"),
            src("contrib", m("contrib", "emp", active=True, email="emp@corp.test")),
        ],
        identity_domain=DOMAIN,
    )
    assert result.deltas == ()
    assert any("outside population scope" in d for d in result.diagnostics)


def test_orphan_termination_signal_is_unresolvable() -> None:
    """A deactivation event for an identity the authoritative source
    does not know: D-7 identity_fuzzy → unresolvable, human queue."""
    result = reconcile_population(
        population(),
        [
            src("auth"),
            src("contrib", m("contrib", "maiden@corp.test", signal=True, email="maiden@corp.test")),
        ],
        identity_domain=DOMAIN,
    )
    (delta,) = result.deltas
    assert delta.bucket == "unresolvable"
    assert result.unresolvable == ("maiden@corp.test",)


def test_terminated_but_active_downstream_is_a_conflict() -> None:
    result = reconcile_population(
        population(),
        [
            src("auth", m("auth", "w1", signal=True, employee_id="E-1", email="w1@corp.test")),
            src("contrib", m("contrib", "w1", active=True, email="w1@corp.test")),
        ],
        identity_domain=DOMAIN,
    )
    (delta,) = result.deltas
    assert delta.bucket == "conflicts"
    assert "E-1" in result.members  # still a member — the conflict is about state


def test_conflicting_global_keys_land_in_conflicts() -> None:
    result = reconcile_population(
        population(),
        [
            src("auth", m("auth", "one", employee_id="E-1", email="one@corp.test")),
            src("contrib", m("contrib", "two", employee_id="E-1", email="two@corp.test")),
        ],
        identity_domain=DOMAIN,
    )
    (delta,) = result.deltas
    assert delta.bucket == "conflicts"


def test_active_auth_only_member_is_right_only() -> None:
    """Active in the authoritative inventory, invisible to the provided
    contributing source (the dormant-local-account shape on an ENTITY
    population)."""
    result = reconcile_population(
        population(type_=PopulationType.ENTITY),
        [
            src("auth", m("auth", "local-bot", active=True, login="local-bot")),
            src("contrib", m("contrib", "emp", active=True, email="emp@corp.test")),
        ],
        identity_domain=DOMAIN,
    )
    by_bucket = {d.bucket: d for d in result.deltas}
    assert by_bucket["right_only"].member_key == "local-bot"
    assert by_bucket["right_only"].sources_absent == ("contrib",)


def test_ratified_disposition_moves_delta_to_excluded_bucket() -> None:
    """A pre-ratified human disposition → excluded, carrying the record.
    The reconciler applies it; it never invents one."""
    result = reconcile_population(
        population(),
        [
            src("auth", m("auth", "w1", signal=True, employee_id="E-1", email="w1@corp.test")),
            src("contrib", m("contrib", "w1", active=True, email="w1@corp.test")),
        ],
        dispositions=(disposition("DISP-1", "E-1"),),
        identity_domain=DOMAIN,
    )
    (delta,) = result.deltas
    assert delta.bucket == "excluded"
    assert delta.disposition_ref == "DISP-1"
    assert delta.disposition is not None and delta.owner == "owner"
    assert result.excluded == ("E-1",)
    assert result.open_deltas == ()


def test_non_human_principals_are_diagnostics_never_buckets() -> None:
    result = reconcile_population(
        population(),
        [
            src("auth"),
            src(
                "contrib",
                m("contrib", "svc-account", active=True, kind=MemberKind.SERVICE_ACCOUNT),
                m("contrib", "deploy-bot", active=True, kind=MemberKind.BOT),
            ),
        ],
        identity_domain=DOMAIN,
    )
    assert result.deltas == ()
    assert any("svc-account" in d and "deploy-bot" in d for d in result.diagnostics)


def test_incomplete_source_never_reconciles() -> None:
    result = reconcile_population(
        population(),
        [
            src("auth", m("auth", "w1", employee_id="E-1")),
            SourceMembers(
                source_id="contrib",
                complete=False,
                notes=("cursor present but next page never retrieved",),
            ),
        ],
        identity_domain=DOMAIN,
    )
    assert not result.basis_complete
    assert result.members == ()
    assert result.population.state is AssuranceState.DEFINED
    assert result.basis_notes == ("contrib: cursor present but next page never retrieved",)


def test_excluded_delta_requires_its_disposition() -> None:
    with pytest.raises(ValueError, match="excluded delta requires"):
        DeltaObject(
            delta_id="p#excluded#x",
            bucket="excluded",
            member_key="x",
        )


def test_source_counts_are_present_and_diagnostic() -> None:
    result = reconcile_population(
        population(),
        [
            src("auth", m("auth", "w1", employee_id="E-1", email="w1@corp.test")),
            src("contrib", m("contrib", "w1", email="w1@corp.test")),
        ],
        identity_domain=DOMAIN,
    )
    assert result.source_counts == {"auth": 1, "contrib": 1}


def test_reperformance_is_byte_identical() -> None:
    sources = [
        src("auth", m("auth", "w1", signal=True, employee_id="E-1", email="w1@corp.test")),
        src(
            "contrib",
            m("contrib", "w1", email="w1@corp.test"),
            m("contrib", "ghost", active=True, email="ghost@vendor.test"),
        ),
    ]
    one = reconcile_population(population(), sources, identity_domain=DOMAIN)
    two = reconcile_population(population(), sources, identity_domain=DOMAIN)
    assert one.model_dump_json() == two.model_dump_json()
