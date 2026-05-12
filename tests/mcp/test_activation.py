"""MCP activation contract tests."""

from __future__ import annotations

import asyncio

from tests.mcp import build_server, create_workspace


def _call(server, name: str, args: dict):
    return asyncio.run(server.call_tool(name, args))


def test_activate_sets_session_state_and_returns_loaded_ids(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    activation = _call(server, "activate", {})
    overview = _call(server, "workspace_overview", {})

    assert activation.isError is False
    assert activation.structuredContent["status"] in {"usable", "usable_with_warnings"}
    assert activation.structuredContent["workspace"] == root.name
    assert activation.structuredContent["doc_count"] == 8
    assert activation.structuredContent["loaded_ids"]
    assert "_ontos_warning" not in activation.structuredContent
    assert "_ontos_warning" not in overview.structuredContent


def test_read_tool_warns_when_activation_was_skipped(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(server, "workspace_overview", {})

    assert result.isError is False
    assert result.structuredContent["_ontos_warning"] == (
        "Ontos activation not performed this MCP session; call activate first."
    )
