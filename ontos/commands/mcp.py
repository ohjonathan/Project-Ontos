"""Client-side MCP configuration commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from ontos.core.antigravity_mcp import (
    AntigravityConfigError,
    antigravity_config_path,
    build_antigravity_ontos_entry,
    load_antigravity_config,
    upsert_antigravity_ontos_entry,
    write_antigravity_config,
)
from ontos.io.files import find_project_root


@dataclass
class MCPInstallOptions:
    """Configuration for `ontos mcp install`."""

    client: str = "antigravity"
    workspace: Optional[Path] = None
    write_enabled: bool = False


def _resolve_workspace_root(workspace: Optional[Path]) -> Tuple[int, Optional[Path], str]:
    """Resolve the served workspace root for client config generation."""
    start_path = workspace or Path.cwd()
    resolved_start = start_path.expanduser().resolve()
    if not resolved_start.exists():
        return 2, None, f"Workspace path does not exist: {start_path}"

    try:
        workspace_root = find_project_root(start_path=resolved_start)
    except FileNotFoundError as exc:
        return 2, None, str(exc)

    return 0, workspace_root, ""


def _run_mcp_install_command(options: MCPInstallOptions) -> Tuple[int, str, Dict[str, str]]:
    """Install or update a supported native MCP client config."""
    if options.client != "antigravity":
        return 2, f"Unsupported MCP client: {options.client}", {}

    exit_code, workspace_root, error_message = _resolve_workspace_root(options.workspace)
    if exit_code != 0 or workspace_root is None:
        return exit_code, error_message, {}

    config_path = antigravity_config_path()
    existing = None
    if config_path.exists():
        try:
            existing = load_antigravity_config(config_path)
        except AntigravityConfigError as exc:
            return 2, str(exc), {"config_path": str(config_path)}

    entry = build_antigravity_ontos_entry(workspace_root, write_enabled=options.write_enabled)
    updated_config, action = upsert_antigravity_ontos_entry(existing, entry)
    write_antigravity_config(config_path, updated_config)

    mode = "write-enabled" if options.write_enabled else "read-only"
    verb = "Created" if action == "created" else "Updated"
    message = f"{verb} Antigravity MCP config at {config_path}"
    data = {
        "client": options.client,
        "action": action,
        "config_path": str(config_path),
        "workspace": str(workspace_root),
        "mode": mode,
    }
    return 0, message, data


def mcp_install_command(options: MCPInstallOptions) -> int:
    """Run `ontos mcp install` and return an exit code."""
    exit_code, _, _ = _run_mcp_install_command(options)
    return exit_code
