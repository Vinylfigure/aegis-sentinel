"""MCP01: the read-only Aegis MCP server.

Proves, against the committed demo-engagement artifacts:
(a) resources/list returns exactly the four artifacts;
(b) resources/read of verdicts round-trips byte-identical to the file;
(c) tools/list contains ONLY the query tool — any future mutating tool
    changes the asserted set and fails here;
(d) the query tool filters correctly;
(e) the mcp_server package contains no file-write calls (AST scan);
(f) an end-to-end stdio round-trip against a real subprocess;
plus: the package imports and fails cleanly without the optional mcp extra.
"""

from __future__ import annotations

import ast
import asyncio
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from aegis_sentinel.mcp_server import ARTIFACT_NAMES, ArtifactStore, artifact_uri
from aegis_sentinel.mcp_server.server import build_server, main

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = REPO_ROOT / "artifacts" / "demo-engagement"
PACKAGE_DIR = REPO_ROOT / "src" / "aegis_sentinel" / "mcp_server"

EXPECTED_URIS = {
    "aegis://demo-engagement/verdicts",
    "aegis://demo-engagement/reconciliation",
    "aegis://demo-engagement/registry",
    "aegis://demo-engagement/poisons",
}


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="module")
def server():
    return build_server(ARTIFACTS_DIR)


# (a) -- resources list exactly the four artifacts


def test_resources_list_exactly_four_artifacts(server):
    resources = _run(server.list_resources())
    assert {str(r.uri) for r in resources} == EXPECTED_URIS
    assert len(resources) == 4
    assert all(r.mime_type == "application/json" for r in resources)


# (b) -- resources/read round-trips byte-identical


def test_read_verdicts_round_trips_byte_identical(server):
    contents = list(_run(server.read_resource(artifact_uri("verdicts"))))
    assert len(contents) == 1
    committed = (ARTIFACTS_DIR / "verdicts.json").read_bytes()
    assert contents[0].content.encode("utf-8") == committed


@pytest.mark.parametrize("name", ARTIFACT_NAMES)
def test_read_every_artifact_round_trips(server, name):
    contents = list(_run(server.read_resource(artifact_uri(name))))
    committed = (ARTIFACTS_DIR / f"{name}.json").read_bytes()
    assert contents[0].content.encode("utf-8") == committed


# (c) -- the tool surface is exactly the one query tool


def test_tools_list_is_only_the_query_tool(server):
    tools = _run(server.list_tools())
    assert {t.name for t in tools} == {"query_verdicts"}


# (d) -- query tool filters correctly


def test_query_verdicts_filters():
    """verdicts.json now carries the full 11-record roster (walking-skeleton
    + poison run, Q17 issue #58) — every real status class present, so the
    status filter genuinely discriminates rather than trivially matching
    a single-record set."""
    store = ArtifactStore(root=ARTIFACTS_DIR)
    everything = store.query_verdicts()
    assert len(everything) == 11
    assert "vr-demo-engagement-0001" in {r["record_id"] for r in everything}

    pass_records = store.query_verdicts(status="PASS")
    assert pass_records == [r for r in everything if r["status"] == "PASS"]
    assert pass_records and all(r["status"] == "PASS" for r in pass_records)
    assert pass_records != everything  # non-PASS records exist now

    # every record in this engagement shares one control
    assert store.query_verdicts(control_id="AM-06") == everything
    assert store.query_verdicts(record_id="vr-demo-engagement-0001") == [
        r for r in everything if r["record_id"] == "vr-demo-engagement-0001"
    ]
    assert store.query_verdicts(control_id="AM-06", status="PASS") == pass_records

    fail_records = store.query_verdicts(status="FAIL")
    assert fail_records == [r for r in everything if r["status"] == "FAIL"]
    assert fail_records and all(r["status"] == "FAIL" for r in fail_records)

    assert store.query_verdicts(control_id="XX-99") == []
    assert store.query_verdicts(status="PASS", record_id="vr-nope") == []


def test_query_verdicts_via_server_call_tool(server):
    hit = _run(server.call_tool("query_verdicts", {"status": "PASS"}))
    assert not hit.is_error
    results = hit.structured_content["result"]
    assert results and all(r["status"] == "PASS" for r in results)
    assert any(r["record_id"] == "vr-demo-engagement-0001" for r in results)

    miss = _run(server.call_tool("query_verdicts", {"control_id": "XX-99"}))
    assert not miss.is_error
    assert miss.structured_content["result"] == []


def test_unknown_artifact_name_rejected():
    store = ArtifactStore(root=ARTIFACTS_DIR)
    with pytest.raises(KeyError):
        store.read_text("../../etc/passwd")


# (e) -- read-only by construction: AST scan for write calls

WRITE_ATTRS = {"write", "writelines", "write_text", "write_bytes"}
# Deletion/creation are mutations too (verifier probe: unlink/rmtree evaded
# the write-only scan). Conservative by attribute name — collisions like
# list.remove() are acceptable false positives in a read-only package.
MUTATE_ATTRS = {
    "unlink",
    "rmdir",
    "mkdir",
    "makedirs",
    "touch",
    "rename",
    "renames",
    "rmtree",
    "remove",
    "removedirs",
    "symlink_to",
    "hardlink_to",
}


def _open_mode_is_write(call: ast.Call) -> bool:
    mode = None
    if len(call.args) >= 2:
        mode = call.args[1]
    for kw in call.keywords:
        if kw.arg == "mode":
            mode = kw.value
    if mode is None:
        return False  # default mode "r"
    if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
        return any(c in mode.value for c in "wax+")
    return True  # non-constant mode: conservatively a violation


