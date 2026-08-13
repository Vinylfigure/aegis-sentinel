"""REC01 — N-source set reconciliation into the six delta buckets.

Reconciliation is set-based (docs/HANDOFF.md §2; PRD-v3 §2): canonical
identity (identity.py), then membership, intersection, left-only,
right-only, conflicts, unresolvable, excluded — every bucket a
first-class :class:`DeltaObject` with owner and disposition fields for
the human workflow. Counts are a smell test, never evidence: the
``source_counts`` diagnostic exists to raise eyebrows, not to prove
anything.

Bucket semantics, relative to the population's AUTHORITATIVE source(s):

- ``intersection`` — canonical identities anchored in the authoritative
  source (and, for ENTITY populations, identities the derivation rule's
  union membership admits) with no contradiction.
- ``left_only`` — **negative space** (PRD-v3 §2: the signature
  capability): an identity present in contributing/corroborating
  sources but absent from the authoritative source. ``sources_absent``
  names the authoritative source(s) the identity failed to reconcile
  against. This is what catches the contractor poison — an active
  identity the authoritative employment record cannot account for.
- ``right_only`` — an *active* identity present only in the
  authoritative source, absent from every provided contributing source
  that should corroborate it (an inactive authoritative-only member is
  expected attrition, not a delta).
- ``conflicts`` — contradictory evidence for one identity: conflicting
  values for a global join key (D-8 — routed to a human, never
  guessed), or a termination-signaled member still active in a
  contributing source.
- ``unresolvable`` — a termination-shaped signal (feed row /
  deactivation event) for an identity that joins to no authoritative
  member: the D-7 ``identity_fuzzy`` branch
  (knowledge/01_corpus/02_design_decisions/Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md)
  — it routes to a human resolution queue and never maps to satisfied.
- ``excluded`` — a delta covered by a **pre-ratified, human-made**
  disposition (F-4 discipline). The reconciler applies ratified
  disposition records; it NEVER manufactures one (PRD-v3 §4: the
  Reconciler may never disposition deltas — that is the human's act).

Workforce scope rule (PRD-v3 §2 — "process assigns scope-relevance"):
for termination-lane populations, an identity whose email domain is the
engagement's declared ``identity_domain``, with no termination signal
and no authoritative anchor, is the *active workforce* — inside the
identity fabric, outside this population's scope — and is not a delta.
An identity outside that domain (or with no identity keys at all) that
holds access the authoritative source cannot account for IS the
negative space this reconciler exists to surface.

Non-human principals (bots, service accounts, groups) are outside the
workforce identity universe and are reported as diagnostics, never
silently dropped into a bucket; their governance is a different lane,
and the break-glass surface specifically is caught at compile time as
E117 (docs/PRD-v3.md §6).

STRICT-adjacent purity: pure functions of their inputs.
"""

from __future__ import annotations

from datetime import date
from typing import Mapping, Sequence

from pydantic import Field, model_validator

from aegis_sentinel.reconcile.identity import (
    WORKFORCE_KINDS,
    IdentityCluster,
    SourceMember,
    build_clusters,
    email_domain,
)
from aegis_sentinel.schema import (
    AegisModel,
    DispositionValue,
    Population,
    PopulationType,
    SourceRole,
)

MODULE_VERSION = "reconcile.setops@0.1.0"

#: The six bucket names, exactly as the frontend contract spells them
#: (web/src/lib/types/artifacts.ts DELTA_BUCKETS).
BUCKETS: tuple[str, ...] = (
    "intersection",
    "left_only",
    "right_only",
    "conflicts",
    "unresolvable",
    "excluded",
)

#: Buckets whose undispositioned members block DISCOVERED→RECONCILED.
DELTA_BUCKETS: tuple[str, ...] = ("left_only", "right_only", "conflicts", "unresolvable")

_ROLE_RANK: dict[SourceRole, int] = {
    SourceRole.AUTHORITATIVE: 0,
    SourceRole.CONTRIBUTING: 1,
    SourceRole.CORROBORATING: 2,
    SourceRole.DISCOVERY: 3,
    SourceRole.EXCLUSION: 4,
}


