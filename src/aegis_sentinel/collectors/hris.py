"""COL01 — deterministic HRIS termination-feed collector.

The transport is an injected callable returning the raw payload bytes, so
the collector logic performs no I/O of its own: fixture bytes in tests,
a real extract later, identical code path either way (no live-tenant
calls in tests — HANDOFF §4 COL01–05). The raw payload is SHA-256 hashed
at intake, the rows are parsed into typed records, and an
EvidenceQualityContract is emitted with all five quality property
methods named. Pagination exhaustion is recorded as evidence even for
the single-page RaaS extract (the workday.terminated_workers capability
entry's exhaustion method: row count asserted against report metadata).

Determinism per D-P3: no clocks — the period and tenant are explicit
inputs, and the extract time travels inside the payload itself.
"""

import hashlib
import json
from collections.abc import Callable
from datetime import date

from pydantic import Field

from aegis_sentinel.schema.enums import AssertionType
from aegis_sentinel.schema.models import (
    SHA256,
    Base,
    EvidenceQualityContract,
    TimeWindow,
)

SOURCE_SYSTEM = "workday"
COLLECTOR_VERSION = "0.1.0"


class TerminationRecord(Base):
    """One termination event row, typed. Edge rows survive intact: a
    missing email stays None (the reconciler buckets it UNRESOLVABLE),
    contractors keep their worker_type, and duplicate rehire rows are
    kept — deduplication is reconciliation's job, not collection's."""

    worker_id: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    email: str | None = None
    worker_type: str = Field(min_length=1)
    termination_date: date


class ReportMetadata(Base):
    row_count: int = Field(ge=0)
    page: int = Field(ge=1)
    total_pages: int = Field(ge=1)


class HrisFeed(Base):
    """The raw extract envelope, closed-schema parsed."""

    report: str = Field(min_length=1)
    report_version: str = Field(min_length=1)
    tenant: str = Field(min_length=1)
    generated_at: str = Field(min_length=1)
    report_metadata: ReportMetadata
    rows: tuple[TerminationRecord, ...]


class PaginationEvidence(Base):
    """Exhaustion is recorded even when the feed is single-page: absence
    of pagination is itself a population-completeness claim and must be
    evidenced, not assumed."""

    method: str = Field(min_length=1)
    pages_fetched: int = Field(ge=1)
    exhausted: bool
    exhaustion_method: str = Field(min_length=1)


class HrisCollection(Base):
    records: tuple[TerminationRecord, ...]
    raw_sha256: str = Field(pattern=SHA256)
    pagination: PaginationEvidence
    contract: EvidenceQualityContract


def _sha256_canonical_json(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def canonical_contract_hash(contract: EvidenceQualityContract) -> str:
    """D-P3 canonical hash: SHA-256 over the contract's canonical JSON
    with its one volatile field (contract_hash itself) nulled."""
    data = contract.model_dump(mode="json")
    data["contract_hash"] = None
    return _sha256_canonical_json(data)


def _build_contract(
    feed: HrisFeed, *, tenant: str, period: TimeWindow, population_ref: str, collector_version: str
) -> EvidenceQualityContract:
    contract = EvidenceQualityContract.model_validate(
        {
            "id": f"eqc-{SOURCE_SYSTEM}-terminations-v1",
            "source": SOURCE_SYSTEM,
            "tenant": tenant,
            "population_ref": population_ref,
            "endpoint": f"RaaS {feed.report} report extract",
            "parameters": {"report": feed.report, "format": "json"},
            "time_window": {
                "start": period.start.isoformat(),
                "end": period.end.isoformat(),
            },
            "schema_version": feed.report_version,
            "collector_version": collector_version,
            "auth_context": "ISU account scoped to the terminations report only",
            "contract_hash": "0" * 64,  # placeholder; replaced by the canonical self-hash
            "quality": {
                "provenance": {
                    "method": "tenant identity asserted in the extract envelope and "
                    "matched against the engagement tenant per collection",
                    "failure_mode": "extract from an unauthenticated or wrong-tenant origin",
                },
                "integrity": {
                    "method": "SHA-256 of the raw payload recorded at intake, WORM-stored",
                    "failure_mode": "hash mismatch against the stored raw payload",
                },
                "population": {
                    "method": "single report extract; row count asserted against "
                    "report metadata row_count and page/total_pages",
                    "failure_mode": "truncated extract — partial termination population",
                },
                "semantics": {
                    "method": "closed-schema parse of every row into typed "
                    "TerminationRecord fields; unknown fields rejected",
                    "failure_mode": "report schema drift or field meaning change",
                },
                "temporal_validity": {
                    "method": "extract generation time recorded in the envelope and "
                    "compared against the asserted period",
                    "failure_mode": "extract generated outside the asserted window",
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


def collect_hris_terminations(
    transport: Callable[[], bytes],
    *,
    tenant: str,
    period: TimeWindow,
    population_ref: str,
    collector_version: str = COLLECTOR_VERSION,
) -> HrisCollection:
    """Collect the termination feed through the injected transport.

    Raises on anything that would silently weaken the population claim:
    a wrong-tenant extract (provenance), a row count that contradicts the
    report metadata, or unexhausted pagination (population).
    """
    raw = transport()
    if not isinstance(raw, bytes):
        raise TypeError("transport must return the raw payload as bytes")
    raw_sha256 = hashlib.sha256(raw).hexdigest()

    feed = HrisFeed.model_validate(json.loads(raw.decode("utf-8")))
    if feed.tenant != tenant:
        raise ValueError(
            f"extract tenant {feed.tenant!r} != engagement tenant {tenant!r} (provenance)"
        )
    meta = feed.report_metadata
    if meta.page != meta.total_pages:
        raise ValueError(
            f"pagination not exhausted: page {meta.page} of {meta.total_pages} (population)"
        )
    if len(feed.rows) != meta.row_count:
        raise ValueError(
            f"{len(feed.rows)} rows != report metadata row_count {meta.row_count} — "
            "truncated extract (population)"
        )

    pagination = PaginationEvidence(
        method="none",
        pages_fetched=1,
        exhausted=True,
        exhaustion_method=(
            f"single report extract; {len(feed.rows)} rows asserted against report "
            f"metadata row_count={meta.row_count}, page {meta.page}/{meta.total_pages}"
        ),
    )
    contract = _build_contract(
        feed,
        tenant=tenant,
        period=period,
        population_ref=population_ref,
        collector_version=collector_version,
    )
    return HrisCollection(
        records=feed.rows,
        raw_sha256=raw_sha256,
        pagination=pagination,
        contract=contract,
    )
