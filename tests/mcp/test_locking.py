from __future__ import annotations

from multiprocessing import Event, Process
import os
from pathlib import Path
import subprocess
import sys

import pytest

from ontos.core.errors import OntosUserError
from ontos.mcp.locking import workspace_lock


def _hold_workspace_lock(workspace_root: str, ready: Event, release: Event) -> None:
    with workspace_lock(Path(workspace_root), timeout=1.0):
        ready.set()
        release.wait(timeout=5.0)


def test_workspace_lock_acquires_and_releases(tmp_path):
    lock_path = tmp_path / ".ontos.lock"

    with workspace_lock(tmp_path):
        assert lock_path.exists()

    with workspace_lock(tmp_path):
        assert lock_path.exists()


def test_workspace_lock_raises_when_busy(tmp_path):
    ready = Event()
    release = Event()
    proc = Process(target=_hold_workspace_lock, args=(str(tmp_path), ready, release))
    proc.start()
    try:
        assert ready.wait(timeout=2.0)
        with pytest.raises(OntosUserError) as exc:
            with workspace_lock(tmp_path, timeout=0.2):
                pass
        assert exc.value.code == "E_WORKSPACE_BUSY"
    finally:
        release.set()
        proc.join(timeout=2.0)
        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=1.0)


def test_workspace_lock_fd_is_not_inherited_by_child_process(tmp_path, monkeypatch):
    lock_path = tmp_path / ".ontos.lock"
    original_open = Path.open

    def open_with_inheritable_fd(self, *args, **kwargs):  # noqa: ANN001
        handle = original_open(self, *args, **kwargs)
        if self.resolve(strict=False) == lock_path.resolve(strict=False):
            os.set_inheritable(handle.fileno(), True)
        return handle

    monkeypatch.setattr(Path, "open", open_with_inheritable_fd)

    child: subprocess.Popen[str] | None = None
    try:
        with workspace_lock(tmp_path, timeout=1.0):
            child = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(1.0)"],
                close_fds=False,
            )
        assert child is not None
        with workspace_lock(tmp_path, timeout=0.2):
            pass
    finally:
        if child is not None:
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=2.0)
