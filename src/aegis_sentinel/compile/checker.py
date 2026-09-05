"""Match (claim, assertion, population) against the capability registry.

Pure: inputs in, report out — no I/O, no clocks (D-P3 scope: this is a
`compile/` package, so the purity gate's determinism bans apply here).

E-codes:
- E117 — a derivation-rule source references a system with no USABLE
  (FROZEN) capability entry. A draft entry exists but is unusable: that
  is the registry's mechanical-unusability doing its job at compile time.
- E118 — a capability entry selected to serve a claim is registry-usable
  (FROZEN) but the active manifest snapshot's `blocks.capabilities` does
  not name it. Being usable is necessary but not sufficient: the ratified
  manifest, not just the registry, must authorize every capability a
  compile actually consumes — this is the boundary enforced structurally,
  rather than left to whatever called the registry.
- E204 — temporal insufficiency: a TIMING assertion must be provable
  over the population's whole period, and the serving capabilities'
  history cannot cover it. The error carries a satisfiable-via
  suggestion built from other registry entries (drafts named with their
  status, so the human sees the ratification path).
- E302 — schema-version drift between an evidence contract and the
  ratified capability entry's documented version.

Zero collectors are emitted for a claim with unresolved E-codes.
"""

from pydantic import Field

from aegis_sentinel.capability.entry import CapabilityEntry, TemporalKind
from aegis_sentinel.capability.registry import Registry
from aegis_sentinel.manifest import ManifestSnapshot
from aegis_sentinel.schema.enums import AssertionType, LifecycleState
from aegis_sentinel.schema.models import Base, Claim, EvidenceQualityContract, Population


class CompileError(Base):
    code: str = Field(pattern=r"^E\d{3}$")
    claim_id: str
    message: str
    suggestion: str | None = None


class CollectorPlan(Base):
    """What a clean compile emits: which capability serves which claim.
    Execution (COL tasks) consumes these; an erroring claim never gets one."""

    claim_id: str
    population_id: str
    capability_ids: tuple[str, ...] = Field(min_length=1)


class CompileReport(Base):
    errors: tuple[CompileError, ...]
    plans: tuple[CollectorPlan, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _period_days(population: Population) -> int:
    return (population.period.end - population.period.start).days


def _covers_timing(entry: CapabilityEntry, required_days: int) -> bool:
    if entry.temporal.kind is TemporalKind.FULL_HISTORY:
        return True
    if entry.temporal.kind is TemporalKind.EVENT_HISTORY:
        return entry.temporal.window_days >= required_days
    return False  # state-only / snapshot-cadence yield no transition timestamps


def _timing_suggestion(registry: Registry, required_days: int) -> str | None:
    candidates = []
    for entry in registry.all():
        if _covers_timing(entry, required_days):
            status = (
                ""
                if entry.lifecycle is LifecycleState.FROZEN
                else f" ({entry.lifecycle.value} — ratify first)"
            )
            kind = entry.temporal.kind.value
            window = (
                f", {entry.temporal.window_days}d" if entry.temporal.window_days is not None else ""
            )
            candidates.append(f"{entry.id} ({kind}{window}){status}")
    if not candidates:
        return None
    return "Satisfiable via: " + " + ".join(sorted(candidates)) + ". Amend manifest?"


def compile_claims(
    claims: tuple[Claim, ...],
    populations: tuple[Population, ...],
    registry: Registry,
    manifest: ManifestSnapshot,
    contracts: tuple[EvidenceQualityContract, ...] = (),
) -> CompileReport:
    populations_by_id = {p.id: p for p in populations}
    contracts_by_population = {c.population_ref: c for c in contracts}
    granted_capabilities = set(manifest.blocks.capabilities)
    errors: list[CompileError] = []
    plans: list[CollectorPlan] = []

    for claim in claims:
        claim_errors: list[CompileError] = []
        population = populations_by_id.get(claim.population_id)
        if population is None:
            claim_errors.append(
                CompileError(
                    code="E117",
                    claim_id=claim.id,
                    message=f"claim references unknown population {claim.population_id}",
                )
            )
            errors.extend(claim_errors)
            continue

        source_systems = (
            tuple(s.system for s in population.derivation_rule.sources)
            if population.derivation_rule
            else (population.authoritative_source.system,)
        )

        serving: list[CapabilityEntry] = []
        for system in dict.fromkeys(source_systems):
            usable = [e for e in registry.usable() if e.system == system]
            if not usable:
                drafts = [
                    e.id
                    for e in registry.all()
                    if e.system == system and e.lifecycle is not LifecycleState.FROZEN
                ]
                hint = f" A draft entry exists ({', '.join(drafts)}) — ratify it." if drafts else ""
                claim_errors.append(
                    CompileError(
                        code="E117",
                        claim_id=claim.id,
                        message=(
                            f"population {population.id} derivation references {system}; "
                            f"no usable capability entry for {system}.{hint}"
                        ),
                    )
                )
            serving.extend(usable)

        for entry in serving:
            if entry.id not in granted_capabilities:
                claim_errors.append(
                    CompileError(
                        code="E118",
                        claim_id=claim.id,
                        message=(
                            f"capability {entry.id} is usable (FROZEN) but manifest "
                            f"v{manifest.version} does not grant it — add it to "
                            "blocks.capabilities or drop the dependency"
                        ),
                    )
                )

        required_days = _period_days(population)
        for assertion in claim.assertions:
            if assertion.type is AssertionType.TIMING and serving:
                if not any(_covers_timing(e, required_days) for e in serving):
                    best = max(
                        (
                            e.temporal.window_days or 0
                            for e in serving
                            if e.temporal.kind is TemporalKind.EVENT_HISTORY
                        ),
                        default=0,
                    )
                    have = f"{best}d event-history" if best else "state-only evidence"
                    claim_errors.append(
                        CompileError(
                            code="E204",
                            claim_id=claim.id,
                            message=(
                                f"TIMING assertion {assertion.id} requires transition "
                                f"timestamps across {required_days}d; serving "
                                f"capabilities yield {have}"
                            ),
                            suggestion=_timing_suggestion(registry, required_days),
                        )
                    )

        contract = contracts_by_population.get(population.id)
        if contract is not None:
            for entry in serving:
                doc_version = entry.provenance.doc_version
                if doc_version is not None and contract.schema_version != doc_version:
                    claim_errors.append(
                        CompileError(
                            code="E302",
                            claim_id=claim.id,
                            message=(
                                f"contract {contract.id} schema_version "
                                f"{contract.schema_version} != ratified {entry.id} "
                                f"doc_version {doc_version} — re-ratify or pin"
                            ),
                        )
                    )

        if claim_errors:
            errors.extend(claim_errors)
        elif serving:
            plans.append(
                CollectorPlan(
                    claim_id=claim.id,
                    population_id=population.id,
                    capability_ids=tuple(sorted({e.id for e in serving})),
                )
            )

    return CompileReport(errors=tuple(errors), plans=tuple(plans))
