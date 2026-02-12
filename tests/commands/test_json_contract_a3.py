"""A3 JSON envelope conformance tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REQUIRED_KEYS = {
    "schema_version",
    "command",
    "status",
    "exit_code",
    "message",
    "data",
    "warnings",
    "error",
}


def _run_ontos(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    project_root = Path(__file__).resolve().parents[2]
    env["PYTHONPATH"] = str(project_root)
    return subprocess.run(
        [sys.executable, "-m", "ontos", *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )


def _init_project(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "doc.md").write_text(
        "---\nid: sample\ntype: atom\nstatus: active\n---\n",
        encoding="utf-8",
    )


def test_json_envelope_keys_for_multiple_commands(tmp_path: Path) -> None:
    _init_project(tmp_path)

    command_sets = [
        ("--json", "query", "--list-ids"),
        ("--json", "doctor"),
        ("--json", "export", "data"),
    ]

    for command in command_sets:
        result = _run_ontos(tmp_path, *command)
        assert result.stdout, f"missing stdout for command: {' '.join(command)}"
        payload = json.loads(result.stdout)
        assert REQUIRED_KEYS.issubset(payload.keys()), payload

