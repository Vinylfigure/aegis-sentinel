"""Jira per-issue changelog collector — Lane B slice of Deliverable 4
(issue #144), collection half of #122's Jira change-approval lane. This
is the source a future evaluator uses to determine approval-before-
deployment ordering (issue #122 Lane B's core claim) — collection only,
no ordering logic here.

The transport is an injected callable taking a requested startAt offset
and returning the raw page bytes (or None when no page exists at that
offset), so the collector logic performs no I/O of its own: fixture
bytes in tests, a real extract later, identical code path either way.
Pagination follows the registry entry jira.issue_changelog: page-based,
startAt/maxResults advanced by the page's own row count until isLast is
true. Every page's raw bytes are SHA-256 hashed at intake (a chain hash
covers the whole fetch in order, mirroring github_members.py's
page_sha256s shape since this is also page-based pagination), and
change-history entries are parsed into closed typed records.

Refusal, never a silent partial population: a wrong-account-token or
wrong-issue page (provenance), a page answering an offset other than
the one requested (integrity), or a non-terminal page claiming
maxResults but delivering fewer rows — truncation (population). startAt
is advanced from our own running row count rather than trusted from the
source, so — unlike the cursor-based collectors — there is no
server-suppliable pointer that could cycle the chain. Jira's changelog
is a full-history source (registry temporal.kind "full-history"): the
contract supports TIMING assertions, unlike the state-only issue
search. An author-less history entry survives collection intact —
identity resolution is the reconciler's job, and a fuzzy identity ends
UNKNOWN_POPULATION per D-7/D-U1, never a silently dropped row.
"""

import hashlib
import json
from collections.abc import Callable
from datetime import datetime

from pydantic import Field

from aegis_sentinel.collectors.hris import PaginationEvidence, canonical_contract_hash
from aegis_sentinel.schema.enums import AssertionType
from aegis_sentinel.schema.models import (
    SHA256,
    Base,
    EvidenceQualityContract,
    TimeWindow,
)

SOURCE_SYSTEM = "jira"
CAPABILITY_ID = "jira.issue_changelog"
COLLECTOR_VERSION = "0.1.0"


class ChangelogItem(Base):
    """One field change within a history entry (registry
    jira.issue_changelog attributes items.field/items.fromString/
    items.toString). from_string/to_string may be null (a field
    transitioning to or from an unset value) and survive intact."""

    field: str = Field(min_length=1)
    from_string: str | None = None
    to_string: str | None = None


class ChangelogEntry(Base):
    """One history record, typed with the registry-yielded attributes
    plus the join key (registry jira.issue_changelog join_keys:
    issue_key). A null author_email survives collection intact — a
    fuzzy identity is the reconciler's job (UNKNOWN_POPULATION per
    D-7/D-U1), never a row silently dropped at collection."""

    issue_key: str = Field(min_length=1)
    created: datetime
    author_email: str | None = None
    items: tuple[ChangelogItem, ...] = Field(min_length=1)


class ChangelogPage(Base):
    """One raw page envelope, closed-schema parsed. account_token and
    issue_key are the tenant/issue identity asserted per page, not just
    once, so a wrong-tenant or wrong-issue page mid-chain is caught."""

    account_token: str = Field(min_length=1)
    issue_key: str = Field(min_length=1)
    captured_at: datetime
    start_at: int = Field(ge=0)
    max_results: int = Field(ge=1)
    is_last: bool
    values: tuple[ChangelogEntry, ...]


class JiraChangelogCollection(Base):
    records: tuple[ChangelogEntry, ...]
    raw_sha256: str = Field(pattern=SHA256)
    page_sha256s: tuple[str, ...] = Field(min_length=1)
    pagination: PaginationEvidence
    contract: EvidenceQualityContract


