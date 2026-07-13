"""Tests for hook dispatcher command (Phase 4)."""

import json
from unittest.mock import patch, MagicMock

import pytest

from ontos.commands.hook import (
    HookOptions,
    hook_command,
    run_pre_push_hook,
    run_pre_commit_hook,
)
from ontos.cli import main


class TestHookOptions:
    """Tests for HookOptions dataclass."""

    def test_creates_with_hook_type(self):
        options = HookOptions(hook_type="pre-push")
        assert options.hook_type == "pre-push"
        assert options.args == []

    def test_creates_with_args(self):
        options = HookOptions(hook_type="pre-commit", args=["--verbose"])
        assert options.args == ["--verbose"]


class TestHookCommand:
    """Tests for hook_command dispatcher."""

    def test_dispatches_pre_push(self):
        with patch("ontos.commands.hook.run_pre_push_hook") as mock:
            mock.return_value = 0
            options = HookOptions(hook_type="pre-push", args=["arg1"])

            result = hook_command(options)

            mock.assert_called_once_with(["arg1"])
            assert result == 0

    def test_dispatches_pre_commit(self):
        with patch("ontos.commands.hook.run_pre_commit_hook") as mock:
            mock.return_value = 0
            options = HookOptions(hook_type="pre-commit")

            result = hook_command(options)

            mock.assert_called_once_with([])
            assert result == 0

    def test_returns_0_for_unknown_hook(self, capsys):
        """Unknown hooks should not block git operations."""
        options = HookOptions(hook_type="unknown-hook")

        result = hook_command(options)

        assert result == 0
        captured = capsys.readouterr()
        assert "Unknown hook type" in captured.err


class TestRunPrePushHook:
    """Tests for run_pre_push_hook."""

    def test_returns_0_when_disabled(self):
        """Should return 0 when hook is disabled in config."""
        mock_config = MagicMock()
        mock_config.hooks.pre_push = False

        with patch("ontos.io.config.load_project_config") as mock_load:
            mock_load.return_value = mock_config

            result = run_pre_push_hook([])

            assert result == 0

    def test_returns_0_on_error(self):
        """Should return 0 (allow) when hook has errors."""
        with patch("ontos.io.config.load_project_config") as mock_load:
            mock_load.side_effect = Exception("Config error")

            result = run_pre_push_hook([])

            assert result == 0


class TestRunPreCommitHook:
    """Tests for run_pre_commit_hook."""

    def test_always_returns_0(self):
        """Pre-commit hook should never block."""
        mock_config = MagicMock()
        mock_config.hooks.pre_commit = True

        with patch("ontos.io.config.load_project_config") as mock_load:
            mock_load.return_value = mock_config

            result = run_pre_commit_hook([])

            assert result == 0

    def test_returns_0_on_error(self):
        """Should return 0 when hook has errors."""
        with patch("ontos.io.config.load_project_config") as mock_load:
            mock_load.side_effect = Exception("Error")

            result = run_pre_commit_hook([])

            assert result == 0


class TestHookJsonContract:
    @staticmethod
    def _payload(capsys):
        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out.count("\n") == 1
        payload = json.loads(captured.out)
        assert payload["schema_version"] == "4.0"
        assert payload["command"] == "hook"
        assert payload["result"]["kind"] == "diagnostic"
        return payload

    def test_clean_pre_commit_is_one_envelope(self, monkeypatch, capsys):
        config = MagicMock()
        config.hooks.pre_commit = True
        monkeypatch.setattr("ontos.io.config.load_project_config", lambda: config)
        monkeypatch.setattr(
            "sys.argv",
            ["ontos", "--json", "hook", "pre-commit"],
        )

        assert main() == 0
        payload = self._payload(capsys)
        assert payload["status"] == "success"
        assert payload["exit_code"] == 0
        assert payload["result"]["status"] == "clean"
        assert payload["result"]["exit_category"] == "clean"

    def test_strict_pre_push_failure_is_findings_envelope(
        self, tmp_path, monkeypatch, capsys
    ):
        config = MagicMock()
        config.hooks.pre_push = True
        config.hooks.strict = True
        config.paths.context_map = "Ontos_Context_Map.md"
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("ontos.io.config.load_project_config", lambda: config)
        monkeypatch.setattr(
            "sys.argv",
            ["ontos", "hook", "pre-push", "--json"],
        )

        assert main() == 1
        payload = self._payload(capsys)
        assert payload["status"] == "success"
        assert payload["exit_code"] == 1
        assert payload["error"] is None
        assert payload["result"]["status"] == "findings"
        assert payload["result"]["exit_category"] == "findings"
        assert payload["data"]["allowed"] is False

    def test_non_strict_pre_push_failure_is_warnings_envelope(
        self, tmp_path, monkeypatch, capsys
    ):
        config = MagicMock()
        config.hooks.pre_push = True
        config.hooks.strict = False
        config.paths.context_map = "Ontos_Context_Map.md"
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("ontos.io.config.load_project_config", lambda: config)
        monkeypatch.setattr(
            "sys.argv",
            ["ontos", "--json", "hook", "pre-push"],
        )

        assert main() == 3
        payload = self._payload(capsys)
        assert payload["status"] == "success"
        assert payload["exit_code"] == 3
        assert payload["result"]["status"] == "warnings"
        assert payload["result"]["exit_category"] == "warnings"
        assert payload["data"]["allowed"] is True

    def test_hook_runtime_error_is_internal_error_envelope(
        self, monkeypatch, capsys
    ):
        def fail_config():
            raise OSError("config unreadable")

        monkeypatch.setattr("ontos.io.config.load_project_config", fail_config)
        monkeypatch.setattr(
            "sys.argv",
            ["ontos", "--json", "hook", "pre-push"],
        )

        assert main() == 5
        payload = self._payload(capsys)
        assert payload["status"] == "error"
        assert payload["exit_code"] == 5
        assert payload["error"]["code"] == "E_HOOK_FAILED"
        assert payload["result"]["status"] == "error"
        assert payload["result"]["exit_category"] == "internal"
