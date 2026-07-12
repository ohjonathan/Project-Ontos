"""Workspace-level advisory locking for MCP and CLI write paths."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import time
from typing import IO, Iterator, Optional

from ontos.core.errors import OntosUserError
from ontos.core.locking import (
    WorkspaceBinding,
    WorkspaceLockGuard,
    capture_workspace_binding,
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


@contextmanager
def workspace_lock(
    workspace_root: Path,
    timeout: float = 5.0,
    *,
    expected_workspace_binding: Optional[WorkspaceBinding] = None,
) -> Iterator[WorkspaceLockGuard]:
    """Acquire an exclusive flock on ``<workspace>/.ontos.lock``."""
    binding = expected_workspace_binding or capture_workspace_binding(
        workspace_root
    )
    verify_workspace_binding(workspace_root, binding)
    lock_path = workspace_root / ".ontos.lock"

    root_guard_fd = open_workspace_guard(workspace_root, binding)
    root_acquired = False
    handle: Optional[IO[str]] = None
    acquired = False
    primary_error: Optional[BaseException] = None
    start = time.monotonic()
    try:
        while True:
            verify_workspace_binding(workspace_root, binding)
            verify_workspace_guard(root_guard_fd, binding)
            if try_acquire_workspace_guard(root_guard_fd):
                root_acquired = True
                break
            if time.monotonic() - start >= timeout:
                raise OntosUserError(
                    "Workspace is locked by another process.",
                    code="E_WORKSPACE_BUSY",
                )
            time.sleep(0.1)

        verify_workspace_binding(workspace_root, binding)
        handle = open_lock_file(lock_path)
        set_non_inheritable(handle)
        verify_workspace_binding(workspace_root, binding)
        verify_lock_file_binding(handle, lock_path)
        while True:
            try:
                verify_workspace_binding(workspace_root, binding)
                verify_lock_file_binding(handle, lock_path)
                if not try_acquire_exclusive(handle):
                    raise BlockingIOError
                acquired = True
                verify_lock_file_binding(handle, lock_path)
                verify_workspace_binding(workspace_root, binding)
                break
            except BlockingIOError:
                if time.monotonic() - start >= timeout:
                    raise OntosUserError(
                        "Workspace is locked by another process.",
                        code="E_WORKSPACE_BUSY",
                    )
                time.sleep(0.1)
        guard = WorkspaceLockGuard(
            workspace_root=workspace_root,
            workspace_binding=binding,
            lock_path=lock_path,
            lock_handle=handle,
            root_guard_fd=root_guard_fd,
        )
        guard.verify()
        yield guard
        guard.verify()
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        try:
            close_lock_resources(
                handle,
                lock_acquired=acquired,
                guard_fd=root_guard_fd,
                guard_acquired=root_acquired,
            )
        except BaseException:
            if primary_error is None:
                raise
