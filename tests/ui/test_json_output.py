"""Tests for JSON output formatting."""

import json
from dataclasses import dataclass
from enum import Enum
from io import StringIO
from pathlib import Path

import pytest

from ontos.ui.json_output import (
    JsonOutputHandler,
    emit_error,
    emit_json,
    emit_result,
    to_json,
    validate_json_output,
)


class TestJsonOutputHandler:
    """Tests for JsonOutputHandler class."""

    def test_emit_outputs_valid_json(self):
        """emit() should output valid JSON."""
        output = StringIO()
        handler = JsonOutputHandler(file=output)
        handler.emit({"key": "value"})
        result = json.loads(output.getvalue())
        assert result == {"key": "value"}

    def test_emit_pretty_indents_output(self):
        """emit() with pretty=True should indent output."""
        output = StringIO()
        handler = JsonOutputHandler(pretty=True, file=output)
        handler.emit({"key": "value"})
        assert "  " in output.getvalue()  # Has indentation

    def test_error_includes_required_fields(self):
        """error() should include status, error_code, message."""
        output = StringIO()
        handler = JsonOutputHandler(file=output)
        handler.error("Test error", "E001")
        result = json.loads(output.getvalue())
        assert result["status"] == "error"
        assert result["error_code"] == "E001"
        assert result["message"] == "Test error"
        assert "details" not in result

    def test_error_includes_details_when_provided(self):
        """error() should include details when provided."""
        output = StringIO()
        handler = JsonOutputHandler(file=output)
        handler.error("Test error", "E001", details="Extra info")
        result = json.loads(output.getvalue())
        assert result["details"] == "Extra info"

    def test_result_includes_success_status(self):
        """result() should set status to success."""
        output = StringIO()
        handler = JsonOutputHandler(file=output)
        handler.result({"count": 5})
        result = json.loads(output.getvalue())
        assert result["status"] == "success"
        assert result["data"] == {"count": 5}

    def test_result_includes_message_when_provided(self):
        """result() should include message when provided."""
        output = StringIO()
        handler = JsonOutputHandler(file=output)
        handler.result({"count": 5}, message="Operation complete")
        result = json.loads(output.getvalue())
        assert result["message"] == "Operation complete"


class TestToJson:
    """Tests for to_json converter."""

    def test_converts_none(self):
        """to_json should pass through None."""
        assert to_json(None) is None

    def test_converts_primitives(self):
        """to_json should pass through primitives."""
        assert to_json(42) == 42
        assert to_json("string") == "string"
        assert to_json(True) is True

    def test_converts_list(self):
        """to_json should convert list items."""
        assert to_json([1, 2, 3]) == [1, 2, 3]

    def test_converts_dict(self):
        """to_json should convert dict values."""
        assert to_json({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    def test_converts_path_to_string(self):
        """to_json should convert Path to string."""
        assert to_json(Path("/foo/bar")) == "/foo/bar"

    def test_converts_enum_to_value(self):
        """to_json should convert Enum to its value."""
        class Status(Enum):
            ACTIVE = "active"
            DRAFT = "draft"

        assert to_json(Status.ACTIVE) == "active"

    def test_converts_dataclass(self):
        """to_json should convert dataclass to dict."""
        @dataclass
        class Sample:
            name: str
            count: int

        result = to_json(Sample(name="test", count=5))
        assert result == {"name": "test", "count": 5}

    def test_converts_nested_dataclass(self):
        """to_json should handle nested dataclasses."""
        @dataclass
        class Inner:
            value: int

        @dataclass
        class Outer:
            inner: Inner
            label: str

        result = to_json(Outer(inner=Inner(value=42), label="test"))
        assert result == {"inner": {"value": 42}, "label": "test"}


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_emit_json(self, capsys):
        """emit_json should output to stdout."""
        emit_json({"test": True})
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result == {"test": True}

    def test_emit_error(self, capsys):
        """emit_error should output error JSON."""
        emit_error("Failed", "E999")
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "error"
        assert result["error_code"] == "E999"

    def test_emit_result(self, capsys):
        """emit_result should output success JSON."""
        emit_result({"items": []})
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "success"


class TestValidateJsonOutput:
    """Tests for JSON validation."""

    def test_valid_json_returns_true(self):
        """validate_json_output returns True for valid JSON."""
        assert validate_json_output('{"key": "value"}') is True
        assert validate_json_output('[]') is True
        assert validate_json_output('"string"') is True

    def test_invalid_json_returns_false(self):
        """validate_json_output returns False for invalid JSON."""
        assert validate_json_output('not json') is False
        assert validate_json_output('{key: value}') is False
        assert validate_json_output('') is False
