"""Focused regressions for context-map Recent Activity rendering."""

from pathlib import Path
from typing import Optional

from ontos.commands.map import (
    _extract_recent_activity_summary,
    _generate_tiered_compact_output,
    _generate_tier1_summary,
    _generate_timeline,
    _log_date_sort_key,
    GenerateMapOptions,
)
from ontos.core.types import DocumentData, DocumentStatus, DocumentType


def _log(
    doc_id: str,
    *,
    content: str = "",
    summary=...,
    date: Optional[str] = None,
    created: Optional[str] = None,
) -> DocumentData:
    frontmatter = {}
    if summary is not ...:
        frontmatter["summary"] = summary
    if date is not None:
        frontmatter["date"] = date
    if created is not None:
        frontmatter["created"] = created
    return DocumentData(
        id=doc_id,
        type=DocumentType.LOG,
        status=DocumentStatus.ACTIVE,
        filepath=Path(f"docs/logs/{doc_id}.md"),
        frontmatter=frontmatter,
        content=content,
    )


def test_explicit_frontmatter_summary_wins_over_body() -> None:
    doc = _log(
        "explicit",
        summary="  Frontmatter\nsummary  ",
        content="# Heading\n\nBody summary that must not win.",
    )

    assert _extract_recent_activity_summary(doc) == "Frontmatter summary"


def test_body_fallback_skips_headings_comments_and_generated_placeholders() -> None:
    doc = _log(
        "body_fallback",
        content="""# Session title

<!-- generated note
that spans lines -->

## Goal

TODO: expand this scaffold.

### Summary

The first substantive body text.
The second body line.
""",
    )

    assert (
        _extract_recent_activity_summary(doc)
        == "The first substantive body text. The second body line."
    )


def test_null_summary_uses_body_but_explicit_empty_summary_remains_authoritative() -> None:
    body = "# Goal\n\nBody fallback"

    assert (
        _extract_recent_activity_summary(_log("null", summary=None, content=body))
        == "Body fallback"
    )
    assert _extract_recent_activity_summary(_log("empty", summary="", content=body)) == ""


def test_noise_only_body_falls_back_to_no_summary() -> None:
    doc = _log(
        "noise",
        content="# Heading\n\n<!-- Untouched placeholder -->\n\n[placeholder]\n\n---\n",
    )

    assert _extract_recent_activity_summary(doc) == "No summary"


def test_body_fallback_skips_setext_heading() -> None:
    doc = _log(
        "setext",
        content="Session title\n=============\n\nSubstantive summary text.",
    )

    assert _extract_recent_activity_summary(doc) == "Substantive summary text."


def test_recent_activity_summary_is_capped_at_200_characters() -> None:
    summary = _extract_recent_activity_summary(_log("long", content="x" * 250))

    assert len(summary) == 200
    assert summary == "x" * 197 + "..."


def test_recent_activity_sort_order_is_date_then_created_then_id() -> None:
    logs = [
        _log("id_only"),
        _log("created_only", created="2026-12-31"),
        _log("dated_new", date="2026-07-03", created="2020-01-01"),
        _log("dated_old", date="2026-07-01", created="2030-01-01"),
        _log("a_tie", date="2026-07-02", created="2026-07-01"),
        _log("z_tie", date="2026-07-02", created="2026-07-01"),
        _log("created_tiebreak", date="2026-07-02", created="2026-07-02"),
    ]

    ordered = sorted(logs, key=_log_date_sort_key, reverse=True)

    assert [doc.id for doc in ordered] == [
        "created_only",
        "dated_new",
        "created_tiebreak",
        "z_tie",
        "a_tie",
        "dated_old",
        "id_only",
    ]


def test_tier1_recent_activity_uses_body_summary_and_escapes_table_pipes() -> None:
    content = _generate_tier1_summary(
        {
            "body": _log(
                "body",
                created="2026-07-14",
                content="# Session\n\nDelivered map | summary fallback.",
            )
        },
        {
            "project_name": "Test",
            "project_root": "/tmp/test",
            "docs_dir": "docs",
            "logs_dir": "docs/logs",
        },
    )

    assert "| body | active | Delivered map \\| summary fallback. |" in content


def test_created_fallback_order_is_shared_by_all_map_views() -> None:
    docs = {
        "dated_old": _log("dated_old", date="2026-01-01"),
        "created_new": _log("created_new", created="2026-07-14"),
    }
    config = {
        "project_name": "Test",
        "project_root": "/tmp/test",
        "docs_dir": "docs",
        "logs_dir": "docs/logs",
    }

    tier1 = _generate_tier1_summary(docs, config)
    timeline = _generate_timeline(docs)
    tiered = _generate_tiered_compact_output(docs, config, GenerateMapOptions())

    assert tier1.index("created_new") < tier1.index("dated_old")
    assert timeline.splitlines()[2] == "- `created_new`"
    assert "latest:created_new" in tiered
