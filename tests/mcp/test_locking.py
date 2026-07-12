from __future__ import annotations

from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from multiprocessing import Event, Process
import os
from pathlib import Path
import subprocess
import sys

import pytest

from ontos.core.errors import OntosUserError
from ontos.core.context import SessionContext
from ontos.mcp.locking import workspace_lock


def test_domain_error_preserves_frozen_contract_and_python314_traceback():
    error = OntosUserError("bad input", code="E_TEST")
    original_hash = hash(error)

    with pytest.raises(FrozenInstanceError):
        error.message = "changed"
    assert hash(error) == original_hash

    @contextmanager
    def boundary():
        yield

    with pytest.raises(OntosUserError) as raised:
        with boundary():
            raise error
    assert raised.value is error


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


@pytest.mark.skipif(os.name != "posix", reason="POSIX directory-flock guard")
def test_workspace_guard_blocks_new_lock_inode_after_visible_unlink(tmp_path):
    lock_path = tmp_path / ".ontos.lock"
    second_error = None

    with pytest.raises(ValueError, match="exactly one link"):
        with workspace_lock(tmp_path, timeout=0.2):
            original_inode = lock_path.stat().st_ino
            lock_path.unlink()
            lock_path.write_text("replacement", encoding="utf-8")
            replacement_inode = lock_path.stat().st_ino
            assert replacement_inode != original_inode

            try:
                with workspace_lock(tmp_path, timeout=0.1):
                    pytest.fail("replacement lock inode was acquired")
            except OntosUserError as exc:
                second_error = exc

    assert second_error is not None
    assert second_error.code == "E_WORKSPACE_BUSY"


@pytest.mark.skipif(os.name != "posix", reason="POSIX lock unlink regression")
def test_outer_guard_rejects_inner_commit_after_lock_path_replacement(tmp_path):
    lock_path = tmp_path / ".ontos.lock"
    target = tmp_path / "target.md"

    with pytest.raises(ValueError, match="exactly one link"):
        with workspace_lock(tmp_path) as guard:
            ctx = SessionContext(
                repo_root=tmp_path,
                config={},
                owns_lock=False,
                expected_workspace_binding=guard.workspace_binding,
                external_lock_guard=guard,
            )
            ctx.buffer_write(target, "must not be written")
            lock_path.unlink()
            lock_path.write_text("replacement", encoding="utf-8")

            with pytest.raises(ValueError, match="exactly one link"):
                ctx.commit()
            assert not target.exists()


def test_workspace_lock_preserves_body_error_and_closes_guard_on_close_failure(
    tmp_path,
    monkeypatch,
):
    import ontos.mcp.locking as locking_module

    real_open = locking_module.open_lock_file
    opened = []
    root_fd = None

    class CloseRaisingProxy:
        def __init__(self, handle):  # noqa: ANN001
            self.handle = handle

        def fileno(self):
            return self.handle.fileno()

        def close(self):
            self.handle.close()
            raise OSError("induced close failure")

    def open_proxy(path):  # noqa: ANN001
        proxy = CloseRaisingProxy(real_open(path))
        opened.append(proxy)
        return proxy

    monkeypatch.setattr(locking_module, "open_lock_file", open_proxy)

    with pytest.raises(RuntimeError, match="primary body failure"):
        with workspace_lock(tmp_path) as guard:
            root_fd = guard.root_guard_fd
            raise RuntimeError("primary body failure")

    assert opened[0].handle.closed
    if root_fd is not None:
        with pytest.raises(OSError):
            os.fstat(root_fd)
