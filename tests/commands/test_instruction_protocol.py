"""Unit tests for shared instruction protocol rendering/helpers."""

import os
from pathlib import Path
import subprocess
import sys

from ontos.commands.instruction_protocol import (
    DEFAULT_USER_CUSTOM_PLACEHOLDER,
    InstructionProtocolConfig,
    preserve_user_custom_section,
    render_activation_protocol_head,
    render_activation_protocol_tail,
    render_trigger_phrases,
)
from ontos.core.instruction_protocol import activation_command_candidates


def test_render_trigger_phrases_contains_expected_commands():
    content = render_trigger_phrases()
    assert "## Trigger Phrases" in content
    assert '- "activate ontos"' in content
    assert '- "reload context"' in content


def test_render_activation_protocol_head_includes_optional_map_sync_row():
    config = InstructionProtocolConfig(
        instruction_file="AGENTS.md",
        regenerate_command="ontos agents",
        regenerate_purpose="Generate instruction files",
        staleness_command="ontos map --sync-agents",
        map_sync_command="ontos map --sync-agents",
        map_sync_purpose="Regenerate map + sync AGENTS.md",
    )
    content = render_activation_protocol_head(config)
    assert "## What is Activation?" in content
    assert "A stale PATH executable must not shadow" in content
    assert "reports an incompatible Ontos version" in content
    assert content.index("./.venv/bin/python") < content.index("python3 -m ontos")
    assert "python3 -m ontos activate" in content
    assert "If every candidate fails" in content
    assert "| `ontos map --sync-agents` | Regenerate map + sync AGENTS.md |" in content
    assert "| `ontos agents` | Generate instruction files |" in content


def test_activation_candidates_prefer_working_repo_venv_over_stale_path(
    tmp_path: Path,
) -> None:
    repo_python = tmp_path / ".venv" / "bin" / "python"
    repo_python.parent.mkdir(parents=True)
    repo_python.write_text(
        f"#!{os.environ.get('SHELL', '/bin/sh')}\nexec {sys.executable!r} \"$@\"\n",
        encoding="utf-8",
    )
    repo_python.chmod(0o755)

    stale_bin = tmp_path / "stale-bin"
    stale_bin.mkdir()
    (stale_bin / "ontos").write_text("#!/bin/sh\necho 'ontos 4.6.0'\n", encoding="utf-8")
    (stale_bin / "python3").write_text("#!/bin/sh\nexit 23\n", encoding="utf-8")
    for executable in stale_bin.iterdir():
        executable.chmod(0o755)

    candidates = activation_command_candidates(tmp_path)
    assert candidates[0] == [str(repo_python), "-m", "ontos"]
    env = dict(os.environ)
    env["PATH"] = str(stale_bin)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
    result = subprocess.run(
        [*candidates[0], "--version"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "4.7.1" in result.stdout


def test_render_activation_protocol_head_omits_map_sync_row_when_unset():
    config = InstructionProtocolConfig(
        instruction_file="CLAUDE.md",
        regenerate_command="ontos export claude --force",
        regenerate_purpose="Regenerate CLAUDE.md",
        staleness_command="ontos export claude --force",
    )
    content = render_activation_protocol_head(config)
    assert "| `ontos map --sync-agents` |" not in content
    assert "| `ontos export claude --force` | Regenerate CLAUDE.md |" in content


def test_render_activation_protocol_tail_contains_markers_and_staleness():
    config = InstructionProtocolConfig(
        instruction_file="CLAUDE.md",
        regenerate_command="ontos export claude --force",
        regenerate_purpose="Regenerate CLAUDE.md",
        staleness_command="ontos export claude --force",
    )
    content = render_activation_protocol_tail(config)
    assert "# USER CUSTOM" in content
    assert "<!-- USER CUSTOM -->" in content
    assert "regenerate with `ontos export claude --force`" in content


def test_preserve_user_custom_section_keeps_literal_regex_backrefs():
    content = (
        "Header\n\n<!-- USER CUSTOM -->\n"
        "<!-- Add your project-specific notes below. This section is preserved during auto-sync. -->\n"
        "<!-- /USER CUSTOM -->\n"
    )
    existing = (
        "Old\n\n<!-- USER CUSTOM -->\n"
        "Use \\1 and \\2 and \\g<99> literally.\n"
        "<!-- /USER CUSTOM -->\n"
    )

    result = preserve_user_custom_section(content, existing)
    assert "Use \\1 and \\2 and \\g<99> literally." in result


def test_preserve_user_custom_section_ignores_default_placeholder_content():
    content = (
        "Header\n\n<!-- USER CUSTOM -->\n"
        "<!-- Add your project-specific notes below. This section is preserved during auto-sync. -->\n"
        "<!-- /USER CUSTOM -->\n"
    )
    existing = f"<!-- USER CUSTOM -->\n{DEFAULT_USER_CUSTOM_PLACEHOLDER}\n<!-- /USER CUSTOM -->"
    result = preserve_user_custom_section(content, existing)
    assert result == content


def test_preserve_user_custom_section_returns_original_when_markers_missing():
    content = "Header\n\n<!-- USER CUSTOM -->\n<!-- /USER CUSTOM -->\n"
    existing = "No markers here"
    assert preserve_user_custom_section(content, existing) == content


def test_preserve_user_custom_section_outermost_markers_win_with_nested_markers():
    content = (
        "Header\n\n<!-- USER CUSTOM -->\n"
        "<!-- Add your project-specific notes below. This section is preserved during auto-sync. -->\n"
        "<!-- /USER CUSTOM -->\n"
    )
    existing = (
        "Old\n\n<!-- USER CUSTOM -->\n"
        "outer-start\n"
        "<!-- USER CUSTOM -->\n"
        "inner-content\n"
        "<!-- /USER CUSTOM -->\n"
        "outer-end\n"
        "<!-- /USER CUSTOM -->\n"
    )

    result = preserve_user_custom_section(content, existing)
    assert "outer-start" in result
    assert "inner-content" in result
    assert "outer-end" in result


def test_preserve_user_custom_section_unbalanced_markers_do_not_truncate():
    content = (
        "Header\n\n<!-- USER CUSTOM -->\n"
        "<!-- Add your project-specific notes below. This section is preserved during auto-sync. -->\n"
        "<!-- /USER CUSTOM -->\n"
    )
    existing = "Old\n\n<!-- USER CUSTOM -->\nmissing close"

    assert preserve_user_custom_section(content, existing) == content
