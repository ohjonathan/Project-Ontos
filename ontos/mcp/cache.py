"""In-memory snapshot cache and freshness checks for the Ontos MCP server."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import threading
import time
from typing import Any, Callable, Dict, Optional, Set, Tuple

from ontos.core.graph import calculate_depths
from ontos.core.snapshot import DocumentSnapshot
from ontos.io.scan_scope import collect_scoped_documents, resolve_scan_scope
from ontos.io.snapshot import create_snapshot
from ontos.mcp.tools import CanonicalSnapshotView, build_canonical_snapshot_view


Fingerprint = Optional[Tuple[int, int]]
TEMP_FILE_SUFFIXES = (".swp", ".swo")


@dataclass(frozen=True)
class SnapshotCacheState:
    snapshot: DocumentSnapshot
    fingerprints: Dict[str, Fingerprint]
    documents_by_path: Dict[str, str]
    depths: Dict[str, int]
    canonical_view: CanonicalSnapshotView
    tracked_doc_path_keys: frozenset[str]
    last_indexed: datetime
    snapshot_revision: int


@dataclass(frozen=True)
class SnapshotCacheView:
    workspace_root: Path
    config: Any
    started_at: datetime
    freshness_mode: str
    snapshot: DocumentSnapshot
    documents_by_path: Dict[str, str]
    depths: Dict[str, int]
    canonical_view: CanonicalSnapshotView
    snapshot_revision: int
    last_indexed: datetime


class SnapshotCache:
    """Keep one canonical Ontos snapshot warm for MCP tool calls."""

    freshness_mode = "file-mtime-fingerprint"

    def __init__(
        self,
        workspace_root: Path,
        config,
        snapshot: DocumentSnapshot,
        *,
        git_commit_provider: Optional[Callable[[], Optional[str]]] = None,
        started_at: Optional[datetime] = None,
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.config = config
        self.started_at = started_at or datetime.now(timezone.utc)
        self.rebuild_lock = threading.Lock()
        self._git_commit_provider = git_commit_provider
        self._state: SnapshotCacheState
        self._replace_state_from_snapshot(snapshot, revision=1)

    @property
    def snapshot(self) -> DocumentSnapshot:
        return self._state.snapshot

    @property
    def fingerprints(self) -> Dict[str, Fingerprint]:
        return self._state.fingerprints

    @property
    def documents_by_path(self) -> Dict[str, str]:
        return self._state.documents_by_path

    @property
    def depths(self) -> Dict[str, int]:
        return self._state.depths

    @property
    def canonical_view(self) -> CanonicalSnapshotView:
        return self._state.canonical_view

    @property
    def snapshot_revision(self) -> int:
        return self._state.snapshot_revision

    @property
    def last_indexed(self) -> datetime:
        return self._state.last_indexed

    def current_view(self) -> SnapshotCacheView:
        """Return a stable read view of the current published cache state."""
        return self._view_for_state(self._state)

    def get_fresh_view(self) -> SnapshotCacheView:
        """Return a stable read view, rebuilding only when tracked inputs changed."""
        state = self._state
        if not self._is_stale(state):
            return self._view_for_state(state)

        with self.rebuild_lock:
            state = self._state
            if not self._is_stale(state):
                return self._view_for_state(state)

            next_revision = state.snapshot_revision + 1
            replacement = self._build_replacement_state(next_revision)
            self._publish_state(replacement)
            return self._view_for_state(replacement)

    def get_fresh_snapshot(self) -> DocumentSnapshot:
        """Return the latest snapshot, rebuilding only when inputs changed."""
        return self.get_fresh_view().snapshot

    def force_refresh(self) -> tuple[DocumentSnapshot, int]:
        """Rebuild the snapshot unconditionally and return duration in milliseconds."""
        started = time.perf_counter()
        with self.rebuild_lock:
            next_revision = self._state.snapshot_revision + 1
            replacement = self._build_replacement_state(next_revision)
            self._publish_state(replacement)

        duration_ms = int((time.perf_counter() - started) * 1000)
        return replacement.snapshot, duration_ms

    def _replace_state_from_snapshot(self, snapshot: DocumentSnapshot, revision: int) -> None:
        self._publish_state(self._materialize_state(snapshot, revision))

    def _build_replacement_state(self, revision: int) -> SnapshotCacheState:
        snapshot = create_snapshot(
            root=self.workspace_root,
            include_content=True,
            filters=None,
            git_commit_provider=self._git_commit_provider,
            scope=None,
        )
        return self._materialize_state(snapshot, revision)

    def _materialize_state(self, snapshot: DocumentSnapshot, revision: int) -> SnapshotCacheState:
        tracked_doc_keys: Set[str] = set()
        fingerprints: Dict[str, Fingerprint] = {}
        documents_by_path: Dict[str, str] = {}

        for doc in snapshot.documents.values():
            resolved = doc.filepath.resolve(strict=False)
            rel_path = resolved.relative_to(self.workspace_root).as_posix()
            key = f"path::{rel_path}"
            tracked_doc_keys.add(key)
            fingerprints[key] = self._stat_fingerprint(resolved)
            documents_by_path[str(resolved)] = doc.id
            documents_by_path[rel_path] = doc.id

        tracked_doc_path_keys = frozenset(tracked_doc_keys)
        fingerprints.update(self._describes_fingerprints(snapshot, tracked_doc_path_keys))

        return SnapshotCacheState(
            snapshot=snapshot,
            fingerprints=fingerprints,
            documents_by_path=documents_by_path,
            depths=calculate_depths(snapshot.graph),
            canonical_view=build_canonical_snapshot_view(snapshot, self.workspace_root),
            tracked_doc_path_keys=tracked_doc_path_keys,
            last_indexed=datetime.now(timezone.utc),
            snapshot_revision=revision,
        )

    def _publish_state(self, replacement: SnapshotCacheState) -> None:
        self._state = replacement

    def _view_for_state(self, state: SnapshotCacheState) -> SnapshotCacheView:
        return SnapshotCacheView(
            workspace_root=self.workspace_root,
            config=self.config,
            started_at=self.started_at,
            freshness_mode=self.freshness_mode,
            snapshot=state.snapshot,
            documents_by_path=state.documents_by_path,
            depths=state.depths,
            canonical_view=state.canonical_view,
            snapshot_revision=state.snapshot_revision,
            last_indexed=state.last_indexed,
        )

    def _is_stale(self, state: SnapshotCacheState) -> bool:
        current_doc_paths = self._scan_canonical_document_keys()
        if current_doc_paths != state.tracked_doc_path_keys:
            return True

        for key in state.tracked_doc_path_keys:
            rel_path = key.split("::", 1)[1]
            current = self._stat_fingerprint(self.workspace_root / rel_path)
            if current != state.fingerprints.get(key):
                return True

        current_describes = self._describes_fingerprints(
            state.snapshot,
            state.tracked_doc_path_keys,
        )
        tracked_extra_keys = set(state.fingerprints) - set(state.tracked_doc_path_keys)
        if tracked_extra_keys != set(current_describes):
            return True

        for key, current in current_describes.items():
            if current != state.fingerprints.get(key):
                return True

        return False

    def _scan_canonical_document_keys(self) -> frozenset[str]:
        effective_scope = resolve_scan_scope(None, self.config.scanning.default_scope)
        paths = collect_scoped_documents(
            self.workspace_root,
            self.config,
            effective_scope,
            base_skip_patterns=self.config.scanning.skip_patterns,
        )
        return frozenset(
            f"path::{path.resolve(strict=False).relative_to(self.workspace_root).as_posix()}"
            for path in paths
        )

    def _describes_fingerprints(
        self,
        snapshot: DocumentSnapshot,
        tracked_doc_path_keys: Set[str] | frozenset[str],
    ) -> Dict[str, Fingerprint]:
        fingerprints: Dict[str, Fingerprint] = {}
        for doc in snapshot.documents.values():
            for raw_target in doc.describes:
                if not self._is_path_like_describes(raw_target):
                    continue

                resolved_target = self._resolve_describes_target(raw_target)
                if resolved_target is None or self._skip_described_target(resolved_target, tracked_doc_path_keys):
                    fingerprints[f"missing::{doc.id}::{raw_target}"] = None
                    continue

                rel_target = resolved_target.relative_to(self.workspace_root).as_posix()
                fingerprints[f"path::{rel_target}"] = self._stat_fingerprint(resolved_target)

        return fingerprints

    def _resolve_describes_target(self, raw_target: str) -> Optional[Path]:
        target_path = Path(raw_target)
        if raw_target.startswith("~"):
            target_path = target_path.expanduser()
        if not target_path.is_absolute():
            target_path = self.workspace_root / target_path

        resolved = target_path.resolve(strict=False)
        if not resolved.is_relative_to(self.workspace_root):
            return None
        return resolved

    def _skip_described_target(self, path: Path, tracked_doc_keys: Set[str] | frozenset[str]) -> bool:
        name = path.name
        if name.endswith(TEMP_FILE_SUFFIXES) or name.endswith("~") or name.startswith("#"):
            return True
        if name.startswith("."):
            rel = path.relative_to(self.workspace_root).as_posix()
            return f"path::{rel}" not in tracked_doc_keys
        return False

    @staticmethod
    def _is_path_like_describes(raw_target: str) -> bool:
        if "/" in raw_target or "\\" in raw_target:
            return True
        final_segment = Path(raw_target).name
        return "." in final_segment.strip(".")

    @staticmethod
    def _stat_fingerprint(path: Path) -> Fingerprint:
        try:
            stat = path.stat()
        except OSError:
            return None
        return stat.st_mtime_ns, stat.st_size
