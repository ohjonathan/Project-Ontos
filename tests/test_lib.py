"""Tests for ontos_lib shim module and core functions.

Updated for Phase 2/3: Tests the actual behavior of the new module structure.
"""

import os
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path
from datetime import datetime

# Import from the new package structure (not deprecated shim)
from ontos.core.frontmatter import (
    parse_frontmatter,
    normalize_depends_on,
    normalize_type,
    load_common_concepts,
)
from ontos.core.config import get_git_last_modified
from ontos.core.paths import find_last_session_date
from ontos.io.yaml import parse_yaml


def test_parse_frontmatter_valid(tmp_path):
    """Test parsing valid frontmatter."""
    doc = tmp_path / "test.md"
    doc.write_text("---\nid: test\ntype: note\n---\nbody")
    fm = parse_frontmatter(str(doc), yaml_parser=parse_yaml)
    assert fm['id'] == 'test'
    assert fm['type'] == 'note'


def test_parse_frontmatter_missing(tmp_path):
    """Test file without frontmatter returns None."""
    doc = tmp_path / "test.md"
    doc.write_text("no frontmatter")
    fm = parse_frontmatter(str(doc), yaml_parser=parse_yaml)
    assert fm is None


def test_parse_frontmatter_malformed(tmp_path):
    """Test malformed YAML returns None."""
    doc = tmp_path / "test.md"
    # This YAML has a syntax error (no key before the colon on line 2)
    doc.write_text("---\nid: test\n: invalid yaml\n---\nbody")
    # Should catch YAMLError and return None
    fm = parse_frontmatter(str(doc), yaml_parser=parse_yaml)
    assert fm is None


def test_normalize_depends_on_none():
    """Test normalize_depends_on with None."""
    assert normalize_depends_on(None) == []


def test_normalize_depends_on_string():
    """Test normalize_depends_on with string."""
    assert normalize_depends_on("doc1") == ["doc1"]


def test_normalize_depends_on_list():
    """Test normalize_depends_on with list."""
    assert normalize_depends_on(["doc1", "doc2"]) == ["doc1", "doc2"]
    assert normalize_depends_on(["doc1", None, ""]) == ["doc1"]


def test_normalize_type_none():
    """Test normalize_type with None."""
    assert normalize_type(None) == 'unknown'


def test_normalize_type_valid():
    """Test normalize_type with valid values."""
    assert normalize_type("concept") == "concept"
    assert normalize_type(["concept"]) == "concept"
    assert normalize_type(["concept | other"]) == "unknown"


def test_load_common_concepts_found():
    """Test loading concepts from file."""
    content = "| `concept-a` | Desc |\n| `concept-b` | Desc |"
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=content)):
        concepts = load_common_concepts()
        assert "concept-a" in concepts
        assert "concept-b" in concepts


def test_load_common_concepts_missing():
    """Test loading concepts when file missing."""
    with patch("os.path.exists", return_value=False):
        concepts = load_common_concepts()
        assert concepts == set()


def test_get_git_last_modified_tracked():
    """Test get_git_last_modified with mocked provider."""
    expected_dt = datetime(2023, 1, 1, 12, 0, 0)
    
    def mock_provider(path):
        return expected_dt
    
    dt = get_git_last_modified("file.md", git_mtime_provider=mock_provider)
    assert dt == expected_dt
    assert dt.year == 2023


def test_get_git_last_modified_untracked():
    """Test get_git_last_modified with provider returning None."""
    def mock_provider(path):
        return None
    
    dt = get_git_last_modified("file.md", git_mtime_provider=mock_provider)
    assert dt is None


def test_get_git_last_modified_no_provider():
    """Test get_git_last_modified without provider returns None."""
    dt = get_git_last_modified("file.md")
    assert dt is None


def test_find_last_session_date_with_logs():
    """Test find_last_session_date with existing logs."""
    with patch("os.path.exists", return_value=True), \
         patch("os.listdir", return_value=["2025-01-01_log.md", "2025-01-02_log.md"]):
        assert find_last_session_date() == "2025-01-02"


def test_find_last_session_date_empty():
    """Test find_last_session_date with no logs."""
    with patch("os.path.exists", return_value=True), \
         patch("os.listdir", return_value=[]):
        assert find_last_session_date() == ""
