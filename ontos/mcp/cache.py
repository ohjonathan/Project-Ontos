"""In-memory snapshot cache and freshness checks for the Ontos MCP server."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import threading
import time
from typing import Callable, Dict, Optional, Set, Tuple

from ontos.core.graph import calculate_depths
from ontos.core.snapshot import DocumentSnapshot
from ontos.core.types import DocumentData
from ontos.io.scan_scope import collect_scoped_documents, resolve_scan_scope
from ontos.io.snapshot import create_snapshot
from ontos.mcp.tools import CanonicalSnapshotView, build_canonical_snapshot_view


Fingerprint = Optional[Tuple[int, int]]
TEMP_FILE_SUFFIXES = (".swp", ".swo")


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

        self.snapshot: DocumentSnapshot = snapshot
        self.fingerprints: Dict[str, Fingerprint] = {}
        self.documents_by_path: Dict[str, str] = {}
        self.depths: Dict[str, int] = {}
        self.snapshot_revision = 1
        self.last_indexed = datetime.now(timezone.utc)
        self.canonical_view: CanonicalSnapshotView
        self._tracked_doc_path_keys: Set[str] = set()

        self._replace_state_from_snapshot(snapshot, revision=1)

    def get_fresh_snapshot(self) -> DocumentSnapshot:
        """Return the latest snapshot, rebuilding only when inputs changed."""
        if not self._is_stale():
            return self.snapshot

        with self.rebuild_lock:
            if not self._is_stale():
                return self.snapshot

            snapshot, state = self._build_replacement_state()
            self._apply_replacement_state(snapshot, state, self.snapshot_revision + 1)
            return self.snapshot

    def force_refresh(self) -> tuple[DocumentSnapshot, int]:
        """Rebuild the snapshot unconditionally and return duration in milliseconds."""
        started = time.perf_counter()
        with self.rebuild_lock:
            snapshot, state = self._build_replacement_state()
            self._apply_replacement_state(snapshot, state, self.snapshot_revision + 1)

        duration_ms = int((time.perf_counter() - started) * 1000)
        return self.snapshot, duration_ms

    def _replace_state_from_snapshot(self, snapshot: DocumentSnapshot, revision: int) -> None:
        state = self._materialize_state(snapshot)
        self._apply_replacement_state(snapshot, state, revision)

    def _build_replacement_state(self) -> tuple[DocumentSnapshot, dict]:
        snapshot = create_snapshot(
            root=self.workspace_root,
            include_content=True,
            filters=None,
            git_commit_provider=self._git_commit_provider,
            scope=None,
        )
        return snapshot, self._materialize_state(snapshot)

    def _materialize_state(self, snapshot: DocumentSnapshot) -> dict:
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

        for doc in snapshot.documents.values():
            for raw_target in doc.describes:
                if not self._is_path_like_describes(raw_target):
                    continue

                resolved_target = self._resolve_describes_target(raw_target)
                if resolved_target is None or self._skip_described_target(resolved_target, tracked_doc_keys):
                    key = f"missing::{doc.id}::{raw_target}"
                    fingerprints.setdefault(key, None)
                    continue

                rel_target = resolved_target.relative_to(self.workspace_root).as_posix()
                fingerprints[f"path::{rel_target}"] = self._stat_fingerprint(resolved_target)

        return {
            "fingerprints": fingerprints,
            "documents_by_path": documents_by_path,
            "depths": calculate_depths(snapshot.graph),
            "canonical_view": build_canonical_snapshot_view(snapshot, self.workspace_root),
            "tracked_doc_path_keys": tracked_doc_keys,
            "last_indexed": datetime.now(timezone.utc),
        }

    def _apply_replacement_state(self, snapshot: DocumentSnapshot, state: dict, revision: int) -> None:
        self.snapshot = snapshot
        self.fingerprints = state["fingerprints"]
        self.documents_by_path = state["documents_by_path"]
        self.depths = state["depths"]
        self.canonical_view = state["canonical_view"]
        self._tracked_doc_path_keys = state["tracked_doc_path_keys"]
        self.last_indexed = state["last_indexed"]
        self.snapshot_revision = revision

    def _is_stale(self) -> bool:
        current_doc_paths = {
            f"path::{path.resolve(strict=False).relative_to(self.workspace_root).as_posix()}"
            for path in self._scan_canonical_document_paths()
        }
        if current_doc_paths != self._tracked_doc_path_keys:
            return True

        for key in current_doc_paths:
            rel_path = key.split("::", 1)[1]
            current = self._stat_fingerprint(self.workspace_root / rel_path)
            if current != self.fingerprints.get(key):
                return True

        current_describes = self._current_describes_fingerprints()
        for key, current in current_describes.items():
            if current != self.fingerprints.get(key):
                return True

        tracked_extra_keys = set(self.fingerprints) - self._tracked_doc_path_keys
        if tracked_extra_keys != set(current_describes):
            return True

        return False

    def _scan_canonical_document_paths(self) -> list[Path]:
        effective_scope = resolve_scan_scope(None, self.config.scanning.default_scope)
        return collect_scoped_documents(
            self.workspace_root,
            self.config,
            effective_scope,
            base_skip_patterns=self.config.scanning.skip_patterns,
        )

    def _current_describes_fingerprints(self) -> Dict[str, Fingerprint]:
        fingerprints: Dict[str, Fingerprint] = {}
        for doc in self.snapshot.documents.values():
            for raw_target in doc.describes:
                if not self._is_path_like_describes(raw_target):
                    continue

                resolved_target = self._resolve_describes_target(raw_target)
                if resolved_target is None or self._skip_described_target(resolved_target, self._tracked_doc_path_keys):
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

    def _skip_described_target(self, path: Path, tracked_doc_keys: Set[str]) -> bool:
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
