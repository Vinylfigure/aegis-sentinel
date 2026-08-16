"""Build the demo-engagement walking skeleton:
COL01 (HRIS collector) → one claim → minimal reconcile → minimal
evaluate → one real verdict record → artifacts/demo-engagement/verdicts.json.

Deterministic by construction (D-P3): fixed period, fixed run identity,
the collected_at timestamp comes from the fixture extract itself, output
JSON is sorted-key — regenerating must be byte-identical to the
committed artifact (tests/test_demo_engagement_drift.py enforces it).

WALKING SKELETON handoff note: the web rendering half of this milestone
(`web` `/verdicts`, frontend track B3/C2 in docs/EXECUTION-PLAN.md) is
deliberately NOT built here — this artifact JSON is the contract the
frontend track consumes; nothing in the verdict path renders.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from aegis_sentinel.capability import Registry
from aegis_sentinel.collectors.hris import collect_hris_terminations
from aegis_sentinel.compile import compile_claims
from aegis_sentinel.evaluate.minimal import evaluate_existence
from aegis_sentinel.lanes import instantiate, load_template
from aegis_sentinel.reconcile.minimal import Member, apply_dispositions, reconcile_population
from aegis_sentinel.schema import (
    Assertion,
    AssertionType,
    AssuranceState,
    Claim,
    DispositionRecord,
    LifecycleState,
    TimeWindow,
    advance,
)

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "collectors"
OUT = ROOT / "artifacts" / "demo-engagement" / "verdicts.json"

# The reference engagement period — the same six months the lane tests
# compile against (183 days, 2026-07-01 → 2026-12-31).
PERIOD = TimeWindow(start=datetime(2026, 7, 1, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC))
BINDINGS = {
    "source-of-truth": "workday",
    "identity-provider": "okta",
    "code-hosting": "github",
    "cloud": "gcp",
    "messaging": "slack",
}
TENANT = "meridian-financial-fixtures"
# Fixed run identity + the fixture's own extract time: no clocks, no ids
# generated here (D-P3) — same inputs, byte-identical artifact.
RUN_ID = "run-demo-engagement-0001"
RECORD_ID = "vr-demo-engagement-0001"
COLLECTED_AT = "2026-12-31T23:59:59Z"
CONTROL_ID = "AM-06"  # the termination lane's canonical control (HANDOFF §1)
SPEC_ID = "spec-hris-terminations-v1"


def demo_registry() -> Registry:
    """The registry as it will look AFTER the Owner ratifies the workday draft.

    ==================================================================
    DEMO-ONLY RATIFICATION — NOT THE REAL THING.
    The on-disk entry registry/capabilities/workday.terminated_workers.json
    stays DRAFT: ratification is a manual-by-design human act (HANDOFF §3,
    invariant 6) and belongs to the Owner alone — it is tracked as an open
    Owner item in the issue tracker, and this script must never perform or
    persist it. Like tests/test_type_checker.py::ratified_workday_registry,
    we build a test-ratified copy in memory only, so the compile gate can be
    exercised end-to-end without forging a ratification on disk.
    ==================================================================
    """
    entries = []
    for entry in Registry.load(ROOT / "registry" / "capabilities").all():
        if entry.id == "workday.terminated_workers":
            # model_copy skips validation/coercion — pass the LifecycleState
            # enum, not the string, or `lifecycle is FROZEN` checks silently miss.
            entry = entry.model_copy(
                update={
                    "ratified_by": "vinylfigure (Ratifier)",
                    "lifecycle": LifecycleState.FROZEN,
                }
            )
        entries.append(entry)
    return Registry(tuple(entries))


def build() -> str:
    """Run the full pipeline over the fixtures; return the artifact text."""
    template = load_template(ROOT / "templates" / "lanes" / "termination.json")
    instance = instantiate(template, BINDINGS, PERIOD)
    population = next(p for p in instance.populations if p.id == "pop-termination-events")

    # The one claim: an EXISTENCE assertion over the collected records.
    claim = Claim(
        id="claim-am06-termination-existence",
        statement=(
            "every termination effective in the period exists as a record "
            "in the authoritative HRIS feed"
        ),
        population_id=population.id,
        assertions=(
            Assertion(
                id="am06-hris-existence-A",
                attribute="A",
                type=AssertionType.EXISTENCE,
                description=(
                    "a termination record exists in the HRIS feed for every "
                    "canonical member of the reconciled termination population"
                ),
            ),
        ),
        framework_refs=("SOC2 AM-06",),
    )

    registry = demo_registry()

    # Compile gate #1 — BEFORE the collector runs: zero collectors are
    # executable for a claim with unresolved E-codes (TYP01 contract).
    report = compile_claims((claim,), (population,), registry)
    if not report.ok:
        raise SystemExit(
            "compile gate failed before collection: "
            + "; ".join(f"{e.code} {e.message}" for e in report.errors)
        )

    fixture = FIXTURES / "hris_terminations.json"
    collection = collect_hris_terminations(
        fixture.read_bytes,
        tenant=TENANT,
        period=PERIOD,
        population_ref=population.id,
    )

    # Compile gate #2 — with the emitted evidence contract, so schema-version
    # drift (E302) is caught before any verdict is recorded.
    report = compile_claims((claim,), (population,), registry, contracts=(collection.contract,))
    if not report.ok:
        raise SystemExit(
            "compile gate failed on the evidence contract: "
            + "; ".join(f"{e.code} {e.message}" for e in report.errors)
        )

    # Ladder: the lane defined the population; the collector discovered it.
    population = advance(population, AssuranceState.DEFINED)
    population = advance(population, AssuranceState.DISCOVERED)

    # Minimal reconciliation: HRIS feed (authoritative) vs offboarding
    # tracker (contributing), canonical identity by email.
    left = tuple(Member(ref=f"worker:{r.worker_id}", email=r.email) for r in collection.records)
    tracker = json.loads((FIXTURES / "offboarding_tracker.json").read_text())
    right = tuple(Member(ref=f"ticket:{t['ticket']}", email=t["email"]) for t in tracker["tickets"])
    result = reconcile_population(population, left, right)

    dispositions = {
        ref: DispositionRecord.model_validate(data)
        for ref, data in json.loads((FIXTURES / "dispositions.json").read_text()).items()
    }
    population = apply_dispositions(result.population, dispositions)
    # DISCOVERED→RECONCILED only passes because every delta is dispositioned.
    population = advance(population, AssuranceState.RECONCILED)

    record = evaluate_existence(
        claim=claim,
        population=population,
        canonical_members=result.canonical_members,
        records=collection.records,
        contract=collection.contract,
        control_id=CONTROL_ID,
        record_id=RECORD_ID,
        run_id=RUN_ID,
        collected_at=COLLECTED_AT,
        spec_id=SPEC_ID,
        spec_hash=collection.contract.contract_hash,
        source="hris-termination-collector",
        source_version=collection.contract.collector_version,
        completeness_ref=f"reconciliations/{population.id}.json",
        evidence_refs=(
            f"tests/fixtures/collectors/hris_terminations.json#sha256={collection.raw_sha256}",
        ),
        chain_prev=None,  # first record in the chain
        support_record_hashes=(collection.raw_sha256,),
    )
    return json.dumps([record], indent=2, sort_keys=True) + "\n"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build())
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