class DeltaDisposition(AegisModel):
    """REI mechanized (PRD-v3 §2): justification + owner + review date.

    Field names match the frontend contract's ``DeltaDisposition``.
    """

    value: DispositionValue
    justification: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    review_date: date


class DeltaObject(AegisModel):
    """One reconciliation delta — frontend-aligned field names.

    ``owner`` and ``disposition`` are human-filled: the reconciler
    populates them only from pre-ratified disposition records passed in
    by the caller; it never auto-dispositions (PRD-v3 §4).
    """

    delta_id: str = Field(min_length=1)
    bucket: str = Field(min_length=1)
    member_key: str = Field(min_length=1)
    display_name: str | None = None
    sources_present: tuple[str, ...] = ()
    sources_absent: tuple[str, ...] = ()
    owner: str | None = None
    disposition: DeltaDisposition | None = None
    #: The disposition record's ratified reference (e.g. DISP-2026-114).
    disposition_ref: str | None = None

    @model_validator(mode="after")
    def _bucket_rules(self) -> "DeltaObject":
        if self.bucket not in BUCKETS:
            raise ValueError(f"bucket must be one of {BUCKETS}, got {self.bucket!r}")
        if self.bucket == "excluded" and self.disposition is None:
            raise ValueError("an excluded delta requires the ratified disposition that excluded it")
        if (self.disposition is None) != (self.disposition_ref is None):
            raise ValueError("disposition and disposition_ref travel together")
        return self

    @property
    def open(self) -> bool:
        """Undispositioned and in a delta bucket — blocks RECONCILED."""
        return self.bucket in DELTA_BUCKETS and self.disposition is None


class RatifiedDeltaDisposition(AegisModel):
    """A human-ratified disposition record the reconciler may apply.

    These come from the engagement fixture (F-4: the agent drafts, a
    human ratifies); ``member_keys`` lists the identity key values the
    disposition covers.
    """

    disposition_ref: str = Field(min_length=1)
    member_keys: tuple[str, ...] = Field(min_length=1)
    value: DispositionValue
    justification: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    review_date: date
    ratified_by: str = Field(min_length=1)

    def covers(self, cluster: IdentityCluster) -> bool:
        return any(cluster.any_key_value(key) for key in self.member_keys)

    def as_disposition(self) -> DeltaDisposition:
        return DeltaDisposition(
            value=self.value,
            justification=self.justification,
            owner=self.owner,
            review_date=self.review_date,
        )


def _delta(
    population: Population,
    bucket: str,
    cluster: IdentityCluster,
    sources_absent: tuple[str, ...],
    dispositions: Sequence[RatifiedDeltaDisposition],
) -> DeltaObject:
    """Build one delta; a covering ratified disposition moves it to excluded."""
    ratified = next((d for d in dispositions if d.covers(cluster)), None)
    final_bucket = "excluded" if ratified is not None else bucket
    return DeltaObject(
        delta_id=f"{population.population_id}#{final_bucket}#{cluster.canonical_key}",
        bucket=final_bucket,
        member_key=cluster.canonical_key,
        display_name=cluster.display_name,
        sources_present=cluster.sources_present,
        sources_absent=sources_absent,
        owner=ratified.owner if ratified is not None else None,
        disposition=ratified.as_disposition() if ratified is not None else None,
        disposition_ref=ratified.disposition_ref if ratified is not None else None,
    )


class ClassifiedSets(AegisModel):
    """The classifier's output: members, per-bucket deltas, diagnostics."""

    members: tuple[str, ...] = ()
    deltas: tuple[DeltaObject, ...] = ()
    diagnostics: tuple[str, ...] = ()
    clusters: tuple[IdentityCluster, ...] = ()

    def bucket_keys(self, bucket: str) -> tuple[str, ...]:
        return tuple(d.member_key for d in self.deltas if d.bucket == bucket)