def _build_contract(
    *,
    account_token: str,
    period: TimeWindow,
    population_ref: str,
    collector_version: str,
) -> EvidenceQualityContract:
    contract = EvidenceQualityContract.model_validate(
        {
            "id": f"eqc-{SOURCE_SYSTEM}-issue-changelog-v1",
            "source": SOURCE_SYSTEM,
            "tenant": account_token,
            "population_ref": population_ref,
            "endpoint": "Jira Cloud REST API v3 GET /rest/api/3/issue/{issueIdOrKey}/changelog",
            "parameters": {"capability": CAPABILITY_ID, "pagination": "page (startAt/maxResults)"},
            "time_window": {
                "start": period.start.isoformat(),
                "end": period.end.isoformat(),
            },
            "schema_version": "jira.issue_changelog/v1",
            "collector_version": collector_version,
            "auth_context": "read:jira-work (classic) or read:issue.changelog:jira (granular)",
            "contract_hash": "0" * 64,  # placeholder; replaced by the canonical self-hash
            "quality": {
                "provenance": {
                    "method": "account_token tenant identity and issue_key asserted in "
                    "every page envelope and matched against the engagement account "
                    "token and requested issue per page",
                    "failure_mode": "page from an unauthenticated, wrong-tenant, or "
                    "wrong-issue origin",
                },
                "integrity": {
                    "method": "SHA-256 of each raw page recorded at intake plus a chain "
                    "hash over the pages in fetch order, WORM-stored",
                    "failure_mode": "hash mismatch against a stored raw page",
                },
                "population": {
                    "method": "page pagination; startAt advanced by the page's own row "
                    "count until isLast is true; a startAt that repeats or fails to "
                    "advance, or a non-terminal page delivering fewer rows than its own "
                    "maxResults claim, refuses the collection",
                    "failure_mode": "broken, cyclic, or truncated startAt chain — partial "
                    "change-history population",
                },
                "semantics": {
                    "method": "closed-schema parse of every history entry into typed "
                    "ChangelogEntry fields; unknown fields rejected",
                    "failure_mode": "Jira Cloud REST API schema drift or field meaning change",
                },
                "temporal_validity": {
                    "method": "full-history source (registry jira.issue_changelog): "
                    "every entry carries its own created timestamp, checked against the "
                    "asserted period",
                    "failure_mode": "changelog history truncated short of the asserted "
                    "period start",
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


def collect_jira_changelog(
    transport: Callable[[int], bytes | None],
    *,
    account_token: str,
    issue_key: str,
    period: TimeWindow,
    collector_version: str = COLLECTOR_VERSION,
) -> JiraChangelogCollection:
    """Collect one issue's field-change history through the injected
    page transport (called with the requested startAt offset, starting
    at 0; returns raw bytes, or None when no page exists at that
    offset).

    Raises on anything that would silently weaken the population or
    provenance claim: a wrong-account-token or wrong-issue page
    (provenance), a page answering an offset other than the one
    requested (integrity), or a non-terminal page delivering fewer rows
    than its own maxResults claim (truncation): a partial change-history
    population is refused, never returned. startAt is advanced from our
    own running count of rows fetched, never from a source-declared
    pointer, so — unlike the cursor-based collectors — there is no
    server-suppliable value that could cycle the chain.
    """
    population_ref = f"pop-jira-issue-changelog-{issue_key}"
    records: list[ChangelogEntry] = []
    page_shas: list[str] = []
    chain = hashlib.sha256()
    start_at = 0

    while True:
        raw = transport(start_at)
        if raw is None:
            raise ValueError(
                f"startAt chain broken at offset {start_at}: the source returned no "
                "page — refusing partial change-history population (population)"
            )
        if not isinstance(raw, bytes):
            raise TypeError("transport must return the raw page payload as bytes (or None)")
        page_shas.append(hashlib.sha256(raw).hexdigest())
        chain.update(raw)

        page = ChangelogPage.model_validate(json.loads(raw.decode("utf-8")))
        if page.account_token != account_token:
            raise ValueError(
                f"page account_token {page.account_token!r} != engagement account_token "
                f"{account_token!r} (provenance)"
            )
        if page.issue_key != issue_key:
            raise ValueError(
                f"page issue_key {page.issue_key!r} != requested issue_key {issue_key!r} "
                "(provenance)"
            )
        if page.start_at != start_at:
            raise ValueError(
                f"page answers startAt {page.start_at} but {start_at} was requested (integrity)"
            )
        if not page.is_last and len(page.values) != page.max_results:
            raise ValueError(
                f"page at startAt={start_at} claims maxResults={page.max_results} but "
                f"returned {len(page.values)} rows mid-chain — truncated page (population)"
            )
        records.extend(page.values)
        if page.is_last:
            break
        start_at += len(page.values)

    pages_fetched = len(page_shas)
    pagination = PaginationEvidence(
        method="page",
        pages_fetched=pages_fetched,
        exhausted=True,
        exhaustion_method=(
            f"startAt/maxResults followed until isLast; {pages_fetched} page(s) "
            f"fetched, {len(records)} history entries"
        ),
    )
    contract = _build_contract(
        account_token=account_token,
        period=period,
        population_ref=population_ref,
        collector_version=collector_version,
    )
    return JiraChangelogCollection(
        records=tuple(records),
        raw_sha256=chain.hexdigest(),
        page_sha256s=tuple(page_shas),
        pagination=pagination,
        contract=contract,
    )
