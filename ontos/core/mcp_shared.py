"""Shared helpers for MCP client configuration adapters."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Protocol, Tuple

try:
    import tomli_w
except ImportError:  # pragma: no cover - exercised once dependency is installed
    tomli_w = None  # type: ignore[assignment]


INITIALIZE_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "ontos-mcp-check", "version": "0"},
    },
}


class MCPConfigError(ValueError):
    """Raised when a client MCP config is malformed."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class MCPConfigScopeError(MCPConfigError):
    """Raised when a config path resolves outside its expected scope."""


@dataclass(frozen=True)
class MCPProbeResult:
    """Result of a lightweight MCP initialize probe."""

    ok: bool
    message: str
    details: Optional[str] = None
    server_info: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class MCPClientContract:
    """Documented contract metadata for a supported MCP client."""

    client: str
    managed: bool
    format: str
    root_key: str
    default_scope: str
    supported_scopes: Tuple[str, ...]
    source_url: str
    last_verified: str


class ManagedMCPAdapter(Protocol):
    """Required interface for managed direct-file MCP adapters."""

    client_name: str
    supported_scopes: Tuple[str, ...]
    default_scope: str

    def resolve_config_path(
        self,
        *,
        scope: str,
        workspace_root: Path,
        home: Optional[Path] = None,
        config_path_override: Optional[Path] = None,
    ) -> Path:
        ...

    def build_ontos_entry(
        self,
        *,
        workspace_root: Path,
        write_enabled: bool,
    ) -> Dict[str, object]:
        ...

    def load_config(self, path: Path) -> Dict[str, object]:
        ...

    def write_config(self, path: Path, data: Dict[str, object]) -> None:
        ...

    def upsert_ontos_entry(
        self,
        existing: Optional[Dict[str, object]],
        entry: Dict[str, object],
    ) -> Tuple[Dict[str, object], str]:
        ...

    def remove_ontos_entry(
        self,
        existing: Optional[Dict[str, object]],
    ) -> Tuple[Optional[Dict[str, object]], str]:
        ...


MCP_CLIENT_CONTRACTS: Dict[str, MCPClientContract] = {
    "antigravity": MCPClientContract(
        client="antigravity",
        managed=True,
        format="json",
        root_key="mcpServers",
        default_scope="user",
        supported_scopes=("user",),
        source_url="internal:ontos-v4.1.3-antigravity",
        last_verified="2026-04-13",
    ),
    "cursor": MCPClientContract(
        client="cursor",
        managed=True,
        format="json",
        root_key="mcpServers",
        default_scope="project",
        supported_scopes=("project", "user"),
        source_url="https://docs.cursor.com/context/mcp",
        last_verified="2026-04-13",
    ),
    "claude-code": MCPClientContract(
        client="claude-code",
        managed=False,
        format="json",
        root_key="mcpServers",
        default_scope="project",
        supported_scopes=("project",),
        source_url="https://docs.anthropic.com/en/docs/claude-code/settings",
        last_verified="2026-04-13",
    ),
    "codex": MCPClientContract(
        client="codex",
        managed=False,
        format="toml",
        root_key="mcp_servers",
        default_scope="user",
        supported_scopes=("user",),
        source_url="https://platform.openai.com/docs/docs-mcp",
        last_verified="2026-04-13",
    ),
    "vscode": MCPClientContract(
        client="vscode",
        managed=False,
        format="json",
        root_key="servers",
        default_scope="project",
        supported_scopes=("project",),
        source_url="https://code.visualstudio.com/docs/copilot/reference/mcp-configuration",
        last_verified="2026-04-13",
    ),
}


def get_client_contract(client: str) -> MCPClientContract:
    """Return the documented contract metadata for a client."""
    try:
        return MCP_CLIENT_CONTRACTS[client]
    except KeyError as exc:
        raise KeyError(f"Unsupported MCP client contract: {client}") from exc


def resolve_ontos_launcher() -> Tuple[str, List[str]]:
    """Resolve the preferred Ontos launcher for external MCP clients."""
    ontos_path = shutil.which("ontos")
    if ontos_path:
        return str(Path(ontos_path).resolve()), []
    return str(Path(sys.executable).resolve()), ["-m", "ontos"]


def build_ontos_stdio_entry(workspace_root: Path, *, write_enabled: bool = False) -> Dict[str, Any]:
    """Build a stdio MCP entry for Ontos."""
    command, prefix_args = resolve_ontos_launcher()
    args = [*prefix_args, "serve", "--workspace", str(workspace_root.expanduser().resolve())]
    if not write_enabled:
        args.append("--read-only")
    return {"command": command, "args": args}


def build_ontos_entry(workspace_root: Path, *, write_enabled: bool = False) -> Dict[str, Any]:
    """Backward-compatible alias for the shared Ontos stdio entry builder."""
    return build_ontos_stdio_entry(workspace_root, write_enabled=write_enabled)


def entries_equivalent(existing_entry: Mapping[str, Any], new_entry: Mapping[str, Any]) -> bool:
    """Compare only the Ontos-owned command line fields."""
    return existing_entry.get("command") == new_entry.get("command") and existing_entry.get("args") == new_entry.get("args")


