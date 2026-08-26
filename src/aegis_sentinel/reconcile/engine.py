"""REC01 — N-source set reconciler with canonical identity.

Set-based reconciliation per the locked ruling (HANDOFF §2) and D-8
model reconciliation (knowledge/01_corpus/02_design_decisions/
Aegis_Design_Fix_D8_Model_Reconciliation.md): named member-sets carry
source roles, members join on canonical identity (the normalized email
from reconcile.minimal — reused, never copied), and every difference is
a first-class schema.Delta object. Counts are diagnostics, never
evidence.

The six buckets partition every canonical identity exactly once, in
this precedence order (each rule fires only when no earlier rule did):

1. EXCLUDED — the identity matches a ratified boundary exclusion; the
   exclusion ref and ratifier are recorded on the delta. Per D-9
   decentralization discipline (knowledge/01_corpus/02_design_decisions/
   Aegis_Design_Fix_D9_Decentralization_Discipline.md) no agent may
   expand — or shrink — its own boundary: exclusions enter this engine
   only as already-ratified refs; the engine never invents one.
2. UNRESOLVABLE — no canonical key is derivable for a member (null or
   garbled email); the source-side member ref is preserved.
3. RIGHT_ONLY — present in some source but absent from the
   authoritative source.
4. LEFT_ONLY — present in the authoritative source but absent from at
   least one other source. Absence dominates attribute comparison: a
   member cannot be adjudicated as agreeing or conflicting with a
   source it is missing from.
5. CONFLICT — present in every source but with mismatched attributes
   (e.g. active in one source, deactivated in another).
6. INTERSECTION — present in every source with no attribute mismatch.

Ladder discipline: LEFT_ONLY / RIGHT_ONLY / CONFLICT / UNRESOLVABLE are
open questions — they attach to the population undispositioned, so
schema.models.advance keeps blocking DISCOVERED→RECONCILED until a
human dispositions each one. INTERSECTION and EXCLUDED are resolved
states, not open questions: presence everywhere needs no sign-off, and
an EXCLUDED delta is born dispositioned because the ratified boundary
exclusion (D-9) *is* its human resolution — it attaches to the
population without blocking the ladder, keeping the exclusion visible
in lineage. Intersection deltas live only in the result buckets: they
are the canonical membership itself, and attaching agreement to the
population as if it were a question would block the ladder on nothing.
"""

from collections.abc import Callable, Mapping, Sequence

from pydantic import Field, model_validator

from aegis_sentinel.reconcile.minimal import Member, canonical_email
from aegis_sentinel.schema.enums import DeltaBucket, DispositionValue, SourceRole
from aegis_sentinel.schema.models import Base, Delta, DispositionRecord, Population

OPEN_BUCKETS = (
    DeltaBucket.LEFT_ONLY,
    DeltaBucket.RIGHT_ONLY,
    DeltaBucket.CONFLICT,
    DeltaBucket.UNRESOLVABLE,
)


class SourceMember(Member):
    """A member as one source sees it: ref + join email (from
    reconcile.minimal.Member) plus the attributes that source asserts
    (e.g. status), compared across sources for CONFLICT detection."""

    attributes: dict[str, str] = Field(default_factory=dict)


class SourceSet(Base):
    """One named member-set with its source role (HANDOFF §2: sources
    carry roles; exactly one per reconciliation is authoritative)."""

    name: str = Field(min_length=1)
    role: SourceRole
    members: tuple[SourceMember, ...] = ()


class BoundaryExclusion(Base):
    """A ratified boundary exclusion: the human act happened upstream
    (D-9 — ratification is never this engine's to perform); the engine
    only matches and records the ref."""

    member: str = Field(min_length=1)
    ref: str = Field(min_length=1)
    ratified_by: str = Field(min_length=1)

    @property
    def member_ref(self) -> str:
        """The same prefixed identity scheme bucket entries carry on the
        wire (Q6/#78) — derived from `member` via the same
        `canonical_email` normalization the engine already joins on, not
        a new identity model."""
        key = canonical_email(self.member)
        if key is None:
            raise ValueError(f"boundary exclusion {self.ref} names no canonical member")
        return f"email:{key}"


