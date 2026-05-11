"""Frontmatter diagnostic and enum repair tests."""

from __future__ import annotations

from textwrap import dedent

from ontos.core.frontmatter_repair import build_enum_repair_plan
from ontos.io.files import load_documents
from ontos.io.yaml import parse_frontmatter_content


def test_invalid_enum_diagnostic_payload_includes_precise_fields(tmp_path):
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
    payloads = [issue.to_dict(root=tmp_path) for issue in result.issues]

    assert payloads == [
        {
            "code": "invalid_enum",
            "path": "docs/review.md",
            "line": 3,
            "doc_id": "review_doc",
            "field": "type",
            "observed_value": "review",
            "allowed_values": [
                "kernel",
                "strategy",
                "product",
                "atom",
                "log",
                "reference",
                "concept",
                "unknown",
            ],
            "suggested_fix": (
                "Change 'type' to one of: kernel, strategy, product, atom, log, "
                "reference, concept, unknown. Preserve the old value as "
                "original_type if it carries lifecycle nuance."
            ),
            "severity": "warning",
            "blocking": False,
            "message": (
                f"{path}:3: invalid frontmatter field 'type' value 'review'. "
                "Expected one of: kernel, strategy, product, atom, log, "
                "reference, concept, unknown"
            ),
        },
        {
            "code": "invalid_enum",
            "path": "docs/review.md",
            "line": 4,
            "doc_id": "review_doc",
            "field": "status",
            "observed_value": "completed",
            "allowed_values": [
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
                "unknown",
            ],
            "suggested_fix": (
                "Change 'status' to one of: draft, active, deprecated, archived, "
                "rejected, complete, auto-generated, scaffold, pending_curation, "
                "in_progress, unknown. "
                "Preserve the old value as original_status if it carries lifecycle nuance."
            ),
            "severity": "warning",
            "blocking": False,
            "message": (
                f"{path}:4: invalid frontmatter field 'status' value 'completed'. "
                "Expected one of: draft, active, deprecated, archived, rejected, "
                "complete, auto-generated, scaffold, pending_curation, in_progress, unknown"
            ),
        },
    ]


def test_enum_repair_plan_maps_known_lifecycle_values_and_reports_unknowns(tmp_path):
    repairable = tmp_path / "repairable.md"
    unresolved = tmp_path / "unresolved.md"
    repairable.write_text(
        "---\nid: repairable\n.type: typo\n---\n",
        encoding="utf-8",
    )
    repairable.write_text(
        "---\nid: repairable\ntype: review\nstatus: completed\n---\n",
        encoding="utf-8",
    )
    unresolved.write_text(
        "---\nid: unresolved\ntype: meeting\nstatus: waiting\n---\n",
        encoding="utf-8",
    )

    plan = build_enum_repair_plan([repairable, unresolved])
    edits = {(edit.path.name, edit.field): edit for edit in plan.edits}

    assert edits[("repairable.md", "type")].repairable is True
    assert edits[("repairable.md", "type")].new_value == "log"
    assert edits[("repairable.md", "status")].repairable is True
    assert edits[("repairable.md", "status")].new_value == "complete"
    assert edits[("unresolved.md", "type")].repairable is False
    assert edits[("unresolved.md", "status")].repairable is False
