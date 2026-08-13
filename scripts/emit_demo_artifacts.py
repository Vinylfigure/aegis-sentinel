#!/usr/bin/env python3
"""Emit the walking-skeleton demo artifacts (docs/EXECUTION-PLAN.md).

Runs the first end-to-end slice over the fixture tenant
(``tests/fixtures/tenants/``): compile the termination lane over the
engagement's six-month period (which produces the real E204 — the Okta
90-day System Log cannot cover 181 days), execute the HRIS collector
against the fixture feed, reconcile the terminations population, and
evaluate the TA-1 feed-completeness assertion pair into sealed verdict
records. Writes ``artifacts/demo-engagement/``:

- ``verdicts.json`` — the verdict records (a real PASS and a real
  UNKNOWN) plus the compile-errors array (the real E204);
- ``populations.json`` — the terminations population at ladder state
  DISCOVERED with its canonical member list and six bucket lists;
- ``capability_registry.json`` — the ratified capability entries.

Deterministic by construction: every timestamp comes from the fixture
engagement (``tests/fixtures/tenants/engagement.json``) — never a wall
clock — and output is sorted-key JSON, so emitting twice is
byte-identical (tests/artifacts/test_emit_determinism.py, which also
keeps the committed artifacts current).

Run from the repo venv: ``python scripts/emit_demo_artifacts.py``.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from aegis_sentinel.capability import Registry
from aegis_sentinel.collectors import FixtureTransport, HrisTerminationsCollector
from aegis_sentinel.compile import CompileResult, compile_program, executable_collectors
from aegis_sentinel.evaluate import evaluate_feed_claim
from aegis_sentinel.manifest import instantiate_lane
from aegis_sentinel.reconcile import SourceMembers, reconcile_population
from aegis_sentinel.schema import LaneTemplate, Period

ROOT = Path(__file__).resolve().parents[1]
TENANTS_DIR = ROOT / "tests" / "fixtures" / "tenants"
DEFAULT_OUT = ROOT / "artifacts" / "demo-engagement"

#: The five fixture systems (PRD-v3 §6), keyed by lane node system_ref.
SYSTEMS = {"hris": "hris", "okta": "okta", "github": "github", "gcp": "gcp", "slack": "slack"}

FEED_CLAIM = "TERM.feed-completeness"
TERMINATIONS_POPULATION = "TERM.terminations"


def load_engagement() -> dict[str, Any]:
    return json.loads((TENANTS_DIR / "engagement.json").read_text(encoding="utf-8"))


def _write(path: Path, payload: dict[str, Any]) -> None:
    """Sorted keys, two-space indent, trailing newline — deterministic bytes."""
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _compile_errors(result: CompileResult) -> list[dict[str, Any]]:
    return [
        {**error.model_dump(mode="json"), "rendered": error.render()} for error in result.errors
    ]


def emit(out_dir: Path) -> None:
    engagement = load_engagement()
    retrieved_at = datetime.fromisoformat(engagement["retrieved_at"])
    evaluated_at = datetime.fromisoformat(engagement["evaluated_at"])
    period = Period(
        start=date.fromisoformat(engagement["period"]["start"]),
        end=date.fromisoformat(engagement["period"]["end"]),
    )

    template = LaneTemplate.model_validate_json(
        (ROOT / "templates" / "lanes" / "termination.json").read_text(encoding="utf-8")
    )
    registry = Registry.load(ROOT / "registry" / "capabilities")
    usable = registry.usable()

    populations, claims = instantiate_lane(template, SYSTEMS, period)
    result = compile_program(claims, populations, usable)

    # Compile-integrity gate (PRD-v3 §7): only error-free claims yield
    # executable plans. TA-1's assertion pair both matched the HRIS feed
    # entry over the same population — one collection serves both.
    plans = [p for p in executable_collectors(result) if p.claim_ref == FEED_CLAIM]
    plan = plans[0]

    collector = HrisTerminationsCollector(FixtureTransport(TENANTS_DIR))
    snapshot = collector.collect(plan, retrieved_at)
    contract = collector.contract(plan, engagement["tenant"], retrieved_at)
    events = collector.events(snapshot)

    population = next(p for p in populations if p.population_id == TERMINATIONS_POPULATION)
    reconciliation = reconcile_population(
        population,
        [
            SourceMembers(
                source_id=plan.source_id,
                complete=snapshot.complete,
                notes=snapshot.incompleteness,
                member_ids=tuple(e.employee_id for e in events),
            )
        ],
    )

    claim = next(c for c in claims if c.claim_id == FEED_CLAIM)
    assert snapshot.snapshot_hash is not None  # sealed by collect()
    verdicts = evaluate_feed_claim(
        claim,
        reconciliation,
        contract,
        manifest_version=engagement["manifest_version"],
        manifest_snapshot_hash=engagement["ratified_manifest_snapshot_hash"],
        collection_snapshot_hash=snapshot.snapshot_hash,
        evaluated_at=evaluated_at,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    _write(
        out_dir / "verdicts.json",
        {
            "engagement": engagement["engagement"],
            "manifest_version": engagement["manifest_version"],
            "verdicts": [v.model_dump(mode="json") for v in verdicts],
            "compile_errors": _compile_errors(result),
        },
    )
    _write(
        out_dir / "populations.json",
        {
            "engagement": engagement["engagement"],
            "populations": [reconciliation.model_dump(mode="json")],
        },
    )
    _write(
        out_dir / "capability_registry.json",
        {
            "entries": [
                entry.model_dump(mode="json") for entry in sorted(usable, key=lambda e: e.entry_id)
            ]
        },
    )

    states = ", ".join(f"{v.assertion_ref}={v.state.value}" for v in verdicts)
    codes = ", ".join(e.code for e in result.errors)
    print(f"wrote {out_dir}: verdicts [{states}]; compile errors [{codes}]")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    emit(args.out)


if __name__ == "__main__":
    main()
