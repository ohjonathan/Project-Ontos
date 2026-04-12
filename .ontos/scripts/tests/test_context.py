"""Tests for SessionContext transaction system.

This test suite validates the core SessionContext functionality:
- Buffer operations (write/delete/move)
- Staged commit behavior for buffered writes
- Rollback behavior
- Lock acquisition and timeout
- Factory initialization
- Diagnostic collection

Per v2.9.5 spec, tests focus on behavior, not internal mechanics.
"""

import fcntl
import types
from multiprocessing import Event, Process
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from ontos.core.context import SessionContext, FileOperation, PendingWrite


def _hold_flock(lock_path: str, ready, release) -> None:
    """Hold an exclusive flock lock until the caller signals release."""
    path = Path(lock_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        ready.set()
        release.wait(timeout=5.0)
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _try_flock_once(lock_path: str, acquired) -> None:
    """Try to acquire the lock once and immediately release it."""
    path = Path(lock_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        acquired.set()
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class TestBufferOperations:
    """Tests for buffer_write, buffer_delete, buffer_move methods."""

    def test_buffer_write_adds_to_pending(self, tmp_path):
        """buffer_write adds a WRITE operation to pending_writes."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(tmp_path / "test.txt", "content")
        
        assert len(ctx.pending_writes) == 1
        assert ctx.pending_writes[0].operation == FileOperation.WRITE
        assert ctx.pending_writes[0].content == "content"

    def test_buffer_delete_adds_to_pending(self, tmp_path):
        """buffer_delete adds a DELETE operation to pending_writes."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_delete(tmp_path / "test.txt")
        
        assert len(ctx.pending_writes) == 1
        assert ctx.pending_writes[0].operation == FileOperation.DELETE

    def test_buffer_move_adds_to_pending(self, tmp_path):
        """buffer_move adds a MOVE operation to pending_writes."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_move(tmp_path / "src.txt", tmp_path / "dst.txt")
        
        assert len(ctx.pending_writes) == 1
        assert ctx.pending_writes[0].operation == FileOperation.MOVE
        assert ctx.pending_writes[0].destination == tmp_path / "dst.txt"

    def test_multiple_operations_in_order(self, tmp_path):
        """Multiple buffered operations maintain order."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(tmp_path / "a.txt", "a")
        ctx.buffer_delete(tmp_path / "b.txt")
        ctx.buffer_write(tmp_path / "c.txt", "c")
        
        assert len(ctx.pending_writes) == 3
        assert ctx.pending_writes[0].operation == FileOperation.WRITE
        assert ctx.pending_writes[1].operation == FileOperation.DELETE
        assert ctx.pending_writes[2].operation == FileOperation.WRITE


class TestCommit:
    """Tests for commit() method - file creation and staged updates."""

    def test_commit_empty_buffer_returns_empty(self, tmp_path):
        """Commit with no pending writes returns empty list."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        result = ctx.commit()
        assert result == []

    def test_commit_creates_file(self, tmp_path):
        """Commit creates file with correct content."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        target = tmp_path / "test.txt"
        ctx.buffer_write(target, "hello world")
        
        result = ctx.commit()
        
        assert target.exists()
        assert target.read_text() == "hello world"
        assert target in result

    def test_commit_creates_nested_directories(self, tmp_path):
        """Commit creates parent directories if needed."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        target = tmp_path / "a" / "b" / "c" / "test.txt"
        ctx.buffer_write(target, "nested")
        
        ctx.commit()
        
        assert target.exists()
        assert target.read_text() == "nested"

    def test_commit_clears_buffer(self, tmp_path):
        """Commit clears pending_writes after success."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(tmp_path / "test.txt", "content")
        
        ctx.commit()
        
        assert len(ctx.pending_writes) == 0

    def test_commit_delete_removes_file(self, tmp_path):
        """Commit with DELETE operation removes file."""
        target = tmp_path / "to_delete.txt"
        target.write_text("delete me")
        
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_delete(target)
        
        ctx.commit()
        
        assert not target.exists()

    def test_commit_move_relocates_file(self, tmp_path):
        """Commit with MOVE operation moves file."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("move me")
        
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_move(source, dest)
        
        ctx.commit()
        
        assert not source.exists()
        assert dest.exists()
        assert dest.read_text() == "move me"

    def test_commit_returns_modified_paths(self, tmp_path):
        """Commit returns list of all modified paths."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        file1 = tmp_path / "a.txt"
        file2 = tmp_path / "b.txt"
        ctx.buffer_write(file1, "a")
        ctx.buffer_write(file2, "b")
        
        result = ctx.commit()
        
        assert file1 in result
        assert file2 in result


class TestCommitFailure:
    """Tests for commit() failure handling and cleanup."""

    def test_commit_cleans_temp_on_failure(self, tmp_path):
        """Commit cleans up temp files when rename fails."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        target = tmp_path / "test.txt"
        ctx.buffer_write(target, "content")
        
        # Mock rename to fail
        with patch.object(Path, 'rename', side_effect=OSError("rename failed")):
            with pytest.raises(OSError):
                ctx.commit()
        
        # The flock substrate keeps a persistent lock file, but temp outputs
        # from the failed write should still be cleaned up.
        remaining = sorted(f.name for f in tmp_path.iterdir() if f.is_file())
        assert remaining == [".ontos.lock"], (
            f"Unexpected residual files after cleanup: {remaining}"
        )
        assert not target.exists()
        assert not target.with_suffix(target.suffix + ".tmp").exists()

    def test_commit_failure_records_error(self, tmp_path):
        """Commit failure records error in context."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        target = tmp_path / "test.txt"
        ctx.buffer_write(target, "content")
        
        with patch.object(Path, 'rename', side_effect=OSError("rename failed")):
            with pytest.raises(OSError):
                ctx.commit()
        
        assert len(ctx.errors) == 1
        assert "Commit failed" in ctx.errors[0]


class TestRollback:
    """Tests for rollback() method."""

    def test_rollback_clears_buffer(self, tmp_path):
        """Rollback discards all pending operations."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(tmp_path / "a.txt", "a")
        ctx.buffer_delete(tmp_path / "b.txt")
        
        ctx.rollback()
        
        assert len(ctx.pending_writes) == 0

    def test_rollback_does_not_create_files(self, tmp_path):
        """Rollback does not create any files."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        target = tmp_path / "should_not_exist.txt"
        ctx.buffer_write(target, "content")
        
        ctx.rollback()
        
        assert not target.exists()


class TestLocking:
    """Tests for commit() locking behavior."""

    def test_commit_raises_on_lock_timeout(self, tmp_path):
        """Commit raises RuntimeError when lock cannot be acquired."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(tmp_path / "test.txt", "content")

        lock_file = tmp_path / ".ontos.lock"
        ready = Event()
        release = Event()
        proc = Process(target=_hold_flock, args=(str(lock_file), ready, release))
        proc.start()

        try:
            assert ready.wait(timeout=5.0), "Timed out waiting for lock holder"
            original_acquire = ctx._acquire_lock

            def short_timeout(lock_path, timeout=5.0):
                return original_acquire(lock_path, timeout=0.2)

            with patch.object(ctx, "_acquire_lock", side_effect=short_timeout):
                with pytest.raises(RuntimeError, match="Could not acquire write lock"):
                    ctx.commit()
        finally:
            release.set()
            proc.join(timeout=5.0)
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=1.0)

    def test_commit_acquires_and_releases_lock(self, tmp_path):
        """Commit properly acquires and releases lock."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(tmp_path / "test.txt", "content")

        ctx.commit()

        lock_file = tmp_path / ".ontos.lock"
        assert lock_file.exists()

        acquired = Event()
        proc = Process(target=_try_flock_once, args=(str(lock_file), acquired))
        proc.start()
        proc.join(timeout=5.0)
        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=1.0)

        assert acquired.is_set(), "Lock remained held after commit"


class TestFromRepo:
    """Tests for from_repo() factory method."""

    def test_from_repo_creates_context_with_config(self, tmp_path):
        """from_repo creates context with loaded config dict."""
        # Mock ontos_config module using SimpleNamespace (not MagicMock)
        mock_config = types.SimpleNamespace(
            DOCS_DIR='custom_docs',
            ONTOS_MODE='prompted'
        )
        
        with patch.dict('sys.modules', {'ontos_config': mock_config}):
            ctx = SessionContext.from_repo(tmp_path)
        
        assert ctx.repo_root == tmp_path
        assert ctx.config.get('DOCS_DIR') == 'custom_docs'
        assert ctx.config.get('ONTOS_MODE') == 'prompted'


class TestDiagnostics:
    """Tests for warn() and error() diagnostic methods."""

    def test_warn_collects_messages(self, tmp_path):
        """warn() adds messages to warnings list."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.warn("warning 1")
        ctx.warn("warning 2")
        
        assert ctx.warnings == ["warning 1", "warning 2"]

    def test_error_collects_messages(self, tmp_path):
        """error() adds messages to errors list."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.error("error 1")
        ctx.error("error 2")
        
        assert ctx.errors == ["error 1", "error 2"]
