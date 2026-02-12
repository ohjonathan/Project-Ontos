"""Backward-compatible re-exports for instruction protocol utilities."""

from ontos.core.instruction_protocol import (  # noqa: F401
    ACTIVATION_PROTOCOL_HEAD_TEMPLATE,
    ACTIVATION_PROTOCOL_TAIL_TEMPLATE,
    DEFAULT_USER_CUSTOM_PLACEHOLDER,
    TRIGGER_PHRASES_TEMPLATE,
    InstructionProtocolConfig,
    preserve_user_custom_section,
    render_activation_protocol_head,
    render_activation_protocol_tail,
    render_trigger_phrases,
)
