from tests.mcp import build_cache, build_server, create_workspace, invoke_tool, run_base_cli, run_mcp_cli

from ontos.mcp import tools


def test_tool_errors_use_normalized_envelope(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    result = invoke_tool(
        "get_document",
        cache,
        tools.get_document,
        document_id="missing_doc",
    )

    assert result.isError is True
    assert result.structuredContent["isError"] is True
    assert result.structuredContent["content"][0]["type"] == "text"


def test_invalid_compact_and_outside_path_errors(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    compact_result = invoke_tool(
        "context_map",
        cache,
        tools.context_map,
        compact="invalid",
    )
    path_result = invoke_tool(
        "get_document",
        cache,
        tools.get_document,
        path="../outside.md",
    )

    assert compact_result.isError is True
    assert path_result.isError is True


def test_help_and_stdout_safety_paths(tmp_path):
    root = create_workspace(tmp_path)

    help_result = run_base_cli(root, "serve", "--help")
    runtime_result = run_mcp_cli(root, "serve", "--workspace", ".")
    server = build_server(root)

    assert help_result.returncode == 0
    assert "usage: ontos serve" in help_result.stdout
    assert runtime_result.stdout == ""
    assert "workspace_overview" in server.instructions
