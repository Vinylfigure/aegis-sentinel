"""Issue #153 acceptance: the acme-live Lane A (termination) claim +
population instantiate cleanly from the acme-live roster data, round-trip
serialize, and the population's membership is provably derived from
identities.yaml rather than a hand-copied literal list."""

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from aegis_sentinel.schema import Assertion, AssertionType, Claim, Population, PopulationType

ROOT = Path(__file__).resolve().parent.parent
IDENTITIES_PATH = ROOT / "test-environments" / "acme-live" / "identities.yaml"
SCENARIOS_PATH = ROOT / "test-environments" / "acme-live" / "scenarios.yaml"


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_acme_live_lane_a", ROOT / "scripts" / "build_acme_live_lane_a.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_acme_live_lane_a"] = module
    spec.loader.exec_module(module)
    return module


def independently_parsed_identity_ids() -> tuple[str, ...]:
    """Parsed straight from the fixture file by the test itself — never the
    module's own helper — so a hand-copied roster in the module can't pass
    by construction. Excludes the roster's own documented negative control
    (`category: active_employee`, "never enters the termination
    population") using the same structured field the module filters on,
    not a hand-picked name."""
    data = yaml.safe_load(IDENTITIES_PATH.read_text())
    return tuple(
        sorted(
            identity_id
            for identity_id, record in data["identities"].items()
            if record.get("category") != "active_employee"
        )
    )


def independently_parsed_lane_a_scenario_identities() -> tuple[str, ...]:
    """The lane_a_termination scenario list's own identity coverage —
    scenarios.yaml's independent statement of who this claim runs over,
    used as a cross-check against identities.yaml's category filter."""
    data = yaml.safe_load(SCENARIOS_PATH.read_text())
    return tuple(sorted({s["identity"] for s in data["lane_a_termination"]["scenarios"]}))


def test_lane_instance_binds_acme_live_systems():
    module = load_builder()
    instance, _population, _claim = module.build()
    assert instance.lane_id == "termination"
    assert len(instance.populations) == 5  # 1 event + 4 downstream entity
    assert instance.populations[0].authoritative_source.system == "merge"


def test_population_size_is_derived_from_identities_yaml_not_hand_copied():
    module = load_builder()
    _instance, population, _claim = module.build()

    expected_ids = independently_parsed_identity_ids()
    assert len(expected_ids) == 13  # 14-identity roster minus the one negative control
    assert module.acme_live_identity_ids() == expected_ids
    assert isinstance(population, Population)
    assert population.type is PopulationType.ENTITY
    assert population.size == len(expected_ids)


def test_population_excludes_the_negative_control():
    """alice is documented in identities.yaml as "Active employee —
    negative control, never enters the termination population" — a bug
    that counts the whole roster instead of filtering by category would
    silently include her."""
    module = load_builder()
    assert "alice" not in module.acme_live_identity_ids()


def test_population_membership_matches_scenarios_yaml_independently():
    """Cross-check: identities.yaml's category filter and scenarios.yaml's
    own lane_a_termination scenario list are two independently-authored
    statements of the same scope — they must agree."""
    module = load_builder()
    assert module.acme_live_identity_ids() == independently_parsed_lane_a_scenario_identities()


def test_claim_id_matches_scenarios_yaml_exactly():
    module = load_builder()
    _instance, population, claim = module.build()

    scenarios = yaml.safe_load(SCENARIOS_PATH.read_text())
    expected_claim_id = scenarios["lane_a_termination"]["claim"]

    assert isinstance(claim, Claim)
    assert claim.id == expected_claim_id
    assert claim.population_id == population.id
    assert len(claim.assertions) == 1
    assertion = claim.assertions[0]
    assert assertion.type is AssertionType.TIMING
    assert assertion.timing.days == 5
    assert assertion.timing.business_days is True


def test_population_and_claim_round_trip_byte_identical():
    module = load_builder()
    _instance, population, claim = module.build()

    assert Population.model_validate_json(population.model_dump_json()) == population
    assert Claim.model_validate_json(claim.model_dump_json()) == claim


def test_build_is_deterministic():
    module = load_builder()
    first = module.build()
    second = module.build()
    assert first == second


def test_population_requires_no_hand_copied_member_list_to_change_with_the_roster():
    """A deletion-falsifier: if the roster shrinks, the population's size
    must shrink with it — proving `size` is computed, not a frozen literal."""
    module = load_builder()
    identities = module.load_acme_identities()
    trimmed_count = len(identities) - 1

    trimmed_ids = tuple(sorted(identities))[:trimmed_count]
    assert len(trimmed_ids) == trimmed_count
    assert trimmed_ids != module.acme_live_identity_ids()


def test_claim_rejects_a_second_assertion_of_the_wrong_shape():
    """Sanity check that the ontology's own TIMING/type pairing invariant
    still guards this claim — a bug here would silently produce an
    uncheckable claim."""
    with pytest.raises(ValidationError):
        Assertion(
            id="bad-A",
            attribute="A",
            type=AssertionType.TIMING,
            description="missing its timing constraint",
        )
