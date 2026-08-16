"""Process-lane templates (LANE01). Lanes ship as data, not code — the
template names roles; instantiation binds roles to concrete systems and
emits the populations and claims the compiler consumes. Freeform lane
editing is a non-goal (PRD-v3 §5): templates only in V1."""

from aegis_sentinel.lanes.template import (
    ControlPoint,
    LaneEdge,
    LaneInstance,
    LaneNode,
    LaneTemplate,
    instantiate,
    load_template,
)

LANE_MODELS = (LaneTemplate,)

__all__ = [
    "ControlPoint",
    "LaneEdge",
    "LaneInstance",
    "LaneNode",
    "LaneTemplate",
    "LANE_MODELS",
    "instantiate",
    "load_template",
]