def classify(
    population: Population,
    members_by_source: Mapping[str, tuple[SourceMember, ...]],
    dispositions: Sequence[RatifiedDeltaDisposition] = (),
    identity_domain: str | None = None,
) -> ClassifiedSets:
    """Cluster all provided sources' members and classify every cluster.

    Membership: clusters anchored in an AUTHORITATIVE source are always
    members; for ENTITY populations, clusters admitted through any
    derivation-rule (membership) source are members too — the accounts
    populations' definitions union SSO-, local-, and group-derived
    access (templates/lanes/termination.json).
    """
    role_by_source = {s.source_id: s.role for s in population.sources}
    rank_by_source = {sid: _ROLE_RANK[role] for sid, role in role_by_source.items()}
    auth_sources = tuple(
        sorted(s for s, role in role_by_source.items() if role is SourceRole.AUTHORITATIVE)
    )
    provided = set(members_by_source)
    provided_non_auth = tuple(sorted(provided - set(auth_sources)))
    membership_sources = set(population.derivation_rule.source_refs) & provided

    all_members = [m for source in sorted(provided) for m in members_by_source[source]]
    workforce = [m for m in all_members if m.kind in WORKFORCE_KINDS]
    non_human = [m for m in all_members if m.kind not in WORKFORCE_KINDS]

    clusters = build_clusters(workforce, rank_by_source)

    member_keys: list[str] = []
    deltas: list[DeltaObject] = []
    diagnostics: list[str] = []

    for cluster in clusters:
        present = set(cluster.sources_present)
        auth_present = bool(present & set(auth_sources))
        auth_absent = tuple(s for s in auth_sources if s not in present)
        any_active = any(m.active for m in cluster.members)
        active_non_auth = any(m.active for m in cluster.members if m.source_id not in auth_sources)
        signaled = any(m.termination_signal for m in cluster.members)
        auth_signaled = any(
            m.termination_signal for m in cluster.members if m.source_id in auth_sources
        )

        if cluster.has_conflict:
            # D-8: contradictory global-key values → a human resolves.
            deltas.append(_delta(population, "conflicts", cluster, (), dispositions))
            if auth_present:
                member_keys.append(cluster.canonical_key)
            continue

        if auth_present:
            member_keys.append(cluster.canonical_key)
            if auth_signaled and active_non_auth:
                # Terminated per the authoritative source, still active in
                # a contributing source: contradictory state — a human
                # dispositions it (the legitimate-exception shape).
                deltas.append(_delta(population, "conflicts", cluster, (), dispositions))
            elif (
                provided_non_auth
                and any_active
                and not (present - set(auth_sources))
                and population.type is not PopulationType.EVENT
            ):
                # Active in the authoritative inventory, invisible to every
                # provided contributing source (e.g. a local account the
                # IdP cannot corroborate).
                deltas.append(
                    _delta(population, "right_only", cluster, provided_non_auth, dispositions)
                )
            continue

        # --- no authoritative anchor ---------------------------------
        if signaled:
            # A termination-shaped signal for an identity the
            # authoritative source does not know: D-7 identity_fuzzy —
            # clerical review, never a guess.
            deltas.append(_delta(population, "unresolvable", cluster, auth_absent, dispositions))
            continue
        if (
            identity_domain is not None
            and email_domain(cluster) == identity_domain
            and not auth_signaled
        ):
            # Active workforce inside the engagement's identity domain:
            # in scope for the lane, out of scope for this population.
            diagnostics.append(
                f"in-domain active workforce identity outside population scope: "
                f"{cluster.canonical_key}"
            )
            if population.type is PopulationType.ENTITY and (present & membership_sources):
                member_keys.append(cluster.canonical_key)
            continue
        if any_active:
            # NEGATIVE SPACE: an active identity present downstream that
            # the authoritative source cannot account for — the
            # contractor poison's detection surface (PRD-v3 §2/§6).
            deltas.append(_delta(population, "left_only", cluster, auth_absent, dispositions))
            if population.type is PopulationType.ENTITY and (present & membership_sources):
                member_keys.append(cluster.canonical_key)
            continue
        diagnostics.append(
            f"inactive unanchored identity (no termination signal): {cluster.canonical_key}"
        )

    if non_human:
        diagnostics.append(
            "non-workforce principals outside the identity universe "
            "(bot/service-account/group; governance is a separate lane): "
            + ", ".join(sorted(m.display_name for m in non_human))
        )

    return ClassifiedSets(
        members=tuple(sorted(set(member_keys), key=str.casefold)),
        deltas=tuple(sorted(deltas, key=lambda d: d.delta_id.casefold())),
        diagnostics=tuple(diagnostics),
        clusters=clusters,
    )
