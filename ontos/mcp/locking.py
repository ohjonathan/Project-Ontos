"""Workspace-level advisory locking for MCP and CLI write paths."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import time
from typing import Iterator

from ontos.core.errors import OntosUserError
from ontos.core.locking import (
    release_exclusive,
    set_non_inheritable,
    try_acquire_exclusive,
)


@contextmanager
def workspace_lock(workspace_root: Path, timeout: float = 5.0) -> Iterator[None]:
    """Acquire an exclusive flock on ``<workspace>/.ontos.lock``."""
    lock_path = workspace_root / ".ontos.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    handle = lock_path.open("a+", encoding="utf-8")
    set_non_inheritable(handle)
    start = time.monotonic()
    try:
        while True:
            try:
                if not try_acquire_exclusive(handle):
                    raise BlockingIOError
                break
            except BlockingIOError:
                if time.monotonic() - start >= timeout:
                    raise OntosUserError(
                        "Workspace is locked by another process.",
                        code="E_WORKSPACE_BUSY",
                    )
                time.sleep(0.1)
        yield
    finally:
        try:
            release_exclusive(handle)
        except OSError:
            pass
        handle.close()
