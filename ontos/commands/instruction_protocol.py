"""Shared instruction protocol blocks for generated agent instruction files."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class InstructionProtocolConfig:
    """Configuration for composing activation protocol sections."""

    instruction_file: str
    regenerate_command: str
    regenerate_purpose: str
    staleness_command: str
    map_sync_command: Optional[str] = None
    map_sync_purpose: Optional[str] = None


DEFAULT_USER_CUSTOM_PLACEHOLDER = (
    "<!-- Add your project-specific notes below. "
    "This section is preserved during auto-sync. -->"
)


TRIGGER_PHRASES_TEMPLATE = """## Trigger Phrases
If the user says any of these as a command (case-insensitive), execute Ontos Activation below:
- "activate ontos"
- "ontos"
- "/ontos"
- "load context"
- "reload context"

Do NOT ask for clarification. Just execute the steps."""


ACTIVATION_PROTOCOL_HEAD_TEMPLATE = """## What is Activation?
Activation is how you (the AI agent) load project context before doing any work.
It is **mandatory**. Do not ask "why" or request clarification—just execute the steps below.

## Ontos Activation
1. Run `ontos map` (or `python3 -m ontos map` if the CLI is not installed). Do not ask—try both.
2. Read `Ontos_Context_Map.md` (Tier 1 minimum: first ~2k tokens).
3. Load only the relevant documents for the task.
4. Follow `depends_on` upward as needed.
5. Confirm: "Loaded: [ids]".

## Re-Activation Trigger

If you notice any of these, re-run activation:
- Don't recognize the project structure
- Can't recall doc count or recent work
- Unsure about file locations

## After Context Compaction (/compact)
If you just regained context after compaction, re-read this file ({instruction_file}). If any Re-Activation Trigger applies, execute Ontos Activation.

## Session End
1. Run `ontos log -e "slug"` to archive session work.
2. Fill in Goal, Key Decisions, Alternatives Considered, and Impacts.

## Quick Reference
| Command | Purpose |
|---------|---------|
| `ontos map` | Regenerate context map |
{map_sync_row}| `{regenerate_command}` | {regenerate_purpose} |
| `ontos doctor` | Health check and validation |
| `ontos log -e "slug"` | Archive session work |
| `ontos query <id>` | Find document by ID |"""


ACTIVATION_PROTOCOL_TAIL_TEMPLATE = """## Core Invariants
- Do not edit `Ontos_Context_Map.md` manually; regenerate with `ontos map`.
- Do not edit `{instruction_file}` manually (except `# USER CUSTOM` section below).
- If a command fails, read the error message and avoid guessing fixes.

# USER CUSTOM

<!-- USER CUSTOM -->
<!-- Add your project-specific notes below. This section is preserved during auto-sync. -->
<!-- /USER CUSTOM -->

## Staleness
If `{instruction_file}` is older than the context map or logs, regenerate with `{staleness_command}`."""


def render_trigger_phrases() -> str:
    """Render shared trigger phrase section."""
    return TRIGGER_PHRASES_TEMPLATE


def render_activation_protocol_head(config: InstructionProtocolConfig) -> str:
    """Render the shared activation protocol sections up to quick reference."""
    map_sync_row = ""
    if config.map_sync_command and config.map_sync_purpose:
        map_sync_row = (
            f"| `{config.map_sync_command}` | {config.map_sync_purpose} |\n"
        )

    return ACTIVATION_PROTOCOL_HEAD_TEMPLATE.format(
        instruction_file=config.instruction_file,
        regenerate_command=config.regenerate_command,
        regenerate_purpose=config.regenerate_purpose,
        map_sync_row=map_sync_row,
    )


def render_activation_protocol_tail(config: InstructionProtocolConfig) -> str:
    """Render shared invariants, user custom block, and staleness section."""
    return ACTIVATION_PROTOCOL_TAIL_TEMPLATE.format(
        instruction_file=config.instruction_file,
        staleness_command=config.staleness_command,
    )


def preserve_user_custom_section(content: str, existing_content: Optional[str]) -> str:
    """Preserve user custom content between stable markers when present."""
    open_marker = "<!-- USER CUSTOM -->"
    close_marker = "<!-- /USER CUSTOM -->"

    if not existing_content:
        return content

    existing_open = existing_content.find(open_marker)
    existing_close = existing_content.rfind(close_marker)
    if existing_open == -1 or existing_close == -1:
        return content
    if existing_close < existing_open + len(open_marker):
        return content

    custom_content = existing_content[existing_open + len(open_marker):existing_close].strip()
    if not custom_content:
        return content

    if custom_content == DEFAULT_USER_CUSTOM_PLACEHOLDER:
        return content

    target_open = content.find(open_marker)
    target_close = content.rfind(close_marker)
    if target_open == -1 or target_close == -1:
        return content
    if target_close < target_open + len(open_marker):
        return content

    return (
        content[: target_open + len(open_marker)]
        + "\n"
        + custom_content
        + "\n"
        + content[target_close:]
    )
