import pytest
from pathlib import Path
from ontos.commands.map import _format_doc_link, GenerateMapOptions
from ontos.io.obsidian import read_file_lenient

def test_format_doc_link_non_obsidian():
    # Backticks for non-obsidian
    assert _format_doc_link("doc1", Path("doc1.md"), False) == "`doc1`"

def test_format_doc_link_obsidian_same_name():
    # [[id]] if filename == id
    assert _format_doc_link("doc1", Path("doc1.md"), True) == "[[doc1]]"

def test_format_doc_link_obsidian_different_name():
    # [[filename|id]] if filename != id
    assert _format_doc_link("doc1", Path("notes/my_note.md"), True) == "[[my_note|doc1]]"

def test_read_file_lenient_bom(tmp_path):
    p = tmp_path / "bom.md"
    # UTF-8 BOM is \xef\xbb\xbf
    p.write_bytes(b'\xef\xbb\xbf---\nid: test\n---\nHello')
    content = read_file_lenient(p)
    assert content.startswith('---')
    assert 'id: test' in content

def test_read_file_lenient_whitespace(tmp_path):
    p = tmp_path / "white.md"
    p.write_text('\n\n  \n---\nid: test\n---\nHello')
    content = read_file_lenient(p)
    assert content.startswith('---')
    assert 'id: test' in content

def test_read_file_lenient_no_frontmatter(tmp_path):
    p = tmp_path / "plain.md"
    p.write_text('Just text')
    content = read_file_lenient(p)
    assert content == 'Just text'
