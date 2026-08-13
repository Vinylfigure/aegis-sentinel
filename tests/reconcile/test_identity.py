"""REC01 identity join: exact-key clustering, precedence, D-8 conflicts.

No fuzzy matching anywhere: members merge only on equal (case-normalized)
values of the same join key, and contradictory global-key values inside
one cluster surface as conflicts for a human — never a guess
(knowledge/01_corpus/02_design_decisions/Aegis_Design_Fix_D8_Model_Reconciliation.md).
"""

from __future__ import annotations

from aegis_sentinel.reconcile import (
    KeyValue,
    MemberKind,
    SourceMember,
    build_clusters,
    email_domain,
)


def member(source: str, display: str, **keys: str) -> SourceMember:
    return SourceMember(
        source_id=source,
        keys=tuple(KeyValue(key=k, value=v) for k, v in keys.items()),
        display_name=display,
        kind=MemberKind.HUMAN,
    )


def test_members_sharing_a_key_merge_into_one_cluster() -> None:
    clusters = build_clusters(
        [
            member("hris", "a@x.test", employee_id="E-1", email="a@x.test"),
            member("okta", "a@x.test", email="a@x.test", login="a-x"),
            member("github", "a-x", login="a-x"),
        ]
    )
    assert len(clusters) == 1
    cluster = clusters[0]
    assert cluster.sources_present == ("github", "hris", "okta")
    # Canonical key precedence: employee_id beats email beats login.
    assert cluster.canonical_key == "E-1"


def test_case_normalized_join_never_fuzzy() -> None:
    clusters = build_clusters(
        [
            member("hris", "a", email="Amara.Diallo@X.test"),
            member("slack", "b", email="amara.diallo@x.test"),
            # Similar-but-different value: NEVER merged (no similarity).
            member("okta", "c", email="amara.dialo@x.test"),
        ]
    )
    assert len(clusters) == 2


def test_conflicting_global_key_is_a_conflict_never_a_guess() -> None:
    """One employee_id, two different emails: D-8 sharp corner → human."""
    clusters = build_clusters(
        [
            member("hris", "one", employee_id="E-9", email="one@x.test"),
            member("payroll", "two", employee_id="E-9", email="two@x.test"),
        ]
    )
    (cluster,) = clusters
    assert cluster.has_conflict
    assert cluster.conflicting_keys == ("email",)


def test_system_local_login_values_never_conflict() -> None:
    """Logins are per-system handles; different logins are not evidence
    of contradiction (identity.py GLOBAL_KEYS)."""
    clusters = build_clusters(
        [
            member("okta", "a", email="a@x.test", login="a@x.test"),
            member("github", "a-gh", email="a@x.test", login="a-gh"),
        ]
    )
    (cluster,) = clusters
    assert not cluster.has_conflict


def test_keyless_member_clusters_alone_under_its_display_name() -> None:
    clusters = build_clusters(
        [
            SourceMember(source_id="github", display_name="bm-legacy-bot"),
            member("okta", "a", email="a@x.test"),
        ]
    )
    assert len(clusters) == 2
    lone = next(c for c in clusters if c.canonical_key == "bm-legacy-bot")
    assert lone.sources_present == ("github",)


def test_authoritative_rank_breaks_canonical_ties() -> None:
    clusters = build_clusters(
        [
            member("okta", "b", email="a@x.test"),
            member("hris", "a", email="a@x.test"),
        ],
        source_role_rank={"hris": 0, "okta": 1},
    )
    (cluster,) = clusters
    assert cluster.display_name == "a"  # the authoritative source's display


def test_email_domain_unanimous_or_none() -> None:
    clusters = build_clusters(
        [
            member("okta", "a", email="a@x.test"),
            member("slack", "a", email="a@x.test"),
        ]
    )
    assert email_domain(clusters[0]) == "x.test"
    mixed = build_clusters(
        [
            member("okta", "a", employee_id="E-1", email="a@x.test"),
            member("slack", "a", employee_id="E-1", email="a@y.test"),
        ]
    )
    assert email_domain(mixed[0]) is None  # ambiguous — never guessed


def test_clustering_is_deterministic() -> None:
    members = [
        member("okta", "b", email="b@x.test"),
        member("hris", "a", employee_id="E-1", email="a@x.test"),
        member("slack", "a", email="a@x.test"),
    ]
    one = build_clusters(members)
    two = build_clusters(list(reversed(members)))
    assert [c.canonical_key for c in one] == [c.canonical_key for c in two]
