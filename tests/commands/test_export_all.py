"""Integration tests for `ontos export --all`."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


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


def test_export_all_generates_three_artifacts(tmp_path: Path) -> None:
    _init_project(tmp_path)
    result = _run_ontos(tmp_path, "export", "--all")

    assert result.returncode == 0
    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / ".cursorrules").exists()
    assert (tmp_path / "CLAUDE.md").exists()


def test_export_all_json_envelope_and_failures(tmp_path: Path) -> None:
    _init_project(tmp_path)
    (tmp_path / "AGENTS.md").write_text("existing", encoding="utf-8")

    result = _run_ontos(tmp_path, "--json", "export", "--all")
    assert result.returncode == 1

    payload = json.loads(result.stdout)
    assert payload["command"] == "export"
    assert payload["status"] == "error"
    assert payload["data"]["artifacts"]["agents_bundle"]["created"] is False
