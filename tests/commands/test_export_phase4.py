"""Tests for export command (Phase 4)."""

from pathlib import Path

import pytest

from ontos.commands.export import (
    ExportOptions,
    CLAUDE_MD_TEMPLATE,
    export_command,
    find_repo_root,
)


class TestExportOptions:
    """Tests for ExportOptions dataclass."""

    def test_default_values(self):
        options = ExportOptions()
        assert options.output_path is None
        assert options.force is False

    def test_with_values(self):
        options = ExportOptions(
            output_path=Path("/tmp/test.md"),
            force=True
        )
        assert options.output_path == Path("/tmp/test.md")
        assert options.force is True


class TestExportCommand:
    """Tests for export_command."""

    def test_creates_claude_md(self, tmp_path, monkeypatch):
        """Should create CLAUDE.md in repo root."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")

        options = ExportOptions()
        exit_code, message = export_command(options)

        assert exit_code == 0
        assert "Created" in message
        assert (tmp_path / "CLAUDE.md").exists()

    def test_fails_if_exists_without_force(self, tmp_path, monkeypatch):
        """Should fail if CLAUDE.md exists and force=False."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        (tmp_path / "CLAUDE.md").write_text("existing content")

        options = ExportOptions(force=False)
        exit_code, message = export_command(options)

        assert exit_code == 1
        assert "already exists" in message
        assert (tmp_path / "CLAUDE.md").read_text() == "existing content"

    def test_overwrites_with_force(self, tmp_path, monkeypatch):
        """Should overwrite if force=True."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        (tmp_path / "CLAUDE.md").write_text("existing content")

        options = ExportOptions(force=True)
        exit_code, message = export_command(options)

        assert exit_code == 0
        assert (tmp_path / "CLAUDE.md").read_text() == CLAUDE_MD_TEMPLATE

    def test_rejects_path_outside_repo(self, tmp_path, monkeypatch):
        """Should reject output path outside repo root."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")

        options = ExportOptions(output_path=tmp_path.parent / "evil.md")
        exit_code, message = export_command(options)

        assert exit_code == 2
        assert "within repository root" in message

    def test_custom_output_path_within_repo(self, tmp_path, monkeypatch):
        """Should allow custom output path within repo."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        options = ExportOptions(output_path=subdir / "AI_INSTRUCTIONS.md")
        exit_code, message = export_command(options)

        assert exit_code == 0
        assert (subdir / "AI_INSTRUCTIONS.md").exists()


class TestFindRepoRoot:
    """Tests for find_repo_root."""

    def test_finds_ontos_toml(self, tmp_path, monkeypatch):
        """Should find directory with .ontos.toml."""
        (tmp_path / ".ontos.toml").write_text("")
        subdir = tmp_path / "a" / "b"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        root = find_repo_root()

        assert root == tmp_path

    def test_finds_git_dir(self, tmp_path, monkeypatch):
        """Should find directory with .git."""
        (tmp_path / ".git").mkdir()
        subdir = tmp_path / "a" / "b"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        root = find_repo_root()

        assert root == tmp_path

    def test_prefers_ontos_toml_over_git(self, tmp_path, monkeypatch):
        """Should prefer .ontos.toml over .git."""
        (tmp_path / ".git").mkdir()
        subdir = tmp_path / "project"
        subdir.mkdir()
        (subdir / ".ontos.toml").write_text("")
        monkeypatch.chdir(subdir)

        root = find_repo_root()

        assert root == subdir


class TestClaudeMdTemplate:
    """Tests for CLAUDE.md template content."""

    def test_template_has_activation_section(self):
        assert "## Ontos Activation" in CLAUDE_MD_TEMPLATE

    def test_template_has_commands(self):
        assert "ontos map" in CLAUDE_MD_TEMPLATE
        assert "ontos log" in CLAUDE_MD_TEMPLATE

    def test_template_mentions_context_map(self):
        assert "Ontos_Context_Map.md" in CLAUDE_MD_TEMPLATE
