"""Shared CLAUDE.md template for instruction artifact generation."""

from typing import Optional

from ontos.core.instruction_protocol import (
    InstructionProtocolConfig,
    preserve_user_custom_section,
    render_activation_protocol_head,
    render_activation_protocol_tail,
    render_trigger_phrases,
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

CLAUDE_WHAT_IS_ONTOS = """## What is Ontos?

Ontos is a local-first documentation management system that:
- Maintains a context map of all project documentation
- Tracks documentation dependencies and status
- Ensures documentation stays synchronized with code changes"""

CLAUDE_MD_TEMPLATE = "\n\n".join(
    [
        CLAUDE_HEADER_TEMPLATE,
        CLAUDE_TOOLING_NOTES,
        render_trigger_phrases(),
        render_activation_protocol_head(CLAUDE_PROTOCOL_CONFIG),
        render_activation_protocol_tail(CLAUDE_PROTOCOL_CONFIG),
        CLAUDE_WHAT_IS_ONTOS,
    ]
) + "\n"


def generate_claude_content(existing_content: Optional[str] = None) -> str:
    """Generate CLAUDE.md content while preserving USER CUSTOM when present."""
    content = preserve_user_custom_section(CLAUDE_MD_TEMPLATE, existing_content)
    return content if content.endswith("\n") else content + "\n"