def _write_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    problems = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_open = (isinstance(func, ast.Name) and func.id == "open") or (
            isinstance(func, ast.Attribute) and func.attr == "open"
        )
        if is_open and _open_mode_is_write(node):
            problems.append(f"{path.name}:{node.lineno}: write-mode open()")
        if isinstance(func, ast.Attribute) and func.attr in WRITE_ATTRS | MUTATE_ATTRS:
            problems.append(f"{path.name}:{node.lineno}: .{func.attr}() call")
    return problems


def test_mcp_server_package_has_no_write_calls():
    files = sorted(PACKAGE_DIR.rglob("*.py"))
    assert files, f"no python files under {PACKAGE_DIR}"
    violations = [v for f in files for v in _write_violations(f)]
    assert violations == []


def test_write_scan_detects_writes():
    """The scanner itself must catch every banned shape (no vacuous pass)."""
    bad = (
        "open(p, 'w')\n"
        "open(p, mode='a')\n"
        "open(p, m)\n"
        "io.open(p, 'r+')\n"
        "path.write_text(s)\n"
        "path.write_bytes(b)\n"
        "fh.write(s)\n"
        "fh.writelines(xs)\n"
        "p.unlink()\n"
        "os.remove(p)\n"
        "shutil.rmtree(d)\n"
        "p.mkdir()\n"
        "os.rename(a, b)\n"
        "p.touch()\n"
    )
    tmp = ast.parse(bad)
    hits = []
    for node in ast.walk(tmp):
        if isinstance(node, ast.Call):
            func = node.func
            is_open = (isinstance(func, ast.Name) and func.id == "open") or (
                isinstance(func, ast.Attribute) and func.attr == "open"
            )
            if is_open and _open_mode_is_write(node):
                hits.append(node.lineno)
            if isinstance(func, ast.Attribute) and func.attr in WRITE_ATTRS | MUTATE_ATTRS:
                hits.append(node.lineno)
    assert hits == list(range(1, 15))


# -- optionality: the package imports and fails cleanly without mcp

GUARD_SNIPPET = """
import importlib.abc
import sys
from pathlib import Path


class BlockMcp(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "mcp" or fullname.startswith("mcp."):
            raise ModuleNotFoundError(f"blocked for test: {fullname}")
        return None


sys.meta_path.insert(0, BlockMcp())

import aegis_sentinel.mcp_server  # noqa: F401  (must import without mcp)
from aegis_sentinel.mcp_server.server import build_server

try:
    build_server(Path("artifacts/demo-engagement"))
except RuntimeError as exc:
    assert "aegis-sentinel[mcp]" in str(exc), exc
    print("GUARD-OK")
else:
    raise SystemExit("build_server unexpectedly succeeded without mcp")
"""


def _subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    src = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    return env


def test_package_imports_and_guards_without_mcp():
    proc = subprocess.run(
        [sys.executable, "-c", GUARD_SNIPPET],
        cwd=REPO_ROOT,
        env=_subprocess_env(),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "GUARD-OK" in proc.stdout


def test_main_rejects_bad_argv(tmp_path):
    assert main(["a", "b"]) == 64
    assert main([str(tmp_path / "missing")]) == 66


# (f) -- end-to-end stdio round-trip against a real subprocess


class _StdioClient:
    """Minimal newline-delimited JSON-RPC 2.0 client over a subprocess."""

    def __init__(self, proc: subprocess.Popen):
        self.proc = proc

    def send(self, message: dict) -> None:
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def request(self, req_id: int, method: str, params: dict | None = None) -> dict:
        message = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            message["params"] = params
        self.send(message)
        while True:
            line = self.proc.stdout.readline()
            assert line, f"server closed stdout awaiting response to {method}"
            reply = json.loads(line)
            if reply.get("id") == req_id:
                assert "error" not in reply, reply
                return reply["result"]


def _stdio_conversation(results: dict) -> None:
    proc = subprocess.Popen(
        [sys.executable, "-m", "aegis_sentinel.mcp_server", str(ARTIFACTS_DIR)],
        cwd=REPO_ROOT,
        env=_subprocess_env(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    results["proc"] = proc
    try:
        client = _StdioClient(proc)
        results["initialize"] = client.request(
            1,
            "initialize",
            {
                "protocolVersion": "2026-07-28",
                "capabilities": {},
                "clientInfo": {"name": "mcp01-test", "version": "0.0.0"},
            },
        )
        client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        results["resources"] = client.request(2, "resources/list")
        results["read"] = client.request(
            3, "resources/read", {"uri": "aegis://demo-engagement/verdicts"}
        )
        results["tools"] = client.request(4, "tools/list")
        results["call"] = client.request(
            5,
            "tools/call",
            {"name": "query_verdicts", "arguments": {"control_id": "AM-06"}},
        )
    finally:
        proc.stdin.close()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_stdio_end_to_end():
    results: dict = {}
    worker = threading.Thread(target=_stdio_conversation, args=(results,), daemon=True)
    worker.start()
    worker.join(timeout=90)
    if worker.is_alive():
        results["proc"].kill()
        worker.join(timeout=10)
        pytest.fail("stdio conversation timed out")

    assert results["initialize"]["serverInfo"]["name"] == "aegis-sentinel"

    uris = {r["uri"] for r in results["resources"]["resources"]}
    assert uris == EXPECTED_URIS

    committed = (ARTIFACTS_DIR / "verdicts.json").read_bytes()
    contents = results["read"]["contents"]
    assert len(contents) == 1
    assert contents[0]["text"].encode("utf-8") == committed

    assert {t["name"] for t in results["tools"]["tools"]} == {"query_verdicts"}

    call = results["call"]
    assert call.get("isError") is not True
    payload = json.loads(call["content"][0]["text"])
    assert payload["record_id"] == "vr-demo-engagement-0001"
    assert payload["control_id"] == "AM-06"
