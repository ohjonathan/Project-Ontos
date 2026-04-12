"""FastMCP bootstrap, registration, and shared tool wrappers for Ontos."""

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
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import CallToolResult, TextContent, Tool as MCPTool, ToolAnnotations

from ontos.core.errors import OntosInternalError, OntosUserError
from ontos.io.config import load_project_config
from ontos.io.snapshot import create_snapshot
from ontos.mcp.cache import SnapshotCache
from ontos.mcp.scanner import slugify
from ontos.mcp.schemas import ToolErrorEnvelope, output_schema_for, validate_success_payload
from ontos.mcp import tools as tool_impl


DEFAULT_USAGE_LOG_PATH = "~/.config/ontos/usage.jsonl"
DEFAULT_PORTFOLIO_DB_PATH = Path.home() / ".config" / "ontos" / "portfolio.db"
CORE_TOOL_NAMES = {
    "workspace_overview",
    "context_map",
    "get_document",
    "list_documents",
    "export_graph",
    "query",
    "health",
    "refresh",
}
PORTFOLIO_MODE_TOOL_NAMES = {"project_registry", "search"}


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

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        try:
            return await super().call_tool(name, arguments)
        except ToolError as exc:
            if (
                name in PORTFOLIO_MODE_TOOL_NAMES
                and str(exc).startswith("Unknown tool:")
            ):
                return _tool_error_result(
                    "E_PORTFOLIO_REQUIRED: Tool is available only in portfolio mode."
                )
            raise


def serve(
    workspace_root: Path,
    *,
    portfolio: bool = False,
    read_only: bool = False,
) -> int:
    """Build cache/index state and start the stdio MCP runtime."""
    workspace_root = workspace_root.resolve()
    cache = _build_cache(workspace_root)

    portfolio_index: Any = None
    try:
        if portfolio:
            portfolio_index = _build_portfolio_index()
        server = create_server(
            cache,
            portfolio_index=portfolio_index,
            read_only=read_only,
            include_bundle_tool=True,
        )
        server.run(transport="stdio")
        return 0
    finally:
        if portfolio_index is not None:
            close = getattr(portfolio_index, "close", None)
            if callable(close):
                close()


