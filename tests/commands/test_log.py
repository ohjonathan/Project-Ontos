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
from ontos.io.yaml import parse_frontmatter_content


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

    def test_uses_configured_logs_directory(self, tmp_path):
        _init_git_project(tmp_path)
        (tmp_path / ".ontos.toml").write_text(
            "[ontos]\nversion = '3.0'\n[paths]\nlogs_dir = 'var/audit-logs'\n",
            encoding="utf-8",
        )
        _, path = create_session_log(
            tmp_path,
            EndSessionOptions(topic="configured"),
            {"branch": "main"},
        )
        assert path.parent == (tmp_path / "var" / "audit-logs")

    def test_preserves_legacy_logs_dir_precedence(self, tmp_path, monkeypatch):
        _init_git_project(tmp_path)
        (tmp_path / "ontos_config.py").write_text(
            "LOGS_DIR = 'legacy/session-logs'\n",
            encoding="utf-8",
        )

        _, path = create_session_log(
            tmp_path,
            EndSessionOptions(topic="legacy"),
            {"branch": "main"},
        )

        assert path.parent == tmp_path / "legacy" / "session-logs"

    def test_frontmatter_round_trips_adversarial_values(self, tmp_path):
        _init_git_project(tmp_path)
        options = EndSessionOptions(
            event_type="fix: quoted # value",
            topic="safe yaml",
            source="agent, local",
            branch='feature/"quoted"',
            concepts=["alpha, beta", "#hash", "2026-07-10"],
            impacts=["depends: value"],
        )
        content, _ = create_session_log(tmp_path, options, {"branch": "ignored"})
        frontmatter, _ = parse_frontmatter_content(content)
        assert frontmatter["event_type"] == options.event_type
        assert frontmatter["source"] == options.source
        assert frontmatter["branch"] == options.branch
        assert frontmatter["concepts"] == options.concepts
        assert frontmatter["impacts"] == options.impacts


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
        marker = tmp_path / ".ontos" / "session_archived"
        assert marker.is_file()
        assert Path(marker.read_text(encoding="utf-8")).is_file()

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

    def test_not_in_git_repo_returns_usage_error(
        self, tmp_path, monkeypatch, capsys
    ):
        """A missing repository is invalid command context, not findings."""
        monkeypatch.chdir(tmp_path)
        # No .git dir — should fail
        options = LogOptions(auto=True, quiet=True, json_output=True)
        result = log_command(options)
        assert result == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["exit_code"] == 2
        assert payload["status"] == "error"
        assert payload["error"]["code"] == "E_WORKSPACE_NOT_FOUND"
        assert payload["result"]["exit_category"] == "usage"

    def test_collision_is_refused_without_overwrite(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        _init_git_project(tmp_path)
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=tmp_path,
            capture_output=True,
        )
        monkeypatch.chdir(tmp_path)
        options = LogOptions(auto=True, quiet=True, title="same session")
        assert log_command(options) == 0
        path = next((tmp_path / "docs" / "logs").glob("*_same-session.md"))
        original = path.read_bytes()
        options.json_output = True
        assert log_command(options) == 2
        assert path.read_bytes() == original
        payload = json.loads(capsys.readouterr().out)
        assert payload["schema_version"] == "4.0"
        assert payload["exit_code"] == 2
        assert payload["result"]["status"] == "error"
        assert payload["result"]["exit_category"] == "usage"
        assert payload["error"]["code"] == "E_FILE_EXISTS"

    def test_write_failure_returns_internal_error(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        _init_git_project(tmp_path)
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=tmp_path,
            capture_output=True,
        )
        monkeypatch.chdir(tmp_path)

        def fail_write(*_args, **_kwargs):
            raise OSError("disk unavailable")

        monkeypatch.setattr("ontos.commands.log._write_log_exclusively", fail_write)

        result = log_command(
            LogOptions(auto=True, quiet=True, json_output=True, title="write failure")
        )

        assert result == 5
        payload = json.loads(capsys.readouterr().out)
        assert payload["exit_code"] == 5
        assert payload["status"] == "error"
        assert payload["result"]["exit_category"] == "internal"

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
    def test_default_logs_dir_symlink_is_rejected_before_resolution(
        self,
        tmp_path,
    ):
        _init_git_project(tmp_path)
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=tmp_path,
            capture_output=True,
        )
        (tmp_path / "docs" / "logs").rmdir()
        (tmp_path / "docs").rmdir()
        outside = tmp_path.parent / f"{tmp_path.name}-outside"
        outside_logs = outside / "logs"
        outside_logs.mkdir(parents=True)
        sentinel = outside / "sentinel.txt"
        sentinel.write_text("do not change", encoding="utf-8")
        (tmp_path / "docs").symlink_to(outside, target_is_directory=True)

        result = _run_ontos(tmp_path, "log", "--auto")

        assert result.returncode == 2
        assert "Configure LOGS_DIR or [paths].logs_dir" in result.stderr
        assert sentinel.read_text(encoding="utf-8") == "do not change"
        assert list(outside_logs.glob("*.md")) == []

    def test_outside_configured_logs_dir_has_actionable_error(self, tmp_path):
        _init_git_project(tmp_path)
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        (tmp_path / ".ontos.toml").write_text(
            "[ontos]\nversion = '3.0'\n[paths]\nlogs_dir = '../outside'\n",
            encoding="utf-8",
        )
        result = _run_ontos(tmp_path, "log", "--auto")

        assert result.returncode == 2
        assert "Refusing unsafe paths.logs_dir configuration" in result.stderr
        assert "inside the workspace" in result.stderr

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
    def test_archive_marker_symlink_preserves_legacy_success_contract(
        self,
        tmp_path,
    ):
        _init_git_project(tmp_path)
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        outside = tmp_path.parent / f"{tmp_path.name}-marker-outside"
        outside.mkdir()
        sentinel = outside / "session_archived"
        sentinel.write_text("do not change", encoding="utf-8")
        (tmp_path / ".ontos").symlink_to(outside, target_is_directory=True)

        result = _run_ontos(tmp_path, "log", "--auto", "--json")

        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["schema_version"] == "4.0"
        assert payload["exit_code"] == 0
        assert payload["result"]["status"] == "clean"
        assert Path(payload["data"]["path"]).is_file()
        assert sentinel.read_text(encoding="utf-8") == "do not change"
