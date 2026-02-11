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


from ontos.io.files import load_documents

def test_loader_duplicate_contract_deterministic_first_wins(tmp_path):
    """Verify that lexicographically first path wins for collisions."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    
    # Create two files with same ID
    # Path 'a.md' comes before 'b.md'
    (docs_dir / "b.md").write_text("---\nid: collision\ntype: atom\n---\nDoc B")
    (docs_dir / "a.md").write_text("---\nid: collision\ntype: atom\n---\nDoc A")
    
    files = list(docs_dir.glob("*.md"))
    load_result = load_documents(files, parse_frontmatter_content)
    
    # Deterministic first-wins means 'a.md' content wins
    assert load_result.documents["collision"].filepath.name == "a.md"
    assert "Doc A" in load_result.documents["collision"].content

def test_loader_duplicate_contract_collision_reporting(tmp_path):
    """Verify duplicate_ids and issues contain correct collision data."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    
    (docs_dir / "a.md").write_text("---\nid: collision\ntype: atom\n---\n")
    (docs_dir / "b.md").write_text("---\nid: collision\ntype: atom\n---\n")
    (docs_dir / "c.md").write_text("---\nid: collision\ntype: atom\n---\n")
    
    files = list(docs_dir.glob("*.md"))
    load_result = load_documents(files, parse_frontmatter_content)
    
    assert "collision" in load_result.duplicate_ids
    # All 3 paths should be tracked
    assert len(load_result.duplicate_ids["collision"]) == 3
    
    duplicate_issues = [i for i in load_result.issues if i.code == "duplicate_id"]
    assert len(duplicate_issues) >= 1
    assert "collision" in duplicate_issues[0].message

def test_loader_duplicate_contract_no_crash_resilience(tmp_path):
    """Verify that non-duplicate docs still load successfully in same batch."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    
    (docs_dir / "a.md").write_text("---\nid: collision\ntype: atom\n---\n")
    (docs_dir / "b.md").write_text("---\nid: collision\ntype: atom\n---\n")
    (docs_dir / "valid.md").write_text("---\nid: valid_doc\ntype: atom\n---\n")
    
    files = list(docs_dir.glob("*.md"))
    load_result = load_documents(files, parse_frontmatter_content)
    
    assert "collision" in load_result.documents
    assert "valid_doc" in load_result.documents
    assert len(load_result.documents) == 2


def test_lstrip_frontmatter_detection_with_leading_whitespace(tmp_path):
    """VUL-04: Verify that leading whitespace before --- is handled leniently."""
    from ontos.io.yaml import parse_frontmatter_content
    from ontos.io.files import load_document_from_content
    content = "\n\n---\nid: lstrip_test\ntype: atom\n---\nBody content"
    path = tmp_path / "lstrip_test.md"
    path.write_text(content)

    doc, issues = load_document_from_content(path, content, parse_frontmatter_content)

    # The lstrip behavior means this IS detected as having frontmatter
    assert doc.id == "lstrip_test"


def test_loader_duplicate_detection_is_case_sensitive(tmp_path):
    """VUL-11: IDs differing only in case should be treated as distinct."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "lower.md").write_text("---\nid: my_doc\ntype: atom\n---\n")
    (docs_dir / "upper.md").write_text("---\nid: MY_DOC\ntype: atom\n---\n")

    files = list(docs_dir.glob("*.md"))
    load_result = load_documents(files, parse_frontmatter_content)

    # Both should load — they are NOT duplicates
    assert "my_doc" in load_result.documents
    assert "MY_DOC" in load_result.documents
    assert len(load_result.duplicate_ids) == 0
