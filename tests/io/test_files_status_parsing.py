"""Regression tests for document status parsing in file loading."""

from pathlib import Path

from ontos.core.types import DocumentStatus
from ontos.io.files import load_document_from_content
from ontos.io.yaml import parse_frontmatter_content


def test_pending_curation_status_parses_to_enum():
    """pending_curation should not fall back to draft."""
    content = """---
id: pending_doc
type: atom
status: pending_curation
---
# Pending Curation
"""

    doc = load_document_from_content(
        path=Path("docs/pending_doc.md"),
        content=content,
        frontmatter_parser=parse_frontmatter_content,
    )

    assert doc.status == DocumentStatus.PENDING_CURATION
