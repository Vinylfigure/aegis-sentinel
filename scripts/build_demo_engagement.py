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

VAL02 second entrypoint (`python scripts/build_demo_engagement.py
poisons`): runs the six poison cases of PRD-v3 §6 through the same real
pipeline over tests/fixtures/poisons/ and writes
artifacts/demo-engagement/{poisons,reconciliation,registry,contracts,snapshot}.json
(drift-tested byte-for-byte by tests/test_poison_suite.py). contracts.json
is Q14's EvidenceQualityContracts, keyed by contract_hash — the same
objects every collector already builds in memory, previously dropped at
serialization (each verdict record's spec_hash IS a key into this map).
snapshot.json is Q16's ratified ManifestSnapshot (see SNAPSHOT_RATIFIER
below) — its populations/claims/capabilities cite ids that also appear in
the other artifacts. The default invocation still writes only
verdicts.json, byte-identical to before.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from aegis_sentinel.capability import Registry
from aegis_sentinel.collectors.gcp_service_accounts import collect_gcp_service_accounts
from aegis_sentinel.collectors.github_members import collect_github_members
from aegis_sentinel.collectors.hris import collect_hris_terminations
from aegis_sentinel.collectors.okta_system_log import collect_okta_deactivations
from aegis_sentinel.compile import compile_claims
from aegis_sentinel.evaluate.minimal import evaluate_existence
from aegis_sentinel.evaluate.typed import MemberTimeline, evaluate_non_existence, evaluate_timing
from aegis_sentinel.lanes import instantiate, load_template
from aegis_sentinel.manifest import CollectorGrant, ManifestBlocks, genesis
from aegis_sentinel.reconcile.engine import (
    BoundaryExclusion,
    SourceMember,
    SourceSet,
    reconcile_sets,
)
from aegis_sentinel.reconcile.minimal import (
    Member,
    apply_dispositions,
    canonical_email,
    reconcile_population,
)
from aegis_sentinel.schema import (
    Assertion,
    AssertionType,
    AssuranceState,
    Claim,
    Delta,
    DerivationRule,
    DispositionRecord,
    LifecycleState,
    Population,
    PopulationType,
    SourceRef,
    SourceRole,
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


# ---------------------------------------------------------------------------
# VAL02 — the six poison cases (PRD-v3 §6) through the SAME real pipeline:
# lane instantiation → compile gate → collectors over the poisoned fixture
# tenant → reconcile_sets → typed evaluator. Deterministic like build():
# fixed run identity, fixture-borne timestamps, sorted-key JSON.
# ---------------------------------------------------------------------------

POISONS = ROOT / "tests" / "fixtures" / "poisons"
# 77-day collection window, deliberately inside the Okta System Log 90-day
# history caveat so the lane's TIMING claim compiles honestly — the
# six-month period is the E204 trap, exercised in tests/test_type_checker.py.
POISON_PERIOD = TimeWindow(
    start=datetime(2026, 10, 15, tzinfo=UTC), end=datetime(2026, 12, 31, tzinfo=UTC)
)
POISON_TENANT = "meridian-financial-poisons"
POISON_PROJECT = "meridian-prod-poisons"
POISON_RUN_ID = "run-poison-engagement-0001"
POISON_COLLECTED_AT = "2026-12-31T23:59:59Z"
RECONCILIATION_REF = "artifacts/demo-engagement/reconciliation.json"

# Q16 (partial) — the ManifestSnapshot the poison engagement's scope is
# ratified under. Fixed clock input, no generated ids (D-P3): byte-identical
# on every rebuild. `[DEMO-ONLY]` in ratified_by is the wire-level twin of
# registry_artifact["note"] below — this is demo_registry()'s in-memory
# ratification restated as a manifest fact, never the Owner's real act.
SNAPSHOT_RATIFIED_AT = datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)
SNAPSHOT_RATIFIER = (
    "vinylfigure (Ratifier) [DEMO-ONLY: mirrors demo_registry()'s in-memory "
    "ratification; the on-disk registry stays DRAFT pending the Owner's real act]"
)
# The registry entries whose collectors this build actually exercises —
# the snapshot's `collectors` block grants only what was really invoked,
# never the full 7-entry registry (slack.scim_users, okta.users,
# github.audit_log sit unused this run).
EXERCISED_CAPABILITY_IDS = frozenset(
    {"workday.terminated_workers", "okta.system_log", "github.members", "gcp.service_accounts"}
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _dumps(obj: dict) -> str:
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def _github_transport(key: str) -> bytes:
    return (POISONS / "github_members" / f"{key}.json").read_bytes()


def _okta_transport():
    """Cursor transport over the fixture pages: each page names the cursor
    it answers, so the map is derived from the fixtures themselves."""
    pages = {}
    for path in sorted((POISONS / "okta_system_log").glob("page-*.json")):
        raw = path.read_bytes()
        pages[json.loads(raw)["cursor"]] = raw
    return pages.get


def _gcp_transport():
    """Token transport: pages chain via their own nextPageToken fields."""
    by_token: dict[str | None, bytes] = {}
    token: str | None = None
    for path in sorted((POISONS / "gcp_service_accounts").glob("page-*.json")):
        raw = path.read_bytes()
        by_token[token] = raw
        token = json.loads(raw).get("nextPageToken")

    def transport(tok: str | None) -> bytes:
        if tok not in by_token:
            raise LookupError(tok)
        return by_token[tok]

    return transport


def _breakglass_case(registry: Registry):
    """Poison 3: the claim over 'everyone capable of modifying production'
    derives from a system with no capability entry at all
    (breakglass.config — the PRD §3 E117 example verbatim). The compile
    gate must refuse BEFORE any collector runs."""
    population = Population(
        id="pop-breakglass-capable",
        name="everyone capable of modifying production",
        type=PopulationType.ENTITY,
        definition=(
            "identities able to modify production, including break-glass "
            "credential paths outside day-to-day IAM"
        ),
        derivation_rule=DerivationRule(
            description="enumerate gcp IAM principals plus the break-glass config store",
            sources=(
                SourceRef(system="gcp", role=SourceRole.AUTHORITATIVE, ref="gcp://iam-principals"),
                SourceRef(
                    system="breakglass.config",
                    role=SourceRole.CONTRIBUTING,
                    ref="breakglass://config",
                ),
            ),
        ),
        period=POISON_PERIOD,
    )
    claim = Claim(
        id="claim-poison-breakglass-coverage",
        statement="every break-glass production credential is enumerated, owned and time-boxed",
        population_id=population.id,
        assertions=(
            Assertion(
                id="poison-breakglass-A",
                attribute="A",
                type=AssertionType.STATE,
                description=(
                    "each break-glass credential appears in the ratified register with an owner"
                ),
            ),
        ),
        framework_refs=("SOC2 AM-06",),
    )
    return compile_claims((claim,), (population,), registry)


def _record_class(record: dict) -> str:
    if record["status"] == "UNKNOWN":
        return f"UNKNOWN:{record['unknown_cause']}"
    return record["status"]


def _blocked_by_open_deltas(
    deltas: tuple[Delta, ...], dispositions: dict[str, DispositionRecord]
) -> list[dict]:
    """Deltas open at first verdict, each self-describing (README Q11):
    its own bucket, and whether `dispositions` — applied AFTER that first
    verdict — has since answered it. Pulled out of build_poison_artifacts
    so the False branch (an unanswered blocker) is unit-testable: every
    fixture-driven artifact reaches RECONCILED, where every open delta is
    by definition answered, so `dispositioned: false` never appears there."""
    return sorted(
        (
            {
                "ref": d.member_ref,
                "bucket": d.bucket.value,
                "dispositioned": d.member_ref in dispositions,
            }
            for d in deltas
            if not d.dispositioned
        ),
        key=lambda entry: entry["ref"],
    )


def build_poison_artifacts() -> dict[str, str]:
    """Run all six poison cases; return {artifact filename: text}."""
    template = load_template(ROOT / "templates" / "lanes" / "termination.json")
    instance = instantiate(template, BINDINGS, POISON_PERIOD)
    event_pop = next(p for p in instance.populations if p.id == "pop-termination-events")
    timing_claim = next(c for c in instance.claims if c.id == "claim-cp-idp-deactivation-workday")
    constraint = next(a.timing for a in timing_claim.assertions if a.timing is not None)
    registry = demo_registry()

    existence_claim = Claim(
        id="claim-poison-hris-existence",
        statement=(
            "every termination effective in the period exists as a record "
            "in the authoritative HRIS feed"
        ),
        population_id=event_pop.id,
        assertions=(
            Assertion(
                id="poison-am06-existence-A",
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
    nonexistence_claim = Claim(
        id="claim-poison-github-nonexistence",
        statement=(
            "no terminated employee retains code-hosting org membership, "
            "including local non-SSO accounts"
        ),
        population_id=event_pop.id,
        assertions=(
            Assertion(
                id="poison-am06-nonexistence-A",
                attribute="A",
                type=AssertionType.NON_EXISTENCE,
                description=(
                    "no terminated identity appears among github access holders "
                    "after the revocation window"
                ),
            ),
        ),
        framework_refs=("SOC2 AM-06",),
    )

    # Poison 3 first: caught at compile, before any collection.
    breakglass_report = _breakglass_case(registry)

    # Compile gate #1 for the claims that WILL run — zero collectors are
    # executable for a claim with unresolved E-codes (TYP01 contract).
    evaluated_claims = (existence_claim, timing_claim, nonexistence_claim)
    report = compile_claims(evaluated_claims, (event_pop,), registry)
    if not report.ok:
        raise SystemExit(
            "compile gate failed before collection: "
            + "; ".join(f"{e.code} {e.message}" for e in report.errors)
        )

    # Collections — the real deterministic collectors over the poisoned
    # fixture tenant (no live calls; transports are fixture-backed).
    hris = collect_hris_terminations(
        (POISONS / "hris_terminations.json").read_bytes,
        tenant=POISON_TENANT,
        period=POISON_PERIOD,
        population_ref=event_pop.id,
    )
    okta = collect_okta_deactivations(
        _okta_transport(),
        tenant=POISON_TENANT,
        period=POISON_PERIOD,
        population_ref=event_pop.id,
    )
    github = collect_github_members(
        _github_transport,
        org=POISON_TENANT,
        period=POISON_PERIOD,
        population_ref="pop-termination-github-access",
    )
    gcp = collect_gcp_service_accounts(
        _gcp_transport(),
        project=POISON_PROJECT,
        period=POISON_PERIOD,
        population_ref="pop-termination-gcp-access",
    )

    # Compile gate #2 per emitted contract (the E302 schema-drift lane).
    for contract in (hris.contract, okta.contract):
        report = compile_claims(evaluated_claims, (event_pop,), registry, contracts=(contract,))
        if not report.ok:
            raise SystemExit(
                "compile gate failed on an evidence contract: "
                + "; ".join(f"{e.code} {e.message}" for e in report.errors)
            )

    # Ladder: the lane defined the population; the collectors discovered it.
    population = advance(advance(event_pop, AssuranceState.DEFINED), AssuranceState.DISCOVERED)

    # Set reconciliation: workday (authoritative) vs okta deactivation
    # targets vs the offboarding tracker, canonical identity by email.
    tracker = _read_json(POISONS / "offboarding_tracker.json")
    sources = (
        SourceSet(
            name="workday",
            role=SourceRole.AUTHORITATIVE,
            members=tuple(
                SourceMember(
                    ref=f"worker:{r.worker_id}",
                    email=r.email,
                    attributes={"worker_type": r.worker_type},
                )
                for r in hris.records
            ),
        ),
        SourceSet(
            name="okta",
            role=SourceRole.CONTRIBUTING,
            members=tuple(
                SourceMember(ref=f"okta:{target.id}", email=target.alternate_id)
                for event in okta.records
                for target in event.target
            ),
        ),
        SourceSet(
            name="offboarding-tracker",
            role=SourceRole.CONTRIBUTING,
            members=tuple(
                SourceMember(
                    ref=f"ticket:{t['ticket']}",
                    email=t["email"],
                    attributes=({"worker_type": t["worker_type"]} if "worker_type" in t else {}),
                )
                for t in tracker["tickets"]
            ),
        ),
    )
    exclusions_fx = _read_json(POISONS / "boundary_exclusions.json")
    boundary = tuple(BoundaryExclusion.model_validate(e) for e in exclusions_fx["reconciliation"])
    result = reconcile_sets(population, sources, boundary_exclusions=boundary)

    # Poison 1 surfaces HERE: the contractor's RIGHT_ONLY delta is open, so
    # the ladder blocks DISCOVERED→RECONCILED and the evaluator refuses a
    # verdict against the blocked denominator (UNKNOWN_POPULATION).
    alpha_record = evaluate_existence(
        claim=existence_claim,
        population=result.population,
        canonical_members=result.canonical_members,
        records=hris.records,
        contract=hris.contract,
        control_id=CONTROL_ID,
        record_id="vr-poison-existence-0001",
        run_id=POISON_RUN_ID,
        collected_at=POISON_COLLECTED_AT,
        spec_id="spec-poison-hris-existence-v1",
        spec_hash=hris.contract.contract_hash,
        source="hris-termination-collector",
        source_version=hris.contract.collector_version,
        completeness_ref=RECONCILIATION_REF,
        evidence_refs=(f"tests/fixtures/poisons/hris_terminations.json#sha256={hris.raw_sha256}",),
        chain_prev=None,
        support_record_hashes=(hris.raw_sha256,),
    )

    # The human acts (fixture-borne, manual-by-design): every open delta
    # dispositioned AFTER the poison-1 verdict was recorded — only then
    # does the ladder allow RECONCILED and the remaining claims a verdict.
    dispositions = {
        ref: DispositionRecord.model_validate(data)
        for ref, data in _read_json(POISONS / "dispositions.json").items()
    }
    reconciled = advance(
        apply_dispositions(result.population, dispositions), AssuranceState.RECONCILED
    )

    # Timelines: HRIS termination dates joined to okta deactivation events
    # by canonical email. The garbled target (poison 4) never joins, so
    # Quinn's revocation stays None — UNKNOWN_EVIDENCE, never a guess.
    revocations: dict[str, object] = {}
    for event in okta.records:
        for target in event.target:
            key = canonical_email(target.alternate_id)
            if key is None or "@" not in key:
                continue  # unresolvable identity — reconciliation owns it
            when = event.published.date()
            if key not in revocations or when < revocations[key]:
                revocations[key] = when
    left_only_members = {d.member_ref.removeprefix("email:") for d in result.buckets.left_only}
    timeline_members = set(result.canonical_members) | left_only_members
    timelines = [
        MemberTimeline(
            member=key,
            termination_date=r.termination_date,
            revocation_date=revocations.get(key),
        )
        for r in hris.records
        if (key := canonical_email(r.email)) in timeline_members
    ]
    exclusion_refs = exclusions_fx["verdicts"]
    timelines += [
        MemberTimeline(member=account.email, termination_date=POISON_PERIOD.start.date())
        for account in gcp.records
        if account.email in exclusion_refs
    ]
    timing_records = evaluate_timing(
        tuple(timelines),
        constraint,
        claim=timing_claim,
        population=reconciled,
        contract=okta.contract,
        exception_dispositions=_read_json(POISONS / "exceptions.json")["exceptions"],
        boundary_exclusions=exclusion_refs,
        control_id=CONTROL_ID,
        record_id_prefix="vr-poison-timing-0001",
        run_id=POISON_RUN_ID,
        collected_at=POISON_COLLECTED_AT,
        spec_id="spec-poison-idp-timing-v1",
        spec_hash=okta.contract.contract_hash,
        source="okta-system-log-collector",
        source_version=okta.contract.collector_version,
        completeness_ref=RECONCILIATION_REF,
        evidence_refs=(f"tests/fixtures/poisons/okta_system_log#sha256={okta.raw_sha256}",),
        chain_prev=None,
        support_record_hashes=(okta.raw_sha256,),
    )
    timing_by_member = {
        r["record_id"].removeprefix("vr-poison-timing-0001-"): r for r in timing_records
    }

    # Poison 2: the dormant local account is named via the ratified
    # local-account register — never guessed from the login.
    identity_map = _read_json(POISONS / "identity_map.json")["map"]
    holders = tuple(
        sorted(
            email
            for member in github.records
            if (email := member.sso_identity or identity_map.get(member.login)) is not None
        )
    )
    nonexistence_record = evaluate_non_existence(
        holders,
        result.canonical_members,
        claim=nonexistence_claim,
        population=reconciled,
        contract=github.contract,
        control_id=CONTROL_ID,
        record_id="vr-poison-nonexistence-0001",
        run_id=POISON_RUN_ID,
        collected_at=POISON_COLLECTED_AT,
        spec_id="spec-poison-github-nonexistence-v1",
        spec_hash=github.contract.contract_hash,
        source="github-members-collector",
        source_version=github.contract.collector_version,
        completeness_ref=RECONCILIATION_REF,
        evidence_refs=(f"tests/fixtures/poisons/github_members#sha256={github.raw_sha256}",),
        chain_prev=None,
        support_record_hashes=(github.raw_sha256,),
    )

    breakglass_errors = [e.model_dump(mode="json") for e in breakglass_report.errors]
    cases = [
        {
            "id": "contractor-absent-from-hris",
            "poison": (
                "contractor offboarded downstream (okta pvt-0009, tracker "
                "POF-3309) but absent from the authoritative HRIS feed"
            ),
            "stage": "evaluate",
            "expected": "UNKNOWN:UNKNOWN_POPULATION",
            "evidence": {"bucket": "right_only", "member_ref": "email:mira.chen@example.com"},
            "actual": {"kind": "verdict", "record": alpha_record},
            "actual_class": _record_class(alpha_record),
        },
        {
            "id": "dormant-github-local-account",
            "poison": (
                "terminated employee still an org member via a dormant "
                "local (non-SSO) account, rhea-bell-local"
            ),
            "stage": "evaluate",
            "expected": "FAIL",
            "evidence": {"login": "rhea-bell-local", "member": "rhea.bell@example.com"},
            "actual": {"kind": "verdict", "record": nonexistence_record},
            "actual_class": _record_class(nonexistence_record),
        },
        {
            "id": "breakglass-capability-missing",
            "poison": (
                "break-glass cloud account claim derives from "
                "breakglass.config, a system with no capability entry"
            ),
            "stage": "compile",
            "expected": "E117",
            "evidence": {"system": "breakglass.config", "population": "pop-breakglass-capable"},
            "actual": {"kind": "compile_error", "errors": breakglass_errors},
            "actual_class": (breakglass_errors[0]["code"] if breakglass_errors else "COMPILED"),
        },
        {
            "id": "garbled-identity-join",
            "poison": (
                "deactivation event target alternate_id garbled "
                "(quinn.ash%example.com) — the identity join cannot resolve it"
            ),
            "stage": "evaluate",
            "expected": "UNKNOWN:UNKNOWN_EVIDENCE",
            "evidence": {"bucket": "unresolvable", "member_ref": "okta:00u9104"},
            "actual": {"kind": "verdict", "record": timing_by_member["quinn.ash@example.com"]},
            "actual_class": _record_class(timing_by_member["quinn.ash@example.com"]),
        },
        {
            "id": "delayed-revocation",
            "poison": (
                "omar.diaz revoked 9 business days after termination "
                "against the 5-business-day constraint"
            ),
            "stage": "evaluate",
            "expected": "FAIL",
            "evidence": {"member": "omar.diaz@example.com"},
            "actual": {"kind": "verdict", "record": timing_by_member["omar.diaz@example.com"]},
            "actual_class": _record_class(timing_by_member["omar.diaz@example.com"]),
        },
        {
            "id": "legitimate-exception",
            "poison": (
                "pia.voss's phased offboarding ran long under a "
                "dispositioned exception — EXCEPTION, never a silent PASS"
            ),
            "stage": "evaluate",
            "expected": "EXCEPTION",
            "evidence": {"member": "pia.voss@example.com"},
            "actual": {"kind": "verdict", "record": timing_by_member["pia.voss@example.com"]},
            "actual_class": _record_class(timing_by_member["pia.voss@example.com"]),
        },
    ]
    for case in cases:
        case["detected"] = case["actual_class"] == case["expected"]
    detected = sum(1 for case in cases if case["detected"])
    detection = {
        "total": len(cases),
        "detected": detected,
        "detection_rate": detected / len(cases),
        "misses": [case["id"] for case in cases if not case["detected"]],
    }

    period = {"start": POISON_PERIOD.start.isoformat(), "end": POISON_PERIOD.end.isoformat()}
    poisons_artifact = {
        "run_id": POISON_RUN_ID,
        "tenant": POISON_TENANT,
        "project": POISON_PROJECT,
        "period": period,
        "collected_at": POISON_COLLECTED_AT,
        "control_id": CONTROL_ID,
        "cases": cases,
        "detection": detection,
        "verdict_records": {
            "existence": [alpha_record],
            "non_existence": [nonexistence_record],
            "timing": list(timing_records),
        },
    }
    blocked_by_open_deltas = _blocked_by_open_deltas(result.population.deltas, dispositions)
    reconciliation_artifact = {
        "population_id": event_pop.id,
        "population_name": event_pop.name,
        # Invariant №3 travels with the reconciliation: a population has a
        # derivation rule OR an authoritative source (never both, never
        # neither). Without it the "why complete" surface can name what
        # differed but not what the population was derived FROM.
        "population_type": event_pop.type.value,
        "definition": event_pop.definition,
        "derivation_rule": (
            event_pop.derivation_rule.model_dump(mode="json")
            if event_pop.derivation_rule is not None
            else None
        ),
        "authoritative_source": (
            event_pop.authoritative_source.model_dump(mode="json")
            if event_pop.authoritative_source is not None
            else None
        ),
        "tenant": POISON_TENANT,
        "period": period,
        "sources": [
            {
                "name": s.name,
                "role": s.role.value,
                "members": [
                    {"ref": m.ref, "email": m.email, "attributes": m.attributes} for m in s.members
                ],
            }
            for s in sources
        ],
        "buckets": result.buckets.model_dump(mode="json"),
        "counts": result.buckets.counts,
        "counts_note": "counts are diagnostics, never evidence (HANDOFF §2)",
        "canonical_members": list(result.canonical_members),
        "boundary_exclusions": [e.model_dump(mode="json") for e in boundary],
        "dispositions": {
            ref: record.model_dump(mode="json") for ref, record in dispositions.items()
        },
        "ladder": {
            "at_first_verdict": result.population.state.value,
            "blocked_by_open_deltas": blocked_by_open_deltas,
            "after_dispositions": reconciled.state.value,
        },
    }
    registry_artifact = {
        "note": (
            "DEMO-ONLY: workday.terminated_workers appears frozen because the "
            "demo registry ratifies a COPY in memory (see demo_registry); the "
            "on-disk entry stays DRAFT pending the Owner's real act."
        ),
        "entries": [e.model_dump(mode="json") for e in sorted(registry.all(), key=lambda e: e.id)],
        "compile_errors": breakglass_errors,
    }

    # Q14 — the EvidenceQualityContracts every collector above already
    # built in memory, keyed by contract_hash. Scoped to the three
    # contracts an evaluate_* call above was actually passed as
    # `contract=` (hris for alpha_record, okta for the timing batch,
    # github for nonexistence_record) — every emitted verdict record's
    # spec_hash IS a key into this map by construction, and this map
    # carries nothing else: gcp.contract is collected but never itself
    # evaluated against (its records only feed the okta-contracted
    # timing timelines), so including it here would orphan a contract no
    # verdict cites.
    contracts_artifact = {
        contract.contract_hash: contract.model_dump(mode="json")
        for contract in (hris.contract, okta.contract, github.contract)
    }

    # Q16 (partial) — the ratified ManifestSnapshot for this engagement.
    # Every id below is drawn from the objects the pipeline itself just
    # built, so it cannot drift into fiction relative to the other three
    # artifacts: population/claim ids from the claims evaluated above,
    # capability ids from the same `registry` serialized into
    # registry_artifact, contract hashes from the same collector calls.
    #
    # EXERCISED_CAPABILITY_IDS is the one hand-maintained exception — there
    # is no field on EvidenceQualityContract that names the capability id
    # it was collected under, only `source` (the bare system: "workday",
    # "okta", "github", "gcp"). This check keeps the constant honest against
    # what was actually collected in THIS build: if a future change adds or
    # drops a collector call without updating the constant, this raises
    # instead of silently shipping a `collectors` block that misrepresents
    # what was really invoked.
    collected_systems = {
        hris.contract.source,
        okta.contract.source,
        github.contract.source,
        gcp.contract.source,
    }
    exercised_systems = {cap_id.split(".", 1)[0] for cap_id in EXERCISED_CAPABILITY_IDS}
    if exercised_systems != collected_systems:
        raise SystemExit(
            "EXERCISED_CAPABILITY_IDS drifted from the collectors this build actually "
            f"invokes: exercised systems {sorted(exercised_systems)} != "
            f"collected systems {sorted(collected_systems)}"
        )

    manifest_blocks = ManifestBlocks(
        populations=(event_pop.id,),
        claims=tuple(sorted({existence_claim.id, timing_claim.id, nonexistence_claim.id})),
        evidence_contracts=tuple(
            sorted(
                {
                    hris.contract.contract_hash,
                    okta.contract.contract_hash,
                    github.contract.contract_hash,
                    gcp.contract.contract_hash,
                }
            )
        ),
        capabilities=tuple(sorted(e.id for e in registry.all())),
        collectors=tuple(
            sorted(
                (
                    CollectorGrant(id=entry.id, permissions=(entry.auth_scope,))
                    for entry in registry.all()
                    if entry.id in EXERCISED_CAPABILITY_IDS
                ),
                key=lambda grant: grant.id,
            )
        ),
    )
    manifest_snapshot = genesis(manifest_blocks, SNAPSHOT_RATIFIER, SNAPSHOT_RATIFIED_AT)

    return {
        "poisons.json": _dumps(poisons_artifact),
        "reconciliation.json": _dumps(reconciliation_artifact),
        "registry.json": _dumps(registry_artifact),
        "contracts.json": _dumps(contracts_artifact),
        "snapshot.json": _dumps(manifest_snapshot.model_dump(mode="json")),
    }


def main_poisons() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    artifacts = build_poison_artifacts()
    for name, text in sorted(artifacts.items()):
        path = OUT.parent / name
        path.write_text(text)
        print(f"wrote {path}")
    detection = json.loads(artifacts["poisons.json"])["detection"]
    print(
        "assurance defect detection rate: "
        f"{detection['detected']}/{detection['total']} = {detection['detection_rate']:.0%}"
    )
    return 0 if detection["detection_rate"] == 1.0 else 1


if __name__ == "__main__":
    sys.exit(main_poisons() if sys.argv[1:] == ["poisons"] else main())
