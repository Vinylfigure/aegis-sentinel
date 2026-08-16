"""COL02 — deterministic Okta System Log deactivation collector.

The transport is an injected callable taking a cursor and returning the
raw page bytes (or None when no page exists at that cursor), so the
collector logic performs no I/O of its own: fixture bytes in tests, a
real extract later, identical code path either way (no live-tenant calls
in tests — HANDOFF §4 COL01–05). Every page's raw bytes are SHA-256
hashed at intake, the cursor chain is recorded page by page (the
okta.system_log capability entry's exhaustion method: follow the 'after'
cursor until absent), events are parsed into closed typed records, and
an EvidenceQualityContract is emitted with all five quality property
methods named.

Refusal, never partial pass: a wrong-tenant page, a cursor chain that
does not terminate (a repeated cursor, or a claimed next page the source
cannot produce), or an asserted period older than the capability's
90-day event-history window all raise — the collector never silently
returns a partial event history (the E204 temporal-insufficiency lane).

Determinism per D-P3: no clocks — the period, tenant, and window depth
are explicit inputs, and the extract time travels inside the payload
itself. A deactivation whose target carries no email survives intact:
identity resolution is the reconciler's job, and a fuzzy identity ends
as UNKNOWN_POPULATION per D-7/D-U1 — never a silently dropped row.
"""

import hashlib
import json
from collections.abc import Callable
from datetime import datetime, timedelta

from pydantic import Field

from aegis_sentinel.schema.enums import AssertionType
from aegis_sentinel.schema.models import (
    SHA256,
    Base,
    EvidenceQualityContract,
    TimeWindow,
)

SOURCE_SYSTEM = "okta"
COLLECTOR_VERSION = "0.1.0"
DEACTIVATE_EVENT_TYPE = "user.lifecycle.deactivate"
# Capability window (registry/capabilities/okta.system_log.json): System Log
# retains 90 days of event history. Explicit input with this default so the
# figure stays capability-derived, not a clock-adjacent constant buried in code.
CAPABILITY_WINDOW_DAYS = 90


class LogPrincipal(Base):
    """An actor or target in a System Log event. alternate_id is the
    email join key (okta.system_log join_keys); a null email survives
    parsing — the reconciler buckets that identity UNRESOLVABLE and the
    verdict path ends UNKNOWN_POPULATION per D-7/D-U1, never a dropped
    row at collection."""

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    alternate_id: str | None = None
    display_name: str | None = None


class LogOutcome(Base):
    result: str = Field(min_length=1)
    reason: str | None = None


class LogEvent(Base):
    """One System Log event, closed-schema typed. Duplicate event uuids
    (cursor-boundary replays) are kept — deduplication is
    reconciliation's job, not collection's."""

    uuid: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    published: datetime
    actor: LogPrincipal
    target: tuple[LogPrincipal, ...] = Field(min_length=1)
    outcome: LogOutcome


class SystemLogPage(Base):
    """One raw page envelope: the cursor it was served for, the 'after'
    cursor it claims comes next (None = terminal), and the extract
    identity every page must assert."""

    tenant: str = Field(min_length=1)
    extracted_at: datetime
    cursor: str | None
    after: str | None
    events: tuple[LogEvent, ...]


class PageEvidence(Base):
    """One link of the recorded cursor chain: the cursor requested, the
    raw bytes' hash at intake, and the next cursor the page claimed."""

    cursor: str | None
    raw_sha256: str = Field(pattern=SHA256)
    events_seen: int = Field(ge=0)
    next_cursor: str | None


class PaginationEvidence(Base):
    """Exhaustion is evidenced by the recorded chain itself: every link
    named, terminating in next_cursor=None. A chain that cannot be shown
    to terminate is refused upstream, never recorded as exhausted."""

    method: str = Field(min_length=1)
    pages_fetched: int = Field(ge=1)
    exhausted: bool
    exhaustion_method: str = Field(min_length=1)
    cursor_chain: tuple[PageEvidence, ...] = Field(min_length=1)


