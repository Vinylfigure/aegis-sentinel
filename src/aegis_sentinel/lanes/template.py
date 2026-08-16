"""Lane templates and their instantiation into SCH01 ontology objects.

A template speaks in *roles* (source-of-truth, identity-provider,
downstream systems); instantiation binds each role to a concrete system
and yields Populations and Claims. Control points carry assertion specs;
the assertion type constrains admissible evidence downstream (TYP01).
Pure data transformation: the period is an explicit input, never a clock.
"""

import json
from pathlib import Path

from pydantic import Field, model_validator

from aegis_sentinel.schema.enums import AssertionType, PopulationType, SourceRole
from aegis_sentinel.schema.models import (
    Assertion,
    Base,
    Claim,
    DerivationRule,
    Population,
    SourceRef,
    TimeWindow,
    TimingConstraint,
)


class LaneNode(Base):
    role: str = Field(min_length=1)
    kind: str = Field(pattern=r"^(system|actor)$")
    description: str = Field(min_length=1)


class LaneEdge(Base):
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    trigger: str = Field(min_length=1)


class AssertionSpec(Base):
    """A control point's testable attribute, template-side: everything an
    Assertion needs except the concrete system names."""

    attribute: str = Field(min_length=1)
    type: AssertionType
    description_template: str = Field(min_length=1)
    timing_days: int | None = Field(default=None, ge=1)
    timing_business_days: bool = True

    @model_validator(mode="after")
    def _timing_paired(self):
        if (self.type is AssertionType.TIMING) != (self.timing_days is not None):
            raise ValueError("timing_days is required for TIMING specs and forbidden otherwise")
        return self


class ControlPoint(Base):
    id: str = Field(min_length=1)
    at_role: str = Field(min_length=1)
    statement_template: str = Field(min_length=1)
    assertions: tuple[AssertionSpec, ...] = Field(min_length=1)
    per_downstream: bool = False


class LaneTemplate(Base):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    event_role: str = Field(min_length=1)
    event_description: str = Field(min_length=1)
    downstream_roles: tuple[str, ...] = Field(min_length=1)
    nodes: tuple[LaneNode, ...] = Field(min_length=2)
    edges: tuple[LaneEdge, ...] = Field(min_length=1)
    control_points: tuple[ControlPoint, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _graph_is_closed(self):
        roles = {n.role for n in self.nodes}
        for edge in self.edges:
            if edge.source not in roles or edge.target not in roles:
                raise ValueError(f"edge {edge.source}->{edge.target} references an unknown role")
        for cp in self.control_points:
            if cp.at_role not in roles:
                raise ValueError(f"control point {cp.id} sits at unknown role {cp.at_role}")
        if self.event_role not in roles:
            raise ValueError(f"event_role {self.event_role} is not a node")
        missing = [r for r in self.downstream_roles if r not in roles]
        if missing:
            raise ValueError(f"downstream roles not in nodes: {missing}")
        return self


class LaneInstance(Base):
    lane_id: str
    populations: tuple[Population, ...]
    claims: tuple[Claim, ...]


def load_template(path: Path) -> LaneTemplate:
    return LaneTemplate.model_validate(json.loads(path.read_text()))


def instantiate(
    template: LaneTemplate,
    bindings: dict[str, str],
    period: TimeWindow,
) -> LaneInstance:
    """Bind roles to concrete systems; emit populations + claims.

    Raises on an unbound role — a lane with a hole in it must not compile
    to a smaller scope silently (no silent N/A).
    """
    unbound = [
        role
        for role in {n.role for n in template.nodes if n.kind == "system"}
        if role not in bindings
    ]
    if unbound:
        raise ValueError(
            f"unbound lane roles: {sorted(unbound)} — "
            "a partial binding never shrinks scope silently"
        )

    event_system = bindings[template.event_role]
    event_pop = Population(
        id=f"pop-{template.id}-events",
        name=f"{template.name}: {template.event_description}",
        type=PopulationType.EVENT,
        definition=f"{template.event_description}, per the {event_system} feed",
        authoritative_source=SourceRef(
            system=event_system,
            role=SourceRole.AUTHORITATIVE,
            ref=f"{event_system}://{template.id}-events",
        ),
        period=period,
    )

    downstream_pops = tuple(
        Population(
            id=f"pop-{template.id}-{bindings[role]}-access",
            name=f"{bindings[role]} access holders",
            type=PopulationType.ENTITY,
            definition=(
                f"identities holding access in {bindings[role]}, "
                f"scope-relevant via the {template.name} lane"
            ),
            derivation_rule=DerivationRule(
                description=(
                    f"enumerate {bindings[role]} members; join against {event_system} identities"
                ),
                sources=(
                    SourceRef(
                        system=bindings[role],
                        role=SourceRole.CONTRIBUTING,
                        ref=f"{bindings[role]}://members",
                    ),
                    SourceRef(
                        system=event_system,
                        role=SourceRole.AUTHORITATIVE,
                        ref=f"{event_system}://identities",
                    ),
                ),
            ),
            period=period,
        )
        for role in template.downstream_roles
    )

    claims = []
    for cp in template.control_points:
        targets = template.downstream_roles if cp.per_downstream else (cp.at_role,)
        for role in targets:
            system = bindings[role]
            population = (
                event_pop
                if cp.at_role == template.event_role
                else next(
                    p for p in downstream_pops if p.id == f"pop-{template.id}-{system}-access"
                )
            )
            assertions = tuple(
                Assertion(
                    id=f"{cp.id}-{system}-{spec.attribute}",
                    attribute=spec.attribute,
                    type=spec.type,
                    description=spec.description_template.format(system=system),
                    timing=(
                        TimingConstraint(
                            days=spec.timing_days, business_days=spec.timing_business_days
                        )
                        if spec.type is AssertionType.TIMING
                        else None
                    ),
                )
                for spec in cp.assertions
            )
            claims.append(
                Claim(
                    id=f"claim-{cp.id}-{system}",
                    statement=cp.statement_template.format(system=system),
                    population_id=population.id,
                    assertions=assertions,
                )
            )

    return LaneInstance(
        lane_id=template.id,
        populations=(event_pop, *downstream_pops),
        claims=tuple(claims),
    )
