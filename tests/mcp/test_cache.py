from concurrent.futures import ThreadPoolExecutor

import pytest

from tests.mcp import build_cache, create_workspace, write_file


def test_cache_rebuilds_on_document_and_describes_changes(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)

    (root / "docs/atom.md").write_text(
        (root / "docs/atom.md").read_text(encoding="utf-8").replace("Atom body", "Atom changed"),
        encoding="utf-8",
    )
    cache.get_fresh_snapshot()
    revision_after_doc = cache.snapshot_revision

    (root / "src/foo.py").write_text("print('changed')\n", encoding="utf-8")
    cache.get_fresh_snapshot()

    assert revision_after_doc == 2
    assert cache.snapshot_revision == 3


def test_cache_missing_target_and_concurrent_refresh_behavior(tmp_path, monkeypatch):
    root = create_workspace(tmp_path)
    cache = build_cache(root)

    cache.get_fresh_snapshot()
    assert cache.snapshot_revision == 1

    (root / "src/never_existed.py").write_text("print('new')\n", encoding="utf-8")

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _n: cache.get_fresh_snapshot(), range(4)))

    assert cache.snapshot_revision == 2

    original_builder = cache._build_replacement_state

    def fail_builder(_revision):
        raise RuntimeError("boom")

    (root / "docs/product.md").write_text(
        (root / "docs/product.md").read_text(encoding="utf-8").replace("Product body", "Broken product"),
        encoding="utf-8",
    )
    monkeypatch.setattr(cache, "_build_replacement_state", fail_builder)

    try:
        cache.get_fresh_snapshot()
    except RuntimeError:
        pass

    assert cache.snapshot_revision == 2
    monkeypatch.setattr(cache, "_build_replacement_state", original_builder)


def test_cache_view_remains_stable_across_refresh(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)
    view_before = cache.current_view()

    write_file(root / "docs/added.md", """
    ---
    id: added_doc
    type: atom
    status: active
    ---
    Added body.
    """)
    cache.force_refresh()
    view_after = cache.current_view()

    assert view_before.snapshot_revision == 1
    assert view_before.canonical_view.total_count == 8
    assert "added_doc" not in view_before.snapshot.documents
    assert view_after.snapshot_revision == 2
    assert view_after.canonical_view.total_count == 9
    assert "added_doc" in view_after.snapshot.documents


def test_cache_detects_new_document_in_existing_subdirectory(tmp_path):
    root = create_workspace(tmp_path)
    nested_docs_dir = root / "docs/nested"
    nested_docs_dir.mkdir(parents=True)
    cache = build_cache(root)

    write_file(nested_docs_dir / "new.md", """
    ---
    id: nested_doc
    type: atom
    status: active
    ---
    Nested body.
    """)
    cache.get_fresh_snapshot()

    assert cache.snapshot_revision == 2
    assert cache.canonical_view.total_count == 9
    assert "nested_doc" in cache.snapshot.documents


def test_cache_ignores_hidden_and_temp_markdown_churn(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)

    write_file(root / "docs/.scratch.md", """
    ---
    id: scratch_doc
    type: atom
    status: active
    ---
    Scratch body.
    """)
    write_file(root / "docs/#draft#.md", """
    ---
    id: draft_doc
    type: atom
    status: active
    ---
    Draft body.
    """)
    cache.get_fresh_snapshot()

    assert cache.snapshot_revision == 1
    assert cache.canonical_view.total_count == 8
    assert "scratch_doc" not in cache.snapshot.documents
    assert "draft_doc" not in cache.snapshot.documents


def test_cache_ignores_symlinked_markdown_outside_workspace(tmp_path):
    root = create_workspace(tmp_path)
    outside_doc = tmp_path / "outside.md"
    outside_doc.write_text(
        "---\nid: outside_doc\ntype: atom\nstatus: active\n---\nOutside body.\n",
        encoding="utf-8",
    )
    symlink_path = root / "docs/escape.md"
    try:
        symlink_path.symlink_to(outside_doc)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    cache = build_cache(root)

    assert cache.canonical_view.total_count == 8
    assert "outside_doc" not in cache.snapshot.documents
