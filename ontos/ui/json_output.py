# ontos/ui/json_output.py
"""JSON output formatting for CLI commands.

Per Roadmap 6.7: Consistent JSON output across all commands.
"""

import json
import sys
import warnings
from dataclasses import fields, is_dataclass
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


COMMAND_ENVELOPE_SCHEMA_VERSION = "4.0"


class ResultStatus(str, Enum):
    """Domain outcome, independent of whether command execution succeeded."""

    CLEAN = "clean"
    FINDINGS = "findings"
    WARNINGS = "warnings"
    INCOMPLETE = "incomplete"
    ERROR = "error"


class ExitCode(IntEnum):
    """Public numeric exit-code taxonomy introduced with schema v4."""

    CLEAN = 0
    FINDINGS = 1
    USAGE = 2
    WARNINGS = 3
    INTERNAL = 5
    INTERRUPTED = 130


class ExitCategory(str, Enum):
    """Machine-readable exit category for the v4 command contract."""

    CLEAN = "clean"
    FINDINGS = "findings"
    WARNINGS = "warnings"
    USAGE = "usage"
    INTERNAL = "internal"
    INTERRUPTED = "interrupted"


_DIRECT_DIAGNOSTIC_COUNT_KEYS = frozenset(
    {
        "errors",
        "failed",
        "failures",
        "findings",
        "info",
        "load_issues",
        "load_warnings",
        "parse_failed_candidates",
        "passed",
        "skipped",
        "validation_errors",
        "validation_info",
        "validation_warnings",
        "warnings",
    }
)
_INCOMPLETE_COUNT_KEYS = frozenset(
    {"load_issues", "load_warnings", "parse_failed_candidates"}
)
_LEGACY_RESULT_STATUS = {
    "clean": ResultStatus.CLEAN,
    "failing": ResultStatus.FINDINGS,
    "fail": ResultStatus.FINDINGS,
    "failed": ResultStatus.FINDINGS,
    "findings": ResultStatus.FINDINGS,
    "pass": ResultStatus.CLEAN,
    "passed": ResultStatus.CLEAN,
    "warn": ResultStatus.WARNINGS,
    "warning": ResultStatus.WARNINGS,
    "warnings": ResultStatus.WARNINGS,
}


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
    schema_version: str = COMMAND_ENVELOPE_SCHEMA_VERSION,
    result_status: Optional[str] = None,
    result_kind: Optional[str] = None,
    diagnostic_counts: Optional[Mapping[str, int]] = None,
    diagnostic_basis: Optional[str] = None,
    diagnostics_complete: Optional[bool] = None,
    exit_category: Optional[str] = None,
) -> None:
    """Emit a v4 command envelope for a successfully executed command."""
    _emit_command_envelope(
        schema_version=schema_version,
        command=command,
        execution_status="success",
        exit_code=exit_code,
        message=message,
        data=data,
        warnings=warnings,
        error=None,
        result_status=result_status,
        result_kind=result_kind,
        diagnostic_counts=diagnostic_counts,
        diagnostic_basis=diagnostic_basis,
        diagnostics_complete=diagnostics_complete,
        exit_category=exit_category,
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
    schema_version: str = COMMAND_ENVELOPE_SCHEMA_VERSION,
    execution_succeeded: Optional[bool] = None,
    result_status: Optional[str] = None,
    result_kind: Optional[str] = None,
    diagnostic_counts: Optional[Mapping[str, int]] = None,
    diagnostic_basis: Optional[str] = None,
    diagnostics_complete: Optional[bool] = None,
    exit_category: Optional[str] = None,
) -> None:
    """Emit a v4 command envelope for a failed or finding-bearing result.

    Older callers used ``emit_command_error`` for both execution failures and
    successfully completed diagnostics that found issues.  In schema v4 those
    states are distinct.  Diagnostic ``E_COMMAND_FAILED`` payloads carrying
    structured evidence are treated as successful execution by default;
    callers can override that inference with ``execution_succeeded``.
    """
    error_payload: Dict[str, Any] = {"code": code}
    if details is not None:
        error_payload["details"] = details

    if execution_succeeded is None:
        execution_succeeded = (
            code == "E_COMMAND_FAILED" and _has_structured_diagnostics(data)
        )
    execution_status = "success" if execution_succeeded else "error"
    _emit_command_envelope(
        schema_version=schema_version,
        command=command,
        execution_status=execution_status,
        exit_code=exit_code,
        message=message,
        data=data,
        warnings=warnings,
        error=None if execution_succeeded else error_payload,
        result_status=result_status,
        result_kind=result_kind,
        diagnostic_counts=diagnostic_counts,
        diagnostic_basis=diagnostic_basis,
        diagnostics_complete=diagnostics_complete,
        exit_category=exit_category,
    )


