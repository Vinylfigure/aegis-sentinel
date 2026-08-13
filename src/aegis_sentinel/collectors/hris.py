"""COL01 — HRIS terminations-feed collector.

Serves the ``hris.terminations_feed.export_v1`` capability entry
(``registry/capabilities/hris.terminations-feed.json``): the daily
terminations export, delivered as fixture page files whose final page
carries a trailer record declaring the total row count. Exhaustion per
the entry's method: *"compare row count against the trailer record's
declared total before accepting the file."*

Completeness (salvaged from the prior scaffold's
``aegis-sentinel/src/completeness.py``):

- no trailer record fetched → exhaustion cannot be asserted (the
  ``assert_exhaustive_pagination`` case: the feed may be truncated);
- data-row count ≠ trailer-declared total → population incomplete or
  double-counted (the ``assert_independent_count`` case — the trailer
  total is the feed's independently declared count).

Either way the snapshot is flagged incomplete with the reason named,
and the downstream evaluator emits a population-level UNKNOWN — never
a partial pass. Seeded failing fixture proving detection:
``tests/fixtures/seeded/hris_truncated_feed/``.
"""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from pydantic import Field

from aegis_sentinel.collectors.base import CollectionSnapshot, Collector
from aegis_sentinel.schema import AegisModel

MODULE_VERSION = "collectors.hris@0.1.0"

#: Feed row discriminator values (page schema hris-termination-feed-page@v1).
RECORD_TYPE_TERMINATION = "termination"
RECORD_TYPE_TRAILER = "trailer"


class TerminationEvent(AegisModel):
    """One parsed termination event from the HRIS feed (COL01 yield)."""

    employee_id: str = Field(min_length=1)
    email: str = Field(min_length=1)
    termination_date: date
    worker_type: str = Field(min_length=1)


def _rows(page: dict[str, Any]) -> list[dict[str, Any]]:
    rows = page.get("rows", [])
    return rows if isinstance(rows, list) else []


class HrisTerminationsCollector(Collector):
    """Collects and parses the HRIS daily terminations export."""

    system: ClassVar[str] = "hris"
    collector_version: ClassVar[str] = MODULE_VERSION
    page_schema_version: ClassVar[str] = "hris-termination-feed-page@v1"

    def _exhausted(self, pages: tuple[dict[str, Any], ...]) -> bool:
        """The trailer record is the feed's end-of-file signal."""
        return any(row.get("record_type") == RECORD_TYPE_TRAILER for row in _rows(pages[-1]))

    def _completeness(self, pages: tuple[dict[str, Any], ...]) -> tuple[bool, tuple[str, ...]]:
        if not pages:
            # Prior scaffold: "No pages fetched; population basis missing."
            return False, ("no pages fetched; population basis missing",)
        trailers = [
            row
            for page in pages
            for row in _rows(page)
            if row.get("record_type") == RECORD_TYPE_TRAILER
        ]
        data_count = sum(
            1
            for page in pages
            for row in _rows(page)
            if row.get("record_type") == RECORD_TYPE_TERMINATION
        )
        if not trailers:
            return False, (
                f"trailer record missing after {len(pages)} page(s); "
                "feed exhaustion cannot be asserted (feed may be truncated)",
            )
        declared = trailers[-1].get("total_rows")
        if declared != data_count:
            return False, (
                f"collected {data_count} termination row(s) != trailer-declared "
                f"total {declared}; population incomplete or double-counted",
            )
        return True, ()

    @staticmethod
    def events(snapshot: CollectionSnapshot) -> tuple[TerminationEvent, ...]:
        """Parse termination events from a snapshot's raw pages, feed order.

        Deterministic typed parse (the EQC semantics method): data rows
        only, trailer excluded; field names per the capability entry's
        ``attributes`` block (``work_email`` → ``email``).
        """
        return tuple(
            TerminationEvent(
                employee_id=row["employee_id"],
                email=row["work_email"],
                termination_date=date.fromisoformat(row["termination_date"]),
                worker_type=row["worker_type"],
            )
            for page in snapshot.pages
            for row in _rows(page)
            if row.get("record_type") == RECORD_TYPE_TERMINATION
        )
