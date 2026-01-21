import pytest
from collections import namedtuple
from ontos.commands.map import _generate_compact_output, CompactMode

Doc = namedtuple('Doc', ['type', 'status', 'frontmatter'])

def test_compact_output_basic():
    docs = {
        "doc1": Doc(type="atom", status="active", frontmatter={}),
        "doc2": Doc(type="kernel", status="stable", frontmatter={})
    }
    output = _generate_compact_output(docs, CompactMode.BASIC)
    expected = "doc1:atom:active\ndoc2:kernel:stable"
    assert output == expected

def test_compact_output_rich_with_escaping():
    docs = {
        "doc1": Doc(type="atom", status="active", frontmatter={"summary": "Line 1\nLine 2 with \"quotes\" and \\backslash"}),
    }
    output = _generate_compact_output(docs, CompactMode.RICH)
    expected = 'doc1:atom:active:"Line 1\\nLine 2 with \\"quotes\\" and \\\\backslash"'
    assert output == expected

def test_compact_output_rich_non_string_summary():
    docs = {
        "doc1": Doc(type="atom", status="active", frontmatter={"summary": ["Line 1", "Line 2"]}),
    }
    output = _generate_compact_output(docs, CompactMode.RICH)
    # ["Line 1", "Line 2"] as string is "['Line 1', 'Line 2']"
    expected = 'doc1:atom:active:"[\'Line 1\', \'Line 2\']"'
    assert output == expected

def test_compact_output_off():
    docs = {"a": Doc(type="t", status="s", frontmatter={})}
    assert _generate_compact_output(docs, CompactMode.OFF) == ""
