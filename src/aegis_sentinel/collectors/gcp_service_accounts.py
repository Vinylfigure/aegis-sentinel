"""COL04 — deterministic GCP service-account collector.

The transport is an injected callable taking a page token (None for the
first page) and returning that page's raw payload bytes, so the
collector logic performs no I/O of its own: fixture pages in tests, the
IAM REST v1 list endpoint later, identical code path either way (no
live-tenant calls in tests — HANDOFF §4 COL01–05). Pagination follows
the gcp.service_accounts capability entry: page method, exhaustion =
follow nextPageToken until absent, token chain recorded as evidence.

Integrity: each raw page is SHA-256 hashed at intake, and the
collection-level raw_sha256 is the SHA-256 over the newline-joined
per-page hex digests in fetch order — a deterministic chain that pins
both page contents and page order.

Edge rows are surfaced, never filtered: break-glass principals
(breakglass-*) and disabled accounts pass through with their disabled
flag captured — deciding what a disabled or break-glass account *means*
is evaluation's job, not collection's.

Refusals (anything that would silently weaken the claim): an account
under a different project (provenance), a nextPageToken the transport
cannot serve — the chain points nowhere (population), and a token chain
that cycles (population).

Determinism per D-P3: no clocks — the period and project are explicit
inputs. STATE-only surface: disabled-at timing needs audit-log pairing
(E204 lane), so EVENT/TIMING assertions are deliberately unsupported.
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

SOURCE_SYSTEM = "gcp"
COLLECTOR_VERSION = "0.1.0"
SCHEMA_VERSION = "v1"  # IAM REST doc_version per the capability entry


class ServiceAccountRecord(Base):
    """One service account row, typed (registry attributes: name, email,
    uniqueId, disabled). Break-glass and disabled accounts survive
    intact — the disabled flag is captured, never used to filter."""

    name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    unique_id: str = Field(alias="uniqueId", min_length=1)
    # proto3 omits false booleans, so absence means enabled.
    disabled: bool = False


class ServiceAccountPage(Base):
    """One raw list-response page, closed-schema parsed."""

    accounts: tuple[ServiceAccountRecord, ...] = ()
    next_page_token: str | None = Field(default=None, alias="nextPageToken", min_length=1)


class TokenPaginationEvidence(Base):
    """Exhaustion evidence for token pagination: the chain itself is
    recorded, not just a page count — population completeness is claimed
    by showing every token was followed until nextPageToken was absent."""

    method: str = Field(min_length=1)
    pages_fetched: int = Field(ge=1)
    token_chain: tuple[str, ...]
    exhausted: bool
    exhaustion_method: str = Field(min_length=1)


class GcpServiceAccountCollection(Base):
    records: tuple[ServiceAccountRecord, ...]
    page_sha256s: tuple[str, ...] = Field(min_length=1)
    raw_sha256: str = Field(pattern=SHA256)
    pagination: TokenPaginationEvidence
    contract: EvidenceQualityContract


def chain_hash(page_sha256s: tuple[str, ...]) -> str:
    """Collection-level raw hash: SHA-256 over the newline-joined
    per-page hex digests in fetch order (content and order both pinned)."""
    return hashlib.sha256("\n".join(page_sha256s).encode("ascii")).hexdigest()


def _build_contract(
    *, project: str, period: TimeWindow, population_ref: str, collector_version: str
) -> EvidenceQualityContract:
    contract = EvidenceQualityContract.model_validate(
        {
            "id": f"eqc-{SOURCE_SYSTEM}-service-accounts-v1",
            "source": SOURCE_SYSTEM,
            "tenant": project,
            "population_ref": population_ref,
            "endpoint": "IAM REST v1 GET /v1/projects/{project}/serviceAccounts",
            "parameters": {"name": f"projects/{project}"},
            "time_window": {
                "start": period.start.isoformat(),
                "end": period.end.isoformat(),
            },
            "schema_version": SCHEMA_VERSION,
            "collector_version": collector_version,
            "auth_context": (
                "least-privilege roles/iam.serviceAccountViewer (iam.serviceAccounts.list only)"
            ),
            "contract_hash": "0" * 64,  # placeholder; replaced by the canonical self-hash
            "quality": {
                "provenance": {
                    "method": "every account name asserted under "
                    "projects/{project}/serviceAccounts/ for the engagement project; "
                    "any foreign-project row refuses the whole collection",
                    "failure_mode": "listing served for a different or wrong project",
                },
                "integrity": {
                    "method": "SHA-256 of each raw page recorded at intake plus a "
                    "collection hash chaining the per-page digests in order, WORM-stored",
                    "failure_mode": "hash mismatch against a stored raw page, or "
                    "reordered/substituted pages",
                },
                "population": {
                    "method": "pageToken chain followed until nextPageToken absent; "
                    "token chain and page count recorded; an unservable or cycling "
                    "token refuses the collection",
                    "failure_mode": "broken token chain — partial service-account "
                    "population presented as complete",
                },
                "semantics": {
                    "method": "closed-schema parse of every account into typed "
                    "ServiceAccountRecord fields (name, email, uniqueId, disabled); "
                    "unknown fields rejected",
                    "failure_mode": "IAM API schema drift or field meaning change",
                },
                "temporal_validity": {
                    "method": "STATE-only snapshot tied to the asserted collection "
                    "window; disabled-at timing deliberately unclaimed (needs "
                    "audit-log pairing, E204 lane)",
                    "failure_mode": "state snapshot misread as history — disabled/"
                    "created timing inferred from a point-in-time listing",
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


def collect_gcp_service_accounts(
    transport: Callable[[str | None], bytes],
    *,
    project: str,
    period: TimeWindow,
    population_ref: str,
    collector_version: str = COLLECTOR_VERSION,
) -> GcpServiceAccountCollection:
    """Collect all service-account pages through the injected transport.

    The transport is called with None for the first page, then with each
    nextPageToken in turn; it must return raw page bytes, and must raise
    LookupError for a token it cannot serve. Raises on anything that
    would silently weaken the claim: a foreign-project account row
    (provenance), a token that points nowhere, or a cycling token chain
    (population). No partial pass: any refusal discards the collection.
    """
    records: list[ServiceAccountRecord] = []
    page_sha256s: list[str] = []
    token_chain: list[str] = []
    expected_prefix = f"projects/{project}/serviceAccounts/"

    token: str | None = None
    while True:
        try:
            raw = transport(token)
        except LookupError as exc:
            raise ValueError(
                f"token chain broken: pageToken {token!r} points nowhere — "
                "unreachable page, partial service-account population (population)"
            ) from exc
        if not isinstance(raw, bytes):
            raise TypeError("transport must return the raw page payload as bytes")
        page_sha256s.append(hashlib.sha256(raw).hexdigest())

        page = ServiceAccountPage.model_validate(json.loads(raw.decode("utf-8")))
        for account in page.accounts:
            if not account.name.startswith(expected_prefix):
                raise ValueError(
                    f"service account {account.name!r} is not under engagement "
                    f"project {project!r} (provenance)"
                )
        records.extend(page.accounts)

        next_token = page.next_page_token
        if next_token is None:
            break
        if next_token in token_chain:
            raise ValueError(
                f"token chain cycle: nextPageToken {next_token!r} already followed (population)"
            )
        token_chain.append(next_token)
        token = next_token

    chain = tuple(token_chain)
    pagination = TokenPaginationEvidence(
        method="page",
        pages_fetched=len(page_sha256s),
        token_chain=chain,
        exhausted=True,
        exhaustion_method=(
            f"followed pageToken chain until nextPageToken absent: "
            f"{len(page_sha256s)} pages, {len(records)} accounts, "
            f"token chain {' -> '.join(chain) if chain else '(single page)'}"
        ),
    )
    contract = _build_contract(
        project=project,
        period=period,
        population_ref=population_ref,
        collector_version=collector_version,
    )
    return GcpServiceAccountCollection(
        records=tuple(records),
        page_sha256s=tuple(page_sha256s),
        raw_sha256=chain_hash(tuple(page_sha256s)),
        pagination=pagination,
        contract=contract,
    )
