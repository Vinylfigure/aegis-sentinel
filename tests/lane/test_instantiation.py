"""LANE01: the termination lane template as data + deterministic instantiation.

Acceptance (docs/HANDOFF.md §4): the lane template (nodes, edges,
control points) is data, not code; instantiating it with the five
fixture systems produces the populations and claims the compiler
consumes. Determinism is part of the contract: two instantiations are
identical, object for object.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from aegis_sentinel.manifest import instantiate_lane
from aegis_sentinel.schema import (
    AssertionType,
    AssuranceState,
    LaneNodeKind,
    LaneTemplate,
    Period,
    PopulationType,
    SourceRole,
    canonical_json,
    sha256_canonical,
)

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = ROOT / "templates" / "lanes" / "termination.json"

#: The five fixture systems (PRD-v3 §6), keyed by node system_ref.
SYSTEMS = {"hris": "hris", "okta": "okta", "github": "github", "gcp": "gcp", "slack": "slack"}
DOWNSTREAM = ("github", "gcp", "slack")
PERIOD = Period(start=date(2026, 1, 1), end=date(2026, 6, 30))


@pytest.fixture(scope="module")
def template() -> LaneTemplate:
    return LaneTemplate.model_validate_json(TEMPLATE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def instantiated(template: LaneTemplate):
    return instantiate_lane(template, SYSTEMS, PERIOD)


def test_template_file_validates(template: LaneTemplate) -> None:
    assert template.lane_id == "TA"
    assert [n.system_ref for n in template.nodes] == ["hris", "okta", "github", "gcp", "slack"]
    assert template.sink_system_refs == DOWNSTREAM
    assert template.nodes[0].kind is LaneNodeKind.ACTOR
    assert [cp.cp_id for cp in template.control_points] == ["TA-1", "TA-2", "TA-3"]


def test_template_roundtrip(template: LaneTemplate) -> None:
    revived = LaneTemplate.model_validate_json(template.model_dump_json())
    assert revived == template
    assert sha256_canonical(revived) == sha256_canonical(template)
    # The committed file itself round-trips: file JSON == model dump.
    on_disk = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    assert canonical_json(on_disk) == canonical_json(template.model_dump(mode="json"))


def test_population_counts_and_types(instantiated) -> None:
    populations, _ = instantiated
    assert [p.population_id for p in populations] == [
        "TERM.terminations",
        "TERM.github.accounts",
        "TERM.gcp.accounts",
        "TERM.slack.accounts",
        "TERM.identity-join",
    ]
    by_id = {p.population_id: p for p in populations}
    assert by_id["TERM.terminations"].type is PopulationType.EVENT
    for system in DOWNSTREAM:
        assert by_id[f"TERM.{system}.accounts"].type is PopulationType.ENTITY
    assert by_id["TERM.identity-join"].type is PopulationType.RELATIONSHIP
    assert all(p.state is AssuranceState.DEFINED for p in populations)
    assert all(p.period == PERIOD for p in populations)


def test_event_population_derives_from_hris_authoritative(instantiated) -> None:
    populations, _ = instantiated
    events = next(p for p in populations if p.population_id == "TERM.terminations")
    roles = {s.source_id: s.role for s in events.sources}
    assert roles["hris-termination-feed"] is SourceRole.AUTHORITATIVE
    assert events.derivation_rule.source_refs == ("hris-termination-feed",)


def test_entity_populations_include_local_and_group_derived(instantiated) -> None:
    populations, _ = instantiated
    for system in DOWNSTREAM:
        pop = next(p for p in populations if p.population_id == f"TERM.{system}.accounts")
        assert "local" in pop.definition
        assert "group membership" in pop.definition
        roles = {s.source_id: s.role for s in pop.sources}
        assert roles[f"{system}-account-inventory"] is SourceRole.AUTHORITATIVE
        assert roles["okta-group-assignments"] is SourceRole.CONTRIBUTING


def test_identity_join_fans_out_across_downstream(instantiated) -> None:
    populations, _ = instantiated
    join = next(p for p in populations if p.population_id == "TERM.identity-join")
    source_ids = {s.source_id for s in join.sources}
    assert source_ids == {
        "hris-termination-feed",
        "okta-system-log",
        "github-account-inventory",
        "gcp-account-inventory",
        "slack-account-inventory",
    }
    assert set(join.derivation_rule.source_refs) == source_ids


def test_claim_counts_and_assertion_ids(instantiated) -> None:
    _, claims = instantiated
    assert [c.claim_id for c in claims] == [
        "TERM.feed-completeness",
        "TERM.timely-revocation",
        "TERM.github.no-residual-access",
        "TERM.gcp.no-residual-access",
        "TERM.slack.no-residual-access",
    ]
    assert sum(len(c.assertions) for c in claims) == 6
    by_id = {c.claim_id: c for c in claims}
    assert [a.assertion_id for a in by_id["TERM.feed-completeness"].assertions] == [
        "TERM-FEED.a",
        "TERM-FEED.b",
    ]
    for system in DOWNSTREAM:
        claim = by_id[f"TERM.{system}.no-residual-access"]
        assert [a.assertion_id for a in claim.assertions] == [f"TERM-{system.upper()}.a"]
        assert claim.population_ref == f"TERM.{system}.accounts"


def test_assertion_types_match_control_point_kinds(template: LaneTemplate, instantiated) -> None:
    """TA-1 → AGGREGATE/EXISTENCE · TA-2 → TIMING · TA-3 → NON_EXISTENCE."""
    _, claims = instantiated
    expected = {
        "TA-1": {AssertionType.AGGREGATE, AssertionType.EXISTENCE},
        "TA-2": {AssertionType.TIMING},
        "TA-3": {AssertionType.NON_EXISTENCE},
    }
    for cp in template.control_points:
        claim_ids = set()
        for ref in cp.claim_template_refs:
            if "{system}" in ref:
                claim_ids.update(ref.replace("{system}", s) for s in DOWNSTREAM)
            else:
                claim_ids.add(ref)
        got = {a.type for c in claims if c.claim_id in claim_ids for a in c.assertions}
        assert got == expected[cp.cp_id], f"{cp.cp_id}: {got}"


def test_timing_assertion_says_five_business_days(instantiated) -> None:
    _, claims = instantiated
    timing = next(c for c in claims if c.claim_id == "TERM.timely-revocation")
    (assertion,) = timing.assertions
    assert assertion.type is AssertionType.TIMING
    assert "five business days" in assertion.predicate_text


def test_every_claim_population_ref_is_produced(instantiated) -> None:
    populations, claims = instantiated
    produced = {p.population_id for p in populations}
    for claim in claims:
        assert claim.population_ref in produced
        for assertion in claim.assertions:
            assert assertion.population_ref in produced


def test_instantiation_is_deterministic(template: LaneTemplate) -> None:
    first = instantiate_lane(template, SYSTEMS, PERIOD)
    second = instantiate_lane(template, SYSTEMS, PERIOD)
    assert first == second
    for a, b in zip(first[0] + first[1], second[0] + second[1], strict=True):
        assert sha256_canonical(a) == sha256_canonical(b)


def test_missing_system_mapping_is_an_error(template: LaneTemplate) -> None:
    partial = {k: v for k, v in SYSTEMS.items() if k != "slack"}
    with pytest.raises(ValueError, match="slack"):
        instantiate_lane(template, partial, PERIOD)
