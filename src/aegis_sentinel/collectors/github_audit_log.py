"""GitHub org audit-log collector — Deliverable 4 collector gap for Lane A
(issue #152), the GitHub-side event-history analogue of
collectors/okta_system_log.py's Okta-side TIMING evidence.

The transport is an injected callable taking a cursor and returning the
raw page bytes (or None when no page exists at that cursor), so the
collector logic performs no I/O of its own: fixture bytes in tests, a
real extract later, identical code path either way (no live-tenant calls
in tests — HANDOFF §4 COL01–05). Pagination follows the registry entry
github.audit_log: cursor-based, Link rel=next followed until absent.
Every page's raw bytes are SHA-256 hashed at intake, the cursor chain is
recorded page by page, events are parsed into closed typed records, and
an EvidenceQualityContract is emitted with all five quality property
methods named.

Refusal, never a silent partial population: a wrong-org page
(provenance), a cursor chain that does not terminate or repeats
(population), a page whose own claimed event count exceeds the rows it
actually carried (truncation), or an asserted period older than the
capability's 180-day event-history window (E204 temporal
insufficiency). No action filter —
the registry's own population description ("org audit events incl.
member removal") admits the whole audit stream, not just
org.remove_member; narrowing to one action is reconciliation's job. A
null user (an org-level action with no specific target account) survives
collection intact — identity resolution is the reconciler's job, and a
fuzzy identity ends UNKNOWN_POPULATION per D-7/D-U1, never a silently
dropped row.
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

SOURCE_SYSTEM = "github"
CAPABILITY_ID = "github.audit_log"
COLLECTOR_VERSION = "0.1.0"
# Capability window (registry/capabilities/github.audit_log.json): audit
# log retains 180 days of event history. Explicit input with this default
# so the figure stays capability-derived, not a clock-adjacent constant
# buried in code.
CAPABILITY_WINDOW_DAYS = 180


class AuditEventRecord(Base):
    """One org audit-log event row, typed with the registry-yielded
    attributes (action/actor/user/created_at). The join key (registry
    github.audit_log join_keys: login) is carried on ``user`` — a null
    user (an org-level action with no specific target account) survives
    collection intact; identity resolution is the reconciler's job, and a
    fuzzy identity ends UNKNOWN_POPULATION per D-7/D-U1, never a dropped
    row."""

    action: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    user: str | None = None
    created_at: datetime


class AuditLogPage(Base):
    """One raw page envelope: the org identity every page must assert,
    the cursor it was served for, the 'after' cursor it claims comes next
    (None = terminal), the extract identity, and the page's own claimed
    event count — a mismatch against len(events) is a truncated page,
    refused rather than silently accepted as a smaller population."""

    org: str = Field(min_length=1)
    extracted_at: datetime
    cursor: str | None
    after: str | None
    event_count: int = Field(ge=0)
    events: tuple[AuditEventRecord, ...]


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


class GithubAuditLogCollection(Base):
    records: tuple[AuditEventRecord, ...]
    raw_sha256: str = Field(pattern=SHA256)
    pagination: PaginationEvidence
    contract: EvidenceQualityContract


def _sha256_canonical_json(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def canonical_contract_hash(contract: EvidenceQualityContract) -> str:
    """D-P3 canonical hash: SHA-256 over the contract's canonical JSON
    with its one volatile field (contract_hash itself) nulled. Kept local
    (mirroring collectors/hris.py) so collector tracks stay independent
    until the conductor extracts a shared helper at merge."""
    data = contract.model_dump(mode="json")
    data["contract_hash"] = None
    return _sha256_canonical_json(data)


def _build_contract(
    *,
    org: str,
    period: TimeWindow,
    population_ref: str,
    window_days: int,
    collector_version: str,
) -> EvidenceQualityContract:
    contract = EvidenceQualityContract.model_validate(
        {
            "id": f"eqc-{SOURCE_SYSTEM}-audit-log-v1",
            "source": SOURCE_SYSTEM,
            "tenant": org,
            "population_ref": population_ref,
            "endpoint": f"REST GET /orgs/{org}/audit-log (Enterprise Cloud)",
            "parameters": {"capability": CAPABILITY_ID, "pagination": "cursor (Link rel=next)"},
            "time_window": {
                "start": period.start.isoformat(),
                "end": period.end.isoformat(),
            },
            "schema_version": "github.audit_log/v1",
            "collector_version": collector_version,
            "auth_context": "read:audit_log (fine-grained: Administration org permission, read)",
            "contract_hash": "0" * 64,  # placeholder; replaced by the canonical self-hash
            "quality": {
                "provenance": {
                    "method": "org identity asserted in every page envelope and matched "
                    "against the engagement org per page",
                    "failure_mode": "page served from an unauthenticated or wrong-org origin",
                },
                "integrity": {
                    "method": "SHA-256 of each raw page recorded at intake in the "
                    "cursor chain; collection hash over the ordered page bytes, WORM-stored",
                    "failure_mode": "hash mismatch against a stored raw page",
                },
                "population": {
                    "method": "cursor pagination; Link rel=next followed until absent; "
                    "chain recorded page by page; a repeated cursor, a claimed next page "
                    "the source cannot produce, or a page's own event count exceeding its "
                    "actual rows refuses the collection",
                    "failure_mode": "broken, cyclic, or truncated cursor chain — partial "
                    "event history",
                },
                "semantics": {
                    "method": "closed-schema parse of every event into typed "
                    "AuditEventRecord fields; unknown fields rejected",
                    "failure_mode": "audit-log schema drift or action-field meaning change",
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
) -> tuple[AuditLogPage, bytes] | None:
    raw = transport(cursor)
    if raw is None:
        return None
    if not isinstance(raw, bytes):
        raise TypeError("transport must return the raw page payload as bytes (or None)")
    page = AuditLogPage.model_validate(json.loads(raw.decode("utf-8")))
    if page.cursor != cursor:
        raise ValueError(
            f"page {page_number} answers cursor {page.cursor!r} but {cursor!r} was "
            "requested (integrity)"
        )
    return page, raw


def collect_github_audit_log(
    transport: Callable[[str | None], bytes | None],
    *,
    org: str,
    period: TimeWindow,
    population_ref: str,
    window_days: int = CAPABILITY_WINDOW_DAYS,
    collector_version: str = COLLECTOR_VERSION,
) -> GithubAuditLogCollection:
    """Collect the org audit-log event stream through the injected cursor
    transport (called with None for the first page, then with each
    claimed 'after' cursor; returns raw bytes, or None when no page
    exists at that cursor).

    Raises on anything that would silently weaken the population or
    timing claim: a wrong-org page (provenance), a cursor chain that does
    not terminate — a repeated cursor or a claimed next page the source
    cannot produce (population) — a page whose own claimed event count
    exceeds the rows it actually carried (truncation), or an asserted
    period start older than the capability window relative to the
    extract timestamp (E204 temporal insufficiency): a partial event
    history is refused, never returned.
    """
    pages: list[AuditLogPage] = []
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
        if page.org != org:
            raise ValueError(f"page org {page.org!r} != engagement org {org!r} (provenance)")
        if len(page.events) != page.event_count:
            raise ValueError(
                f"page {len(pages) + 1} claims event_count={page.event_count} but "
                f"returned {len(page.events)} rows — truncated page (population)"
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

    records = tuple(event for page in pages for event in page.events)
    pagination = PaginationEvidence(
        method="cursor",
        pages_fetched=len(pages),
        exhausted=True,
        exhaustion_method=(
            f"followed the Link rel=next ('after') cursor chain until absent "
            f"across {len(pages)} page(s) ({len(records)} events); chain recorded "
            "page by page, terminal next_cursor=None"
        ),
        cursor_chain=tuple(chain),
    )
    contract = _build_contract(
        org=org,
        period=period,
        population_ref=population_ref,
        window_days=window_days,
        collector_version=collector_version,
    )
    return GithubAuditLogCollection(
        records=records,
        raw_sha256=combined.hexdigest(),
        pagination=pagination,
        contract=contract,
    )
