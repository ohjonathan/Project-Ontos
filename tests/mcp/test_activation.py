"""MCP activation contract tests."""

from __future__ import annotations

import asyncio

from ontos.core.types import ValidationError, ValidationErrorType
from ontos.mcp.tools import _snapshot_issue, _validation_issues

from tests.mcp import build_server, create_workspace


def _call(server, name: str, args: dict):
    return asyncio.run(server.call_tool(name, args))


def test_activate_sets_session_state_and_returns_loaded_ids(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    activation = _call(server, "activate", {})
    overview = _call(server, "workspace_overview", {})

    assert activation.isError is False
    assert activation.structuredContent["status"] in {"usable", "usable_with_warnings"}
    assert activation.structuredContent["workspace"] == root.name
    assert activation.structuredContent["doc_count"] == 8
    assert activation.structuredContent["loaded_ids"]
    assert "_ontos_warning" not in activation.structuredContent
    assert "_ontos_warning" not in overview.structuredContent


def test_read_tool_warns_when_activation_was_skipped(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(server, "workspace_overview", {})

    assert result.isError is False
    assert result.structuredContent["_ontos_warning"] == (
        "Ontos activation not performed this MCP session; call activate first."
    )


def test_get_context_bundle_pre_activate_warning_lands_in_warnings_list(tmp_path):
    # #115: `get_context_bundle` declares `warnings: List[str]` with
    # `additionalProperties: false`. The pre-activate reminder must land in
    # that list, not as an undeclared `_ontos_warning` key (which the MCP SDK
    # rejects against the strict output schema).
    root = create_workspace(tmp_path)
    server = build_server(root, include_bundle_tool=True)

    result = _call(server, "get_context_bundle", {"token_budget": 8192})

    assert result.isError is False
    assert "_ontos_warning" not in result.structuredContent
    warnings = result.structuredContent["warnings"]
    assert isinstance(warnings, list)
    assert "Ontos activation not performed this MCP session; call activate first." in warnings


def test_get_context_bundle_no_warning_after_activate(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root, include_bundle_tool=True)

    _call(server, "activate", {})
    result = _call(server, "get_context_bundle", {"token_budget": 8192})

    assert result.isError is False
    assert "_ontos_warning" not in result.structuredContent
    warnings = result.structuredContent["warnings"]
    assert "Ontos activation not performed this MCP session; call activate first." not in warnings


def test_validation_issues_enriches_with_rule_id_document_id_file_path():
    # (#117) Warnings emitted from ValidationError instances should surface
    # rule_id (from error_type.value), document_id (doc_id), and file_path so
    # downstream agents can triage without a second query.
    errors = [
        ValidationError(
            error_type=ValidationErrorType.ORPHAN,
            doc_id="model_a_bronze_sourcepacket_review",
            filepath="docs/reviews/model_a_bronze_sourcepacket_review.md",
            message="Document has no incoming dependencies",
            fix_suggestion="Add this document to another document's depends_on",
            severity="warning",
        ),
        ValidationError(
            error_type=ValidationErrorType.OUT_OF_SCOPE_DEPENDENCY,
            doc_id="meta-orchestrator-kickoff",
            filepath="docs/handoffs/orchestrator.md",
            message="External dependency resolved from disk: '.llm-dev/framework/framework.md' (declared in meta-orchestrator-kickoff) exists at '.llm-dev/framework/framework.md' but is not a loaded document.",
            fix_suggestion="",
            severity="warning",
        ),
    ]

    issues = _validation_issues(errors)

    assert issues[0]["severity"] == "warning"
    assert issues[0]["rule_id"] == "orphan"
    assert issues[0]["document_id"] == "model_a_bronze_sourcepacket_review"
    assert issues[0]["file_path"] == "docs/reviews/model_a_bronze_sourcepacket_review.md"
    assert issues[1]["rule_id"] == "out_of_scope_dependency"
    assert issues[1]["document_id"] == "meta-orchestrator-kickoff"


def test_validation_issues_drops_empty_context_fields():
    # Bare ValidationError instances with no doc_id / filepath stay compact
    # (no empty-string fields leaking into the payload).
    issue = ValidationError(
        error_type=ValidationErrorType.CYCLE,
        doc_id="",
        filepath="",
        message="Circular dependency: a -> b -> a",
        fix_suggestion="",
        severity="error",
    )

    [record] = _validation_issues([issue])

    assert record["rule_id"] == "cycle"
    assert record["severity"] == "error"
    assert "document_id" not in record
    assert "file_path" not in record


def test_snapshot_issue_classifies_well_known_prefixes():
    # (#117) Bare snapshot strings get a rule_id based on their leading
    # prefix, so the warning channel is parseable.
    assert _snapshot_issue("Log missing fields: branch")["rule_id"] == "schema.log_missing_fields"
    assert _snapshot_issue("Broken dependency: 'x' (declared in y) does not exist")["rule_id"] == "broken_link"
    assert _snapshot_issue("Document has no incoming dependencies")["rule_id"] == "orphan"
    assert _snapshot_issue("Dependency depth 8 exceeds max 5")["rule_id"] == "depth"
    # Unknown shape falls back to a generic snapshot rule_id.
    assert _snapshot_issue("Completely novel message")["rule_id"] == "snapshot"
