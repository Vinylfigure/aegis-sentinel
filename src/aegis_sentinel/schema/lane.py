"""Lane templates: ITGC process lanes as data, not code (LANE01).

PRD-v3 §2 (Process): lanes ship as templates instantiated per stack —
freeform editing is out of V1. A lane carries direction, actors,
triggers, and control points (the sketch's diamonds, rendered in
docs/prototypes/process-graph.html). The template is pure data: nodes,
edges, control points, and parameterized population/claim templates
whose ``{system}`` placeholder expands over the lane's SINK systems at
instantiation time (src/aegis_sentinel/manifest/instantiate.py).

Placeholders: ``{<system_ref>}`` for any node's system (e.g. ``{hris}``,
``{okta}``) resolves through the systems mapping passed to
``instantiate_lane``; ``{system}`` binds to the current downstream SINK
system. A template whose ``template_id`` contains ``{system}`` is
expanded once per SINK; otherwise it instantiates once (and a
``{system}`` inside its *source* templates fans out across all SINKs —
how a single relationship population joins every downstream system).

Control points sit on edges (the diamonds sit *between* systems);
``edge_refs`` is plural because a fan-out control point spans every
edge it gates (TA-3 verifies revocation on each Okta→sink edge).
"""

from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from aegis_sentinel.schema.canonical import AegisModel
from aegis_sentinel.schema.claim import AssertionType, FrameworkMapping
from aegis_sentinel.schema.population import PopulationType, SourceRole

MODULE_VERSION = "schema.lane@0.1.0"

#: The per-downstream-system placeholder in parameterized templates.
SYSTEM_PLACEHOLDER = "{system}"


class LaneNodeKind(str, Enum):
    """ACTOR originates events; SYSTEM relays; SINK is a fan-out target."""

    ACTOR = "ACTOR"
    SYSTEM = "SYSTEM"
    SINK = "SINK"


class ControlNature(str, Enum):
    """How the control operates: configuration, automation, or a human."""

    CFG = "CFG"
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class ControlFunction(str, Enum):
    """Preventative gates the flow; detective observes it after the fact."""

    PREV = "PREV"
    DET = "DET"


class LaneNode(AegisModel):
    """One system (or actor) on the lane. ``system_ref`` is generic —
    the role on the lane (``hris``), never a vendor or client name —
    and is the key the instantiation systems mapping resolves."""

    node_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    system_ref: str = Field(min_length=1)
    kind: LaneNodeKind


class LaneEdge(AegisModel):
    """A directed flow between two nodes carrying one kind of event."""

    from_node: str = Field(min_length=1)
    to_node: str = Field(min_length=1)
    event_kind: str = Field(min_length=1)

    @property
    def key(self) -> str:
        """The edge's reference key, as used by ``ControlPoint.edge_refs``."""
        return f"{self.from_node}->{self.to_node}"


class ControlPoint(AegisModel):
    """A diamond on the flow: where a control sits and what it claims.

    ``claim_template_refs`` name the claim templates this control point
    justifies — the control point *is* the reason those claims exist.
    """

    cp_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    edge_refs: tuple[str, ...] = Field(min_length=1)
    nature: ControlNature
    function: ControlFunction
    claim_template_refs: tuple[str, ...] = Field(min_length=1)


class SourceTemplate(AegisModel):
    """A parameterized population source: id may carry placeholders."""

    source_id: str = Field(min_length=1)
    role: SourceRole


class PopulationTemplate(AegisModel):
    """A parameterized Population: same shape, placeholders unresolved.

    ``source_refs`` must name declared source templates verbatim (the
    same closed-reference rule Population enforces after resolution).
    """

    template_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: PopulationType
    definition: str = Field(min_length=1)
    rule_text: str = Field(min_length=1)
    source_templates: tuple[SourceTemplate, ...] = Field(min_length=1)
    source_refs: tuple[str, ...] = Field(min_length=1)

    @property
    def per_system(self) -> bool:
        """True when the template expands once per SINK system."""
        return SYSTEM_PLACEHOLDER in self.template_id

    @model_validator(mode="after")
    def _source_refs_declared(self) -> "PopulationTemplate":
        declared = {s.source_id for s in self.source_templates}
        missing = [ref for ref in self.source_refs if ref not in declared]
        if missing:
            raise ValueError(
                "population template rule references undeclared source template(s): "
                + ", ".join(missing)
            )
        return self


class AssertionTemplate(AegisModel):
    """One lettered, typed assertion of a claim template."""

    letter: str = Field(pattern=r"^[a-z]+$")
    type: AssertionType
    predicate_text: str = Field(min_length=1)