class DeltaBuckets(Base):
    """All six buckets as first-class Delta objects. Member refs are
    the payload; the counts property is a diagnostic, never evidence."""

    intersection: tuple[Delta, ...] = ()
    left_only: tuple[Delta, ...] = ()
    right_only: tuple[Delta, ...] = ()
    conflict: tuple[Delta, ...] = ()
    unresolvable: tuple[Delta, ...] = ()
    excluded: tuple[Delta, ...] = ()

    @property
    def counts(self) -> dict[str, int]:
        """Diagnostics only — never evidence (HANDOFF §2)."""
        return {bucket.value: len(getattr(self, bucket.value)) for bucket in DeltaBucket}


class SetReconcileResult(Base):
    population: Population
    buckets: DeltaBuckets
    canonical_members: tuple[str, ...]

    @model_validator(mode="after")
    def _open_deltas_attached(self):
        attached = {(d.bucket, d.member_ref) for d in self.population.deltas}
        for bucket in (*OPEN_BUCKETS, DeltaBucket.EXCLUDED):
            for delta in getattr(self.buckets, bucket.value):
                if (delta.bucket, delta.member_ref) not in attached:
                    raise ValueError(f"{bucket.value} delta {delta.member_ref} not attached")
        return self


def default_canonicalizer(member: Member) -> str | None:
    """Canonical identity via reconcile.minimal.canonical_email, plus a
    plausibility floor: a 'garbled' email (no @) derives no key, so the
    member lands in UNRESOLVABLE rather than joining on junk."""
    key = canonical_email(member.email)
    if key is None or "@" not in key:
        return None
    return key


def _conflicting_attributes(views: Sequence[SourceMember]) -> dict[str, tuple[str, ...]]:
    """Attribute names asserted with more than one distinct value across
    the sources' views of one canonical identity."""
    seen: dict[str, set[str]] = {}
    for view in views:
        for name, value in view.attributes.items():
            seen.setdefault(name, set()).add(value)
    return {name: tuple(sorted(values)) for name, values in seen.items() if len(values) > 1}


