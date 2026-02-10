"""Shared CLAUDE.md template for export commands."""

from typing import Optional

from ontos.commands.instruction_protocol import (
    InstructionProtocolConfig,
    preserve_user_custom_section,
    render_activation_protocol_head,
    render_activation_protocol_tail,
)


CLAUDE_PROTOCOL_CONFIG = InstructionProtocolConfig(
    instruction_file="CLAUDE.md",
    regenerate_command="ontos export claude --force",
    regenerate_purpose="Regenerate CLAUDE.md",
    staleness_command="ontos export claude --force",
)


CLAUDE_HEADER_TEMPLATE = """# CLAUDE.md

This project uses **Ontos** for documentation management."""


CLAUDE_TOOLING_NOTES = """## Claude Notes
If `MEMORY.md` exists, use it for Claude memory only. Project activation still comes from this file."""


CLAUDE_MD_TEMPLATE = "\n\n".join(
    [
        CLAUDE_HEADER_TEMPLATE,
        CLAUDE_TOOLING_NOTES,
        render_activation_protocol_head(CLAUDE_PROTOCOL_CONFIG),
        render_activation_protocol_tail(CLAUDE_PROTOCOL_CONFIG),
    ]
)


def generate_claude_content(existing_content: Optional[str] = None) -> str:
    """Generate CLAUDE.md content while preserving USER CUSTOM when present."""
    return preserve_user_custom_section(CLAUDE_MD_TEMPLATE, existing_content)
