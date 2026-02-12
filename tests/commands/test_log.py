"""Tests for the log command: creation, flags, JSON output, and return types."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ontos.commands.log import (
    EndSessionOptions,
    LogOptions,
    create_session_log,
    log_command,
)


def _init_git_project(tmp_path: Path) -> None:
    """Create a minimal git+ontos project for log tests."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".ontos.toml").write_text(
        "[ontos]\nversion = '3.0'\n", encoding="utf-8"
    )
    docs_logs = tmp_path / "docs" / "logs"
    docs_logs.mkdir(parents=True)


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


# ---------------------------------------------------------------------------
# create_session_log (unit)
# ---------------------------------------------------------------------------

class TestCreateSessionLog:
    def test_basic_creation(self, tmp_path):
        """create_session_log returns content and path."""
        _init_git_project(tmp_path)
        options = EndSessionOptions(event_type="chore", topic="test session")
        git_info = {"branch": "main", "commits": [], "changed_files": []}
        content, path = create_session_log(tmp_path, options, git_info)
        assert "id:" in content
        assert "type: log" in content
        assert path.suffix == ".md"

    def test_topic_appears_in_filename(self, tmp_path):
        _init_git_project(tmp_path)
        options = EndSessionOptions(topic="my-special-topic")
        git_info = {"branch": "main", "commits": [], "changed_files": []}
        _, path = create_session_log(tmp_path, options, git_info)
        assert "my-special-topic" in path.name

    def test_event_type_in_frontmatter(self, tmp_path):
        _init_git_project(tmp_path)
        options = EndSessionOptions(event_type="feature", topic="feat")
        git_info = {"branch": "main", "commits": [], "changed_files": []}
        content, _ = create_session_log(tmp_path, options, git_info)
        assert "event_type: feature" in content


# ---------------------------------------------------------------------------
# log_command (integration via subprocess)
# ---------------------------------------------------------------------------

class TestLogCommandCLI:
    def test_auto_flag_creates_log(self, tmp_path):
        """--auto flag skips prompts and creates a log."""
        _init_git_project(tmp_path)
        # Initialize a real git repo so git commands work
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=tmp_path,
            capture_output=True,
        )
        result = _run_ontos(tmp_path, "log", "--auto")
        assert result.returncode == 0

    def test_json_output_has_envelope_keys(self, tmp_path):
        """--json output conforms to v3.3 envelope schema."""
        _init_git_project(tmp_path)
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=tmp_path,
            capture_output=True,
        )
        result = _run_ontos(tmp_path, "--json", "log", "--auto")
        assert result.stdout, "expected JSON output on stdout"
        payload = json.loads(result.stdout)
        required = {
            "schema_version", "command", "status", "exit_code",
            "message", "data", "warnings", "error",
        }
        assert required.issubset(payload.keys()), f"Missing keys: {required - set(payload.keys())}"

    def test_return_type_is_int(self, tmp_path, monkeypatch):
        """log_command should return an int exit code."""
        _init_git_project(tmp_path)
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=tmp_path,
            capture_output=True,
        )
        monkeypatch.chdir(tmp_path)
        options = LogOptions(auto=True, quiet=True)
        result = log_command(options)
        assert isinstance(result, int)
        assert result == 0

    def test_not_in_git_repo_returns_error(self, tmp_path, monkeypatch):
        """log_command returns 1 when not in a git repository."""
        monkeypatch.chdir(tmp_path)
        # No .git dir — should fail
        options = LogOptions(auto=True, quiet=True)
        result = log_command(options)
        assert result == 1
