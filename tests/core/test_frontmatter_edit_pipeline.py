from __future__ import annotations

import pytest

from ontos.core.frontmatter_edit import patch_frontmatter_fields
from ontos.io.yaml import parse_frontmatter_content


def test_patch_preserves_bom_crlf_comments_quoting_and_body() -> None:
    original = (
        "\ufeff---\r\n"
        "# retained header\r\n"
        "id: preserved_doc\r\n"
        "title: \"2026-07-10 # literal\"\r\n"
        "status: draft\r\n"
        "---\r\n"
        "Body with a delimiter:\r\n---\r\n"
    )

    updated = patch_frontmatter_fields(
        original,
        {"status": "active", "depends_on": ["alpha, beta", "#hash"]},
    )

    assert updated.startswith("\ufeff---\r\n# retained header\r\n")
    assert 'title: "2026-07-10 # literal"\r\n' in updated
    assert "Body with a delimiter:\r\n---\r\n" in updated
    assert "\n" not in updated.replace("\r\n", "")
    frontmatter, body = parse_frontmatter_content(updated.removeprefix("\ufeff"))
    assert frontmatter["status"] == "active"
    assert frontmatter["depends_on"] == ["alpha, beta", "#hash"]
    assert body == "Body with a delimiter:\r\n---\r\n"


def test_patch_preserves_indented_frontmatter_block_delimiter() -> None:
    original = "---\nid: block_doc\nsummary: |\n  phase --- two\nstatus: draft\n---\nbody\n"
    updated = patch_frontmatter_fields(original, {"status": "active"})
    assert "summary: |\n  phase --- two\n" in updated
    frontmatter, body = parse_frontmatter_content(updated)
    assert frontmatter["summary"] == "phase --- two\n"
    assert body == "body\n"


def test_patch_rejects_duplicate_target_field() -> None:
    content = "---\nid: duplicate\nstatus: draft\nstatus: active\n---\n"
    with pytest.raises(ValueError, match="more than once"):
        patch_frontmatter_fields(content, {"status": "active"})


def test_patch_preserves_comment_on_changed_field() -> None:
    content = "---\nid: commented\nstatus: draft # explain why\n---\n"
    updated = patch_frontmatter_fields(content, {"status": "active"})
    assert "status: active # explain why\n" in updated
    frontmatter, _ = parse_frontmatter_content(updated)
    assert frontmatter["status"] == "active"


def test_patch_rejects_comment_inside_rewritten_collection() -> None:
    content = "---\nid: commented\ndepends_on:\n  - old # keep\n---\n"
    with pytest.raises(ValueError, match="collection comment"):
        patch_frontmatter_fields(content, {"depends_on": ["new"]})
