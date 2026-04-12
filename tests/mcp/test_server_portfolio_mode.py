from __future__ import annotations

import asyncio

from mcp.types import CallToolResult

from tests.mcp import build_server, create_workspace, list_tools


CORE_TOOLS = {
    "workspace_overview",
    "context_map",
    "get_document",
    "list_documents",
    "export_graph",
    "query",
    "health",
    "refresh",
}

WRITE_TOOLS = {
    "scaffold_document",
    "log_session",
    "promote_document",
}


class FakePortfolioIndex:
    def get_projects(self):
        return [
            {
                "slug": "workspace",
                "path": "/tmp/workspace",
                "status": "documented",
                "doc_count": 8,
                "last_scanned": "2026-04-11T00:00:00Z",
                "tags": [],
                "has_ontos": 1,
            }
        ]

    def search_fts(self, query, workspace, offset, limit):
        _ = (query, workspace, offset, limit)
        return {"total_hits": 0, "results": []}


def test_create_server_includes_bundle_tool_in_single_workspace_mode(tmp_path):
    root = create_workspace(tmp_path)

    server = build_server(root, include_bundle_tool=True)
    tool_map = {tool.name: tool for tool in list_tools(server)}

    assert set(tool_map) == CORE_TOOLS | WRITE_TOOLS | {"get_context_bundle"}
    assert len(tool_map) == 12
    assert tool_map["get_context_bundle"].annotations.readOnlyHint is True
    assert "workspace_id" in tool_map["get_context_bundle"].inputSchema["properties"]
    assert "token_budget" in tool_map["get_context_bundle"].inputSchema["properties"]


def test_create_server_registers_track_a_portfolio_matrix(tmp_path):
    root = create_workspace(tmp_path)

    server = build_server(
        root,
        portfolio_index=FakePortfolioIndex(),
        include_bundle_tool=True,
    )
    tool_map = {tool.name: tool for tool in list_tools(server)}

    expected = (
        CORE_TOOLS
        | WRITE_TOOLS
        | {"project_registry", "search", "get_context_bundle"}
    )

    assert set(tool_map) == expected
    assert len(tool_map) == 14
    assert tool_map["project_registry"].annotations.readOnlyHint is True
    assert tool_map["search"].annotations.readOnlyHint is True
    assert tool_map["get_context_bundle"].annotations.readOnlyHint is True

    for name in ("workspace_overview", "search", "project_registry", "get_context_bundle"):
        assert "workspace_id" in tool_map[name].inputSchema["properties"]


def test_single_workspace_call_to_portfolio_tool_returns_structured_error(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root, include_bundle_tool=True)
    tool_names = {tool.name for tool in list_tools(server)}

    assert "project_registry" not in tool_names
    assert "search" not in tool_names

    result = asyncio.run(server.call_tool("project_registry", {}))
    assert isinstance(result, CallToolResult)
    assert result.isError is True
    assert result.structuredContent["isError"] is True
    assert "E_PORTFOLIO_REQUIRED" in result.content[0].text
