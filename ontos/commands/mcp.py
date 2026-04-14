"""Client-side MCP configuration commands."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from ontos.core.antigravity_mcp import (
    AntigravityConfigError,
    antigravity_config_path,
    build_antigravity_ontos_entry,
    load_antigravity_config,
    write_antigravity_config,
)
from ontos.io.files import find_project_root


@dataclass(frozen=True)
class MCPClientContract:
    """Contract metadata for a supported MCP client."""

    client: str
    managed: bool
    format: str
    root_key: str
    default_scope: str
    supported_scopes: Tuple[str, ...]


@dataclass
class MCPInstallOptions:
    """Configuration for `ontos mcp install`."""

    client: str = "antigravity"
    workspace: Optional[Path] = None
    scope: Optional[str] = None
    write_enabled: bool = False
    config_path: Optional[Path] = None


@dataclass
class MCPUninstallOptions:
    """Configuration for `ontos mcp uninstall`."""

    client: str = "antigravity"
    scope: Optional[str] = None
    config_path: Optional[Path] = None


@dataclass
class MCPPrintConfigOptions:
    """Configuration for `ontos mcp print-config`."""

    client: str = "antigravity"
    workspace: Optional[Path] = None
    scope: Optional[str] = None
    write_enabled: bool = False
    config_path: Optional[Path] = None


CLIENT_CONTRACTS: Dict[str, MCPClientContract] = {
    "antigravity": MCPClientContract(
        client="antigravity",
        managed=True,
        format="json",
        root_key="mcpServers",
        default_scope="user",
        supported_scopes=("user",),
    ),
    "cursor": MCPClientContract(
        client="cursor",
        managed=True,
        format="json",
        root_key="mcpServers",
        default_scope="project",
        supported_scopes=("project", "user"),
    ),
    "claude-code": MCPClientContract(
        client="claude-code",
        managed=False,
        format="json",
        root_key="mcpServers",
        default_scope="project",
        supported_scopes=("project",),
    ),
    "codex": MCPClientContract(
        client="codex",
        managed=False,
        format="toml",
        root_key="mcp_servers",
        default_scope="user",
        supported_scopes=("user",),
    ),
    "vscode": MCPClientContract(
        client="vscode",
        managed=False,
        format="json",
        root_key="servers",
        default_scope="project",
        supported_scopes=("project",),
    ),
}


class MCPConfigError(ValueError):
    """Raised when an MCP client config document is malformed."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


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


def _contract_for(client: str) -> Optional[MCPClientContract]:
    """Return contract metadata for the requested client."""
    return CLIENT_CONTRACTS.get(client)


def _resolve_scope(contract: MCPClientContract, requested_scope: Optional[str]) -> Tuple[int, Optional[str], str]:
    """Resolve and validate the requested client scope."""
    scope = requested_scope or contract.default_scope
    if scope not in contract.supported_scopes:
        supported = ", ".join(contract.supported_scopes)
        return 2, None, f"Unsupported scope for {contract.client}: {scope} (supported: {supported})"
    return 0, scope, ""


def _validate_config_path_extension(contract: MCPClientContract, config_path: Path) -> Tuple[int, str]:
    """Validate `--config-path` against the client config format."""
    suffix = config_path.suffix.lower()
    expected = ".toml" if contract.format == "toml" else ".json"
    if suffix != expected:
        return 2, (
            f"Config path extension mismatch for {contract.client}: "
            f"expected {expected}, got {config_path}"
        )
    return 0, ""


def _default_config_path(
    contract: MCPClientContract,
    *,
    scope: str,
    workspace_root: Optional[Path],
    home: Optional[Path] = None,
) -> Path:
    """Resolve the default config path for the requested client and scope."""
    base_home = (home or Path.home()).expanduser()

    if contract.client == "antigravity":
        return antigravity_config_path(home=base_home)
    if contract.client == "cursor":
        if scope == "project":
            assert workspace_root is not None
            return workspace_root / ".cursor" / "mcp.json"
        return base_home / ".cursor" / "mcp.json"
    if contract.client == "claude-code":
        assert workspace_root is not None
        return workspace_root / ".mcp.json"
    if contract.client == "codex":
        return base_home / ".codex" / "config.toml"
    if contract.client == "vscode":
        assert workspace_root is not None
        return workspace_root / ".vscode" / "mcp.json"

    raise ValueError(f"Unsupported client: {contract.client}")


