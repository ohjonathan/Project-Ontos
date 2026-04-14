from __future__ import annotations

import json
from pathlib import Path

import pytest

from ontos.core.cursor_mcp import inspect_cursor_ontos_config


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_probe_script(path: Path, *, exit_code: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if exit_code == 0:
        content = """#!/usr/bin/env python3
import json
import sys

_ = sys.stdin.read()
print(json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "serverInfo": {
            "name": "ontos-test",
            "version": "0",
        }
    },
}))
"""
    else:
        content = f"""#!/usr/bin/env python3
import sys

sys.exit({exit_code})
"""
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _cursor_entry(command: str, workspace: Path, *, args: list[str] | None = None) -> dict:
    return {
        "mcpServers": {
            "ontos": {
                "command": command,
                "args": args
                if args is not None
                else ["serve", "--workspace", str(workspace.resolve()), "--read-only"],
            }
        }
    }


def test_inspect_cursor_ontos_config_skips_when_file_missing(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = inspect_cursor_ontos_config(scope="project", workspace_root=workspace)

    assert result.code == "not_present"
    assert result.ok is True
    assert result.file_present is False
    assert result.entry_present is False


def test_inspect_cursor_ontos_config_warns_on_malformed_json(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config_path = workspace / ".cursor" / "mcp.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("{ invalid json\n", encoding="utf-8")

    result = inspect_cursor_ontos_config(scope="project", workspace_root=workspace)

    assert result.code == "invalid_json"
    assert result.ok is False
    assert "invalid json" in result.message.lower()


@pytest.mark.parametrize(
    ("name", "payload", "expected_code", "expected_snippet"),
    [
        (
            "missing_command",
            {"mcpServers": {"ontos": {"args": ["serve", "--workspace", "/tmp/ws", "--read-only"]}}},
            "bad_command",
            "missing a valid command",
        ),
        (
            "non_string_command",
            {"mcpServers": {"ontos": {"command": 123, "args": ["serve", "--workspace", "/tmp/ws", "--read-only"]}}},
            "bad_command",
            "missing a valid command",
        ),
        (
            "missing_args",
            {"mcpServers": {"ontos": {"command": "/tmp/bin/cursor-ok"}}},
            "bad_command",
            "does not invoke 'serve'",
        ),
        (
            "non_list_args",
            {"mcpServers": {"ontos": {"command": "/tmp/bin/cursor-ok", "args": "serve"}}},
            "bad_command",
            "invalid args",
        ),
        (
            "bad_executable",
            {"mcpServers": {"ontos": {"command": "/definitely/not/a/command", "args": ["serve", "--workspace", "/tmp/ws"]}}},
            "bad_command",
            "not executable",
        ),
        (
            "missing_serve",
            {"mcpServers": {"ontos": {"command": "/tmp/bin/cursor-ok", "args": ["-m", "ontos", "--workspace", "/tmp/ws"]}}},
            "bad_command",
            "does not invoke 'serve'",
        ),
        (
            "missing_workspace",
            {"mcpServers": {"ontos": {"command": "/tmp/bin/cursor-ok", "args": ["serve"]}}},
            "bad_workspace",
            "missing --workspace",
        ),
        (
            "non_absolute_workspace",
            {"mcpServers": {"ontos": {"command": "/tmp/bin/cursor-ok", "args": ["serve", "--workspace", "relative/path"]}}},
            "bad_workspace",
            "must be an absolute path",
        ),
        (
            "missing_workspace_path",
            {"mcpServers": {"ontos": {"command": "/tmp/bin/cursor-ok", "args": ["serve", "--workspace", "/tmp/ws/missing"]}}},
            "bad_workspace",
            "does not exist",
        ),
        (
            "initialize_probe_failure",
            {"mcpServers": {"ontos": {"command": "/tmp/bin/cursor-fail", "args": ["serve", "--workspace", "/tmp/ws", "--read-only"]}}},
            "probe_failed",
            "failed a direct MCP initialize probe",
        ),
    ],
)
def test_inspect_cursor_ontos_config_reports_validation_failures(
    tmp_path: Path,
    name: str,
    payload: dict,
    expected_code: str,
    expected_snippet: str,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config_path = workspace / ".cursor" / "mcp.json"
    probe_script = tmp_path / "bin" / "cursor-ok"
    _write_probe_script(probe_script, exit_code=0)

    if name == "bad_executable":
        payload = _cursor_entry("/definitely/not/a/command", workspace, args=["serve", "--workspace", str(workspace.resolve())])
    elif name == "missing_command":
        payload = {"mcpServers": {"ontos": {"args": ["serve", "--workspace", str(workspace.resolve()), "--read-only"]}}}
    elif name == "non_string_command":
        payload = {"mcpServers": {"ontos": {"command": 123, "args": ["serve", "--workspace", str(workspace.resolve()), "--read-only"]}}}
    elif name == "missing_args":
        payload = {"mcpServers": {"ontos": {"command": str(probe_script.resolve())}}}
    elif name == "non_list_args":
        payload = {"mcpServers": {"ontos": {"command": str(probe_script.resolve()), "args": "serve"}}}
    elif name == "missing_serve":
        payload = {"mcpServers": {"ontos": {"command": str(probe_script.resolve()), "args": ["-m", "ontos", "--workspace", str(workspace.resolve())]}}}
    elif name == "missing_workspace":
        payload = {"mcpServers": {"ontos": {"command": str(probe_script.resolve()), "args": ["serve"]}}}
    elif name == "non_absolute_workspace":
        payload = {"mcpServers": {"ontos": {"command": str(probe_script.resolve()), "args": ["serve", "--workspace", "relative/path"]}}}
    elif name == "missing_workspace_path":
        payload = {"mcpServers": {"ontos": {"command": str(probe_script.resolve()), "args": ["serve", "--workspace", str(workspace / "missing")]}}}
    elif name == "initialize_probe_failure":
        probe_script = tmp_path / "bin" / "cursor-fail"
        _write_probe_script(probe_script, exit_code=3)
        payload = {"mcpServers": {"ontos": {"command": str(probe_script), "args": ["serve", "--workspace", str(workspace.resolve()), "--read-only"]}}}

    _write_json(config_path, payload)

    result = inspect_cursor_ontos_config(scope="project", workspace_root=workspace)

    assert result.code == expected_code
    assert result.ok is False
    assert expected_snippet in result.message or expected_snippet in (result.details or "")


def test_inspect_cursor_ontos_config_returns_success_for_valid_entry(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    probe_script = tmp_path / "bin" / "cursor-ok"
    _write_probe_script(probe_script, exit_code=0)
    config_path = workspace / ".cursor" / "mcp.json"
    _write_json(
        config_path,
        _cursor_entry(
            str(probe_script),
            workspace,
            args=["serve", "--workspace", str(workspace.resolve()), "--read-only"],
        ),
    )

    result = inspect_cursor_ontos_config(scope="project", workspace_root=workspace)

    assert result.code == "ok"
    assert result.ok is True
    assert result.mode == "read-only"
    assert result.workspace == workspace.resolve()
    assert result.entry_present is True
    assert result.file_present is True
