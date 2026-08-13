"""VAL01 — mutation-suite harness core.

Provenance: docs/PRD-v3.md §6 (the six poison cases seeded into the V1
termination lane) and §7 (headline metric: **assurance defect detection
rate** — mutated defects that produce compile-error / UNKNOWN / FAIL
divided by defects introduced; any silent PASS is a build-stopping bug).
Acceptance: docs/HANDOFF.md §4 VAL01 — detection rate computed, and a
deliberately-silent-PASS fixture fails the build (the harness bites).

Design:

- Fixtures live in ``tests/fixtures/mutations/<poison>/`` and carry a
  closed-shape ``expected_outcome.json`` (parsed by :class:`Outcome`).
- A :class:`PipelineRunner` (protocol) turns a fixture directory into an
  observed :class:`Outcome`. Runners are registered per poison in
  :data:`RUNNER_REGISTRY` by the tasks that build the pipeline. TYP01
  registered the first real runner (:class:`BreakglassCompileRunner` —
  the break-glass poison is detected by the actual compiler); VAL02
  wires the rest.
- A fixture with no registered runner is counted ``runnable=False``
  (pending) — it is **never** silently counted as detected, and the
  detection rate is computed only over runnable fixtures. With zero
  runnable fixtures the rate is ``None`` (not meaningful), never 100%.

This is harness infrastructure, not the verdict path: nothing here
produces a verdict, and nothing under ``src/`` imports it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from functools import cache
from pathlib import Path
from typing import Callable, Mapping, Protocol

from aegis_sentinel.capability import Registry
from aegis_sentinel.compile import compile_program
from aegis_sentinel.engagement import EngagementRun, run_demo_engagement
from aegis_sentinel.manifest import instantiate_lane
from aegis_sentinel.schema import (
    DerivationRule,
    LaneTemplate,
    Period,
    Source,
    SourceRole,
)
from aegis_sentinel.schema.verdict import UnknownWhyCode, VerdictState

REPO_ROOT = Path(__file__).resolve().parents[2]
MUTATIONS_DIR = REPO_ROOT / "tests" / "fixtures" / "mutations"

#: The six playbook poisons (docs/PRD-v3.md §6). Discovery must find
#: exactly this set — a missing or extra fixture directory is an error.
EXPECTED_POISONS = frozenset(
    {
        "breakglass-cloud-account",
        "contractor-absent-hris",
        "delayed-revocation",
        "dormant-github-local-account",
        "failed-identity-join",
        "legitimate-exception",
    }
)

_OUTCOME_KEYS = frozenset({"detection", "verdict_state", "why_code", "e_code"})
_DETECTIONS = frozenset({"COMPILE_ERROR", "VERDICT"})


class MalformedOutcomeError(ValueError):
    """An outcome mapping violated the closed expected-outcome shape."""


@dataclass(frozen=True)
class Outcome:
    """One pipeline outcome: a compile error or a verdict.

    Closed shape shared by expected outcomes (``expected_outcome.json``)
    and observed outcomes (returned by runners):

    - ``detection == "COMPILE_ERROR"`` -> ``e_code`` set (e.g. ``E117``),
      ``verdict_state`` and ``why_code`` are ``None``.
    - ``detection == "VERDICT"`` -> ``verdict_state`` set; ``why_code``
      set iff the state is UNKNOWN; ``e_code`` is ``None``.
    """

    detection: str
    verdict_state: VerdictState | None
    why_code: UnknownWhyCode | None
    e_code: str | None

    def __post_init__(self) -> None:
        if self.detection not in _DETECTIONS:
            raise MalformedOutcomeError(f"detection must be one of {sorted(_DETECTIONS)}")
        if self.detection == "COMPILE_ERROR":
            if not self.e_code:
                raise MalformedOutcomeError("COMPILE_ERROR outcome requires an e_code")
            if self.verdict_state is not None or self.why_code is not None:
                raise MalformedOutcomeError(
                    "COMPILE_ERROR outcome carries no verdict_state/why_code"
                )
        else:  # VERDICT
            if self.e_code is not None:
                raise MalformedOutcomeError("VERDICT outcome carries no e_code")
            if self.verdict_state is None:
                raise MalformedOutcomeError("VERDICT outcome requires a verdict_state")
            if (self.verdict_state is VerdictState.UNKNOWN) != (self.why_code is not None):
                raise MalformedOutcomeError("why_code is required iff verdict_state is UNKNOWN")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "Outcome":
        """Parse the closed JSON shape; unknown or missing keys are rejected."""
        if set(raw) != _OUTCOME_KEYS:
            raise MalformedOutcomeError(
                f"outcome keys must be exactly {sorted(_OUTCOME_KEYS)}, got {sorted(raw)}"
            )
        state = raw["verdict_state"]
        why = raw["why_code"]
        return cls(
            detection=str(raw["detection"]),
            verdict_state=None if state is None else VerdictState(state),
            why_code=None if why is None else UnknownWhyCode(why),
            e_code=None if raw["e_code"] is None else str(raw["e_code"]),
        )

    @property
    def is_silent_pass(self) -> bool:
        return self.detection == "VERDICT" and self.verdict_state is VerdictState.PASS


@dataclass(frozen=True)
class MutationFixture:
    """One poison fixture directory plus its parsed expected outcome."""

    poison: str
    path: Path
    expected: Outcome


class PipelineRunner(Protocol):
    """Runs the (future) pipeline against one fixture directory.

    Implementations are registered in :data:`RUNNER_REGISTRY` by the
    tasks that build the pipeline (TYP01/EVAL01 wiring lands in VAL02).
    """

    def run(self, fixture_dir: Path) -> Outcome: ...  # pragma: no cover


#: poison name -> implemented runner. VAL01 shipped this empty; tasks
#: that build the pipeline register real runners below (TYP01: the
#: break-glass compile runner; VAL02 wires the rest).
RUNNER_REGISTRY: dict[str, PipelineRunner] = {}


def register_runner(poison: str, runner: PipelineRunner) -> None:
    if poison not in EXPECTED_POISONS:
        raise KeyError(f"unknown poison {poison!r}; expected one of {sorted(EXPECTED_POISONS)}")
    RUNNER_REGISTRY[poison] = runner


def load_expected_outcome(fixture_dir: Path) -> Outcome:
    """Load and validate ``expected_outcome.json`` for one poison.

    A poison's expected outcome may never be a silent PASS — every
    playbook mutation must surface as compile-error / UNKNOWN / FAIL /
    EXCEPTION (docs/PRD-v3.md §7).
    """
    raw = json.loads((fixture_dir / "expected_outcome.json").read_text(encoding="utf-8"))
    outcome = Outcome.from_mapping(raw)
    if outcome.is_silent_pass:
        raise MalformedOutcomeError(
            f"{fixture_dir.name}: a poison fixture may not expect PASS (silent-PASS ban)"
        )
    return outcome


def discover_fixtures(mutations_dir: Path = MUTATIONS_DIR) -> tuple[MutationFixture, ...]:
    """Discover the poison fixture directories; the set must be exact."""
    dirs = sorted(p for p in mutations_dir.iterdir() if p.is_dir())
    found = {p.name for p in dirs}
    if found != EXPECTED_POISONS:
        raise MalformedOutcomeError(
            f"poison fixture set mismatch: missing={sorted(EXPECTED_POISONS - found)} "
            f"extra={sorted(found - EXPECTED_POISONS)}"
        )
    return tuple(
        MutationFixture(poison=p.name, path=p, expected=load_expected_outcome(p)) for p in dirs
    )


@dataclass(frozen=True)
class PoisonResult:
    """Per-poison harness result. ``detected`` is None while not runnable."""

    poison: str
    runnable: bool
    detected: bool | None
    expected: Outcome
    observed: Outcome | None


@dataclass(frozen=True)
class SuiteReport:
    """Suite-level report over all six poisons."""

    results: tuple[PoisonResult, ...]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def runnable(self) -> tuple[PoisonResult, ...]:
        return tuple(r for r in self.results if r.runnable)

    @property
    def detected_count(self) -> int:
        return sum(1 for r in self.runnable if r.detected)

    @property
    def detection_rate(self) -> float | None:
        """assurance_defect_detection_rate = detected / runnable.

        ``None`` when nothing is runnable — a rate over zero fixtures is
        not meaningful and is never reported as 100%.
        """
        runnable = self.runnable
        if not runnable:
            return None
        return self.detected_count / len(runnable)

    def table(self) -> str:
        """Per-poison table plus the headline line, for the pytest report."""
        header = f"{'poison':<32} {'runnable':<9} {'detected':<9} expected -> observed"
        lines = [header, "-" * len(header)]
        for r in self.results:
            detected = "-" if r.detected is None else ("yes" if r.detected else "NO")
            expected = _summarize(r.expected)
            observed = "(no runner registered)" if r.observed is None else _summarize(r.observed)
            lines.append(
                f"{r.poison:<32} {'yes' if r.runnable else 'no':<9} {detected:<9} "
                f"{expected} -> {observed}"
            )
        rate = self.detection_rate
        n_runnable = len(self.runnable)
        if rate is None:
            lines.append(
                f"{n_runnable}/{self.total} poisons runnable — detection rate not yet meaningful"
            )
        else:
            lines.append(
                f"assurance_defect_detection_rate = {self.detected_count}/{n_runnable} "
                f"= {rate:.0%} over {n_runnable} runnable of {self.total} poisons"
            )
        return "\n".join(lines)


def _summarize(o: Outcome) -> str:
    if o.detection == "COMPILE_ERROR":
        return f"COMPILE_ERROR {o.e_code}"
    assert o.verdict_state is not None
    why = f"/{o.why_code.value}" if o.why_code is not None else ""
    return f"VERDICT {o.verdict_state.value}{why}"


def evaluate_suite(
    fixtures: tuple[MutationFixture, ...],
    registry: Mapping[str, PipelineRunner],
) -> SuiteReport:
    """Run every fixture that has a registered runner; score strictly.

    Detected means the observed outcome equals the expected outcome
    exactly (state, why-code, e-code). A silent PASS can never count as
    detected: no poison's expected outcome is PASS (enforced at load),
    so an always-PASS runner scores undetected by construction.
    """
    results: list[PoisonResult] = []
    for fixture in fixtures:
        runner = registry.get(fixture.poison)
        if runner is None:
            results.append(
                PoisonResult(
                    poison=fixture.poison,
                    runnable=False,
                    detected=None,
                    expected=fixture.expected,
                    observed=None,
                )
            )
            continue
        observed = runner.run(fixture.path)
        detected = observed == fixture.expected and not observed.is_silent_pass
        results.append(
            PoisonResult(
                poison=fixture.poison,
                runnable=True,
                detected=detected,
                expected=fixture.expected,
                observed=observed,
            )
        )
    return SuiteReport(results=tuple(results))


class BreakglassCompileRunner:
    """Runs the REAL compiler (TYP01) against the break-glass poison.

    The poison (docs/PRD-v3.md §6; this fixture's README): a break-glass
    GCP account provisioned outside every IdP-derived population. Encoded
    as the mutation the README describes — the GCP accounts population's
    derivation rule references ``breakglass.config``, a source with no
    ratified capability entry — so the claim over that population must
    refuse to compile with E117 before any collector runs.

    Honest by construction: if the compiler someday stopped erroring,
    this runner returns a silent PASS outcome, which the harness scores
    undetected and the build gate turns red.
    """

    _MISSING_SOURCE = "breakglass.config"
    _POISONED_POPULATION = "TERM.gcp.accounts"
    _SYSTEMS = {"hris": "hris", "okta": "okta", "github": "github", "gcp": "gcp", "slack": "slack"}

    def run(self, fixture_dir: Path) -> Outcome:
        template_path = REPO_ROOT / "templates" / "lanes" / "termination.json"
        template = LaneTemplate.model_validate_json(template_path.read_text(encoding="utf-8"))
        period = Period(start=date(2026, 5, 1), end=date(2026, 6, 29))  # inside Okta's 90d
        populations, claims = instantiate_lane(template, self._SYSTEMS, period)
        poisoned = [self._poison(p) for p in populations]
        view = Registry.load(REPO_ROOT / "registry" / "capabilities").usable()
        result = compile_program(claims, poisoned, view)
        errors = [e for compilation in result.claims for e in compilation.errors]
        if not errors:  # poison missed -> silent PASS -> scored undetected
            return Outcome(
                detection="VERDICT", verdict_state=VerdictState.PASS, why_code=None, e_code=None
            )
        return Outcome(
            detection="COMPILE_ERROR", verdict_state=None, why_code=None, e_code=errors[0].code
        )

    def _poison(self, population):
        if population.population_id != self._POISONED_POPULATION:
            return population
        rule = population.derivation_rule
        return population.model_copy(
            update={
                "sources": population.sources
                + (Source(source_id=self._MISSING_SOURCE, role=SourceRole.CONTRIBUTING),),
                "derivation_rule": DerivationRule(
                    rule_text=rule.rule_text
                    + "; union break-glass accounts enumerated by breakglass.config",
                    source_refs=rule.source_refs + (self._MISSING_SOURCE,),
                ),
            }
        )


register_runner("breakglass-cloud-account", BreakglassCompileRunner())


# ---- VAL02: the five verdict-path poisons, against the REAL pipeline -----
#
# One deterministic engagement run (compile → collect → reconcile →
# evaluate over the fixture tenants; aegis_sentinel.engagement.runner)
# serves all five runners. Each runner first verifies that ITS poison's
# specific driver is present (the delta / the named member in the
# evidence), then reports the pipeline's verdict for the affected
# assertion. If the driver is missing — the pipeline stopped seeing the
# poison — the runner returns a silent PASS outcome, which the harness
# scores undetected and the build gate turns red.


@cache
def _engagement_run() -> EngagementRun:
    return run_demo_engagement(REPO_ROOT)


def _verdict_outcome(record) -> Outcome:
    return Outcome(
        detection="VERDICT",
        verdict_state=record.state,
        why_code=record.why_code,
        e_code=None,
    )


_SILENT_PASS = Outcome(
    detection="VERDICT", verdict_state=VerdictState.PASS, why_code=None, e_code=None
)


@dataclass(frozen=True)
class VerdictPoisonRunner:
    """Reports one assertion's REAL verdict, gated on the poison's driver.

    ``driver`` inspects the engagement run and returns True iff the
    poison's specific footprint is present (e.g. the negative-space
    delta exists, or the poisoned member is named in the verdict
    evidence). No driver → silent PASS → undetected.
    """

    assertion_ref: str
    driver: "Callable[[EngagementRun], bool]"

    def run(self, fixture_dir: Path) -> Outcome:
        run = _engagement_run()
        record = run.verdict_for(self.assertion_ref)
        if not self.driver(run):
            return _SILENT_PASS
        return _verdict_outcome(record)


def _contractor_negative_space(run: EngagementRun) -> bool:
    """The contractor's identity is a left_only negative-space delta:
    present downstream, absent from the authoritative HRIS source, and
    NOT dispositioned (the FAIL-vs-UNKNOWN ruling stands as UNKNOWN)."""
    deltas = run.reconciliations["TERM.identity-join"].deltas
    return any(
        d.bucket == "left_only"
        and d.member_key == "ctr.blake.morgan@example-vendor.com"
        and "hris-termination-feed" in d.sources_absent
        and d.disposition is None
        for d in deltas
    )


def _dormant_local_account_named(run: EngagementRun) -> bool:
    record = run.verdict_for("TERM-GITHUB.a")
    return record.message is not None and "bm-legacy-bot" in record.message


def _unresolvable_join(run: EngagementRun) -> bool:
    """The maiden-name orphan lands in the unresolvable bucket AND the
    affected member is named in the TERM-FEED.b evidence."""
    deltas = run.reconciliations["TERM.identity-join"].deltas
    orphan = any(d.bucket == "unresolvable" and "dana.kowalski" in d.member_key for d in deltas)
    record = run.verdict_for("TERM-FEED.b")
    return orphan and record.message is not None and "E-1033" in record.message


def _delayed_revocation_named(run: EngagementRun) -> bool:
    record = run.verdict_for("TERM-TIMING.a")
    return (
        record.message is not None
        and "marcus.webb" in record.message
        and "9 business day" in record.message
    )


def _exception_dispositioned(run: EngagementRun) -> bool:
    record = run.verdict_for("TERM-SLACK.a")
    return record.disposition_ref == "DISP-2026-114"


register_runner(
    "contractor-absent-hris",
    VerdictPoisonRunner("TERM-JOIN.a", _contractor_negative_space),
)
register_runner(
    "dormant-github-local-account",
    VerdictPoisonRunner("TERM-GITHUB.a", _dormant_local_account_named),
)
register_runner(
    "failed-identity-join",
    VerdictPoisonRunner("TERM-FEED.b", _unresolvable_join),
)
register_runner(
    "delayed-revocation",
    VerdictPoisonRunner("TERM-TIMING.a", _delayed_revocation_named),
)
register_runner(
    "legitimate-exception",
    VerdictPoisonRunner("TERM-SLACK.a", _exception_dispositioned),
)


class MutationDetectionFailure(AssertionError):
    """Raised when a runnable poison went undetected — fails the build."""


def assert_suite_detects(report: SuiteReport) -> None:
    """The build gate: any undetected runnable poison raises.

    With zero runnable fixtures this returns without raising (the
    pipeline is not built yet); callers surface that explicitly via
    :meth:`SuiteReport.table`, which reports the rate as not meaningful.
    """
    rate = report.detection_rate
    if rate is None:
        return
    if rate != 1.0:
        missed = [r.poison for r in report.runnable if not r.detected]
        raise MutationDetectionFailure(
            f"assurance_defect_detection_rate={rate:.0%} < 100%; undetected poisons: {missed}\n"
            + report.table()
        )
