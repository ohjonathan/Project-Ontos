"""Workspace-level advisory locking for MCP and CLI write paths."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
from pathlib import Path
import time
from typing import Iterator

from ontos.core.errors import OntosUserError


@contextmanager
def workspace_lock(workspace_root: Path, timeout: float = 5.0) -> Iterator[None]:
    """Acquire an exclusive flock on ``<workspace>/.ontos.lock``."""
    lock_path = workspace_root / ".ontos.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    handle = lock_path.open("a+", encoding="utf-8")
    start = time.monotonic()
    try:
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
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
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        handle.close()
