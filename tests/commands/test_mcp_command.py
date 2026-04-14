from __future__ import annotations

import json
import os
import site
import subprocess
import sys
from pathlib import Path

import pytest

from ontos.commands.mcp import MCPInstallOptions, _run_mcp_install_command
from ontos.core.antigravity_mcp import (
    build_antigravity_ontos_entry,
    upsert_antigravity_ontos_entry,
    write_antigravity_config,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.9/3.10 fallback
    import tomli as tomllib  # type: ignore


def _run_ontos(
    cwd: Path,
    *args: str,
    home: Path,
    path_override: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    pythonpath_entries = [str(PROJECT_ROOT)]
    for entry in [site.getusersitepackages(), *site.getsitepackages()]:
        if entry and entry not in pythonpath_entries:
            pythonpath_entries.append(entry)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    env["HOME"] = str(home)
    if path_override is not None:
        env["PATH"] = path_override
    return subprocess.run(
        [sys.executable, "-m", "ontos", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def _init_workspace(root: Path) -> None:
    (root / ".ontos.toml").write_text("[ontos]\nversion = '4.1'\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "doc.md").write_text(
        "---\nid: sample\ntype: atom\nstatus: active\n---\n",
        encoding="utf-8",
    )


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _python_launcher_entry(workspace: Path, *, write_enabled: bool = False) -> dict:
    args = ["-m", "ontos", "serve", "--workspace", str(workspace.resolve())]
    if not write_enabled:
        args.append("--read-only")
    return {"command": str(Path(sys.executable).resolve()), "args": args}


def test_mcp_install_creates_antigravity_config_with_read_only_default(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    result = _run_ontos(
        workspace,
        "mcp",
        "install",
        "--client",
        "antigravity",
        home=home,
    )

    assert result.returncode == 0, result.stderr
    config_path = home / ".gemini" / "antigravity" / "mcp_config.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))

    entry = payload["mcpServers"]["ontos"]
    assert Path(entry["command"]).is_absolute()
    assert entry["args"][-1] == "--read-only"
    assert "--workspace" in entry["args"]
    workspace_index = entry["args"].index("--workspace")
    assert entry["args"][workspace_index + 1] == str(workspace.resolve())


def test_mcp_install_merges_existing_servers(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    config_path = home / ".gemini" / "antigravity" / "mcp_config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "github-mcp-server": {
                        "command": "docker",
                        "args": ["run", "-i", "--rm", "ghcr.io/github/github-mcp-server"],
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_ontos(
        workspace,
        "mcp",
        "install",
        "--client",
        "antigravity",
        home=home,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert "github-mcp-server" in payload["mcpServers"]
    assert "ontos" in payload["mcpServers"]


def test_mcp_install_falls_back_to_python_module_when_ontos_not_on_path(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    result = _run_ontos(
        workspace,
        "mcp",
        "install",
        "--client",
        "antigravity",
        home=home,
        path_override="/usr/bin:/bin",
    )

    assert result.returncode == 0, result.stderr
    config_path = home / ".gemini" / "antigravity" / "mcp_config.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    entry = payload["mcpServers"]["ontos"]
    assert entry["command"] == str(Path(sys.executable).resolve())
    assert entry["args"][:3] == ["-m", "ontos", "serve"]


def test_mcp_install_rejects_invalid_existing_json_without_rewriting(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    config_path = home / ".gemini" / "antigravity" / "mcp_config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("{ invalid json\n", encoding="utf-8")
    original = config_path.read_text(encoding="utf-8")

    result = _run_ontos(
        workspace,
        "mcp",
        "install",
        "--client",
        "antigravity",
        home=home,
    )

    assert result.returncode == 2
    assert "invalid json" in result.stdout.lower() or "invalid json" in result.stderr.lower()
    assert config_path.read_text(encoding="utf-8") == original


def test_mcp_install_json_envelope_reports_created_config(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    result = _run_ontos(
        workspace,
        "--json",
        "mcp",
        "install",
        "--client",
        "antigravity",
        home=home,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["command"] == "mcp-install"
    assert payload["data"]["client"] == "antigravity"
    assert payload["data"]["mode"] == "read-only"


def test_mcp_install_write_enabled_omits_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    result = _run_ontos(
        workspace,
        "--json",
        "mcp",
        "install",
        "--client",
        "antigravity",
        "--write-enabled",
        home=home,
    )

    assert result.returncode == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["mode"] == "write-enabled"

    config_path = home / ".gemini" / "antigravity" / "mcp_config.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    entry = payload["mcpServers"]["ontos"]
    assert "--read-only" not in entry["args"]


def test_mcp_install_creates_cursor_project_config_with_read_only_default(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    result = _run_ontos(
        workspace,
        "mcp",
        "install",
        "--client",
        "cursor",
        "--scope",
        "project",
        home=home,
    )

    assert result.returncode == 0, result.stderr
    config_path = workspace / ".cursor" / "mcp.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    entry = payload["mcpServers"]["ontos"]
    assert Path(entry["command"]).is_absolute()
    assert entry["args"][-1] == "--read-only"
    assert "serve" in entry["args"]
    workspace_index = entry["args"].index("--workspace")
    assert entry["args"][workspace_index + 1] == str(workspace.resolve())


def test_mcp_install_creates_cursor_user_config_with_read_only_default(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    result = _run_ontos(
        workspace,
        "mcp",
        "install",
        "--client",
        "cursor",
        "--scope",
        "user",
        home=home,
    )

    assert result.returncode == 0, result.stderr
    config_path = home / ".cursor" / "mcp.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    entry = payload["mcpServers"]["ontos"]
    assert Path(entry["command"]).is_absolute()
    assert entry["args"][-1] == "--read-only"
    assert "serve" in entry["args"]
    workspace_index = entry["args"].index("--workspace")
    assert entry["args"][workspace_index + 1] == str(workspace.resolve())


def test_mcp_install_cursor_merges_existing_servers(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    config_path = workspace / ".cursor" / "mcp.json"
    _write_json(
        config_path,
        {
            "mcpServers": {
                "github-mcp-server": {
                    "command": "docker",
                    "args": ["run", "-i", "--rm", "ghcr.io/github/github-mcp-server"],
                }
            }
        },
    )

    result = _run_ontos(
        workspace,
        "mcp",
        "install",
        "--client",
        "cursor",
        "--scope",
        "project",
        home=home,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert "github-mcp-server" in payload["mcpServers"]
    assert "ontos" in payload["mcpServers"]


def test_mcp_install_cursor_identical_rerun_returns_noop(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    config_path = workspace / ".cursor" / "mcp.json"
    _write_json(
        config_path,
        {
            "mcpServers": {
                "ontos": {
                    **_python_launcher_entry(workspace),
                    "env": {"PERSIST": "yes"},
                }
            }
        },
    )

    before = config_path.read_text(encoding="utf-8")
    result = _run_ontos(
        workspace,
        "--json",
        "mcp",
        "install",
        "--client",
        "cursor",
        "--scope",
        "project",
        home=home,
        path_override="/usr/bin:/bin",
    )

    assert result.returncode == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["action"] == "noop"
    assert config_path.read_text(encoding="utf-8") == before


def test_mcp_install_cursor_updates_user_added_fields_when_entry_changes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    config_path = workspace / ".cursor" / "mcp.json"
    _write_json(
        config_path,
        {
            "mcpServers": {
                "ontos": {
                    "command": str(Path(sys.executable).resolve()),
                    "args": ["-m", "ontos", "serve", "--workspace", str(workspace.resolve())],
                    "env": {"PERSIST": "yes"},
                }
            }
        },
    )

    result = _run_ontos(
        workspace,
        "--json",
        "mcp",
        "install",
        "--client",
        "cursor",
        "--scope",
        "project",
        home=home,
        path_override="/usr/bin:/bin",
    )

    assert result.returncode == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["action"] == "updated"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    entry = payload["mcpServers"]["ontos"]
    assert "env" not in entry
    assert entry["args"][-1] == "--read-only"


def test_mcp_install_cursor_write_enabled_omits_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    result = _run_ontos(
        workspace,
        "--json",
        "mcp",
        "install",
        "--client",
        "cursor",
        "--scope",
        "project",
        "--write-enabled",
        home=home,
    )

    assert result.returncode == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["mode"] == "write-enabled"

    config_path = workspace / ".cursor" / "mcp.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    entry = payload["mcpServers"]["ontos"]
    assert "--read-only" not in entry["args"]


@pytest.mark.parametrize(
    ("client", "config_path"),
    [
        ("cursor", ".cursor/mcp.toml"),
        ("antigravity", ".gemini/antigravity/mcp_config.toml"),
    ],
)
def test_mcp_install_rejects_invalid_config_path_extension(
    tmp_path: Path,
    client: str,
    config_path: str,
) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    result = _run_ontos(
        workspace,
        "mcp",
        "install",
        "--client",
        client,
        "--config-path",
        str((home / config_path).resolve()),
        home=home,
    )

    assert result.returncode == 2
    combined = (result.stdout + result.stderr).lower()
    assert "config-path" in combined or "extension" in combined or "toml" in combined or "json" in combined


def test_mcp_uninstall_removes_only_ontos_entry(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    config_path = workspace / ".cursor" / "mcp.json"
    _write_json(
        config_path,
        {
            "mcpServers": {
                "github-mcp-server": {
                    "command": "docker",
                    "args": ["run", "-i", "--rm", "ghcr.io/github/github-mcp-server"],
                },
                "ontos": _python_launcher_entry(workspace),
            }
        },
    )

    result = _run_ontos(
        workspace,
        "--json",
        "mcp",
        "uninstall",
        "--client",
        "cursor",
        "--scope",
        "project",
        home=home,
    )

    assert result.returncode == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["action"] == "removed"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert "ontos" not in payload["mcpServers"]
    assert "github-mcp-server" in payload["mcpServers"]


def test_mcp_uninstall_noop_when_entry_missing(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    result = _run_ontos(
        workspace,
        "--json",
        "mcp",
        "uninstall",
        "--client",
        "cursor",
        "--scope",
        "project",
        home=home,
    )

    assert result.returncode == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["action"] == "noop"


@pytest.mark.parametrize(
    ("client", "expected_root", "expected_snippet_token"),
    [
        ("antigravity", "mcpServers", '"mcpServers"'),
        ("cursor", "mcpServers", '"mcpServers"'),
        ("claude-code", "mcpServers", '"mcpServers"'),
        ("vscode", "servers", '"servers"'),
    ],
)
def test_mcp_print_config_json_clients_emit_full_document(
    tmp_path: Path,
    client: str,
    expected_root: str,
    expected_snippet_token: str,
) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    result = _run_ontos(
        workspace,
        "--json",
        "mcp",
        "print-config",
        "--client",
        client,
        home=home,
    )

    assert result.returncode == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["client"] == client
    assert envelope["data"]["config_path"]
    assert expected_snippet_token in envelope["data"]["snippet"]

    if client == "vscode":
        snippet = envelope["data"]["snippet"]
        payload = json.loads(snippet)
    else:
        payload = json.loads(envelope["data"]["snippet"])

    assert expected_root in payload
    assert "ontos" in payload[expected_root]


def test_mcp_print_config_codex_outputs_complete_toml_document(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    result = _run_ontos(
        workspace,
        "--json",
        "mcp",
        "print-config",
        "--client",
        "codex",
        home=home,
    )

    assert result.returncode == 0, result.stderr
    envelope = json.loads(result.stdout)
    snippet = envelope["data"]["snippet"]
    parsed = tomllib.loads(snippet)

    assert envelope["data"]["format"] == "toml"
    assert "mcp_servers" in parsed
    assert "ontos" in parsed["mcp_servers"]
    assert "[mcp_servers.ontos]" in snippet


def test_mcp_print_config_plain_writes_document_to_stdout_and_hint_to_stderr(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    result = _run_ontos(
        workspace,
        "mcp",
        "print-config",
        "--client",
        "codex",
        home=home,
    )

    assert result.returncode == 0, result.stderr
    assert "[mcp_servers.ontos]" in result.stdout
    assert "mcp_config" in result.stderr.lower() or "config" in result.stderr.lower()
    assert result.stderr.strip()


def test_mcp_install_antigravity_identical_rerun_returns_noop(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    config_path = home / ".gemini" / "antigravity" / "mcp_config.json"
    _write_json(
        config_path,
        {
            "mcpServers": {
                "ontos": {
                    **_python_launcher_entry(workspace),
                    "env": {"PERSIST": "yes"},
                }
            }
        },
    )

    before = config_path.read_text(encoding="utf-8")
    result = _run_ontos(
        workspace,
        "--json",
        "mcp",
        "install",
        "--client",
        "antigravity",
        home=home,
        path_override="/usr/bin:/bin",
    )

    assert result.returncode == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["action"] == "noop"
    assert config_path.read_text(encoding="utf-8") == before


def test_antigravity_install_golden_snapshot(monkeypatch, tmp_path: Path) -> None:
    snapshot_path = Path(__file__).resolve().parents[1] / "fixtures" / "mcp" / "antigravity_install_golden.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    monkeypatch.setattr(
        "ontos.core.mcp_shared.resolve_ontos_launcher",
        lambda: ("/opt/ontos/bin/ontos", []),
    )

    entry = build_antigravity_ontos_entry(Path("/workspace/project"))
    entry["command"] = "<ontos-command>"
    entry["args"][2] = "<workspace-root>"

    payload, action = upsert_antigravity_ontos_entry(None, entry)
    assert action == "created"
    assert payload["mcpServers"]["ontos"] == snapshot

    config_path = tmp_path / "mcp_config.json"
    write_antigravity_config(config_path, payload)
    expected_bytes = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    assert config_path.read_bytes() == expected_bytes
    assert json.loads(config_path.read_text(encoding="utf-8")) == payload


def test_mcp_install_unwritable_config_dir(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)
    monkeypatch.chdir(workspace)
    monkeypatch.setenv("HOME", str(home))

    def _raise_permission_error(path: Path, data: dict) -> None:
        raise PermissionError("Permission denied")

    monkeypatch.setattr("ontos.commands.mcp.write_antigravity_config", _raise_permission_error)

    exit_code, message, data = _run_mcp_install_command(MCPInstallOptions(client="antigravity"))

    assert exit_code == 2
    assert message.startswith("Could not write config:")
    assert str(home / ".gemini" / "antigravity" / "mcp_config.json") in message
    assert data["config_path"] == str(home / ".gemini" / "antigravity" / "mcp_config.json")
    assert data["error"] == "Permission denied"
    assert "fallback_snippet" in data
    assert data["fallback_snippet"]
