"""COL04 — GCP IAM bindings collector (Cloud Asset Inventory shape).

Serves ``gcp.iam.cloud_asset_v1`` (``registry/capabilities/gcp.iam.json``):
``searchAllIamPolicies`` results — one entry per resource, each carrying
``policy.bindings`` with a principals list per role. STATE_ONLY.
Pagination per the entry's exhaustion method: *"pass pageToken from the
previous response's nextPageToken until the response omits it"* — a feed
that ends while the last page still carries ``nextPageToken`` is flagged
incomplete (seeded fixture
``tests/fixtures/seeded/gcp_missing_page_token_target/``).

Entry history caveat worth repeating here: principals with access
outside IAM policy bindings (downloaded keys, break-glass accounts
provisioned out of band) do not appear in policy search — but a
break-glass principal that *does* hold a binding (the fixture tenant's
``breakglass-admin@example-prod.iam.gserviceaccount.com``, roles/owner)
is enumerated like any other member. The collector parses; deciding that
the principal joins to no identity anywhere is REC01's job (PRD-v3 §4).
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from aegis_sentinel.collectors.base import CollectionSnapshot, Collector
from aegis_sentinel.schema import AegisModel

MODULE_VERSION = "collectors.gcp@0.1.0"


class IamBinding(AegisModel):
    """One (resource, role) binding with its principals list (COL04 yield)."""

    resource: str = Field(min_length=1)
    project: str = Field(min_length=1)
    role: str = Field(min_length=1)
    members: tuple[str, ...] = Field(min_length=1)


def _results(page: dict[str, Any]) -> list[dict[str, Any]]:
    results = page.get("results", [])
    return results if isinstance(results, list) else []


def _has_next(page: dict[str, Any]) -> bool:
    return bool(page.get("nextPageToken"))


class GcpIamBindingsCollector(Collector):
    """Collects and parses IAM policy bindings via Cloud Asset Inventory."""

    system: ClassVar[str] = "gcp"
    collector_version: ClassVar[str] = MODULE_VERSION
    page_schema_version: ClassVar[str] = "gcp-iam-policy-page@v1"

    def _exhausted(self, pages: tuple[dict[str, Any], ...]) -> bool:
        """Token pagination: the response omits ``nextPageToken``."""
        return not _has_next(pages[-1])

    def _completeness(self, pages: tuple[dict[str, Any], ...]) -> tuple[bool, tuple[str, ...]]:
        if not pages:
            return False, ("no pages fetched; population basis missing",)
        if _has_next(pages[-1]):
            return False, (
                f"nextPageToken present after {len(pages)} page(s) but the target "
                "page was never retrieved; IAM policy enumeration may be truncated",
            )
        return True, ()

    @staticmethod
    def bindings(snapshot: CollectionSnapshot) -> tuple[IamBinding, ...]:
        """Typed parse: flatten each result's ``policy.bindings``, feed order."""
        return tuple(
            IamBinding(
                resource=result["resource"],
                project=result["project"],
                role=binding["role"],
                members=tuple(binding["members"]),
            )
            for page in snapshot.pages
            for result in _results(page)
            for binding in result["policy"]["bindings"]
        )

    @staticmethod
    def principals(snapshot: CollectionSnapshot) -> tuple[str, ...]:
        """Every distinct principal holding any binding, sorted."""
        return tuple(
            sorted(
                {
                    member
                    for binding in GcpIamBindingsCollector.bindings(snapshot)
                    for member in binding.members
                }
            )
        )
