"""Frontmatter diagnostic and enum repair tests."""

from __future__ import annotations

from textwrap import dedent

from ontos.core.frontmatter_repair import apply_enum_repair_plan, build_enum_repair_plan
from ontos.io.files import load_documents
from ontos.io.yaml import parse_frontmatter_content


_CANONICAL_TYPES = [
    "kernel",
    "strategy",
    "product",
    "atom",
    "log",
    "reference",
    "concept",
    "handoff",
    "tracker",
    "retro",
    "review",
    "spec",
    "report",
    "adr",
    "policy",
    "unknown",
]

_CANONICAL_STATUSES = [
    "draft",
    "active",
    "deprecated",
    "archived",
    "rejected",
    "complete",
    "auto-generated",
    "scaffold",
    "pending_curation",
    "in_progress",
    "proposed",
    "ready",
    "completed",
    "revised",
    "in-lifecycle",
    "unknown",
]


def test_invalid_enum_diagnostic_payload_includes_precise_fields(tmp_path):
    # (#117) `review` and `completed` are now canonical values; use truly
    # unknown values (`meeting`, `waiting`) to exercise the invalid-enum
    # path. The allowed_values list reflects the widened vocabulary so
    # downstream tooling sees the new options.
    path = tmp_path / "docs" / "review.md"
    path.parent.mkdir()
    path.write_text(
        dedent(
            """
            ---
            id: review_doc
            type: meeting
            status: waiting
            ---
            Review body.
            """
        ).lstrip(),
        encoding="utf-8",
    )

    result = load_documents([path], parse_frontmatter_content)
    payloads = [issue.to_dict(root=tmp_path) for issue in result.issues]
    types_allowed = ", ".join(_CANONICAL_TYPES)
    statuses_allowed = ", ".join(_CANONICAL_STATUSES)

    assert payloads == [
        {
            "code": "invalid_enum",
            "path": "docs/review.md",
            "line": 3,
            "doc_id": "review_doc",
            "field": "type",
            "observed_value": "meeting",
            "allowed_values": _CANONICAL_TYPES,
            "suggested_fix": (
                f"Change 'type' to one of: {types_allowed}. "
                "Preserve the old value as original_type if it carries lifecycle nuance."
            ),
            "severity": "warning",
            "blocking": False,
            "message": (
                f"{path}:3: invalid frontmatter field 'type' value 'meeting'. "
                f"Expected one of: {types_allowed}"
            ),
        },
        {
            "code": "invalid_enum",
            "path": "docs/review.md",
            "line": 4,
            "doc_id": "review_doc",
            "field": "status",
            "observed_value": "waiting",
            "allowed_values": _CANONICAL_STATUSES,
            "suggested_fix": (
                f"Change 'status' to one of: {statuses_allowed}. "
                "Preserve the old value as original_status if it carries lifecycle nuance."
            ),
            "severity": "warning",
            "blocking": False,
            "message": (
                f"{path}:4: invalid frontmatter field 'status' value 'waiting'. "
                f"Expected one of: {statuses_allowed}"
            ),
        },
    ]


def test_canonical_lifecycle_values_load_clean_without_diagnostics(tmp_path):
    # (#117) `type: review` + `status: completed` are now first-class
    # canonical values — no diagnostic should fire and conservative repair
    # should not coerce them.
    path = tmp_path / "docs" / "review.md"
    path.parent.mkdir()
    path.write_text(
        dedent(
            """
            ---
            id: review_doc
            type: review
            status: completed
            ---
            Review body.
            """
        ).lstrip(),
        encoding="utf-8",
    )

    result = load_documents([path], parse_frontmatter_content)
    assert result.issues == []
    doc = result.documents["review_doc"]
    assert doc.type.value == "review"
    assert doc.status.value == "completed"


def test_enum_repair_plan_maps_known_lifecycle_values_and_reports_unknowns(tmp_path):
    # `proposal` is still aliased (not canonical); `final-report` redirects
    # to the new canonical `report` type. Truly unknown values are unresolved.
    repairable = tmp_path / "repairable.md"
    unresolved = tmp_path / "unresolved.md"
    repairable.write_text(
        "---\nid: repairable\ntype: proposal\nstatus: passed\n---\n",
        encoding="utf-8",
    )
    unresolved.write_text(
        "---\nid: unresolved\ntype: meeting\nstatus: waiting\n---\n",
        encoding="utf-8",
    )

    plan = build_enum_repair_plan([repairable, unresolved])
    edits = {(edit.path.name, edit.field): edit for edit in plan.edits}

    assert edits[("repairable.md", "type")].repairable is True
    assert edits[("repairable.md", "type")].new_value == "strategy"
    assert edits[("repairable.md", "status")].repairable is True
    assert edits[("repairable.md", "status")].new_value == "complete"
    assert edits[("unresolved.md", "type")].repairable is False
    assert edits[("unresolved.md", "status")].repairable is False


