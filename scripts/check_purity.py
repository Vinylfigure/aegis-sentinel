"""INFRA01 per-file purity gate, wired into verify.sh quick (the inner
loop) so a purity breach fails at edit time, not review time.

Bans everywhere under src/aegis_sentinel/: AI-client and network imports
(the verdict path is deterministic, PRD-v3 §5). Additionally bans, in
evaluate/ and compile/ packages (D-P3): datetime.now, random, uuid,
os.environ — clocks are explicit inputs and determinism is the contract.
Files outside src/aegis_sentinel/ are out of scope and exit 0. Stdlib
only: this runs from the PostToolUse hook with the system python3.
"""

import ast
import sys
from pathlib import Path

FORBIDDEN_IMPORT_PREFIXES = (
    "anthropic",
    "openai",
    "google.genai",
    "litellm",
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "http",
    "socket",
)

DETERMINISM_SCOPED_DIRS = ("evaluate", "compile")
DETERMINISM_BANNED_IMPORTS = ("random", "uuid")
DETERMINISM_BANNED_CALLS = {("datetime", "now"), ("datetime", "today"), ("os", "environ")}


def forbidden_uses(path: Path, in_determinism_scope: bool) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    problems = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        for name in names:
            if any(name == p or name.startswith(p + ".") for p in FORBIDDEN_IMPORT_PREFIXES):
                problems.append(f"line {node.lineno}: forbidden import {name}")
            if in_determinism_scope and name in DETERMINISM_BANNED_IMPORTS:
                problems.append(f"line {node.lineno}: nondeterministic import {name} (D-P3)")
        if in_determinism_scope and isinstance(node, ast.Attribute):
            base = node.value
            if isinstance(base, ast.Name) and (base.id, node.attr) in DETERMINISM_BANNED_CALLS:
                problems.append(f"line {node.lineno}: {base.id}.{node.attr} banned (D-P3)")
            # Alias-proof over-approximation: any .now()/.today() attribute
            # access is a clock read regardless of what the base is bound to
            # (dt.datetime.now, date.today, ...). Clocks are explicit inputs.
            elif node.attr in ("now", "today"):
                problems.append(f"line {node.lineno}: .{node.attr} clock access banned (D-P3)")
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_purity.py <file.py>", file=sys.stderr)
        return 64
    path = Path(argv[1]).resolve()
    parts = path.parts
    if "aegis_sentinel" not in parts or "src" not in parts:
        return 0
    scoped = any(d in parts for d in DETERMINISM_SCOPED_DIRS)
    problems = forbidden_uses(path, scoped)
    if problems:
        print(f"purity gate: {path}", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
