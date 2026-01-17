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
        """Init returns exit code 0 if config exists (idempotent)."""
        (git_repo / ".ontos.toml").write_text("[ontos]\n")

        options = InitOptions(path=git_repo)
        code, msg = init_command(options)

        assert code == 0  # Changed in v3.0.2: exit 0 for better UX
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

        options = InitOptions(path=git_repo, force=True)
        code, _ = init_command(options)

        # Should succeed
        assert code == 0

        # Hook should now be ours
        content = foreign_hook.read_text()
        assert ONTOS_HOOK_MARKER in content
