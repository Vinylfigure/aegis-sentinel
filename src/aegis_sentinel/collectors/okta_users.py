"""Okta directory-users collector — Deliverable 4 collector gap for Lane A
(issue #152), the stable per-user snapshot Okta-side reconciliation joins
against (collectors/okta_system_log.py's events alone don't carry a
queryable directory snapshot).

The transport is an injected callable taking a cursor and returning the
raw page bytes (or None when no page exists at that cursor), so the
collector logic performs no I/O of its own: fixture bytes in tests, a
real extract later, identical code path either way (no live-tenant calls
in tests — HANDOFF §4 COL01–05). Pagination follows the registry entry
okta.users: cursor-based, Link rel=next 'after' cursor followed until
absent. Every page's raw bytes are SHA-256 hashed at intake, the cursor
chain is recorded page by page, users are parsed into closed typed
records, and an EvidenceQualityContract is emitted with all five quality
property methods named.

Refusal, never a silent partial population: a wrong-tenant page
(provenance), or a cursor chain that does not terminate or repeats
(population). Okta is a STATE-only source (registry temporal.kind
"state-only"): the contract supports no TIMING assertion by itself. A
null email survives collection intact — identity resolution is the
reconciler's job, and a fuzzy identity ends UNKNOWN_POPULATION per
D-7/D-U1, never a silently dropped row.
"""

import hashlib
import json
from collections.abc import Callable
from datetime import datetime

from pydantic import Field

from aegis_sentinel.schema.enums import AssertionType
from aegis_sentinel.schema.models import (
    SHA256,
    Base,
    EvidenceQualityContract,
    TimeWindow,
)

SOURCE_SYSTEM = "okta"
CAPABILITY_ID = "okta.users"
COLLECTOR_VERSION = "0.1.0"


class UserRecord(Base):
    """One directory-user row, typed with the registry-yielded attributes
    (id/status/profile.email/profile.login/statusChanged). A null email
    survives collection intact — identity resolution is the reconciler's
    job, and a fuzzy identity ends UNKNOWN_POPULATION per D-7/D-U1, never
    a silently dropped row."""

    id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    email: str | None = None
    login: str = Field(min_length=1)
    status_changed: datetime


class UsersPage(Base):
    """One raw page envelope: the tenant identity every page must assert,
    the cursor it was served for, the 'after' cursor it claims comes next
    (None = terminal), and the extract identity."""

    tenant: str = Field(min_length=1)
    extracted_at: datetime
    cursor: str | None
    after: str | None
    rows: tuple[UserRecord, ...]


class PageEvidence(Base):
    """One link of the recorded cursor chain: the cursor requested, the
    raw bytes' hash at intake, and the next cursor the page claimed."""

    cursor: str | None
    raw_sha256: str = Field(pattern=SHA256)
    rows_seen: int = Field(ge=0)
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


class OktaUsersCollection(Base):
    records: tuple[UserRecord, ...]
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
    tenant: str,
    period: TimeWindow,
    population_ref: str,
    collector_version: str,
) -> EvidenceQualityContract:
    contract = EvidenceQualityContract.model_validate(
        {
            "id": f"eqc-{SOURCE_SYSTEM}-users-v1",
            "source": SOURCE_SYSTEM,
            "tenant": tenant,
            "population_ref": population_ref,
            "endpoint": "Users API GET /api/v1/users",
            "parameters": {"capability": CAPABILITY_ID, "pagination": "cursor ('after')"},
            "time_window": {
                "start": period.start.isoformat(),
                "end": period.end.isoformat(),
            },
            "schema_version": "okta.users/v1",
            "collector_version": collector_version,
            "auth_context": "API token scoped to okta.users.read only",
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
                    "method": "cursor pagination followed via Link rel=next 'after' "
                    "until absent; chain recorded page by page; a repeated cursor or a "
                    "claimed next page the source cannot produce refuses the collection",
                    "failure_mode": "broken or cyclic cursor chain — partial user population",
                },
                "semantics": {
                    "method": "closed-schema parse of every row into typed UserRecord "
                    "fields; unknown fields rejected",
                    "failure_mode": "Users API schema drift or field meaning change",
                },
                "temporal_validity": {
                    "method": "state-only snapshot (registry okta.users): capture time "
                    "recorded in every page envelope and compared against the asserted "
                    "period; supports no TIMING assertion by itself",
                    "failure_mode": "snapshot captured outside the asserted window, or the "
                    "current-directory list mistaken for status history",
                },
            },
            "supported_assertion_types": [
                AssertionType.STATE,
                AssertionType.EXISTENCE,
                AssertionType.NON_EXISTENCE,
            ],
        }
    )
    return contract.model_copy(update={"contract_hash": canonical_contract_hash(contract)})


def _fetch_page(
    transport: Callable[[str | None], bytes | None], cursor: str | None, page_number: int
) -> tuple[UsersPage, bytes] | None:
    raw = transport(cursor)
    if raw is None:
        return None
    if not isinstance(raw, bytes):
        raise TypeError("transport must return the raw page payload as bytes (or None)")
    page = UsersPage.model_validate(json.loads(raw.decode("utf-8")))
    if page.cursor != cursor:
        raise ValueError(
            f"page {page_number} answers cursor {page.cursor!r} but {cursor!r} was "
            "requested (integrity)"
        )
    return page, raw


def collect_okta_users(
    transport: Callable[[str | None], bytes | None],
    *,
    tenant: str,
    period: TimeWindow,
    population_ref: str,
    collector_version: str = COLLECTOR_VERSION,
) -> OktaUsersCollection:
    """Collect the directory-user population through the injected cursor
    transport (called with None for the first page, then with each
    claimed 'after' cursor; returns raw bytes, or None when no page
    exists at that cursor).

    Raises on anything that would silently weaken the population or
    provenance claim: a wrong-tenant page (provenance), or a cursor chain
    that does not terminate — a repeated cursor or a claimed next page
    the source cannot produce (population): a partial user population is
    refused, never returned.
    """
    pages: list[UsersPage] = []
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
                "refusing partial user population (population)"
            )
        page, raw = fetched
        page_sha = hashlib.sha256(raw).hexdigest()
        if page.tenant != tenant:
            raise ValueError(
                f"page tenant {page.tenant!r} != engagement tenant {tenant!r} (provenance)"
            )
        pages.append(page)
        combined.update(raw)
        chain.append(
            PageEvidence(
                cursor=cursor,
                raw_sha256=page_sha,
                rows_seen=len(page.rows),
                next_cursor=page.after,
            )
        )
        if page.after is None:
            break
        if page.after in seen_cursors:
            raise ValueError(
                f"cursor chain does not terminate: cursor {page.after!r} repeats — "
                "refusing partial user population (population)"
            )
        cursor = page.after

    records = tuple(row for page in pages for row in page.rows)
    pagination = PaginationEvidence(
        method="cursor",
        pages_fetched=len(pages),
        exhausted=True,
        exhaustion_method=(
            f"followed the Link rel=next 'after' cursor chain until absent across "
            f"{len(pages)} page(s) ({len(records)} users); chain recorded page by "
            "page, terminal next_cursor=None"
        ),
        cursor_chain=tuple(chain),
    )
    contract = _build_contract(
        tenant=tenant,
        period=period,
        population_ref=population_ref,
        collector_version=collector_version,
    )
    return OktaUsersCollection(
        records=records,
        raw_sha256=combined.hexdigest(),
        pagination=pagination,
        contract=contract,
    )
