"""Server wiring: artifacts as MCP resources plus the one query tool.

The ``mcp`` SDK import is confined to :func:`build_server` so importing
this module never requires the optional extra; only actually building or
running the server does. Read-only by construction: resources call
``ArtifactStore.read_text`` and the sole tool filters verdicts in memory.
"""

from __future__ import annotations

import sys
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from aegis_sentinel.mcp_server.artifacts import ARTIFACT_NAMES, ArtifactStore, artifact_uri

if TYPE_CHECKING:  # pragma: no cover
    from mcp.server.mcpserver import MCPServer

DEFAULT_ARTIFACTS_DIR = Path("artifacts") / "demo-engagement"

_DESCRIPTIONS = {
    "verdicts": "Verdict records emitted by the demo engagement run.",
    "reconciliation": "Population reconciliation buckets and boundary exclusions.",
    "registry": "Capability registry entries and compile errors.",
    "poisons": "Poison-suite cases exercising the verdict path.",
}


def build_server(root: Path) -> "MCPServer":
    """A read-only MCP server over the artifacts directory ``root``."""
    try:
        from mcp.server.mcpserver import MCPServer
        from mcp.server.mcpserver.resources import FunctionResource
    except ImportError as exc:  # pragma: no cover - exercised via subprocess test
        raise RuntimeError(
            "the MCP SDK is not installed; install the optional extra: "
            "pip install 'aegis-sentinel[mcp]'"
        ) from exc

    store = ArtifactStore(root=root)
    server = MCPServer(
        name="aegis-sentinel",
        instructions=(
            "Read-only access to the committed Aegis demo-engagement artifacts. "
            "Resources expose the raw JSON; query_verdicts filters verdict records."
        ),
    )
    for name in ARTIFACT_NAMES:
        server.add_resource(
            FunctionResource(
                uri=artifact_uri(name),
                name=name,
                description=_DESCRIPTIONS[name],
                mime_type="application/json",
                fn=partial(store.read_text, name),
            )
        )

    @server.tool(
        name="query_verdicts",
        description=(
            "Filter the verdict records by control_id, status, and/or record_id; "
            "all filters optional and conjunctive. Read-only."
        ),
    )
    def query_verdicts(
        control_id: str | None = None,
        status: str | None = None,
        record_id: str | None = None,
    ) -> list[dict]:
        return store.query_verdicts(control_id=control_id, status=status, record_id=record_id)

    return server


def main(argv: list[str] | None = None) -> int:
    """Entry point: ``python -m aegis_sentinel.mcp_server [artifacts-dir]``.

    The artifacts directory comes from argv (never the environment) and
    defaults to ``artifacts/demo-engagement`` relative to the CWD.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        print("usage: python -m aegis_sentinel.mcp_server [artifacts-dir]", file=sys.stderr)
        return 64
    root = Path(args[0]) if args else DEFAULT_ARTIFACTS_DIR
    if not root.is_dir():
        print(f"artifacts directory not found: {root}", file=sys.stderr)
        return 66
    build_server(root).run(transport="stdio")
    return 0
