"""Tests for YAML edge cases and null value handling."""

import pytest
from unittest.mock import patch
from ontos_generate_context_map import (
    normalize_depends_on,
    normalize_type,
    scan_docs,
    validate_dependencies
)

# Default orphan types (User Mode) - atoms should be flagged as orphans
DEFAULT_ALLOWED_ORPHAN_TYPES = ['product', 'strategy', 'kernel']


class TestNormalizeDependsOn:
    """Tests for normalize_depends_on function."""

    def test_none_value(self):
        """Test that None returns empty list."""
        assert normalize_depends_on(None) == []

    def test_empty_string(self):
        """Test that empty string returns empty list."""
        assert normalize_depends_on("") == []
        assert normalize_depends_on("   ") == []

    def test_single_string(self):
        """Test that single string returns list with one item."""
        assert normalize_depends_on("dep1") == ["dep1"]

    def test_list_of_strings(self):
        """Test that list of strings is preserved."""
        assert normalize_depends_on(["dep1", "dep2"]) == ["dep1", "dep2"]

    def test_list_with_none_values(self):
        """Test that None values in list are filtered."""
        assert normalize_depends_on(["dep1", None, "dep2"]) == ["dep1", "dep2"]

    def test_list_with_empty_strings(self):
        """Test that empty strings in list are filtered."""
        assert normalize_depends_on(["dep1", "", "dep2"]) == ["dep1", "dep2"]

    def test_mixed_list(self):
        """Test list with mixed None and empty values."""
        assert normalize_depends_on([None, "", "valid", "  ", None]) == ["valid"]

    def test_numeric_values_converted(self):
        """Test that numeric values are converted to strings."""
        result = normalize_depends_on([123, "dep"])
        assert result == ["123", "dep"]


class TestNormalizeType:
    """Tests for normalize_type function."""

    def test_none_value(self):
        """Test that None returns 'unknown'."""
        assert normalize_type(None) == "unknown"

    def test_empty_string(self):
        """Test that empty string returns 'unknown'."""
        assert normalize_type("") == "unknown"
        assert normalize_type("   ") == "unknown"

    def test_valid_type(self):
        """Test that valid type string is returned."""
        assert normalize_type("kernel") == "kernel"
        assert normalize_type("strategy") == "strategy"
        assert normalize_type("product") == "product"
        assert normalize_type("atom") == "atom"

    def test_type_with_whitespace(self):
        """Test that whitespace is stripped."""
        assert normalize_type("  atom  ") == "atom"

    def test_list_type(self):
        """Test that list type uses first element."""
        assert normalize_type(["kernel", "strategy"]) == "kernel"

    def test_list_with_none_first(self):
        """Test list with None as first element."""
        assert normalize_type([None, "atom"]) == "unknown"

    def test_empty_list(self):
        """Test empty list returns unknown."""
        assert normalize_type([]) == "unknown"

    def test_pipe_in_type(self):
        """Test that pipe character causes unknown."""
        assert normalize_type("kernel | strategy") == "unknown"
        assert normalize_type(["kernel | strategy"]) == "unknown"


class TestScanDocsWithNullValues:
    """Tests for scan_docs with YAML null/empty edge cases."""

    def test_null_depends_on(self, tmp_path):
        """Test file with null depends_on."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("""---
id: test_doc
type: atom
depends_on:
---
# Test
""")
        result, warnings = scan_docs([str(docs_dir)])
        assert "test_doc" in result
        assert result["test_doc"]["depends_on"] == []

    def test_null_type(self, tmp_path):
        """Test file with null type."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("""---
id: test_doc
type:
---
# Test
""")
        result, warnings = scan_docs([str(docs_dir)])
        assert "test_doc" in result
        assert result["test_doc"]["type"] == "unknown"

    def test_explicit_null_yaml(self, tmp_path):
        """Test file with explicit YAML null values."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("""---
id: test_doc
type: null
depends_on: null
status: null
---
# Test
""")
        result, warnings = scan_docs([str(docs_dir)])
        assert "test_doc" in result
        assert result["test_doc"]["type"] == "unknown"
        assert result["test_doc"]["depends_on"] == []
        assert result["test_doc"]["status"] == "unknown"

    def test_empty_id_skipped(self, tmp_path):
        """Test that documents with empty ID are skipped."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("""---
id:
type: atom
---
# Test
""")
        result, warnings = scan_docs([str(docs_dir)])
        assert len(result) == 0

    def test_whitespace_id_skipped(self, tmp_path):
        """Test that documents with whitespace-only ID are skipped."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("""---
id: "   "
type: atom
---
# Test
""")
        result, warnings = scan_docs([str(docs_dir)])
        assert len(result) == 0


class TestValidateDependenciesWithNullValues:
    """Tests for validate_dependencies with edge case data."""

    @patch('ontos_generate_context_map.ALLOWED_ORPHAN_TYPES', DEFAULT_ALLOWED_ORPHAN_TYPES)
    def test_empty_depends_on_no_crash(self):
        """Test that empty depends_on doesn't cause crash in User Mode."""
        files_data = {
            'test_doc': {
                'filepath': 'docs/test.md',
                'filename': 'test.md',
                'type': 'atom',
                'depends_on': [],  # Empty list (normalized from null)
                'status': 'active'
            }
        }
        # Should not raise any exception
        issues = validate_dependencies(files_data)
        # Should report as orphan since no dependents (in User Mode)
        assert any('[ORPHAN]' in issue for issue in issues)

    def test_normalized_string_dep_works(self):
        """Test that string deps are already normalized to list."""
        files_data = {
            'doc_a': {
                'filepath': 'docs/a.md',
                'filename': 'a.md',
                'type': 'atom',
                'depends_on': ['doc_b'],  # Already normalized
                'status': 'active'
            },
            'doc_b': {
                'filepath': 'docs/b.md',
                'filename': 'b.md',
                'type': 'kernel',
                'depends_on': [],
                'status': 'active'
            }
        }
        issues = validate_dependencies(files_data)
        # Should work without crashing
        broken = [i for i in issues if '[BROKEN LINK]' in i]
        assert len(broken) == 0

    def test_unknown_type_gets_lowest_rank(self):
        """Test that unknown type gets lowest rank (no false violations)."""
        files_data = {
            'unknown_doc': {
                'filepath': 'docs/unknown.md',
                'filename': 'unknown.md',
                'type': 'unknown',  # Normalized from null
                'depends_on': ['kernel_doc'],
                'status': 'active'
            },
            'kernel_doc': {
                'filepath': 'docs/kernel.md',
                'filename': 'kernel.md',
                'type': 'kernel',
                'depends_on': [],
                'status': 'active'
            }
        }
        issues = validate_dependencies(files_data)
        # Unknown depending on kernel should not be an architecture violation
        arch_issues = [i for i in issues if '[ARCHITECTURE]' in i]
        assert len(arch_issues) == 0
