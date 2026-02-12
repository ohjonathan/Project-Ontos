# ontos/ui/json_output.py
"""JSON output formatting for CLI commands.

Per Roadmap 6.7: Consistent JSON output across all commands.
"""

import json
import sys
import warnings
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class JsonOutputHandler:
    """Handler for JSON output mode."""

    def __init__(self, pretty: bool = False, file=None):
        """
        Initialize JSON output handler.

        Args:
            pretty: If True, indent JSON output for readability
            file: Output file (default: sys.stdout)
        """
        self.pretty = pretty
        self.file = file or sys.stdout

    def emit(self, data: Dict[str, Any]) -> None:
        """Emit data as JSON to output."""
        if self.pretty:
            output = json.dumps(data, indent=2, default=str, ensure_ascii=False)
        else:
            output = json.dumps(data, default=str, ensure_ascii=False)
        print(output, file=self.file)

    def error(
        self,
        message: str,
        code: str,
        details: Optional[str] = None
    ) -> None:
        """Emit error in JSON format."""
        data: Dict[str, Any] = {
            "status": "error",
            "error_code": code,
            "message": message,
        }
        if details is not None:
            data["details"] = details
        self.emit(data)

    def result(self, data: Any, message: Optional[str] = None) -> None:
        """
        Emit success result in JSON format.

        Named 'result' per Roadmap 6.7 specification.
        """
        output: Dict[str, Any] = {
            "status": "success",
            "data": to_json(data),
        }
        if message is not None:
            output["message"] = message
        self.emit(output)


def to_json(obj: Any) -> Any:
    """
    Convert Ontos objects to JSON-serializable types.

    Handles:
    - Dataclasses -> dict
    - Lists -> list of converted items
    - Paths -> str
    - Enums -> value
    - Other -> as-is
    """
    if obj is None:
        return None
    elif is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_json(getattr(obj, f.name)) for f in fields(obj)}
    elif isinstance(obj, list):
        return [to_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: to_json(v) for k, v in obj.items()}
    elif isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, Enum):
        return obj.value
    else:
        return obj


# Convenience functions

def emit_json(data: Dict[str, Any], pretty: bool = False) -> None:
    """Emit JSON to stdout."""
    JsonOutputHandler(pretty=pretty).emit(data)


def emit_error(
    message: str,
    code: str,
    details: Optional[str] = None
) -> None:
    """Emit error JSON to stdout.

    Deprecated: prefer `emit_command_error()` for command envelopes.
    """
    warnings.warn(
        "emit_error() is deprecated; use emit_command_error().",
        DeprecationWarning,
        stacklevel=2,
    )
    emit_command_error(
        command="ontos",
        exit_code=1,
        code=code,
        message=message,
        details=details,
    )


def emit_result(data: Any, message: Optional[str] = None) -> None:
    """Emit success result JSON to stdout."""
    JsonOutputHandler().result(data, message)


def emit_command_success(
    command: str,
    exit_code: int,
    message: str,
    data: Optional[Any] = None,
    warnings: Optional[List[str]] = None,
    *,
    schema_version: str = "3.3",
) -> None:
    """Emit command success envelope with stable top-level schema."""
    emit_json(
        {
            "schema_version": schema_version,
            "command": command,
            "status": "success",
            "exit_code": exit_code,
            "message": message,
            "data": to_json(data if data is not None else {}),
            "warnings": warnings or [],
            "error": None,
        }
    )


def emit_command_error(
    command: str,
    exit_code: int,
    code: str,
    message: str,
    details: Optional[str] = None,
    data: Optional[Any] = None,
    warnings: Optional[List[str]] = None,
    *,
    schema_version: str = "3.3",
) -> None:
    """Emit command error envelope with stable top-level schema."""
    error_payload: Dict[str, Any] = {"code": code}
    if details is not None:
        error_payload["details"] = details

    emit_json(
        {
            "schema_version": schema_version,
            "command": command,
            "status": "error",
            "exit_code": exit_code,
            "message": message,
            "data": to_json(data if data is not None else {}),
            "warnings": warnings or [],
            "error": error_payload,
        }
    )


def validate_json_output(output: str) -> bool:
    """
    Validate that a string is valid JSON.

    Used by wrapper command JSON validation.
    """
    try:
        json.loads(output)
        return True
    except json.JSONDecodeError:
        return False