def test_extended_canonical_aliases_map_to_new_first_class_types(tmp_path):
    # `retrospective` → `retro` (was `log`), `final-report` → `report`
    # (was `log`). New canonical types receive the alias instead of
    # collapsing into `log`.
    path = tmp_path / "doc.md"
    path.write_text(
        "---\nid: doc\ntype: retrospective\nstatus: done\n---\n",
        encoding="utf-8",
    )
    plan = build_enum_repair_plan([path])
    edits = {edit.field: edit for edit in plan.edits}

    assert edits["type"].repairable is True
    assert edits["type"].new_value == "retro"
    assert edits["status"].repairable is True
    assert edits["status"].new_value == "complete"


def test_enum_repair_preserves_case_inline_comments_and_crlf(tmp_path):
    path = tmp_path / "docs" / "case.md"
    path.parent.mkdir()
    path.write_bytes(
        b"---\r\nid: case_doc\r\ntype: Proposal # rationale\r\n"
        b"status: DONE # workflow\r\n---\r\nBody\r\n"
    )

    plan = build_enum_repair_plan([path])
    assert len(plan.repairable_edits) == 2
    apply_enum_repair_plan(plan, repo_root=tmp_path)

    updated = path.read_bytes().decode("utf-8")
    assert "type: strategy # rationale\r\n" in updated
    assert "status: complete # workflow\r\n" in updated
    assert "original_type: Proposal\r\n" in updated
    assert "original_status: DONE\r\n" in updated
    assert "\n" not in updated.replace("\r\n", "")


def _write_doc(tmp_path, name, doc_type, status):
    path = tmp_path / "docs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        dedent(
            f"""
            ---
            id: {name.removesuffix('.md')}
            type: {doc_type}
            status: {status}
            ---
            Body.
            """
        ).lstrip(),
        encoding="utf-8",
    )
    return path


def test_builtin_in_progress_alias_is_repairable(tmp_path):
    # (#178 / plan §11.4) The hyphenated spelling of the canonical
    # `in_progress` status must repair without any configuration.
    path = _write_doc(tmp_path, "wip.md", "log", "in-progress")

    plan = build_enum_repair_plan([path])

    assert len(plan.edits) == 1
    edit = plan.edits[0]
    assert edit.repairable is True
    assert edit.new_value == "in_progress"
    assert edit.source == "built-in"


def test_config_aliases_make_project_values_repairable(tmp_path):
    # The issue's reproduced pain: values like `runbook` and
    # `provider_limited_fallback_complete` were 0-repairable.
    path = _write_doc(
        tmp_path, "runbook.md", "runbook", "provider_limited_fallback_complete"
    )

    plan = build_enum_repair_plan(
        [path],
        type_aliases={"runbook": "reference"},
        status_aliases={"provider_limited_fallback_complete": "complete"},
    )

    by_field = {edit.field: edit for edit in plan.edits}
    assert by_field["type"].new_value == "reference"
    assert by_field["type"].source == "config"
    assert by_field["status"].new_value == "complete"
    assert by_field["status"].source == "config"
    assert plan.unresolved_edits == []


def test_config_alias_wins_over_builtin(tmp_path):
    # Built-in maps halted -> rejected; a project may decide differently.
    path = _write_doc(tmp_path, "halted.md", "log", "halted")

    plan = build_enum_repair_plan(
        [path], status_aliases={"halted": "archived"}
    )

    assert plan.edits[0].new_value == "archived"
    assert plan.edits[0].source == "config"


def test_unmapped_value_stays_unresolved_with_alias_hint(tmp_path):
    path = _write_doc(tmp_path, "odd.md", "log", "backlog")

    plan = build_enum_repair_plan([path])

    assert len(plan.unresolved_edits) == 1
    edit = plan.unresolved_edits[0]
    assert edit.new_value is None
    assert edit.source is None
    assert "[frontmatter.aliases.status]" in edit.reason


def test_config_alias_apply_preserves_original_value(tmp_path):
    path = _write_doc(tmp_path, "wip2.md", "log", "in-progress")

    plan = build_enum_repair_plan([path])
    apply_enum_repair_plan(plan, repo_root=tmp_path)

    content = path.read_text(encoding="utf-8")
    assert "status: in_progress" in content
    assert "original_status: in-progress" in content
