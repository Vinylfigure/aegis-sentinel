"""Deterministic lane-template instantiation (LANE01).

``instantiate_lane`` turns a LaneTemplate plus a systems mapping and a
period into the concrete Populations and Claims the compiler consumes
(docs/HANDOFF.md §4 LANE01). Pure function: no I/O, no clock reads, no
randomness — the same template, mapping, and period always produce the
identical object list in the identical order (template declaration
order; ``{system}`` expansion in SINK-node declaration order).

Placeholder semantics are defined in aegis_sentinel.schema.lane: every
node ``system_ref`` is a placeholder key the caller's mapping resolves;
``{system}`` binds per downstream SINK system. Unresolved placeholders
are an error, never silently passed through.
"""

from __future__ import annotations

import re
from typing import Mapping

from aegis_sentinel.schema.claim import Assertion, Claim
from aegis_sentinel.schema.lane import (
    SYSTEM_PLACEHOLDER,
    ClaimTemplate,
    LaneTemplate,
    PopulationTemplate,
)
from aegis_sentinel.schema.population import (
    AssuranceState,
    DerivationRule,
    Period,
    Population,
    Source,
)

MODULE_VERSION = "manifest.instantiate@0.1.0"

_PLACEHOLDER_RE = re.compile(r"\{[A-Za-z0-9_]+\}")


def _substitute(text: str, bindings: Mapping[str, str]) -> str:
    """Resolve every ``{key}`` placeholder; leftovers are an error."""
    for key, value in bindings.items():
        text = text.replace("{" + key + "}", value)
    leftover = _PLACEHOLDER_RE.findall(text)
    if leftover:
        raise ValueError(f"unresolved placeholder(s) {leftover} in {text!r}")
    return text


def _expand_ids(
    template_ids: tuple[str, ...],
    bindings: Mapping[str, str],
    downstream: tuple[str, ...],
) -> tuple[str, ...]:
    """Resolve ids; an unbound ``{system}`` fans out across downstream.

    Inside a per-system template ``system`` is already in ``bindings``
    and binds to the current SINK; in a lane-wide template (the identity
    join) a ``{system}`` source expands once per SINK system.
    """
    out: list[str] = []
    for tid in template_ids:
        if SYSTEM_PLACEHOLDER in tid and "system" not in bindings:
            out.extend(_substitute(tid, {**bindings, "system": s}) for s in downstream)
        else:
            out.append(_substitute(tid, bindings))
    return tuple(out)


def _build_population(
    template: PopulationTemplate,
    bindings: Mapping[str, str],
    downstream: tuple[str, ...],
    period: Period,
) -> Population:
    sources = tuple(
        Source(source_id=sid, role=st.role)
        for st in template.source_templates
        for sid in _expand_ids((st.source_id,), bindings, downstream)
    )
    return Population(
        population_id=_substitute(template.template_id, bindings),
        name=_substitute(template.name, bindings),
        type=template.type,
        definition=_substitute(template.definition, bindings),
        derivation_rule=DerivationRule(
            rule_text=_substitute(template.rule_text, bindings),
            source_refs=_expand_ids(template.source_refs, bindings, downstream),
        ),
        sources=sources,
        period=period,
        state=AssuranceState.DEFINED,
    )


def _build_claim(template: ClaimTemplate, bindings: Mapping[str, str]) -> Claim:
    claim_id = _substitute(template.template_id, bindings)
    population_ref = _substitute(template.population_ref, bindings)
    prefix = _substitute(template.assertion_prefix, bindings).upper()
    assertions = tuple(
        Assertion(
            assertion_id=f"{prefix}.{a.letter}",
            claim_ref=claim_id,
            type=a.type,
            predicate_text=_substitute(a.predicate_text, bindings),
            population_ref=population_ref,
        )
        for a in template.assertions
    )
    return Claim(
        claim_id=claim_id,
        statement=_substitute(template.statement, bindings),
        population_ref=population_ref,
        framework_mappings=template.framework_mappings,
        assertions=assertions,
    )


def instantiate_lane(
    template: LaneTemplate,
    systems: Mapping[str, str],
    period: Period,
) -> tuple[list[Population], list[Claim]]:
    """Instantiate a lane template with concrete systems for a period.

    ``systems`` maps every node ``system_ref`` placeholder to the
    concrete system id used in produced object ids. Returns the
    populations and claims in template declaration order; per-system
    templates expand in SINK-node declaration order. Every claim's
    ``population_ref`` must resolve to a produced population — a
    template wired to a population it never produces is an error here,
    not a downstream surprise.
    """
    refs = {n.system_ref for n in template.nodes}
    missing = sorted(refs - set(systems))
    if missing:
        raise ValueError(f"systems mapping missing node system_ref(s): {missing}")
    base_bindings = {ref: systems[ref] for ref in refs}
    downstream = tuple(systems[ref] for ref in template.sink_system_refs)
    if not downstream:
        raise ValueError(f"lane template {template.lane_id!r} declares no SINK node")

    populations: list[Population] = []
    for pt in template.population_templates:
        if pt.per_system:
            for system in downstream:
                populations.append(
                    _build_population(pt, {**base_bindings, "system": system}, downstream, period)
                )
        else:
            populations.append(_build_population(pt, base_bindings, downstream, period))

    claims: list[Claim] = []
    for ct in template.claim_templates:
        if ct.per_system:
            for system in downstream:
                claims.append(_build_claim(ct, {**base_bindings, "system": system}))
        else:
            claims.append(_build_claim(ct, base_bindings))

    produced = {p.population_id for p in populations}
    dangling = sorted({c.population_ref for c in claims if c.population_ref not in produced})
    if dangling:
        raise ValueError(f"claim population_ref(s) resolve to no produced population: {dangling}")

    return populations, claims
