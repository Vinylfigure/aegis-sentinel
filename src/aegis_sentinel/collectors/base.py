"""Collector base — deterministic evidence retrieval (COL01+; PRD-v3 §4).

A collector executes a :class:`~aegis_sentinel.compile.CompiledCollectorPlan`
(TYP01) against an injected :class:`Transport`, exhausts pagination per the
matched capability entry's declared method, hashes every raw page and the
assembled collection via ``schema/canonical.py``, and emits an
:class:`~aegis_sentinel.schema.EvidenceQualityContract` with all five
quality-property methods named from plan/capability fields. Collectors
retrieve, hash, and record — they never interpret, summarize, or decide
(PRD-v3 §4).

Completeness semantics are salvaged from the prior scaffold's completeness
module (``aegis-sentinel/src/completeness.py``:
``assert_exhaustive_pagination`` / ``assert_independent_count``): partial
collection — exhaustion unproven, or the collected count differing from an
independently declared total — is never a partial pass. The snapshot is
flagged incomplete with named reasons, and the downstream evaluator turns
the whole population UNKNOWN at population level (D-U1;
``evaluate/minimal.py``).

``retrieved_at`` is an EXPLICIT input everywhere: collectors never read a
clock (D-P3 discipline, applied beyond the strict lanes by choice).
No live-tenant calls in tests — transports are injected, and
:class:`FixtureTransport` reads fixture-tenant page files
(docs/HANDOFF.md §4 COL01–05).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Protocol

from pydantic import Field, model_validator

from aegis_sentinel.capability.entry import TemporalShape, TemporalShapeKind
from aegis_sentinel.compile import CompiledCollectorPlan
from aegis_sentinel.compile.typecheck import EVENT_FAMILY, STATE_FAMILY, STATE_SHAPES
from aegis_sentinel.schema import (
    AegisModel,
    AssertionType,
    EvidenceQualityContract,
    Parameter,
    QualityProperty,
    sha256_canonical,
)

MODULE_VERSION = "collectors.base@0.1.0"

SHA256_PATTERN = r"^[a-f0-9]{64}$"


def supported_assertion_types(temporal: TemporalShape) -> frozenset[AssertionType]:
    """Assertion types a surface's temporal shape entitles a contract to support.

    Mirrors the compiler's matching families (``compile.typecheck``): state
    shapes support STATE / EXISTENCE / NON_EXISTENCE; event history supports
    TIMING / SEQUENCE / EVENT; AGGREGATE needs an enumerable yield, which
    every capability entry has by schema (a pagination exhaustion method is
    required). A snapshot-cadence feed therefore never claims it can prove a
    TIMING assertion (PRD-v3 §2).
    """
    types: set[AssertionType] = {AssertionType.AGGREGATE}
    if temporal.kind in STATE_SHAPES:
        types |= STATE_FAMILY
    if temporal.kind in (TemporalShapeKind.EVENT_HISTORY, TemporalShapeKind.FULL_HISTORY):
        types |= EVENT_FAMILY
    return frozenset(types)


def _shape_text(temporal: TemporalShape) -> str:
    if temporal.kind is TemporalShapeKind.EVENT_HISTORY:
        return f"event-history(window={temporal.window_days}d)"
    return temporal.kind.value.lower().replace("_", "-")


class PageRequest(AegisModel):
    """One page fetch, addressed by system, surface, and 1-based index."""

    system: str = Field(min_length=1)
    surface: str = Field(min_length=1)
    page_index: int = Field(ge=1)


class Transport(Protocol):
    """Injected page fetcher. ``None`` means: no such page (feed ended).

    Tests and the demo pipeline inject :class:`FixtureTransport`; live
    transports (COL02+) implement the same protocol so the collector body
    never changes between fixture and tenant runs.
    """

    def fetch_page(self, request: PageRequest) -> dict[str, Any] | None: ...  # pragma: no cover


class FixtureTransport:
    """Reads fixture-tenant pages from ``<root>/<system>/page-<n>.json``.

    The only transport used anywhere in tests and the demo pipeline —
    no live-tenant calls (docs/HANDOFF.md §4). A missing file is the end
    of the feed and returns ``None``; the collector's completeness check
    decides whether what was fetched proves exhaustion.
    """

    __slots__ = ("_root",)

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def fetch_page(self, request: PageRequest) -> dict[str, Any] | None:
        path = self._root / request.system / f"page-{request.page_index}.json"
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))


class CollectionSnapshot(AegisModel):
    """One collection run, hashed before any interpretation.

    ``page_hashes[i]`` is the SHA-256 canonical-JSON hash of raw
    ``pages[i]`` exactly as retrieved; ``snapshot_hash`` seals the
    assembled collection (its own field nulled, prior
    ``compute_record_hash`` semantics). ``retrieved_at`` is the caller's
    explicit input, never a clock read.

    Constructor-enforced: ``complete`` iff ``incompleteness`` is empty —
    an incomplete snapshot always names why (salvaged fail-loud
    discipline from the prior scaffold's ``CompletenessError``).
    """

    plan_ref: str = Field(min_length=1)
    entry_id: str = Field(min_length=1)
    system: str = Field(min_length=1)
    population_ref: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    retrieved_at: datetime
    pages: tuple[dict[str, Any], ...] = ()
    page_hashes: tuple[str, ...] = ()
    complete: bool
    incompleteness: tuple[str, ...] = ()
    snapshot_hash: str | None = Field(default=None, pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def _flag_matches_reasons(self) -> "CollectionSnapshot":
        if self.complete and self.incompleteness:
            raise ValueError("a complete snapshot may not carry incompleteness reasons")
        if not self.complete and not self.incompleteness:
            raise ValueError("an incomplete snapshot must name its incompleteness")
        if len(self.pages) != len(self.page_hashes):
            raise ValueError(f"{len(self.pages)} page(s) but {len(self.page_hashes)} page hash(es)")
        return self

    def compute_snapshot_hash(self) -> str:
        """Canonical hash of the assembled collection, own hash field nulled."""
        return sha256_canonical(self, ["snapshot_hash"])

    def sealed(self) -> "CollectionSnapshot":
        """Return a copy with ``snapshot_hash`` computed and set."""
        return self.model_copy(update={"snapshot_hash": self.compute_snapshot_hash()})


def plan_ref(plan: CompiledCollectorPlan) -> str:
    """Deterministic reference string for one compiled collector plan."""
    return f"{plan.claim_ref}/{plan.assertion_ref}/{plan.entry_id}"


class Collector(ABC):
    """Executes compiled collector plans for one system's surfaces.

    Subclasses (one per capability surface, COL01–05) supply the
    surface-specific exhaustion signal and completeness check; the base
    drives the fetch loop, hashes every raw page and the assembled
    snapshot, and emits the EvidenceQualityContract.
    """

    #: The system this collector serves; must match ``plan.system``.
    system: ClassVar[str]
    #: EQC ``collector_version`` (contract identity, PRD-v3 §2).
    collector_version: ClassVar[str]
    #: EQC ``schema_version``: the raw page schema this collector parses.
    page_schema_version: ClassVar[str]

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def collect(self, plan: CompiledCollectorPlan, retrieved_at: datetime) -> CollectionSnapshot:
        """Fetch until the surface's exhaustion signal or the feed ends.

        The fetch loop stops when the subclass reports the exhaustion
        signal present (e.g. the HRIS feed's trailer record) or the
        transport runs out of pages; :meth:`_completeness` then decides —
        per the capability entry's exhaustion method — whether the fetched
        pages prove exhaustion. Partial collection is a flagged-incomplete
        snapshot, never an error and never a partial pass.
        """
        if plan.system != self.system:
            raise ValueError(
                f"plan {plan_ref(plan)} targets system {plan.system!r}; "
                f"this collector serves {self.system!r}"
            )
        pages: list[dict[str, Any]] = []
        hashes: list[str] = []
        index = 1
        while True:
            payload = self._transport.fetch_page(
                PageRequest(system=plan.system, surface=plan.surface, page_index=index)
            )
            if payload is None:
                break
            pages.append(payload)
            hashes.append(sha256_canonical(payload))
            if self._exhausted(tuple(pages)):
                break
            index += 1
        complete, reasons = self._completeness(tuple(pages))
        return CollectionSnapshot(
            plan_ref=plan_ref(plan),
            entry_id=plan.entry_id,
            system=plan.system,
            population_ref=plan.population_ref,
            source_id=plan.source_id,
            retrieved_at=retrieved_at,
            pages=tuple(pages),
            page_hashes=tuple(hashes),
            complete=complete,
            incompleteness=reasons,
        ).sealed()

    def contract(
        self, plan: CompiledCollectorPlan, tenant: str, retrieved_at: datetime
    ) -> EvidenceQualityContract:
        """The EQC for one plan: identity + five named property methods.

        Every method is named from plan/capability fields (PRD-v3 §2) —
        the population property carries the capability entry's exhaustion
        method verbatim, temporal validity carries the entry's temporal
        shape over the plan's window. ``contract_hash`` is computed with
        ``retrieved_at`` nulled (the contract's identity is authored
        before collection runs; ``schema/contract.py``).
        """
        eqc = EvidenceQualityContract(
            source_system=plan.system,
            tenant=tenant,
            population_ref=plan.population_ref,
            endpoint=plan.surface,
            parameters=(
                Parameter(name="entry_id", value=plan.entry_id),
                Parameter(name="source_id", value=plan.source_id),
            ),
            time_window=plan.time_window,
            schema_version=self.page_schema_version,
            collector_version=self.collector_version,
            retrieved_at=retrieved_at,
            auth_context=plan.auth_scope,
            provenance=QualityProperty(
                method=(
                    f"least-privilege retrieval declared by capability entry "
                    f"{plan.entry_id}: {plan.auth_scope}"
                )
            ),
            integrity=QualityProperty(
                method=(
                    "SHA-256 over canonical JSON of every raw page and the assembled "
                    "collection snapshot (schema/canonical.py), computed before any "
                    "interpretation"
                )
            ),
            population=QualityProperty(method=plan.pagination.exhaustion_method),
            semantics=QualityProperty(
                method=(
                    f"typed parse of {self.page_schema_version} records; identity keyed "
                    f"by {', '.join(plan.join_keys)}"
                )
            ),
            temporal_validity=QualityProperty(
                method=(
                    f"evidence represents {_shape_text(plan.temporal)} over "
                    f"{plan.time_window.start.isoformat()}..{plan.time_window.end.isoformat()}"
                )
            ),
            supported_assertion_types=supported_assertion_types(plan.temporal),
        )
        return eqc.model_copy(update={"contract_hash": eqc.compute_contract_hash()})

    @abstractmethod
    def _exhausted(self, pages: tuple[dict[str, Any], ...]) -> bool:
        """True when the fetched pages carry the surface's exhaustion signal."""

    @abstractmethod
    def _completeness(self, pages: tuple[dict[str, Any], ...]) -> tuple[bool, tuple[str, ...]]:
        """(complete, reasons) per the capability entry's exhaustion method."""
