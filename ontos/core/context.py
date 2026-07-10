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
    release_exclusive,
    set_non_inheritable,
    try_acquire_exclusive,
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


@dataclass
class _CommitRecord:
    """Prepared operation and its rollback state."""

    operation: FileOperation
    path: Path
    destination: Optional[Path] = None
    final_anchor: Optional[_DirectoryAnchor] = None
    source_anchor: Optional[_DirectoryAnchor] = None
    temp_name: Optional[str] = None
    backup_name: Optional[str] = None
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
    # via an outer workspace-lock context manager) and _acquire_lock /
    # _release_lock become no-ops. See the v4.1 spec addendum A1 for
    # the full contract.
    owns_lock: bool = True

    # Mutable state (changes during session)
    pending_writes: List[PendingWrite] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    _lock_handle: Optional[object] = field(default=None, init=False, repr=False)

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
        self.pending_writes.append(PendingWrite(
            operation=FileOperation.MOVE,
            path=source,
            destination=destination
        ))

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
                    temp_name = self._stage_text(
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
                        )
                    )
                elif op.operation == FileOperation.DELETE:
                    try:
                        final_anchor = anchor_for(op.path, create=False)
                    except FileNotFoundError:
                        continue
                    if self._entry_is_regular(final_anchor, op.path.name):
                        staged.append(
                            _CommitRecord(
                                op.operation,
                                op.path,
                                final_anchor=final_anchor,
                            )
                        )
                elif op.operation == FileOperation.MOVE:
                    try:
                        source_anchor = anchor_for(op.path, create=False)
                    except FileNotFoundError:
                        continue
                    if self._entry_is_regular(source_anchor, op.path.name):
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

                if self._entry_is_regular(record.final_anchor, final.name):
                    record.backup_name = self._reserve_backup(
                        record.final_anchor,
                        final.name,
                    )
                    try:
                        self._replace_entry(
                            record.final_anchor,
                            final.name,
                            record.final_anchor,
                            record.backup_name,
                        )
                    except BaseException:
                        # The reserved name is only an empty placeholder until
                        # the rename succeeds. It must never be mistaken for a
                        # recovery copy.
                        self._unlink_entry(
                            record.final_anchor,
                            record.backup_name,
                            missing_ok=True,
                        )
                        record.backup_name = None
                        raise
                    record.backup_has_original = True

                if record.operation == FileOperation.WRITE:
                    assert record.temp_name is not None
                    self._replace_entry(
                        record.final_anchor,
                        record.temp_name,
                        record.final_anchor,
                        final.name,
                    )
                    record.temp_name = None
                elif record.operation == FileOperation.MOVE:
                    assert record.source_anchor is not None
                    self._verify_anchor_binding(record.source_anchor)
                    if not self._entry_is_regular(
                        record.source_anchor,
                        record.path.name,
                    ):
                        raise FileNotFoundError(record.path)
                    self._replace_entry(
                        record.source_anchor,
                        record.path.name,
                        record.final_anchor,
                        final.name,
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

            for record in staged:
                if record.backup_name is not None:
                    try:
                        assert record.final_anchor is not None
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
        root = root_input.resolve()
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
        root = self.repo_root.expanduser().resolve()
        relative_parent = path.parent.relative_to(root)
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        flags |= getattr(os, "O_CLOEXEC", 0)
        current_fd = os.open(root, flags)
        try:
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
        root = self.repo_root.expanduser().resolve()
        relative_parent = path.parent.relative_to(root)
        handles: List[int] = []
        current = root
        try:
            handles.append(self._pin_windows_directory(current))
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
        root = self.repo_root.expanduser().resolve()
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

    def _entry_is_regular(self, anchor: _DirectoryAnchor, name: str) -> bool:
        info = self._entry_stat(anchor, name)
        if info is None:
            return False
        path = anchor.path / name
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(f"destination must not be a symlink: {path}")
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"operation path must name a regular file: {path}")
        return True

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
    ) -> str:
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
        try:
            if hasattr(os, "fchmod"):
                mode = stat.S_IMODE(final_info.st_mode) if final_info else 0o644
                os.fchmod(fd, mode)
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                fd = -1
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            return temp_name
        except BaseException:
            if fd >= 0:
                os.close(fd)
            self._unlink_entry(anchor, temp_name, missing_ok=True)
            raise

    def _reserve_backup(self, anchor: _DirectoryAnchor, final_name: str) -> str:
        fd, backup_name = self._create_unique_file(
            anchor,
            prefix=f".{final_name}.",
            suffix=".bak",
        )
        os.close(fd)
        return backup_name

    def _replace_entry(
        self,
        source_anchor: _DirectoryAnchor,
        source_name: str,
        destination_anchor: _DirectoryAnchor,
        destination_name: str,
    ) -> None:
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
                try:
                    if self._entry_stat(record.final_anchor, final.name) is not None:
                        self._replace_entry(
                            record.final_anchor,
                            final.name,
                            record.source_anchor,
                            record.path.name,
                        )
                    record.applied = False
                except OSError as exc:
                    errors.append(f"could not restore move source {record.path}: {exc}")
                    can_restore_destination = False
            elif record.operation == FileOperation.WRITE and record.applied:
                try:
                    self._unlink_entry(
                        record.final_anchor,
                        final.name,
                        missing_ok=True,
                    )
                    record.applied = False
                except OSError as exc:
                    errors.append(f"could not remove failed write {final}: {exc}")
                    can_restore_destination = False

            if record.backup_has_original and record.backup_name is not None:
                backup_path = record.final_anchor.path / record.backup_name
                if can_restore_destination:
                    try:
                        self._replace_entry(
                            record.final_anchor,
                            record.backup_name,
                            record.final_anchor,
                            final.name,
                        )
                    except OSError as exc:
                        errors.append(
                            f"could not restore {final}: {exc}; recovery backup "
                            f"preserved at {backup_path}"
                        )
                    else:
                        record.backup_name = None
                        record.backup_has_original = False
                else:
                    errors.append(
                        f"recovery backup preserved at {backup_path}"
                    )
            elif record.backup_name is not None:
                # A reservation that never received the original is disposable.
                try:
                    self._unlink_entry(
                        record.final_anchor,
                        record.backup_name,
                        missing_ok=True,
                    )
                except OSError as exc:
                    errors.append(
                        f"could not remove empty backup reservation "
                        f"{record.final_anchor.path / record.backup_name}: {exc}"
                    )
                else:
                    record.backup_name = None

            if record.temp_name is not None:
                try:
                    self._unlink_entry(
                        record.final_anchor,
                        record.temp_name,
                        missing_ok=True,
                    )
                except OSError as exc:
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
        if not self.owns_lock:
            return True

        lock_path.parent.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        handle = lock_path.open("a+", encoding="utf-8")
        set_non_inheritable(handle)

        try:
            while time.monotonic() - start < timeout:
                try:
                    if not try_acquire_exclusive(handle):
                        raise BlockingIOError
                except BlockingIOError:
                    time.sleep(0.1)
                    continue
                # flock succeeded — hand ownership of the handle to the
                # instance so _release_lock can close it.
                self._lock_handle = handle
                return True
        except BaseException:
            # m-12: any non-BlockingIOError raised between open() and a
            # successful flock (signals, OSError from sleep, etc.) must
            # not leak the file handle. Close and re-raise.
            handle.close()
            raise

        # Timed out waiting for the lock — close the handle and report.
        handle.close()
        return False

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
        if self._lock_handle is None:
            return
        try:
            release_exclusive(self._lock_handle)
        except OSError:
            pass
        finally:
            self._lock_handle.close()
            self._lock_handle = None
