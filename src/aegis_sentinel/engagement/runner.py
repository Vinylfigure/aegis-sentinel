"""The demo engagement, end to end, against the REAL pipeline (VAL02).

One deterministic run over the fixture tenants
(``tests/fixtures/tenants/``): instantiate the termination lane,
compile it (the six-month E204 exhibit and the break-glass E117 both
fall out of the full-period compile), re-scope the TIMING claim to the
engagement's honest 60-day window and compile that clean, execute the
real collectors over the fixture transport, run the REC01 set
reconciler per population, and evaluate every compiled claim into
sealed verdict records — five verdict states across the engagement.

Poison detections this run carries (docs/PRD-v3.md §6; the poison
table in tests/fixtures/tenants/README.md):

- contractor absent from HRIS → negative-space ``left_only`` delta on
  the identity join → TERM-JOIN.a UNKNOWN(UNKNOWN_POPULATION);
- dormant GitHub local account → TERM-GITHUB.a FAIL;
- break-glass cloud account → the gcp accounts population's derivation
  references ``breakglass.config`` (the tenant's real break-glass
  surface, discovered in scoping) with no ratified capability entry →
  E117; the claim over it never compiles and no gcp collector executes
  for it (compile-integrity guardrail, PRD-v3 §7);
- failed identity join → ``unresolvable`` orphan delta + TERM-FEED.b
  UNKNOWN(UNKNOWN_POPULATION, identity_fuzzy);
- delayed revocation → TERM-TIMING.a FAIL (9 business days > 5);
- legitimate exception → TERM-SLACK.a EXCEPTION (DISP-2026-114).

Determinism: every timestamp is an engagement-fixture constant (D-P3 —
no wall clock anywhere in the pipeline); collections run over the
injected :class:`~aegis_sentinel.collectors.FixtureTransport`; all
ordering is explicit. Same fixtures, same run, byte-identical records.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from aegis_sentinel.capability import Registry, RegistryView
from aegis_sentinel.capability.entry import CapabilityEntry
from aegis_sentinel.collectors import (
    CollectionSnapshot,
    FixtureTransport,
    GcpIamBindingsCollector,
    GithubAuditLogCollector,
    GithubOrgMembersCollector,
    HrisTerminationsCollector,
    OktaSystemLogCollector,
    OktaUsersCollector,
    SlackUsersCollector,
)
from aegis_sentinel.compile import (
    CompiledCollectorPlan,
    compile_program,
    executable_collectors,
)
from aegis_sentinel.compile.typecheck import AnyCompileError
from aegis_sentinel.evaluate import (
    AccountCase,
    RatifiedScopeExclusion,
    TimingCase,
    evaluate_attributability_claim,
    evaluate_feed_claim,
    evaluate_non_existence_claim,
    evaluate_ratified_exclusion,
    evaluate_timing_claim,
)
from aegis_sentinel.manifest import instantiate_lane
from aegis_sentinel.reconcile import (
    IdentityCluster,
    KeyValue,
    MemberKind,
    RatifiedDeltaDisposition,
    ReconciliationResult,
    SourceMember,
    SourceMembers,
    build_clusters,
    email_domain,
    reconcile_population,
    to_ratified,
    to_reconciled,
)
from aegis_sentinel.schema import (
    AssertionType,
    Claim,
    DerivationRule,
    EvidenceQualityContract,
    LaneTemplate,
    Period,
    Population,
    Source,
    SourceRole,
    VerdictRecord,
)

MODULE_VERSION = "engagement.runner@0.1.0"

#: The five fixture systems (PRD-v3 §6), keyed by lane node system_ref.
SYSTEMS: dict[str, str] = {
    "hris": "hris",
    "okta": "okta",
    "github": "github",
    "gcp": "gcp",
    "slack": "slack",
}

#: The tenant's break-glass configuration surface: real, in scope, and
#: with NO ratified capability entry — the E117 the engagement carries
#: as a standing compile error until a human ratifies an entry for it.
BREAKGLASS_SOURCE = "breakglass.config"
GCP_ACCOUNTS_POPULATION = "TERM.gcp.accounts"

FEED_CLAIM = "TERM.feed-completeness"
TIMING_CLAIM = "TERM.timely-revocation"
JOIN_CLAIM = "TERM.attributability"
TERMINATIONS_POPULATION = "TERM.terminations"
JOIN_POPULATION = "TERM.identity-join"

_SRC_HRIS = "hris-termination-feed"
_SRC_SYSLOG = "okta-system-log"
_SRC_GROUPS = "okta-group-assignments"

OKTA_USERS_ENTRY = "okta.users.api_v1"
OKTA_LOG_ENTRY = "okta.system_log.api_v1"
GITHUB_MEMBERS_ENTRY = "github.org_members.rest_v3"
GITHUB_AUDIT_ENTRY = "github.audit_log.rest_v3"
GCP_ENTRY = "gcp.iam.cloud_asset_v1"


def add_breakglass_source(population: Population) -> Population:
    """Declare the break-glass surface on the gcp accounts population.

    This is the engagement's honest scope: the tenant HAS a break-glass
    account outside every IdP-derived population, so the population
    that claims to cover "every account able to authenticate to gcp"
    must name that surface — and the compiler must then refuse (E117)
    because no ratified capability entry exists for it. Same mutation
    shape as the breakglass poison runner (tests/mutation/conftest.py).
    """
    if population.population_id != GCP_ACCOUNTS_POPULATION:
        return population
    rule = population.derivation_rule
    return population.model_copy(
        update={
            "sources": population.sources
            + (Source(source_id=BREAKGLASS_SOURCE, role=SourceRole.CONTRIBUTING),),
            "derivation_rule": DerivationRule(
                rule_text=rule.rule_text
                + "; union break-glass accounts enumerated by breakglass.config",
                source_refs=rule.source_refs + (BREAKGLASS_SOURCE,),
            ),
        }
    )


def plan_from_entry(
    entry: CapabilityEntry,
    *,
    claim_ref: str,
    assertion_ref: str,
    assertion_type: AssertionType,
    population_ref: str,
    source_id: str,
    time_window: Period,
) -> CompiledCollectorPlan:
    """A collector plan derived field-by-field from one ratified entry."""
    return CompiledCollectorPlan(
        claim_ref=claim_ref,
        assertion_ref=assertion_ref,
        assertion_type=assertion_type,
        population_ref=population_ref,
        source_id=source_id,
        entry_id=entry.entry_id,
        system=entry.system,
        surface=entry.surface,
        auth_scope=entry.auth_scope,
        pagination=entry.pagination,
        temporal=entry.temporal,
        join_keys=entry.join_keys,
        time_window=time_window,
    )


@dataclass(frozen=True)
class EngagementRun:
    """Everything one deterministic engagement run produced."""

    engagement: dict[str, Any]
    template: LaneTemplate
    registry_view: RegistryView
    populations: tuple[Population, ...]
    claims: tuple[Claim, ...]
    reconciliations: dict[str, ReconciliationResult]
    clusters: tuple[IdentityCluster, ...]
    verdicts: tuple[VerdictRecord, ...]
    compile_errors: tuple[AnyCompileError, ...]
    contracts: dict[str, EvidenceQualityContract]
    snapshots: dict[str, CollectionSnapshot]
    timing_window: Period

    def verdict_for(self, assertion_ref: str) -> VerdictRecord:
        for record in self.verdicts:
            if record.assertion_ref == assertion_ref:
                return record
        raise KeyError(f"no verdict for assertion {assertion_ref!r}")


def _snapshot_ref(snapshot: CollectionSnapshot) -> str:
    assert snapshot.snapshot_hash is not None  # sealed by collect()
    return f"collection-snapshot:sha256:{snapshot.snapshot_hash}"


def _cluster_for(clusters: tuple[IdentityCluster, ...], value: str) -> IdentityCluster | None:
    for cluster in clusters:
        if cluster.any_key_value(value):
            return cluster
    return None


def _gcp_source_members(bindings) -> tuple[SourceMember, ...]:
    members: dict[str, SourceMember] = {}
    for binding in bindings:
        for principal in binding.members:
            if principal in members:
                continue
            prefix, _, name = principal.partition(":")
            if prefix == "user":
                members[principal] = SourceMember(
                    source_id="gcp-account-inventory",
                    keys=(KeyValue(key="email", value=name),),
                    display_name=name,
                    kind=MemberKind.HUMAN,
                    active=True,
                )
            elif prefix == "serviceAccount":
                members[principal] = SourceMember(
                    source_id="gcp-account-inventory",
                    display_name=name,
                    kind=MemberKind.SERVICE_ACCOUNT,
                    active=True,
                )
            else:  # group: — an access path, not a principal identity
                members[principal] = SourceMember(
                    source_id="gcp-account-inventory",
                    display_name=name,
                    kind=MemberKind.GROUP,
                    active=True,
                )
    return tuple(members[k] for k in sorted(members))


def run_demo_engagement(root: Path) -> EngagementRun:
    """Run the whole engagement deterministically; see module docstring."""
    tenants_dir = root / "tests" / "fixtures" / "tenants"
    engagement = json.loads((tenants_dir / "engagement.json").read_text(encoding="utf-8"))
    retrieved_at = datetime.fromisoformat(engagement["retrieved_at"])
    evaluated_at = datetime.fromisoformat(engagement["evaluated_at"])
    period = Period(
        start=date.fromisoformat(engagement["period"]["start"]),
        end=date.fromisoformat(engagement["period"]["end"]),
    )
    timing_window = Period(
        start=date.fromisoformat(engagement["timing_window"]["start"]),
        end=date.fromisoformat(engagement["timing_window"]["end"]),
    )
    identity_domain: str = engagement["identity_domain"]
    manifest_version: str = engagement["manifest_version"]
    manifest_hash: str = engagement["ratified_manifest_snapshot_hash"]
    tenant: str = engagement["tenant"]
    dispositions = tuple(
        RatifiedDeltaDisposition.model_validate(raw)
        for raw in engagement.get("delta_dispositions", ())
    )

    template = LaneTemplate.model_validate_json(
        (root / "templates" / "lanes" / "termination.json").read_text(encoding="utf-8")
    )
    usable = Registry.load(root / "registry" / "capabilities").usable()

    # ---- compile: full period (the exhibits), then the honest window ----
    populations, claims = instantiate_lane(template, SYSTEMS, period)
    populations = [add_breakglass_source(p) for p in populations]
    full_result = compile_program(claims, populations, usable)
    compile_errors = tuple(full_result.errors)  # E204 (TA-2/181d) + E117 (breakglass)

    populations_60, claims_60 = instantiate_lane(template, SYSTEMS, timing_window)
    timing_claim = next(c for c in claims_60 if c.claim_id == TIMING_CLAIM)
    timing_result = compile_program([timing_claim], populations_60, usable)
    timing_plans = executable_collectors(timing_result)
    if not timing_plans:
        raise RuntimeError(
            "the re-scoped TIMING claim failed to compile:\n" + timing_result.render_errors()
        )
    timing_plan = timing_plans[0]

    lane_plans = {p.claim_ref: p for p in executable_collectors(full_result)}
    feed_plan = lane_plans[FEED_CLAIM]
    github_plan = lane_plans["TERM.github.no-residual-access"]
    slack_plan = lane_plans["TERM.slack.no-residual-access"]
    join_plan = lane_plans[JOIN_CLAIM]

    # ---- collect (fixture transport only; no live-tenant calls) --------
    okta_surfaces = {
        usable.get(OKTA_USERS_ENTRY).surface: "users",
        usable.get(OKTA_LOG_ENTRY).surface: "system-log",
    }
    github_surfaces = {
        usable.get(GITHUB_MEMBERS_ENTRY).surface: "org-members",
        usable.get(GITHUB_AUDIT_ENTRY).surface: "audit-log",
    }
    flat = FixtureTransport(tenants_dir)
    okta_transport = FixtureTransport(tenants_dir, surfaces=okta_surfaces)
    github_transport = FixtureTransport(tenants_dir, surfaces=github_surfaces)

    okta_users_plan = plan_from_entry(
        usable.get(OKTA_USERS_ENTRY),
        claim_ref="ENG.collections",
        assertion_ref="ENG-OKTA-USERS.a",
        assertion_type=AssertionType.STATE,
        population_ref="TERM.github.accounts",
        source_id=_SRC_GROUPS,
        time_window=period,
    )
    github_audit_plan = plan_from_entry(
        usable.get(GITHUB_AUDIT_ENTRY),
        claim_ref="ENG.collections",
        assertion_ref="ENG-GITHUB-AUDIT.a",
        assertion_type=AssertionType.EVENT,
        population_ref=TERMINATIONS_POPULATION,
        source_id="github-audit-log",
        time_window=Period(start=date(2026, 1, 2), end=date(2026, 6, 30)),
    )
    gcp_join_plan = plan_from_entry(
        usable.get(GCP_ENTRY),
        claim_ref="ENG.collections",
        assertion_ref="ENG-GCP-INVENTORY.a",
        assertion_type=AssertionType.STATE,
        population_ref=JOIN_POPULATION,
        source_id="gcp-account-inventory",
        time_window=period,
    )

    hris = HrisTerminationsCollector(flat)
    okta_users_collector = OktaUsersCollector(okta_transport)
    syslog_collector = OktaSystemLogCollector(okta_transport)
    gh_members_collector = GithubOrgMembersCollector(github_transport)
    gh_audit_collector = GithubAuditLogCollector(github_transport)
    gcp_collector = GcpIamBindingsCollector(flat)
    slack_collector = SlackUsersCollector(flat)

    snapshots = {
        "hris": hris.collect(feed_plan, retrieved_at),
        "okta-users": okta_users_collector.collect(okta_users_plan, retrieved_at),
        "okta-system-log": syslog_collector.collect(timing_plan, retrieved_at),
        "github-members": gh_members_collector.collect(github_plan, retrieved_at),
        "github-audit": gh_audit_collector.collect(github_audit_plan, retrieved_at),
        "gcp": gcp_collector.collect(gcp_join_plan, retrieved_at),
        "slack": slack_collector.collect(slack_plan, retrieved_at),
    }
    contracts = {
        "hris": hris.contract(feed_plan, tenant, retrieved_at),
        # The attributability claim's own contract: same authoritative
        # surface, identity-join population identity.
        "identity-join": hris.contract(join_plan, tenant, retrieved_at),
        "okta-users": okta_users_collector.contract(okta_users_plan, tenant, retrieved_at),
        "okta-system-log": syslog_collector.contract(timing_plan, tenant, retrieved_at),
        "github-members": gh_members_collector.contract(github_plan, tenant, retrieved_at),
        "github-audit": gh_audit_collector.contract(github_audit_plan, tenant, retrieved_at),
        "gcp": gcp_collector.contract(gcp_join_plan, tenant, retrieved_at),
        "slack": slack_collector.contract(slack_plan, tenant, retrieved_at),
    }

    hris_events = HrisTerminationsCollector.events(snapshots["hris"])
    okta_users = OktaUsersCollector.users(snapshots["okta-users"])
    deactivations = OktaSystemLogCollector.deactivations(snapshots["okta-system-log"])
    gh_accounts = GithubOrgMembersCollector.accounts(snapshots["github-members"])
    gh_removals = GithubAuditLogCollector.removals(snapshots["github-audit"])
    gcp_bindings = GcpIamBindingsCollector.bindings(snapshots["gcp"])
    slack_users = SlackUsersCollector.users(snapshots["slack"])

    # ---- typed source members for the set reconciler -------------------
    hris_members = tuple(
        SourceMember(
            source_id=_SRC_HRIS,
            keys=(
                KeyValue(key="employee_id", value=e.employee_id),
                KeyValue(key="email", value=e.email),
            ),
            display_name=e.email,
            active=False,
            termination_signal=True,
        )
        for e in hris_events
    )
    syslog_members = tuple(
        SourceMember(
            source_id=_SRC_SYSLOG,
            keys=(KeyValue(key="email", value=e.target_alternate_id),),
            display_name=e.target_alternate_id,
            active=False,
            termination_signal=True,
        )
        for e in deactivations
    )
    github_members = tuple(
        SourceMember(
            source_id="github-account-inventory",
            keys=(KeyValue(key="login", value=a.login),)
            + ((KeyValue(key="email", value=a.saml_name_id),) if a.saml_name_id else ()),
            display_name=a.login,
            kind=(
                MemberKind.OUTSIDE_COLLABORATOR
                if a.membership == "outside_collaborator"
                else MemberKind.HUMAN
            ),
            active=True,
        )
        for a in gh_accounts
    )
    okta_group_members = tuple(
        SourceMember(
            source_id=_SRC_GROUPS,
            keys=(
                KeyValue(key="email", value=u.email),
                KeyValue(key="login", value=u.login),
            ),
            display_name=u.email,
            active=True,
        )
        for u in okta_users
        if u.status == "ACTIVE"
    )
    gcp_members = _gcp_source_members(gcp_bindings)
    slack_members = tuple(
        SourceMember(
            source_id="slack-account-inventory",
            keys=(KeyValue(key="email", value=u.email),) if u.email else (),
            display_name=u.name,
            kind=MemberKind.BOT if u.is_bot else MemberKind.HUMAN,
            active=not u.deleted,
        )
        for u in slack_users
    )

    by_population = {p.population_id: p for p in populations}
    delta_owner = engagement.get("ratified_by", "unassigned")

    # ---- reconcile ------------------------------------------------------
    reconciliations: dict[str, ReconciliationResult] = {}

    terminations = by_population[TERMINATIONS_POPULATION]
    term_recon = reconcile_population(
        terminations,
        [
            SourceMembers(
                source_id=_SRC_HRIS,
                complete=snapshots["hris"].complete,
                notes=snapshots["hris"].incompleteness,
                member_ids=tuple(e.employee_id for e in hris_events),
            )
        ],
    )
    # Zero open deltas → RECONCILED; then the human ratification the
    # engagement fixture records (F-4) → RATIFIED.
    term_population = to_ratified(
        to_reconciled(term_recon.population, term_recon), engagement["ratified_by"]
    )
    term_recon = term_recon.model_copy(update={"population": term_population})
    reconciliations[TERMINATIONS_POPULATION] = term_recon

    def _accounts_recon(system: str, inventory: tuple[SourceMember, ...]) -> None:
        population = by_population[f"TERM.{system}.accounts"]
        result = reconcile_population(
            population,
            [
                SourceMembers(
                    source_id=f"{system}-account-inventory",
                    complete=snapshots["github-members" if system == "github" else system].complete,
                    notes=(),
                    members=inventory,
                ),
                SourceMembers(
                    source_id=_SRC_GROUPS,
                    complete=snapshots["okta-users"].complete,
                    notes=(),
                    members=okta_group_members,
                ),
            ],
            dispositions=dispositions,
            identity_domain=identity_domain,
            delta_owner=delta_owner,
        )
        reconciliations[population.population_id] = result

    _accounts_recon("github", github_members)
    _accounts_recon("slack", slack_members)
    # gcp accounts: E117 — the derivation rule names breakglass.config,
    # which no ratified capability entry can enumerate; the population
    # cannot be discovered and stays DEFINED (compile-integrity, PRD §7).

    join_population = by_population[JOIN_POPULATION]
    join_sources = [
        SourceMembers(
            source_id=_SRC_HRIS,
            complete=snapshots["hris"].complete,
            notes=(),
            members=hris_members,
        ),
        SourceMembers(
            source_id=_SRC_SYSLOG,
            complete=snapshots["okta-system-log"].complete,
            notes=(),
            members=syslog_members,
        ),
        SourceMembers(
            source_id="github-account-inventory",
            complete=snapshots["github-members"].complete,
            notes=(),
            members=github_members,
        ),
        SourceMembers(
            source_id="gcp-account-inventory",
            complete=snapshots["gcp"].complete,
            notes=(),
            members=gcp_members,
        ),
        SourceMembers(
            source_id="slack-account-inventory",
            complete=snapshots["slack"].complete,
            notes=(),
            members=slack_members,
        ),
    ]
    join_recon = reconcile_population(
        join_population,
        join_sources,
        dispositions=dispositions,
        identity_domain=identity_domain,
        delta_owner=delta_owner,
    )
    reconciliations[JOIN_POPULATION] = join_recon

    # One identity universe for the evaluator joins: the join sources'
    # workforce members, clustered exactly as the reconciler clusters them.
    clusters = build_clusters(
        [
            m
            for source in join_sources
            for m in source.members
            if m.kind in {MemberKind.HUMAN, MemberKind.OUTSIDE_COLLABORATOR}
        ],
        {s.source_id: i for i, s in enumerate(join_sources)},
    )

    okta_emails = {u.email.casefold() for u in okta_users}

    def _cluster_emails(cluster: IdentityCluster) -> set[str]:
        return set(cluster.key_values("email"))

    def _disposition_for(cluster: IdentityCluster) -> str | None:
        for disposition in dispositions:
            if disposition.covers(cluster):
                return disposition.disposition_ref
        return None

    # ---- evaluate -------------------------------------------------------
    deprovisioned: list[str] = []
    unresolved: list[str] = []
    excepted: list[tuple[str, str]] = []
    for event in hris_events:
        cluster = _cluster_for(clusters, event.employee_id)
        assert cluster is not None  # every feed row was clustered above
        if any(m.source_id == _SRC_SYSLOG for m in cluster.members):
            deprovisioned.append(event.employee_id)
            continue
        ref = _disposition_for(cluster)
        if ref is not None:
            excepted.append((event.employee_id, ref))
        elif not (_cluster_emails(cluster) & okta_emails):
            # No IdP identity resolvable for this worker at all: the
            # canonical join failed (D-7 identity_fuzzy), never guessed.
            unresolved.append(event.employee_id)

    feed_claim = next(c for c in claims if c.claim_id == FEED_CLAIM)
    feed_verdicts = evaluate_feed_claim(
        feed_claim,
        term_recon,
        contracts["hris"],
        manifest_version=manifest_version,
        manifest_snapshot_hash=manifest_hash,
        collection_snapshot_hash=snapshots["hris"].snapshot_hash or "",
        evaluated_at=evaluated_at,
        deprovisioned_member_ids=tuple(deprovisioned),
        unresolved_member_ids=tuple(unresolved),
        excepted_members=tuple(excepted),
        extra_evidence_refs=(_snapshot_ref(snapshots["okta-system-log"]),),
    )

    deactivated_on: dict[str, date] = {}
    for event in deactivations:
        deactivated_on.setdefault(
            event.target_alternate_id.casefold(),
            event.published.astimezone(timezone.utc).date(),
        )
    removed_on: dict[str, date] = {}
    for removal in gh_removals:
        removed_on.setdefault(
            removal.user.casefold(),
            datetime.fromtimestamp(removal.timestamp_ms / 1000, tz=timezone.utc).date(),
        )

    timing_cases: list[TimingCase] = []
    for event in hris_events:
        if not (timing_window.start <= event.termination_date <= timing_window.end):
            continue
        cluster = _cluster_for(clusters, event.employee_id)
        assert cluster is not None
        idp_date = next(
            (
                deactivated_on[email]
                for email in sorted(_cluster_emails(cluster))
                if email in deactivated_on
            ),
            None,
        )
        # GitHub removal events carry only the (already-removed) login;
        # a removed member's login joins to no cluster key, so the
        # removal is attributed only where a cluster key matches —
        # never guessed from name shape (D-8).
        removal_date = next(
            (
                removed_on[login]
                for login in sorted(cluster.key_values("login"))
                if login in removed_on
            ),
            None,
        )
        timing_cases.append(
            TimingCase(
                member_key=event.employee_id,
                display_name=event.email,
                termination_date=event.termination_date,
                idp_deactivated_on=idp_date,
                downstream_removed_on=removal_date,
                unresolved=event.employee_id in unresolved,
                disposition_ref=dict(excepted).get(event.employee_id),
            )
        )
    timing_verdict = evaluate_timing_claim(
        timing_claim,
        timing_cases,
        contracts["okta-system-log"],
        manifest_version=manifest_version,
        manifest_snapshot_hash=manifest_hash,
        evidence_refs=(
            _snapshot_ref(snapshots["hris"]),
            _snapshot_ref(snapshots["okta-system-log"]),
            _snapshot_ref(snapshots["github-audit"]),
        ),
        evaluated_at=evaluated_at,
        limit_business_days=5,
    )

    join_claim = next(c for c in claims if c.claim_id == JOIN_CLAIM)
    join_verdict = evaluate_attributability_claim(
        join_claim,
        join_recon,
        contracts["identity-join"],
        manifest_version=manifest_version,
        manifest_snapshot_hash=manifest_hash,
        evidence_refs=tuple(
            _snapshot_ref(snapshots[key])
            for key in ("hris", "okta-system-log", "github-members", "gcp", "slack")
        ),
        evaluated_at=evaluated_at,
    )

    def _account_case(
        member_key: str, display_name: str, active: bool, cluster: IdentityCluster | None
    ) -> AccountCase:
        terminated = cluster is not None and any(m.source_id == _SRC_HRIS for m in cluster.members)
        identity_known = cluster is not None and bool(_cluster_emails(cluster))
        domain = email_domain(cluster) if cluster is not None else None
        return AccountCase(
            member_key=member_key,
            display_name=display_name,
            active=active,
            terminated=terminated,
            identity_known=identity_known,
            workforce_attributable=terminated or domain == identity_domain,
            disposition_ref=_disposition_for(cluster) if cluster is not None else None,
        )

    github_cases = tuple(
        _account_case(a.login, a.login, True, _cluster_for(clusters, a.login)).model_copy(
            update={"dormant": a.last_active < period.start}
        )
        for a in gh_accounts
    )
    github_claim = next(c for c in claims if c.claim_id == "TERM.github.no-residual-access")
    github_verdict = evaluate_non_existence_claim(
        github_claim,
        github_cases,
        contracts["github-members"],
        manifest_version=manifest_version,
        manifest_snapshot_hash=manifest_hash,
        evidence_refs=(
            _snapshot_ref(snapshots["github-members"]),
            _snapshot_ref(snapshots["hris"]),
        ),
        evaluated_at=evaluated_at,
    )

    slack_cases = tuple(
        _account_case(
            u.email or u.name,
            u.name,
            not u.deleted,
            _cluster_for(clusters, u.email) if u.email else None,
        )
        for u in slack_users
        if not u.is_bot
    )
    slack_claim = next(c for c in claims if c.claim_id == "TERM.slack.no-residual-access")
    slack_verdict = evaluate_non_existence_claim(
        slack_claim,
        slack_cases,
        contracts["slack"],
        manifest_version=manifest_version,
        manifest_snapshot_hash=manifest_hash,
        evidence_refs=(
            _snapshot_ref(snapshots["slack"]),
            _snapshot_ref(snapshots["hris"]),
        ),
        evaluated_at=evaluated_at,
    )

    excluded_verdicts = tuple(
        evaluate_ratified_exclusion(
            RatifiedScopeExclusion.model_validate(raw),
            manifest_version=manifest_version,
            manifest_snapshot_hash=manifest_hash,
            evaluated_at=evaluated_at,
        )
        for raw in engagement.get("scope_exclusions", ())
    )

    verdicts = (
        *feed_verdicts,
        timing_verdict,
        join_verdict,
        github_verdict,
        slack_verdict,
        *excluded_verdicts,
    )

    # ---- final population states (ladder, PRD-v3 §2) --------------------
    final_populations = tuple(
        reconciliations[p.population_id].population
        if p.population_id in reconciliations
        else p  # gcp accounts stays DEFINED behind its E117
        for p in populations
    )

    return EngagementRun(
        engagement=engagement,
        template=template,
        registry_view=usable,
        populations=final_populations,
        claims=tuple(claims),
        reconciliations=reconciliations,
        clusters=clusters,
        verdicts=verdicts,
        compile_errors=compile_errors,
        contracts=contracts,
        snapshots=snapshots,
        timing_window=timing_window,
    )
