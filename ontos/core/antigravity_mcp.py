"""Helpers for Antigravity native MCP configuration."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ANTIGRAVITY_CONFIG_RELATIVE_PATH = Path(".gemini") / "antigravity" / "mcp_config.json"

INITIALIZE_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "ontos-antigravity-check", "version": "0"},
    },
}


class AntigravityConfigError(ValueError):
    """Raised when the native Antigravity config is malformed."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


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


def antigravity_app_candidates(home: Optional[Path] = None) -> List[Path]:
    """Return possible Antigravity app bundle locations."""
    base_home = Path(home) if home is not None else Path.home()
    return [
        Path("/Applications/Antigravity.app"),
        base_home.expanduser() / "Applications" / "Antigravity.app",
    ]


def detect_antigravity_installation(home: Optional[Path] = None) -> AntigravityInstallation:
    """Detect whether Antigravity is installed or already configured."""
    config_path = antigravity_config_path(home=home)
    app_path = next((path for path in antigravity_app_candidates(home=home) if path.exists()), None)
    detected = app_path is not None or config_path.exists() or config_path.parent.exists()
    return AntigravityInstallation(config_path=config_path, app_path=app_path, detected=detected)


def resolve_ontos_launcher() -> Tuple[str, List[str]]:
    """Resolve the preferred Ontos launcher for external MCP clients."""
    ontos_path = shutil.which("ontos")
    if ontos_path:
        return str(Path(ontos_path).resolve()), []
    return str(Path(sys.executable).resolve()), ["-m", "ontos"]


def build_antigravity_ontos_entry(workspace_root: Path, *, write_enabled: bool = False) -> Dict[str, Any]:
    """Build the native Antigravity entry for the served Ontos workspace."""
    command, prefix_args = resolve_ontos_launcher()
    args = [*prefix_args, "serve", "--workspace", str(workspace_root.expanduser().resolve())]
    if not write_enabled:
        args.append("--read-only")
    return {"command": command, "args": args}


def load_antigravity_config(path: Path) -> Dict[str, Any]:
    """Load and validate the top-level Antigravity config document."""
    if not path.exists():
        raise AntigravityConfigError("missing", f"Antigravity MCP config not found: {path}")

    try:
        if path.stat().st_size == 0:
            raise AntigravityConfigError("empty", f"Antigravity MCP config is empty: {path}")
    except OSError as exc:
        raise AntigravityConfigError("unreadable", f"Could not read Antigravity MCP config: {exc}") from exc

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AntigravityConfigError("unreadable", f"Could not read Antigravity MCP config: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AntigravityConfigError("invalid_json", f"Antigravity MCP config is invalid JSON: {path}") from exc

    if not isinstance(data, dict):
        raise AntigravityConfigError("invalid_root", "Antigravity MCP config root must be a JSON object")

    servers = data.get("mcpServers")
    if servers is not None and not isinstance(servers, dict):
        raise AntigravityConfigError("invalid_root", "Antigravity MCP config field 'mcpServers' must be an object")

    return data


def write_antigravity_config(path: Path, data: Dict[str, Any]) -> None:
    """Write the native Antigravity config with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def upsert_antigravity_ontos_entry(existing: Optional[Dict[str, Any]], entry: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """Upsert only the Ontos server entry while preserving other servers."""
    action = "created" if existing is None else "updated"
    payload: Dict[str, Any] = dict(existing or {})
    servers = payload.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise AntigravityConfigError("invalid_root", "Antigravity MCP config field 'mcpServers' must be an object")
    servers["ontos"] = entry
    return payload, action


def extract_workspace_arg(args: List[str]) -> Optional[Path]:
    """Extract the workspace argument from an Ontos stdio command line."""
    for index, value in enumerate(args):
        if value == "--workspace" and index + 1 < len(args):
            return Path(args[index + 1]).expanduser()
        if value.startswith("--workspace="):
            return Path(value.split("=", 1)[1]).expanduser()
    return None


def resolve_executable(command: str) -> Optional[str]:
    """Resolve a command to an executable path if possible."""
    if not command:
        return None
    if os.path.sep in command or (os.path.altsep and os.path.altsep in command):
        candidate = Path(command).expanduser()
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate.resolve())
        return None
    resolved = shutil.which(command)
    if not resolved:
        return None
    return str(Path(resolved).resolve())


def probe_mcp_initialize(command: str, args: List[str], *, timeout: int = 15) -> AntigravityProbeResult:
    """Probe the configured command with one MCP initialize request."""
    payload = json.dumps(INITIALIZE_REQUEST) + "\n"

    try:
        result = subprocess.run(
            [command, *args],
            input=payload,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return AntigravityProbeResult(ok=False, message="initialize probe failed", details=str(exc))
    except subprocess.TimeoutExpired as exc:
        return AntigravityProbeResult(ok=False, message="initialize probe timed out", details=str(exc))
    except OSError as exc:
        return AntigravityProbeResult(ok=False, message="initialize probe failed", details=str(exc))

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        return AntigravityProbeResult(ok=False, message="initialize probe failed", details=details)

    stdout = result.stdout.strip()
    if not stdout:
        return AntigravityProbeResult(ok=False, message="initialize probe failed", details="stdout was empty")

    first_line = stdout.splitlines()[0]
    try:
        response = json.loads(first_line)
    except json.JSONDecodeError as exc:
        return AntigravityProbeResult(
            ok=False,
            message="initialize probe failed",
            details=f"Invalid JSON-RPC response: {exc}",
        )

    result_payload = response.get("result")
    if not isinstance(result_payload, dict):
        return AntigravityProbeResult(
            ok=False,
            message="initialize probe failed",
            details=f"Unexpected response payload: {response}",
        )

    server_info = result_payload.get("serverInfo")
    return AntigravityProbeResult(
        ok=True,
        message="initialize probe passed",
        server_info=server_info if isinstance(server_info, dict) else None,
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
