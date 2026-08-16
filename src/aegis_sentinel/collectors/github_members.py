"""COL03 — deterministic GitHub org-members collector.

The transport is an injected callable taking a page key and returning the
raw page payload bytes, so the collector logic performs no I/O of its
own: fixture bytes in tests, a real paginated API later, identical code
path either way (no live-tenant calls in tests — HANDOFF §4 COL01–05).
Pagination follows the registry entry github.members: page-based, with
Link rel=next exhaustion — simulated in fixtures by a "link_next" field
on each page envelope; exhaustion = follow until absent, page count
recorded as evidence. Every page's raw bytes are SHA-256 hashed at
intake and a chain hash covers the whole fetch in order.

Refusals — anything that would silently weaken the population or
provenance claim raises: a wrong-org page (provenance), a mid-chain page
carrying fewer rows than its own per_page claim (truncation:
population), a page-number sequence break, or a link_next cycle.

Edge rows survive intact: a dormant local account (site_admin false, no
SSO identity marker) and machine accounts are surfaced, never filtered —
flagging them is reconciliation's job, not collection's.

The source is STATE-only (registry temporal.kind "state-only"): the
contract supports no TIMING assertion by itself; pair with an
event-history source (E204 lane). Determinism per D-P3: no clocks — the
period and org are explicit inputs, and the capture time travels inside
each page envelope.
"""

import hashlib
from collections.abc import Callable
from json import loads

from pydantic import Field

from aegis_sentinel.collectors.hris import PaginationEvidence, canonical_contract_hash
from aegis_sentinel.schema.enums import AssertionType
from aegis_sentinel.schema.models import (
    SHA256,
    Base,
    EvidenceQualityContract,
    TimeWindow,
)

SOURCE_SYSTEM = "github"
CAPABILITY_ID = "github.members"
API_VERSION = "2022-11-28"
COLLECTOR_VERSION = "0.1.0"


class MemberRecord(Base):
    """One org-member row, typed with the registry-yielded attributes
    plus the SSO identity marker. Edge rows survive intact: a machine
    account keeps its type, and a dormant local account (site_admin
    false, sso_identity None) is surfaced, not filtered — flagging it is
    reconciliation's job, not collection's."""

    login: str = Field(min_length=1)
    id: int = Field(ge=1)
    type: str = Field(min_length=1)
    site_admin: bool
    sso_identity: str | None = None


class MemberPage(Base):
    """One raw page envelope, closed-schema parsed. link_next simulates
    the Link rel=next header: present means more pages follow, absent
    means the chain is exhausted (registry github.members pagination)."""

    org: str = Field(min_length=1)
    endpoint: str = Field(min_length=1)
    api_version: str = Field(min_length=1)
    captured_at: str = Field(min_length=1)
    page: int = Field(ge=1)
    per_page: int = Field(ge=1)
    link_next: str | None = None
    rows: tuple[MemberRecord, ...]


class GithubMembersCollection(Base):
    records: tuple[MemberRecord, ...]
    raw_sha256: str = Field(pattern=SHA256)
    page_sha256s: tuple[str, ...] = Field(min_length=1)
    pagination: PaginationEvidence
    contract: EvidenceQualityContract


