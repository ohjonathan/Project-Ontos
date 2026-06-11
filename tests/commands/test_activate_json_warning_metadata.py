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

    result = _run(root, "--json", "activate", "--warnings", "full")
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


def _depth_chain_workspace(root: Path) -> Path:
    """A doc chain longer than ``max_dependency_depth`` so the validator emits
    a depth warning (D.2 codex F1 — Case 2 CLI integration coverage).
    """
    _write(
        root / ".ontos.toml",
        """
        [ontos]
        version = "4.4"

        [validation]
        max_dependency_depth = 1
        """,
    )
    # depth-chain: a → b → c (3 hops > 1)
    _write(
        root / "docs/a.md",
        """
        ---
        id: doc_a
        type: atom
        status: active
        depends_on: [doc_b]
        ---
        A.
        """,
    )
    _write(
        root / "docs/b.md",
        """
        ---
        id: doc_b
        type: atom
        status: active
        depends_on: [doc_c]
        ---
        B.
        """,
    )
    _write(
        root / "docs/c.md",
        """
        ---
        id: doc_c
        type: atom
        status: active
        ---
        C.
        """,
    )
    return root


def test_activate_json_depth_warning_carries_structured_metadata(tmp_path: Path) -> None:
    """D.2 codex F1, Case 2 — CLI JSON path emits depth warnings as structured records."""
    root = _depth_chain_workspace(tmp_path)

    result = _run(root, "--json", "activate", "--warnings", "full")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    depth_records = [
        w for w in payload["data"]["validation"]["warnings"] if w.get("rule_id") == "depth"
    ]
    assert depth_records, (
        f"expected at least one depth warning in {payload['data']['validation']['warnings']!r}"
    )
    record = depth_records[0]
    assert record["severity"] == "warning"
    assert record["document_id"]
    assert record["file_path"]


def _out_of_scope_workspace(root: Path) -> Path:
    """A doc whose `depends_on` resolves to a workspace-relative path that
    exists on disk but is not loaded as a doc (PR #118 / v4.5.0 behavior).
    The validator emits an ``out_of_scope_dependency`` warning (D.2 codex F1
    — Case 4 CLI integration coverage).
    """
    _write(
        root / ".ontos.toml",
        """
        [ontos]
        version = "4.4"
        """,
    )
    # External markdown file outside the scanned docs/ tree (so it exists on
    # disk but is not loaded as a doc — no doc-id match in the graph).
    _write(root / "external/notes.md", "External notes content.\n")
    _write(
        root / "docs/atom.md",
        """
        ---
        id: atom_with_external_dep
        type: atom
        status: active
        depends_on: [external/notes.md]
        ---
        Atom referencing an external file.
        """,
    )
    return root


def test_activate_json_out_of_scope_dependency_carries_structured_metadata(tmp_path: Path) -> None:
    """D.2 codex F1, Case 4 — CLI JSON path emits out-of-scope dependency warnings."""
    root = _out_of_scope_workspace(tmp_path)

    result = _run(root, "--json", "activate", "--warnings", "full")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    out_of_scope = [
        w
        for w in payload["data"]["validation"]["warnings"]
        if w.get("rule_id") == "out_of_scope_dependency"
    ]
    assert out_of_scope, (
        f"expected at least one out_of_scope_dependency warning in {payload['data']['validation']['warnings']!r}"
    )
    record = out_of_scope[0]
    assert record["severity"] == "warning"
    assert record["document_id"] == "atom_with_external_dep"
    assert record["file_path"].endswith("docs/atom.md")


