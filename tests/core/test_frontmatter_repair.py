"""Frontmatter diagnostic and enum repair tests."""

from __future__ import annotations

from textwrap import dedent

from ontos.core.frontmatter_repair import build_enum_repair_plan
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
