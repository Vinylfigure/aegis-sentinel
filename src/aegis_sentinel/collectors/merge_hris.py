"""COL06 — deterministic Merge HRIS employee-roster collector.

The transport is an injected callable taking a cursor and returning the
raw page bytes (or None when no page exists at that cursor), so the
collector logic performs no I/O of its own: fixture bytes in tests, a
real extract later, identical code path either way (no live-tenant
calls in tests — HANDOFF §4 COL01–05). Pagination follows the registry
entry merge.hris.employees: cursor-based, the page's own 'next' field
passed back as the 'cursor' query param until it is null. Every page's
raw bytes are SHA-256 hashed at intake, the cursor chain is recorded
page by page, employees are parsed into closed typed records, and an
EvidenceQualityContract is emitted with all five quality property
methods named.

Refusal, never partial pass: a page asserting the wrong X-Account-Token
tenant identity (provenance — Merge's auth model per the registry
entry, not just an org name), a cursor chain that does not terminate (a
repeated cursor, or a claimed next page the source cannot produce), or
a page whose own claimed row count exceeds the rows it actually carried
(truncation) all raise — the collector never silently returns a
partial employee population.

Determinism per D-P3: no clocks — the account token and period are
explicit inputs, and the capture time travels inside the payload
itself. Merge is a STATE-only source (registry temporal.kind
"state-only"): the contract supports no TIMING assertion by itself. An
employee row missing either join key (employee_id, email) survives
collection intact — identity resolution is the reconciler's job, and a
fuzzy identity ends UNKNOWN_POPULATION per D-7/D-U1, never a silently
dropped row.
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

SOURCE_SYSTEM = "merge"
CAPABILITY_ID = "merge.hris.employees"
COLLECTOR_VERSION = "0.1.0"
DEFAULT_PAGE_SIZE = 30


class EmployeeRecord(Base):
    """One employee roster row, typed with the registry-yielded
    attributes plus the join-key fields (registry merge.hris.employees
    join_keys: employee_id, email). Either join key may be null and the
    row still survives collection intact — a fuzzy identity is the
    reconciler's job (UNKNOWN_POPULATION per D-7/D-U1), never a row
    silently dropped at collection."""

    id: str = Field(min_length=1)
    employee_id: str | None = None
    email: str | None = None
    employment_status: str = Field(min_length=1)
    termination_date: datetime | None = None
    start_date: datetime | None = None


class EmployeePage(Base):
    """One raw page envelope, closed-schema parsed. account_token is the
    X-Account-Token tenant-identity header Merge's Unified API keys
    authorization to (registry auth_scope) — asserted per page, not
    just once, so a wrong-tenant page mid-chain is caught. count is the
    page's own claimed row count; a mismatch against len(results) is a
    truncated page, refused rather than silently accepted."""

    account_token: str = Field(min_length=1)
    captured_at: datetime
    cursor: str | None
    next: str | None
    count: int = Field(ge=0)
    results: tuple[EmployeeRecord, ...]


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


class MergeHrisCollection(Base):
    records: tuple[EmployeeRecord, ...]
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
    account_token: str,
    period: TimeWindow,
    population_ref: str,
    page_size: int,
    collector_version: str,
) -> EvidenceQualityContract:
    contract = EvidenceQualityContract.model_validate(
        {
            "id": f"eqc-{SOURCE_SYSTEM}-hris-employees-v1",
            "source": SOURCE_SYSTEM,
            "tenant": account_token,
            "population_ref": population_ref,
            "endpoint": "Merge Unified API GET /api/hris/v1/employees",
            "parameters": {
                "capability": CAPABILITY_ID,
                "pagination": "cursor ('next')",
                "page_size": str(page_size),
            },
            "time_window": {
                "start": period.start.isoformat(),
                "end": period.end.isoformat(),
            },
            "schema_version": "merge.hris.employees/v1",
            "collector_version": collector_version,
            "auth_context": "API key (Authorization: Bearer) plus X-Account-Token "
            "identifying the linked HRIS tenant",
            "contract_hash": "0" * 64,  # placeholder; replaced by the canonical self-hash
            "quality": {
                "provenance": {
                    "method": "X-Account-Token tenant identity asserted in every page "
                    "envelope and matched against the engagement account token per page "
                    "— Merge's auth model keys to the linked HRIS tenant, not an org name",
                    "failure_mode": "page from an unauthenticated or wrong-account-token origin",
                },
                "integrity": {
                    "method": "SHA-256 of each raw page recorded at intake in the "
                    "cursor chain; collection hash over the ordered page bytes, WORM-stored",
                    "failure_mode": "hash mismatch against a stored raw page",
                },
                "population": {
                    "method": "cursor pagination followed via 'next' until absent; "
                    "chain recorded page by page; a repeated cursor, a claimed next page "
                    "the source cannot produce, or a page's own row count exceeding its "
                    "actual rows refuses the collection",
                    "failure_mode": "broken, cyclic, or truncated cursor chain — partial "
                    "employee population",
                },
                "semantics": {
                    "method": "closed-schema parse of every row into typed EmployeeRecord "
                    "fields; unknown fields rejected",
                    "failure_mode": "Merge Unified API schema drift or field meaning change",
                },
                "temporal_validity": {
                    "method": "state-only snapshot (registry merge.hris.employees): "
                    "capture time recorded in every page envelope and compared against "
                    "the asserted period; supports no TIMING assertion by itself",
                    "failure_mode": "snapshot captured outside the asserted window, or the "
                    "current-state roster mistaken for employment history",
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
) -> tuple[EmployeePage, bytes] | None:
    raw = transport(cursor)
    if raw is None:
        return None
    if not isinstance(raw, bytes):
        raise TypeError("transport must return the raw page payload as bytes (or None)")
    page = EmployeePage.model_validate(json.loads(raw.decode("utf-8")))
    if page.cursor != cursor:
        raise ValueError(
            f"page {page_number} answers cursor {page.cursor!r} but {cursor!r} was "
            "requested (integrity)"
        )
    return page, raw


def collect_merge_employees(
    transport: Callable[[str | None], bytes | None],
    *,
    account_token: str,
    period: TimeWindow,
    population_ref: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    collector_version: str = COLLECTOR_VERSION,
) -> MergeHrisCollection:
    """Collect the employee roster through the injected cursor transport
    (called with None for the first page, then with each claimed 'next'
    cursor; returns raw bytes, or None when no page exists at that
    cursor).

    Raises on anything that would silently weaken the population or
    provenance claim: a wrong-account-token page (provenance), a cursor
    chain that does not terminate — a repeated cursor or a claimed next
    page the source cannot produce (population) — or a page whose own
    claimed row count exceeds the rows it actually carried (truncation):
    a partial employee population is refused, never returned.
    """
    pages: list[EmployeePage] = []
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
                "refusing partial employee population (population)"
            )
        page, raw = fetched
        page_sha = hashlib.sha256(raw).hexdigest()
        if page.account_token != account_token:
            raise ValueError(
                f"page account_token {page.account_token!r} != engagement account_token "
                f"{account_token!r} (provenance)"
            )
        if len(page.results) != page.count:
            raise ValueError(
                f"page {len(pages) + 1} claims count={page.count} but returned "
                f"{len(page.results)} rows — truncated page (population)"
            )
        pages.append(page)
        combined.update(raw)
        chain.append(
            PageEvidence(
                cursor=cursor,
                raw_sha256=page_sha,
                rows_seen=len(page.results),
                next_cursor=page.next,
            )
        )
        if page.next is None:
            break
        if page.next in seen_cursors:
            raise ValueError(
                f"cursor chain does not terminate: cursor {page.next!r} repeats — "
                "refusing partial employee population (population)"
            )
        cursor = page.next

    records = tuple(record for page in pages for record in page.results)
    pagination = PaginationEvidence(
        method="cursor",
        pages_fetched=len(pages),
        exhausted=True,
        exhaustion_method=(
            f"followed the 'next' cursor chain until absent across {len(pages)} "
            f"page(s) ({len(records)} employees); chain recorded page by page, "
            "terminal next_cursor=None"
        ),
        cursor_chain=tuple(chain),
    )
    contract = _build_contract(
        account_token=account_token,
        period=period,
        population_ref=population_ref,
        page_size=page_size,
        collector_version=collector_version,
    )
    return MergeHrisCollection(
        records=records,
        raw_sha256=combined.hexdigest(),
        pagination=pagination,
        contract=contract,
    )
