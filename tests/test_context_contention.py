"""Write-contention tests for SessionContext + workspace_lock.

Covers v4.1 Track B Dev 1 scope:

* A1 regression — ``SessionContext(owns_lock=False)`` works inside a
  ``workspace_lock()`` and the same call would deadlock/timeout with the
  default ``owns_lock=True``. See
  ``.project-internal/reviews/ontos-v4.1-spec-addendum-v1.2.md`` A1.
* Two concurrent writers on the same workspace — the second times out
  with ``RuntimeError("Could not acquire write lock...")``.
* A writer holding the workspace lock does not stall a reader that does
  not flock (portfolio-read path per C.0 findings Q2).
* SF-8 — a pre-v4.1 PID-style ``.ontos.lock`` file (arbitrary text
  content, no flock held) is acquired by the new flock-based path.
* m-12 — a handle leak between ``open()`` and a successful flock in
  ``_acquire_lock`` is prevented when an unexpected exception is raised.
"""

from __future__ import annotations

import fcntl
import time
from multiprocessing import Event, Process, Queue
from pathlib import Path
from typing import Optional

import pytest

from ontos.core.context import SessionContext
from ontos.mcp.locking import workspace_lock


# ---------------------------------------------------------------------------
# multiprocessing helpers (top-level so they are picklable on macOS spawn).
# ---------------------------------------------------------------------------


def _writer_child(workspace: str, ready, release, result: Queue) -> None:
    """Hold an exclusive flock on ``<workspace>/.ontos.lock`` until released.

    Signals ``ready`` once the lock is held; waits for ``release`` before
    dropping it. Reports success/failure through ``result``.
    """
    try:
        ctx = SessionContext(repo_root=Path(workspace), config={})
        lock_path = Path(workspace) / ".ontos.lock"
        acquired = ctx._acquire_lock(lock_path, timeout=5.0)
        if not acquired:
            result.put(("fail", "first writer could not acquire"))
            return
        ready.set()
        release.wait(timeout=10.0)
        ctx._release_lock(lock_path)
        result.put(("ok", None))
    except BaseException as exc:  # pragma: no cover — surfaced via Queue
        result.put(("error", repr(exc)))


def _second_writer_child(workspace: str, result: Queue) -> None:
    """Attempt a committed write; should raise RuntimeError under contention."""
    try:
        ctx = SessionContext(repo_root=Path(workspace), config={})
        ctx.buffer_write(Path(workspace) / "doc.md", "hello")
        ctx.commit()
        result.put(("ok", None))
    except RuntimeError as exc:
        result.put(("runtime", str(exc)))
    except BaseException as exc:  # pragma: no cover
        result.put(("error", repr(exc)))


def _outer_lock_child(workspace: str, ready, release, result: Queue) -> None:
    """Hold ``workspace_lock()`` on ``workspace`` until released.

    Used to simulate an outer flock held by a different process while the
    parent process runs a reader-that-does-not-flock.
    """
    try:
        with workspace_lock(Path(workspace), timeout=5.0):
            ready.set()
            release.wait(timeout=10.0)
        result.put(("ok", None))
    except BaseException as exc:  # pragma: no cover
        result.put(("error", repr(exc)))


# ---------------------------------------------------------------------------
# Tests.
# ---------------------------------------------------------------------------


