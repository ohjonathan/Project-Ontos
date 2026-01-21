import pytest
from ontos.core.frontmatter import normalize_tags, normalize_aliases

def test_normalize_tags():
    # Only concepts
    assert normalize_tags({"concepts": ["a", "b"]}) == ["a", "b"]
    # Only tags
    assert normalize_tags({"tags": ["c", "d"]}) == ["c", "d"]
    # Merged and sorted
    assert normalize_tags({"concepts": ["b", "a"], "tags": ["c", "b"]}) == ["a", "b", "c"]
    # String input
    assert normalize_tags({"tags": "single"}) == ["single"]
    # Empty
    assert normalize_tags({}) == []
    assert normalize_tags({"tags": [None, ""], "concepts": []}) == []

def test_normalize_aliases():
    # Explicit aliases
    assert normalize_aliases({"aliases": ["one", "two"]}, "my_doc") == ["My Doc", "my-doc", "one", "two"]
    # String input
    assert normalize_aliases({"aliases": "alone"}, "my_doc") == ["My Doc", "alone", "my-doc"]
    # Auto-generation from id
    assert normalize_aliases({}, "auth_flow") == ["Auth Flow", "auth-flow"]
    assert normalize_aliases({}, "") == []
