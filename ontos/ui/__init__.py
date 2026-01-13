"""
Ontos UI Layer.

This layer handles output formatting for the CLI:
- JSON output formatting (json_output.py)
- Progress indicators (progress.py)
- Human-readable output (output.py - existing)

Layer Rules:
- May import from core/ (types only)
- Must NOT import from io/ or commands/
"""

from ontos.ui.output import OutputHandler
from ontos.ui.json_output import (
    JsonOutputHandler,
    emit_json,
    emit_error,
    emit_result,
    to_json,
    validate_json_output,
)

__all__ = [
    # output.py
    "OutputHandler",
    # json_output.py
    "JsonOutputHandler",
    "emit_json",
    "emit_error",
    "emit_result",
    "to_json",
    "validate_json_output",
]
