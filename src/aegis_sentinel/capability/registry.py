"""Versioned on-disk capability registry (JSON per D-P2).

The compiler-facing surface is usable(): only FROZEN entries — an
unratified draft is visible for review but mechanically unusable.
"""

from pathlib import Path

from aegis_sentinel.capability.entry import CapabilityEntry
from aegis_sentinel.schema.enums import LifecycleState


class Registry:
    def __init__(self, entries: tuple[CapabilityEntry, ...]):
        ids = [e.id for e in entries]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate capability entry ids in registry")
        self._entries = entries

    @classmethod
    def load(cls, directory: Path) -> "Registry":
        entries = tuple(
            CapabilityEntry.model_validate_json(path.read_text())
            for path in sorted(directory.glob("*.json"))
        )
        return cls(entries)

    def all(self) -> tuple[CapabilityEntry, ...]:
        return self._entries

    def usable(self) -> tuple[CapabilityEntry, ...]:
        return tuple(e for e in self._entries if e.lifecycle is LifecycleState.FROZEN)

    def get_usable(self, entry_id: str) -> CapabilityEntry | None:
        for entry in self.usable():
            if entry.id == entry_id:
                return entry
        return None