class TestA1OwnsLockRegression:
    """A1 — `SessionContext(owns_lock=False)` inside `workspace_lock`.

    The default `owns_lock=True` path would deadlock against an outer
    flock held by `workspace_lock()` (same process, different fd, same
    file — `flock(2)` treats them independently); `owns_lock=False` is
    the contract introduced by addendum v1.2 A1.
    """

    def test_owns_lock_false_allows_commit_under_workspace_lock(self, tmp_path):
        target = tmp_path / "note.md"
        with workspace_lock(tmp_path, timeout=5.0):
            ctx = SessionContext(
                repo_root=tmp_path, config={}, owns_lock=False
            )
            ctx.buffer_write(target, "hello A1")
            modified = ctx.commit()
        assert modified == [target]
        assert target.read_text() == "hello A1"

    def test_default_owns_lock_true_deadlocks_under_workspace_lock(self, tmp_path):
        """Same setup with the default owns_lock=True must fail fast.

        The inner acquire uses a small timeout so the test does not pay
        the full 5s; the point is that the lock WOULD be acquired if
        `owns_lock=False` were the default, and is NOT acquired when the
        outer workspace_lock is held.
        """
        ctx = SessionContext(repo_root=tmp_path, config={})  # owns_lock=True

        with workspace_lock(tmp_path, timeout=5.0):
            lock_path = tmp_path / ".ontos.lock"
            # Directly exercise _acquire_lock with a short timeout to
            # keep the test fast — the production path (commit()) uses
            # the full 5s window and raises RuntimeError on False.
            acquired = ctx._acquire_lock(lock_path, timeout=0.2)
            assert acquired is False, (
                "default owns_lock=True must fail to acquire while the "
                "outer workspace_lock is held — this is the A1 deadlock "
                "the owns_lock=False contract prevents"
            )
            assert ctx._lock_handle is None

    def test_owns_lock_false_acquire_release_are_noops(self, tmp_path):
        ctx = SessionContext(
            repo_root=tmp_path, config={}, owns_lock=False
        )
        lock_path = tmp_path / ".ontos.lock"
        # No outer flock held — the contract is still "do nothing".
        assert ctx._acquire_lock(lock_path, timeout=0.1) is True
        assert ctx._lock_handle is None
        ctx._release_lock(lock_path)  # Must not raise.
        assert ctx._lock_handle is None


class TestTwoWriterContention:
    """Two writers on the same workspace — second must time out."""

    def test_second_writer_times_out_with_runtime_error(self, tmp_path):
        ready = Event()
        release = Event()
        first_q: Queue = Queue()
        second_q: Queue = Queue()

        first = Process(
            target=_writer_child,
            args=(str(tmp_path), ready, release, first_q),
        )
        first.start()
        try:
            assert ready.wait(timeout=5.0), "first writer never signalled ready"

            second = Process(
                target=_second_writer_child,
                args=(str(tmp_path), second_q),
            )
            start = time.monotonic()
            second.start()
            second.join(timeout=20.0)
            elapsed = time.monotonic() - start

            assert not second.is_alive(), "second writer did not exit"
            assert second.exitcode == 0, (
                f"second writer crashed: exitcode={second.exitcode}"
            )

            status, payload = second_q.get(timeout=2.0)
            assert status == "runtime", (
                f"second writer should have raised RuntimeError; "
                f"got {status!r} with payload {payload!r}"
            )
            assert "Could not acquire write lock" in payload
            # The retry loop in _acquire_lock is 5s; the second writer
            # should fail somewhere around that mark.
            assert 4.5 <= elapsed <= 15.0, (
                f"second writer elapsed={elapsed:.2f}s — expected ~5s retry window"
            )
        finally:
            release.set()
            first.join(timeout=5.0)
            if first.is_alive():  # pragma: no cover
                first.terminate()
                first.join(timeout=2.0)


class TestWriterVsNonFlockingReader:
    """A reader that does not flock must not block behind a writer.

    Per C.0 findings Q2 (sub-questions table), portfolio-level read
    tools (``project_registry``, ``search_portfolio``, ``verify
    --portfolio``) operate on ``portfolio.db`` and do NOT acquire the
    workspace flock. This test asserts that invariant at the substrate
    layer: an outer ``workspace_lock()`` in one process does not impede
    a bare filesystem read in another process (no flock acquisition).
    """

    def test_non_flocking_reader_unblocked_by_writer(self, tmp_path):
        # Place a file the "reader" will read.
        sentinel = tmp_path / "doc.md"
        sentinel.write_text("data")

        ready = Event()
        release = Event()
        holder_q: Queue = Queue()
        holder = Process(
            target=_outer_lock_child,
            args=(str(tmp_path), ready, release, holder_q),
        )
        holder.start()
        try:
            assert ready.wait(timeout=5.0), "holder never signalled ready"

            # The reader-like path: just read the file. No flock.
            start = time.monotonic()
            content = sentinel.read_text()
            # Also stat the lockfile path, simulating a tool that may
            # inspect the lockfile's metadata without acquiring it.
            lockfile = tmp_path / ".ontos.lock"
            assert lockfile.exists()
            _ = lockfile.stat()
            elapsed = time.monotonic() - start

            assert content == "data"
            assert elapsed < 1.0, (
                f"non-flocking reader blocked for {elapsed:.2f}s while "
                f"writer held workspace_lock — must not stall"
            )
        finally:
            release.set()
            holder.join(timeout=5.0)
            if holder.is_alive():  # pragma: no cover
                holder.terminate()
                holder.join(timeout=2.0)


