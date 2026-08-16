"""Lane collectors (COL01–05): deterministic, injected-transport, no
live-tenant calls in tests. Native code on versioned APIs is the default
verdict-path posture (HANDOFF §2 MCP ruling); no LLM or network imports
here — the purity gate sweeps this package like the rest of the verdict
path."""

from aegis_sentinel.collectors.hris import (
    COLLECTOR_VERSION,
    HrisCollection,
    HrisFeed,
    PaginationEvidence,
    TerminationRecord,
    canonical_contract_hash,
    collect_hris_terminations,
)

__all__ = [
    "COLLECTOR_VERSION",
    "HrisCollection",
    "HrisFeed",
    "PaginationEvidence",
    "TerminationRecord",
    "canonical_contract_hash",
    "collect_hris_terminations",
]
