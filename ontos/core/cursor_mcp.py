"""Helpers for Cursor MCP configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ontos.core.mcp_shared import (
    MCPConfigError,
    MCPProbeResult,
    ManagedMCPAdapter,
    build_ontos_stdio_entry,
    extract_workspace_arg,
    load_json_object_config,
    probe_mcp_initialize,
    remove_named_server_entry,
    resolve_executable,
    upsert_named_server_entry,
    write_json_object_config,
)


CURSOR_CONFIG_FILENAME = "mcp.json"


class CursorConfigError(MCPConfigError):
    """Raised when a Cursor MCP config is malformed."""


@dataclass(frozen=True)
class CursorInspection:
    """Inspection result for one Cursor scope."""

    scope: str
    code: str
    ok: bool
    message: str
    details: Optional[str]
    config_path: Path
    file_present: bool
    entry_present: bool
    mode: Optional[str] = None
    command: Optional[str] = None
    args: Tuple[str, ...] = ()
    workspace: Optional[Path] = None
    probe: Optional[MCPProbeResult] = None


def cursor_config_path(
    *,
    scope: str,
    workspace_root: Path,
    home: Optional[Path] = None,
    config_path_override: Optional[Path] = None,
) -> Path:
    """Resolve the Cursor MCP config path for the requested scope."""
    if config_path_override is not None:
        return config_path_override.expanduser().resolve()

    if scope == "project":
        return workspace_root.expanduser().resolve() / ".cursor" / CURSOR_CONFIG_FILENAME
    if scope == "user":
        base_home = Path(home) if home is not None else Path.home()
        return base_home.expanduser() / ".cursor" / CURSOR_CONFIG_FILENAME
    raise ValueError(f"Unsupported Cursor MCP scope: {scope}")


def build_cursor_ontos_entry(workspace_root: Path, *, write_enabled: bool = False) -> Dict[str, Any]:
    """Build the managed Cursor Ontos MCP entry."""
    return build_ontos_stdio_entry(workspace_root, write_enabled=write_enabled)


def load_cursor_config(path: Path) -> Dict[str, Any]:
    """Load and validate the top-level Cursor config document."""
    try:
        return load_json_object_config(path, client_label="Cursor", root_key="mcpServers")
    except MCPConfigError as exc:
        raise CursorConfigError(exc.code, str(exc)) from exc


def write_cursor_config(path: Path, data: Dict[str, Any]) -> None:
    """Write the Cursor config with stable formatting."""
    write_json_object_config(path, data)


def upsert_cursor_ontos_entry(existing: Optional[Dict[str, Any]], entry: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """Upsert only the Cursor Ontos entry while preserving sibling data."""
    try:
        return upsert_named_server_entry(existing, entry, root_key="mcpServers", client_label="Cursor")
    except MCPConfigError as exc:
        raise CursorConfigError(exc.code, str(exc)) from exc


def remove_cursor_ontos_entry(existing: Optional[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], str]:
    """Remove only the Cursor Ontos entry while preserving sibling data."""
    try:
        return remove_named_server_entry(existing, root_key="mcpServers", client_label="Cursor")
    except MCPConfigError as exc:
        raise CursorConfigError(exc.code, str(exc)) from exc


def inspect_cursor_ontos_config(
    *,
    scope: str,
    workspace_root: Path,
    home: Optional[Path] = None,
    config_path_override: Optional[Path] = None,
) -> CursorInspection:
    """Inspect one Cursor scope for a managed Ontos MCP entry."""
    config_path = cursor_config_path(
        scope=scope,
        workspace_root=workspace_root,
        home=home,
        config_path_override=config_path_override,
    )

    if not config_path.exists():
        return CursorInspection(
            scope=scope,
            code="not_present",
            ok=True,
            message=f"Cursor {scope} MCP config not present",
            details=None,
            config_path=config_path,
            file_present=False,
            entry_present=False,
        )

    try:
        data = load_cursor_config(config_path)
    except CursorConfigError as exc:
        detail_map = {
            "empty": f"Run 'ontos mcp install --client cursor --scope {scope}' to write {config_path}.",
            "invalid_json": f"Fix or remove {config_path}, then rerun 'ontos mcp install --client cursor --scope {scope}'.",
            "invalid_root": f"Fix or remove {config_path}, then rerun 'ontos mcp install --client cursor --scope {scope}'.",
            "unreadable": str(exc),
        }
        return CursorInspection(
            scope=scope,
            code=exc.code,
            ok=False,
            message=str(exc),
            details=detail_map.get(exc.code, str(exc)),
            config_path=config_path,
            file_present=True,
            entry_present=False,
        )

    servers = data.get("mcpServers") or {}
    entry = servers.get("ontos")
    if not isinstance(entry, dict):
        return CursorInspection(
            scope=scope,
            code="not_configured",
            ok=True,
            message=f"Cursor {scope} config has no Ontos MCP entry",
            details=None,
            config_path=config_path,
            file_present=True,
            entry_present=False,
        )

    command = entry.get("command")
    args = entry.get("args") or []
    if not isinstance(command, str) or not command.strip():
        return CursorInspection(
            scope=scope,
            code="bad_command",
            ok=False,
            message=f"Cursor {scope} Ontos entry is missing a valid command",
            details=f"Run 'ontos mcp install --client cursor --scope {scope}' to regenerate the Ontos entry.",
            config_path=config_path,
            file_present=True,
            entry_present=True,
        )
    if not isinstance(args, list) or any(not isinstance(item, str) for item in args):
        return CursorInspection(
            scope=scope,
            code="bad_command",
            ok=False,
            message=f"Cursor {scope} Ontos entry has invalid args",
            details="Expected 'args' to be a list of strings.",
            config_path=config_path,
            file_present=True,
            entry_present=True,
            command=command,
        )

    if resolve_executable(command) is None:
        return CursorInspection(
            scope=scope,
            code="bad_command",
            ok=False,
            message=f"Cursor {scope} Ontos command is not executable: {command}",
            details=f"Run 'ontos mcp install --client cursor --scope {scope}' to rewrite the command path.",
            config_path=config_path,
            file_present=True,
            entry_present=True,
            command=command,
            args=tuple(args),
        )

    if "serve" not in args:
        return CursorInspection(
            scope=scope,
            code="bad_command",
            ok=False,
            message=f"Cursor {scope} Ontos entry does not invoke 'serve'",
            details="Expected args to include 'serve'.",
            config_path=config_path,
            file_present=True,
            entry_present=True,
            command=command,
            args=tuple(args),
        )

    workspace = extract_workspace_arg(args)
    if workspace is None:
        return CursorInspection(
            scope=scope,
            code="bad_workspace",
            ok=False,
            message=f"Cursor {scope} Ontos entry is missing --workspace",
            details=f"Run 'ontos mcp install --client cursor --scope {scope}' to add an absolute workspace path.",
            config_path=config_path,
            file_present=True,
            entry_present=True,
            command=command,
            args=tuple(args),
        )
    if not workspace.is_absolute():
        return CursorInspection(
            scope=scope,
            code="bad_workspace",
            ok=False,
            message=f"Cursor {scope} Ontos workspace must be an absolute path",
            details=f"Observed workspace: {workspace}",
            config_path=config_path,
            file_present=True,
            entry_present=True,
            command=command,
            args=tuple(args),
            workspace=workspace,
        )
    if not workspace.exists():
        return CursorInspection(
            scope=scope,
            code="bad_workspace",
            ok=False,
            message=f"Cursor {scope} Ontos workspace does not exist: {workspace}",
            details="Run 'ontos mcp install --client cursor --workspace /absolute/path' with a valid project root.",
            config_path=config_path,
            file_present=True,
            entry_present=True,
            command=command,
            args=tuple(args),
            workspace=workspace,
        )

    mode = "read-only" if "--read-only" in args else "write-enabled"
    probe = probe_mcp_initialize(command, args)
    if not probe.ok:
        return CursorInspection(
            scope=scope,
            code="probe_failed",
            ok=False,
            message=f"Cursor {scope} Ontos entry failed a direct MCP initialize probe",
            details=probe.details or probe.message,
            config_path=config_path,
            file_present=True,
            entry_present=True,
            mode=mode,
            command=command,
            args=tuple(args),
            workspace=workspace,
            probe=probe,
        )

    return CursorInspection(
        scope=scope,
        code="ok",
        ok=True,
        message=f"Cursor {scope} Ontos entry valid ({mode})",
        details=None,
        config_path=config_path,
        file_present=True,
        entry_present=True,
        mode=mode,
        command=command,
        args=tuple(args),
        workspace=workspace,
        probe=probe,
    )


@dataclass(frozen=True)
class CursorMCPAdapter(ManagedMCPAdapter):
    """Concrete managed adapter for Cursor."""

    client_name: str = "cursor"
    supported_scopes: Tuple[str, ...] = ("project", "user")
    default_scope: str = "project"

    def resolve_config_path(
        self,
        *,
        scope: str,
        workspace_root: Path,
        home: Optional[Path] = None,
        config_path_override: Optional[Path] = None,
    ) -> Path:
        return cursor_config_path(
            scope=scope,
            workspace_root=workspace_root,
            home=home,
            config_path_override=config_path_override,
        )

    def build_ontos_entry(
        self,
        *,
        workspace_root: Path,
        write_enabled: bool,
    ) -> Dict[str, object]:
        return build_cursor_ontos_entry(workspace_root, write_enabled=write_enabled)

    def load_config(self, path: Path) -> Dict[str, object]:
        return load_cursor_config(path)

    def write_config(self, path: Path, data: Dict[str, object]) -> None:
        write_cursor_config(path, data)

    def upsert_ontos_entry(
        self,
        existing: Optional[Dict[str, object]],
        entry: Dict[str, object],
    ) -> Tuple[Dict[str, object], str]:
        return upsert_cursor_ontos_entry(existing, entry)

    def remove_ontos_entry(
        self,
        existing: Optional[Dict[str, object]],
    ) -> Tuple[Optional[Dict[str, object]], str]:
        return remove_cursor_ontos_entry(existing)


CURSOR_MCP_ADAPTER = CursorMCPAdapter()
