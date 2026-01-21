"""Document caching with mtime-based invalidation.

PURE: This module contains no I/O operations. Callers must provide
mtime values from their own file operations.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    mtime: float
    data: Any


@dataclass
class DocumentCache:
    """In-memory document cache with mtime invalidation.

    Usage:
        cache = DocumentCache()

        # Check cache (caller provides current mtime)
        if (cached := cache.get(path, current_mtime)) is not None:
            return cached

        # Parse and store
        data = parse_document(path)
        cache.set(path, data, current_mtime)
        return data
    """
    _entries: Dict[Path, CacheEntry] = field(default_factory=dict)
    _hits: int = 0
    _misses: int = 0

    def get(self, path: Path, current_mtime: float) -> Optional[Any]:
        """Get cached document if mtime unchanged.

        Args:
            path: Resolved file path.
            current_mtime: Current file modification time.

        Returns:
            Cached data if valid, None if cache miss or invalidated.
        """
        path = path.resolve()

        if path not in self._entries:
            self._misses += 1
            return None

        entry = self._entries[path]
        if current_mtime == entry.mtime:
            self._hits += 1
            return entry.data

        # Invalidated
        del self._entries[path]
        self._misses += 1
        return None

    def set(self, path: Path, data: Any, mtime: float) -> None:
        """Store document in cache.

        Args:
            path: Resolved file path.
            data: Parsed document data.
            mtime: File modification time at parse time.
        """
        path = path.resolve()
        self._entries[path] = CacheEntry(mtime=mtime, data=data)

    def invalidate(self, path: Path) -> None:
        """Remove specific path from cache."""
        path = path.resolve()
        self._entries.pop(path, None)

    def clear(self) -> None:
        """Clear entire cache."""
        self._entries.clear()
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> dict:
        """Return cache statistics."""
        total = self._hits + self._misses
        return {
            "entries": len(self._entries),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
        }
