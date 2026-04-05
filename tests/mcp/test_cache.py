from concurrent.futures import ThreadPoolExecutor

from tests.mcp import build_cache, create_workspace


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

    def fail_builder():
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
