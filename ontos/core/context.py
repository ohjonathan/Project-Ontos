"""SessionContext - Transaction-aware session state.

This module implements the core SessionContext dataclass which captures all
state for an Ontos session and provides transaction support for file operations.

Per v2.8 implementation plan, SessionContext:
- Is the single source of truth for repository configuration
- Buffers file operations for later commit
- Applies buffered writes sequentially during commit
- Uses cross-platform advisory locking to serialize commit attempts
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum
import errno
import os
import secrets
import stat
import tempfile
import time

from ontos.core.locking import (
    WorkspaceBinding,
    WorkspaceLockGuard,
    close_lock_resources,
    open_workspace_guard,
    open_lock_file,
    set_non_inheritable,
    try_acquire_exclusive,
    try_acquire_workspace_guard,
    verify_lock_file_binding,
    verify_workspace_binding,
    verify_workspace_guard,
)


class FileOperation(Enum):
    """Types of file operations that can be buffered."""
    WRITE = "write"
    DELETE = "delete"
    MOVE = "move"


@dataclass
class PendingWrite:
    """A buffered file operation."""
    operation: FileOperation
    path: Path
    content: Optional[str] = None  # For WRITE
    destination: Optional[Path] = None  # For MOVE


@dataclass
class _DirectoryAnchor:
    """Pinned parent directory used for race-safe filesystem operations."""

    path: Path
    fd: Optional[int] = None
    windows_handles: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class _EntryBinding:
    """No-follow identity captured while a temporary entry is still open."""

    device: int
    inode: int
    file_type: int


@dataclass
class _CommitRecord:
    """Prepared operation and its rollback state."""

    operation: FileOperation
    path: Path
    destination: Optional[Path] = None
    final_anchor: Optional[_DirectoryAnchor] = None
    source_anchor: Optional[_DirectoryAnchor] = None
    source_binding: Optional[_EntryBinding] = None
    temp_name: Optional[str] = None
    temp_binding: Optional[_EntryBinding] = None
    backup_name: Optional[str] = None
    backup_binding: Optional[_EntryBinding] = None
    backup_has_original: bool = False
    applied: bool = False


@dataclass
class SessionContext:
    """Captures all state for an Ontos session.

    This is the single source of truth for:
    - Repository configuration
    - Environment state
    - Pending file operations (transaction buffer)

    SCOPE LIMITS (v2.8):
    SessionContext should NOT:
    - Handle output formatting (that's OutputHandler's job)
    - Contain I/O providers (keep git calls as marked impure functions)
    - Cache parsed documents (keep it focused on transaction state)
    - Grow beyond config + env + writes + diagnostics
    """
    # Immutable state (set at creation)
    repo_root: Path
    config: Dict
    cwd: Path = field(default_factory=Path.cwd)
    env: Dict[str, str] = field(default_factory=lambda: dict(os.environ))

    # Lock ownership (v4.1 A1 — single-lock discipline).
    # When True (default), commit() acquires and releases an advisory lock on
    # <repo_root>/.ontos.lock around the critical section. When False,
    # commit() assumes the caller already holds that flock (for example,
    # via an outer workspace-lock context manager). The outer owner must
    # provide ``external_lock_verifier``; acquisition fails closed without
    # that bound proof. See the v4.1 spec addendum A1 for the full contract.
    owns_lock: bool = True

    # Optional identity captured by an outer preflight. MCP write tools pass
    # this through their workspace-lock boundary so an ``owns_lock=False``
    # context cannot adopt a replacement directory after validation.
    expected_workspace_binding: Optional[WorkspaceBinding] = None

    # Typed guard supplied by an outer lock owner. MCP uses this to bind its
    # ``workspace_lock`` handles to the inner ``owns_lock=False`` transaction.
    external_lock_guard: Optional[WorkspaceLockGuard] = field(
        default=None,
        repr=False,
    )

    # Mutable state (changes during session)
    pending_writes: List[PendingWrite] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    _lock_handle: Optional[object] = field(default=None, init=False, repr=False)
    _root_lock_fd: Optional[int] = field(default=None, init=False, repr=False)
    _workspace_binding: Optional[_EntryBinding] = field(
        default=None,
        init=False,
        repr=False,
    )

    @classmethod
    def from_repo(cls, repo_root: Path) -> 'SessionContext':
        """Factory method to create context from repository path.

        This encapsulates config loading logic.
        
        Args:
            repo_root: Path to the repository root.
            
        Returns:
            SessionContext instance with loaded configuration.
        """
        # Build a config dict from the resolved settings
        config = {}
        config_keys = [
            'DOCS_DIR', 'AUTO_ARCHIVE_ON_PUSH', 'AUTO_CONSOLIDATE',
            'LOG_RETENTION_COUNT', 'ONTOS_MODE', 'DEFAULT_SOURCE',
            'SKIP_PATTERNS', 'LOGS_DIR', 'SCAN_DIRECTORIES'
        ]
        
        # Try to load config values
        try:
            import ontos_config
            for key in config_keys:
                if hasattr(ontos_config, key):
                    config[key] = getattr(ontos_config, key)
        except ImportError:
            pass
            
        return cls(repo_root=repo_root, config=config)

    def buffer_write(self, path: Path, content: str) -> None:
        """Buffer a file write for later commit.
        
        Args:
            path: Target file path.
            content: Content to write.
        """
        self._bind_existing_workspace()
        self.pending_writes.append(PendingWrite(
            operation=FileOperation.WRITE,
            path=path,
            content=content
        ))

    def buffer_delete(self, path: Path) -> None:
        """Buffer a file deletion for later commit.
        
        Args:
            path: File path to delete.
        """
        self._bind_existing_workspace()
        self.pending_writes.append(PendingWrite(
            operation=FileOperation.DELETE,
            path=path
        ))

    def buffer_move(self, source: Path, destination: Path) -> None:
        """Buffer a file move for later commit.
        
        Args:
            source: Source file path.
            destination: Destination file path.
        """
        self._bind_existing_workspace()
        self.pending_writes.append(PendingWrite(
            operation=FileOperation.MOVE,
            path=source,
            destination=destination
        ))

    def _bind_existing_workspace(self) -> None:
        """Pin an existing root when mutation intent is first buffered.

        Buffering historically permits a not-yet-created root, so absence is
        deferred to commit.  An existing root is bound immediately; replacing
        it between buffering and commit is then rejected.
        """
        try:
            self._workspace_root()
        except (FileNotFoundError, ValueError):
            return

    def create_text_file_exclusively(self, path: Path, content: str) -> Path:
        """Create one workspace-contained UTF-8 file without following links.

        This is the collision-refusing counterpart to :meth:`commit`.  It is
        used by commands whose contract is "create once" rather than
        "replace", while retaining the same pinned-parent and no-follow path
        guarantees as buffered writes.
        """
        candidate = self._safe_workspace_path(path, "operation path")
        anchor = self._open_parent_anchor(candidate, create=True)
        fd = -1
        created_info: Optional[os.stat_result] = None
        try:
            self._verify_anchor_binding(anchor)
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            flags |= getattr(os, "O_NOFOLLOW", 0)
            flags |= getattr(os, "O_CLOEXEC", 0)
            if anchor.fd is not None:
                fd = os.open(candidate.name, flags, 0o644, dir_fd=anchor.fd)
            else:
                fd = os.open(candidate, flags, 0o644)
            created_info = os.fstat(fd)

            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                fd = -1
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())

            self._verify_anchor_binding(anchor)
            visible_info = self._entry_stat(anchor, candidate.name)
            if visible_info is None or created_info is None or (
                visible_info.st_dev,
                visible_info.st_ino,
            ) != (created_info.st_dev, created_info.st_ino):
                raise RuntimeError(
                    f"Workspace entry changed during exclusive create: {candidate}"
                )
            if anchor.fd is not None:
                os.fsync(anchor.fd)
            return candidate
        except BaseException:
            if fd >= 0:
                os.close(fd)
            if created_info is not None:
                try:
                    visible_info = self._entry_stat(anchor, candidate.name)
                    if visible_info is not None and (
                        visible_info.st_dev,
                        visible_info.st_ino,
                    ) == (created_info.st_dev, created_info.st_ino):
                        self._unlink_entry(anchor, candidate.name, missing_ok=True)
                except OSError:
                    pass
            raise
        finally:
            self._close_anchor(anchor)

    def commit(self) -> List[Path]:
        """Execute all buffered operations from the current session.

        Writes and moves stage temporary files before applying updates. The
        commit is best-effort across buffered operations, not a global
        transactional two-phase commit.

        Returns:
            List of paths successfully modified.

        Raises:
            IOError: If a write operation fails.
            RuntimeError: If lock cannot be acquired.
        """
        if not self.pending_writes:
            return []

        lock_path = self.repo_root / ".ontos.lock"
        if not self._acquire_lock(lock_path):
            raise RuntimeError(
                "Could not acquire write lock. "
                "Another Ontos process may be running."
            )

        staged: List[_CommitRecord] = []
        anchors: Dict[Path, _DirectoryAnchor] = {}
        modified: List[Path] = []

        def anchor_for(path: Path, *, create: bool) -> _DirectoryAnchor:
            existing = anchors.get(path.parent)
            if existing is not None:
                return existing
            opened = self._open_parent_anchor(path, create=create)
            anchors[path.parent] = opened
            return opened

        try:
            operations = self._prepare_operations()

            # Phase 1: stage every write before changing a destination.
            for op in operations:
                if op.operation == FileOperation.WRITE:
                    final_anchor = anchor_for(op.path, create=True)
                    temp_name, temp_binding = self._stage_text(
                        final_anchor,
                        op.path.name,
                        op.content or "",
                    )
                    staged.append(
                        _CommitRecord(
                            op.operation,
                            op.path,
                            final_anchor=final_anchor,
                            temp_name=temp_name,
                            temp_binding=temp_binding,
                        )
                    )
                elif op.operation == FileOperation.DELETE:
                    try:
                        final_anchor = anchor_for(op.path, create=False)
                    except FileNotFoundError:
                        continue
                    source_binding = self._existing_regular_binding(
                        final_anchor,
                        op.path.name,
                        "delete source",
                    )
                    if source_binding is not None:
                        staged.append(
                            _CommitRecord(
                                op.operation,
                                op.path,
                                final_anchor=final_anchor,
                                source_binding=source_binding,
                            )
                        )
                elif op.operation == FileOperation.MOVE:
                    try:
                        source_anchor = anchor_for(op.path, create=False)
                    except FileNotFoundError:
                        continue
                    source_binding = self._existing_regular_binding(
                        source_anchor,
                        op.path.name,
                        "move source",
                    )
                    if source_binding is not None:
                        assert op.destination is not None
                        final_anchor = anchor_for(
                            op.destination,
                            create=True,
                        )
                        staged.append(
                            _CommitRecord(
                                op.operation,
                                op.path,
                                destination=op.destination,
                                final_anchor=final_anchor,
                                source_anchor=source_anchor,
                                source_binding=source_binding,
                            )
                        )

            # Phase 2: mutate entries relative to pinned parent handles. A
            # concurrent rename or symlink swap can invalidate the visible
            # pathname, but cannot redirect these operations outside the
            # workspace directory that was opened without following links.
            for record in staged:
                final = record.destination or record.path
                assert record.final_anchor is not None
                self._verify_anchor_binding(record.final_anchor)

                if record.operation == FileOperation.DELETE:
                    assert record.source_binding is not None
                    self._verify_entry_binding(
                        record.final_anchor,
                        final.name,
                        record.source_binding,
                        "delete source",
                    )

                final_info = self._entry_stat(record.final_anchor, final.name)
                if record.operation == FileOperation.DELETE and final_info is None:
                    raise RuntimeError(
                        f"delete source disappeared during commit: {record.path}"
                    )
                if final_info is not None:
                    if record.operation == FileOperation.DELETE:
                        assert record.source_binding is not None
                        original_binding = record.source_binding
                    else:
                        original_binding = self._regular_binding(
                            final_info,
                            record.final_anchor.path / final.name,
                            "destination",
                        )
                    (
                        record.backup_name,
                        record.backup_binding,
                    ) = self._reserve_backup(
                        record.final_anchor,
                        final.name,
                    )
                    reservation_binding = record.backup_binding
                    assert reservation_binding is not None
                    try:
                        self._verify_entry_binding(
                            record.final_anchor,
                            record.backup_name,
                            record.backup_binding,
                            "commit backup reservation",
                        )
                        self._verify_entry_binding(
                            record.final_anchor,
                            final.name,
                            original_binding,
                            "commit destination",
                        )
                        self._replace_entry(
                            record.final_anchor,
                            final.name,
                            record.final_anchor,
                            record.backup_name,
                            source_binding=original_binding,
                            destination_binding=record.backup_binding,
                        )
                    except BaseException as exc:
                        # A rename can complete and still surface an ambiguous
                        # exception. Reconcile the name before deciding whether
                        # it is an empty reservation or the recovery copy.
                        backup_path = (
                            record.final_anchor.path / record.backup_name
                        )
                        backup_info = self._entry_stat(
                            record.final_anchor,
                            record.backup_name,
                        )
                        actual_binding = None
                        if backup_info is not None:
                            try:
                                actual_binding = self._regular_binding(
                                    backup_info,
                                    backup_path,
                                    "commit backup",
                                )
                            except RuntimeError:
                                pass
                        if actual_binding == original_binding:
                            record.backup_has_original = True
                            record.backup_binding = original_binding
                            raise
                        if actual_binding == reservation_binding:
                            final_now = self._entry_stat(
                                record.final_anchor,
                                final.name,
                            )
                            final_binding = (
                                self._regular_binding(
                                    final_now,
                                    record.final_anchor.path / final.name,
                                    "commit destination",
                                )
                                if final_now is not None
                                else None
                            )
                            if final_binding == original_binding:
                                self._unlink_bound_entry(
                                    record.final_anchor,
                                    record.backup_name,
                                    reservation_binding,
                                    "commit backup reservation",
                                )
                                record.backup_name = None
                                record.backup_binding = None
                                raise
                        raise RuntimeError(
                            f"{exc}; ambiguous backup rename state; recovery "
                            f"entry preserved at {backup_path}"
                        ) from exc
                    record.backup_has_original = True
                    record.backup_binding = original_binding
                    self._verify_entry_binding(
                        record.final_anchor,
                        record.backup_name,
                        original_binding,
                        "commit recovery backup",
                    )
                    if record.operation == FileOperation.DELETE:
                        self._verify_entry_absent(
                            record.final_anchor,
                            final.name,
                            "deleted destination",
                        )

                if record.operation == FileOperation.WRITE:
                    assert record.temp_name is not None
                    assert record.temp_binding is not None
                    self._verify_entry_binding(
                        record.final_anchor,
                        record.temp_name,
                        record.temp_binding,
                        "staged write",
                    )
                    self._replace_entry(
                        record.final_anchor,
                        record.temp_name,
                        record.final_anchor,
                        final.name,
                        source_binding=record.temp_binding,
                        destination_binding=None,
                    )
                    record.temp_name = None
                    record.applied = True
                    self._verify_entry_binding(
                        record.final_anchor,
                        final.name,
                        record.temp_binding,
                        "committed write",
                    )
                elif record.operation == FileOperation.MOVE:
                    assert record.source_anchor is not None
                    assert record.source_binding is not None
                    self._verify_anchor_binding(record.source_anchor)
                    self._verify_entry_binding(
                        record.source_anchor,
                        record.path.name,
                        record.source_binding,
                        "move source",
                    )
                    self._replace_entry(
                        record.source_anchor,
                        record.path.name,
                        record.final_anchor,
                        final.name,
                        source_binding=record.source_binding,
                        destination_binding=None,
                    )
                    record.applied = True
                    self._verify_entry_binding(
                        record.final_anchor,
                        final.name,
                        record.source_binding,
                        "moved destination",
                    )
                # DELETE is applied by moving the original to its backup.

                record.applied = True
                self._verify_anchor_binding(record.final_anchor)
                if record.source_anchor is not None:
                    self._verify_anchor_binding(record.source_anchor)
                modified.append(final)
                self._fsync_anchor(record.final_anchor)
                if (
                    record.operation == FileOperation.MOVE
                    and record.source_anchor is not None
                    and record.source_anchor is not record.final_anchor
                ):
                    self._fsync_anchor(record.source_anchor)

            # Keep recovery copies until the root and lock identities have
            # been revalidated after every mutation.  A tampered visible
            # lock then enters the normal rollback path instead of allowing a
            # successful commit under an orphaned advisory lock.
            self._verify_held_lock(lock_path)

            for record in staged:
                if record.backup_name is not None:
                    try:
                        assert record.final_anchor is not None
                        assert record.backup_binding is not None
                        self._verify_entry_binding(
                            record.final_anchor,
                            record.backup_name,
                            record.backup_binding,
                            "commit recovery backup",
                        )
                        self._unlink_entry(
                            record.final_anchor,
                            record.backup_name,
                            missing_ok=True,
                        )
                    except OSError as exc:
                        backup = record.final_anchor.path / record.backup_name
                        self.warn(f"Could not remove commit backup {backup}: {exc}")
                    else:
                        record.backup_name = None
                        record.backup_binding = None
                        record.backup_has_original = False

        except BaseException as e:
            rollback_errors = self._rollback_records(staged)
            detail = f"Commit failed: {e}"
            if rollback_errors:
                detail += "; rollback failed: " + "; ".join(rollback_errors)
            self.error(detail)
            raise

        finally:
            for anchor in reversed(list(anchors.values())):
                self._close_anchor(anchor)
            self._release_lock(lock_path)
            self.pending_writes.clear()

        return modified

    def _prepare_operations(self) -> List[PendingWrite]:
        """Normalize, contain, and de-duplicate buffered operations."""
        prepared: List[PendingWrite] = []
        used_paths: set[Path] = set()

        for op in self.pending_writes:
            path = self._safe_workspace_path(op.path, "operation path")
            destination = None
            if op.operation == FileOperation.WRITE and op.content is None:
                raise ValueError(f"Buffered write has no content: {path}")
            if op.operation == FileOperation.MOVE:
                if op.destination is None:
                    raise ValueError(f"Buffered move has no destination: {path}")
                destination = self._safe_workspace_path(
                    op.destination,
                    "move destination",
                )
                if destination == path:
                    raise ValueError(f"Move source and destination are identical: {path}")

            operation_paths = {path}
            if destination is not None:
                operation_paths.add(destination)
            duplicate = operation_paths & used_paths
            if duplicate:
                rendered = ", ".join(str(item) for item in sorted(duplicate))
                raise ValueError(f"Multiple buffered operations target the same path: {rendered}")
            used_paths.update(operation_paths)
            prepared.append(
                PendingWrite(
                    operation=op.operation,
                    path=path,
                    content=op.content,
                    destination=destination,
                )
            )

        return prepared

    def _safe_workspace_path(self, path: Path, label: str) -> Path:
        """Return a lexical workspace path without trusting symlink resolution."""
        root_input = Path(os.path.abspath(self.repo_root.expanduser()))
        root = self._workspace_root()
        candidate = path.expanduser()
        if candidate.is_absolute():
            candidate = Path(os.path.abspath(candidate))
            relative = None
            for base in (root_input, root):
                try:
                    relative = candidate.relative_to(base)
                    break
                except ValueError:
                    continue
            if relative is None:
                raise ValueError(f"{label} is outside the workspace: {path}")
            candidate = root / relative
        else:
            candidate = Path(os.path.abspath(root / candidate))

        if not candidate.is_relative_to(root):
            raise ValueError(f"{label} is outside the workspace: {path}")
        if candidate == root:
            raise ValueError(f"{label} must name a file inside the workspace: {path}")

        current = root
        relative = candidate.relative_to(root)
        for component in relative.parts[:-1]:
            current /= component
            try:
                info = os.lstat(current)
            except FileNotFoundError:
                break
            if stat.S_ISLNK(info.st_mode):
                raise ValueError(
                    f"{label} must not contain a symlinked directory: {current}"
                )
            if not stat.S_ISDIR(info.st_mode):
                raise ValueError(
                    f"{label} parent component must be a directory: {current}"
                )

        try:
            info = os.lstat(candidate)
        except FileNotFoundError:
            pass
        else:
            if stat.S_ISLNK(info.st_mode):
                raise ValueError(f"{label} must not be a symlink: {candidate}")
            if not stat.S_ISREG(info.st_mode):
                raise ValueError(f"{label} must name a regular file: {path}")
        return candidate

    def _workspace_root(self) -> Path:
        """Return a real workspace root while rejecting a redirected root."""
        root_input = Path(os.path.abspath(self.repo_root.expanduser()))
        info = os.lstat(root_input)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        file_attributes = getattr(info, "st_file_attributes", 0)
        if stat.S_ISLNK(info.st_mode) or (
            reparse_flag and file_attributes & reparse_flag
        ):
            raise ValueError(
                f"workspace root must not be a symlink or reparse point: {root_input}"
            )
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError(f"workspace root must be a directory: {root_input}")
        binding = self._binding_from_stat(info)
        public_binding = (binding.device, binding.inode, binding.file_type)
        if (
            self.expected_workspace_binding is not None
            and public_binding != self.expected_workspace_binding
        ):
            raise RuntimeError(
                f"workspace root changed since preflight: {root_input}"
            )
        if self._workspace_binding is None:
            self._workspace_binding = binding
        elif binding != self._workspace_binding:
            raise RuntimeError(
                f"workspace root changed during session: {root_input}"
            )
        return root_input.resolve(strict=True)

    def _open_parent_anchor(self, path: Path, *, create: bool) -> _DirectoryAnchor:
        """Pin every parent component without following links.

        POSIX mutations use ``*at`` operations relative to the returned file
        descriptor. Windows keeps non-delete-sharing handles open for every
        component, preventing a directory from being renamed or exchanged
        while path-based CRT operations run.
        """
        if os.name == "posix":
            return self._open_posix_parent(path, create=create)
        if os.name == "nt":  # pragma: no cover - exercised by Windows CI.
            return self._open_windows_parent(path, create=create)

        if create:  # pragma: no cover - unsupported platform fallback.
            path.parent.mkdir(parents=True, exist_ok=True)
        elif not path.parent.is_dir():
            raise FileNotFoundError(path.parent)
        self._reject_parent_symlinks(path)
        return _DirectoryAnchor(path=path.parent)

    def _open_posix_parent(self, path: Path, *, create: bool) -> _DirectoryAnchor:
        root = self._workspace_root()
        relative_parent = path.parent.relative_to(root)
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        flags |= getattr(os, "O_CLOEXEC", 0)
        current_fd = os.open(root, flags)
        try:
            if self._binding_from_stat(os.fstat(current_fd)) != self._workspace_binding:
                raise RuntimeError(
                    f"workspace root changed before directory pin: {root}"
                )
            for component in relative_parent.parts:
                try:
                    next_fd = os.open(component, flags, dir_fd=current_fd)
                except FileNotFoundError:
                    if not create:
                        raise
                    try:
                        os.mkdir(component, 0o755, dir_fd=current_fd)
                    except FileExistsError:
                        # A racing creator is safe only if the no-follow open
                        # below proves it created a real directory.
                        pass
                    next_fd = os.open(component, flags, dir_fd=current_fd)
                except OSError as exc:
                    if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                        raise ValueError(
                            f"operation path parent must contain only real "
                            f"directories: {path.parent}"
                        ) from exc
                    raise
                os.close(current_fd)
                current_fd = next_fd
            return _DirectoryAnchor(path=path.parent, fd=current_fd)
        except BaseException:
            os.close(current_fd)
            raise

    def _open_windows_parent(
        self,
        path: Path,
        *,
        create: bool,
    ) -> _DirectoryAnchor:
        """Pin a Windows directory chain against rename/reparse races."""
        root = self._workspace_root()
        relative_parent = path.parent.relative_to(root)
        handles: List[int] = []
        current = root
        try:
            handles.append(self._pin_windows_directory(current))
            if self._binding_from_stat(os.lstat(current)) != self._workspace_binding:
                raise RuntimeError(
                    f"workspace root changed before directory pin: {root}"
                )
            for component in relative_parent.parts:
                current /= component
                try:
                    os.lstat(current)
                except FileNotFoundError:
                    if not create:
                        raise
                    try:
                        current.mkdir()
                    except FileExistsError:
                        pass
                handles.append(self._pin_windows_directory(current))
            return _DirectoryAnchor(path=path.parent, windows_handles=handles)
        except BaseException:
            self._close_windows_handles(handles)
            raise

    @staticmethod
    def _pin_windows_directory(path: Path) -> int:
        """Open one directory without following reparse points or sharing delete."""
        import ctypes  # pragma: no cover - Windows only.
        from ctypes import wintypes  # pragma: no cover - Windows only.

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create_file = kernel32.CreateFileW
        create_file.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        )
        create_file.restype = wintypes.HANDLE

        file_read_attributes = 0x0080
        file_share_read = 0x00000001
        file_share_write = 0x00000002
        open_existing = 3
        backup_semantics = 0x02000000
        open_reparse_point = 0x00200000
        handle = create_file(
            str(path),
            file_read_attributes,
            file_share_read | file_share_write,
            None,
            open_existing,
            backup_semantics | open_reparse_point,
            None,
        )
        invalid_handle = ctypes.c_void_p(-1).value
        if handle == invalid_handle:
            raise ctypes.WinError(ctypes.get_last_error())

        get_attributes = kernel32.GetFileAttributesW
        get_attributes.argtypes = (wintypes.LPCWSTR,)
        get_attributes.restype = wintypes.DWORD
        attributes = get_attributes(str(path))
        invalid_attributes = 0xFFFFFFFF
        is_directory = 0x00000010
        is_reparse_point = 0x00000400
        if (
            attributes == invalid_attributes
            or not attributes & is_directory
            or attributes & is_reparse_point
        ):
            kernel32.CloseHandle(handle)
            if attributes & is_reparse_point:
                raise ValueError(f"operation path must not contain a reparse point: {path}")
            raise ValueError(f"operation path parent must be a directory: {path}")
        return int(handle)

    @staticmethod
    def _close_windows_handles(handles: List[int]) -> None:
        if not handles:
            return
        import ctypes  # pragma: no cover - Windows only.
        from ctypes import wintypes  # pragma: no cover - Windows only.

        close_handle = ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle
        close_handle.argtypes = (wintypes.HANDLE,)
        for handle in reversed(handles):
            close_handle(wintypes.HANDLE(handle))

    def _close_anchor(self, anchor: _DirectoryAnchor) -> None:
        if anchor.fd is not None:
            os.close(anchor.fd)
            anchor.fd = None
        if anchor.windows_handles:
            self._close_windows_handles(anchor.windows_handles)
            anchor.windows_handles.clear()

    def _verify_anchor_binding(self, anchor: _DirectoryAnchor) -> None:
        """Fail closed when the visible pathname no longer names the pin."""
        if anchor.fd is not None:
            probe = self._open_posix_parent(
                anchor.path / ".ontos-anchor-probe",
                create=False,
            )
            try:
                pinned = os.fstat(anchor.fd)
                visible = os.fstat(probe.fd)  # type: ignore[arg-type]
                if (pinned.st_dev, pinned.st_ino) != (visible.st_dev, visible.st_ino):
                    raise RuntimeError(
                        f"Workspace directory changed during commit: {anchor.path}"
                    )
            finally:
                self._close_anchor(probe)
            return

        # Windows handles exclude FILE_SHARE_DELETE and therefore pin every
        # component. This recheck catches a pre-existing reparse point on
        # generic platforms and makes the invariant explicit.
        self._reject_parent_symlinks(anchor.path / ".ontos-anchor-probe")

    def _reject_parent_symlinks(self, path: Path) -> None:
        root = self._workspace_root()
        current = root
        for component in path.parent.relative_to(root).parts:
            current /= component
            info = os.lstat(current)
            if stat.S_ISLNK(info.st_mode):
                raise ValueError(f"operation path must not contain a symlink: {current}")
            if not stat.S_ISDIR(info.st_mode):
                raise ValueError(f"operation path parent must be a directory: {current}")

    def _entry_stat(self, anchor: _DirectoryAnchor, name: str) -> Optional[os.stat_result]:
        try:
            if anchor.fd is not None:
                return os.stat(name, dir_fd=anchor.fd, follow_symlinks=False)
            return os.lstat(anchor.path / name)
        except FileNotFoundError:
            return None

    def _existing_regular_binding(
        self,
        anchor: _DirectoryAnchor,
        name: str,
        label: str,
    ) -> Optional[_EntryBinding]:
        info = self._entry_stat(anchor, name)
        if info is None:
            return None
        return self._regular_binding(info, anchor.path / name, label)

    @staticmethod
    def _binding_from_stat(info: os.stat_result) -> _EntryBinding:
        return _EntryBinding(
            device=info.st_dev,
            inode=info.st_ino,
            file_type=stat.S_IFMT(info.st_mode),
        )

    def _regular_binding(
        self,
        info: os.stat_result,
        path: Path,
        label: str,
    ) -> _EntryBinding:
        if not stat.S_ISREG(info.st_mode):
            raise RuntimeError(f"{label} must remain a regular file: {path}")
        return self._binding_from_stat(info)

    def _verify_entry_binding(
        self,
        anchor: _DirectoryAnchor,
        name: str,
        expected: _EntryBinding,
        label: str,
    ) -> None:
        """Revalidate an entry by no-follow identity immediately before use."""
        path = anchor.path / name
        info = self._entry_stat(anchor, name)
        if info is None:
            raise RuntimeError(f"{label} disappeared during commit: {path}")
        actual = self._regular_binding(info, path, label)
        if actual != expected:
            raise RuntimeError(f"{label} changed during commit: {path}")

    def _verify_entry_absent(
        self,
        anchor: _DirectoryAnchor,
        name: str,
        label: str,
    ) -> None:
        """Require an anchored entry name to remain unoccupied."""
        if self._entry_stat(anchor, name) is not None:
            raise RuntimeError(
                f"{label} appeared during commit: {anchor.path / name}"
            )

    def _create_unique_file(
        self,
        anchor: _DirectoryAnchor,
        *,
        prefix: str,
        suffix: str,
    ) -> tuple[int, str]:
        if anchor.fd is None:
            fd, path = tempfile.mkstemp(
                dir=str(anchor.path),
                prefix=prefix,
                suffix=suffix,
            )
            return fd, Path(path).name

        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        flags |= getattr(os, "O_CLOEXEC", 0)
        while True:
            name = f"{prefix}{secrets.token_hex(12)}{suffix}"
            try:
                fd = os.open(name, flags, 0o600, dir_fd=anchor.fd)
            except FileExistsError:
                continue
            return fd, name

    def _stage_text(
        self,
        anchor: _DirectoryAnchor,
        final_name: str,
        content: str,
    ) -> tuple[str, _EntryBinding]:
        """Write and fsync UTF-8 content to an anchored exclusive temp file."""
        self._verify_anchor_binding(anchor)
        final_info = self._entry_stat(anchor, final_name)
        if final_info is not None:
            if stat.S_ISLNK(final_info.st_mode):
                raise ValueError(
                    f"destination must not be a symlink: {anchor.path / final_name}"
                )
            if not stat.S_ISREG(final_info.st_mode):
                raise ValueError(
                    f"destination must be a regular file: {anchor.path / final_name}"
                )

        fd, temp_name = self._create_unique_file(
            anchor,
            prefix=f".{final_name}.",
            suffix=".tmp",
        )
        staged_binding: Optional[_EntryBinding] = None
        try:
            staged_info = os.fstat(fd)
            staged_binding = self._regular_binding(
                staged_info,
                anchor.path / temp_name,
                "staged write",
            )
            if hasattr(os, "fchmod"):
                mode = stat.S_IMODE(final_info.st_mode) if final_info else 0o644
                os.fchmod(fd, mode)
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                fd = -1
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
                staged_info = os.fstat(handle.fileno())
            return temp_name, self._regular_binding(
                staged_info,
                anchor.path / temp_name,
                "staged write",
            )
        except BaseException:
            if fd >= 0:
                os.close(fd)
            if staged_binding is not None:
                try:
                    self._unlink_bound_entry(
                        anchor,
                        temp_name,
                        staged_binding,
                        "failed staged write",
                    )
                except (OSError, RuntimeError):
                    # A changed temp entry belongs to the racer. Leave it
                    # untouched rather than unlinking an unbound name.
                    pass
            raise

    def _reserve_backup(
        self,
        anchor: _DirectoryAnchor,
        final_name: str,
    ) -> tuple[str, _EntryBinding]:
        fd, backup_name = self._create_unique_file(
            anchor,
            prefix=f".{final_name}.",
            suffix=".bak",
        )
        try:
            info = os.fstat(fd)
        finally:
            os.close(fd)
        return backup_name, self._regular_binding(
            info,
            anchor.path / backup_name,
            "commit backup reservation",
        )

    def _replace_entry(
        self,
        source_anchor: _DirectoryAnchor,
        source_name: str,
        destination_anchor: _DirectoryAnchor,
        destination_name: str,
        *,
        source_binding: _EntryBinding,
        destination_binding: Optional[_EntryBinding],
    ) -> None:
        self._verify_entry_binding(
            source_anchor,
            source_name,
            source_binding,
            "rename source",
        )
        if destination_binding is None:
            self._verify_entry_absent(
                destination_anchor,
                destination_name,
                "rename destination",
            )
        else:
            self._verify_entry_binding(
                destination_anchor,
                destination_name,
                destination_binding,
                "rename destination",
            )
        if source_anchor.fd is not None and destination_anchor.fd is not None:
            os.replace(
                source_name,
                destination_name,
                src_dir_fd=source_anchor.fd,
                dst_dir_fd=destination_anchor.fd,
            )
            return
        self._verify_anchor_binding(source_anchor)
        if destination_anchor is not source_anchor:
            self._verify_anchor_binding(destination_anchor)
        os.replace(
            source_anchor.path / source_name,
            destination_anchor.path / destination_name,
        )

    def _unlink_bound_entry(
        self,
        anchor: _DirectoryAnchor,
        name: str,
        binding: _EntryBinding,
        label: str,
    ) -> None:
        """Unlink only the entry whose no-follow identity was captured."""
        self._verify_entry_binding(anchor, name, binding, label)
        self._unlink_entry(anchor, name, missing_ok=False)

    @staticmethod
    def _unlink_entry(
        anchor: _DirectoryAnchor,
        name: str,
        *,
        missing_ok: bool,
    ) -> None:
        try:
            if anchor.fd is not None:
                os.unlink(name, dir_fd=anchor.fd)
            else:
                os.unlink(anchor.path / name)
        except FileNotFoundError:
            if not missing_ok:
                raise

    def _rollback_records(self, records: List[_CommitRecord]) -> List[str]:
        errors: List[str] = []
        for record in reversed(records):
            final = record.destination or record.path
            assert record.final_anchor is not None
            can_restore_destination = True

            if record.operation == FileOperation.MOVE and record.applied:
                assert record.source_anchor is not None
                assert record.source_binding is not None
                try:
                    if self._entry_stat(record.final_anchor, final.name) is None:
                        raise RuntimeError(
                            "moved destination disappeared; original source "
                            f"cannot be restored: {final}"
                        )
                    self._replace_entry(
                        record.final_anchor,
                        final.name,
                        record.source_anchor,
                        record.path.name,
                        source_binding=record.source_binding,
                        destination_binding=None,
                    )
                    record.applied = False
                except (OSError, RuntimeError) as exc:
                    errors.append(f"could not restore move source {record.path}: {exc}")
                    can_restore_destination = False
            elif record.operation == FileOperation.WRITE and record.applied:
                assert record.temp_binding is not None
                try:
                    self._unlink_bound_entry(
                        record.final_anchor,
                        final.name,
                        record.temp_binding,
                        "failed committed write",
                    )
                    record.applied = False
                except (OSError, RuntimeError) as exc:
                    errors.append(f"could not remove failed write {final}: {exc}")
                    can_restore_destination = False

            if record.backup_has_original and record.backup_name is not None:
                backup_path = record.final_anchor.path / record.backup_name
                if can_restore_destination:
                    try:
                        if record.backup_binding is None:
                            raise RuntimeError(
                                f"recovery backup identity is unavailable: {backup_path}"
                            )
                        self._verify_entry_binding(
                            record.final_anchor,
                            record.backup_name,
                            record.backup_binding,
                            "commit recovery backup",
                        )
                        self._replace_entry(
                            record.final_anchor,
                            record.backup_name,
                            record.final_anchor,
                            final.name,
                            source_binding=record.backup_binding,
                            destination_binding=None,
                        )
                    except (OSError, RuntimeError) as exc:
                        errors.append(
                            f"could not restore {final}: {exc}; recovery backup "
                            f"preserved at {backup_path}"
                        )
                    else:
                        record.backup_name = None
                        record.backup_binding = None
                        record.backup_has_original = False
                else:
                    errors.append(
                        f"recovery backup preserved at {backup_path}"
                    )
            elif record.backup_name is not None:
                # A reservation that never received the original is disposable.
                try:
                    if record.backup_binding is None:
                        raise RuntimeError(
                            "backup reservation identity is unavailable"
                        )
                    self._unlink_bound_entry(
                        record.final_anchor,
                        record.backup_name,
                        record.backup_binding,
                        "commit backup reservation",
                    )
                except (OSError, RuntimeError) as exc:
                    errors.append(
                        f"could not remove empty backup reservation "
                        f"{record.final_anchor.path / record.backup_name}: {exc}"
                    )
                else:
                    record.backup_name = None
                    record.backup_binding = None

            if record.temp_name is not None:
                try:
                    if record.temp_binding is None:
                        raise RuntimeError("staged write identity is unavailable")
                    self._unlink_bound_entry(
                        record.final_anchor,
                        record.temp_name,
                        record.temp_binding,
                        "staged write cleanup",
                    )
                except (OSError, RuntimeError) as exc:
                    errors.append(
                        f"could not remove staged write "
                        f"{record.final_anchor.path / record.temp_name}: {exc}"
                    )
                else:
                    record.temp_name = None
        return errors

    @staticmethod
    def _fsync_anchor(anchor: _DirectoryAnchor) -> None:
        """Best-effort durability for rename metadata on supporting systems."""
        if anchor.fd is not None:
            try:
                os.fsync(anchor.fd)
            except OSError:
                pass
            return
        flags = getattr(os, "O_DIRECTORY", 0) | os.O_RDONLY
        try:
            fd = os.open(anchor.path, flags)
        except OSError:
            return
        try:
            os.fsync(fd)
        except OSError:
            pass
        finally:
            os.close(fd)

    def rollback(self) -> None:
        """Discard all buffered operations."""
        self.pending_writes.clear()

    def warn(self, message: str) -> None:
        """Record a warning (does not print).
        
        Args:
            message: Warning message to record.
        """
        self.warnings.append(message)

    def error(self, message: str) -> None:
        """Record an error (does not print).
        
        Args:
            message: Error message to record.
        """
        self.errors.append(message)

    def _acquire_lock(self, lock_path: Path, timeout: float = 5.0) -> bool:
        """Acquire an exclusive advisory lock for this workspace.

        When ``self.owns_lock`` is False the caller is expected to hold
        the flock on the workspace lockfile (acquired by an outer
        workspace-lock context manager) and this method is a no-op —
        see v4.1 spec addendum A1.
        """
        self._workspace_root()
        assert self._workspace_binding is not None
        workspace_binding = (
            self._workspace_binding.device,
            self._workspace_binding.inode,
            self._workspace_binding.file_type,
        )
        if not self.owns_lock:
            guard = self.external_lock_guard
            if not isinstance(guard, WorkspaceLockGuard):
                raise RuntimeError(
                    "owns_lock=False requires a bound outer lock guard"
                )
            if guard.workspace_binding != workspace_binding:
                raise RuntimeError(
                    "outer lock guard belongs to a different workspace"
                )
            guard.verify()
            return True

        guard_fd = open_workspace_guard(self.repo_root, workspace_binding)
        guard_acquired = False
        handle = None
        lock_acquired = False
        start = time.monotonic()
        try:
            while time.monotonic() - start < timeout:
                verify_workspace_binding(self.repo_root, workspace_binding)
                verify_workspace_guard(guard_fd, workspace_binding)
                if try_acquire_workspace_guard(guard_fd):
                    guard_acquired = True
                    break
                time.sleep(0.1)
            if not guard_acquired:
                if guard_fd is not None:
                    os.close(guard_fd)
                return False

            verify_workspace_binding(self.repo_root, workspace_binding)
            handle = open_lock_file(lock_path)
            set_non_inheritable(handle)
            verify_lock_file_binding(handle, lock_path)
            while time.monotonic() - start < timeout:
                try:
                    verify_workspace_binding(self.repo_root, workspace_binding)
                    verify_workspace_guard(guard_fd, workspace_binding)
                    verify_lock_file_binding(handle, lock_path)
                    if not try_acquire_exclusive(handle):
                        raise BlockingIOError
                    lock_acquired = True
                    verify_lock_file_binding(handle, lock_path)
                    verify_workspace_binding(self.repo_root, workspace_binding)
                except BlockingIOError:
                    time.sleep(0.1)
                    continue
                # flock succeeded — hand ownership of the handle to the
                # instance so _release_lock can close it.
                self._lock_handle = handle
                self._root_lock_fd = guard_fd
                return True
        except BaseException:
            # m-12: any non-BlockingIOError raised between open() and a
            # successful flock (signals, OSError from sleep, etc.) must
            # not leak the file handle. Close and re-raise.
            try:
                close_lock_resources(
                    handle,
                    lock_acquired=lock_acquired,
                    guard_fd=guard_fd,
                    guard_acquired=guard_acquired,
                )
            except BaseException:
                # Preserve the acquisition failure after exhausting cleanup.
                pass
            raise

        # Timed out waiting for the lock — close the handle and report.
        close_lock_resources(
            handle,
            lock_acquired=lock_acquired,
            guard_fd=guard_fd,
            guard_acquired=guard_acquired,
        )
        return False

    def _verify_held_lock(self, lock_path: Path) -> None:
        """Revalidate the root and active lock before discarding backups."""
        self._workspace_root()
        assert self._workspace_binding is not None
        workspace_binding = (
            self._workspace_binding.device,
            self._workspace_binding.inode,
            self._workspace_binding.file_type,
        )
        if not self.owns_lock:
            guard = self.external_lock_guard
            if not isinstance(guard, WorkspaceLockGuard):
                raise RuntimeError("bound outer lock guard is unavailable")
            if guard.workspace_binding != workspace_binding:
                raise RuntimeError(
                    "outer lock guard belongs to a different workspace"
                )
            guard.verify()
            return
        if self._lock_handle is None:
            raise RuntimeError("workspace lock handle is not held")
        verify_workspace_guard(self._root_lock_fd, workspace_binding)
        verify_workspace_binding(self.repo_root, workspace_binding)
        verify_lock_file_binding(self._lock_handle, lock_path)

    def _release_lock(self, lock_path: Path) -> None:
        """Release the file lock.

        When ``self.owns_lock`` is False this is a no-op — the caller owns
        the outer flock and is responsible for releasing it.

        Args:
            lock_path: Path to lock file.
        """
        _ = lock_path
        if not self.owns_lock:
            return
        handle = self._lock_handle
        guard_fd = self._root_lock_fd
        self._lock_handle = None
        self._root_lock_fd = None
        try:
            close_lock_resources(
                handle,
                lock_acquired=handle is not None,
                guard_fd=guard_fd,
                guard_acquired=guard_fd is not None,
            )
        except BaseException as exc:
            self.error(f"Workspace lock cleanup failed: {exc}")
