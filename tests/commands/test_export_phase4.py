"""Tests for export command (Phase 4)."""

from pathlib import Path
import re

import pytest

from ontos.commands.agents import generate_agents_content
from ontos.commands.claude_template import CLAUDE_MD_TEMPLATE
from ontos.commands.export import (
    ExportOptions,
    _run_export_command,
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

    def test_public_command_returns_exit_code(self, tmp_path, monkeypatch):
        """Public export_command should return int exit code only."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        options = ExportOptions(output_path=tmp_path / "claude_public.md")
        result = export_command(options)
        assert isinstance(result, int)
        assert result == 0

    def test_creates_claude_md(self, tmp_path, monkeypatch):
        """Should create CLAUDE.md in repo root."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")

        options = ExportOptions()
        exit_code, message = _run_export_command(options)

        assert exit_code == 0
        assert "Created" in message
        assert (tmp_path / "CLAUDE.md").exists()

    def test_fails_if_exists_without_force(self, tmp_path, monkeypatch):
        """Should fail if CLAUDE.md exists and force=False."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        (tmp_path / "CLAUDE.md").write_text("existing content")

        options = ExportOptions(force=False)
        exit_code, message = _run_export_command(options)

        assert exit_code == 1
        assert "already exists" in message
        assert (tmp_path / "CLAUDE.md").read_text() == "existing content"

    def test_overwrites_with_force(self, tmp_path, monkeypatch):
        """Should overwrite if force=True."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        (tmp_path / "CLAUDE.md").write_text("existing content")

        options = ExportOptions(force=True)
        exit_code, message = _run_export_command(options)

        assert exit_code == 0
        assert (tmp_path / "CLAUDE.md").read_text() == CLAUDE_MD_TEMPLATE

    def test_overwrites_with_force_preserves_user_custom(self, tmp_path, monkeypatch):
        """Should preserve USER CUSTOM section on forced overwrite."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        (tmp_path / "CLAUDE.md").write_text(
            CLAUDE_MD_TEMPLATE.replace(
                "<!-- USER CUSTOM -->\n"
                "<!-- Add your project-specific notes below. This section is preserved during auto-sync. -->\n"
                "<!-- /USER CUSTOM -->",
                "<!-- USER CUSTOM -->\nKeep this note.\n<!-- /USER CUSTOM -->",
            )
        )

        options = ExportOptions(force=True)
        exit_code, _ = _run_export_command(options)

        assert exit_code == 0
        content = (tmp_path / "CLAUDE.md").read_text()
        assert "Keep this note." in content
        assert "## Staleness" in content

    def test_rejects_path_outside_repo(self, tmp_path, monkeypatch):
        """Should reject output path outside repo root."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")

        options = ExportOptions(output_path=tmp_path.parent / "evil.md")
        exit_code, message = _run_export_command(options)

        assert exit_code == 2
        assert "within repository root" in message

    def test_custom_output_path_within_repo(self, tmp_path, monkeypatch):
        """Should allow custom output path within repo."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        options = ExportOptions(output_path=subdir / "AI_INSTRUCTIONS.md")
        exit_code, message = _run_export_command(options)

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

    def test_template_has_activation_resilience_sections(self):
        assert "## Trigger Phrases" in CLAUDE_MD_TEMPLATE
        assert "## Re-Activation Trigger" in CLAUDE_MD_TEMPLATE
        assert "## After Context Compaction (/compact)" in CLAUDE_MD_TEMPLATE
        assert "## Staleness" in CLAUDE_MD_TEMPLATE

    def test_template_has_mandatory_activation_language(self):
        assert "It is **mandatory**." in CLAUDE_MD_TEMPLATE
        assert "Do NOT ask for clarification." in CLAUDE_MD_TEMPLATE

    def test_template_has_commands(self):
        assert "ontos map" in CLAUDE_MD_TEMPLATE
        assert "ontos log" in CLAUDE_MD_TEMPLATE
        assert "ontos export claude --force" in CLAUDE_MD_TEMPLATE

    def test_template_mentions_context_map(self):
        assert "Ontos_Context_Map.md" in CLAUDE_MD_TEMPLATE

    def test_template_does_not_reference_manual(self):
        assert "Ontos_Manual.md" not in CLAUDE_MD_TEMPLATE

    def test_template_has_what_is_ontos_section(self):
        assert "## What is Ontos?" in CLAUDE_MD_TEMPLATE

    def test_template_has_user_custom_markers(self):
        assert "<!-- USER CUSTOM -->" in CLAUDE_MD_TEMPLATE
        assert "<!-- /USER CUSTOM -->" in CLAUDE_MD_TEMPLATE
        assert CLAUDE_MD_TEMPLATE.endswith("\n")

    def test_template_parity_with_agents_activation_protocol(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        agents_content = generate_agents_content()

        assert agents_content.endswith("\n")

        def extract_section(content: str, heading: str) -> str:
            start = content.index(heading)
            search_start = start + len(heading)
            next_h2 = content.find("\n## ", search_start)
            next_h1 = content.find("\n# ", search_start)
            section_ends = [idx for idx in [next_h2, next_h1] if idx != -1]
            end = min(section_ends) if section_ends else len(content)
            return content[start:end].strip()

        def extract_block(content: str, start_heading: str, end_heading: str) -> str:
            start = content.index(start_heading)
            end_start = content.index(end_heading, start)
            search_start = end_start + len(end_heading)
            next_h2 = content.find("\n## ", search_start)
            next_h1 = content.find("\n# ", search_start)
            block_ends = [idx for idx in [next_h2, next_h1] if idx != -1]
            end = min(block_ends) if block_ends else len(content)
            return content[start:end].strip()

        def normalize_shared_block(block: str) -> str:
            normalized = block
            normalized = normalized.replace("AGENTS.md", "<INSTRUCTION_FILE>")
            normalized = normalized.replace("CLAUDE.md", "<INSTRUCTION_FILE>")
            normalized = normalized.replace("`ontos agents`", "`<COMMAND>`")
            normalized = normalized.replace("`ontos map --sync-agents`", "`<COMMAND>`")
            normalized = normalized.replace("`ontos export claude --force`", "`<COMMAND>`")
            normalized = normalized.replace("Generate instruction files", "<PURPOSE>")
            normalized = normalized.replace("Regenerate map + sync AGENTS.md", "<PURPOSE>")
            normalized = normalized.replace("Regenerate CLAUDE.md", "<PURPOSE>")
            normalized = normalized.replace(
                "Regenerate map + sync <INSTRUCTION_FILE>",
                "<PURPOSE>",
            )
            normalized = normalized.replace("Regenerate <INSTRUCTION_FILE>", "<PURPOSE>")
            normalized = re.sub(
                r"\n## Project Stats\n(?:- .*(?:\n|$))+",
                "\n",
                normalized,
            )
            normalized = re.sub(
                r"^\| `<COMMAND>` \| .*sync <INSTRUCTION_FILE> \|\n?",
                "",
                normalized,
                flags=re.MULTILINE,
            )
            normalized = normalized.replace(
                "| `<COMMAND>` | <PURPOSE> |\n| `<COMMAND>` | <PURPOSE> |\n",
                "| `<COMMAND>` | <PURPOSE> |\n",
            )
            normalized = re.sub(r"\n{3,}", "\n\n", normalized)
            return normalized

        agents_trigger = extract_section(agents_content, "## Trigger Phrases")
        claude_trigger = extract_section(CLAUDE_MD_TEMPLATE, "## Trigger Phrases")
        assert agents_trigger == claude_trigger

        agents_body = extract_block(
            agents_content,
            "## What is Activation?",
            "## Staleness",
        )
        claude_body = extract_block(
            CLAUDE_MD_TEMPLATE,
            "## What is Activation?",
            "## Staleness",
        )
        assert normalize_shared_block(agents_body) == normalize_shared_block(claude_body)


class TestExportClaudeTemplate:
    """Tests for export claude template content."""

    def test_export_claude_template_no_manual(self):
        from ontos.commands.export_claude import CLAUDE_MD_TEMPLATE as CLAUDE_MD_TEMPLATE_CLAUDE
        assert "Ontos_Manual.md" not in CLAUDE_MD_TEMPLATE_CLAUDE
