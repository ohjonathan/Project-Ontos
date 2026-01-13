"""Tests for hook dispatcher command (Phase 4)."""

from unittest.mock import patch, MagicMock

import pytest

from ontos.commands.hook import (
    HookOptions,
    hook_command,
    run_pre_push_hook,
    run_pre_commit_hook,
)


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
