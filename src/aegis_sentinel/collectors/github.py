"""COL03 — GitHub collectors: org roster snapshot + audit-log events.

Two surfaces, two collectors, one system:

- :class:`GithubOrgMembersCollector` serves ``github.org_members.rest_v3``
  (``registry/capabilities/github.org-members.json``): the STATE_ONLY
  account inventory across BOTH endpoints the entry names — org members
  and outside collaborators. Page pagination per the entry's exhaustion
  method: *"follow the Link rel="next" header until absent, on both the
  members and outside_collaborators endpoints"* — simulated in fixture
  pages as a ``link_next`` field plus an ``endpoint`` discriminator.
  Completeness therefore requires both endpoints retrieved and each
  exhausted; a 404-shaped body where the Link header promised a page is
  flagged (seeded fixture ``tests/fixtures/seeded/github_short_page/``).

  LOCAL accounts: the entry's history caveat — local (non-SSO) accounts
  may have no IdP counterpart at all — is why the parse carries the
  fixture-side ``saml_name_id`` enrichment (``None`` marks a local
  account; the live surface exposes this via the SAML external-identity
  mapping). The dormant-account poison lives here.

- :class:`GithubAuditLogCollector` serves ``github.audit_log.rest_v3``
  (``registry/capabilities/github.audit-log.json``): EVENT_HISTORY
  membership-removal events (``org.remove_member``). Cursor pagination:
  follow the after cursor from the Link rel="next" header until absent.

Both parse only; they never interpret (PRD-v3 §4).
"""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from pydantic import Field

from aegis_sentinel.collectors.base import CollectionSnapshot, Collector
from aegis_sentinel.schema import AegisModel

MODULE_VERSION = "collectors.github@0.1.0"

#: Endpoint suffixes the org-roster surface must exhaust (entry method).
ENDPOINT_MEMBERS = "members"
ENDPOINT_OUTSIDE = "outside_collaborators"
#: Audit-log action for organization membership removal.
ACTION_REMOVE_MEMBER = "org.remove_member"


class GithubAccount(AegisModel):
    """One parsed GitHub account (COL03 roster yield).

    ``saml_name_id is None`` marks a LOCAL (non-SSO) account —
    the identity join to HRIS/IdP has nothing to key on (entry caveat).
    """

    login: str = Field(min_length=1)
    id: int = Field(ge=1)
    type: str = Field(min_length=1)
    site_admin: bool
    role: str = Field(min_length=1)
    saml_name_id: str | None
    last_active: date
    membership: str = Field(min_length=1)  # "member" | "outside_collaborator"

    @property
    def is_local(self) -> bool:
        return self.saml_name_id is None


class GithubAuditEvent(AegisModel):
    """One parsed audit-log event (COL03 audit yield)."""

    timestamp_ms: int = Field(ge=0)
    action: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    user: str = Field(min_length=1)
    org: str = Field(min_length=1)
    created_at_ms: int = Field(ge=0)


def _items(page: dict[str, Any]) -> list[dict[str, Any]]:
    items = page.get("items", [])
    return items if isinstance(items, list) else []


def _has_next(page: dict[str, Any]) -> bool:
    return bool(page.get("link_next"))


def _endpoint_kind(page: dict[str, Any]) -> str:
    endpoint = page.get("endpoint", "")
    return endpoint.rsplit("/", 1)[-1] if isinstance(endpoint, str) else ""


def _error_shaped(page: dict[str, Any]) -> bool:
    """A REST error body where a result page was promised (e.g. 404)."""
    return "items" not in page and "message" in page


