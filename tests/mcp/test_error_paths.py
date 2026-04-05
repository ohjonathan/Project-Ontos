from unittest.mock import patch

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


def test_query_missing_entity_returns_error(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    result = invoke_tool(
        "query",
        cache,
        tools.query,
        entity_id="nonexistent_doc",
    )

    assert result.isError is True
    assert "not found" in result.structuredContent["content"][0]["text"].lower()


def test_export_graph_outside_workspace_returns_error(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    result = invoke_tool(
        "export_graph",
        cache,
        tools.export_graph,
        export_to_file="../escape.json",
    )

    assert result.isError is True


def test_generic_exception_returns_error_not_crash(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    def failing_tool(cache, **kwargs):
        raise RuntimeError("unexpected internal failure")

    result = invoke_tool(
        "workspace_overview",
        cache,
        failing_tool,
    )

    assert result.isError is True
    assert "internal error" in result.structuredContent["content"][0]["text"].lower()


def test_get_document_requires_exactly_one_identifier(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    # Neither document_id nor path
    result = invoke_tool(
        "get_document",
        cache,
        tools.get_document,
    )

    assert result.isError is True


def test_usage_logging_failure_does_not_block_tool_execution(tmp_path):
    cache = build_cache(create_workspace(tmp_path, usage_logging=True))

    with patch("ontos.mcp.server._log_usage", side_effect=PermissionError("denied")):
        result = invoke_tool(
            "health",
            cache,
            tools.health,
        )

    assert result.isError is False
    assert result.structuredContent["doc_count"] == 8


def test_help_and_stdout_safety_paths(tmp_path):
    root = create_workspace(tmp_path)

    help_result = run_base_cli(root, "serve", "--help")
    runtime_result = run_mcp_cli(root, "serve", "--workspace", ".")
    server = build_server(root)

    assert help_result.returncode == 0
    assert "usage: ontos serve" in help_result.stdout
    assert runtime_result.stdout == ""
    assert "workspace_overview" in server.instructions
