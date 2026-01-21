"""Tests for ontos.commands.init module (Phase 3)."""
import pytest
from pathlib import Path
import subprocess

from ontos.commands.init import (
    init_command,
    InitOptions,
    ONTOS_HOOK_MARKER,
    _is_ontos_hook,
    _check_git_repo,
)


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    return tmp_path


class TestInitCommand:
    """Tests for init_command() function."""

    def test_init_empty_directory(self, git_repo):
        """Init in empty git repo creates .ontos.toml."""
        options = InitOptions(path=git_repo)
        code, msg = init_command(options)

        # Exit code 0 (success) or 3 (hooks skipped) are both valid
        assert code in (0, 3)
        assert (git_repo / ".ontos.toml").exists()

    def test_init_creates_directory_structure(self, git_repo):
        """Init creates the expected directory structure."""
        options = InitOptions(path=git_repo)
        init_command(options)

        assert (git_repo / "docs").is_dir()
        assert (git_repo / "docs" / "logs").is_dir()
        assert (git_repo / "docs" / "strategy").is_dir()
        assert (git_repo / "docs" / "reference").is_dir()
        assert (git_repo / "docs" / "archive").is_dir()

    def test_init_already_initialized(self, git_repo):
        """Init returns exit code 0 if config exists (v3.0.0 LLM-friendly)."""
        (git_repo / ".ontos.toml").write_text("[ontos]\n")

        options = InitOptions(path=git_repo)
        code, msg = init_command(options)

        assert code == 0  # v3.0.0: LLM-friendly exit code
        assert "Already initialized" in msg

    def test_init_force_reinitialize(self, git_repo):
        """Init --force overwrites existing config."""
        (git_repo / ".ontos.toml").write_text("[ontos]\nversion = 'old'\n")

        options = InitOptions(path=git_repo, force=True)
        code, msg = init_command(options)

        # Should succeed (0) or have hooks skipped (3)
        assert code in (0, 3)

        # Config should be overwritten with new content
        content = (git_repo / ".ontos.toml").read_text()
        assert 'version = "3.0"' in content

    def test_init_not_git_repo(self, tmp_path):
        """Init fails with exit code 2 if not git repo."""
        options = InitOptions(path=tmp_path)
        code, msg = init_command(options)

        assert code == 2
        assert "Not a git repository" in msg


class TestHookDetection:
    """Tests for hook detection functions."""

    def test_hook_marker_detection(self, tmp_path):
        """Hooks with ONTOS_HOOK_MARKER are recognized as ours."""
        hook_file = tmp_path / "pre-commit"
        hook_file.write_text(f"#!/bin/sh\n{ONTOS_HOOK_MARKER}\necho test\n")

        assert _is_ontos_hook(hook_file) is True

    def test_hook_without_marker_not_detected(self, tmp_path):
        """Hooks without marker are not recognized as ours."""
        hook_file = tmp_path / "pre-commit"
        hook_file.write_text("#!/bin/sh\necho other hook\n")

        assert _is_ontos_hook(hook_file) is False

    def test_nonexistent_hook_not_detected(self, tmp_path):
        """Non-existent hook file returns False."""
        hook_file = tmp_path / "pre-commit"
        assert _is_ontos_hook(hook_file) is False


class TestGitRepoCheck:
    """Tests for _check_git_repo() function."""

    def test_check_git_repo_valid(self, git_repo):
        """Valid git repo returns None (no error)."""
        result = _check_git_repo(git_repo)
        assert result is None

    def test_check_git_repo_not_git(self, tmp_path):
        """Non-git directory returns error tuple."""
        result = _check_git_repo(tmp_path)
        assert result is not None
        code, msg = result
        assert code == 2
        assert "Not a git repository" in msg