def _log_schema_workspace(root: Path) -> Path:
    """A log doc missing required schema fields so the validator emits a
    schema-class warning (D.2 codex F1 — Case 3 CLI integration coverage).
    The CLI path reports the structured enum value ``rule_id == "schema"``;
    finer-grained snapshot rule_ids like ``schema.log_missing_fields`` are
    MCP-only by design.
    """
    _write(
        root / ".ontos.toml",
        """
        [ontos]
        version = "4.4"
        """,
    )
    # A skeleton anchor doc so the workspace has at least one regular doc.
    _write(
        root / "docs/atom.md",
        """
        ---
        id: atom_anchor
        type: atom
        status: active
        ---
        Anchor.
        """,
    )
    # A log doc with `type: log` but missing the required fields the
    # validator's log-schema check looks for (e.g. `branch`, `concepts`).
    _write(
        root / "docs/logs/2026-05-22.md",
        """
        ---
        id: log_2026_05_22
        type: log
        status: active
        ---
        Log body without required fields.
        """,
    )
    return root


def test_activate_json_schema_class_warning_carries_structured_metadata(tmp_path: Path) -> None:
    """D.2 codex F1 + D.5 codex F1, Case 3 — CLI JSON path emits schema-class
    warnings as structured records when a log doc is missing required fields.

    The validator emits a `ValidationErrorType.SCHEMA` warning (rule_id ==
    ``"schema"``) for log docs missing required fields like ``branch``. We
    assert specifically on that rule_id so the test is load-bearing — if the
    schema warning disappears from the CLI JSON payload, the test fails.
    """
    root = _log_schema_workspace(tmp_path)

    result = _run(root, "--json", "activate", "--warnings", "full")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    log_id = "log_2026_05_22"
    schema_records = [
        w
        for w in payload["data"]["validation"]["warnings"]
        if w.get("document_id") == log_id and w.get("rule_id") == "schema"
    ]
    assert schema_records, (
        "expected at least one rule_id=='schema' warning for the log doc in "
        f"{payload['data']['validation']['warnings']!r}"
    )
    record = schema_records[0]
    assert record["severity"] == "warning"
    assert record["file_path"].endswith("docs/logs/2026-05-22.md")
    assert "Log missing fields" in record["message"]


