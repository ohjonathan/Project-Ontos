"""Regression tests for MCP stdio stream routing.

Guards against the v4.1.0 blocker where `ontos serve` routed every JSON-RPC
response to stderr because `sys.stdout` was still aliased to `sys.stderr` when
FastMCP's stdio transport snapshotted the outbound stream.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import ontos

from tests.mcp import create_empty_workspace


INITIALIZE_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "regression", "version": "0"},
    },
}


def _run_serve(root: Path, request: dict) -> subprocess.CompletedProcess[str]:
    payload = json.dumps(request) + "\n"
    return subprocess.run(
        [sys.executable, "-m", "ontos", "serve", "--workspace", str(root)],
        input=payload,
        text=True,
        capture_output=True,
        timeout=15,
    )


def test_initialize_response_lands_on_stdout(tmp_path):
    root = create_empty_workspace(tmp_path)
    result = _run_serve(root, INITIALIZE_REQUEST)

    assert result.returncode == 0, (
        f"serve exited {result.returncode}; stderr={result.stderr[:400]!r}"
    )
    assert result.stdout.strip(), (
        f"JSON-RPC response missing from stdout; stderr was: {result.stderr[:400]!r}"
    )

    first_line = result.stdout.strip().splitlines()[0]
    response = json.loads(first_line)
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response, response


def test_stderr_contains_no_jsonrpc(tmp_path):
    root = create_empty_workspace(tmp_path)
    result = _run_serve(root, INITIALIZE_REQUEST)

    assert result.returncode == 0, (
        f"serve exited {result.returncode}; stderr={result.stderr[:400]!r}"
    )
    assert "jsonrpc" not in result.stderr, (
        f"JSON-RPC payload leaked to stderr: {result.stderr[:400]!r}"
    )


def test_server_info_version_matches_package_version(tmp_path):
    root = create_empty_workspace(tmp_path)
    result = _run_serve(root, INITIALIZE_REQUEST)

    response = json.loads(result.stdout.strip().splitlines()[0])
    server_info = response["result"]["serverInfo"]
    assert server_info["name"] == "Ontos"
    assert server_info["version"] == ontos.__version__, (
        f"serverInfo.version={server_info['version']!r} "
        f"expected ontos.__version__={ontos.__version__!r}"
    )