def reconcile_sets(
    population: Population,
    sources: Sequence[SourceSet],
    *,
    boundary_exclusions: Sequence[BoundaryExclusion] = (),
    canonicalizer: Callable[[Member], str | None] = default_canonicalizer,
) -> SetReconcileResult:
    """Join N named member-sets by canonical identity for one population.

    Requires exactly one AUTHORITATIVE source (HANDOFF §2 source roles);
    LEFT_ONLY / RIGHT_ONLY are relative to it. Returns all six buckets
    (D-8 set reconciliation) plus the population with its open-question
    deltas — and its born-dispositioned EXCLUDED deltas (D-9) —
    attached, and size set to the canonical intersection count (a
    diagnostic, not evidence). Ladder state is untouched: advancing is
    the caller's explicit act via schema.models.advance, which blocks
    DISCOVERED→RECONCILED while any attached delta is undispositioned.
    """
    if len(sources) < 2:
        raise ValueError("set reconciliation needs at least two sources")
    names = [s.name for s in sources]
    if len(set(names)) != len(names):
        raise ValueError(f"source names must be unique, got {sorted(names)}")
    authoritative = [s for s in sources if s.role is SourceRole.AUTHORITATIVE]
    if len(authoritative) != 1:
        raise ValueError(
            f"exactly one authoritative source required, got {len(authoritative)} "
            f"({sorted(s.name for s in authoritative)})"
        )
    authoritative_name = authoritative[0].name

    excluded_by_key: dict[str, BoundaryExclusion] = {}
    for exclusion in boundary_exclusions:
        key = canonical_email(exclusion.member)
        if key is None:
            raise ValueError(f"boundary exclusion {exclusion.ref} names no canonical member")
        excluded_by_key[key] = exclusion

    # canonical key -> source name -> that source's view of the member
    views: dict[str, dict[str, SourceMember]] = {}
    unresolvable_members: list[SourceMember] = []
    for source in sources:
        for member in source.members:
            key = canonicalizer(member)
            if key is None:
                unresolvable_members.append(member)
            else:
                # last view per source wins; duplicates within a source
                # (e.g. rehire rows) dedupe on canonical identity
                views.setdefault(key, {})[source.name] = member

    buckets: dict[DeltaBucket, list[Delta]] = {bucket: [] for bucket in DeltaBucket}
    for member in sorted(unresolvable_members, key=lambda m: m.ref):
        buckets[DeltaBucket.UNRESOLVABLE].append(
            Delta(bucket=DeltaBucket.UNRESOLVABLE, member_ref=member.ref, owner=None)
        )
    for key in sorted(views):
        present = views[key]
        member_ref = f"email:{key}"
        if key in excluded_by_key:
            exclusion = excluded_by_key[key]
            buckets[DeltaBucket.EXCLUDED].append(
                Delta(
                    bucket=DeltaBucket.EXCLUDED,
                    member_ref=member_ref,
                    owner=exclusion.ratified_by,
                    disposition=DispositionRecord(
                        value=DispositionValue.NOT_APPLICABLE,
                        owner=exclusion.ratified_by,
                        rationale=f"ratified boundary exclusion {exclusion.ref} (D-9)",
                    ),
                )
            )
        elif authoritative_name not in present:
            buckets[DeltaBucket.RIGHT_ONLY].append(
                Delta(bucket=DeltaBucket.RIGHT_ONLY, member_ref=member_ref)
            )
        elif len(present) < len(sources):
            buckets[DeltaBucket.LEFT_ONLY].append(
                Delta(bucket=DeltaBucket.LEFT_ONLY, member_ref=member_ref)
            )
        elif _conflicting_attributes(tuple(present.values())):
            buckets[DeltaBucket.CONFLICT].append(
                Delta(bucket=DeltaBucket.CONFLICT, member_ref=member_ref)
            )
        else:
            buckets[DeltaBucket.INTERSECTION].append(
                Delta(bucket=DeltaBucket.INTERSECTION, member_ref=member_ref)
            )

    canonical_members = tuple(
        d.member_ref.removeprefix("email:") for d in buckets[DeltaBucket.INTERSECTION]
    )
    attached = tuple(
        delta for bucket in (*OPEN_BUCKETS, DeltaBucket.EXCLUDED) for delta in buckets[bucket]
    )
    reconciled = population.model_copy(update={"deltas": attached, "size": len(canonical_members)})
    return SetReconcileResult(
        population=reconciled,
        buckets=DeltaBuckets(
            intersection=tuple(buckets[DeltaBucket.INTERSECTION]),
            left_only=tuple(buckets[DeltaBucket.LEFT_ONLY]),
            right_only=tuple(buckets[DeltaBucket.RIGHT_ONLY]),
            conflict=tuple(buckets[DeltaBucket.CONFLICT]),
            unresolvable=tuple(buckets[DeltaBucket.UNRESOLVABLE]),
            excluded=tuple(buckets[DeltaBucket.EXCLUDED]),
        ),
        canonical_members=canonical_members,
    )


def load_source_sets(raw: Sequence[Mapping]) -> tuple[SourceSet, ...]:
    """Parse fixture/manifest JSON into SourceSet objects (closed
    schema — unknown fields are rejected, D-P1)."""
    return tuple(SourceSet.model_validate(item) for item in raw)


def load_boundary_exclusions(raw: Sequence[Mapping]) -> tuple[BoundaryExclusion, ...]:
    return tuple(BoundaryExclusion.model_validate(item) for item in raw)