class OktaSystemLogCollection(Base):
    records: tuple[LogEvent, ...]
    raw_sha256: str = Field(pattern=SHA256)
    pagination: PaginationEvidence
    contract: EvidenceQualityContract


def _sha256_canonical_json(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def canonical_contract_hash(contract: EvidenceQualityContract) -> str:
    """D-P3 canonical hash: SHA-256 over the contract's canonical JSON
    with its one volatile field (contract_hash itself) nulled. Kept
    local (mirroring collectors/hris.py) so collector tracks stay
    independent until the conductor extracts a shared helper at merge."""
    data = contract.model_dump(mode="json")
    data["contract_hash"] = None
    return _sha256_canonical_json(data)


def _build_contract(
    *,
    tenant: str,
    period: TimeWindow,
    population_ref: str,
    window_days: int,
    collector_version: str,
) -> EvidenceQualityContract:
    contract = EvidenceQualityContract.model_validate(
        {
            "id": f"eqc-{SOURCE_SYSTEM}-system-log-deactivations-v1",
            "source": SOURCE_SYSTEM,
            "tenant": tenant,
            "population_ref": population_ref,
            "endpoint": "System Log API GET /api/v1/logs",
            "parameters": {
                "filter": f'eventType eq "{DEACTIVATE_EVENT_TYPE}"',
                "pagination": "cursor ('after')",
            },
            "time_window": {
                "start": period.start.isoformat(),
                "end": period.end.isoformat(),
            },
            "schema_version": "okta.system_log/v1",
            "collector_version": collector_version,
            "auth_context": "API token scoped to okta.logs.read only",
            "contract_hash": "0" * 64,  # placeholder; replaced by the canonical self-hash
            "quality": {
                "provenance": {
                    "method": "tenant identity asserted in every page envelope and "
                    "matched against the engagement tenant per page",
                    "failure_mode": "page from an unauthenticated or wrong-tenant origin",
                },
                "integrity": {
                    "method": "SHA-256 of each raw page recorded at intake in the "
                    "cursor chain; collection hash over the ordered page bytes, WORM-stored",
                    "failure_mode": "hash mismatch against a stored raw page",
                },
                "population": {
                    "method": "cursor pagination followed via 'after' until absent; "
                    "chain recorded page by page; a repeated cursor or a claimed "
                    "next page the source cannot produce refuses the collection",
                    "failure_mode": "broken or cyclic cursor chain — partial event history",
                },
                "semantics": {
                    "method": "closed-schema parse of every event into typed LogEvent "
                    "fields; unknown fields rejected; only "
                    f"{DEACTIVATE_EVENT_TYPE} events admitted as records",
                    "failure_mode": "System Log schema drift or eventType meaning change",
                },
                "temporal_validity": {
                    "method": f"asserted period checked against the {window_days}-day "
                    "event-history window relative to the extract timestamp in the "
                    "payload; an older period start refuses (E204)",
                    "failure_mode": "asserted period reaching beyond retained history — "
                    "silently partial TIMING evidence",
                },
            },
            "supported_assertion_types": [
                AssertionType.EVENT,
                AssertionType.EXISTENCE,
                AssertionType.NON_EXISTENCE,
                AssertionType.TIMING,
            ],
        }
    )
    return contract.model_copy(update={"contract_hash": canonical_contract_hash(contract)})


def _fetch_page(
    transport: Callable[[str | None], bytes | None], cursor: str | None, page_number: int
) -> tuple[SystemLogPage, bytes] | None:
    raw = transport(cursor)
    if raw is None:
        return None
    if not isinstance(raw, bytes):
        raise TypeError("transport must return the raw page payload as bytes (or None)")
    page = SystemLogPage.model_validate(json.loads(raw.decode("utf-8")))
    if page.cursor != cursor:
        raise ValueError(
            f"page {page_number} answers cursor {page.cursor!r} but {cursor!r} was "
            "requested (integrity)"
        )
    return page, raw


def collect_okta_deactivations(
    transport: Callable[[str | None], bytes | None],
    *,
    tenant: str,
    period: TimeWindow,
    population_ref: str,
    window_days: int = CAPABILITY_WINDOW_DAYS,
    collector_version: str = COLLECTOR_VERSION,
) -> OktaSystemLogCollection:
    """Collect user.lifecycle.deactivate events through the injected
    cursor transport (called with None for the first page, then with
    each claimed 'after' cursor; returns raw bytes, or None when no
    page exists at that cursor).

    Raises on anything that would silently weaken the population or
    timing claim: a wrong-tenant page (provenance), a cursor chain that
    does not terminate — a repeated cursor or a claimed next page the
    source cannot produce (population) — or an asserted period start
    older than the capability window relative to the extract timestamp
    (E204 temporal insufficiency): a partial event history is refused,
    never returned.
    """
    pages: list[SystemLogPage] = []
    chain: list[PageEvidence] = []
    combined = hashlib.sha256()
    cursor: str | None = None
    seen_cursors: set[str | None] = set()

    while True:
        seen_cursors.add(cursor)
        fetched = _fetch_page(transport, cursor, len(pages) + 1)
        if fetched is None:
            if not pages:
                raise ValueError(
                    "cursor chain broken: the source returned no first page (population)"
                )
            raise ValueError(
                f"cursor chain broken after {len(pages)} page(s): page {len(pages)} "
                f"claims next cursor {cursor!r} but the source returned no page — "
                "refusing partial event history (population)"
            )
        page, raw = fetched
        page_sha = hashlib.sha256(raw).hexdigest()
        if page.tenant != tenant:
            raise ValueError(
                f"page tenant {page.tenant!r} != engagement tenant {tenant!r} (provenance)"
            )
        if not pages:
            # Window honesty before fetching further: the extract timestamp
            # travels in the payload (D-P3 — no clocks), and the asserted
            # period must fit inside the capability's event-history window.
            window_floor = page.extracted_at - timedelta(days=window_days)
            if period.start < window_floor:
                raise ValueError(
                    f"asserted period start {period.start.isoformat()} predates the "
                    f"{window_days}-day event-history window (floor "
                    f"{window_floor.isoformat()}) relative to extract time "
                    f"{page.extracted_at.isoformat()} — refusing partial event "
                    "history (E204 temporal insufficiency)"
                )
        pages.append(page)
        combined.update(raw)
        chain.append(
            PageEvidence(
                cursor=cursor,
                raw_sha256=page_sha,
                events_seen=len(page.events),
                next_cursor=page.after,
            )
        )
        if page.after is None:
            break
        if page.after in seen_cursors:
            raise ValueError(
                f"cursor chain does not terminate: cursor {page.after!r} repeats — "
                "refusing partial event history (population)"
            )
        cursor = page.after

    records = tuple(
        event
        for page in pages
        for event in page.events
        if event.event_type == DEACTIVATE_EVENT_TYPE
    )
    total_events = sum(len(page.events) for page in pages)
    pagination = PaginationEvidence(
        method="cursor",
        pages_fetched=len(pages),
        exhausted=True,
        exhaustion_method=(
            f"followed the 'after' cursor chain until absent across {len(pages)} "
            f"page(s) ({total_events} events seen, {len(records)} "
            f"{DEACTIVATE_EVENT_TYPE}); chain recorded page by page, terminal "
            "next_cursor=None"
        ),
        cursor_chain=tuple(chain),
    )
    contract = _build_contract(
        tenant=tenant,
        period=period,
        population_ref=population_ref,
        window_days=window_days,
        collector_version=collector_version,
    )
    return OktaSystemLogCollection(
        records=records,
        raw_sha256=combined.hexdigest(),
        pagination=pagination,
        contract=contract,
    )
