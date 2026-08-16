"""COL05 — deterministic Slack SCIM workspace-user collector.

The transport is an injected callable taking a 1-based startIndex and
returning that page's raw payload bytes, so the collector logic performs
no I/O of its own: fixture bytes in tests, a real SCIM client later,
identical code path either way (no live-tenant calls in tests — HANDOFF
§4 COL01–05). Every page's raw bytes are SHA-256 hashed at intake (plus
a combined hash over the pages in fetch order), rows are parsed into
typed records, and an EvidenceQualityContract is emitted with all five
quality property methods named.

Pagination follows the slack.scim_users capability entry
(startIndex/count against totalResults): pages are fetched from
startIndex 1, advancing by each page's itemsPerPage, until
startIndex + count exceeds totalResults; every startIndex visited is
recorded as exhaustion evidence. That capability entry is DRAFT — its
parameters are recall-sourced pending doc verification — so this
collector runs against fixtures only and the EQC provenance method
names the draft status explicitly.

Edge rows are surfaced, never filtered: a LOCAL non-SSO account (no
SAML identity marker in the payload) keeps its rows with
local_account=True, and a deactivated user keeps its row with
active=False — flagging is collection's job, judgment is downstream.

Determinism per D-P3: no clocks — the period and workspace are explicit
inputs, and page contents alone determine the output.
"""

import hashlib
import json
from collections.abc import Callable

from pydantic import Field

from aegis_sentinel.collectors.hris import canonical_contract_hash
from aegis_sentinel.schema.enums import AssertionType
from aegis_sentinel.schema.models import (
    SHA256,
    Base,
    EvidenceQualityContract,
    TimeWindow,
)

SOURCE_SYSTEM = "slack"
COLLECTOR_VERSION = "0.1.0"
LIST_RESPONSE_URN = "urn:ietf:params:scim:api:messages:2.0:ListResponse"


class ScimEmail(Base):
    value: str = Field(min_length=1)
    primary: bool = False


class ScimUser(Base):
    """One SCIM user resource, closed-schema parsed. The samlIdentity
    marker is the fixture's SSO-linkage assertion: absent means a LOCAL
    non-SSO account (the field's real-world placement is part of what
    doc verification of the DRAFT capability entry must settle)."""

    id: str = Field(min_length=1)
    user_name: str = Field(alias="userName", min_length=1)
    emails: tuple[ScimEmail, ...] = ()
    active: bool
    saml_identity: str | None = Field(alias="samlIdentity", default=None)


class ScimPage(Base):
    """One SCIM ListResponse page envelope. The workspace field is the
    extract's origin assertion, matched against the engagement workspace
    per page (provenance)."""

    schemas: tuple[str, ...] = Field(min_length=1)
    workspace: str = Field(min_length=1)
    total_results: int = Field(alias="totalResults", ge=0)
    start_index: int = Field(alias="startIndex", ge=1)
    items_per_page: int = Field(alias="itemsPerPage", ge=0)
    resources: tuple[ScimUser, ...] = Field(alias="Resources", default=())


class WorkspaceUserRecord(Base):
    """One workspace user, typed, with edge conditions surfaced as
    flags: local_account=True marks a non-SSO account (no SAML identity
    marker), active=False marks a deactivated user. Neither is filtered
    — downstream reconciliation judges, collection only reports."""

    id: str = Field(min_length=1)
    user_name: str = Field(min_length=1)
    email: str | None = None
    active: bool
    local_account: bool


class PaginationEvidence(Base):
    """Exhaustion evidence per the capability entry's method: every
    startIndex visited is recorded, and the walk ends only once
    startIndex + count passes totalResults."""

    method: str = Field(min_length=1)
    pages_fetched: int = Field(ge=1)
    start_indices: tuple[int, ...] = Field(min_length=1)
    exhausted: bool
    exhaustion_method: str = Field(min_length=1)


class SlackScimCollection(Base):
    records: tuple[WorkspaceUserRecord, ...]
    raw_sha256: str = Field(pattern=SHA256)
    page_sha256: tuple[str, ...] = Field(min_length=1)
    pagination: PaginationEvidence
    contract: EvidenceQualityContract


def _primary_email(user: ScimUser) -> str | None:
    for email in user.emails:
        if email.primary:
            return email.value
    return user.emails[0].value if user.emails else None


def _parse_page(raw: bytes, *, workspace: str, start_index: int) -> ScimPage:
    page = ScimPage.model_validate(json.loads(raw.decode("utf-8")))
    if LIST_RESPONSE_URN not in page.schemas:
        raise ValueError(
            f"page at startIndex {start_index} is not a SCIM ListResponse "
            f"({LIST_RESPONSE_URN} missing from schemas) (semantics)"
        )
    if page.workspace != workspace:
        raise ValueError(
            f"page workspace {page.workspace!r} != engagement workspace {workspace!r} (provenance)"
        )
    if page.start_index != start_index:
        raise ValueError(
            f"page asserts startIndex {page.start_index}, requested {start_index} (population)"
        )
    if len(page.resources) != page.items_per_page:
        raise ValueError(
            f"page at startIndex {start_index} delivered {len(page.resources)} "
            f"resources but asserts itemsPerPage={page.items_per_page} (population)"
        )
    return page


