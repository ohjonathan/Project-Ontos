from __future__ import annotations

import json
import os
import site
import subprocess
import sys
from pathlib import Path

from ontos.core.cursor_mcp import inspect_cursor_ontos_config


INITIALIZE_RESPONSE = {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {"serverInfo": {"name": "ontos-test", "version": "0"}},
}


def _init_workspace(root: Path) -> None:
    (root / ".ontos.toml").write_text("[ontos]\nversion = '4.7'\n", encoding="utf-8")
    docs = root / "docs"
    docs.mkdir()
    (docs / "doc.md").write_text(
        "---\nid: sample\ntype: atom\nstatus: active\n---\n",
        encoding="utf-8",
    )
    (root / "Ontos_Context_Map.md").write_text(
        "---\nid: ontos_context_map\ntype: reference\nstatus: active\n---\n\n# Context Map\n",
        encoding="utf-8",
    )


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _pythonpath_env(home: Path) -> dict[str, str]:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    entries = [str(repo_root)]
    for entry in [site.getusersitepackages(), *site.getsitepackages()]:
        if entry and entry not in entries:
            entries.append(entry)
    if env.get("PYTHONPATH"):
        entries.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(entries)
    env["HOME"] = str(home)
    return env


def test_doctor_does_not_execute_project_cursor_command_from_repo_config(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    _init_workspace(workspace)

    marker = tmp_path / "payload-ran.txt"
    payload = f"from pathlib import Path; Path({str(marker)!r}).write_text('ran', encoding='utf-8')"
    _write_json(
        workspace / ".cursor" / "mcp.json",
        {
            "mcpServers": {
                "ontos": {
                    "command": "python3",
                    "args": ["-c", payload, "serve", "--workspace", str(workspace.resolve())],
                }
            }
        },
    )

    result = subprocess.run(
        [sys.executable, "-m", "ontos", "--json", "doctor"],
        cwd=workspace,
        capture_output=True,
        text=True,
        env=_pythonpath_env(home),
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert not marker.exists(), "project-scoped Cursor MCP probe executed repo-sourced payload"
    envelope = json.loads(result.stdout)
    cursor_check = next(check for check in envelope["data"]["checks"] if check["name"] == "cursor_mcp")
    assert cursor_check["status"] == "warning"
    assert "probe skipped" in cursor_check.get("details", "").lower()


def test_managed_project_cursor_launcher_still_runs_initialize_probe(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_workspace(workspace)
    marker = tmp_path / "managed-probe-ran.txt"
    probe_script = tmp_path / "bin" / "ontos-probe"
    probe_script.parent.mkdir(parents=True)
    probe_script.write_text(
        f"""#!/usr/bin/env python3
import json
import sys
from pathlib import Path

_ = sys.stdin.read()
Path({str(marker)!r}).write_text("ran", encoding="utf-8")
print(json.dumps({INITIALIZE_RESPONSE!r}))
""",
        encoding="utf-8",
    )
    probe_script.chmod(0o755)

    from ontos.core import mcp_shared

    monkeypatch.setattr(mcp_shared, "resolve_ontos_launcher", lambda: (str(probe_script.resolve()), []))
    _write_json(
        workspace / ".cursor" / "mcp.json",
        {
            "mcpServers": {
                "ontos": {
                    "command": str(probe_script.resolve()),
                    "args": ["serve", "--workspace", str(workspace.resolve()), "--read-only"],
                }
            }
        },
    )

    result = inspect_cursor_ontos_config(
        scope="project",
        workspace_root=workspace,
        allow_unmanaged_probe=False,
    )

    assert result.code == "ok"
    assert result.probe is not None
    assert result.probe.ok is True
    assert marker.read_text(encoding="utf-8") == "ran"


def _managed_launcher_workspace(tmp_path: Path, monkeypatch) -> tuple[Path, Path, Path]:
    """Workspace whose trusted launcher records that it was executed."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_workspace(workspace)
    marker = tmp_path / "smuggled-subcommand-ran.txt"
    launcher = tmp_path / "bin" / "ontos-probe"
    launcher.parent.mkdir(parents=True)
    launcher.write_text(
        f"""#!/usr/bin/env python3
import sys
from pathlib import Path

_ = sys.stdin.read()
Path({str(marker)!r}).write_text("ran", encoding="utf-8")
""",
        encoding="utf-8",
    )
    launcher.chmod(0o755)

    from ontos.core import mcp_shared

    monkeypatch.setattr(mcp_shared, "resolve_ontos_launcher", lambda: (str(launcher.resolve()), []))
    return workspace, marker, launcher


def test_trusted_launcher_cannot_smuggle_a_subcommand_past_the_probe_gate(tmp_path: Path, monkeypatch) -> None:
    """A repo config may name Ontos's own launcher, then hide `ontos scaffold --apply`
    behind a `--` separator while still satisfying the `serve` / `--workspace` preflight."""
    workspace, marker, launcher = _managed_launcher_workspace(tmp_path, monkeypatch)
    _write_json(
        workspace / ".cursor" / "mcp.json",
        {
            "mcpServers": {
                "ontos": {
                    "command": str(launcher.resolve()),
                    "args": [
                        "scaffold",
                        "--apply",
                        "--",
                        "serve",
                        "--workspace",
                        str(workspace.resolve()),
                    ],
                }
            }
        },
    )

    result = inspect_cursor_ontos_config(
        scope="project",
        workspace_root=workspace,
        allow_unmanaged_probe=False,
    )

    assert result.code == "unmanaged_probe_skipped"
    assert result.probe is None
    assert not marker.exists(), "trusted launcher executed an attacker-chosen subcommand"


def test_trusted_launcher_cannot_smuggle_a_duplicate_workspace_arg(tmp_path: Path, monkeypatch) -> None:
    """`extract_workspace_arg` returns the first `--workspace`, so a second one must not ride along."""
    workspace, marker, launcher = _managed_launcher_workspace(tmp_path, monkeypatch)
    _write_json(
        workspace / ".cursor" / "mcp.json",
        {
            "mcpServers": {
                "ontos": {
                    "command": str(launcher.resolve()),
                    "args": [
                        "serve",
                        "--workspace",
                        str(workspace.resolve()),
                        "--workspace",
                        str(tmp_path.resolve()),
                    ],
                }
            }
        },
    )

    result = inspect_cursor_ontos_config(
        scope="project",
        workspace_root=workspace,
        allow_unmanaged_probe=False,
    )

    assert result.code == "unmanaged_probe_skipped"
    assert result.probe is None
    assert not marker.exists(), "trusted launcher executed a duplicated --workspace argv"


def test_probe_gate_defaults_to_safe_without_explicit_opt_out(tmp_path: Path, monkeypatch) -> None:
    """Callers that forget `allow_unmanaged_probe=False` must still be protected."""
    workspace, marker, launcher = _managed_launcher_workspace(tmp_path, monkeypatch)
    _write_json(
        workspace / ".cursor" / "mcp.json",
        {
            "mcpServers": {
                "ontos": {
                    "command": str(launcher.resolve()),
                    "args": ["scaffold", "--apply", "--", "serve", "--workspace", str(workspace.resolve())],
                }
            }
        },
    )

    result = inspect_cursor_ontos_config(scope="project", workspace_root=workspace)

    assert result.code == "unmanaged_probe_skipped"
    assert not marker.exists(), "default-constructed inspection executed a repo-supplied subcommand"
