"""Tests for frontmatter parsing functionality.

Updated for Phase 2/3: Uses ontos.core.frontmatter and ontos.io.yaml.
"""

import pytest
from ontos.core.frontmatter import parse_frontmatter
from ontos.io.yaml import parse_yaml


class TestParseFrontmatter:
    """Tests for parse_frontmatter function."""

    def test_valid_frontmatter(self, valid_kernel_doc):
        """Test parsing valid YAML frontmatter."""
        result = parse_frontmatter(str(valid_kernel_doc), yaml_parser=parse_yaml)
        assert result is not None
        assert result['id'] == 'mission'
        assert result['type'] == 'kernel'
        assert result['status'] == 'active'
        assert result['depends_on'] == []

    def test_frontmatter_with_dependencies(self, valid_atom_doc):
        """Test parsing frontmatter with dependencies."""
        result = parse_frontmatter(str(valid_atom_doc), yaml_parser=parse_yaml)
        assert result is not None
        assert result['id'] == 'api_spec'
        assert result['depends_on'] == ['mission']

    def test_missing_frontmatter(self, doc_without_frontmatter):
        """Test file without frontmatter returns None."""
        result = parse_frontmatter(str(doc_without_frontmatter), yaml_parser=parse_yaml)
        assert result is None

    def test_template_frontmatter(self, template_doc):
        """Test parsing template with underscore prefix."""
        result = parse_frontmatter(str(template_doc), yaml_parser=parse_yaml)
        assert result is not None
        assert result['id'] == '_template'

    def test_nonexistent_file(self, tmp_path):
        """Test parsing nonexistent file returns None (graceful degradation)."""
        # Note: parse_frontmatter returns None for missing files (doesn't raise)
        # This is the expected behavior for the dependency injection pattern
        result = parse_frontmatter(str(tmp_path / "nonexistent.md"), yaml_parser=parse_yaml)
        assert result is None


# Note: TestScanDocs was removed because scan_docs is no longer exported
# from the legacy script. The functionality is tested via integration tests.
