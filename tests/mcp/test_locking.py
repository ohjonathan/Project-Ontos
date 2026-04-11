from __future__ import annotations

from multiprocessing import Event, Process
from pathlib import Path

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