def test_activate_json_error_severity_lands_under_errors_with_structured_shape(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """D.2 codex F1, Case 6 — CLI JSON path emits error-severity records under
    ``data.validation.errors`` with the same structured shape.

    Uses monkeypatch because ``generate_context_map`` currently emits warning-
    severity entries for broken `depends_on` (no naturally-occurring error-
    severity output via the standard fixture pipeline). The monkeypatch
    injects a controlled `ValidationResult` so we can verify the wiring.
    """
    import ontos.commands.activate as activate_mod

    # Anchor workspace with a single doc so docs is non-empty (which is the
    # branch that actually calls generate_context_map and serializes results).
    _write(
        tmp_path / ".ontos.toml",
        """
        [ontos]
        version = "4.4"
        """,
    )
    _write(
        tmp_path / "docs/atom.md",
        """
        ---
        id: atom_anchor
        type: atom
        status: active
        ---
        Anchor.
        """,
    )

    synthetic_error = ValidationError(
        error_type=ValidationErrorType.BROKEN_LINK,
        doc_id="atom_anchor",
        filepath="docs/atom.md",
        message="Broken dependency: missing_doc",
        fix_suggestion="Create the target doc or remove the dependency.",
        severity="error",
    )
    synthetic_warning = ValidationError(
        error_type=ValidationErrorType.ORPHAN,
        doc_id="atom_anchor",
        filepath="docs/atom.md",
        message="Document has no incoming dependencies",
        fix_suggestion="",
        severity="warning",
    )

    def _patched_generate_context_map(docs, gen_config, options):
        return "stub-content", ValidationResult(
            errors=[synthetic_error], warnings=[synthetic_warning]
        )

    monkeypatch.setattr(activate_mod, "generate_context_map", _patched_generate_context_map)

    exit_code, payload = activate_mod.run_activation(
        scope=None, write_map=False, root=tmp_path, warnings_mode="full"
    )
    # Exit code is 0 because errors are still load_result + validation_warnings,
    # not validation_errors specifically; activation considers all-with-warnings
    # as 'usable_with_warnings' (exit 0). The key assertion is the payload shape.
    assert exit_code == 0

    errors = payload["validation"]["errors"]
    warnings = payload["validation"]["warnings"]

    assert len(errors) == 1
    err = errors[0]
    assert err["severity"] == "error"
    assert err["rule_id"] == "broken_link"
    assert err["document_id"] == "atom_anchor"
    assert err["file_path"] == "docs/atom.md"
    assert err["message"] == "Broken dependency: missing_doc"

    assert len(warnings) == 1
    warn = warnings[0]
    assert warn["severity"] == "warning"
    assert warn["rule_id"] == "orphan"


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
    # (#132) The stable empty budget shape is present on the not-usable path too.
    assert validation["warnings_total"] == 0
    assert validation["warnings_truncated"] is False
    assert validation["warning_groups"] == []


# =============================================================================
# (#132) Warning grouping / budgeting modes
# =============================================================================


def test_activate_json_default_is_grouped(tmp_path: Path) -> None:
    """Default (no flag) returns grouped warnings: empty inline list, groups
    with bounded full-record samples, and summary counts from the full list."""
    root = _orphan_workspace(tmp_path)

    result = _run(root, "--json", "activate")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    validation = payload["data"]["validation"]
    assert validation["warnings"] == []
    assert validation["warnings_truncated"] is True
    groups = validation["warning_groups"]
    assert groups, "expected at least one warning group"
    assert sum(group["count"] for group in groups) == validation["warnings_total"]
    assert validation["warnings_total"] == payload["data"]["summary"]["validation_warnings"]
    orphan_group = next(g for g in groups if g["rule_id"] == "orphan")
    assert 0 < len(orphan_group["samples"]) <= 3
    sample = orphan_group["samples"][0]
    assert sample["severity"] == "warning"
    assert sample["rule_id"] == "orphan"
    assert "message" in sample
    # Status/exit semantics are unchanged by the budget.
    assert payload["data"]["status"] == "usable_with_warnings"


def test_activate_json_summary_mode_drops_samples(tmp_path: Path) -> None:
    root = _orphan_workspace(tmp_path)

    result = _run(root, "--json", "activate", "--warnings", "summary")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    validation = payload["data"]["validation"]
    assert validation["warnings"] == []
    assert all(group["samples"] == [] for group in validation["warning_groups"])
    assert validation["warnings_total"] > 0


def test_activate_json_warning_rule_filters_full_records(tmp_path: Path) -> None:
    root = _orphan_workspace(tmp_path)

    result = _run(
        root, "--json", "activate",
        "--warnings", "full", "--warning-rule", "orphan",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    validation = payload["data"]["validation"]
    assert validation["warnings"], "expected inline records in full mode"
    assert all(record["rule_id"] == "orphan" for record in validation["warnings"])
    assert validation["warnings_total"] == len(validation["warnings"])
    assert validation["warnings_truncated"] is False
    # Summary counts stay computed from the unfiltered list.
    assert payload["data"]["summary"]["validation_warnings"] >= validation["warnings_total"]


def test_activate_json_full_with_limit_truncates(tmp_path: Path) -> None:
    root = _orphan_workspace(tmp_path)

    result = _run(root, "--json", "activate", "--warnings", "full", "--limit", "1")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    validation = payload["data"]["validation"]
    assert len(validation["warnings"]) == 1
    assert validation["warnings_total"] >= 1
    if validation["warnings_total"] > 1:
        assert validation["warnings_truncated"] is True
    # The full record shape is preserved under --warnings full.
    record = validation["warnings"][0]
    assert {"severity", "message"} <= set(record)


def test_cli_and_mcp_grouping_parity() -> None:
    """Feeding identical record lists to the shared grouping utility yields
    identical payloads — the single-source-of-truth guarantee for #132."""
    from ontos.core.warning_groups import group_warning_records, groups_to_payload

    records = [
        _orphan_warning("kernel_doc", "docs/kernel/kernel_doc.md").to_dict(),
        {"severity": "warning", "rule_id": "schema.log_missing_fields",
         "message": "Log missing fields: date"},
    ]
    cli_payload = groups_to_payload(group_warning_records(list(records)))
    mcp_payload = groups_to_payload(group_warning_records(list(records)))
    assert cli_payload == mcp_payload


# =============================================================================
# (#134) Allowlisted external file dependencies land in the info bucket
# =============================================================================


def _external_dep_workspace(root: Path) -> Path:
    _write(
        root / ".ontos.toml",
        """
        [ontos]
        version = "4.6"

        [validation]
        allowed_orphan_types = ["atom", "log"]
        allowed_external_dependency_paths = ["external/**"]
        """,
    )
    _write(root / "external/notes.txt", "not a doc\n")
    _write(
        root / "docs/anchor.md",
        """
        ---
        id: anchor_doc
        type: atom
        status: active
        depends_on: [external/notes.txt]
        ---
        Anchor body.
        """,
    )
    return root


def test_activate_json_allowlisted_dep_lands_in_info_not_warnings(tmp_path: Path) -> None:
    root = _external_dep_workspace(tmp_path)

    result = _run(root, "--json", "activate", "--warnings", "full")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    validation = payload["data"]["validation"]
    assert validation["info"], "expected the allowlisted dep in validation.info"
    record = validation["info"][0]
    assert record["rule_id"] == "external_file_dependency"
    assert record["severity"] == "info"
    assert record["document_id"] == "anchor_doc"
    assert payload["data"]["summary"]["validation_info"] == 1

    # The allowlisted dep must NOT appear among warnings or flip status.
    assert all(
        w.get("rule_id") != "external_file_dependency" for w in validation["warnings"]
    )
    # atom is an allowed orphan type, so the workspace is fully clean -> usable.
    assert payload["data"]["status"] == "usable"
    assert payload["data"]["summary"]["validation_warnings"] == 0


def test_activate_json_info_groups_follow_warning_budget(tmp_path: Path) -> None:
    root = _external_dep_workspace(tmp_path)

    result = _run(root, "--json", "activate")  # default grouped mode
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    validation = payload["data"]["validation"]
    assert validation["info"] == []  # inline records only in full mode
    assert validation["info_total"] == 1
    groups = validation["info_groups"]
    assert len(groups) == 1
    assert groups[0]["rule_id"] == "external_file_dependency"
    assert groups[0]["count"] == 1
    assert groups[0]["samples"]


def test_activate_json_rejects_invalid_limit_with_envelope(tmp_path: Path) -> None:
    """(#138 review) --limit < 1 must fail inside the JSON envelope, not as
    plain text on stdout."""
    root = _orphan_workspace(tmp_path)

    for bad in ("0", "-1"):
        result = _run(root, "--json", "activate", "--limit", bad)
        assert result.returncode == 1
        envelope = json.loads(result.stdout)  # stdout must stay valid JSON
        assert envelope["command"] == "activate"
        assert envelope["status"] == "error"
        assert envelope["error"]["code"] == "E_USER_INPUT"
        assert "--limit" in envelope["message"]

    human = _run(root, "activate", "--limit", "0")
    assert human.returncode == 1
    assert "--limit must be >= 1" in human.stdout


def test_activate_warning_rule_filters_info_total(tmp_path: Path) -> None:
    """(#140 review) --warning-rule must filter info_total/info_groups the
    same way it filters warnings_total."""
    root = _external_dep_workspace(tmp_path)

    result = _run(root, "--json", "activate", "--warning-rule", "orphan")
    assert result.returncode == 0, result.stderr
    validation = json.loads(result.stdout)["data"]["validation"]

    # The only info record is external_file_dependency; under an orphan
    # filter the info channel must be empty AND its total must say so.
    assert validation["info"] == []
    assert validation["info_groups"] == []
    assert validation["info_total"] == 0

    matching = _run(
        root, "--json", "activate", "--warning-rule", "external_file_dependency"
    )
    validation = json.loads(matching.stdout)["data"]["validation"]
    assert validation["info_total"] == 1
    assert validation["info_groups"][0]["rule_id"] == "external_file_dependency"
