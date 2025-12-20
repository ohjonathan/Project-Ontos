"""Tests for frontmatter parsing functionality."""

import pytest
from ontos_generate_context_map import parse_frontmatter


class TestParseFrontmatter:
    """Tests for parse_frontmatter function."""

    def test_valid_frontmatter(self, valid_kernel_doc):
        """Test parsing valid YAML frontmatter."""
        result = parse_frontmatter(str(valid_kernel_doc))
        assert result is not None
        assert result['id'] == 'mission'
        assert result['type'] == 'kernel'
        assert result['status'] == 'active'
        assert result['depends_on'] == []

    def test_frontmatter_with_dependencies(self, valid_atom_doc):
        """Test parsing frontmatter with dependencies."""
        result = parse_frontmatter(str(valid_atom_doc))
        assert result is not None
        assert result['id'] == 'api_spec'
        assert result['depends_on'] == ['mission']

    def test_missing_frontmatter(self, doc_without_frontmatter):
        """Test file without frontmatter returns None."""
        result = parse_frontmatter(str(doc_without_frontmatter))
        assert result is None

    def test_template_frontmatter(self, template_doc):
        """Test parsing template with underscore prefix."""
        result = parse_frontmatter(str(template_doc))
        assert result is not None
        assert result['id'] == '_template'

    def test_nonexistent_file(self, tmp_path):
        """Test parsing nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            parse_frontmatter(str(tmp_path / "nonexistent.md"))


class TestScanDocs:
    """Tests for scan_docs function."""

    def test_scan_valid_docs(self, temp_docs_dir, valid_kernel_doc, valid_atom_doc):
        """Test scanning directory with valid docs."""
        from ontos_generate_context_map import scan_docs

        result, warnings = scan_docs([str(temp_docs_dir)])
        assert len(result) == 2
        assert 'mission' in result
        assert 'api_spec' in result

    def test_skip_underscore_prefix(self, temp_docs_dir, template_doc):
        """Test that IDs starting with underscore are skipped."""
        from ontos_generate_context_map import scan_docs

        result, warnings = scan_docs([str(temp_docs_dir)])
        assert '_template' not in result

    def test_skip_missing_frontmatter(self, temp_docs_dir, doc_without_frontmatter):
        """Test that files without frontmatter are skipped."""
        from ontos_generate_context_map import scan_docs

        result, warnings = scan_docs([str(temp_docs_dir)])
        assert len(result) == 0

    def test_scan_multiple_directories(self, tmp_path):
        """Test scanning multiple directories."""
        from ontos_generate_context_map import scan_docs

        dir1 = tmp_path / "docs1"
        dir1.mkdir()
        (dir1 / "doc1.md").write_text("""---
id: doc1
type: atom
---
""")

        dir2 = tmp_path / "docs2"
        dir2.mkdir()
        (dir2 / "doc2.md").write_text("""---
id: doc2
type: atom
---
""")

        result, warnings = scan_docs([str(dir1), str(dir2)])
        assert len(result) == 2
        assert 'doc1' in result
        assert 'doc2' in result

    def test_scan_nonexistent_directory(self, tmp_path):
        """Test scanning nonexistent directory returns warning."""
        from ontos_generate_context_map import scan_docs

        result, warnings = scan_docs([str(tmp_path / "nonexistent")])
        assert any("Directory not found" in w for w in warnings)
        assert len(result) == 0
