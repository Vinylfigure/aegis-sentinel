"""Per-file verdict-path purity checker (AST-based, no regex).

Shared engine for tests/test_verdict_path_purity.py and the
scripts/check-purity.sh wrapper (which runs this module as a script on a
single file so the verify.sh quick lane can block an impure edit locally).

Provenance: AST-walk import extraction salvaged from the prior scaffold's
purity gate at aegis-sentinel/tests/test_verdict_path_purity.py, extended
here with alias-resolving call/attribute bans per docs/DECISIONS.md D-P3
(determinism discipline) and docs/HANDOFF.md section 3 (no LLM calls in
collectors/ reconcile/ evaluate/ compile/).

Rules:
- Base rules (every verdict-path file): no LLM-client or agent-transport
  imports (anthropic, openai, google.generativeai, litellm, mcp,
  aegis_sentinel.llm).
- Strict rules (evaluate/ and compile/ only, per D-P3): additionally no
  random, uuid, requests, httpx, urllib.request, socket imports; no calls
  to datetime.datetime.now/utcnow/today, datetime.date.today, or
  time.time; no os.environ access. Clock values are explicit inputs.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# Forbidden import prefixes in EVERY verdict-path file.
BASE_FORBIDDEN_IMPORTS: tuple[str, ...] = (
    "anthropic",
    "openai",
    "google.generativeai",
    "litellm",
    "mcp",
    "aegis_sentinel.llm",
)

# Additionally forbidden import prefixes in evaluate/ and compile/ (D-P3).
STRICT_FORBIDDEN_IMPORTS: tuple[str, ...] = (
    "random",
    "uuid",
    "requests",
    "httpx",
    "urllib.request",
    "socket",
)

# Fully-resolved call targets banned in evaluate/ and compile/ (D-P3).
STRICT_FORBIDDEN_CALLS: frozenset[str] = frozenset(
    {
        "datetime.datetime.now",
        "datetime.datetime.utcnow",
        "datetime.datetime.today",
        "datetime.date.today",
        "time.time",
    }
)

# Fully-resolved attribute accesses banned in evaluate/ and compile/ (D-P3).
STRICT_FORBIDDEN_ATTRIBUTES: frozenset[str] = frozenset({"os.environ"})

# The verdict-path packages under src/aegis_sentinel/ (HANDOFF section 3).
VERDICT_PACKAGES: tuple[str, ...] = (
    "schema",
    "capability",
    "collectors",
    "reconcile",
    "evaluate",
    "compile",
    "manifest",
)

# Packages where the strict D-P3 determinism bans apply.
STRICT_PACKAGES: tuple[str, ...] = ("evaluate", "compile")


def _matches_prefix(name: str, prefixes: tuple[str, ...]) -> str | None:
    for prefix in prefixes:
        if name == prefix or name.startswith(prefix + "."):
            return prefix
    return None


def _alias_map(tree: ast.Module) -> dict[str, str]:
    """Map local names to the fully-qualified thing they were bound to."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".")[0]
                full = alias.name if alias.asname else alias.name.split(".")[0]
                aliases[local] = full
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for alias in node.names:
                local = alias.asname or alias.name
                aliases[local] = f"{node.module}.{alias.name}"
    return aliases


def _resolve(node: ast.expr, aliases: dict[str, str]) -> str | None:
    """Resolve a Name/Attribute chain to a dotted name via the alias map."""
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    if isinstance(node, ast.Attribute):
        base = _resolve(node.value, aliases)
        if base is None:
            return None
        return f"{base}.{node.attr}"
    return None


def check_source(source: str, filename: str, strict: bool) -> list[str]:
    """Return a list of human-readable violations for one file's source."""
    tree = ast.parse(source, filename=filename)
    violations: list[str] = []

    import_prefixes = BASE_FORBIDDEN_IMPORTS + (STRICT_FORBIDDEN_IMPORTS if strict else ())
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module] + [f"{node.module}.{alias.name}" for alias in node.names]
        for name in names:
            hit = _matches_prefix(name, import_prefixes)
            if hit is not None:
                kind = "strict-lane" if hit in STRICT_FORBIDDEN_IMPORTS else "verdict-path"
                violations.append(
                    f"{filename}:{node.lineno}: forbidden {kind} import '{name}' "
                    f"(matches ban on '{hit}')"
                )
                break

    if strict:
        aliases = _alias_map(tree)
        seen: set[tuple[int, str]] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                target = _resolve(node.func, aliases)
                if target in STRICT_FORBIDDEN_CALLS:
                    violations.append(
                        f"{filename}:{node.lineno}: forbidden nondeterministic call "
                        f"'{target}()' (D-P3: clock values must be explicit inputs)"
                    )
            elif isinstance(node, (ast.Attribute, ast.Name)):
                target = _resolve(node, aliases)
                if target in STRICT_FORBIDDEN_ATTRIBUTES and (node.lineno, target) not in seen:
                    seen.add((node.lineno, target))
                    violations.append(
                        f"{filename}:{node.lineno}: forbidden access to '{target}' "
                        "(D-P3: environment reads banned in evaluate/ and compile/)"
                    )

    return sorted(set(violations))


def classify(path: Path) -> tuple[bool, bool]:
    """(should_check, strict) for a file path.

    - Files under src/aegis_sentinel/ in a verdict package: checked; strict
      if the package is evaluate/ or compile/.
    - Files under src/aegis_sentinel/ in any other subpackage (the LLM
      lane, e.g. aegis_sentinel/llm/): skipped — the lane may import LLM
      clients; the roster test keeps it out of the verdict path instead.
    - Anything else (tests, scripts, fixtures): base rules only, strict
      added when an 'evaluate' or 'compile' path segment is present.
    """
    parts = path.resolve().parts
    if "aegis_sentinel" in parts:
        idx = parts.index("aegis_sentinel")
        rest = parts[idx + 1 :]
        if len(rest) <= 1:  # top-level module such as aegis_sentinel/__init__.py
            return True, False
        pkg = rest[0]
        if pkg in VERDICT_PACKAGES:
            return True, pkg in STRICT_PACKAGES
        return False, False
    strict = any(part in STRICT_PACKAGES for part in path.parts)
    return True, strict


def check_file(path: Path, strict: bool | None = None) -> list[str]:
    should_check, inferred_strict = classify(path)
    if strict is None:
        if not should_check:
            return []
        strict = inferred_strict
    return check_source(path.read_text(), str(path), strict)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: purity_single.py <file.py>", file=sys.stderr)
        return 64
    path = Path(argv[1])
    if not path.is_file():
        print(f"purity: no such file: {path}", file=sys.stderr)
        return 64
    should_check, _ = classify(path)
    if not should_check:
        print(f"purity: {path}: outside the verdict path — skipped")
        return 0
    violations = check_file(path)
    if violations:
        print("PURITY VIOLATION — the verdict path must stay deterministic:", file=sys.stderr)
        for violation in violations:
            print(f"  {violation}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
