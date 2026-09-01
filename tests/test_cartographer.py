"""CAP10 acceptance (docs/DECISIONS.md D7): the Cartographer proposes
capability entries with citations from an allowlisted doc set; proposals
are drafts; it cannot probe; it cannot ratify."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from aegis_sentinel.capability import (
    AccessMode,
    CartographerRefusal,
    Pagination,
    TemporalCoverage,
    YieldedPopulation,
    is_allowed_citation,
    propose_entry,
)
from aegis_sentinel.schema.enums import LifecycleState

REGISTRY_DIR = Path(__file__).resolve().parent.parent / "registry" / "capabilities"


def _github_audit_log_kwargs(
    citations: tuple[str, ...], history_caveats: tuple[str, ...] = ()
) -> dict:
    return dict(
        id="github.audit_log",
        system="github",
        surface="REST GET /orgs/{org}/audit-log (Enterprise Cloud)",
        access_modes=(AccessMode.DIRECT_API,),
        populations_yielded=(
            YieldedPopulation(
                type="event",
                description="org audit events incl. member removal (org.remove_member)",
                attributes=("action", "actor", "user", "created_at"),
            ),
        ),
        temporal=TemporalCoverage(kind="event-history", window_days=180),
        join_keys=("login",),
        auth_scope="read:audit_log (fine-grained: 'Administration' org permission, read)",
        pagination=Pagination(
            method="cursor", exhaustion_method="follow Link rel=next until absent"
        ),
        citations=citations,
        researched_by="vinylfigure",
        researched_at=datetime(2026, 8, 16, tzinfo=UTC),
        history_caveats=history_caveats,
    )


@pytest.mark.parametrize(
    ("system", "citation", "expected"),
    [
        ("github", "https://docs.github.com/en/enterprise-cloud@latest/rest/orgs/audit-log", True),
        ("github", "https://docs.github.com.evil.example/phishing", False),
        ("github", "https://evil.example/docs.github.com", False),
        ("gcp", "https://cloud.google.com/iam/docs/service-accounts", True),
        ("okta", "https://help.okta.com/en-us/content/topics/security/system-log", True),
        ("okta", "https://developer.okta.com/docs/reference/api/system-log/", True),
        ("okta", "https://okta.com/blog/system-log", False),
        ("slack", "https://api.slack.com/scim", True),
        ("slack", "https://slack.com/help/articles/scim-provisioning", True),
        ("slack", "https://subdomain.slack.com/help/x", True),
        ("slack", "https://slack.com/legal/terms", False),
        ("slack", "https://slack.com/pricing", False),
        ("slack", "https://slack.com", False),
        ("workday", "https://community.workday.com/anything", False),
        ("workday", "https://workday.com/en-us/products.html", False),
        ("made-up-system", "https://docs.github.com/x", False),
    ],
)
def test_d7_allowlist_by_vendor_first_party_domain(system: str, citation: str, expected: bool):
    assert is_allowed_citation(system, citation) is expected


def test_workday_has_no_allowed_domain_v1():
    """D7 rule 2: Workday's docs sit behind Community auth a sandboxed
    session can't reach — every Workday citation fails the allowlist until
    the Owner supplies excerpts directly, regardless of domain."""
    assert not is_allowed_citation("workday", "https://doc.workday.com/anything")


def test_propose_entry_with_allowed_citations_is_draft():
    entry = propose_entry(
        **_github_audit_log_kwargs(
            citations=("https://docs.github.com/en/enterprise-cloud@latest/rest/orgs/audit-log",)
        )
    )
    assert entry.lifecycle is LifecycleState.DRAFT
    assert entry.ratified_by is None


def test_propose_entry_refuses_disallowed_citation_without_a_caveat():
    with pytest.raises(CartographerRefusal, match="D7 allowlist"):
        propose_entry(**_github_audit_log_kwargs(citations=("https://evil.example/fake-docs",)))


def test_propose_entry_allows_disallowed_citation_when_gap_is_named():
    """D7 rule 3: a disallowed/unreachable source may still be recorded as
    a secondary-source note, but only alongside a caveat naming the gap —
    exactly the shape already on-disk for github.audit_log."""
    entry = propose_entry(
        **_github_audit_log_kwargs(
            citations=("https://evil.example/fake-docs",),
            history_caveats=(
                "DRAFT: docs.github.com audit-log reference unreachable through this "
                "session's proxy (404) — source_unreachable, non-ratifiable secondary "
                "note only",
            ),
        )
    )
    assert entry.lifecycle is LifecycleState.DRAFT


def test_propose_entry_reproduces_the_on_disk_github_audit_log_entry():
    """Fidelity check: feeding propose_entry() the exact citations and
    caveat already ratified-as-draft on disk yields a byte-identical
    CapabilityEntry (id excluded from comparison only by construction --
    it's supplied explicitly, not derived)."""
    on_disk = (REGISTRY_DIR / "github.audit_log.json").read_text()
    from aegis_sentinel.capability import CapabilityEntry

    disk_entry = CapabilityEntry.model_validate_json(on_disk)
    proposed = propose_entry(
        **_github_audit_log_kwargs(
            citations=disk_entry.provenance.citations,
            history_caveats=disk_entry.history_caveats,
        )
    )
    assert proposed == disk_entry


def test_propose_entry_has_no_ratify_lever():
    """cannot ratify: no keyword lets a caller set ratified_by or a
    non-DRAFT lifecycle -- that's a TypeError, not a runtime refusal."""
    kwargs = _github_audit_log_kwargs(
        citations=("https://docs.github.com/en/enterprise-cloud@latest/rest/orgs/audit-log",)
    )
    with pytest.raises(TypeError):
        propose_entry(ratified_by="vinylfigure (Ratifier)", **kwargs)
    with pytest.raises(TypeError):
        propose_entry(lifecycle="frozen", **kwargs)


def test_cartographer_module_does_not_import_collectors():
    """cannot probe, structurally: the Cartographer's source never
    references the collector package that talks to live tenants."""
    import ast

    from aegis_sentinel.capability import cartographer

    tree = ast.parse(Path(cartographer.__file__).read_text())
    assert not any(
        isinstance(node, ast.ImportFrom) and node.module and "collectors" in node.module
        for node in ast.walk(tree)
    )
