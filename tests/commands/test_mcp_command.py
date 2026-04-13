from __future__ import annotations

import json
import os
import site
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
