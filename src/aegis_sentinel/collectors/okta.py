"""COL02 — Okta collectors: users snapshot + System Log deprovisioning events.

Two surfaces, two collectors, one system:

- :class:`OktaUsersCollector` serves ``okta.users.api_v1``
  (``registry/capabilities/okta.users.json``): the STATE_ONLY user
  inventory. Cursor pagination per the entry's exhaustion method —
  *"follow the after cursor from the Link rel="next" header until the
  header is absent"* — simulated in fixture pages as a ``link_next``
  field. A feed that ends while the last page still carries a cursor is
  flagged incomplete (the seeded fixture
  ``tests/fixtures/seeded/okta_truncated_users/`` proves detection).

- :class:`OktaSystemLogCollector` serves ``okta.system_log.api_v1``
  (``registry/capabilities/okta.system-log.json``): EVENT_HISTORY
  deprovisioning events (``user.lifecycle.deactivate``). Exhaustion per
  the entry's method: *"follow the after cursor ... until a page
  returns zero events"* — the zero-event page is the exhaustion signal,
  so a feed that ends on a non-empty page is flagged incomplete.

Both parse only; they never interpret (PRD-v3 §4). Deactivation
timestamps: ``statusChanged`` on a DEPROVISIONED user (users surface),
``published`` on a deactivate event (log surface).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from aegis_sentinel.collectors.base import CollectionSnapshot, Collector
from aegis_sentinel.schema import AegisModel

MODULE_VERSION = "collectors.okta@0.1.0"

#: Okta user lifecycle status marking a deprovisioned account.
STATUS_DEPROVISIONED = "DEPROVISIONED"
#: System Log event type for user deactivation (deprovisioning).
EVENT_DEACTIVATE = "user.lifecycle.deactivate"


class OktaUser(AegisModel):
    """One parsed Okta user (COL02 users-surface yield)."""

    id: str = Field(min_length=1)
    login: str = Field(min_length=1)
    email: str = Field(min_length=1)
    status: str = Field(min_length=1)
    created: datetime
    activated: datetime
    status_changed: datetime

    @property
    def deactivated_at(self) -> datetime | None:
        """Deactivation timestamp where present: ``statusChanged`` carries
        the most recent lifecycle transition, so it is the deactivation
        time iff the user is DEPROVISIONED (entry history caveat)."""
        return self.status_changed if self.status == STATUS_DEPROVISIONED else None


class OktaLogEvent(AegisModel):
    """One parsed System Log event (COL02 log-surface yield)."""

    uuid: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    published: datetime
    actor_id: str = Field(min_length=1)
    actor_alternate_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    target_alternate_id: str = Field(min_length=1)
    outcome: str = Field(min_length=1)


def _items(page: dict[str, Any]) -> list[dict[str, Any]]:
    items = page.get("items", [])
    return items if isinstance(items, list) else []


def _has_next(page: dict[str, Any]) -> bool:
    return bool(page.get("link_next"))


class OktaUsersCollector(Collector):
    """Collects and parses the Okta user inventory (STATE_ONLY)."""

    system: ClassVar[str] = "okta"
    collector_version: ClassVar[str] = MODULE_VERSION
    page_schema_version: ClassVar[str] = "okta-users-page@v1"

    def _exhausted(self, pages: tuple[dict[str, Any], ...]) -> bool:
        """Cursor pagination: no Link rel="next" on the last page."""
        return not _has_next(pages[-1])

    def _completeness(self, pages: tuple[dict[str, Any], ...]) -> tuple[bool, tuple[str, ...]]:
        if not pages:
            return False, ("no pages fetched; population basis missing",)
        if _has_next(pages[-1]):
            return False, (
                f'Link rel="next" cursor present after {len(pages)} page(s) but the '
                "next page was never retrieved; user enumeration may be truncated",
            )
        return True, ()

    @staticmethod
    def users(snapshot: CollectionSnapshot) -> tuple[OktaUser, ...]:
        """Typed parse of user records from raw pages, feed order."""
        return tuple(
            OktaUser(
                id=row["id"],
                login=row["profile"]["login"],
                email=row["profile"]["email"],
                status=row["status"],
                created=row["created"],
                activated=row["activated"],
                status_changed=row["statusChanged"],
            )
            for page in snapshot.pages
            for row in _items(page)
        )


class OktaSystemLogCollector(Collector):
    """Collects and parses System Log deprovisioning events (EVENT_HISTORY)."""

    system: ClassVar[str] = "okta"
    collector_version: ClassVar[str] = MODULE_VERSION
    page_schema_version: ClassVar[str] = "okta-system-log-page@v1"

    def _exhausted(self, pages: tuple[dict[str, Any], ...]) -> bool:
        """Log pagination: a page returning zero events is the end signal
        (the Link header is always present on this surface)."""
        return not _items(pages[-1])

    def _completeness(self, pages: tuple[dict[str, Any], ...]) -> tuple[bool, tuple[str, ...]]:
        if not pages:
            return False, ("no pages fetched; population basis missing",)
        if _items(pages[-1]):
            return False, (
                f"feed ended after {len(pages)} page(s) without a zero-event page; "
                "event exhaustion cannot be asserted (log may be truncated)",
            )
        return True, ()

    @staticmethod
    def events(snapshot: CollectionSnapshot) -> tuple[OktaLogEvent, ...]:
        """Typed parse of log events from raw pages, feed order.

        ``target[0]`` is the subject user per the entry's
        ``target.alternateId`` attribute exposure.
        """
        return tuple(
            OktaLogEvent(
                uuid=row["uuid"],
                event_type=row["eventType"],
                published=row["published"],
                actor_id=row["actor"]["id"],
                actor_alternate_id=row["actor"]["alternateId"],
                target_id=row["target"][0]["id"],
                target_alternate_id=row["target"][0]["alternateId"],
                outcome=row["outcome"]["result"],
            )
            for page in snapshot.pages
            for row in _items(page)
        )

    @staticmethod
    def deactivations(snapshot: CollectionSnapshot) -> tuple[OktaLogEvent, ...]:
        """The deprovisioning subset: ``user.lifecycle.deactivate`` only."""
        return tuple(
            event
            for event in OktaSystemLogCollector.events(snapshot)
            if event.event_type == EVENT_DEACTIVATE
        )
