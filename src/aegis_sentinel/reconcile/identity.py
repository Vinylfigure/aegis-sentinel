"""REC01 — canonical-identity join across N evidence sources.

Deterministic exact-key clustering: members from different sources merge
into one canonical identity iff they share an equal (case-normalized)
value for the same join key. Key precedence for choosing the canonical
member key is ``employee_id > email > login`` (the join keys the
capability entries declare; registry/capabilities/*.json).

D-8 discipline (knowledge/01_corpus/02_design_decisions/
Aegis_Design_Fix_D8_Model_Reconciliation.md): reconcile toward the
human, never toward the match. There is no fuzzy matching here — no
similarity scores, no token overlap, no "probably the same person". A
member matched by different keys in different sources with conflicting
values for the same global key is a CONFLICT for a human to resolve,
never a guess; identities that share no exact key never merge, and the
set reconciler (setops.py) routes the resulting gaps to delta buckets
instead of papering over them.

``login`` is deliberately excluded from conflict detection: logins are
system-local handles (a GitHub login and a Slack handle legitimately
differ for one person), while ``employee_id`` and ``email`` are global
identity claims — two different values for a global key inside one
cluster is contradictory evidence, the D-8 "sharp corner".

STRICT-adjacent purity: pure functions of their inputs — no I/O, no
clock, no randomness (docs/HANDOFF.md §3).
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable, Mapping, Sequence

from pydantic import Field

from aegis_sentinel.schema import AegisModel

MODULE_VERSION = "reconcile.identity@0.1.0"

#: Canonical join-key precedence (highest first) for picking a cluster's
#: canonical member key. Matches the keys declared across the ratified
#: capability entries (employee_id/email from HRIS; email/login from the
#: IdP and the downstream inventories).
KEY_PRECEDENCE: tuple[str, ...] = ("employee_id", "email", "login")

#: Keys that assert a *global* identity: conflicting values inside one
#: cluster are a CONFLICT (D-8), never averaged away. ``login`` is
#: system-local and exempt.
GLOBAL_KEYS: frozenset[str] = frozenset({"employee_id", "email"})


class MemberKind(str, Enum):
    """What kind of principal a source member is.

    Non-human kinds (BOT / SERVICE_ACCOUNT / GROUP) are outside the
    termination lane's workforce-identity universe — service-account
    governance is its own lane, and the break-glass poison is caught at
    compile time (E117) precisely because its surface has no ratified
    capability entry (docs/PRD-v3.md §6).
    """

    HUMAN = "HUMAN"
    OUTSIDE_COLLABORATOR = "OUTSIDE_COLLABORATOR"
    BOT = "BOT"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"
    GROUP = "GROUP"


#: Kinds that participate in the workforce identity join.
WORKFORCE_KINDS: frozenset[MemberKind] = frozenset(
    {MemberKind.HUMAN, MemberKind.OUTSIDE_COLLABORATOR}
)


class KeyValue(AegisModel):
    """One join-key value a source exposes for a member."""

    key: str = Field(min_length=1)
    value: str = Field(min_length=1)


class SourceMember(AegisModel):
    """One member as one source enumerated it.

    ``active`` is the source's own notion of a live principal (Okta
    ACTIVE, Slack ``deleted: false``, GitHub current-roster membership).
    ``termination_signal`` marks termination-shaped records: an HRIS
    feed row or an IdP deactivation event.
    """

    source_id: str = Field(min_length=1)
    keys: tuple[KeyValue, ...] = ()
    display_name: str = Field(min_length=1)
    kind: MemberKind = MemberKind.HUMAN
    active: bool = False
    termination_signal: bool = False

    def normalized_keys(self) -> tuple[tuple[str, str], ...]:
        """(key, casefolded value) pairs — the exact-match join basis."""
        return tuple((kv.key, kv.value.casefold()) for kv in self.keys)


class IdentityCluster(AegisModel):
    """One canonical identity: every source member that shares a key."""

    canonical_key: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    members: tuple[SourceMember, ...] = Field(min_length=1)
    #: Global keys carrying >1 distinct value inside this cluster (D-8
    #: conflict — a human resolves it; the reconciler never guesses).
    conflicting_keys: tuple[str, ...] = ()

    @property
    def sources_present(self) -> tuple[str, ...]:
        return tuple(sorted({m.source_id for m in self.members}))

    @property
    def has_conflict(self) -> bool:
        return bool(self.conflicting_keys)

    def key_values(self, key: str) -> tuple[str, ...]:
        """Distinct casefolded values for one key, sorted."""
        return tuple(
            sorted({kv.value.casefold() for m in self.members for kv in m.keys if kv.key == key})
        )

    def any_key_value(self, value: str) -> bool:
        """True if any key value (or the canonical key) matches, casefolded."""
        needle = value.casefold()
        if self.canonical_key.casefold() == needle:
            return True
        return any(kv.value.casefold() == needle for m in self.members for kv in m.keys)


def _canonical_key(members: Sequence[SourceMember], roles_rank: Mapping[str, int]) -> str:
    """Deterministic canonical key: best (precedence, source rank, value).

    Members from better-ranked sources (authoritative first) win ties;
    the original (non-casefolded) value is preserved for display.
    """
    best: tuple[int, int, str] | None = None
    best_value = ""
    for member in members:
        rank = roles_rank.get(member.source_id, len(roles_rank) + 1)
        for kv in member.keys:
            try:
                precedence = KEY_PRECEDENCE.index(kv.key)
            except ValueError:
                precedence = len(KEY_PRECEDENCE)
            candidate = (precedence, rank, kv.value.casefold())
            if best is None or candidate < best:
                best = candidate
                best_value = kv.value
    if not best_value:
        # No join key at all: the display name is the only handle. Such a
        # cluster can never merge with anything — exactly the dormant
        # local-account shape (tests/fixtures/tenants/README.md).
        best_value = members[0].display_name
    return best_value


def _display_name(members: Sequence[SourceMember], roles_rank: Mapping[str, int]) -> str:
    ranked = sorted(
        members,
        key=lambda m: (roles_rank.get(m.source_id, len(roles_rank) + 1), m.source_id),
    )
    return ranked[0].display_name


def build_clusters(
    members: Iterable[SourceMember],
    source_role_rank: Mapping[str, int] | None = None,
) -> tuple[IdentityCluster, ...]:
    """Union-find over exact (key, casefolded value) matches.

    Returns clusters sorted by canonical key (casefolded) for
    determinism. ``source_role_rank`` (lower = more authoritative)
    breaks display/canonical ties; omitted means all sources rank
    equally and ties fall to source_id order.
    """
    roles_rank = dict(source_role_rank or {})
    member_list = list(members)
    parent = list(range(len(member_list)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)

    seen: dict[tuple[str, str], int] = {}
    for index, member in enumerate(member_list):
        for pair in member.normalized_keys():
            if pair in seen:
                union(seen[pair], index)
            else:
                seen[pair] = index

    grouped: dict[int, list[SourceMember]] = {}
    for index, member in enumerate(member_list):
        grouped.setdefault(find(index), []).append(member)

    clusters: list[IdentityCluster] = []
    for group in grouped.values():
        conflicting = tuple(
            sorted(
                key
                for key in GLOBAL_KEYS
                if len({kv.value.casefold() for m in group for kv in m.keys if kv.key == key}) > 1
            )
        )
        clusters.append(
            IdentityCluster(
                canonical_key=_canonical_key(group, roles_rank),
                display_name=_display_name(group, roles_rank),
                members=tuple(
                    sorted(group, key=lambda m: (m.source_id, m.display_name.casefold()))
                ),
                conflicting_keys=conflicting,
            )
        )
    return tuple(sorted(clusters, key=lambda c: (c.canonical_key.casefold(), c.canonical_key)))


def email_domain(cluster: IdentityCluster) -> str | None:
    """The cluster's email domain, iff every email agrees on one.

    Multiple distinct domains → ``None`` (ambiguous — never guessed).
    """
    domains = {value.rsplit("@", 1)[-1] for value in cluster.key_values("email") if "@" in value}
    if len(domains) == 1:
        return next(iter(domains))
    return None