def create_server(
    cache: SnapshotCache,
    *,
    portfolio_index: Any = None,
    read_only: bool = False,
    include_bundle_tool: bool = False,
) -> FastMCP:
    """Create and register the Ontos MCP server."""
    workspace_name = cache.workspace_root.name
    portfolio_mode = portfolio_index is not None

    # Tool implementations infer scope behavior from these cache attributes.
    setattr(cache, "portfolio_mode", portfolio_mode)
    setattr(cache, "portfolio_index", portfolio_index)
    setattr(cache, "primary_workspace_slug", _workspace_slug(cache.workspace_root))
    setattr(cache, "read_only", read_only)

    server = OntosFastMCP(
        name="Ontos",
        instructions=_render_instructions(
            cache,
            portfolio_mode=portfolio_mode,
            include_bundle_tool=include_bundle_tool,
        ),
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

    _register_core_tools(
        cache=cache,
        workspace_name=workspace_name,
        register_fn=register,
    )

    _register_write_tools(
        cache=cache,
        workspace_name=workspace_name,
        portfolio_index=portfolio_index,
        read_only=read_only,
        register_fn=register,
    )

    if portfolio_index is not None:
        _register_portfolio_tools(
            cache=cache,
            portfolio_index=portfolio_index,
            register_fn=register,
        )

    if include_bundle_tool:
        _register_bundle_tool(
            cache=cache,
            portfolio_index=portfolio_index,
            register_fn=register,
        )

    return server


def _register_core_tools(
    *,
    cache: SnapshotCache,
    workspace_name: str,
    register_fn: Callable[..., None],
) -> None:
    def handle_workspace_overview(
        workspace_id: str | None = None,
    ) -> CallToolResult:
        return _invoke_read_tool(
            "workspace_overview",
            cache,
            tool_impl.workspace_overview,
            workspace_id=workspace_id,
        )

    def handle_context_map(
        compact: str = "tiered",
        workspace_id: str | None = None,
    ) -> CallToolResult:
        return _invoke_read_tool(
            "context_map",
            cache,
            tool_impl.context_map,
            compact=compact,
            workspace_id=workspace_id,
        )

    def handle_get_document(
        document_id: str | None = None,
        path: str | None = None,
        include_content: bool = True,
        workspace_id: str | None = None,
    ) -> CallToolResult:
        return _invoke_read_tool(
            "get_document",
            cache,
            tool_impl.get_document,
            document_id=document_id,
            path=path,
            include_content=include_content,
            workspace_id=workspace_id,
        )

    def handle_list_documents(
        type: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
        workspace_id: str | None = None,
    ) -> CallToolResult:
        return _invoke_read_tool(
            "list_documents",
            cache,
            tool_impl.list_documents,
            type=type,
            status=status,
            offset=offset,
            limit=limit,
            workspace_id=workspace_id,
        )

    def handle_export_graph(
        summary_only: bool = True,
        export_to_file: str | None = None,
        workspace_id: str | None = None,
    ) -> CallToolResult:
        return _invoke_read_tool(
            "export_graph",
            cache,
            tool_impl.export_graph,
            summary_only=summary_only,
            export_to_file=export_to_file,
            workspace_id=workspace_id,
        )

    def handle_query(
        entity_id: str,
        workspace_id: str | None = None,
    ) -> CallToolResult:
        return _invoke_read_tool(
            "query",
            cache,
            tool_impl.query,
            entity_id=entity_id,
            workspace_id=workspace_id,
        )

    def handle_health(workspace_id: str | None = None) -> CallToolResult:
        return _invoke_read_tool(
            "health",
            cache,
            tool_impl.health,
            workspace_id=workspace_id,
        )

    def handle_refresh(workspace_id: str | None = None) -> CallToolResult:
        return _invoke_read_tool(
            "refresh",
            cache,
            tool_impl.refresh,
            ensure_fresh=False,
            use_live_cache=True,
            workspace_id=workspace_id,
        )

    register_fn(
        name="workspace_overview",
        title="Workspace Overview",
        description=f"Returns a structured overview of the {workspace_name} workspace.",
        handler=handle_workspace_overview,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 4000},
    )
    register_fn(
        name="context_map",
        title="Context Map",
        description=f"Returns the context map for the {workspace_name} workspace.",
        handler=handle_context_map,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 64000},
    )
    register_fn(
        name="get_document",
        title="Get Document",
        description=f"Returns a canonical Ontos document from the {workspace_name} workspace.",
        handler=handle_get_document,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 120000},
    )
    register_fn(
        name="list_documents",
        title="List Documents",
        description=f"Lists canonical Ontos documents from the {workspace_name} workspace.",
        handler=handle_list_documents,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 32000},
    )
    register_fn(
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
    register_fn(
        name="query",
        title="Query Document",
        description=(
            f"Returns dependency details for one canonical document in the {workspace_name} workspace."
        ),
        handler=handle_query,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 8000},
    )
    register_fn(
        name="health",
        title="Server Health",
        description=f"Returns cache and runtime health for the {workspace_name} workspace.",
        handler=handle_health,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 4000},
    )
    register_fn(
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


def _register_write_tools(
    *,
    cache: SnapshotCache,
    workspace_name: str,
    portfolio_index: Any,
    read_only: bool,
    register_fn: Callable[..., None],
) -> None:
    """Register the v4.1 Track B single-file write tools (Dev 2)."""
    from ontos.mcp import writes as write_impl

    def handle_scaffold_document(
        path: str,
        content: str = "",
        workspace_id: Optional[str] = None,
    ) -> CallToolResult:
        return _invoke_write_tool(
            "scaffold_document",
            cache,
            write_impl.scaffold_document,
            portfolio_index=portfolio_index,
            read_only=read_only,
            path=path,
            content=content,
            workspace_id=workspace_id,
        )

    def handle_log_session(
        title: str,
        event_type: str = "chore",
        source: str = "mcp",
        branch: str = "unknown",
        body: str = "",
        workspace_id: Optional[str] = None,
    ) -> CallToolResult:
        return _invoke_write_tool(
            "log_session",
            cache,
            write_impl.log_session,
            portfolio_index=portfolio_index,
            read_only=read_only,
            title=title,
            event_type=event_type,
            source=source,
            branch=branch,
            body=body,
            workspace_id=workspace_id,
        )

    def handle_promote_document(
        document_id: str,
        new_level: int,
        workspace_id: Optional[str] = None,
    ) -> CallToolResult:
        return _invoke_write_tool(
            "promote_document",
            cache,
            write_impl.promote_document,
            portfolio_index=portfolio_index,
            read_only=read_only,
            document_id=document_id,
            new_level=new_level,
            workspace_id=workspace_id,
        )

    write_annotations = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    )

    register_fn(
        name="scaffold_document",
        title="Scaffold Document",
        description=(
            f"Creates a new scaffolded Markdown document in the {workspace_name} "
            "workspace."
        ),
        handler=handle_scaffold_document,
        annotations=write_annotations,
        meta={"anthropic/maxResultSizeChars": 4000},
    )
    register_fn(
        name="log_session",
        title="Log Session",
        description=(
            f"Creates a dated session log under logs_dir in the {workspace_name} "
            "workspace."
        ),
        handler=handle_log_session,
        annotations=write_annotations,
        meta={"anthropic/maxResultSizeChars": 4000},
    )
    register_fn(
        name="promote_document",
        title="Promote Document",
        description=(
            f"Updates a document's curation_level frontmatter in the "
            f"{workspace_name} workspace."
        ),
        handler=handle_promote_document,
        annotations=write_annotations,
        meta={"anthropic/maxResultSizeChars": 4000},
    )


