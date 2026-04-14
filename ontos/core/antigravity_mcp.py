"""Helpers for Antigravity native MCP configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ontos.core.mcp_shared import (
    MCPConfigError,
    build_ontos_stdio_entry,
    extract_workspace_arg,
    load_json_object_config,
    probe_mcp_initialize as shared_probe_mcp_initialize,
    resolve_executable,
    resolve_ontos_launcher,
    upsert_named_server_entry,
    write_json_object_config,
)


ANTIGRAVITY_CONFIG_RELATIVE_PATH = Path(".gemini") / "antigravity" / "mcp_config.json"


class AntigravityConfigError(MCPConfigError):
    """Raised when the native Antigravity config is malformed."""


@dataclass(frozen=True)
class AntigravityInstallation:
    """Detected Antigravity installation details."""

    config_path: Path
    app_path: Optional[Path]
    detected: bool


@dataclass(frozen=True)
class AntigravityProbeResult:
    """Result of a lightweight MCP initialize probe."""

    ok: bool
    message: str
    details: Optional[str] = None
    server_info: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class AntigravityInspection:
    """Inspection result for the native Antigravity Ontos MCP entry."""

    code: str
    ok: bool
    message: str
    details: Optional[str]
    config_path: Path
    detected: bool
    mode: Optional[str] = None
    command: Optional[str] = None
    args: Tuple[str, ...] = ()
    workspace: Optional[Path] = None
    probe: Optional[AntigravityProbeResult] = None


def antigravity_config_path(home: Optional[Path] = None) -> Path:
    """Return the native Antigravity config path."""
    base_home = Path(home) if home is not None else Path.home()
    return base_home.expanduser() / ANTIGRAVITY_CONFIG_RELATIVE_PATH


def detect_antigravity_installation(home: Optional[Path] = None) -> AntigravityInstallation:
    """Detect whether the user has created Antigravity native MCP config state."""
    config_path = antigravity_config_path(home=home)
    detected = config_path.parent.exists()
    return AntigravityInstallation(config_path=config_path, app_path=None, detected=detected)


def build_antigravity_ontos_entry(workspace_root: Path, *, write_enabled: bool = False) -> Dict[str, Any]:
    """Build the native Antigravity entry for the served Ontos workspace."""
    return build_ontos_stdio_entry(workspace_root, write_enabled=write_enabled)


def load_antigravity_config(path: Path) -> Dict[str, Any]:
    """Load and validate the top-level Antigravity config document."""
    try:
        return load_json_object_config(path, client_label="Antigravity", root_key="mcpServers")
    except MCPConfigError as exc:
        raise AntigravityConfigError(exc.code, str(exc)) from exc


def write_antigravity_config(path: Path, data: Dict[str, Any]) -> None:
    """Write the native Antigravity config with stable formatting."""
    write_json_object_config(path, data)


def upsert_antigravity_ontos_entry(existing: Optional[Dict[str, Any]], entry: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """Upsert only the Ontos server entry while preserving other servers."""
    try:
        return upsert_named_server_entry(existing, entry, root_key="mcpServers", client_label="Antigravity")
    except MCPConfigError as exc:
        raise AntigravityConfigError(exc.code, str(exc)) from exc


def probe_mcp_initialize(command: str, args: List[str], *, timeout: int = 15) -> AntigravityProbeResult:
    """Probe the configured command with one MCP initialize request."""
    result = shared_probe_mcp_initialize(command, args, timeout=timeout)
    return AntigravityProbeResult(
        ok=result.ok,
        message=result.message,
        details=result.details,
        server_info=result.server_info,
    )


def inspect_antigravity_ontos_config(home: Optional[Path] = None) -> AntigravityInspection:
    """Inspect the native Antigravity Ontos MCP configuration."""
    installation = detect_antigravity_installation(home=home)
    config_path = installation.config_path

    if not installation.detected:
        return AntigravityInspection(
            code="not_detected",
            ok=True,
            message="Antigravity not detected; skipping native MCP config check",
            details=None,
            config_path=config_path,
            detected=False,
        )

    if not config_path.exists():
        return AntigravityInspection(
            code="missing",
            ok=False,
            message="Antigravity native MCP config is missing",
            details=f"Run 'ontos mcp install --client antigravity' to create {config_path}.",
            config_path=config_path,
            detected=True,
        )

    try:
        data = load_antigravity_config(config_path)
    except AntigravityConfigError as exc:
        detail_map = {
            "empty": f"Run 'ontos mcp install --client antigravity' to write {config_path}.",
            "invalid_json": f"Fix or remove {config_path}, then rerun 'ontos mcp install --client antigravity'.",
            "invalid_root": f"Fix or remove {config_path}, then rerun 'ontos mcp install --client antigravity'.",
            "unreadable": str(exc),
        }
        return AntigravityInspection(
            code=exc.code,
            ok=False,
            message=str(exc),
            details=detail_map.get(exc.code, str(exc)),
            config_path=config_path,
            detected=True,
        )

    servers = data.get("mcpServers") or {}
    entry = servers.get("ontos")
    if not isinstance(entry, dict):
        return AntigravityInspection(
            code="missing_ontos_entry",
            ok=False,
            message="Antigravity config is missing mcpServers.ontos",
            details="Run 'ontos mcp install --client antigravity' to add the Ontos server entry.",
            config_path=config_path,
            detected=True,
        )

    command = entry.get("command")
    args = entry.get("args") or []
    if not isinstance(command, str) or not command.strip():
        return AntigravityInspection(
            code="bad_command",
            ok=False,
            message="Antigravity Ontos entry is missing a valid command",
            details="Run 'ontos mcp install --client antigravity' to regenerate the Ontos entry.",
            config_path=config_path,
            detected=True,
        )
    if not isinstance(args, list) or any(not isinstance(item, str) for item in args):
        return AntigravityInspection(
            code="bad_command",
            ok=False,
            message="Antigravity Ontos entry has invalid args",
            details="Expected 'args' to be a list of strings.",
            config_path=config_path,
            detected=True,
            command=command,
        )

    if resolve_executable(command) is None:
        return AntigravityInspection(
            code="bad_command",
            ok=False,
            message=f"Antigravity Ontos command is not executable: {command}",
            details="Run 'ontos mcp install --client antigravity' to rewrite the command path.",
            config_path=config_path,
            detected=True,
            command=command,
            args=tuple(args),
        )

    if "serve" not in args:
        return AntigravityInspection(
            code="bad_command",
            ok=False,
            message="Antigravity Ontos entry does not invoke 'serve'",
            details="Expected args to include 'serve'.",
            config_path=config_path,
            detected=True,
            command=command,
            args=tuple(args),
        )

    workspace = extract_workspace_arg(args)
    if workspace is None:
        return AntigravityInspection(
            code="bad_workspace",
            ok=False,
            message="Antigravity Ontos entry is missing --workspace",
            details="Run 'ontos mcp install --client antigravity' to add an absolute workspace path.",
            config_path=config_path,
            detected=True,
            command=command,
            args=tuple(args),
        )
    if not workspace.is_absolute():
        return AntigravityInspection(
            code="bad_workspace",
            ok=False,
            message="Antigravity Ontos workspace must be an absolute path",
            details=f"Observed workspace: {workspace}",
            config_path=config_path,
            detected=True,
            command=command,
            args=tuple(args),
            workspace=workspace,
        )
    if not workspace.exists():
        return AntigravityInspection(
            code="bad_workspace",
            ok=False,
            message=f"Antigravity Ontos workspace does not exist: {workspace}",
            details="Run 'ontos mcp install --client antigravity --workspace /absolute/path' with a valid project root.",
            config_path=config_path,
            detected=True,
            command=command,
            args=tuple(args),
            workspace=workspace,
        )

    mode = "read-only" if "--read-only" in args else "write-enabled"
    probe = probe_mcp_initialize(command, args)
    if not probe.ok:
        return AntigravityInspection(
            code="probe_failed",
            ok=False,
            message="Antigravity Ontos entry failed a direct MCP initialize probe",
            details=probe.details or probe.message,
            config_path=config_path,
            detected=True,
            mode=mode,
            command=command,
            args=tuple(args),
            workspace=workspace,
            probe=probe,
        )

    return AntigravityInspection(
        code="ok",
        ok=True,
        message=f"Antigravity Ontos entry valid ({mode})",
        details=None,
        config_path=config_path,
        detected=True,
        mode=mode,
        command=command,
        args=tuple(args),
        workspace=workspace,
        probe=probe,
    )
