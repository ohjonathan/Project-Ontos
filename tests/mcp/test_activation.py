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


# =============================================================================
# (#132) Grouped activation warnings + list_validation_warnings pagination
# =============================================================================


def test_activate_returns_grouped_warnings_with_empty_inline_list(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    activation = _call(server, "activate", {})

    assert activation.isError is False
    content = activation.structuredContent
    # Orientation fields stay at the top of the declared schema.
    assert list(content)[:6] == [
        "status", "workspace", "workspace_path", "doc_count",
        "loaded_ids", "recommendation",
    ]
    assert content["warnings"] == []
    assert isinstance(content["warnings_total"], int)
    if content["warnings_total"]:
        assert content["warnings_truncated"] is True
        groups = content["warning_groups"]
        assert sum(group["count"] for group in groups) == content["warnings_total"]
        for group in groups:
            assert len(group["samples"]) <= 3
            for sample in group["samples"]:
                assert {"severity", "message"} <= set(sample)
    else:
        assert content["warnings_truncated"] is False
        assert content["warning_groups"] == []


def test_activate_summary_mode_has_empty_samples(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    activation = _call(server, "activate", {"warnings": "summary"})

    assert activation.isError is False
    for group in activation.structuredContent["warning_groups"]:
        assert group["samples"] == []


def test_activate_rejects_full_warnings_mode(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(server, "activate", {"warnings": "full"})

    assert result.isError is True
    text = result.content[0].text
    assert "E_INVALID_WARNINGS_MODE" in text or "list_validation_warnings" in text


def test_list_validation_warnings_pages_full_records(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)
    _call(server, "activate", {})

    full = _call(server, "list_validation_warnings", {})
    assert full.isError is False
    content = full.structuredContent
    assert content["offset"] == 0
    assert content["total_count"] == len(content["warnings"]) or (
        content["total_count"] > len(content["warnings"])
    )
    total = content["total_count"]
    # Record shape parity with activate samples / CLI records.
    for record in content["warnings"]:
        assert {"severity", "message"} <= set(record)

    if total > 1:
        page = _call(
            server, "list_validation_warnings", {"offset": 1, "limit": 1}
        ).structuredContent
        assert page["offset"] == 1
        assert len(page["warnings"]) == 1
        assert page["total_count"] == total
        assert page["warnings"][0] == content["warnings"][1]


def test_list_validation_warnings_filters_by_rule_id(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)
    _call(server, "activate", {})

    full = _call(server, "list_validation_warnings", {}).structuredContent
    rules = {record.get("rule_id") for record in full["warnings"]}
    if not rules:
        return  # clean fixture; nothing to filter
    rule = next(iter(r for r in rules if r))
    filtered = _call(
        server, "list_validation_warnings", {"rule_id": rule}
    ).structuredContent
    assert filtered["warnings"], f"expected records for rule {rule}"
    assert all(record["rule_id"] == rule for record in filtered["warnings"])
    assert filtered["total_count"] <= full["total_count"]


def test_list_validation_warnings_rejects_bad_pagination(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    bad_offset = _call(server, "list_validation_warnings", {"offset": -1})
    assert bad_offset.isError is True
    bad_limit = _call(server, "list_validation_warnings", {"limit": 0})
    assert bad_limit.isError is True
    too_big = _call(server, "list_validation_warnings", {"limit": 501})
    assert too_big.isError is True


def test_list_validation_warnings_carries_pre_activate_warning(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(server, "list_validation_warnings", {})

    assert result.isError is False
    assert result.structuredContent["_ontos_warning"] == (
        "Ontos activation not performed this MCP session; call activate first."
    )


def test_mcp_groups_match_cli_grouping_for_same_records(tmp_path):
    """The MCP activate warning_groups are exactly what the shared core
    utility produces for the same normalized record list (#132 parity)."""
    from ontos.core.warning_groups import group_warning_records, groups_to_payload
    from ontos.mcp.tools import _normalize_warnings
    from tests.mcp import build_cache

    cache = build_cache(create_workspace(tmp_path))
    from ontos.mcp import tools

    payload = tools.activate(cache)
    view = cache.get_fresh_view()
    records = _normalize_warnings(
        view.snapshot.validation_result, view.snapshot.warnings
    )
    expected = groups_to_payload(group_warning_records(records))
    assert payload["warning_groups"] == expected
    assert payload["warnings_total"] == len(records)


# =============================================================================
# (#134) Info bucket (allowlisted external file deps) on the MCP surface
# =============================================================================


def test_activate_emits_info_groups_separate_from_warnings(tmp_path):
    root = create_workspace(tmp_path)
    # Add an allowlisted external file dep to the fixture workspace.
    (root / "apps").mkdir(exist_ok=True)
    (root / "apps" / "real.py").write_text("code", encoding="utf-8")
    config_path = root / ".ontos.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        + "\n[validation]\nallowed_external_dependency_paths = ['apps/**']\n",
        encoding="utf-8",
    )
    (root / "docs" / "with_file_dep.md").write_text(
        "---\nid: with_file_dep\ntype: atom\nstatus: active\n"
        "depends_on: [apps/real.py]\n---\nBody\n",
        encoding="utf-8",
    )
    server = build_server(root)

    activation = _call(server, "activate", {})

    assert activation.isError is False
    content = activation.structuredContent
    assert content["info_total"] == 1
    assert content["info_groups"][0]["rule_id"] == "external_file_dependency"
    assert content["info_groups"][0]["by_severity"] == {"info": 1}
    # Info never merges into the warning channel or its totals.
    rule_ids = {group["rule_id"] for group in content["warning_groups"]}
    assert "external_file_dependency" not in rule_ids


def test_list_validation_warnings_pages_info_records(tmp_path):
    root = create_workspace(tmp_path)
    (root / "apps").mkdir(exist_ok=True)
    (root / "apps" / "real.py").write_text("code", encoding="utf-8")
    config_path = root / ".ontos.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        + "\n[validation]\nallowed_external_dependency_paths = ['apps/**']\n",
        encoding="utf-8",
    )
    (root / "docs" / "with_file_dep.md").write_text(
        "---\nid: with_file_dep\ntype: atom\nstatus: active\n"
        "depends_on: [apps/real.py]\n---\nBody\n",
        encoding="utf-8",
    )
    server = build_server(root)
    _call(server, "activate", {})

    result = _call(server, "list_validation_warnings", {"severity": "info"})

    assert result.isError is False
    records = result.structuredContent["warnings"]
    assert records
    assert all(record["severity"] == "info" for record in records)
    assert records[0]["rule_id"] == "external_file_dependency"


def test_snapshot_issue_classifies_external_file_dependency_prefix():
    issue = _snapshot_issue(
        "External file dependency (allowlisted): 'apps/real.py' "
        "(declared in handoff) resolved to 'apps/real.py'."
    )
    assert issue["rule_id"] == "external_file_dependency"
