"""Tests for the canonical document loading contract (Track A1)."""
import pytest
from pathlib import Path
from ontos.io.files import load_document_from_content, DocumentLoadIssue
from ontos.io.yaml import parse_frontmatter_content
from ontos.core.types import DocumentType, DocumentStatus

def test_load_document_with_enum_coercion_failure(tmp_path):
    """Verify that invalid enum values produce issues instead of crashing."""
    content = """---
id: bad_enum
type: invalid_type
status: invalid_status
---
Body content"""
    path = tmp_path / "bad_enum.md"
    
    doc, issues = load_document_from_content(path, content, parse_frontmatter_content)
    
    assert doc.id == "bad_enum"
    # Fallback to KERNEL/DRAFT on failure (or whatever the coercion logic does)
    # The important part is the issues list
    assert any(i.code == "invalid_enum" for i in issues)
    assert any("type" in i.message.lower() for i in issues)
    assert any("status" in i.message.lower() for i in issues)

def test_load_document_with_invalid_references(tmp_path):
    """Verify that non-list/scalar references produce warnings."""
    content = """---
id: bad_refs
depends_on: { "not": "allowed" }
describes: { "not": "allowed" }
---
Body content"""
    path = tmp_path / "bad_refs.md"
    
    doc, issues = load_document_from_content(path, content, parse_frontmatter_content)
    
    assert any(i.code == "invalid_reference_type" for i in issues)
    assert any("depends_on" in i.message.lower() for i in issues)
    assert any("describes" in i.message.lower() for i in issues)

def test_load_document_with_mixed_describes(tmp_path):
    """Verify that non-string describes members produce warnings."""
    content = """---
id: mixed_describes
describes:
  - "valid_atom"
  - 123
---
Body content"""
    path = tmp_path / "mixed_describes.md"
    
    doc, issues = load_document_from_content(path, content, parse_frontmatter_content)
    
    assert any("Non-string member" in i.message for i in issues)
    # VUL-02: Ensure non-string target '123' is dropped, not coerced to "123"
    assert doc.describes == ["valid_atom"]
