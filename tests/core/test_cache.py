import pytest
from pathlib import Path
from ontos.core.cache import DocumentCache

def test_cache_basic_operations():
    cache = DocumentCache()
    path = Path("/tmp/test.md").resolve()
    mtime = 123.0
    data = {"id": "test"}

    # Miss
    assert cache.get(path, mtime) is None
    assert cache.stats["misses"] == 1

    # Set and Hit
    cache.set(path, data, mtime)
    assert cache.get(path, mtime) == data
    assert cache.stats["hits"] == 1
    assert cache.stats["entries"] == 1

def test_cache_invalidation():
    cache = DocumentCache()
    path = Path("/tmp/test.md").resolve()
    mtime = 123.0
    data = {"id": "test"}

    cache.set(path, data, mtime)
    
    # Invalidation on mtime change
    assert cache.get(path, 124.0) is None
    assert cache.stats["misses"] == 1
    assert cache.stats["entries"] == 0

def test_cache_explicit_invalidate_and_clear():
    cache = DocumentCache()
    path1 = Path("/tmp/test1.md").resolve()
    path2 = Path("/tmp/test2.md").resolve()
    
    cache.set(path1, {"v": 1}, 100.0)
    cache.set(path2, {"v": 2}, 100.0)
    
    cache.invalidate(path1)
    assert cache.get(path1, 100.0) is None
    assert cache.get(path2, 100.0) is not None
    
    cache.clear()
    assert cache.stats["entries"] == 0
    assert cache.stats["hits"] == 0