class TestSF8StaleLegacyLockfile:
    """SF-8 — a pre-v4.1 PID-style ``.ontos.lock`` must not break acquire.

    Earlier Ontos versions wrote PID/text content into ``.ontos.lock``.
    The v4.1 flock-based path opens the file in ``"a+"`` and flocks the
    fd; it does not read or parse the file's content. This test proves
    it.
    """

    def test_stale_pid_style_lockfile_is_acquired(self, tmp_path):
        lock_path = tmp_path / ".ontos.lock"
        lock_path.write_text("12345\nworkspace=/some/old/path\n")

        ctx = SessionContext(repo_root=tmp_path, config={})
        acquired = ctx._acquire_lock(lock_path, timeout=1.0)
        try:
            assert acquired is True
            assert ctx._lock_handle is not None
            # The file's prior contents remain — open in append mode
            # does not truncate. This is intentional and harmless; flock
            # is purely fd-based.
            assert lock_path.read_text().startswith("12345")
        finally:
            ctx._release_lock(lock_path)

    def test_no_codepath_parses_lockfile_content(self):
        """Assert the regression surface never existed.

        The acquire path must not ``read()`` the lockfile expecting a
        PID-style format. Narrow source inspection of the two lock
        primitives guards against anyone reintroducing PID parsing.
        """
        import inspect as _inspect

        import ontos.core.context as context_module
        import ontos.mcp.locking as locking_module

        acquire_src = _inspect.getsource(SessionContext._acquire_lock)
        release_src = _inspect.getsource(SessionContext._release_lock)
        locking_src = _inspect.getsource(locking_module.workspace_lock)

        for src, name in (
            (acquire_src, "SessionContext._acquire_lock"),
            (release_src, "SessionContext._release_lock"),
            (locking_src, "workspace_lock"),
        ):
            assert ".readline" not in src, (
                f"{name} must not readline() the lockfile"
            )
            assert ".readlines" not in src, (
                f"{name} must not readlines() the lockfile"
            )
            assert "read_text" not in src, (
                f"{name} must not read_text() the lockfile"
            )
            # Bare `handle.read(` on the lock handle would also be a
            # regression. `fileno().read` is not a real API but guard
            # broadly against `<anything>.read(` that isn't part of
            # ``read_text`` (handled above).
            assert ".read(" not in src, (
                f"{name} must not read() the lockfile's contents"
            )

        # Reference ``context_module`` to keep the import alive for
        # future assertions — this also ensures the module still exposes
        # SessionContext at the expected path.
        assert context_module.SessionContext is SessionContext


class TestM12HandleLeakFix:
    """m-12 — close the handle on any non-BlockingIOError between open/flock."""

    def test_unexpected_exception_does_not_leak_handle(self, tmp_path, monkeypatch):
        """Force an OSError out of ``fcntl.flock`` and confirm cleanup.

        Pre-m-12 the loop would drop the opened handle on the floor. Now
        the handle must be closed and the exception re-raised.
        """
        ctx = SessionContext(repo_root=tmp_path, config={})
        lock_path = tmp_path / ".ontos.lock"

        opened_handles: list = []
        real_open = Path.open

        def tracking_open(self: Path, *args, **kwargs):
            handle = real_open(self, *args, **kwargs)
            if self == lock_path:
                opened_handles.append(handle)
            return handle

        def exploding_flock(fd, op):  # noqa: ANN001
            raise OSError("induced flock failure")

        monkeypatch.setattr(Path, "open", tracking_open)
        monkeypatch.setattr(fcntl, "flock", exploding_flock)

        with pytest.raises(OSError, match="induced flock failure"):
            ctx._acquire_lock(lock_path, timeout=1.0)

        assert len(opened_handles) == 1, "lock path was not opened exactly once"
        handle = opened_handles[0]
        assert handle.closed, (
            "m-12 regression: unexpected exception between open() and "
            "successful flock leaked the file handle"
        )
        assert ctx._lock_handle is None