def _resolve_config_path(
    contract: MCPClientContract,
    *,
    scope: str,
    workspace_root: Optional[Path],
    config_path_override: Optional[Path],
) -> Tuple[int, Optional[Path], str]:
    """Resolve the final config path, including override validation."""
    if config_path_override is not None:
        config_path = config_path_override.expanduser().resolve()
        exit_code, error = _validate_config_path_extension(contract, config_path)
        if exit_code != 0:
            return exit_code, None, error
        return 0, config_path, ""

    return 0, _default_config_path(contract, scope=scope, workspace_root=workspace_root), ""


def _load_json_object_config(path: Path, *, client_label: str, root_key: str) -> Dict[str, Any]:
    """Load and validate a JSON object config document."""
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

    root = data.get(root_key)
    if root is not None and not isinstance(root, dict):
        raise MCPConfigError("invalid_root", f"{client_label} MCP config field '{root_key}' must be an object")

    return data


def _write_json_object_config(path: Path, data: Mapping[str, Any]) -> None:
    """Write a JSON object config with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(data), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _entries_equivalent(existing_entry: Optional[Mapping[str, Any]], new_entry: Mapping[str, Any]) -> bool:
    """Compare only Ontos-owned fields for install noop detection."""
    if not isinstance(existing_entry, Mapping):
        return False
    return existing_entry.get("command") == new_entry.get("command") and existing_entry.get("args") == new_entry.get("args")


def _upsert_server_entry(
    existing: Optional[Dict[str, Any]],
    *,
    root_key: str,
    entry: Mapping[str, Any],
) -> Tuple[Dict[str, Any], str]:
    """Upsert a single Ontos server entry while preserving sibling data."""
    payload: Dict[str, Any] = dict(existing or {})
    root = payload.setdefault(root_key, {})
    if not isinstance(root, dict):
        raise MCPConfigError("invalid_root", f"MCP config field '{root_key}' must be an object")

    existing_entry = root.get("ontos")
    if _entries_equivalent(existing_entry, entry):
        return payload, "noop"

    action = "created" if not isinstance(existing_entry, Mapping) else "updated"
    root["ontos"] = dict(entry)
    return payload, action


def _remove_server_entry(existing: Optional[Dict[str, Any]], *, root_key: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Remove only the Ontos server entry while preserving the rest of the document."""
    if existing is None:
        return None, "noop"

    payload: Dict[str, Any] = dict(existing)
    root = payload.setdefault(root_key, {})
    if not isinstance(root, dict):
        raise MCPConfigError("invalid_root", f"MCP config field '{root_key}' must be an object")

    if "ontos" not in root:
        return payload, "noop"

    root.pop("ontos", None)
    return payload, "removed"


def _build_stdio_entry(workspace_root: Path, *, write_enabled: bool) -> Dict[str, Any]:
    """Build the standard Ontos stdio entry."""
    return build_antigravity_ontos_entry(workspace_root, write_enabled=write_enabled)


def _render_json_snippet(contract: MCPClientContract, entry: Mapping[str, Any]) -> str:
    """Render a complete JSON document for print-config output."""
    rendered_entry: Dict[str, Any]
    if contract.client == "vscode":
        rendered_entry = {"type": "stdio", **dict(entry)}
    else:
        rendered_entry = dict(entry)

    payload = {contract.root_key: {"ontos": rendered_entry}}
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _render_toml_snippet(entry: Mapping[str, Any]) -> str:
    """Render a complete TOML document for Codex print-config output."""
    try:
        import tomli_w
    except ModuleNotFoundError as exc:
        raise RuntimeError("tomli_w is required for Codex print-config output") from exc

    return tomli_w.dumps({"mcp_servers": {"ontos": dict(entry)}})


