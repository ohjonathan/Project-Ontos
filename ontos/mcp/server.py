"""FastMCP bootstrap, registration, and shared tool wrapper for Ontos."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import traceback
from typing import Any, Callable, Dict, Optional, Union

import ontos
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent, Tool as MCPTool, ToolAnnotations

from ontos.core.errors import OntosInternalError, OntosUserError
from ontos.io.config import load_project_config
from ontos.io.snapshot import create_snapshot
from ontos.mcp.cache import SnapshotCache
from ontos.mcp.schemas import ToolErrorEnvelope, output_schema_for, validate_success_payload
from ontos.mcp import tools as tool_impl


DEFAULT_USAGE_LOG_PATH = "~/.config/ontos/usage.jsonl"


class OntosFastMCP(FastMCP):
    """FastMCP variant that advertises explicit output schemas per tool."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._output_schemas: Dict[str, Dict[str, Any]] = {}
        super().__init__(*args, **kwargs)

    def set_output_schema(self, tool_name: str, schema: Dict[str, Any]) -> None:
        self._output_schemas[tool_name] = schema

    async def list_tools(self) -> list[MCPTool]:
        tools = self._tool_manager.list_tools()
        return [
            MCPTool(
                name=info.name,
                title=info.title,
                description=info.description,
                inputSchema=info.parameters,
                outputSchema=self._output_schemas.get(info.name),
                annotations=info.annotations,
                icons=info.icons,
                _meta=info.meta,
            )
            for info in tools
        ]


def serve(workspace_root: Path) -> int:
    """Build the cache and start the stdio MCP runtime."""
    workspace_root = workspace_root.resolve()
    config = load_project_config(
        config_path=workspace_root / ".ontos.toml",
        repo_root=workspace_root,
    )
    snapshot = create_snapshot(
        root=workspace_root,
        include_content=True,
        filters=None,
        git_commit_provider=_git_commit_provider(workspace_root),
        scope=None,
    )
    cache = SnapshotCache(
        workspace_root,
        config,
        snapshot,
        git_commit_provider=_git_commit_provider(workspace_root),
        started_at=datetime.now(timezone.utc),
    )
    server = create_server(cache)
    server.run(transport="stdio")
    return 0


def create_server(cache: SnapshotCache) -> FastMCP:
    """Create and register the Ontos MCP server for one workspace."""
    workspace_name = cache.workspace_root.name
    server = OntosFastMCP(
        name="Ontos",
        instructions=_render_instructions(cache),
        log_level="ERROR",
    )

    def register(
        *,
        name: str,
        title: str,
        description: str,
        handler: Callable[..., Any],
        annotations: ToolAnnotations,
        meta: Dict[str, Any],
    ) -> None:
        server.tool(
            name=name,
            title=title,
            description=description,
            annotations=annotations,
            meta=meta,
            structured_output=False,
        )(handler)
        server.set_output_schema(name, output_schema_for(name))

    def handle_workspace_overview() -> CallToolResult:
        return _invoke_tool("workspace_overview", cache, tool_impl.workspace_overview)

    def handle_context_map(compact: str = "tiered") -> CallToolResult:
        return _invoke_tool(
            "context_map",
            cache,
            tool_impl.context_map,
            compact=compact,
        )

    def handle_get_document(
        document_id: str | None = None,
        path: str | None = None,
        include_content: bool = True,
    ) -> CallToolResult:
        return _invoke_tool(
            "get_document",
            cache,
            tool_impl.get_document,
            document_id=document_id,
            path=path,
            include_content=include_content,
        )

    def handle_list_documents(
        type: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> CallToolResult:
        return _invoke_tool(
            "list_documents",
            cache,
            tool_impl.list_documents,
            type=type,
            status=status,
            offset=offset,
            limit=limit,
        )

    def handle_export_graph(
        summary_only: bool = True,
        export_to_file: str | None = None,
    ) -> CallToolResult:
        return _invoke_tool(
            "export_graph",
            cache,
            tool_impl.export_graph,
            summary_only=summary_only,
            export_to_file=export_to_file,
        )

    def handle_query(entity_id: str) -> CallToolResult:
        return _invoke_tool(
            "query",
            cache,
            tool_impl.query,
            entity_id=entity_id,
        )

    def handle_health() -> CallToolResult:
        return _invoke_tool("health", cache, tool_impl.health)

    def handle_refresh() -> CallToolResult:
        return _invoke_tool(
            "refresh",
            cache,
            tool_impl.refresh,
            ensure_fresh=False,
            use_live_cache=True,
        )

    register(
        name="workspace_overview",
        title="Workspace Overview",
        description=f"Returns a structured overview of the {workspace_name} workspace.",
        handler=handle_workspace_overview,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 4000},
    )
    register(
        name="context_map",
        title="Context Map",
        description=f"Returns the context map for the {workspace_name} workspace.",
        handler=handle_context_map,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 64000},
    )
    register(
        name="get_document",
        title="Get Document",
        description=f"Returns a canonical Ontos document from the {workspace_name} workspace.",
        handler=handle_get_document,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 120000},
    )
    register(
        name="list_documents",
        title="List Documents",
        description=f"Lists canonical Ontos documents from the {workspace_name} workspace.",
        handler=handle_list_documents,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 32000},
    )
    register(
        name="export_graph",
        title="Export Graph",
        description=f"Exports the canonical Ontos graph for the {workspace_name} workspace.",
        handler=handle_export_graph,
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
        meta={"anthropic/maxResultSizeChars": 200000},
    )
    register(
        name="query",
        title="Query Document",
        description=f"Returns dependency details for one canonical document in the {workspace_name} workspace.",
        handler=handle_query,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 8000},
    )
    register(
        name="health",
        title="Server Health",
        description=f"Returns cache and runtime health for the {workspace_name} workspace.",
        handler=handle_health,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 4000},
    )
    # Keep these hints false: refresh mutates observable server state
    # (`snapshot_revision`, `last_indexed`, and cached snapshot contents)
    # even though it does not write workspace files.
    register(
        name="refresh",
        title="Refresh Cache",
        description=f"Rebuilds the in-memory Ontos snapshot for the {workspace_name} workspace.",
        handler=handle_refresh,
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
        meta={"anthropic/maxResultSizeChars": 4000},
    )
    return server


