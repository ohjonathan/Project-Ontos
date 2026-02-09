"""Regression tests for Tier 1 Key Documents behavior."""

from pathlib import Path

from ontos.commands.map import _format_rel_path, _generate_document_table, _generate_tier1_summary
from ontos.core.types import DocumentData, DocumentStatus, DocumentType


def _make_doc(doc_id: str, depends_on=None) -> DocumentData:
    """Create a minimal document for map summary tests."""
    return DocumentData(
        id=doc_id,
        filepath=Path(f"docs/{doc_id}.md"),
        type=DocumentType.ATOM,
        status=DocumentStatus.ACTIVE,
        frontmatter={},
        content="",
        depends_on=depends_on or [],
    )


def test_tier1_key_documents_lists_top_three_only():
    """Key Documents should show only top 3 by in-degree."""
    docs = {
        "key_a": _make_doc("key_a"),
        "key_b": _make_doc("key_b"),
        "key_c": _make_doc("key_c"),
        "key_d": _make_doc("key_d"),
        "key_e": _make_doc("key_e"),
    }

    # in-degree counts: a=5, b=4, c=3, d=2, e=1
    for idx in range(5):
        docs[f"ref_a_{idx}"] = _make_doc(f"ref_a_{idx}", ["key_a"])
    for idx in range(4):
        docs[f"ref_b_{idx}"] = _make_doc(f"ref_b_{idx}", ["key_b"])
    for idx in range(3):
        docs[f"ref_c_{idx}"] = _make_doc(f"ref_c_{idx}", ["key_c"])
    for idx in range(2):
        docs[f"ref_d_{idx}"] = _make_doc(f"ref_d_{idx}", ["key_d"])
    docs["ref_e_0"] = _make_doc("ref_e_0", ["key_e"])

    summary = _generate_tier1_summary(docs, {"project_name": "Test"})

    assert "### Key Documents" in summary
    assert "- `key_a` (5 dependents) — docs/key_a.md" in summary
    assert "- `key_b` (4 dependents) — docs/key_b.md" in summary
    assert "- `key_c` (3 dependents) — docs/key_c.md" in summary
    assert "- `key_d` (2 dependents)" not in summary
    assert "- `key_e` (1 dependents)" not in summary


def test_tier1_key_documents_omitted_without_dependency_data():
    """Key Documents section is omitted when no in-degree data exists."""
    docs = {
        "doc_a": _make_doc("doc_a"),
        "doc_b": _make_doc("doc_b"),
    }

    summary = _generate_tier1_summary(docs, {"project_name": "Test"})

    assert "### Key Documents" not in summary
    assert "No dependency data yet." not in summary


def test_tier1_key_documents_never_leaks_absolute_paths(tmp_path):
    """Key Documents should not emit absolute paths when outside project root."""
    docs = {
        "inside": _make_doc("inside"),
        "outside": DocumentData(
            id="outside",
            filepath=tmp_path.parent / "outside.md",
            type=DocumentType.ATOM,
            status=DocumentStatus.ACTIVE,
            frontmatter={},
            content="",
            depends_on=[],
        ),
        "ref_inside": _make_doc("ref_inside", ["inside"]),
        "ref_outside": DocumentData(
            id="ref_outside",
            filepath=tmp_path / "ref_outside.md",
            type=DocumentType.ATOM,
            status=DocumentStatus.ACTIVE,
            frontmatter={},
            content="",
            depends_on=["outside"],
        ),
    }

    summary = _generate_tier1_summary(
        docs,
        {"project_name": "Test", "project_root": str(tmp_path)},
    )

    assert "outside.md" in summary
    assert str(tmp_path.parent) not in summary


def test_format_rel_path_uses_cwd_when_no_root(tmp_path, monkeypatch):
    """When no root_path is provided, paths are relative to CWD."""
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "docs" / "file.md"
    assert _format_rel_path(path) == "docs/file.md"


def test_format_rel_path_returns_relative_input_when_outside_cwd(tmp_path, monkeypatch):
    """Relative paths outside CWD should return the input path."""
    inner = tmp_path / "inner"
    inner.mkdir()
    monkeypatch.chdir(inner)
    path = Path("../outside.md")
    assert _format_rel_path(path) == "../outside.md"


def test_format_rel_path_handles_resolve_failure(tmp_path, monkeypatch):
    """Resolve failures should not leak absolute paths."""
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "docs" / "file.md"

    def _raise_resolve(self):
        raise OSError("boom")

    monkeypatch.setattr(Path, "resolve", _raise_resolve)
    assert _format_rel_path(path) == "docs/file.md"


def test_document_table_paths_are_relative_and_no_absolute(tmp_path):
    """Document table should avoid absolute paths, even outside root."""
    docs = {
        "inside": DocumentData(
            id="inside",
            filepath=tmp_path / "docs" / "inside.md",
            type=DocumentType.ATOM,
            status=DocumentStatus.ACTIVE,
            frontmatter={},
            content="",
            depends_on=[],
        ),
        "outside": DocumentData(
            id="outside",
            filepath=tmp_path.parent / "outside.md",
            type=DocumentType.ATOM,
            status=DocumentStatus.ACTIVE,
            frontmatter={},
            content="",
            depends_on=[],
        ),
    }

    table = _generate_document_table(docs, root_path=tmp_path)

    assert "docs/inside.md" in table
    assert "outside.md" in table
    assert str(tmp_path) not in table
