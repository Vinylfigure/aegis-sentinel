"""TYP01 acceptance: the Okta trap — a six-month TIMING assertion against
a 90-day window fails compilation with E204 and a correct suggestion —
plus E117, E118, E302, and the zero-collectors-on-error rule."""

from datetime import UTC, datetime
from pathlib import Path

from aegis_sentinel.capability import Registry
from aegis_sentinel.compile import compile_claims
from aegis_sentinel.lanes import instantiate, load_template
from aegis_sentinel.manifest import ManifestBlocks, genesis
from aegis_sentinel.schema import EvidenceQualityContract, LifecycleState, TimeWindow

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = Registry.load(ROOT / "registry" / "capabilities")
SIX_MONTHS = TimeWindow(
    start=datetime(2026, 7, 1, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC)
)
BINDINGS = {
    "source-of-truth": "workday",
    "identity-provider": "okta",
    "code-hosting": "github",
    "cloud": "gcp",
    "messaging": "slack",
}
AT = datetime(2026, 8, 16, tzinfo=UTC)
# Grants every registry entry (draft or frozen) — a stand-in for "the manifest
# authorizes whatever the registry could ever serve", so these compiles keep
# exercising E117/E204/E302 exactly as before E118 existed; the E118-specific
# tests below build their own narrower manifest instead.
ALL_GRANTED_MANIFEST = genesis(
    ManifestBlocks(capabilities=tuple(sorted(e.id for e in REGISTRY.all()))),
    "vinylfigure (Ratifier)",
    AT,
)


def lane_instance():
    return instantiate(
        load_template(ROOT / "templates" / "lanes" / "termination.json"),
        BINDINGS,
        SIX_MONTHS,
    )


def test_six_month_timing_vs_okta_90d_fails_with_e204_and_suggestion():
    instance = lane_instance()
    okta_claims = tuple(c for c in instance.claims if c.id == "claim-cp-no-residual-access-okta")
    okta_pop = tuple(p for p in instance.populations if "okta" in p.id)
    report = compile_claims(okta_claims, okta_pop, REGISTRY, ALL_GRANTED_MANIFEST)
    e204 = [e for e in report.errors if e.code == "E204"]
    assert e204, f"expected E204, got {[e.code for e in report.errors]}"
    assert "183d" in e204[0].message and "90d event-history" in e204[0].message
    assert e204[0].suggestion is not None
    assert "workday.terminated_workers (full-history) (draft — ratify first)" in e204[0].suggestion


def test_unregistered_system_fails_with_e117_naming_the_gap():
    instance = lane_instance()
    # The full lane compiled: workday and slack systems have only DRAFT
    # entries, so their populations must E117 — with the ratification hint.
    report = compile_claims(
        tuple(instance.claims), tuple(instance.populations), REGISTRY, ALL_GRANTED_MANIFEST
    )
    e117 = [e for e in report.errors if e.code == "E117"]
    assert e117
    slack_errors = [e for e in e117 if "slack" in e.message]
    assert slack_errors and "slack.scim_users" in slack_errors[0].message
    assert "ratify it" in slack_errors[0].message


def test_zero_collectors_for_erroring_claims():
    instance = lane_instance()
    report = compile_claims(
        tuple(instance.claims), tuple(instance.populations), REGISTRY, ALL_GRANTED_MANIFEST
    )
    erroring = {e.claim_id for e in report.errors}
    planned = {p.claim_id for p in report.plans}
    assert not (erroring & planned), "a claim with unresolved E-codes got a collector plan"


def ratified_workday_registry():
    """The registry as it will look after the Owner ratifies the workday
    draft — built in-test, never by editing the on-disk registry."""
    entries = []
    for entry in REGISTRY.all():
        if entry.id == "workday.terminated_workers":
            # model_copy skips validation/coercion — pass the enum, not the
            # string, or `lifecycle is FROZEN` checks silently miss.
            entry = entry.model_copy(
                update={
                    "ratified_by": "vinylfigure (Ratifier)",
                    "lifecycle": LifecycleState.FROZEN,
                }
            )
        entries.append(entry)
    return Registry(tuple(entries))