def _invoke_tool(
    tool_name: str,
    cache: SnapshotCache,
    tool_fn: Callable[..., Dict[str, Any]],
    *,
    ensure_fresh: bool = True,
    use_live_cache: bool = False,
    **kwargs: Any,
) -> Union[Dict[str, Any], CallToolResult]:
    try:
        _log_usage(cache, tool_name)
    except Exception:
        traceback.print_exc(file=sys.stderr)
    try:
        tool_input = cache.current_view()
        if ensure_fresh:
            tool_input = cache.get_fresh_view()
        if use_live_cache:
            tool_input = cache
        payload = tool_fn(tool_input, **kwargs)
        validated = validate_success_payload(tool_name, payload)
        return _tool_success_result(validated)
    except OntosUserError as exc:
        return _tool_error_result(str(exc))
    except OntosInternalError as exc:
        print(f"[ontos-mcp] {exc.code}: {exc}", file=sys.stderr)
        if exc.details:
            print(exc.details, file=sys.stderr)
        return _tool_error_result(f"Internal error: {exc}")
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return _tool_error_result(f"Internal error in {tool_name}")


def _tool_error_result(message: str) -> CallToolResult:
    envelope = ToolErrorEnvelope(
        isError=True,
        content=[{"type": "text", "text": message}],
    ).model_dump(mode="json", by_alias=True)
    return CallToolResult(
        isError=True,
        structuredContent=envelope,
        content=[TextContent(type="text", text=message)],
    )


def _tool_success_result(payload: Dict[str, Any]) -> CallToolResult:
    return CallToolResult(
        isError=False,
        structuredContent=payload,
        content=[
            TextContent(
                type="text",
                text=json.dumps(payload, ensure_ascii=True),
            )
        ],
    )


def _readonly_annotations() -> ToolAnnotations:
    return ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )


def _render_instructions(cache: SnapshotCache) -> str:
    workspace_name = cache.workspace_root.name
    doc_count = cache.canonical_view.total_count
    last_indexed_relative = _relative_time(cache.last_indexed)
    return (
        f"Ontos is a documentation knowledge graph for {workspace_name} "
        f"({doc_count} documents, last indexed {last_indexed_relative}). "
        "It tracks architecture docs, strategy decisions, and technical "
        "specifications as a typed dependency graph with 5 document types: "
        "kernel (foundational principles), strategy (goals and roadmap), "
        "product (user-facing specs), atom (technical implementation docs), "
        "and log (session history). All tools are deterministic, local-only, "
        "and fast (<100ms cached after warmup). "
        "Start with `workspace_overview` for project orientation \u2014 it returns "
        "deterministic IDs, key documents, graph stats, and warnings in a "
        "structured response under ~1KB. "
        "Use `context_map` when you need the full human-readable markdown narrative. "
        "Use `get_document` to read a specific document's content. "
        "Use `list_documents` to browse the full document set with optional "
        "type/status filters. "
        "Use `query` for single-entity dependency lookups. "
        "Use `export_graph` for structured graph export; `export_to_file` writes "
        "a JSON dump inside the workspace. "
        "Use `health` to check server status and index freshness."
    )


def _relative_time(value: datetime) -> str:
    now = datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    delta = max(0, int((now - value.astimezone(timezone.utc)).total_seconds()))
    if delta < 5:
        return "just now"
    if delta < 60:
        return f"{delta}s ago"
    if delta < 3600:
        return f"{delta // 60}m ago"
    return f"{delta // 3600}h ago"


def _log_usage(cache: SnapshotCache, tool_name: str) -> None:
    if not cache.config.mcp.usage_logging:
        return

    raw_path = cache.config.mcp.usage_log_path or DEFAULT_USAGE_LOG_PATH
    usage_path = Path(raw_path).expanduser()
    usage_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tool_name": tool_name,
    }
    with usage_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def _git_commit_provider(workspace_root: Path) -> Callable[[], Optional[str]]:
    def provider() -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=workspace_root,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return None
        return result.stdout.strip() or None

    return provider
