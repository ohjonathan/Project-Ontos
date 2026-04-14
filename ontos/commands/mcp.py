"""Client-side MCP configuration commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ontos.core.antigravity_mcp import (
    AntigravityConfigError,
    antigravity_config_path,
    build_antigravity_ontos_entry,
    load_antigravity_config,
    upsert_antigravity_ontos_entry,
    write_antigravity_config,
)
from ontos.core.cursor_mcp import CURSOR_MCP_ADAPTER, CursorConfigError
from ontos.core.mcp_shared import (
    MCPConfigError,
    MCPConfigScopeError,
    get_client_contract,
    remove_named_server_entry,
    render_client_config_document,
    validate_config_path_scope,
)
from ontos.io.files import find_project_root


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


def _resolve_scope(client: str, requested_scope: Optional[str]) -> Tuple[int, Optional[str], str]:
    """Resolve and validate the requested client scope."""
    try:
        contract = get_client_contract(client)
    except KeyError:
        return 2, None, f"Unsupported MCP client: {client}"

    scope = requested_scope or contract.default_scope
    if scope not in contract.supported_scopes:
        supported = ", ".join(contract.supported_scopes)
        return 2, None, f"Unsupported scope for {client}: {scope} (supported: {supported})"
    return 0, scope, ""


def _validate_config_path_extension(client: str, config_path: Path) -> Tuple[int, str]:
    """Validate `--config-path` against the client config format."""
    contract = get_client_contract(client)
    expected = ".toml" if contract.format == "toml" else ".json"
    if config_path.suffix.lower() != expected:
        return 2, (
            f"Config path extension mismatch for {client}: "
            f"expected {expected}, got {config_path}"
        )
    return 0, ""


def _resolve_managed_config_path(
    *,
    client: str,
    scope: str,
    workspace_root: Path,
    config_path_override: Optional[Path],
) -> Tuple[int, Optional[Path], str]:
    """Resolve the managed config path using the owning adapter layer."""
    override = None
    if config_path_override is not None:
        override = config_path_override.expanduser().resolve()
        exit_code, error = _validate_config_path_extension(client, override)
        if exit_code != 0:
            return exit_code, None, error

    if client == "antigravity":
        return 0, override or antigravity_config_path(), ""
    if client == "cursor":
        return 0, CURSOR_MCP_ADAPTER.resolve_config_path(
            scope=scope,
            workspace_root=workspace_root,
            config_path_override=override,
        ), ""
    return 2, None, f"Unsupported MCP client: {client}"


def _validate_managed_config_scope(config_path: Path, scope: str, workspace_root: Path) -> Tuple[int, str]:
    """Reject config paths that resolve outside the expected scope."""
    try:
        validate_config_path_scope(
            config_path,
            scope,
            workspace_root=workspace_root,
            home=Path.home(),
        )
    except (MCPConfigScopeError, ValueError) as exc:
        return 2, str(exc)
    return 0, ""


def _resolve_print_config_path(
    *,
    client: str,
    scope: str,
    workspace_root: Path,
    config_path_override: Optional[Path],
) -> Tuple[int, Optional[Path], str]:
    """Resolve the reported target path for print-config output."""
    override = None
    if config_path_override is not None:
        override = config_path_override.expanduser().resolve()
        exit_code, error = _validate_config_path_extension(client, override)
        if exit_code != 0:
            return exit_code, None, error
        return 0, override, ""

    if client == "antigravity":
        return 0, antigravity_config_path(), ""
    if client == "cursor":
        return 0, CURSOR_MCP_ADAPTER.resolve_config_path(scope=scope, workspace_root=workspace_root), ""
    if client == "claude-code":
        return 0, workspace_root / ".mcp.json", ""
    if client == "codex":
        return 0, Path.home().expanduser() / ".codex" / "config.toml", ""
    if client == "vscode":
        return 0, workspace_root / ".vscode" / "mcp.json", ""
    return 2, None, f"Unsupported MCP client: {client}"


def _build_fallback_data(
    *,
    client: str,
    scope: str,
    workspace_root: Path,
    config_path: Path,
    write_enabled: bool,
    error: str,
) -> Dict[str, Any]:
    """Build additive error data with a manual print-config fallback."""
    fallback_format, fallback_snippet = render_client_config_document(
        client,
        workspace_root=workspace_root,
        write_enabled=write_enabled,
    )
    return {
        "client": client,
        "scope": scope,
        "config_path": str(config_path),
        "error": error,
        "fallback_format": fallback_format,
        "fallback_snippet": fallback_snippet,
    }


def _load_managed_config(client: str, config_path: Path) -> Dict[str, object]:
    """Load a managed client config using the owning adapter."""
    if client == "antigravity":
        return load_antigravity_config(config_path)
    if client == "cursor":
        return CURSOR_MCP_ADAPTER.load_config(config_path)
    raise ValueError(f"Unsupported managed client: {client}")


def _build_managed_entry(client: str, workspace_root: Path, *, write_enabled: bool) -> Dict[str, object]:
    """Build the managed Ontos entry via the owning adapter layer."""
    if client == "antigravity":
        return build_antigravity_ontos_entry(workspace_root, write_enabled=write_enabled)
    if client == "cursor":
        return CURSOR_MCP_ADAPTER.build_ontos_entry(workspace_root=workspace_root, write_enabled=write_enabled)
    raise ValueError(f"Unsupported managed client: {client}")


def _upsert_managed_entry(
    client: str,
    existing: Optional[Dict[str, object]],
    entry: Dict[str, object],
) -> Tuple[Dict[str, object], str]:
    """Upsert a managed Ontos entry via the owning adapter layer."""
    if client == "antigravity":
        return upsert_antigravity_ontos_entry(existing, entry)
    if client == "cursor":
        return CURSOR_MCP_ADAPTER.upsert_ontos_entry(existing, entry)
    raise ValueError(f"Unsupported managed client: {client}")


def _write_managed_config(client: str, config_path: Path, data: Dict[str, object]) -> None:
    """Write a managed client config via the owning adapter layer."""
    if client == "antigravity":
        write_antigravity_config(config_path, data)
        return
    if client == "cursor":
        CURSOR_MCP_ADAPTER.write_config(config_path, data)
        return
    raise ValueError(f"Unsupported managed client: {client}")


def _remove_managed_entry(
    client: str,
    existing: Optional[Dict[str, object]],
) -> Tuple[Optional[Dict[str, object]], str]:
    """Remove a managed Ontos entry via the owning adapter layer."""
    if client == "antigravity":
        return remove_named_server_entry(existing, root_key="mcpServers", client_label="Antigravity")
    if client == "cursor":
        return CURSOR_MCP_ADAPTER.remove_ontos_entry(existing)
    raise ValueError(f"Unsupported managed client: {client}")


def _run_mcp_install_command(options: MCPInstallOptions) -> Tuple[int, str, Dict[str, Any]]:
    """Install or update a supported native MCP client config."""
    try:
        contract = get_client_contract(options.client)
    except KeyError:
        return 2, f"Unsupported MCP client: {options.client}", {}
    if not contract.managed:
        return 2, f"Unsupported MCP client: {options.client}", {}

    exit_code, scope, error_message = _resolve_scope(options.client, options.scope)
    if exit_code != 0 or scope is None:
        return exit_code, error_message, {}

    exit_code, workspace_root, error_message = _resolve_workspace_root(options.workspace)
    if exit_code != 0 or workspace_root is None:
        return exit_code, error_message, {}

    exit_code, config_path, error_message = _resolve_managed_config_path(
        client=options.client,
        scope=scope,
        workspace_root=workspace_root,
        config_path_override=options.config_path,
    )
    if exit_code != 0 or config_path is None:
        return exit_code, error_message, {}

    exit_code, error_message = _validate_managed_config_scope(config_path, scope, workspace_root)
    if exit_code != 0:
        return exit_code, error_message, {}

    existing = None
    if config_path.exists():
        try:
            existing = _load_managed_config(options.client, config_path)
        except (AntigravityConfigError, CursorConfigError, MCPConfigError) as exc:
            return 2, str(exc), _build_fallback_data(
                client=options.client,
                scope=scope,
                workspace_root=workspace_root,
                config_path=config_path,
                write_enabled=options.write_enabled,
                error=str(exc),
            )

    entry = _build_managed_entry(options.client, workspace_root, write_enabled=options.write_enabled)
    updated_config, action = _upsert_managed_entry(options.client, existing, entry)

    if action != "noop":
        try:
            _write_managed_config(options.client, config_path, updated_config)
        except OSError as exc:
            return 2, f"Could not write config: {config_path}: {exc}", _build_fallback_data(
                client=options.client,
                scope=scope,
                workspace_root=workspace_root,
                config_path=config_path,
                write_enabled=options.write_enabled,
                error=str(exc),
            )

    mode = "write-enabled" if options.write_enabled else "read-only"
    if action == "created":
        message = f"Created {options.client} MCP config at {config_path}"
    elif action == "updated":
        message = f"Updated {options.client} MCP config at {config_path}"
    else:
        message = f"{options.client.capitalize()} MCP config already up to date at {config_path}"

    return 0, message, {
        "client": options.client,
        "scope": scope,
        "action": action,
        "config_path": str(config_path),
        "workspace": str(workspace_root),
        "mode": mode,
    }


def _run_mcp_uninstall_command(options: MCPUninstallOptions) -> Tuple[int, str, Dict[str, Any]]:
    """Remove the Ontos MCP entry for a managed client."""
    try:
        contract = get_client_contract(options.client)
    except KeyError:
        return 2, f"Unsupported MCP client: {options.client}", {}
    if not contract.managed:
        return 2, f"Unsupported MCP client: {options.client}", {}

    exit_code, scope, error_message = _resolve_scope(options.client, options.scope)
    if exit_code != 0 or scope is None:
        return exit_code, error_message, {}

    exit_code, workspace_root, error_message = _resolve_workspace_root(None)
    if exit_code != 0 and options.config_path is None:
        return exit_code, error_message, {}

    exit_code, config_path, error_message = _resolve_managed_config_path(
        client=options.client,
        scope=scope,
        workspace_root=workspace_root or Path.cwd().resolve(),
        config_path_override=options.config_path,
    )
    if exit_code != 0 or config_path is None:
        return exit_code, error_message, {}

    exit_code, error_message = _validate_managed_config_scope(
        config_path,
        scope,
        workspace_root or Path.cwd().resolve(),
    )
    if exit_code != 0:
        return exit_code, error_message, {}

    if not config_path.exists():
        return 0, f"No Ontos MCP entry found at {config_path}", {
            "client": options.client,
            "scope": scope,
            "action": "noop",
            "config_path": str(config_path),
        }

    try:
        existing = _load_managed_config(options.client, config_path)
    except (AntigravityConfigError, CursorConfigError, MCPConfigError) as exc:
        if workspace_root is None:
            exit_code, workspace_root, error_message = _resolve_workspace_root(None)
            if exit_code != 0 or workspace_root is None:
                return 2, str(exc), {"config_path": str(config_path), "error": str(exc)}
        return 2, str(exc), _build_fallback_data(
            client=options.client,
            scope=scope,
            workspace_root=workspace_root,
            config_path=config_path,
            write_enabled=False,
            error=str(exc),
        )

    updated_config, action = _remove_managed_entry(options.client, existing)
    if action != "noop" and updated_config is not None:
        try:
            _write_managed_config(options.client, config_path, updated_config)
        except OSError as exc:
            if workspace_root is None:
                exit_code, workspace_root, error_message = _resolve_workspace_root(None)
                if exit_code != 0 or workspace_root is None:
                    return 2, f"Could not write config: {config_path}: {exc}", {
                        "config_path": str(config_path),
                        "error": str(exc),
                    }
            return 2, f"Could not write config: {config_path}: {exc}", _build_fallback_data(
                client=options.client,
                scope=scope,
                workspace_root=workspace_root,
                config_path=config_path,
                write_enabled=False,
                error=str(exc),
            )

    message = (
        f"Removed Ontos MCP entry from {config_path}"
        if action == "removed"
        else f"No Ontos MCP entry found at {config_path}"
    )
    return 0, message, {
        "client": options.client,
        "scope": scope,
        "action": action,
        "config_path": str(config_path),
    }


def _run_mcp_print_config_command(options: MCPPrintConfigOptions) -> Tuple[int, str, Dict[str, Any]]:
    """Render the full manual config document without writing to disk."""
    try:
        contract = get_client_contract(options.client)
    except KeyError:
        return 2, f"Unsupported MCP client: {options.client}", {}

    exit_code, scope, error_message = _resolve_scope(options.client, options.scope)
    if exit_code != 0 or scope is None:
        return exit_code, error_message, {}

    exit_code, workspace_root, error_message = _resolve_workspace_root(options.workspace)
    if exit_code != 0 or workspace_root is None:
        return exit_code, error_message, {}

    exit_code, config_path, error_message = _resolve_print_config_path(
        client=options.client,
        scope=scope,
        workspace_root=workspace_root,
        config_path_override=options.config_path,
    )
    if exit_code != 0 or config_path is None:
        return exit_code, error_message, {}

    try:
        output_format, snippet = render_client_config_document(
            options.client,
            workspace_root=workspace_root,
            write_enabled=options.write_enabled,
        )
    except RuntimeError as exc:
        return 5, str(exc), {
            "client": options.client,
            "scope": scope,
            "config_path": str(config_path),
        }

    return 0, f"Generated {options.client} MCP config for {config_path}", {
        "client": options.client,
        "scope": scope,
        "config_path": str(config_path),
        "format": output_format,
        "snippet": snippet,
    }


def mcp_install_command(options: MCPInstallOptions) -> int:
    """Run `ontos mcp install` and return an exit code."""
    exit_code, _, _ = _run_mcp_install_command(options)
    return exit_code