def _build_contract(
    *, org: str, period: TimeWindow, population_ref: str, collector_version: str
) -> EvidenceQualityContract:
    contract = EvidenceQualityContract.model_validate(
        {
            "id": f"eqc-{SOURCE_SYSTEM}-members-v1",
            "source": SOURCE_SYSTEM,
            "tenant": org,
            "population_ref": population_ref,
            "endpoint": f"REST v3 GET /orgs/{org}/members",
            "parameters": {"capability": CAPABILITY_ID, "format": "json"},
            "time_window": {
                "start": period.start.isoformat(),
                "end": period.end.isoformat(),
            },
            "schema_version": API_VERSION,
            "collector_version": collector_version,
            "auth_context": "read:org (GitHub App: Organization members, read-only)",
            "contract_hash": "0" * 64,  # placeholder; replaced by the canonical self-hash
            "quality": {
                "provenance": {
                    "method": "org identity asserted in every page envelope and matched "
                    "against the engagement org per page",
                    "failure_mode": "page served from an unauthenticated or wrong-org origin",
                },
                "integrity": {
                    "method": "SHA-256 of each raw page payload recorded at intake plus a "
                    "chain hash over the pages in fetch order, WORM-stored",
                    "failure_mode": "hash mismatch against a stored raw page payload",
                },
                "population": {
                    "method": "page pagination; Link rel=next followed until absent with "
                    "page count recorded; every mid-chain page asserted to carry exactly "
                    "its claimed per_page rows and page numbers asserted contiguous",
                    "failure_mode": "truncated or skipped page — partial member population",
                },
                "semantics": {
                    "method": "closed-schema parse of every row into typed MemberRecord "
                    "fields; unknown fields rejected",
                    "failure_mode": "API schema drift or field meaning change",
                },
                "temporal_validity": {
                    "method": "state-only snapshot (registry github.members): capture time "
                    "recorded in every page envelope and compared against the asserted "
                    "period; supports no TIMING assertion by itself",
                    "failure_mode": "snapshot captured outside the asserted window, or the "
                    "current-state list mistaken for membership history",
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


def collect_github_members(
    transport: Callable[[str], bytes],
    *,
    org: str,
    period: TimeWindow,
    population_ref: str,
    first_page: str = "page_1",
    collector_version: str = COLLECTOR_VERSION,
) -> GithubMembersCollection:
    """Collect the org-member population through the injected transport.

    Follows the link_next chain from ``first_page`` until absent (the
    Link rel=next exhaustion method of registry entry github.members),
    recording the page count. Raises on anything that would silently
    weaken the population claim: a wrong-org page (provenance), a
    mid-chain page with fewer rows than its own per_page claim
    (truncation), a page-number sequence break, or a link_next cycle.
    """
    records: list[MemberRecord] = []
    page_shas: list[str] = []
    chain = hashlib.sha256()
    visited: set[str] = set()
    key: str | None = first_page
    expected_page = 1

    while key is not None:
        if key in visited:
            raise ValueError(f"link_next cycle: page key {key!r} already fetched (population)")
        visited.add(key)

        raw = transport(key)
        if not isinstance(raw, bytes):
            raise TypeError("transport must return the raw page payload as bytes")
        page_shas.append(hashlib.sha256(raw).hexdigest())
        chain.update(raw)

        page = MemberPage.model_validate(loads(raw.decode("utf-8")))
        if page.org != org:
            raise ValueError(f"page org {page.org!r} != engagement org {org!r} (provenance)")
        if page.page != expected_page:
            raise ValueError(
                f"page sequence break: got page {page.page}, expected {expected_page} (population)"
            )
        if page.link_next is not None and len(page.rows) != page.per_page:
            raise ValueError(
                f"page {page.page} claims per_page={page.per_page} but returned "
                f"{len(page.rows)} rows mid-chain — truncated page (population)"
            )
        records.extend(page.rows)
        key = page.link_next
        expected_page += 1

    pages_fetched = len(page_shas)
    pagination = PaginationEvidence(
        method="page",
        pages_fetched=pages_fetched,
        exhausted=True,
        exhaustion_method=(
            f"Link rel=next (link_next) followed until absent; {pages_fetched} pages "
            f"fetched, {len(records)} rows, page numbers contiguous 1..{pages_fetched}"
        ),
    )
    contract = _build_contract(
        org=org,
        period=period,
        population_ref=population_ref,
        collector_version=collector_version,
    )
    return GithubMembersCollection(
        records=tuple(records),
        raw_sha256=chain.hexdigest(),
        page_sha256s=tuple(page_shas),
        pagination=pagination,
        contract=contract,
    )
