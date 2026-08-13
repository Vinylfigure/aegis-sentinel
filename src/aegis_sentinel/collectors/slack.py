"""COL05 — Slack users collector (``users.list``).

Serves ``slack.users.web_api`` (``registry/capabilities/slack.users.json``):
the STATE_ONLY workspace member inventory; the ``deleted`` flag marks
deactivated members (current state only — timing needs the Audit Logs
API, per the entry's history caveat). Cursor pagination per the entry's
exhaustion method: *"follow response_metadata.next_cursor until it is
empty"* — a feed that ends while the last page still carries a non-empty
cursor is flagged incomplete (seeded fixture
``tests/fixtures/seeded/slack_truncated_cursor/``). A page with
``"ok": false`` is a Web API error envelope, never member data.
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from aegis_sentinel.collectors.base import CollectionSnapshot, Collector
from aegis_sentinel.schema import AegisModel

MODULE_VERSION = "collectors.slack@0.1.0"


class SlackUser(AegisModel):
    """One parsed Slack workspace member (COL05 yield).

    ``email`` is ``None`` where the profile carries no email (bot users;
    the entry's auth scope note — ``users:read.email`` gates the field).
    """

    id: str = Field(min_length=1)
    team_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    deleted: bool
    is_bot: bool
    is_admin: bool
    is_owner: bool
    email: str | None
    updated: int = Field(ge=0)


def _members(page: dict[str, Any]) -> list[dict[str, Any]]:
    members = page.get("members", [])
    return members if isinstance(members, list) else []


def _next_cursor(page: dict[str, Any]) -> str:
    metadata = page.get("response_metadata", {})
    cursor = metadata.get("next_cursor", "") if isinstance(metadata, dict) else ""
    return cursor if isinstance(cursor, str) else ""


class SlackUsersCollector(Collector):
    """Collects and parses the workspace member inventory."""

    system: ClassVar[str] = "slack"
    collector_version: ClassVar[str] = MODULE_VERSION
    page_schema_version: ClassVar[str] = "slack-users-page@v1"

    def _exhausted(self, pages: tuple[dict[str, Any], ...]) -> bool:
        """Cursor pagination: an ok page whose ``next_cursor`` is empty."""
        last = pages[-1]
        return bool(last.get("ok")) and not _next_cursor(last)

    def _completeness(self, pages: tuple[dict[str, Any], ...]) -> tuple[bool, tuple[str, ...]]:
        if not pages:
            return False, ("no pages fetched; population basis missing",)
        reasons: list[str] = []
        for index, page in enumerate(pages, start=1):
            if not page.get("ok"):
                reasons.append(
                    f'"ok": false Web API envelope on page {index} '
                    f"(error: {page.get('error', 'unnamed')}); member data missing"
                )
        if not reasons and _next_cursor(pages[-1]):
            reasons.append(
                f"response_metadata.next_cursor non-empty after {len(pages)} page(s) "
                "but the next page was never retrieved; member enumeration may be truncated"
            )
        return (not reasons), tuple(reasons)

    @staticmethod
    def users(snapshot: CollectionSnapshot) -> tuple[SlackUser, ...]:
        """Typed parse of members from raw pages, feed order."""
        return tuple(
            SlackUser(
                id=row["id"],
                team_id=row["team_id"],
                name=row["name"],
                deleted=row["deleted"],
                is_bot=row["is_bot"],
                is_admin=row["is_admin"],
                is_owner=row["is_owner"],
                email=row["profile"].get("email"),
                updated=row["updated"],
            )
            for page in snapshot.pages
            for row in _members(page)
        )
