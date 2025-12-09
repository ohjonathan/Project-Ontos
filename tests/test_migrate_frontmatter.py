"""Tests for migrate_frontmatter functionality."""

import pytest
from ontos_migrate_frontmatter import has_frontmatter, scan_for_untagged_files, generate_prompt


class TestHasFrontmatter:
    """Tests for has_frontmatter function."""

    def test_file_with_frontmatter(self, valid_kernel_doc):
        """Test detection of file with frontmatter."""
        assert has_frontmatter(str(valid_kernel_doc)) is True

    def test_file_without_frontmatter(self, doc_without_frontmatter):
        """Test detection of file without frontmatter."""
        assert has_frontmatter(str(doc_without_frontmatter)) is False

    def test_nonexistent_file(self, tmp_path):
        """Test handling of nonexistent file."""
        result = has_frontmatter(str(tmp_path / "nonexistent.md"))
        assert result is False


class TestScanForUntaggedFiles:
    """Tests for scan_for_untagged_files function."""

    def test_find_untagged_file(self, temp_docs_dir, doc_without_frontmatter):
        """Test finding files without frontmatter."""
        result = scan_for_untagged_files(str(temp_docs_dir))
        assert len(result) == 1
        assert str(doc_without_frontmatter) in result

    def test_skip_tagged_files(self, temp_docs_dir, valid_kernel_doc):
        """Test skipping files with frontmatter."""
        result = scan_for_untagged_files(str(temp_docs_dir))
        assert len(result) == 0

    def test_mixed_files(self, temp_docs_dir, valid_kernel_doc, doc_without_frontmatter):
        """Test with mix of tagged and untagged files."""
        result = scan_for_untagged_files(str(temp_docs_dir))
        assert len(result) == 1
        assert str(doc_without_frontmatter) in result
        assert str(valid_kernel_doc) not in result


class TestGeneratePrompt:
    """Tests for generate_prompt function."""

    def test_prompt_contains_files(self):
        """Test that prompt contains listed files."""
        files = ['docs/file1.md', 'docs/file2.md']
        prompt = generate_prompt(files)

        assert 'docs/file1.md' in prompt
        assert 'docs/file2.md' in prompt

    def test_prompt_contains_taxonomy(self):
        """Test that prompt contains type taxonomy."""
        prompt = generate_prompt(['docs/test.md'])

        assert 'kernel' in prompt
        assert 'strategy' in prompt
        assert 'product' in prompt
        assert 'atom' in prompt

    def test_prompt_contains_heuristic(self):
        """Test that prompt contains classification heuristic."""
        prompt = generate_prompt(['docs/test.md'])

        assert 'what else breaks' in prompt.lower()