def test_clean_state_claim_compiles_to_a_plan():
    """With workday ratified, a non-TIMING github claim compiles cleanly —
    every lane population joins against the HRIS source, so the plan
    carries both capabilities."""
    instance = lane_instance()
    github_claims = tuple(
        c for c in instance.claims if c.id == "claim-cp-no-residual-access-github"
    )
    github_pop = tuple(p for p in instance.populations if "github" in p.id)
    non_timing = tuple(
        c.model_copy(update={"assertions": tuple(a for a in c.assertions if a.type != "TIMING")})
        for c in github_claims
    )
    report = compile_claims(
        non_timing, github_pop, ratified_workday_registry(), ALL_GRANTED_MANIFEST
    )
    assert report.ok, [e.message for e in report.errors]
    assert report.plans
    assert report.plans[0].capability_ids == ("github.members", "workday.terminated_workers")


def test_e118_refuses_a_usable_capability_the_manifest_does_not_grant():
    """workday is ratified/usable, but the manifest only grants the OTHER
    capability the github claim needs — the compile must refuse, not just
    skip the manifest check because the registry was satisfied."""
    instance = lane_instance()
    github_claims = tuple(
        c for c in instance.claims if c.id == "claim-cp-no-residual-access-github"
    )
    github_pop = tuple(p for p in instance.populations if "github" in p.id)
    non_timing = tuple(
        c.model_copy(update={"assertions": tuple(a for a in c.assertions if a.type != "TIMING")})
        for c in github_claims
    )
    ungranted_manifest = genesis(
        ManifestBlocks(capabilities=("workday.terminated_workers",)),
        "vinylfigure (Ratifier)",
        AT,
    )
    report = compile_claims(non_timing, github_pop, ratified_workday_registry(), ungranted_manifest)
    e118 = [e for e in report.errors if e.code == "E118"]
    assert e118, f"expected E118, got {[e.code for e in report.errors]}"
    assert "github.members" in e118[0].message
    assert "v1" in e118[0].message
    erroring = {e.claim_id for e in report.errors}
    planned = {p.claim_id for p in report.plans}
    assert not (erroring & planned), "a claim with an ungranted capability got a collector plan"


def test_e118_absent_once_the_manifest_grants_the_capability():
    """The same claim, same registry, but the manifest now names both
    capabilities it needs — E118 must not fire, and the plan is unaffected."""
    instance = lane_instance()
    github_claims = tuple(
        c for c in instance.claims if c.id == "claim-cp-no-residual-access-github"
    )
    github_pop = tuple(p for p in instance.populations if "github" in p.id)
    non_timing = tuple(
        c.model_copy(update={"assertions": tuple(a for a in c.assertions if a.type != "TIMING")})
        for c in github_claims
    )
    report = compile_claims(
        non_timing, github_pop, ratified_workday_registry(), ALL_GRANTED_MANIFEST
    )
    assert not any(e.code == "E118" for e in report.errors), [e.message for e in report.errors]
    assert report.plans


def test_e302_on_schema_version_drift():
    instance = lane_instance()
    github_pop = next(p for p in instance.populations if "github" in p.id)
    claim = next(c for c in instance.claims if c.population_id == github_pop.id)
    non_timing = claim.model_copy(
        update={"assertions": tuple(a for a in claim.assertions if a.type != "TIMING")}
    )
    eqc = EvidenceQualityContract.model_validate_json(
        (ROOT / "tests" / "fixtures" / "ontology" / "eqc_valid.json").read_text()
    )
    drifted = eqc.model_copy(
        update={"population_ref": github_pop.id, "schema_version": "2999-01-01"}
    )
    report = compile_claims(
        (non_timing,), (github_pop,), REGISTRY, ALL_GRANTED_MANIFEST, contracts=(drifted,)
    )
    assert any(e.code == "E302" and "re-ratify or pin" in e.message for e in report.errors)
