"""Cross-platform advisory file locking primitives.

The package supports Windows for its base CLI, so importing Ontos must not
unconditionally import the POSIX-only :mod:`fcntl` module.  Both the CLI write
context and MCP write tools use this module to keep one lock contract.
"""

from __future__ import annotations

from dataclasses import dataclass
import errno
import os
from pathlib import Path
import stat
from typing import IO, Optional, Tuple

try:  # pragma: no branch - exactly one backend is available per platform.
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - exercised on Windows CI.
    _fcntl = None

try:  # pragma: no branch - imported only on Windows.
    import msvcrt as _msvcrt
except ImportError:  # pragma: no cover - normal on POSIX.
    _msvcrt = None


WorkspaceBinding = Tuple[int, int, int]


def capture_workspace_binding(workspace_root: Path) -> WorkspaceBinding:
    """Capture the no-follow identity of a real workspace directory.

    Callers that perform validation before acquiring ``.ontos.lock`` carry
    this value through the lock boundary so replacing the directory entry
    cannot redirect a later writer into a different workspace.
    """
    root = Path(os.path.abspath(Path(workspace_root).expanduser()))
    info = os.lstat(root)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    file_attributes = getattr(info, "st_file_attributes", 0)
    if stat.S_ISLNK(info.st_mode) or (
        reparse_flag and file_attributes & reparse_flag
    ):
        raise ValueError(
            f"workspace root must not be a symlink or reparse point: {root}"
        )
    if not stat.S_ISDIR(info.st_mode):
        raise ValueError(f"workspace root must be a directory: {root}")
    return (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))


def verify_workspace_binding(
    workspace_root: Path,
    expected: WorkspaceBinding,
) -> None:
    """Fail closed when a workspace path no longer names ``expected``."""
    current = capture_workspace_binding(workspace_root)
    if current != expected:
        raise RuntimeError(
            f"workspace root changed during operation: {workspace_root}"
        )


def open_workspace_guard(
    workspace_root: Path,
    expected: WorkspaceBinding,
) -> Optional[int]:
    """Open the workspace directory used as the POSIX coordination guard.

    A lockfile can be unlinked while an advisory lock is held on POSIX.  A
    second writer could otherwise create a new inode and acquire an unrelated
    lock.  Locking the stable directory inode as well keeps all writers in the
    same coordination domain even if the visible lockfile name is attacked.
    Windows denies deletion of the opened lockfile through its sharing flags,
    so the extra directory flock is not needed there.
    """
    if _fcntl is None:
        return None
    root = Path(os.path.abspath(Path(workspace_root).expanduser()))
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    fd = os.open(root, flags)
    try:
        info = os.fstat(fd)
        actual = (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))
        if actual != expected:
            raise RuntimeError(
                f"workspace root changed before guard acquisition: {root}"
            )
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError(f"workspace guard must be a directory: {root}")
        os.set_inheritable(fd, False)
        return fd
    except BaseException:
        os.close(fd)
        raise


def verify_workspace_guard(
    guard_fd: Optional[int],
    expected: WorkspaceBinding,
) -> None:
    """Require an opened directory guard to retain the expected identity."""
    if guard_fd is None:
        return
    info = os.fstat(guard_fd)
    actual = (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))
    if actual != expected or not stat.S_ISDIR(info.st_mode):
        raise RuntimeError("workspace directory guard changed while held")