class ClaimTemplate(AegisModel):
    """A parameterized Claim with lettered typed assertions.

    ``assertion_prefix`` becomes the id prefix after placeholder
    resolution and uppercasing (``TERM-{system}`` → ``TERM-GITHUB``),
    so instantiated ids satisfy ``ASSERTION_ID_PATTERN`` — the SCH01
    pattern is never loosened to admit template ids.
    """

    template_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    population_ref: str = Field(min_length=1)
    assertion_prefix: str = Field(pattern=r"^[A-Za-z0-9{}-]+$")
    framework_mappings: tuple[FrameworkMapping, ...] = ()
    assertions: tuple[AssertionTemplate, ...] = Field(min_length=1)

    @property
    def per_system(self) -> bool:
        """True when the template expands once per SINK system."""
        return SYSTEM_PLACEHOLDER in self.template_id

    @model_validator(mode="after")
    def _letters_unique_and_placeholders_bounded(self) -> "ClaimTemplate":
        letters = [a.letter for a in self.assertions]
        if len(letters) != len(set(letters)):
            raise ValueError(f"duplicate assertion letters in {self.template_id!r}")
        if not self.per_system:
            carriers = [
                field
                for field, text in (
                    ("population_ref", self.population_ref),
                    ("assertion_prefix", self.assertion_prefix),
                    ("statement", self.statement),
                    *(("predicate_text", a.predicate_text) for a in self.assertions),
                )
                if SYSTEM_PLACEHOLDER in text
            ]
            if carriers:
                raise ValueError(
                    f"claim template {self.template_id!r} is not per-system but "
                    f"{sorted(set(carriers))} carry {SYSTEM_PLACEHOLDER!r}"
                )
        return self


class LaneTemplate(AegisModel):
    """A whole lane as data: graph + control points + typed templates.

    Constructor-enforced closure: edges reference declared nodes,
    control points reference declared edges and claim templates, claim
    templates reference declared population templates. A template that
    names a thing it does not declare cannot be constructed — the same
    discipline Population applies to its sources.
    """

    lane_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    direction: str = Field(min_length=1)
    trigger: str = Field(min_length=1)
    nodes: tuple[LaneNode, ...] = Field(min_length=1)
    edges: tuple[LaneEdge, ...] = Field(min_length=1)
    control_points: tuple[ControlPoint, ...] = Field(min_length=1)
    population_templates: tuple[PopulationTemplate, ...] = Field(min_length=1)
    claim_templates: tuple[ClaimTemplate, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _references_closed(self) -> "LaneTemplate":
        node_ids = [n.node_id for n in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("duplicate node_id in lane template")
        declared_nodes = set(node_ids)

        edge_keys: list[str] = []
        for edge in self.edges:
            for end in (edge.from_node, edge.to_node):
                if end not in declared_nodes:
                    raise ValueError(f"edge {edge.key!r} references undeclared node {end!r}")
            edge_keys.append(edge.key)
        if len(edge_keys) != len(set(edge_keys)):
            raise ValueError("duplicate edge (same from_node->to_node) in lane template")

        cp_ids = [cp.cp_id for cp in self.control_points]
        if len(cp_ids) != len(set(cp_ids)):
            raise ValueError("duplicate cp_id in lane template")

        pop_ids = [p.template_id for p in self.population_templates]
        if len(pop_ids) != len(set(pop_ids)):
            raise ValueError("duplicate population template_id in lane template")

        claim_ids = [c.template_id for c in self.claim_templates]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("duplicate claim template_id in lane template")

        declared_edges = set(edge_keys)
        declared_claims = set(claim_ids)
        declared_pops = set(pop_ids)
        for cp in self.control_points:
            for ref in cp.edge_refs:
                if ref not in declared_edges:
                    raise ValueError(f"control point {cp.cp_id!r} references unknown edge {ref!r}")
            for ref in cp.claim_template_refs:
                if ref not in declared_claims:
                    raise ValueError(
                        f"control point {cp.cp_id!r} references unknown claim template {ref!r}"
                    )
        for claim in self.claim_templates:
            if claim.population_ref not in declared_pops:
                raise ValueError(
                    f"claim template {claim.template_id!r} references unknown "
                    f"population template {claim.population_ref!r}"
                )
        return self

    @property
    def sink_system_refs(self) -> tuple[str, ...]:
        """SINK node system_refs in declared node order (the fan-out set)."""
        return tuple(n.system_ref for n in self.nodes if n.kind is LaneNodeKind.SINK)
