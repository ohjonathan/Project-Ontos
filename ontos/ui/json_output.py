# ontos/ui/json_output.py
"""JSON output formatting for CLI commands.

Per Roadmap 6.7: Consistent JSON output across all commands.
"""

import json
import sys
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
    """Emit error JSON to stdout."""
    JsonOutputHandler().error(message, code, details)


def emit_result(data: Any, message: Optional[str] = None) -> None:
    """Emit success result JSON to stdout."""
    JsonOutputHandler().result(data, message)


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