def _invoke_write_tool(
    tool_name: str,
    cache: SnapshotCache,
    tool_fn: Callable[..., CallToolResult],
    *,
    portfolio_index: Any,
    read_only: bool,
    **kwargs: Any,
) -> CallToolResult:
    """Shared write-tool invoker.

    Write tool implementations own their own locking (workspace_lock + A3
    rebuild path), schema validation, and error envelope construction. This
    wrapper records usage telemetry, guards against unexpected exceptions
    above the tool body, and surfaces them as structured MCP errors.
    """
    try:
        _log_usage(cache, tool_name)
    except Exception:
        traceback.print_exc(file=sys.stderr)

    try:
        return tool_fn(
            cache,
            portfolio_index=portfolio_index,
            read_only=read_only,
            **kwargs,
        )
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


def _register_portfolio_tools(
    *,
    cache: SnapshotCache,
    portfolio_index: Any,
    register_fn: Callable[..., None],
) -> None:
    def handle_project_registry(workspace_id: str | None = None) -> CallToolResult:
        _ = workspace_id
        return _invoke_portfolio_tool(
            "project_registry",
            portfolio_index,
            tool_impl.project_registry,
            cache=cache,
        )

    def handle_search(
        query_string: str,
        workspace_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> CallToolResult:
        return _invoke_portfolio_tool(
            "search",
            portfolio_index,
            tool_impl.search,
            cache=cache,
            query_string=query_string,
            workspace_id=workspace_id,
            offset=offset,
            limit=limit,
        )

    register_fn(
        name="project_registry",
        title="Project Registry",
        description="Returns indexed portfolio project metadata.",
        handler=handle_project_registry,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 32000},
    )
    register_fn(
        name="search",
        title="Search Portfolio",
        description="Searches indexed portfolio documents using full-text search.",
        handler=handle_search,
        annotations=_readonly_annotations(),
        meta={"anthropic/maxResultSizeChars": 120000},
    )


def _register_bundle_tool(
    *,
    cache: SnapshotCache,
    portfolio_index: Any,
    register_fn: Callable[..., None],
) -> None:
    if portfolio_index is None:
        def handle_get_context_bundle(
            workspace_id: str | None = None,
            token_budget: int = 8192,
        ) -> CallToolResult:
            return _invoke_read_tool(
                "get_context_bundle",
                cache,
                _get_context_bundle_single_workspace,
                ensure_fresh=False,
                use_live_cache=True,
                workspace_id=workspace_id,
                token_budget=token_budget,
            )
    else:
        def handle_get_context_bundle(
            workspace_id: str | None = None,
            token_budget: int = 8192,
        ) -> CallToolResult:
            return _invoke_portfolio_tool(
                "get_context_bundle",
                portfolio_index,
                tool_impl.get_context_bundle,
                cache=cache,
                cache_input=cache,
                workspace_id=workspace_id,
                token_budget=token_budget,
            )

    register_fn(
        name="get_context_bundle",
        title="Get Context Bundle",
        description="Returns a token-budgeted context package for a workspace.",
        handler=handle_get_context_bundle,
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
        meta={"anthropic/maxResultSizeChars": 200000},
    )


def _get_context_bundle_single_workspace(
    cache: SnapshotCache,
    *,
    workspace_id: str | None = None,
    token_budget: int = 8192,
) -> dict[str, Any]:
    return tool_impl.get_context_bundle(
        None,
        cache,
        workspace_id=workspace_id,
        token_budget=token_budget,
    )


