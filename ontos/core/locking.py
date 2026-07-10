"""Cross-platform advisory file locking primitives.

The package supports Windows for its base CLI, so importing Ontos must not
unconditionally import the POSIX-only :mod:`fcntl` module.  Both the CLI write
context and MCP write tools use this module to keep one lock contract.
"""

from __future__ import annotations

import os
from typing import IO

try:  # pragma: no branch - exactly one backend is available per platform.
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - exercised on Windows CI.
    _fcntl = None

try:  # pragma: no branch - imported only on Windows.
    import msvcrt as _msvcrt
except ImportError:  # pragma: no cover - normal on POSIX.
    _msvcrt = None


def set_non_inheritable(handle: IO[str]) -> None:
    """Prevent a child process from inheriting a held workspace lock."""
    os.set_inheritable(handle.fileno(), False)


def try_acquire_exclusive(handle: IO[str]) -> bool:
    """Attempt a non-blocking exclusive lock on ``handle``.

    Returns ``False`` when another process owns the lock and raises for other
    operating-system errors.
    """
    if _fcntl is not None:
        try:
            _fcntl.flock(handle.fileno(), _fcntl.LOCK_EX | _fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        return True

    if _msvcrt is None:  # pragma: no cover - defensive unsupported platform.
        raise RuntimeError("No supported file-locking backend is available")

    # msvcrt locks a byte range from the current file position.  Ensure the
    # lockfile has at least one byte without parsing or replacing legacy text.
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write("\0")
        handle.flush()
    handle.seek(0)
    try:  # pragma: no cover - exercised on Windows CI.
        _msvcrt.locking(handle.fileno(), _msvcrt.LK_NBLCK, 1)
    except OSError as exc:
        # Windows reports lock contention as EACCES/EDEADLK (and sometimes
        # EAGAIN depending on the runtime).  Other failures remain actionable.
        if getattr(exc, "errno", None) in {11, 13, 36}:
            return False
        raise
    return True


def release_exclusive(handle: IO[str]) -> None:
    """Release an advisory lock previously acquired on ``handle``."""
    if _fcntl is not None:
        _fcntl.flock(handle.fileno(), _fcntl.LOCK_UN)
        return

    if _msvcrt is None:  # pragma: no cover - defensive unsupported platform.
        raise RuntimeError("No supported file-locking backend is available")
    handle.seek(0)
    _msvcrt.locking(handle.fileno(), _msvcrt.LK_UNLCK, 1)  # pragma: no cover


def backend_name() -> str:
    """Return the active backend name for diagnostics and smoke tests."""
    if _fcntl is not None:
        return "fcntl"
    if _msvcrt is not None:  # pragma: no cover - exercised on Windows CI.
        return "msvcrt"
    return "unavailable"  # pragma: no cover