class GithubOrgMembersCollector(Collector):
    """Collects and parses the org roster: members + outside collaborators."""

    system: ClassVar[str] = "github"
    collector_version: ClassVar[str] = MODULE_VERSION
    page_schema_version: ClassVar[str] = "github-org-page@v1"

    def _exhausted(self, pages: tuple[dict[str, Any], ...]) -> bool:
        """Both endpoints retrieved and each endpoint's last page carries
        no Link rel="next" — the entry's dual-endpoint exhaustion method."""
        if any(_error_shaped(page) for page in pages):
            return False
        last_by_endpoint: dict[str, dict[str, Any]] = {}
        for page in pages:
            last_by_endpoint[_endpoint_kind(page)] = page
        return all(
            endpoint in last_by_endpoint and not _has_next(last_by_endpoint[endpoint])
            for endpoint in (ENDPOINT_MEMBERS, ENDPOINT_OUTSIDE)
        )

    def _completeness(self, pages: tuple[dict[str, Any], ...]) -> tuple[bool, tuple[str, ...]]:
        if not pages:
            return False, ("no pages fetched; population basis missing",)
        reasons: list[str] = []
        for index, page in enumerate(pages, start=1):
            if _error_shaped(page):
                reasons.append(
                    f"{page.get('status', 'error')}-shaped response on "
                    f"{page.get('endpoint', 'unknown endpoint')} (page {index}) where "
                    'Link rel="next" promised a page; enumeration truncated'
                )
        clean = [page for page in pages if not _error_shaped(page)]
        last_by_endpoint: dict[str, dict[str, Any]] = {}
        for page in clean:
            last_by_endpoint[_endpoint_kind(page)] = page
        for endpoint in (ENDPOINT_MEMBERS, ENDPOINT_OUTSIDE):
            last = last_by_endpoint.get(endpoint)
            if last is None:
                reasons.append(
                    f"{endpoint} endpoint never retrieved; account inventory basis incomplete"
                )
            elif _has_next(last):
                reasons.append(
                    f'Link rel="next" present on the last {endpoint} page but the next '
                    "page was never retrieved; enumeration may be truncated"
                )
        return (not reasons), tuple(reasons)

    @staticmethod
    def accounts(snapshot: CollectionSnapshot) -> tuple[GithubAccount, ...]:
        """Typed parse of accounts from raw pages, feed order, endpoint-tagged."""
        return tuple(
            GithubAccount(
                login=row["login"],
                id=row["id"],
                type=row["type"],
                site_admin=row["site_admin"],
                role=row["role"],
                saml_name_id=row["saml_name_id"],
                last_active=date.fromisoformat(row["last_active"]),
                membership=(
                    "outside_collaborator" if _endpoint_kind(page) == ENDPOINT_OUTSIDE else "member"
                ),
            )
            for page in snapshot.pages
            for row in _items(page)
        )


class GithubAuditLogCollector(Collector):
    """Collects and parses org audit-log events (EVENT_HISTORY)."""

    system: ClassVar[str] = "github"
    collector_version: ClassVar[str] = MODULE_VERSION
    page_schema_version: ClassVar[str] = "github-audit-log-page@v1"

    def _exhausted(self, pages: tuple[dict[str, Any], ...]) -> bool:
        """Cursor pagination: no Link rel="next" on the last page."""
        return not _has_next(pages[-1])

    def _completeness(self, pages: tuple[dict[str, Any], ...]) -> tuple[bool, tuple[str, ...]]:
        if not pages:
            return False, ("no pages fetched; population basis missing",)
        if _has_next(pages[-1]):
            return False, (
                f'Link rel="next" cursor present after {len(pages)} page(s) but the '
                "next page was never retrieved; event enumeration may be truncated",
            )
        return True, ()

    @staticmethod
    def events(snapshot: CollectionSnapshot) -> tuple[GithubAuditEvent, ...]:
        """Typed parse of audit events from raw pages, feed order."""
        return tuple(
            GithubAuditEvent(
                timestamp_ms=row["@timestamp"],
                action=row["action"],
                actor=row["actor"],
                user=row["user"],
                org=row["org"],
                created_at_ms=row["created_at"],
            )
            for page in snapshot.pages
            for row in _items(page)
        )

    @staticmethod
    def removals(snapshot: CollectionSnapshot) -> tuple[GithubAuditEvent, ...]:
        """The membership-removal subset: ``org.remove_member`` only."""
        return tuple(
            event
            for event in GithubAuditLogCollector.events(snapshot)
            if event.action == ACTION_REMOVE_MEMBER
        )
