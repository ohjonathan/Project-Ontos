from pathlib import Path

from ontos.commands.map import _format_doc_link
from ontos.io.files import load_document
from ontos.io.yaml import parse_frontmatter_content

def test_format_doc_link_non_obsidian():
    # Backticks for non-obsidian
    assert _format_doc_link("doc1", Path("doc1.md"), False) == "`doc1`"

def test_format_doc_link_obsidian_same_name():
    # [[id]] if filename == id
    assert _format_doc_link("doc1", Path("doc1.md"), True) == "[[doc1]]"

def test_format_doc_link_obsidian_different_name():
    # [[filename|id]] if filename != id
    assert _format_doc_link("doc1", Path("notes/my_note.md"), True) == "[[my_note|doc1]]"

def test_filename_with_spaces():
    """Filenames with spaces should produce correct wikilink."""
    result = _format_doc_link(
        doc_id="my_document",
        doc_path=Path("docs/my document.md"),
        obsidian_mode=True
    )
    assert result == "[[my document|my_document]]"

def test_unicode_filename():
    """Unicode filenames should produce correct wikilink."""
    result = _format_doc_link(
        doc_id="japanese_doc",
        doc_path=Path("docs/日本語.md"),
        obsidian_mode=True
    )
    assert result == "[[日本語|japanese_doc]]"

def test_canonical_loader_handles_utf8_bom(tmp_path):
    p = tmp_path / "bom.md"
    p.write_bytes(b'\xef\xbb\xbf---\nid: test\ntype: atom\n---\nHello')

    document = load_document(p, parse_frontmatter_content)

    assert document.id == "test"
    assert "Hello" in document.content


def test_canonical_loader_handles_leading_whitespace(tmp_path):
    p = tmp_path / "white.md"
    p.write_text(
        '\n\n  \n---\nid: test\ntype: atom\n---\nHello',
        encoding="utf-8",
    )

    document = load_document(p, parse_frontmatter_content)

    assert document.id == "test"
    assert "Hello" in document.content
