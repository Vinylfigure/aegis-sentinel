"""AST-level purity gate for the verdict path.

No module under src/aegis_sentinel/ may import an AI client or a network
stack: verdicts are pure functions of captured evidence (docs/EVALUATION.md
§3, item 4). This is an import check, not a call check — an import alone is
already a purity breach in the verdict path.
"""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src" / "aegis_sentinel"

FORBIDDEN_PREFIXES = (
    # AI clients
    "anthropic",
    "openai",
    "google.genai",
    "litellm",
    # network stacks
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "http",
    "socket",
)


def forbidden_imports(path):
    tree = ast.parse(path.read_text(), filename=str(path))
    hits = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        for name in names:
            if any(name == p or name.startswith(p + ".") for p in FORBIDDEN_PREFIXES):
                hits.append(f"{path}:{node.lineno} imports {name}")
    return hits


def test_verdict_path_has_no_ai_or_network_imports():
    modules = sorted(SRC.rglob("*.py"))
    assert modules, "src/aegis_sentinel is empty — the purity gate has nothing to guard"
    breaches = [hit for module in modules for hit in forbidden_imports(module)]
    assert not breaches, "\n".join(breaches)