def try_acquire_workspace_guard(guard_fd: Optional[int]) -> bool:
    """Try to lock the stable workspace directory inode without blocking."""
    if guard_fd is None:
        return True
    assert _fcntl is not None
    try:
        _fcntl.flock(guard_fd, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
    except BlockingIOError:
        return False
    return True


def release_workspace_guard(guard_fd: Optional[int]) -> None:
    """Release a workspace directory guard acquired by this module."""
    if guard_fd is None:
        return
    assert _fcntl is not None
    _fcntl.flock(guard_fd, _fcntl.LOCK_UN)


def open_lock_file(lock_path: Path) -> IO[str]:
    """Open a persistent workspace lock without following the final entry.

    The lock file intentionally survives release and may contain legacy text.
    Opening it must therefore preserve existing bytes while rejecting symbolic
    links and Windows reparse points before the locking backend can write its
    one-byte sentinel.
    """
    # Resolve trusted ancestors so normal platform aliases such as macOS
    # ``/var -> /private/var`` remain usable, but keep the workspace-root entry
    # itself lexical so the no-follow open below can reject a symlinked root.
    path = Path(os.path.abspath(Path(lock_path).expanduser()))
    workspace_root = path.parent
    if workspace_root == Path(workspace_root.anchor):
        anchored_path = workspace_root / path.name
    else:
        anchored_path = (
            workspace_root.parent.resolve(strict=True)
            / workspace_root.name
            / path.name
        )

    if os.name == "posix":
        return _open_posix_lock_file(anchored_path)
    if os.name == "nt":  # pragma: no cover - exercised by Windows CI.
        return _open_windows_lock_file(anchored_path)
    raise RuntimeError("No no-follow lock-file opener is available")


def verify_lock_file_binding(handle: IO[str], lock_path: Path) -> None:
    """Require the visible lock name to match the open single-link handle."""
    opened = os.fstat(handle.fileno())
    if not stat.S_ISREG(opened.st_mode):
        raise ValueError(f"Workspace lock must remain a regular file: {lock_path}")
    if opened.st_nlink != 1:
        raise ValueError(
            "Workspace lock must have exactly one link while held: "
            f"{lock_path} (links={opened.st_nlink})"
        )
    try:
        visible = os.lstat(lock_path)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Workspace lock path disappeared while held: {lock_path}"
        ) from exc
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    file_attributes = getattr(visible, "st_file_attributes", 0)
    if stat.S_ISLNK(visible.st_mode) or (
        reparse_flag and file_attributes & reparse_flag
    ):
        raise ValueError(
            f"Workspace lock must not become a symlink or reparse point: {lock_path}"
        )
    if not stat.S_ISREG(visible.st_mode):
        raise ValueError(f"Workspace lock must remain a regular file: {lock_path}")
    if visible.st_nlink != 1:
        raise ValueError(
            "Workspace lock must have exactly one visible link: "
            f"{lock_path} (links={visible.st_nlink})"
        )
    if (visible.st_dev, visible.st_ino) != (opened.st_dev, opened.st_ino):
        raise RuntimeError(
            f"Workspace lock path changed while held: {lock_path}"
        )


@dataclass(frozen=True)
class WorkspaceLockGuard:
    """Runtime-bound proof of one held workspace and lock identity."""

    workspace_root: Path
    workspace_binding: WorkspaceBinding
    lock_path: Path
    lock_handle: IO[str]
    root_guard_fd: Optional[int]

    def verify(self) -> None:
        """Require both visible paths and both held handles to stay bound."""
        verify_workspace_guard(self.root_guard_fd, self.workspace_binding)
        verify_workspace_binding(self.workspace_root, self.workspace_binding)
        verify_lock_file_binding(self.lock_handle, self.lock_path)


def _open_posix_lock_file(lock_path: Path) -> IO[str]:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:  # pragma: no cover - defensive.
        raise RuntimeError("This POSIX runtime lacks no-follow directory opens")

    directory_flags = os.O_RDONLY | directory | nofollow
    directory_flags |= getattr(os, "O_CLOEXEC", 0)
    anchor = Path(lock_path.parent.anchor)
    directory_fd = os.open(anchor, directory_flags)
    try:
        for component in lock_path.parent.parts[1:]:
            try:
                next_fd = os.open(component, directory_flags, dir_fd=directory_fd)
            except OSError as exc:
                if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise ValueError(
                        "Workspace lock parent path must contain only real "
                        "directories, not symbolic links: "
                        f"{lock_path.parent}"
                    ) from exc
                raise
            os.close(directory_fd)
            directory_fd = next_fd
    except BaseException:
        os.close(directory_fd)
        raise
    fd = -1
    try:
        file_flags = os.O_RDWR | os.O_CREAT | os.O_APPEND | nofollow
        file_flags |= getattr(os, "O_CLOEXEC", 0)
        try:
            fd = os.open(
                lock_path.name,
                file_flags,
                0o666,
                dir_fd=directory_fd,
            )
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise ValueError(
                    f"Workspace lock must not be a symbolic link: {lock_path}"
                ) from exc
            raise

        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(
                f"Workspace lock must be a regular file: {lock_path}"
            )
        if info.st_nlink != 1:
            detail = (
                "must not have multiple hard links"
                if info.st_nlink > 1
                else "must have exactly one visible link"
            )
            raise ValueError(f"Workspace lock {detail}: {lock_path}")
        handle = os.fdopen(fd, "a+", encoding="utf-8")
        fd = -1
        return handle
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(directory_fd)


