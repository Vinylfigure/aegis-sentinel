#!/usr/bin/env python3
"""Emit the FULL demo-engagement artifacts (VAL02; docs/EXECUTION-PLAN.md).

Runs the real pipeline end to end over the fixture tenant via
``aegis_sentinel.engagement.run_demo_engagement`` (compile → collect →
reconcile → evaluate) and writes ``artifacts/demo-engagement/``:

- ``verdicts.json`` — every sealed verdict record (all FIVE states:
  PASS / FAIL / UNKNOWN / EXCLUDED / EXCEPTION) plus the compile-error
  exhibits: the six-month E204 (Okta 90-day System Log vs the 181-day
  period) and the break-glass E117.
- ``populations.json`` — every lane population with its ladder state
  (RATIFIED terminations · DISCOVERED populations blocked by open
  deltas · the DEFINED gcp population behind its E117).
- ``reconciliation.json`` — per-population ReconciliationResults with
  all six buckets as first-class deltas, negative space included, and
  the diagnostic (never evidentiary) per-source counts.
- ``capability_registry.json`` — the ratified capability entries.
- ``manifest.json`` — the v1 ratified-snapshot summary
  (ratified_by "vinylfigure (Ratifier)").
- ``proof_graph.json`` — the ten-stage lineage for the TIMING FAIL
  verdict (commitment → requirement → claim → population → sources →
  reconciliation → contract → snapshot → assertion → verdict), node
  kinds and relations matching the frontend contract
  (web/src/data/engagement/proof_graph.json).

Deterministic by construction: every timestamp comes from the fixture
engagement (D-P3 — no wall clock anywhere in the pipeline) and output
is sorted-key JSON, so emitting twice is byte-identical
(tests/artifacts/test_emit_determinism.py, which also keeps the
committed artifacts current).

Run from the repo venv: ``python scripts/emit_demo_artifacts.py``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from aegis_sentinel.engagement import EngagementRun, run_demo_engagement
from aegis_sentinel.schema import SourceRole, VerdictState

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "artifacts" / "demo-engagement"

TIMING_ASSERTION = "TERM-TIMING.a"


def _write(path: Path, payload: Any) -> None:
    """Sorted keys, two-space indent, trailing newline — deterministic bytes."""
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _verdicts_payload(run: EngagementRun) -> dict[str, Any]:
    return {
        "engagement": run.engagement["engagement"],
        "manifest_version": run.engagement["manifest_version"],
        "verdicts": [v.model_dump(mode="json") for v in run.verdicts],
        "compile_errors": [
            {**error.model_dump(mode="json"), "rendered": error.render()}
            for error in run.compile_errors
        ],
    }


def _populations_payload(run: EngagementRun) -> dict[str, Any]:
    return {
        "engagement": run.engagement["engagement"],
        "populations": [p.model_dump(mode="json") for p in run.populations],
    }


def _reconciliation_payload(run: EngagementRun) -> dict[str, Any]:
    reconciliations = []
    for population_id in sorted(run.reconciliations):
        result = run.reconciliations[population_id]
        reconciliations.append(
            {
                "population_ref": result.population_ref,
                "canonical_identity_keys": list(result.canonical_identity_keys),
                # DIAGNOSTIC ONLY: counts are a smell test, never evidence
                # (docs/HANDOFF.md §2).
                "source_counts": dict(result.source_counts),
                "deltas": [d.model_dump(mode="json") for d in result.deltas],
                "members": list(result.members),
                "basis_complete": result.basis_complete,
                "basis_notes": list(result.basis_notes),
                "buckets": {
                    "intersection": list(result.intersection),
                    "left_only": list(result.left_only),
                    "right_only": list(result.right_only),
                    "conflicts": list(result.conflicts),
                    "unresolvable": list(result.unresolvable),
                    "excluded": list(result.excluded),
                },
                "diagnostics": list(result.diagnostics),
                "ladder_state": result.population.state.value,
            }
        )
    return {"engagement": run.engagement["engagement"], "reconciliations": reconciliations}


def _registry_payload(run: EngagementRun) -> dict[str, Any]:
    return {
        "entries": [
            entry.model_dump(mode="json")
            for entry in sorted(run.registry_view, key=lambda e: e.entry_id)
        ]
    }


def _manifest_payload(run: EngagementRun) -> dict[str, Any]:
    engagement = run.engagement
    states: dict[str, int] = {}
    for population in run.populations:
        states[population.state.value] = states.get(population.state.value, 0) + 1
    return {
        "manifest_version": engagement["manifest_version"],
        "snapshot_hash": engagement["ratified_manifest_snapshot_hash"],
        "ratified_by": engagement["ratified_by"],
        "ratified_at": engagement["ratified_at"],
        "engagement": engagement["engagement"],
        "period": engagement["period"],
        "boundary": engagement["boundary"],
        "notes": (
            "v1 ratified scope snapshot over the fixture tenant; the TIMING claim "
            "is evaluated over the re-scoped honest window "
            f"{run.timing_window.start.isoformat()}..{run.timing_window.end.isoformat()} "
            "(the six-month ask stays as the E204 exhibit)"
        ),
        "summary": {
            "claims": len(run.claims),
            "populations_by_state": dict(sorted(states.items())),
            "verdict_states_present": sorted({v.state.value for v in run.verdicts}),
            "compile_error_codes": [e.code for e in run.compile_errors],
        },
    }


def _proof_graph_payload(run: EngagementRun) -> list[dict[str, Any]]:
    """Ten-stage lineage for the TIMING FAIL verdict (frontend shape)."""
    verdict = run.verdict_for(TIMING_ASSERTION)
    claim = next(c for c in run.claims if c.claim_id == verdict.claim_ref)
    assertion = next(a for a in claim.assertions if a.assertion_id == TIMING_ASSERTION)
    population = next(p for p in run.populations if p.population_id == verdict.population_ref)
    reconciliation = run.reconciliations[population.population_id]
    contract = run.contracts["okta-system-log"]
    snapshot = run.snapshots["okta-system-log"]
    soc2 = next(m for m in claim.framework_mappings if m.framework == "SOC2")
    internal = next(m for m in claim.framework_mappings if m.framework == "internal")
    assert verdict.record_hash is not None and snapshot.snapshot_hash is not None
    assert contract.retrieved_at is not None
    contract_hash = contract.contract_hash or contract.compute_contract_hash()

    sources = sorted(population.sources, key=lambda s: s.source_id)
    source_nodes = [
        {
            "node_id": f"n-src-{i}",
            "kind": "source",
            "label": f"{source.source_id} — {source.role.value}",
            "ref": source.source_id,
        }
        for i, source in enumerate(sources, start=1)
    ]
    nodes = [
        {
            "node_id": "n-cmt",
            "kind": "commitment",
            "label": f"SOC 2 Type II — {soc2.control_id}",
            "ref": f"cmt-soc2-{soc2.control_id.lower()}",
        },
        {
            "node_id": "n-req",
            "kind": "requirement",
            "label": f"Revoke logical access on separation, timely ({internal.control_id})",
            "ref": f"req-{internal.control_id.lower()}",
        },
        {
            "node_id": "n-claim",
            "kind": "claim",
            "label": f"{claim.claim_id} — {claim.statement}",
            "ref": claim.claim_id,
        },
        {
            "node_id": "n-pop",
            "kind": "population",
            "label": (
                f"{population.name} · {population.type.value} · "
                f"{population.size} members · {population.state.value}"
            ),
            "ref": population.population_id,
        },
        *source_nodes,
        {
            "node_id": "n-rec",
            "kind": "reconciliation",
            "label": (
                f"rec-{population.population_id} — set reconciliation, "
                f"{len(reconciliation.deltas)} delta(s), "
                f"{len(reconciliation.open_deltas)} open"
            ),
            "ref": f"rec-{population.population_id}",
        },
        {
            "node_id": "n-eqc",
            "kind": "contract",
            "label": (
                f"EQC {contract.source_system} {contract.endpoint} — supports "
                + " · ".join(sorted(t.value for t in contract.supported_assertion_types))
            ),
            "ref": contract_hash,
        },
        {
            "node_id": "n-snap",
            "kind": "snapshot",
            "label": (
                f"WORM snapshot {contract.retrieved_at.date().isoformat()} — "
                f"sha256 {snapshot.snapshot_hash[:8]}…{snapshot.snapshot_hash[-4:]}"
            ),
            "ref": snapshot.snapshot_hash,
        },
        {
            "node_id": "n-assert",
            "kind": "assertion",
            "label": f"{assertion.assertion_id} — TIMING: {assertion.predicate_text}",
            "ref": assertion.assertion_id,
        },
        {
            "node_id": "n-verdict",
            "kind": "verdict",
            "label": f"{verdict.state.value} — {(verdict.message or '').split(';')[1].strip()}",
            "ref": verdict.record_hash,
        },
    ]
    role_relation = {
        SourceRole.AUTHORITATIVE: "derived_from",
        SourceRole.CONTRIBUTING: "derived_from",
        SourceRole.CORROBORATING: "corroborated_by",
        SourceRole.DISCOVERY: "discovered_by",
        SourceRole.EXCLUSION: "excluded_by",
    }
    edges = [
        {"from": "n-cmt", "to": "n-req", "relation": "imposes"},
        {"from": "n-req", "to": "n-claim", "relation": "mechanized_as"},
        {"from": "n-claim", "to": "n-pop", "relation": "scoped_over"},
        *(
            {
                "from": "n-pop",
                "to": node["node_id"],
                "relation": role_relation[source.role],
            }
            for node, source in zip(source_nodes, sources)
        ),
        *({"from": node["node_id"], "to": "n-rec", "relation": "feeds"} for node in source_nodes),
        {"from": "n-rec", "to": "n-eqc", "relation": "completeness_basis"},
        {"from": "n-eqc", "to": "n-snap", "relation": "collected_as"},
        {"from": "n-snap", "to": "n-assert", "relation": "supports"},
        {"from": "n-claim", "to": "n-assert", "relation": "decomposed_into"},
        {"from": "n-assert", "to": "n-verdict", "relation": "evaluated_to"},
    ]
    return [{"verdict_ref": verdict.record_hash, "nodes": nodes, "edges": edges}]


def emit(out_dir: Path) -> None:
    run = run_demo_engagement(ROOT)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write(out_dir / "verdicts.json", _verdicts_payload(run))
    _write(out_dir / "populations.json", _populations_payload(run))
    _write(out_dir / "reconciliation.json", _reconciliation_payload(run))
    _write(out_dir / "capability_registry.json", _registry_payload(run))
    _write(out_dir / "manifest.json", _manifest_payload(run))
    _write(out_dir / "proof_graph.json", _proof_graph_payload(run))

    states = ", ".join(f"{v.assertion_ref}={v.state.value}" for v in run.verdicts)
    codes = ", ".join(e.code for e in run.compile_errors)
    present = sorted({v.state.value for v in run.verdicts})
    assert set(present) == {s.value for s in VerdictState}, (
        f"five-state gate: expected all five verdict states, got {present}"
    )
    print(f"wrote {out_dir}: verdicts [{states}]; compile errors [{codes}]")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    emit(args.out)


if __name__ == "__main__":
    main()
