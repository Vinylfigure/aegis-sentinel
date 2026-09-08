"""Instantiate the acme-live Lane A (termination) claim + population
(issue #153, Deliverable 3 slice of #122).

Issue #123/PR #127 scaffolded `test-environments/acme-live/{ground-truth,
identities,scenarios,config.example}.yaml` — data and docs only, with
"adapters/registry/CLI wiring" explicitly deferred. Nothing in
`src/aegis_sentinel/` has read that data since. This script is the first
consumer: it reuses the same `load_template`/`instantiate` mechanism the
demo engagement (`scripts/build_demo_engagement.py`) and LANE01/LANE02
already exercise, bound against acme-live's own systems (Merge/Okta/
GitHub/GCP/Slack), proving the termination lane template applies here too.

It then builds the one population + claim this slice needs: a population
enumerated from the acme-live identity roster, and the Lane A claim
`scenarios.yaml` already names by id
(`terminated_access_revoked_within_5_business_days`).

No collector/adapter calls: `identities.yaml`/`ground-truth.yaml` are
treated as if they were already-reconciled input, since no live Merge/
Okta/GitHub adapters exist yet (that gap is separate follow-on scope, see
#142/#144). This slice only proves the claim/population *shape*
instantiates correctly from the acme-live data — no reconciliation, no
evaluation, no verdict.
"""

from datetime import UTC, datetime
from pathlib import Path

import yaml

from aegis_sentinel.lanes import LaneInstance, instantiate, load_template
from aegis_sentinel.schema import (
    Assertion,
    AssertionType,
    Claim,
    DerivationRule,
    Population,
    PopulationType,
    SourceRef,
    SourceRole,
    TimeWindow,
    TimingConstraint,
)

ROOT = Path(__file__).resolve().parent.parent
ACME_LIVE = ROOT / "test-environments" / "acme-live"
TEMPLATE_PATH = ROOT / "templates" / "lanes" / "termination.json"

# Same reference period as the demo engagement (scripts/build_demo_engagement.py)
# — an explicit input, never a clock (D-P3).
PERIOD = TimeWindow(start=datetime(2026, 7, 1, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC))

# acme-live's own systems, per test-environments/acme-live/README.md's
# provisioning list and identities.yaml's field names (merge_employment_status,
# okta_status, github_login) — same role set the demo engagement binds,
# different concrete systems.
BINDINGS = {
    "source-of-truth": "merge",
    "identity-provider": "okta",
    "code-hosting": "github",
    "cloud": "gcp",
    "messaging": "slack",
}

# The exact claim id scenarios.yaml's lane_a_termination block already names.
CLAIM_ID = "terminated_access_revoked_within_5_business_days"
POPULATION_ID = "pop-acme-live-termination-roster"


# The one identity category identities.yaml itself documents as never
# entering the termination population (alice: "Active employee — negative
# control, never enters the termination population"). Every other category,
# including the three ratified-exclusion ones (service_account, break_glass,
# board_advisor), is a real termination-lane event that a later disposition
# rules out — only this category was never an event to begin with.
NEGATIVE_CONTROL_CATEGORY = "active_employee"


def load_acme_identities() -> dict[str, dict]:
    """The acme-live identity roster, parsed straight off disk — never
    hand-copied into a literal list."""
    data = yaml.safe_load((ACME_LIVE / "identities.yaml").read_text())
    return data["identities"]


def acme_live_identity_ids() -> tuple[str, ...]:
    """The termination-lane population: every roster identity except the
    negative control, keyed off identities.yaml's own `category` field —
    never a hand-picked name."""
    identities = load_acme_identities()
    return tuple(
        sorted(
            identity_id
            for identity_id, record in identities.items()
            if record.get("category") != NEGATIVE_CONTROL_CATEGORY
        )
    )


def build() -> tuple[LaneInstance, Population, Claim]:
    """Bind the termination lane template against acme-live's systems, and
    build the roster population + Lane A claim over it."""
    template = load_template(TEMPLATE_PATH)
    instance = instantiate(template, BINDINGS, PERIOD)

    roster = acme_live_identity_ids()
    population = Population(
        id=POPULATION_ID,
        name="Acme Corp Lane A identity roster",
        type=PopulationType.ENTITY,
        definition=(
            "every identity recorded in the acme-live roster except the "
            f"{NEGATIVE_CONTROL_CATEGORY!r} negative control, in scope for the "
            "termination-access claim"
        ),
        derivation_rule=DerivationRule(
            description=(
                "enumerate every identity in the acme-live roster whose category "
                f"is not {NEGATIVE_CONTROL_CATEGORY!r}"
            ),
            sources=(
                SourceRef(
                    system="acme-live-identities",
                    role=SourceRole.AUTHORITATIVE,
                    ref="test-environments/acme-live/identities.yaml",
                ),
            ),
        ),
        period=PERIOD,
        size=len(roster),
    )

    claim = Claim(
        id=CLAIM_ID,
        statement=(
            "every terminated Acme Corp identity had downstream access revoked "
            "within 5 business days of termination"
        ),
        population_id=population.id,
        assertions=(
            Assertion(
                id=f"{CLAIM_ID}-A",
                attribute="A",
                type=AssertionType.TIMING,
                description=(
                    "downstream access revocation occurred within 5 business days "
                    "of the Merge HRIS termination event"
                ),
                timing=TimingConstraint(days=5, business_days=True),
            ),
        ),
        framework_refs=("SOC2 AM-06",),
    )

    return instance, population, claim


def main() -> None:
    instance, population, claim = build()
    print(
        f"lane instance {instance.lane_id}: {len(instance.populations)} populations, "
        f"{len(instance.claims)} template claims"
    )
    print(f"acme-live population {population.id}: size={population.size}")
    print(f"acme-live claim {claim.id}: {claim.statement}")


if __name__ == "__main__":
    main()