def _render_print_config_snippet(contract: MCPClientContract, entry: Mapping[str, Any]) -> str:
    """Render the full self-contained document for print-config or fallback output."""
    if contract.format == "toml":
        return _render_toml_snippet(entry)
    return _render_json_snippet(contract, entry)


def _load_managed_config(contract: MCPClientContract, config_path: Path) -> Dict[str, Any]:
    """Load a managed client config document."""
    if contract.client == "antigravity":
        return load_antigravity_config(config_path)
    return _load_json_object_config(config_path, client_label=contract.client.capitalize(), root_key=contract.root_key)


def _write_managed_config(contract: MCPClientContract, config_path: Path, data: Dict[str, Any]) -> None:
    """Write a managed client config document."""
    if contract.client == "antigravity":
        write_antigravity_config(config_path, data)
        return
    _write_json_object_config(config_path, data)


def _fallback_data(
    contract: MCPClientContract,
    *,
    scope: str,
    workspace_root: Path,
    config_path: Path,
    write_enabled: bool,
    error: str,
) -> Dict[str, str]:
    """Build additive failure payload data, including manual fallback output."""
    snippet = _render_print_config_snippet(
        contract,
        _build_stdio_entry(workspace_root, write_enabled=write_enabled),
    )
    return {
        "client": contract.client,
        "scope": scope,
        "config_path": str(config_path),
        "error": error,
        "fallback_format": contract.format,
        "fallback_snippet": snippet,
    }


def _run_mcp_install_command(options: MCPInstallOptions) -> Tuple[int, str, Dict[str, Any]]:
    """Install or update a supported native MCP client config."""
    contract = _contract_for(options.client)
    if contract is None or not contract.managed:
        return 2, f"Unsupported MCP client: {options.client}", {}

    exit_code, scope, error_message = _resolve_scope(contract, options.scope)
    if exit_code != 0 or scope is None:
        return exit_code, error_message, {}

    exit_code, workspace_root, error_message = _resolve_workspace_root(options.workspace)
    if exit_code != 0 or workspace_root is None:
        return exit_code, error_message, {}

    exit_code, config_path, error_message = _resolve_config_path(
        contract,
        scope=scope,
        workspace_root=workspace_root,
        config_path_override=options.config_path,
    )
    if exit_code != 0 or config_path is None:
        return exit_code, error_message, {}

    existing = None
    if config_path.exists():
        try:
            existing = _load_managed_config(contract, config_path)
        except (AntigravityConfigError, MCPConfigError) as exc:
            return 2, str(exc), _fallback_data(
                contract,
                scope=scope,
                workspace_root=workspace_root,
                config_path=config_path,
                write_enabled=options.write_enabled,
                error=str(exc),
            )

    entry = _build_stdio_entry(workspace_root, write_enabled=options.write_enabled)
    updated_config, action = _upsert_server_entry(existing, root_key=contract.root_key, entry=entry)
    if action != "noop":
        try:
            _write_managed_config(contract, config_path, updated_config)
        except OSError as exc:
            return 2, f"Could not write config: {config_path}: {exc}", _fallback_data(
                contract,
                scope=scope,
                workspace_root=workspace_root,
                config_path=config_path,
                write_enabled=options.write_enabled,
                error=str(exc),
            )

    mode = "write-enabled" if options.write_enabled else "read-only"
    if action == "created":
        message = f"Created {contract.client} MCP config at {config_path}"
    elif action == "updated":
        message = f"Updated {contract.client} MCP config at {config_path}"
    else:
        message = f"{contract.client.capitalize()} MCP config already up to date at {config_path}"

    data: Dict[str, Any] = {
        "client": contract.client,
        "scope": scope,
        "action": action,
        "config_path": str(config_path),
        "workspace": str(workspace_root),
        "mode": mode,
    }
    return 0, message, data


