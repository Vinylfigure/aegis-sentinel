"""Engagement — deterministic full-lane orchestration over fixture tenants.

Drives the REAL pipeline end to end (compile → collect → reconcile →
evaluate) for the demo engagement; consumed by
``scripts/emit_demo_artifacts.py`` and the VAL02 mutation runners
(tests/mutation/conftest.py). Verdict-path discipline applies: no LLM
import anywhere (docs/HANDOFF.md §3), no wall clock — every timestamp
comes from the engagement fixture.
"""

from aegis_sentinel.engagement.runner import (
    BREAKGLASS_SOURCE,
    SYSTEMS,
    EngagementRun,
    add_breakglass_source,
    run_demo_engagement,
)

__all__ = [
    "BREAKGLASS_SOURCE",
    "SYSTEMS",
    "EngagementRun",
    "add_breakglass_source",
    "run_demo_engagement",
]
