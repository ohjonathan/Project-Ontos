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


def test_get_context_bundle_pre_activate_warning_lands_in_warnings_list(tmp_path):
    # #115: `get_context_bundle` declares `warnings: List[str]` with
    # `additionalProperties: false`. The pre-activate reminder must land in
    # that list, not as an undeclared `_ontos_warning` key (which the MCP SDK
    # rejects against the strict output schema).
    root = create_workspace(tmp_path)
    server = build_server(root, include_bundle_tool=True)

    result = _call(server, "get_context_bundle", {"token_budget": 8192})

    assert result.isError is False
    assert "_ontos_warning" not in result.structuredContent
    warnings = result.structuredContent["warnings"]
    assert isinstance(warnings, list)
    assert "Ontos activation not performed this MCP session; call activate first." in warnings


def test_get_context_bundle_no_warning_after_activate(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root, include_bundle_tool=True)

    _call(server, "activate", {})
    result = _call(server, "get_context_bundle", {"token_budget": 8192})

    assert result.isError is False
    assert "_ontos_warning" not in result.structuredContent
    warnings = result.structuredContent["warnings"]
    assert "Ontos activation not performed this MCP session; call activate first." not in warnings
