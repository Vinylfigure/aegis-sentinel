"""Mechanical enforcement of the architectural rule: no LLM client import
anywhere in the verdict path, and no nondeterminism in evaluate/ or
compile/. If an agent's output could change whether something passes, the
design is wrong — this test makes that a merge blocker instead of a
code-review hope.

Provenance: the AST-walk import check, the explicit file roster, and the
file_list_is_current companion test are salvaged from the prior
scaffold's gate at aegis-sentinel/tests/test_verdict_path_purity.py,
adapted to the v3 src-layout (src/aegis_sentinel/) and extended with the
D-P3 determinism bans (docs/DECISIONS.md) for evaluate/ and compile/.
Guardrail source: docs/HANDOFF.md section 3 ("No LLM calls anywhere in
collectors/ reconcile/ evaluate/ compile/").
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from purity_single import (
    STRICT_PACKAGES,
    VERDICT_PACKAGES,
    check_file,
    check_source,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "aegis_sentinel"
FIXTURES = ROOT / "tests" / "fixtures" / "purity"
CHECK_PURITY = ROOT / "scripts" / "check-purity.sh"

# The explicit roster: every .py under src/aegis_sentinel/ in the verdict
# packages {schema, capability, collectors, reconcile, evaluate, compile,
# manifest}. A new module joins this list (and .github/CODEOWNERS)
# deliberately — test_file_list_is_current fails until it does.
VERDICT_PATH_FILES = [
    "src/aegis_sentinel/capability/__init__.py",
    "src/aegis_sentinel/capability/entry.py",
    "src/aegis_sentinel/capability/registry.py",
    "src/aegis_sentinel/collectors/__init__.py",
    "src/aegis_sentinel/collectors/base.py",
    "src/aegis_sentinel/collectors/gcp.py",
    "src/aegis_sentinel/collectors/github.py",
    "src/aegis_sentinel/collectors/hris.py",
    "src/aegis_sentinel/collectors/okta.py",
    "src/aegis_sentinel/collectors/slack.py",
    "src/aegis_sentinel/compile/__init__.py",
    "src/aegis_sentinel/compile/errors.py",
    "src/aegis_sentinel/compile/typecheck.py",
    "src/aegis_sentinel/engagement/__init__.py",
    "src/aegis_sentinel/engagement/runner.py",
    "src/aegis_sentinel/evaluate/__init__.py",
    "src/aegis_sentinel/evaluate/assertions.py",
    "src/aegis_sentinel/evaluate/business_days.py",
    "src/aegis_sentinel/evaluate/minimal.py",
    "src/aegis_sentinel/manifest/__init__.py",
    "src/aegis_sentinel/manifest/instantiate.py",
    "src/aegis_sentinel/reconcile/__init__.py",
    "src/aegis_sentinel/reconcile/deltas.py",
    "src/aegis_sentinel/reconcile/identity.py",
    "src/aegis_sentinel/reconcile/minimal.py",
    "src/aegis_sentinel/reconcile/setops.py",
    "src/aegis_sentinel/schema/__init__.py",
    "src/aegis_sentinel/schema/canonical.py",
    "src/aegis_sentinel/schema/claim.py",
    "src/aegis_sentinel/schema/contract.py",
    "src/aegis_sentinel/schema/disposition.py",
    "src/aegis_sentinel/schema/lane.py",
    "src/aegis_sentinel/schema/population.py",
    "src/aegis_sentinel/schema/verdict.py",
]


def _is_strict(rel_path: str) -> bool:
    return Path(rel_path).parts[2] in STRICT_PACKAGES


@pytest.mark.parametrize("rel_path", VERDICT_PATH_FILES)
def test_roster_files_exist(rel_path: str) -> None:
    """A stale roster entry (file deleted or moved) must be pruned deliberately."""
    assert (ROOT / rel_path).is_file(), (
        f"{rel_path} is in VERDICT_PATH_FILES but does not exist; "
        "prune the roster (and .github/CODEOWNERS) deliberately."
    )


@pytest.mark.parametrize("rel_path", VERDICT_PATH_FILES)
def test_verdict_path_purity(rel_path: str) -> None:
    violations = check_file(ROOT / rel_path, strict=_is_strict(rel_path))
    assert not violations, (
        f"{rel_path} violates verdict-path purity (HANDOFF section 3 / D-P3):\n"
        + "\n".join(violations)
    )


def test_file_list_is_current() -> None:
    """If a new .py appears in a verdict package it must be added to
    VERDICT_PATH_FILES (and to .github/CODEOWNERS) deliberately.
    compile/ landed with TYP01; collectors/, reconcile/, and evaluate/
    (strict lane) landed with the walking skeleton. The loop enforces
    any future package the moment it appears, and skips missing
    directories gracefully."""
    known = set(VERDICT_PATH_FILES)
    for pkg in VERDICT_PACKAGES:
        pkg_dir = SRC / pkg
        if not pkg_dir.is_dir():
            continue
        for path in sorted(pkg_dir.rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            assert rel in known, (
                f"New verdict-path module {rel} is not registered; add it to "
                "VERDICT_PATH_FILES in tests/test_verdict_path_purity.py and "
                "to .github/CODEOWNERS."
            )


# --- gate-proving fixtures (never importable: stored as .py.txt) ----------


def test_fixture_llm_import_in_schema_flagged() -> None:
    """An anthropic import in a hypothetical schema file is flagged even in
    non-strict lanes (LLM clients are banned everywhere in the path)."""
    source = (FIXTURES / "bad_schema_llm_import.py.txt").read_text()
    violations = check_source(source, "src/aegis_sentinel/schema/hypothetical.py", strict=False)
    assert any("anthropic" in v for v in violations), violations


def test_fixture_datetime_now_in_evaluate_flagged() -> None:
    """A datetime.now() call in evaluate/ is flagged by the strict D-P3 lane,
    and is NOT an import-level violation in the base lane."""
    source = (FIXTURES / "bad_evaluate_datetime_now.py.txt").read_text()
    strict = check_source(source, "src/aegis_sentinel/evaluate/hypothetical.py", strict=True)
    assert any("datetime.datetime.now" in v for v in strict), strict
    base = check_source(source, "src/aegis_sentinel/schema/hypothetical.py", strict=False)
    assert base == [], base


def test_fixture_strict_bans_cover_aliases_and_environ() -> None:
    """Aliased imports must not dodge the AST resolver, and os.environ
    access (attribute or from-import) is flagged in strict lanes."""
    source = (FIXTURES / "bad_evaluate_aliased.py.txt").read_text()
    violations = check_source(source, "src/aegis_sentinel/compile/hypothetical.py", strict=True)
    joined = "\n".join(violations)
    assert "time.time" in joined, violations
    assert "os.environ" in joined, violations
    assert "uuid" in joined, violations


def test_fixture_clean_file_passes() -> None:
    source = (FIXTURES / "clean_evaluate.py.txt").read_text()
    assert check_source(source, "src/aegis_sentinel/evaluate/clean.py", strict=True) == []


def test_check_purity_script_via_subprocess(tmp_path: Path) -> None:
    """scripts/check-purity.sh: exit 0 on a clean file, nonzero with a clear
    message on a violating file."""
    clean = tmp_path / "clean_module.py"
    clean.write_text((FIXTURES / "clean_evaluate.py.txt").read_text())
    result = subprocess.run(["bash", str(CHECK_PURITY), str(clean)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

    bad = tmp_path / "bad_module.py"
    bad.write_text((FIXTURES / "bad_schema_llm_import.py.txt").read_text())
    result = subprocess.run(["bash", str(CHECK_PURITY), str(bad)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "PURITY VIOLATION" in result.stderr
    assert "anthropic" in result.stderr


def test_verify_quick_gates_purity_via_subprocess(tmp_path: Path) -> None:
    """verify.sh quick passes a clean .py and fails a seeded-bad .py (the
    bad fixture is ruff-clean so the purity gate is what bites)."""
    verify = ROOT / "scripts" / "verify.sh"
    env_path = str(Path(sys.executable).parent)

    clean = tmp_path / "clean_module.py"
    clean.write_text((FIXTURES / "clean_evaluate.py.txt").read_text())
    result = subprocess.run(
        ["bash", str(verify), "quick", str(clean)],
        capture_output=True,
        text=True,
        env={"PATH": env_path + ":/usr/bin:/bin"},
    )
    assert result.returncode == 0, result.stdout + result.stderr

    bad = tmp_path / "bad_module.py"
    bad.write_text((FIXTURES / "bad_schema_llm_import.py.txt").read_text())
    result = subprocess.run(
        ["bash", str(verify), "quick", str(bad)],
        capture_output=True,
        text=True,
        env={"PATH": env_path + ":/usr/bin:/bin"},
    )
    assert result.returncode != 0
    assert "PURITY VIOLATION" in result.stderr