def _build_contract(
    *,
    workspace: str,
    period: TimeWindow,
    population_ref: str,
    collector_version: str,
) -> EvidenceQualityContract:
    contract = EvidenceQualityContract.model_validate(
        {
            "id": "eqc-slack-scim-users-v1",
            "source": SOURCE_SYSTEM,
            "tenant": workspace,
            "population_ref": population_ref,
            "endpoint": "SCIM v2 GET /scim/v2/Users",
            "parameters": {
                "pagination": "startIndex/count",
                "attributes": "id,userName,emails,active",
            },
            "time_window": {
                "start": period.start.isoformat(),
                "end": period.end.isoformat(),
            },
            "schema_version": LIST_RESPONSE_URN,
            "collector_version": collector_version,
            "auth_context": "admin-scoped OAuth token (SCIM requires Business+/Enterprise Grid)",
            "contract_hash": "0" * 64,  # placeholder; replaced by the canonical self-hash
            "quality": {
                "provenance": {
                    "method": "workspace identity asserted in every page envelope and "
                    "matched against the engagement workspace; capability entry "
                    "slack.scim_users is DRAFT (recall-sourced, pending doc "
                    "verification), so collection runs against fixtures only",
                    "failure_mode": "page from an unauthenticated or wrong-workspace origin, "
                    "or the draft capability entry proving wrong once doc-verified",
                },
                "integrity": {
                    "method": "SHA-256 of each raw page payload recorded at intake, plus a "
                    "combined hash over the pages in fetch order, WORM-stored",
                    "failure_mode": "hash mismatch against a stored raw page payload",
                },
                "population": {
                    "method": "startIndex/count walk until startIndex + count exceeds "
                    "totalResults, indices recorded; collected row total asserted "
                    "equal to totalResults",
                    "failure_mode": "truncated walk or totalResults mismatch — partial "
                    "workspace-user population",
                },
                "semantics": {
                    "method": "closed-schema parse of every resource into typed "
                    "WorkspaceUserRecord fields; unknown fields rejected; local "
                    "non-SSO and inactive accounts flagged, never filtered",
                    "failure_mode": "SCIM schema drift or field meaning change",
                },
                "temporal_validity": {
                    "method": "state-only snapshot (per the capability entry's temporal "
                    "kind): membership state as of the collection run, asserted "
                    "against the engagement period; no event timeline claimed",
                    "failure_mode": "snapshot consumed as if it evidenced events or "
                    "timing inside the window",
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


def collect_slack_scim_users(
    transport: Callable[[int], bytes],
    *,
    workspace: str,
    period: TimeWindow,
    population_ref: str,
    collector_version: str = COLLECTOR_VERSION,
) -> SlackScimCollection:
    """Collect all workspace users through the injected page transport.

    Raises on anything that would silently weaken the population claim:
    a wrong-workspace page (provenance), pages whose users sum to fewer
    than totalResults claims (population), a page that stalls the walk,
    or totalResults drifting between pages of one collection run.
    """
    pages: list[ScimPage] = []
    page_hashes: list[str] = []
    combined = hashlib.sha256()
    start_index = 1
    total_results: int | None = None

    while total_results is None or start_index <= total_results:
        raw = transport(start_index)
        if not isinstance(raw, bytes):
            raise TypeError("transport must return the raw page payload as bytes")
        page_hashes.append(hashlib.sha256(raw).hexdigest())
        combined.update(raw)

        page = _parse_page(raw, workspace=workspace, start_index=start_index)
        if total_results is None:
            total_results = page.total_results
        elif page.total_results != total_results:
            raise ValueError(
                f"totalResults drifted mid-walk: {page.total_results} at startIndex "
                f"{start_index} != {total_results} on the first page (population)"
            )
        pages.append(page)

        if page.items_per_page == 0 and start_index <= total_results:
            collected = sum(len(p.resources) for p in pages)
            raise ValueError(
                f"totalResults mismatch: pages exhausted at startIndex {start_index} "
                f"with {collected} users collected but totalResults claims "
                f"{total_results} (population)"
            )
        start_index += page.items_per_page

    users = [user for page in pages for user in page.resources]
    if len(users) != total_results:
        raise ValueError(
            f"totalResults mismatch: {len(users)} users collected != totalResults "
            f"{total_results} (population)"
        )

    records = tuple(
        WorkspaceUserRecord(
            id=user.id,
            user_name=user.user_name,
            email=_primary_email(user),
            active=user.active,
            local_account=user.saml_identity is None,
        )
        for user in users
    )
    start_indices = tuple(p.start_index for p in pages)
    pagination = PaginationEvidence(
        method="startIndex/count",
        pages_fetched=len(pages),
        start_indices=start_indices,
        exhausted=True,
        exhaustion_method=(
            f"startIndex walk {list(start_indices)} advanced by itemsPerPage until "
            f"startIndex + count exceeded totalResults={total_results}; "
            f"{len(users)} users asserted against totalResults={total_results}"
        ),
    )
    contract = _build_contract(
        workspace=workspace,
        period=period,
        population_ref=population_ref,
        collector_version=collector_version,
    )
    return SlackScimCollection(
        records=records,
        raw_sha256=combined.hexdigest(),
        page_sha256=tuple(page_hashes),
        pagination=pagination,
        contract=contract,
    )