def _invoke_read_tool(
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

    workspace_id = kwargs.get("workspace_id")
    if _is_cross_workspace_read(tool_name, cache, workspace_id):
        return _tool_error_result(
            "E_CROSS_WORKSPACE_NOT_SUPPORTED: Cross-workspace reads are not "
            "supported for this tool. Start a separate `ontos serve` in the "
            "target workspace."
        )

    try:
        tool_input: Any = cache.current_view()
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


def _invoke_portfolio_tool(
    tool_name: str,
    portfolio_index: Any,
    tool_fn: Callable[..., Dict[str, Any]],
    *,
    cache: SnapshotCache | None = None,
    **kwargs: Any,
) -> Union[Dict[str, Any], CallToolResult]:
    if portfolio_index is None:
        return _tool_error_result(
            "E_PORTFOLIO_REQUIRED: Tool is available only in portfolio mode."
        )

    try:
        if cache is not None:
            _log_usage(cache, tool_name)
    except Exception:
        traceback.print_exc(file=sys.stderr)

    try:
        cache_input = kwargs.pop("cache_input", None)
        if cache_input is None:
            payload = tool_fn(portfolio_index, **kwargs)
        else:
            payload = tool_fn(portfolio_index, cache_input, **kwargs)
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


def _invoke_tool(
    tool_name: str,
    cache: SnapshotCache,
    tool_fn: Callable[..., Dict[str, Any]],
    *,
    ensure_fresh: bool = True,
    use_live_cache: bool = False,
    **kwargs: Any,
) -> Union[Dict[str, Any], CallToolResult]:
    """Legacy wrapper retained for existing tests and imports."""
    return _invoke_read_tool(
        tool_name,
        cache,
        tool_fn,
        ensure_fresh=ensure_fresh,
        use_live_cache=use_live_cache,
        **kwargs,
    )


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


def _render_instructions(
    cache: SnapshotCache,
    *,
    portfolio_mode: bool,
    include_bundle_tool: bool,
) -> str:
    workspace_name = cache.workspace_root.name
    doc_count = cache.canonical_view.total_count
    last_indexed_relative = _relative_time(cache.last_indexed)
    instructions = (
        f"Ontos is a documentation knowledge graph for {workspace_name} "
        f"({doc_count} documents, last indexed {last_indexed_relative}). "
        "It tracks architecture docs, strategy decisions, and technical "
        "specifications as a typed dependency graph with 5 document types: "
        "kernel (foundational principles), strategy (goals and roadmap), "
        "product (user-facing specs), atom (technical implementation docs), "
        "and log (session history). All tools are deterministic, local-only, "
        "and fast (<100ms cached after warmup). "
        "Start with `workspace_overview` for project orientation. "
        "Use `context_map` for the full markdown narrative. "
        "Use `get_document` to read one document. "
        "Use `list_documents` to browse by type/status. "
        "Use `query` for dependency lookups. "
        "Use `export_graph` for structured graph export. "
        "Use `health` to check server status and index freshness."
    )
    if include_bundle_tool:
        instructions += (
            " Use `get_context_bundle` to assemble a token-budgeted context bundle."
        )
    if portfolio_mode:
        instructions += (
            " Portfolio mode also enables `project_registry` and `search` for "
            "cross-workspace discovery."
        )
    return instructions


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


def _build_cache(workspace_root: Path) -> SnapshotCache:
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
    return SnapshotCache(
        workspace_root,
        config,
        snapshot,
        git_commit_provider=_git_commit_provider(workspace_root),
        started_at=datetime.now(timezone.utc),
    )


def _build_portfolio_index() -> Any:
    from ontos.mcp.portfolio import PortfolioIndex
    from ontos.mcp.portfolio_config import load_portfolio_config

    config = load_portfolio_config()
    scan_roots = [Path(path).expanduser() for path in config.scan_roots]
    registry_path = (
        Path(config.registry_path).expanduser()
        if config.registry_path
        else None
    )
    index = PortfolioIndex(DEFAULT_PORTFOLIO_DB_PATH)
    index.open()
    index.rebuild_all(
        scan_roots=scan_roots,
        exclude=list(config.exclude),
        registry_path=registry_path,
    )
    return index


def _workspace_slug(workspace_root: Path) -> str:
    return slugify(workspace_root.name)


def _is_cross_workspace_read(
    tool_name: str,
    cache: SnapshotCache,
    workspace_id: Any,
) -> bool:
    if workspace_id is None:
        return False
    if tool_name not in CORE_TOOL_NAMES:
        return False
    if not getattr(cache, "portfolio_mode", False):
        return False
    return str(workspace_id) != _workspace_slug(cache.workspace_root)