def _emit_command_envelope(
    *,
    schema_version: str,
    command: str,
    execution_status: str,
    exit_code: int,
    message: str,
    data: Optional[Any],
    warnings: Optional[List[str]],
    error: Optional[Dict[str, Any]],
    result_status: Optional[str],
    result_kind: Optional[str],
    diagnostic_counts: Optional[Mapping[str, int]],
    diagnostic_basis: Optional[str],
    diagnostics_complete: Optional[bool],
    exit_category: Optional[str],
) -> None:
    serialized_data = to_json(data if data is not None else {})
    diagnostics = _diagnostics_payload(
        serialized_data,
        counts=diagnostic_counts,
        basis=diagnostic_basis,
        complete=diagnostics_complete,
    )
    normalized_result = _result_status(
        execution_status=execution_status,
        exit_code=exit_code,
        data=serialized_data,
        diagnostics=diagnostics,
        explicit=result_status,
    )
    normalized_kind = result_kind or (
        "diagnostic" if diagnostics["basis"] is not None else "operation"
    )
    # ``exit_category`` is derived exclusively from the public numeric exit
    # taxonomy.  Keep accepting the legacy keyword while callers migrate, but
    # never allow it (or the domain-level result status) to contradict the
    # process exit code advertised by the same envelope.
    normalized_exit_category = _exit_category(
        execution_status=execution_status,
        exit_code=exit_code,
        result_status=normalized_result,
    )

    emit_json(
        {
            "schema_version": schema_version,
            "command": command,
            "status": execution_status,
            "exit_code": exit_code,
            "message": message,
            "result": {
                "status": normalized_result,
                "kind": normalized_kind,
                "exit_category": normalized_exit_category,
                "diagnostics": diagnostics,
            },
            "data": serialized_data,
            "warnings": warnings or [],
            "error": error,
        }
    )


def _has_structured_diagnostics(data: Optional[Any]) -> bool:
    if not isinstance(data, Mapping):
        return False
    return bool(
        "result_status" in data
        or isinstance(data.get("summary"), Mapping)
        or any(key in data for key in _DIRECT_DIAGNOSTIC_COUNT_KEYS)
    )


def _diagnostics_payload(
    data: Any,
    *,
    counts: Optional[Mapping[str, int]],
    basis: Optional[str],
    complete: Optional[bool],
) -> Dict[str, Any]:
    if counts is not None:
        normalized_counts = _numeric_counts(counts)
        return {
            "basis": basis or "caller",
            "complete": bool(complete) if complete is not None else False,
            "counts": normalized_counts,
        }

    if isinstance(data, Mapping):
        summary = data.get("summary")
        if isinstance(summary, Mapping):
            summary_counts = _numeric_counts(summary)
            if summary_counts:
                return {
                    "basis": "data.summary",
                    "complete": True if complete is None else bool(complete),
                    "counts": summary_counts,
                }

        direct_counts = _numeric_counts(
            {
                key: data[key]
                for key in _DIRECT_DIAGNOSTIC_COUNT_KEYS
                if key in data
            }
        )
        if direct_counts:
            return {
                "basis": "data",
                "complete": True if complete is None else bool(complete),
                "counts": direct_counts,
            }

    return {
        "basis": basis,
        "complete": False if complete is None else bool(complete),
        "counts": {},
    }


def _numeric_counts(values: Mapping[str, Any]) -> Dict[str, int]:
    return {
        str(key): value
        for key, value in values.items()
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
    }


def _result_status(
    *,
    execution_status: str,
    exit_code: int,
    data: Any,
    diagnostics: Mapping[str, Any],
    explicit: Optional[str],
) -> str:
    if execution_status == "error":
        return ResultStatus.ERROR.value

    selected: Optional[ResultStatus] = None

    # The keyword argument is an explicit caller decision and therefore wins
    # over legacy diagnostic-count heuristics.
    if explicit is not None:
        selected = _normalize_result_status(explicit)
        if selected is not None:
            return selected.value

    # A status embedded in a legacy data payload remains an inference input:
    # incomplete-evidence counters may refine clean/warnings to incomplete.
    if isinstance(data, Mapping):
        candidate = data.get("result_status")
        if isinstance(candidate, str):
            selected = _normalize_result_status(candidate)

    if selected == ResultStatus.FINDINGS:
        return selected.value

    counts = diagnostics.get("counts", {})
    if isinstance(counts, Mapping) and any(
        counts.get(key, 0) > 0 for key in _INCOMPLETE_COUNT_KEYS
    ):
        return ResultStatus.INCOMPLETE.value
    if selected is not None:
        return selected.value
    if exit_code == 0:
        return ResultStatus.CLEAN.value
    if exit_code == 3:
        return ResultStatus.WARNINGS.value
    return ResultStatus.FINDINGS.value


def _normalize_result_status(raw: str) -> Optional[ResultStatus]:
    selected = _LEGACY_RESULT_STATUS.get(str(raw).lower())
    if selected is not None:
        return selected
    try:
        return ResultStatus(str(raw).lower())
    except ValueError:
        return None


def _exit_category(
    *,
    execution_status: str,
    exit_code: int,
    result_status: str,
) -> str:
    # ``execution_status`` and ``result_status`` remain accepted for private
    # API compatibility, but neither may redefine the numeric exit taxonomy.
    # Unknown/reserved codes collapse to the documented internal category.
    return {
        int(ExitCode.CLEAN): ExitCategory.CLEAN.value,
        int(ExitCode.FINDINGS): ExitCategory.FINDINGS.value,
        int(ExitCode.USAGE): ExitCategory.USAGE.value,
        int(ExitCode.WARNINGS): ExitCategory.WARNINGS.value,
        int(ExitCode.INTERNAL): ExitCategory.INTERNAL.value,
        int(ExitCode.INTERRUPTED): ExitCategory.INTERRUPTED.value,
    }.get(int(exit_code), ExitCategory.INTERNAL.value)


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
