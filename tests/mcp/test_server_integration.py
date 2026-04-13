"""Integration tests for the MCP server (spec Section 7)."""

import json
from pathlib import Path

from mcp.types import ListToolsResult

from tests.mcp import build_cache, build_server, create_workspace, list_tools, write_file


def test_server_lists_all_tools_with_correct_annotations(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)
    tool_map = {tool.name: tool for tool in list_tools(server)}

    expected_tools = {
        "workspace_overview",
        "context_map",
        "get_document",
        "list_documents",
        "export_graph",
        "query",
        "health",
        "refresh",
        # v4.1 Track B (Dev 2) — single-file write tools.
        "scaffold_document",
        "log_session",
        "promote_document",
        # v4.1 Track B (Dev 3) — multi-file write tool.
        "rename_document",
    }
    assert set(tool_map.keys()) == expected_tools
    assert len(tool_map) == len(expected_tools)

    # export_graph, refresh, and the write tools are non-read-only
    for name in ("export_graph", "refresh", "scaffold_document",
                 "log_session", "promote_document", "rename_document"):
        assert tool_map[name].annotations.readOnlyHint is False, (
            f"{name} must not be readOnly"
        )
    assert tool_map["refresh"].annotations.idempotentHint is False

    # Read-only tools
    for name in ("workspace_overview", "context_map", "get_document",
                 "list_documents", "query", "health"):
        assert tool_map[name].annotations.readOnlyHint is True, f"{name} should be readOnly"


def test_list_tools_output_schemas_are_object_or_absent(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)
    for tool in list_tools(server):
        assert tool.outputSchema is None or tool.outputSchema["type"] == "object", (
            f"Tool '{tool.name}' advertises a non-object outputSchema; "
            "strict MCP clients reject the entire tools/list response."
        )


def test_tools_list_wire_payload_has_object_typed_or_absent_output_schemas(tmp_path):
    """Transport-level round-trip: serialize tools/list exactly as the MCP
    SDK does on the wire (mcp/shared/session.py: model_dump(by_alias=True,
    mode="json", exclude_none=True)), re-parse the JSON, and assert each
    tool entry either omits ``outputSchema`` or types it as an object.

    Higher-level tests inspect ``list_tools()`` return values, which can
    mask bugs introduced by the Pydantic serializer (e.g. a future change
    that emits ``outputSchema: null`` instead of omitting the key — some
    strict clients treat ``null`` as a validation failure). This test
    pins the actual bytes Claude Code parses.
    """
    root = create_workspace(tmp_path)
    server = build_server(root)
    result = ListToolsResult(tools=list_tools(server))

    wire_json = result.model_dump_json(by_alias=True, exclude_none=True)
    parsed = json.loads(wire_json)

    tool_names = {entry["name"] for entry in parsed["tools"]}
    assert "export_graph" in tool_names, "export_graph must still be advertised"

    for entry in parsed["tools"]:
        if "outputSchema" not in entry:
            continue
        schema = entry["outputSchema"]
        assert isinstance(schema, dict), (
            f"Tool '{entry['name']}' serialized outputSchema={schema!r}; "
            "MCP clients expect an object or omission."
        )
        assert schema.get("type") == "object", (
            f"Tool '{entry['name']}' wire outputSchema has type "
            f"{schema.get('type')!r}; strict MCP clients (e.g. Claude Code) "
            "reject the entire tools/list response when any outputSchema "
            "is not root-typed as 'object'. See issue #97."
        )

    export_entry = next(t for t in parsed["tools"] if t["name"] == "export_graph")
    assert "outputSchema" not in export_entry, (
        "export_graph must NOT serialize an outputSchema key on the wire "
        "until its response is refactored into a discriminated object "
        "(Option A, deferred to 4.2.0). A serialized key of any value — "
        "including null — risks regressing issue #97."
    )


def test_tool_descriptions_include_workspace_name(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)
    tool_map = {tool.name: tool for tool in list_tools(server)}
    workspace_name = root.name

    for name, tool in tool_map.items():
        assert workspace_name in tool.description, (
            f"Tool '{name}' description should include workspace name '{workspace_name}'"
        )


def test_instructions_mention_workspace_overview(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    assert "workspace_overview" in server.instructions


def test_instructions_contain_workspace_identity(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    assert root.name in server.instructions


def test_instructions_not_mutated_on_rebuild(tmp_path):
    from ontos.mcp.server import create_server

    root = create_workspace(tmp_path)
    cache = build_cache(root)
    server = create_server(cache)
    instructions_before = server.instructions

    # Mutate workspace so the rebuild produces different doc_count
    write_file(root / "docs/extra.md", """
    ---
    id: extra_doc
    type: atom
    status: active
    ---
    Extra body.
    """)
    cache.force_refresh()

    # Instructions are startup-time only; they should not change even
    # though doc_count increased after rebuild
    assert cache.canonical_view.total_count > 8
    assert server.instructions == instructions_before


def test_serve_binds_config_to_workspace_across_cwd(tmp_path, monkeypatch):
    from ontos.mcp import server as mcp_server

    launch_root = create_workspace(tmp_path / "launch")
    target_root = tmp_path / "target"
    target_root.mkdir(parents=True)
    write_file(
        target_root / ".ontos.toml",
        """
        [ontos]
        version = "4.0"

        [paths]
        docs_dir = "knowledge"

        [scanning]
        skip_patterns = ["_template.md", "archive/*"]

        [mcp]
        usage_logging = false
        """,
    )
    write_file(
        target_root / "knowledge/primary.md",
        """
        ---
        id: primary_doc
        type: atom
        status: active
        ---
        Primary body.
        """,
    )
    captured = {}

    class DummyServer:
        def run(self, transport: str) -> None:
            captured["transport"] = transport

    def fake_create_server(cache, **kwargs):
        captured["docs_dir"] = cache.config.paths.docs_dir
        captured["initial_count"] = cache.canonical_view.total_count
        captured["kwargs"] = kwargs
        write_file(
            target_root / "knowledge/extra.md",
            """
            ---
            id: extra_doc
            type: atom
            status: active
            ---
            Extra body.
            """,
        )
        cache.force_refresh()
        captured["refreshed_count"] = cache.canonical_view.total_count
        return DummyServer()

    monkeypatch.chdir(launch_root)
    monkeypatch.setattr(mcp_server, "create_server", fake_create_server)

    exit_code = mcp_server.serve(Path(target_root))

    assert exit_code == 0
    assert captured["transport"] == "stdio"
    assert captured["docs_dir"] == "knowledge"
    assert captured["initial_count"] == 1
    assert captured["refreshed_count"] == 2
    assert captured["kwargs"]["include_bundle_tool"] is True