class TestHookInstallation:
    """Tests for hook installation."""

    def test_hooks_installed(self, git_repo):
        """Init installs hooks in .git/hooks."""
        options = InitOptions(path=git_repo)
        code, _ = init_command(options)

        if code == 0:  # Only check if hooks weren't skipped
            assert (git_repo / ".git" / "hooks" / "pre-commit").exists()
            assert (git_repo / ".git" / "hooks" / "pre-push").exists()

    def test_skip_hooks_option(self, git_repo):
        """--skip-hooks option prevents hook installation."""
        options = InitOptions(path=git_repo, skip_hooks=True)
        code, _ = init_command(options)

        assert code == 0
        # Hooks directory exists but our hooks should not be there
        # (git init creates sample hooks which is fine)
        pre_commit = git_repo / ".git" / "hooks" / "pre-commit"
        if pre_commit.exists():
            content = pre_commit.read_text()
            assert ONTOS_HOOK_MARKER not in content

    def test_hook_collision_does_not_overwrite(self, git_repo):
        """Existing non-Ontos hook is not overwritten without --force."""
        # Create a foreign hook
        hooks_dir = git_repo / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        foreign_hook = hooks_dir / "pre-commit"
        foreign_hook.write_text("#!/bin/sh\necho 'foreign hook'\n")

        options = InitOptions(path=git_repo)
        code, _ = init_command(options)

        # Should exit with code 3 (hooks skipped)
        assert code == 3

        # Foreign hook should be preserved
        content = foreign_hook.read_text()
        assert "foreign hook" in content
        assert ONTOS_HOOK_MARKER not in content

    def test_hook_collision_force_overwrites(self, git_repo):
        """--force overwrites existing non-Ontos hooks."""
        # Create a foreign hook
        hooks_dir = git_repo / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        foreign_hook = hooks_dir / "pre-commit"
        foreign_hook.write_text("#!/bin/sh\necho 'foreign hook'\n")

        options = InitOptions(path=git_repo, force=True, yes=True)
        code, _ = init_command(options)

        # Should succeed
        assert code == 0

        # Hook should now be ours and the foreign content should be gone
        content = foreign_hook.read_text()
        assert ONTOS_HOOK_MARKER in content
        assert "foreign hook" not in content

class TestHookConfirmation:
    """Tests for hook confirmation flow (v3.0.5 UX-1)."""

    def test_skip_hooks_flag_skips_confirmation(self, git_repo):
        """--skip-hooks bypasses confirmation entirely."""
        options = InitOptions(path=git_repo, skip_hooks=True)
        code, _ = init_command(options)

        assert code == 0
        # No hooks should be installed
        pre_commit = git_repo / ".git" / "hooks" / "pre-commit"
        if pre_commit.exists():
            assert ONTOS_HOOK_MARKER not in pre_commit.read_text()

    def test_yes_flag_skips_confirmation(self, git_repo):
        """--yes installs hooks without prompting."""
        options = InitOptions(path=git_repo, yes=True)
        code, _ = init_command(options)

        assert code in (0, 3)  # 0 success, 3 if collision
        # In clean repo, hooks should be installed
        if code == 0:
            pre_commit = git_repo / ".git" / "hooks" / "pre-commit"
            assert pre_commit.exists()
            assert ONTOS_HOOK_MARKER in pre_commit.read_text()

    def test_skip_hooks_wins_over_yes(self, git_repo):
        """--skip-hooks takes precedence over --yes."""
        options = InitOptions(path=git_repo, skip_hooks=True, yes=True)
        code, _ = init_command(options)

        assert code == 0
        pre_commit = git_repo / ".git" / "hooks" / "pre-commit"
        if pre_commit.exists():
            assert ONTOS_HOOK_MARKER not in pre_commit.read_text()

    def test_ctrl_c_aborts_init_and_cleans_up(self, git_repo, monkeypatch):
        """Ctrl+C during hook confirmation aborts entire init and cleans up all changes."""
        # Simulate KeyboardInterrupt during input()
        def mock_input(prompt):
            raise KeyboardInterrupt()
        monkeypatch.setattr('builtins.input', mock_input)
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo)
        code, msg = init_command(options)

        # Should return SIGINT exit code
        assert code == 130
        assert "Aborted" in msg

        # Verification of complete cleanup
        assert not (git_repo / ".ontos.toml").exists()
        assert not (git_repo / "docs").exists()
        assert not (git_repo / "Ontos_Context_Map.md").exists()

    def test_ctrl_d_skips_hooks(self, git_repo, monkeypatch):
        """EOF (Ctrl+D) during hook confirmation skips hooks but proceeds with init."""
        # Simulate EOFError during input()
        def mock_input(prompt):
            raise EOFError()
        monkeypatch.setattr('builtins.input', mock_input)
        monkeypatch.setattr('sys.stdin.isatty', lambda: True)

        options = InitOptions(path=git_repo)
        code, msg = init_command(options)

        assert code == 0
        assert (git_repo / ".ontos.toml").exists()
        # Hooks should NOT be installed
        pre_commit = git_repo / ".git" / "hooks" / "pre-commit"
        if pre_commit.exists():
            assert ONTOS_HOOK_MARKER not in pre_commit.read_text()

    def test_non_tty_auto_installs_hooks(self, git_repo, monkeypatch):
        """Non-TTY (CI) environment auto-installs hooks."""
        monkeypatch.setattr('sys.stdin.isatty', lambda: False)
        
        options = InitOptions(path=git_repo)
        code, _ = init_command(options)

        assert code == 0
        assert (git_repo / ".git" / "hooks" / "pre-commit").exists()
        assert ONTOS_HOOK_MARKER in (git_repo / ".git" / "hooks" / "pre-commit").read_text()
