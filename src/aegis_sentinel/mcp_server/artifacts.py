"""Pure read-side access to the committed demo-engagement artifacts.

This module is deliberately free of any MCP dependency so the query and
read logic stays importable (and unit-testable) without the optional
``mcp`` extra. Reads only — no write calls of any kind belong here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

#: The four committed artifacts the server exposes, in listing order.
ARTIFACT_NAMES: tuple[str, ...] = ("verdicts", "reconciliation", "registry", "poisons")

URI_PREFIX = "aegis://demo-engagement/"


def artifact_uri(name: str) -> str:
    """URI for a named artifact, e.g. ``aegis://demo-engagement/verdicts``."""
    return f"{URI_PREFIX}{name}"


@dataclass(frozen=True)
class ArtifactStore:
    """Read-only view over an artifacts directory (default demo-engagement)."""

    root: Path

    def path_for(self, name: str) -> Path:
        if name not in ARTIFACT_NAMES:
            raise KeyError(f"unknown artifact {name!r}; expected one of {ARTIFACT_NAMES}")
        return self.root / f"{name}.json"

    def read_text(self, name: str) -> str:
        """The artifact's exact committed bytes, decoded as UTF-8."""
        return self.path_for(name).read_text(encoding="utf-8")

    def query_verdicts(
        self,
        control_id: str | None = None,
        status: str | None = None,
        record_id: str | None = None,
    ) -> list[dict]:
        """Filter verdict records; every filter is optional and conjunctive."""
        records: list[dict] = json.loads(self.read_text("verdicts"))
        if control_id is not None:
            records = [r for r in records if r.get("control_id") == control_id]
        if status is not None:
            records = [r for r in records if r.get("status") == status]
        if record_id is not None:
            records = [r for r in records if r.get("record_id") == record_id]
        return records