def _run_mcp_uninstall_command(options: MCPUninstallOptions) -> Tuple[int, str, Dict[str, Any]]:
    """Remove the Ontos MCP entry for a managed client."""
    contract = _contract_for(options.client)
    if contract is None or not contract.managed:
        return 2, f"Unsupported MCP client: {options.client}", {}

    exit_code, scope, error_message = _resolve_scope(contract, options.scope)
    if exit_code != 0 or scope is None:
        return exit_code, error_message, {}

    workspace_root: Optional[Path] = None
    if scope == "project" or options.config_path is None:
        exit_code, workspace_root, error_message = _resolve_workspace_root(None)
        if exit_code != 0 and options.config_path is None:
            return exit_code, error_message, {}

    exit_code, config_path, error_message = _resolve_config_path(
        contract,
        scope=scope,
        workspace_root=workspace_root,
        config_path_override=options.config_path,
    )
    if exit_code != 0 or config_path is None:
        return exit_code, error_message, {}

    if not config_path.exists():
        return 0, f"No Ontos MCP entry found at {config_path}", {
            "client": contract.client,
            "scope": scope,
            "action": "noop",
            "config_path": str(config_path),
        }

    try:
        existing = _load_managed_config(contract, config_path)
    except (AntigravityConfigError, MCPConfigError) as exc:
        if workspace_root is None:
            exit_code, workspace_root, error_message = _resolve_workspace_root(None)
            if exit_code != 0 or workspace_root is None:
                return 2, str(exc), {"config_path": str(config_path), "error": str(exc)}
        return 2, str(exc), _fallback_data(
            contract,
            scope=scope,
            workspace_root=workspace_root,
            config_path=config_path,
            write_enabled=False,
            error=str(exc),
        )

    updated_config, action = _remove_server_entry(existing, root_key=contract.root_key)
    if action != "noop" and updated_config is not None:
        try:
            _write_managed_config(contract, config_path, updated_config)
        except OSError as exc:
            if workspace_root is None:
                exit_code, workspace_root, error_message = _resolve_workspace_root(None)
                if exit_code != 0 or workspace_root is None:
                    return 2, f"Could not write config: {config_path}: {exc}", {
                        "config_path": str(config_path),
                        "error": str(exc),
                    }
            return 2, f"Could not write config: {config_path}: {exc}", _fallback_data(
                contract,
                scope=scope,
                workspace_root=workspace_root,
                config_path=config_path,
                write_enabled=False,
                error=str(exc),
            )

    if action == "removed":
        message = f"Removed Ontos MCP entry from {config_path}"
    else:
        message = f"No Ontos MCP entry found at {config_path}"

    return 0, message, {
        "client": contract.client,
        "scope": scope,
        "action": action,
        "config_path": str(config_path),
    }


def _run_mcp_print_config_command(options: MCPPrintConfigOptions) -> Tuple[int, str, Dict[str, Any]]:
    """Render the full manual config document without writing to disk."""
    contract = _contract_for(options.client)
    if contract is None:
        return 2, f"Unsupported MCP client: {options.client}", {}

    exit_code, scope, error_message = _resolve_scope(contract, options.scope)
    if exit_code != 0 or scope is None:
        return exit_code, error_message, {}

    needs_workspace = True
    exit_code, workspace_root, error_message = _resolve_workspace_root(options.workspace)
    if needs_workspace and (exit_code != 0 or workspace_root is None):
        return exit_code, error_message, {}

    exit_code, config_path, error_message = _resolve_config_path(
        contract,
        scope=scope,
        workspace_root=workspace_root,
        config_path_override=options.config_path,
    )
    if exit_code != 0 or config_path is None:
        return exit_code, error_message, {}

    try:
        snippet = _render_print_config_snippet(
            contract,
            _build_stdio_entry(workspace_root, write_enabled=options.write_enabled),
        )
    except RuntimeError as exc:
        return 5, str(exc), {"client": contract.client, "scope": scope, "config_path": str(config_path)}

    data: Dict[str, Any] = {
        "client": contract.client,
        "scope": scope,
        "config_path": str(config_path),
        "format": contract.format,
        "snippet": snippet,
    }
    message = f"Generated {contract.client} MCP config for {config_path}"
    return 0, message, data


def mcp_install_command(options: MCPInstallOptions) -> int:
    """Run `ontos mcp install` and return an exit code."""
    exit_code, _, _ = _run_mcp_install_command(options)
    return exit_code
