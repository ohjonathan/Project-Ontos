
import sys
import os
import pytest
from unittest.mock import patch, mock_open

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../.ontos/scripts')))

from ontos_lib import (
    parse_frontmatter,
    normalize_depends_on,
    normalize_type,
    load_common_concepts,
    get_git_last_modified,
    find_last_session_date
)
from ontos_config import DOCS_DIR

def test_parse_frontmatter_valid():
    content = "---\nid: test\ntype: note\n---\nbody"
    with patch("builtins.open", mock_open(read_data=content)):
        fm = parse_frontmatter("dummy.md")
        assert fm['id'] == 'test'
        assert fm['type'] == 'note'

def test_parse_frontmatter_missing():
    content = "no frontmatter"
    with patch("builtins.open", mock_open(read_data=content)):
        fm = parse_frontmatter("dummy.md")
        assert fm is None

def test_parse_frontmatter_malformed():
    content = "---\nid: test\n: invalid yaml\n---\nbody"
    with patch("builtins.open", mock_open(read_data=content)):
        # Should catch YAMLError and return None (and maybe print error)
        fm = parse_frontmatter("dummy.md")
        assert fm is None

def test_normalize_depends_on_none():
    assert normalize_depends_on(None) == []

def test_normalize_depends_on_string():
    assert normalize_depends_on("doc1") == ["doc1"]

def test_normalize_depends_on_list():
    assert normalize_depends_on(["doc1", "doc2"]) == ["doc1", "doc2"]
    assert normalize_depends_on(["doc1", None, ""]) == ["doc1"]

def test_normalize_type_none():
    assert normalize_type(None) == 'unknown'

def test_normalize_type_valid():
    assert normalize_type("concept") == "concept"
    assert normalize_type(["concept"]) == "concept"
    assert normalize_type(["concept | other"]) == "unknown"

def test_load_common_concepts_found():
    content = "| `concept-a` | Desc |\n| `concept-b` | Desc |"
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=content)):
        concepts = load_common_concepts()
        assert "concept-a" in concepts
        assert "concept-b" in concepts

def test_load_common_concepts_missing():
    with patch("os.path.exists", return_value=False):
        concepts = load_common_concepts()
        assert concepts == set()

# get_git_last_modified tests mocked
def test_get_git_last_modified_tracked():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "1672574400"  # Unix timestamp for 2023-01-01 12:00:00
        dt = get_git_last_modified("file.md")
        assert dt.year == 2023

def test_get_git_last_modified_untracked():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        dt = get_git_last_modified("file.md")
        assert dt is None

def test_find_last_session_date_with_logs():
    with patch("os.path.exists", return_value=True), \
         patch("os.listdir", return_value=["2025-01-01_log.md", "2025-01-02_log.md"]):
        assert find_last_session_date() == "2025-01-02"

def test_find_last_session_date_empty():
    with patch("os.path.exists", return_value=True), \
         patch("os.listdir", return_value=[]):
        assert find_last_session_date() == ""
