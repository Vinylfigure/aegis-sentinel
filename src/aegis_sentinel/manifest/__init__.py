"""Assurance Manifest plane (minimal for LANE01; SCH03 extends this).

Holds deterministic construction of manifest inputs from lane
templates. Ratified scope snapshots, diffs, and PROPOSED_SCOPE_CHANGE
land here with SCH03. No LLM, no network — same rule as schema/.
"""

from aegis_sentinel.manifest.instantiate import instantiate_lane

__all__ = ["instantiate_lane"]