def load_json_object_config(path: Path, *, client_label: str, root_key: str) -> Dict[str, Any]:
    """Load and validate a JSON config whose root must be an object."""
    if not path.exists():
        raise MCPConfigError("missing", f"{client_label} MCP config not found: {path}")

    try:
        if path.stat().st_size == 0:
            raise MCPConfigError("empty", f"{client_label} MCP config is empty: {path}")
    except OSError as exc:
        raise MCPConfigError("unreadable", f"Could not read {client_label} MCP config: {exc}") from exc

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MCPConfigError("unreadable", f"Could not read {client_label} MCP config: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MCPConfigError("invalid_json", f"{client_label} MCP config is invalid JSON: {path}") from exc

    if not isinstance(data, dict):
        raise MCPConfigError("invalid_root", f"{client_label} MCP config root must be a JSON object")

    servers = data.get(root_key)
    if servers is not None and not isinstance(servers, dict):
        raise MCPConfigError("invalid_root", f"{client_label} MCP config field '{root_key}' must be an object")

    return data


def write_json_object_config(path: Path, data: Dict[str, Any]) -> None:
    """Write a JSON config with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def upsert_named_server_entry(
    existing: Optional[Dict[str, Any]],
    entry: Dict[str, Any],
    *,
    root_key: str,
    client_label: str,
    server_name: str = "ontos",
) -> Tuple[Dict[str, Any], str]:
    """Upsert a server entry while preserving sibling data."""
    payload: Dict[str, Any] = dict(existing or {})
    current_servers = payload.get(root_key)
    if current_servers is None:
        servers: Dict[str, Any] = {}
        payload[root_key] = servers
    elif isinstance(current_servers, dict):
        servers = dict(current_servers)
        payload[root_key] = servers
    else:
        raise MCPConfigError("invalid_root", f"{client_label} MCP config field '{root_key}' must be an object")

    existing_entry = servers.get(server_name)
    if isinstance(existing_entry, dict) and entries_equivalent(existing_entry, entry):
        return payload, "noop"

    action = "created" if server_name not in servers else "updated"
    servers[server_name] = entry
    return payload, action


def remove_named_server_entry(
    existing: Optional[Dict[str, Any]],
    *,
    root_key: str,
    client_label: str,
    server_name: str = "ontos",
) -> Tuple[Optional[Dict[str, Any]], str]:
    """Remove only the named server entry while preserving sibling data."""
    if existing is None:
        return None, "noop"

    payload: Dict[str, Any] = dict(existing)
    current_servers = payload.get(root_key)
    if current_servers is None:
        return payload, "noop"
    if not isinstance(current_servers, dict):
        raise MCPConfigError("invalid_root", f"{client_label} MCP config field '{root_key}' must be an object")

    servers = dict(current_servers)
    if server_name not in servers:
        payload[root_key] = servers
        return payload, "noop"

    del servers[server_name]
    payload[root_key] = servers
    return payload, "removed"


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


def probe_mcp_initialize(command: str, args: List[str], *, timeout: int = 15) -> MCPProbeResult:
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
        return MCPProbeResult(ok=False, message="initialize probe failed", details=str(exc))
    except subprocess.TimeoutExpired as exc:
        return MCPProbeResult(ok=False, message="initialize probe timed out", details=str(exc))
    except OSError as exc:
        return MCPProbeResult(ok=False, message="initialize probe failed", details=str(exc))

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        return MCPProbeResult(ok=False, message="initialize probe failed", details=details)

    stdout = result.stdout.strip()
    if not stdout:
        return MCPProbeResult(ok=False, message="initialize probe failed", details="stdout was empty")

    first_line = stdout.splitlines()[0]
    try:
        response = json.loads(first_line)
    except json.JSONDecodeError as exc:
        return MCPProbeResult(
            ok=False,
            message="initialize probe failed",
            details=f"Invalid JSON-RPC response: {exc}",
        )

    result_payload = response.get("result")
    if not isinstance(result_payload, dict):
        return MCPProbeResult(
            ok=False,
            message="initialize probe failed",
            details=f"Unexpected response payload: {response}",
        )

    server_info = result_payload.get("serverInfo")
    return MCPProbeResult(
        ok=True,
        message="initialize probe passed",
        server_info=server_info if isinstance(server_info, dict) else None,
    )


def _json_document(root_key: str, entry: Mapping[str, Any], *, stdio_type: bool = False) -> str:
    payload: Dict[str, Any] = {root_key: {"ontos": dict(entry)}}
    if stdio_type:
        typed_entry = dict(entry)
        typed_entry["type"] = "stdio"
        payload[root_key]["ontos"] = typed_entry
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _toml_document(root_key: str, entry: Mapping[str, Any]) -> str:
    if tomli_w is None:  # pragma: no cover - depends on environment packaging
        raise RuntimeError("tomli_w is required to render TOML MCP config output")
    payload = {root_key: {"ontos": dict(entry)}}
    return tomli_w.dumps(payload)


def render_client_config_document(
    client: str,
    *,
    workspace_root: Path,
    write_enabled: bool = False,
) -> Tuple[str, str]:
    """Render a complete config document for a supported client."""
    contract = get_client_contract(client)
    entry = build_ontos_stdio_entry(workspace_root, write_enabled=write_enabled)

    if contract.format == "json":
        include_stdio_type = contract.root_key == "servers"
        return "json", _json_document(contract.root_key, entry, stdio_type=include_stdio_type)
    if contract.format == "toml":
        return "toml", _toml_document(contract.root_key, entry)
    raise ValueError(f"Unsupported config format for client {client}: {contract.format}")
