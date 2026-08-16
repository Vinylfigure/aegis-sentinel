"""MCP01: read-only Aegis MCP server over the committed demo-engagement artifacts.

Transport choice: the official Python MCP SDK (``mcp``, installed via the
optional ``aegis-sentinel[mcp]`` extra) speaking stdio. The SDK installed
cleanly from the index, so no hand-rolled JSON-RPC shim was needed. The SDK
import lives inside :func:`aegis_sentinel.mcp_server.server.build_server`
so the core package imports and works without the extra.

Read-only by construction: the server exposes the four demo-engagement
artifacts as resources (``aegis://demo-engagement/<name>``) plus a single
``query_verdicts`` filter tool. No module in this package performs any file
write — ``tests/test_mcp_server.py`` enforces that structurally with an AST
scan for write-mode ``open`` calls and ``write_*`` attribute calls.

Launch: ``python -m aegis_sentinel.mcp_server [artifacts-dir]`` (default
``artifacts/demo-engagement``); the directory comes from argv, never the
environment.
"""

from aegis_sentinel.mcp_server.artifacts import ARTIFACT_NAMES, ArtifactStore, artifact_uri

__all__ = ["ARTIFACT_NAMES", "ArtifactStore", "artifact_uri"]
