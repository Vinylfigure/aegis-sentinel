"""Versioned on-disk capability registry (PRD-v3 §3; SCH02).

Entries live as one JSON file per entry under ``registry/capabilities/``
(JSON, not YAML — D-P2) and are versioned by git like everything else.
:meth:`Registry.load` validates every file against
:class:`~aegis_sentinel.capability.entry.CapabilityEntry` — an invalid
file fails the whole load (an unvalidated registry is not a registry).

The ratification gate is mechanical, not convention: :meth:`Registry.all`
is the inspection view (drafts included); :meth:`Registry.usable` is the
*only* compiler-facing view and contains exactly the entries with
``provenance.ratified_by`` set. Compiler code (TYP01) must resolve
capabilities through ``usable()`` — a Cartographer draft cannot type-check
a claim no matter what any caller intends.

Pure stdlib + pydantic: no LLM, no network, no clock reads.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from aegis_sentinel.capability.entry import CapabilityEntry

MODULE_VERSION = "capability.registry@0.1.0"


class RegistryView:
    """An immutable, filterable set of capability entries.

    Both :meth:`Registry.all` and :meth:`Registry.usable` return one of
    these; lookup helpers (``for_system`` …) return further-narrowed
    views, so a filter applied to the usable view can never surface an
    unratified entry.
    """

    __slots__ = ("_entries",)

    def __init__(self, entries: tuple[CapabilityEntry, ...]) -> None:
        self._entries = tuple(entries)

    def __iter__(self) -> Iterator[CapabilityEntry]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def entries(self) -> tuple[CapabilityEntry, ...]:
        return self._entries

    def entry_ids(self) -> tuple[str, ...]:
        return tuple(e.entry_id for e in self._entries)

    def get(self, entry_id: str) -> CapabilityEntry:
        """Return the entry with this id; ``KeyError`` if absent from the view.

        Absent-from-view is the mechanical unusability: an unratified
        entry_id raises here when looked up through ``usable()``.
        """
        for entry in self._entries:
            if entry.entry_id == entry_id:
                return entry
        raise KeyError(f"no entry {entry_id!r} in this registry view")

    def for_system(self, system: str) -> "RegistryView":
        """Narrow to one system's surfaces (e.g. ``for_system("okta")``)."""
        return RegistryView(tuple(e for e in self._entries if e.system == system))


class Registry:
    """All capability entries loaded from one on-disk registry directory."""

    __slots__ = ("_entries",)

    def __init__(self, entries: tuple[CapabilityEntry, ...]) -> None:
        seen: set[str] = set()
        for entry in entries:
            if entry.entry_id in seen:
                raise ValueError(f"duplicate entry_id {entry.entry_id!r} in registry")
            seen.add(entry.entry_id)
        self._entries = tuple(entries)

    @classmethod
    def load(cls, dir_path: str | Path) -> "Registry":
        """Load and validate every ``*.json`` entry under ``dir_path``.

        In this repo the directory is ``registry/capabilities/``. Files
        are read in sorted-name order so load order (and every view
        derived from it) is deterministic. Any invalid file raises
        ``pydantic.ValidationError`` and fails the whole load.
        """
        directory = Path(dir_path)
        if not directory.is_dir():
            raise FileNotFoundError(f"registry directory not found: {directory}")
        entries = tuple(
            CapabilityEntry.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(directory.glob("*.json"))
        )
        return cls(entries)

    def all(self) -> RegistryView:
        """Every entry, drafts included — the inspection/review view."""
        return RegistryView(self._entries)

    def usable(self) -> RegistryView:
        """Only human-ratified entries — the sole compiler-facing view."""
        return RegistryView(tuple(e for e in self._entries if e.is_ratified))
