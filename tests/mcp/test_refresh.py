from tests.mcp import build_cache, build_server, create_workspace, list_tools

from ontos.mcp import tools


def test_refresh_contract_and_annotations(tmp_path):
    cache = build_cache(create_workspace(tmp_path))
    revision_before = cache.snapshot_revision

    payload = tools.refresh(cache)
    tool_map = {tool.name: tool for tool in list_tools(build_server(cache.workspace_root))}
    refresh_tool = tool_map["refresh"]

    assert payload["refreshed"] is True
    assert payload["doc_count"] == 8
    assert payload["duration_ms"] >= 0
    assert cache.snapshot_revision == revision_before + 1
    assert refresh_tool.annotations.readOnlyHint is False
    assert refresh_tool.annotations.idempotentHint is False
    assert refresh_tool.annotations.destructiveHint is False


def test_server_lists_tools_and_instructions(tmp_path):
    cache = build_cache(create_workspace(tmp_path))
    server = build_server(cache.workspace_root)
    tool_map = {tool.name: tool for tool in list_tools(server)}

    assert len(tool_map) == 12
    assert "workspace_overview" in tool_map
    assert "scaffold_document" in tool_map
    assert "log_session" in tool_map
    assert "promote_document" in tool_map
    assert "rename_document" in tool_map
    assert "workspace_overview" in server.instructions
    assert "workspace" in tool_map["workspace_overview"].description
