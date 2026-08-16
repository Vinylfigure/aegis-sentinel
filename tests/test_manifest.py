"""SCH03 acceptance: snapshots version through ratification only (D-L1),
stale proposals are refused, and the diff is human-readable."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aegis_sentinel.manifest import (
    ManifestBlocks,
    ManifestSnapshot,
    ProposedScopeChange,
    diff,
    genesis,
    ratify,
)

AT = datetime(2026, 8, 16, tzinfo=UTC)

V1_BLOCKS = ManifestBlocks(
    boundary=("commitment:soc2-2026",),
    populations=("pop-terminations-2026H2",),
    claims=("claim-am06-termination",),
    evidence_contracts=("eqc-github-members-v1",),
    capabilities=("github.members",),
    collectors=({"id": "col-github-members", "permissions": ("read:org",)},),
    tests=("tests/mutation",),
)


def proposal(base_version=1, **updates):
    blocks = V1_BLOCKS.model_copy(update=updates)
    return ProposedScopeChange(
        id="psc-001",
        base_version=base_version,
        description="add okta capability to scope",
        proposer="overlord (draft)",
        proposed_blocks=blocks,
    )


def test_genesis_requires_ratifier():
    with pytest.raises(ValueError, match="ratifier"):
        genesis(V1_BLOCKS, "  ", AT)
    v1 = genesis(V1_BLOCKS, "vinylfigure (Ratifier)", AT)
    assert v1.version == 1 and v1.lifecycle.value == "frozen"


def test_frozen_snapshot_requires_ratification_fields():
    with pytest.raises(ValidationError, match="ratified_by"):
        ManifestSnapshot(version=1, blocks=V1_BLOCKS, lifecycle="frozen")


def test_ratify_produces_next_frozen_and_supersedes_current():
    v1 = genesis(V1_BLOCKS, "vinylfigure (Ratifier)", AT)
    change = proposal(capabilities=("github.members", "okta.system_log"))
    v2, superseded = ratify(change, v1, "vinylfigure (Ratifier)", AT)
    assert v2.version == 2 and v2.lifecycle.value == "frozen"
    assert superseded.version == 1 and superseded.lifecycle.value == "superseded"
    assert v1.lifecycle.value == "frozen"  # ratify is pure; the input is untouched


def test_ratify_refuses_missing_ratifier_and_stale_base():
    v1 = genesis(V1_BLOCKS, "vinylfigure (Ratifier)", AT)
    with pytest.raises(ValueError, match="ratifier"):
        ratify(proposal(), v1, "", AT)
    with pytest.raises(ValueError, match="stale proposal"):
        ratify(proposal(base_version=7), v1, "vinylfigure (Ratifier)", AT)


def test_ratify_refuses_superseded_current():
    v1 = genesis(V1_BLOCKS, "vinylfigure (Ratifier)", AT)
    _, superseded = ratify(proposal(), v1, "vinylfigure (Ratifier)", AT)
    with pytest.raises(ValueError, match="FROZEN"):
        ratify(proposal(), superseded, "vinylfigure (Ratifier)", AT)


def test_diff_is_human_readable():
    v1 = genesis(V1_BLOCKS, "vinylfigure (Ratifier)", AT)
    change = proposal(
        capabilities=("github.members", "okta.system_log"),
        populations=(),
    )
    v2, _ = ratify(change, v1, "vinylfigure (Ratifier)", AT)
    text = diff(v1, v2)
    assert "manifest v1 -> v2" in text
    assert "+ capabilities: okta.system_log" in text
    assert "- populations: pop-terminations-2026H2" in text
