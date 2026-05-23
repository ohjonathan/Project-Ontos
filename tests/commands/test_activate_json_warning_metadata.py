"""CLI regressions for #119 — `ontos activate --json` structured validation
metadata (`severity`, `rule_id`, `message`, `document_id`, `file_path`).

Mirrors the MCP enrichment landed in PR #118 / v4.5.0 (deliverable
project-ontos-github-issues-115-117). See
docs/specs/project-ontos-issue-119-cli-activate-json-warning-metadata-spec.md
§1.4.1 for the canonical case list.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from ontos.core.types import ValidationError, ValidationErrorType, ValidationResult
from ontos.mcp.tools import _validation_issues


REPO_ROOT = Path(__file__).resolve().parents[2]


# =============================================================================
# Helpers
# =============================================================================


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip(), encoding="utf-8")


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "ontos", *args],
        cwd=root,
        text=True,
        capture_output=True,
        env=env,
    )


def _orphan_warning(doc_id: str, filepath: str) -> ValidationError:
    return ValidationError(
        error_type=ValidationErrorType.ORPHAN,
        doc_id=doc_id,
        filepath=filepath,
        message="Document has no incoming dependencies",
        fix_suggestion="Add a dependency from another document, or change type to one in allowed_orphan_types.",
        severity="warning",
    )


# =============================================================================
# Unit tests — ValidationError.to_dict() shape (Cases 1-6 from spec §1.4.1)
# =============================================================================


def test_to_dict_orphan_includes_rule_id_document_id_file_path() -> None:
    """Case 1 — orphan warning carries severity, rule_id, message, document_id, file_path."""
    issue = _orphan_warning("kernel_doc", "docs/kernel/kernel_doc.md")

    record = issue.to_dict()

    assert record == {
        "severity": "warning",
        "message": "Document has no incoming dependencies",
        "rule_id": "orphan",
        "document_id": "kernel_doc",
        "file_path": "docs/kernel/kernel_doc.md",
    }


def test_to_dict_depth_warning_emits_depth_rule_id() -> None:
    """Case 2 — depth warning carries rule_id == 'depth' and doc context."""
    issue = ValidationError(
        error_type=ValidationErrorType.DEPTH,
        doc_id="leaf_doc",
        filepath="docs/leaf.md",
        message="Dependency depth 6 exceeds max 5",
        fix_suggestion="Flatten the dependency chain or raise max_dependency_depth.",
        severity="warning",
    )

    record = issue.to_dict()

    assert record["rule_id"] == "depth"
    assert record["severity"] == "warning"
    assert record["document_id"] == "leaf_doc"
    assert record["file_path"] == "docs/leaf.md"


def test_to_dict_schema_warning_emits_schema_rule_id() -> None:
    """Case 3 — schema warning (e.g. log doc missing required fields) → rule_id == 'schema'.

    Note: finer-grained snapshot rule_ids like ``schema.log_missing_fields`` are
    MCP-only by design; the CLI path reports the structured enum value ``schema``.
    """
    issue = ValidationError(
        error_type=ValidationErrorType.SCHEMA,
        doc_id="logs_2026_05_22",
        filepath="docs/logs/2026-05-22.md",
        message="Log missing fields: branch",
        fix_suggestion="Add the required `branch` field to the log frontmatter.",
        severity="warning",
    )

    record = issue.to_dict()

    assert record["rule_id"] == "schema"
    assert record["document_id"] == "logs_2026_05_22"
    assert record["file_path"] == "docs/logs/2026-05-22.md"


def test_to_dict_out_of_scope_dependency_emits_correct_rule_id() -> None:
    """Case 4 — depends_on resolved on disk but not loaded → rule_id == 'out_of_scope_dependency'."""
    issue = ValidationError(
        error_type=ValidationErrorType.OUT_OF_SCOPE_DEPENDENCY,
        doc_id="strategy_a",
        filepath="docs/strategy/a.md",
        message="External dependency resolved from disk: '.llm-dev/framework/framework.md' (declared in strategy_a)",
        fix_suggestion="Either load the target as a doc or rephrase the dependency.",
        severity="warning",
    )

    record = issue.to_dict()

    assert record["rule_id"] == "out_of_scope_dependency"
    assert record["document_id"] == "strategy_a"
    assert record["file_path"] == "docs/strategy/a.md"


def test_to_dict_squashes_empty_document_id_and_file_path() -> None:
    """Case 5 — empty doc_id / filepath are absent from the public payload (not present as empty strings)."""
    issue = ValidationError(
        error_type=ValidationErrorType.ORPHAN,
        doc_id="",
        filepath="",
        message="Document has no incoming dependencies",
        fix_suggestion="",
        severity="warning",
    )

    record = issue.to_dict()

    assert record == {
        "severity": "warning",
        "message": "Document has no incoming dependencies",
        "rule_id": "orphan",
    }
    assert "document_id" not in record
    assert "file_path" not in record


def test_to_dict_error_severity_preserved() -> None:
    """Case 6 — error-severity ValidationError serializes with severity == 'error'."""
    issue = ValidationError(
        error_type=ValidationErrorType.BROKEN_LINK,
        doc_id="strategy_a",
        filepath="docs/strategy/a.md",
        message="Broken dependency: missing_doc",
        fix_suggestion="Create the target doc or remove the dependency.",
        severity="error",
    )

    record = issue.to_dict()

    assert record["severity"] == "error"
    assert record["rule_id"] == "broken_link"
    assert record["document_id"] == "strategy_a"
    assert record["file_path"] == "docs/strategy/a.md"


# =============================================================================
# Parity tests — CLI and MCP paths produce identical lists (Case 8 from spec)
# =============================================================================


def test_cli_and_mcp_serialization_identical_for_validation_result() -> None:
    """Case 8 (mandatory) — CLI and MCP serialize the same ValidationResult identically.

    This is the load-bearing regression for the §0 'bit-for-bit' invariant: if
    these two lists ever diverge, MCP and CLI consumers will see different
    payloads for the same underlying ValidationError, defeating the whole
    purpose of #119.
    """
    enriched = _orphan_warning("kernel_doc", "docs/kernel/kernel_doc.md")
    sparse = ValidationError(
        error_type=ValidationErrorType.ORPHAN,
        doc_id="",
        filepath="",
        message="Bare snapshot orphan",
        fix_suggestion="",
        severity="warning",
    )
    result = ValidationResult(warnings=[enriched, sparse])

    cli_serialized = [issue.to_dict() for issue in result.warnings]
    mcp_serialized = _validation_issues(result.warnings)

    assert cli_serialized == mcp_serialized


# =============================================================================
# Integration test — CLI JSON envelope carries the structured shape end-to-end
# =============================================================================


def _orphan_workspace(root: Path) -> Path:
    """Build a temp workspace whose context map will surface at least one
    orphan warning. Uses a non-atom type (default ``allowed_orphan_types`` is
    ``["atom"]``) so the orphan rule fires regardless of the default config.
    """
    _write(
        root / ".ontos.toml",
        """
        [ontos]
        version = "4.4"

        [scanning]
        skip_patterns = ["*/docs/reviews/*"]
        """,
    )
    # A kernel doc with no incoming dependencies — kernel is not in default
    # allowed_orphan_types, so the validator must emit an orphan warning.
    _write(
        root / "docs/kernel.md",
        """
        ---
        id: kernel_doc
        type: kernel
        status: active
        ---
        Kernel body.
        """,
    )
    return root


def test_activate_json_emits_structured_validation_warnings(tmp_path: Path) -> None:
    """End-to-end — `ontos --json activate` writes objects, not strings, under
    ``data.validation.warnings`` and ``data.validation.errors``.
    """
    root = _orphan_workspace(tmp_path)

    result = _run(root, "--json", "activate")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    validation = payload["data"]["validation"]
    assert isinstance(validation["errors"], list)
    assert isinstance(validation["warnings"], list)

    # Every record (if any) is a dict with severity + message.
    for record in validation["warnings"] + validation["errors"]:
        assert isinstance(record, dict), f"expected dict, got {type(record).__name__}: {record!r}"
        assert "severity" in record
        assert "message" in record

    # At least one orphan warning must appear (the kernel doc has no incoming deps).
    orphan_records = [w for w in validation["warnings"] if w.get("rule_id") == "orphan"]
    assert orphan_records, (
        f"expected at least one orphan warning in {validation['warnings']!r}"
    )
    orphan = orphan_records[0]
    assert orphan["severity"] == "warning"
    assert orphan["document_id"] == "kernel_doc"
    assert orphan["file_path"].endswith("docs/kernel.md")


def test_activate_json_not_usable_path_emits_empty_lists(tmp_path: Path) -> None:
    """Case 7 — the ``_not_usable()`` branch (no docs loaded, no existing context
    map) still emits empty ``validation.errors`` / ``validation.warnings`` lists,
    unaffected by the shape change.
    """
    _write(
        tmp_path / ".ontos.toml",
        """
        [ontos]
        version = "4.4"
        """,
    )
    # No docs at all and no Context Map → _not_usable path.

    result = _run(tmp_path, "--json", "activate")
    payload = json.loads(result.stdout)

    # _not_usable returns exit 1 with an error envelope; the inner data block
    # still includes the validation shell.
    assert result.returncode == 1, result.stderr
    validation = payload["data"]["validation"]
    assert validation["errors"] == []
    assert validation["warnings"] == []
