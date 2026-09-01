"""REC10: the Surveyor (deterministic lane, PRD-v3 §3/§8) — "once a
capability entry is ratified and a read scope is granted through the
manifest, a deterministic probe (not the LLM) executes the entry's
enumeration once against the real tenant ... and diffs observed-vs-
documented. Drift between docs and reality is itself a finding."

`run_probe()` is the whole of its mechanical authority, mirroring the
collectors' injected-transport shape (COL01-05): the transport is a
callable returning raw probe-response bytes, so this module performs no
I/O of its own — fixture bytes in tests, a real extract later, identical
code path either way (no live-tenant calls in tests). `run_probe()`
refuses outright on any entry that isn't `lifecycle=FROZEN` (HANDOFF §4
REC10 — "one ratified enumeration per entry"; a DRAFT entry has not been
ratified, so there is nothing to probe), and refuses a response whose
tenant doesn't match the engagement tenant, exactly as the collectors
do. This mirrors the collectors' own scope precisely: like COL01-05,
`run_probe()` checks the capability entry's own ratification, not
whether a specific ratified manifest snapshot actually grants this
engagement that capability — snapshot-level scope enforcement is a
call-site concern (the manifest gates which collectors/probes a run may
invoke at all), not re-implemented per collector or probe.

The probe never writes, ratifies, or corrects the registry — it only
reports drift as `Finding`s for a human to act on (registry health
metric, PRD-v3 §7).
"""

import hashlib
import json
from collections.abc import Callable
from datetime import datetime

from pydantic import Field

from aegis_sentinel.capability.entry import CapabilityEntry, PaginationMethod, TemporalKind
from aegis_sentinel.schema.enums import LifecycleState
from aegis_sentinel.schema.models import SHA256, Base


class ProbeRefusal(ValueError):
    """Raised instead of silently probing a capability entry the Surveyor
    has no ratified scope to touch, or a response whose tenant doesn't
    match the engagement — refusal, never a partial or mislabeled probe."""


class ObservedCapability(Base):
    """What the probe actually saw, parsed from the raw response.
    `earliest_record_at` is only meaningful for an event-history entry —
    it is the timestamp of the oldest record the enumeration reached
    before exhausting, from which observed retention depth is derived
    rather than trusted as a self-reported number."""

    tenant: str = Field(min_length=1)
    extracted_at: datetime
    schema_attributes: tuple[str, ...] = Field(min_length=1)
    pagination_method: PaginationMethod
    earliest_record_at: datetime | None = None


class Finding(Base):
    """One point of drift between the ratified entry's documentation and
    what the probe observed. `kind` names the drift class; `documented`
    and `observed` are the two sides, always as strings so schema-set and
    scalar drift render identically."""

    entry_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    documented: str
    observed: str
    detail: str = Field(min_length=1)


class ProbeResult(Base):
    entry_id: str = Field(min_length=1)
    tenant: str = Field(min_length=1)
    raw_sha256: str = Field(pattern=SHA256)
    observed: ObservedCapability
    findings: tuple[Finding, ...]


def _schema_drift(entry: CapabilityEntry, observed: ObservedCapability) -> Finding | None:
    # Union across every yielded population (github.members-shaped entries
    # document more than one, e.g. entity + relationship attributes from the
    # same surface) — the probe response carries one flat observed set, so
    # drift is judged against everything documented, not just population[0].
    documented = {
        attr for population in entry.populations_yielded for attr in population.attributes
    }
    seen = set(observed.schema_attributes)
    if documented == seen:
        return None
    missing = sorted(documented - seen)
    extra = sorted(seen - documented)
    detail_parts = []
    if missing:
        detail_parts.append(f"documented but not observed: {', '.join(missing)}")
    if extra:
        detail_parts.append(f"observed but not documented: {', '.join(extra)}")
    return Finding(
        entry_id=entry.id,
        kind="schema_drift",
        documented=", ".join(sorted(documented)),
        observed=", ".join(sorted(seen)),
        detail="; ".join(detail_parts),
    )


def _pagination_drift(entry: CapabilityEntry, observed: ObservedCapability) -> Finding | None:
    if entry.pagination.method == observed.pagination_method:
        return None
    return Finding(
        entry_id=entry.id,
        kind="pagination_drift",
        documented=entry.pagination.method.value,
        observed=observed.pagination_method.value,
        detail=(
            f"documented pagination method {entry.pagination.method.value!r} does not "
            f"match the observed method {observed.pagination_method.value!r}"
        ),
    )


def _temporal_drift(entry: CapabilityEntry, observed: ObservedCapability) -> Finding | None:
    if entry.temporal.kind is not TemporalKind.EVENT_HISTORY:
        return None
    if observed.earliest_record_at is None:
        return None
    documented_days = entry.temporal.window_days
    observed_days = (observed.extracted_at - observed.earliest_record_at).days
    if observed_days == documented_days:
        return None
    return Finding(
        entry_id=entry.id,
        kind="temporal_drift",
        documented=f"{documented_days}d",
        observed=f"{observed_days}d",
        detail=(
            f"documented event-history window is {documented_days} day(s); the probe's "
            f"earliest reachable record was {observed_days} day(s) before the extract "
            "time — actual retention depth differs from the registered capability"
        ),
    )


def run_probe(
    entry: CapabilityEntry,
    transport: Callable[[CapabilityEntry], bytes],
    *,
    tenant: str,
) -> ProbeResult:
    """Execute the entry's documented enumeration once through the
    injected transport (called with the entry; returns the raw probe
    response bytes) and diff observed-vs-documented.

    Raises `ProbeRefusal` if the entry isn't ratified (`lifecycle !=
    FROZEN`), if the response's tenant doesn't match `tenant` (provenance,
    mirroring the collectors' wrong-tenant refusal), or if the response
    claims an `earliest_record_at` after its own `extracted_at`
    (malformed — refused rather than reported as a nonsensical negative
    retention depth). Never partial: a refusal always precedes any
    finding being recorded.
    """
    if entry.lifecycle is not LifecycleState.FROZEN:
        raise ProbeRefusal(
            f"{entry.id}: Surveyor may only probe a ratified (FROZEN) entry — one "
            "ratified enumeration per entry, HANDOFF §4 REC10; this entry is "
            f"{entry.lifecycle.value}"
        )
    raw = transport(entry)
    if not isinstance(raw, bytes):
        raise TypeError("transport must return the raw probe response as bytes")
    raw_sha256 = hashlib.sha256(raw).hexdigest()
    observed = ObservedCapability.model_validate(json.loads(raw.decode("utf-8")))
    if observed.tenant != tenant:
        raise ProbeRefusal(
            f"{entry.id}: probe response tenant {observed.tenant!r} != engagement "
            f"tenant {tenant!r} (provenance)"
        )
    if (
        observed.earliest_record_at is not None
        and observed.earliest_record_at > observed.extracted_at
    ):
        raise ProbeRefusal(
            f"{entry.id}: probe response earliest_record_at "
            f"{observed.earliest_record_at.isoformat()} is after extracted_at "
            f"{observed.extracted_at.isoformat()} — malformed response, refusing "
            "rather than reporting a nonsensical negative retention depth"
        )
    findings = tuple(
        finding
        for finding in (
            _schema_drift(entry, observed),
            _pagination_drift(entry, observed),
            _temporal_drift(entry, observed),
        )
        if finding is not None
    )
    return ProbeResult(
        entry_id=entry.id,
        tenant=tenant,
        raw_sha256=raw_sha256,
        observed=observed,
        findings=findings,
    )