def _open_windows_lock_file(lock_path: Path) -> IO[str]:
    """Open the lock itself on Windows, then reject reparse handles."""
    if _msvcrt is None:  # pragma: no cover - defensive Windows runtime.
        raise RuntimeError("Windows lock-file support is unavailable")

    import ctypes  # pragma: no cover - Windows only.
    from ctypes import wintypes  # pragma: no cover - Windows only.

    class ByHandleFileInformation(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

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
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    get_information = kernel32.GetFileInformationByHandle
    get_information.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(ByHandleFileInformation),
    )
    get_information.restype = wintypes.BOOL

    generic_read = 0x80000000
    generic_write = 0x40000000
    file_read_attributes = 0x0080
    file_share_read = 0x00000001
    file_share_write = 0x00000002
    open_existing = 3
    open_always = 4
    file_attribute_normal = 0x00000080
    file_attribute_directory = 0x00000010
    file_attribute_reparse_point = 0x00000400
    file_flag_backup_semantics = 0x02000000
    file_flag_open_reparse_point = 0x00200000
    invalid_handle = ctypes.c_void_p(-1).value

    def open_handle(path: Path, access: int, disposition: int, flags: int) -> int:
        handle = create_file(
            str(path),
            access,
            file_share_read | file_share_write,
            None,
            disposition,
            flags,
            None,
        )
        if handle == invalid_handle:
            raise ctypes.WinError(ctypes.get_last_error())
        return int(handle)

    def information_for(handle: int) -> ByHandleFileInformation:
        information = ByHandleFileInformation()
        if not get_information(
            wintypes.HANDLE(handle),
            ctypes.byref(information),
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return information

    parent_handles: list[int] = []
    lock_handle: Optional[int] = None
    fd = -1
    try:
        current = Path(lock_path.parent.anchor)
        parent_paths = [current]
        for component in lock_path.parent.parts[1:]:
            current /= component
            parent_paths.append(current)
        for parent_path in parent_paths:
            parent_handle = open_handle(
                parent_path,
                file_read_attributes,
                open_existing,
                file_flag_backup_semantics | file_flag_open_reparse_point,
            )
            parent_handles.append(parent_handle)
            parent_information = information_for(parent_handle)
            parent_attributes = int(parent_information.dwFileAttributes)
            if parent_attributes & file_attribute_reparse_point:
                raise ValueError(
                    "Workspace lock parent path must not contain a reparse "
                    f"point: {parent_path}"
                )
            if not parent_attributes & file_attribute_directory:
                raise ValueError(
                    f"Workspace lock parent must be a directory: {parent_path}"
                )

        lock_handle = open_handle(
            lock_path,
            generic_read | generic_write,
            open_always,
            file_attribute_normal | file_flag_open_reparse_point,
        )
        lock_information = information_for(lock_handle)
        lock_attributes = int(lock_information.dwFileAttributes)
        if lock_attributes & file_attribute_reparse_point:
            raise ValueError(
                f"Workspace lock must not be a reparse point: {lock_path}"
            )
        if lock_attributes & file_attribute_directory:
            raise ValueError(
                f"Workspace lock must be a regular file: {lock_path}"
            )
        link_count = int(lock_information.nNumberOfLinks)
        if link_count != 1:
            detail = (
                "must not have multiple hard links"
                if link_count > 1
                else "must have exactly one visible link"
            )
            raise ValueError(f"Workspace lock {detail}: {lock_path}")

        fd_flags = os.O_RDWR | os.O_APPEND | getattr(os, "O_NOINHERIT", 0)
        fd = _msvcrt.open_osfhandle(lock_handle, fd_flags)
        lock_handle = None  # CRT descriptor now owns the Windows handle.
        handle = os.fdopen(fd, "a+", encoding="utf-8")
        fd = -1
        return handle
    finally:
        if fd >= 0:
            os.close(fd)
        if lock_handle is not None:
            close_handle(wintypes.HANDLE(lock_handle))
        for parent_handle in reversed(parent_handles):
            close_handle(wintypes.HANDLE(parent_handle))


def set_non_inheritable(handle: IO[str]) -> None:
    """Prevent a child process from inheriting a held workspace lock."""
    os.set_inheritable(handle.fileno(), False)


def try_acquire_exclusive(handle: IO[str]) -> bool:
    """Attempt a non-blocking exclusive lock on ``handle``.

    Returns ``False`` when another process owns the lock and raises for other
    operating-system errors.
    """
    info = os.fstat(handle.fileno())
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("Workspace lock handle must remain a regular file")
    if info.st_nlink != 1:
        detail = (
            "must not have multiple hard links"
            if info.st_nlink > 1
            else "must have exactly one visible link"
        )
        raise ValueError(f"Workspace lock handle {detail}")

    if _fcntl is not None:
        try:
            _fcntl.flock(handle.fileno(), _fcntl.LOCK_EX | _fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        return True

    if _msvcrt is None:  # pragma: no cover - defensive unsupported platform.
        raise RuntimeError("No supported file-locking backend is available")
    return _try_acquire_windows_lock(handle)


def release_exclusive(handle: IO[str]) -> None:
    """Release an advisory lock previously acquired on ``handle``."""
    if _fcntl is not None:
        _fcntl.flock(handle.fileno(), _fcntl.LOCK_UN)
        return

    if _msvcrt is None:  # pragma: no cover - defensive unsupported platform.
        raise RuntimeError("No supported file-locking backend is available")
    _release_windows_lock(handle)


def close_lock_resources(
    handle: Optional[IO[str]],
    *,
    lock_acquired: bool,
    guard_fd: Optional[int],
    guard_acquired: bool,
) -> None:
    """Release and close every lock resource even when one cleanup fails."""
    errors: list[BaseException] = []
    if handle is not None:
        if lock_acquired:
            try:
                release_exclusive(handle)
            except BaseException as exc:
                errors.append(exc)
        try:
            handle.close()
        except BaseException as exc:
            errors.append(exc)
    if guard_acquired:
        try:
            release_workspace_guard(guard_fd)
        except BaseException as exc:
            errors.append(exc)
    if guard_fd is not None:
        try:
            os.close(guard_fd)
        except BaseException as exc:
            errors.append(exc)
    if errors:
        raise errors[0]


def _windows_overlapped_type():
    """Build the Win32 OVERLAPPED layout without importing it on POSIX."""
    import ctypes  # pragma: no cover - Windows only.
    from ctypes import wintypes  # pragma: no cover - Windows only.

    class Overlapped(ctypes.Structure):
        _fields_ = [
            ("Internal", ctypes.c_void_p),
            ("InternalHigh", ctypes.c_void_p),
            ("Offset", wintypes.DWORD),
            ("OffsetHigh", wintypes.DWORD),
            ("hEvent", wintypes.HANDLE),
        ]

    return Overlapped


def _try_acquire_windows_lock(handle: IO[str]) -> bool:
    """Lock byte range zero without extending or mutating an empty file."""
    import ctypes  # pragma: no cover - Windows only.
    from ctypes import wintypes  # pragma: no cover - Windows only.

    overlapped_type = _windows_overlapped_type()
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    lock_file_ex = kernel32.LockFileEx
    lock_file_ex.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(overlapped_type),
    )
    lock_file_ex.restype = wintypes.BOOL
    os_handle = _msvcrt.get_osfhandle(handle.fileno())
    overlapped = overlapped_type()
    flags = 0x00000002 | 0x00000001  # EXCLUSIVE | FAIL_IMMEDIATELY
    if lock_file_ex(
        wintypes.HANDLE(os_handle),
        flags,
        0,
        1,
        0,
        ctypes.byref(overlapped),
    ):
        return True
    error = ctypes.get_last_error()
    if error == 33:  # ERROR_LOCK_VIOLATION
        return False
    raise ctypes.WinError(error)


def _release_windows_lock(handle: IO[str]) -> None:
    """Release the non-mutating Win32 byte-range lock."""
    import ctypes  # pragma: no cover - Windows only.
    from ctypes import wintypes  # pragma: no cover - Windows only.

    overlapped_type = _windows_overlapped_type()
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    unlock_file_ex = kernel32.UnlockFileEx
    unlock_file_ex.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(overlapped_type),
    )
    unlock_file_ex.restype = wintypes.BOOL
    os_handle = _msvcrt.get_osfhandle(handle.fileno())
    overlapped = overlapped_type()
    if not unlock_file_ex(
        wintypes.HANDLE(os_handle),
        0,
        1,
        0,
        ctypes.byref(overlapped),
    ):
        raise ctypes.WinError(ctypes.get_last_error())


def backend_name() -> str:
    """Return the active backend name for diagnostics and smoke tests."""
    if _fcntl is not None:
        return "fcntl"
    if _msvcrt is not None:  # pragma: no cover - exercised on Windows CI.
        return "msvcrt"
    return "unavailable"  # pragma: no cover
