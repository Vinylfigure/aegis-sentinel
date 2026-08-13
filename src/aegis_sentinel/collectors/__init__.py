"""Collectors — the deterministic retrieval lane (COL01+; PRD-v3 §4).

Collectors retrieve per evidence contract, hash, and record; they never
interpret, summarize, or decide. No LLM import anywhere in this package
(docs/HANDOFF.md §3); enforced by tests/test_verdict_path_purity.py.
"""

from aegis_sentinel.collectors.base import (
    CollectionSnapshot,
    Collector,
    FixtureTransport,
    PageRequest,
    Transport,
    supported_assertion_types,
)
from aegis_sentinel.collectors.gcp import GcpIamBindingsCollector, IamBinding
from aegis_sentinel.collectors.github import (
    GithubAccount,
    GithubAuditEvent,
    GithubAuditLogCollector,
    GithubOrgMembersCollector,
)
from aegis_sentinel.collectors.hris import (
    HrisTerminationsCollector,
    TerminationEvent,
)
from aegis_sentinel.collectors.okta import (
    OktaLogEvent,
    OktaSystemLogCollector,
    OktaUser,
    OktaUsersCollector,
)
from aegis_sentinel.collectors.slack import SlackUser, SlackUsersCollector

__all__ = [
    # base
    "PageRequest",
    "Transport",
    "FixtureTransport",
    "CollectionSnapshot",
    "Collector",
    "supported_assertion_types",
    # hris (COL01)
    "HrisTerminationsCollector",
    "TerminationEvent",
    # okta (COL02)
    "OktaUsersCollector",
    "OktaSystemLogCollector",
    "OktaUser",
    "OktaLogEvent",
    # github (COL03)
    "GithubOrgMembersCollector",
    "GithubAuditLogCollector",
    "GithubAccount",
    "GithubAuditEvent",
    # gcp (COL04)
    "GcpIamBindingsCollector",
    "IamBinding",
    # slack (COL05)
    "SlackUsersCollector",
    "SlackUser",
]
