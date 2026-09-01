"""CAP10: the Cartographer agent (LLM lane, PRD-v3 §3/§8) — "the agent maps
the territory; it does not annex it." `propose_entry()` is the whole of its
mechanical authority: it turns researched documentation citations into a
`CapabilityEntry` proposal, and it is structurally unable to do either of
the two things the invariant forbids it:

- **cannot ratify** — there is no parameter through which a caller can set
  `ratified_by` or a non-DRAFT `lifecycle`; every entry this function
  returns is `lifecycle=DRAFT, ratified_by=None`, full stop.
- **cannot probe** — this module never imports `collectors/` and never
  touches a live tenant; a citation is just a documentation URL string, not
  an access credential.

Enforces D7 (`docs/DECISIONS.md`): a citation outside the vendor's
first-party doc allowlist may still be proposed (rule 3's secondary-source
allowance), but only alongside a caveat that names the gap — silent
omission is refused.
"""

from datetime import datetime

from aegis_sentinel.capability.allowlist import SOURCE_UNREACHABLE, is_allowed_citation
from aegis_sentinel.capability.entry import (
    AccessMode,
    CapabilityEntry,
    Pagination,
    Provenance,
    TemporalCoverage,
    YieldedPopulation,
)
from aegis_sentinel.schema.enums import LifecycleState


class CartographerRefusal(ValueError):
    """Raised instead of silently proposing an unverifiable capability
    entry — a Cartographer proposal must always say why any citation
    outside the D7 allowlist is there."""


def _names_the_gap(history_caveats: tuple[str, ...]) -> bool:
    return any("DRAFT:" in caveat and SOURCE_UNREACHABLE in caveat for caveat in history_caveats)


def propose_entry(
    *,
    id: str,
    system: str,
    surface: str,
    access_modes: tuple[AccessMode, ...],
    populations_yielded: tuple[YieldedPopulation, ...],
    temporal: TemporalCoverage,
    join_keys: tuple[str, ...],
    auth_scope: str,
    pagination: Pagination,
    citations: tuple[str, ...],
    researched_by: str,
    researched_at: datetime,
    rate_limits: str | None = None,
    history_caveats: tuple[str, ...] = (),
    doc_version: str | None = None,
) -> CapabilityEntry:
    """Propose a DRAFT capability entry. Raises `CartographerRefusal` if any
    citation sits outside the D7 allowlist and `history_caveats` doesn't
    record why (a `DRAFT: ...source_unreachable...` note) — D7 rule 3:
    missing evidence is UNKNOWN, never silently accepted."""
    disallowed = tuple(c for c in citations if not is_allowed_citation(system, c))
    if disallowed and not _names_the_gap(history_caveats):
        raise CartographerRefusal(
            f"{system}: citation(s) outside the D7 allowlist ({', '.join(disallowed)}) "
            "require a history_caveats entry containing 'DRAFT:' and "
            f"'{SOURCE_UNREACHABLE}' naming the gap — see docs/DECISIONS.md D7 rule 3"
        )
    return CapabilityEntry(
        id=id,
        system=system,
        surface=surface,
        access_modes=access_modes,
        populations_yielded=populations_yielded,
        temporal=temporal,
        join_keys=join_keys,
        auth_scope=auth_scope,
        pagination=pagination,
        rate_limits=rate_limits,
        history_caveats=history_caveats,
        provenance=Provenance(
            researched_by=researched_by,
            researched_at=researched_at,
            citations=citations,
            doc_version=doc_version,
        ),
        ratified_by=None,
        lifecycle=LifecycleState.DRAFT,
    )
