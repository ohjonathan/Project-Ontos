"""Unit tests for shared instruction protocol rendering/helpers."""

from ontos.commands.instruction_protocol import (
    DEFAULT_USER_CUSTOM_PLACEHOLDER,
    InstructionProtocolConfig,
    preserve_user_custom_section,
    render_activation_protocol_head,
    render_activation_protocol_tail,
    render_trigger_phrases,
)


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
    assert "| `ontos map --sync-agents` | Regenerate map + sync AGENTS.md |" in content
    assert "| `ontos agents` | Generate instruction files |" in content


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
