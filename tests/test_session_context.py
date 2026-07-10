"""Tests for SessionContext and backwards compatibility.

Tests the v2.8 refactoring deliverables:
- SessionContext buffer/commit/rollback operations
- File locking with flock
- Backwards compatibility (old imports reference same objects as new)
"""

import fcntl
import inspect
from multiprocessing import Event, Process
import os
from pathlib import Path
import stat
import pytest

import ontos.core.context as context_module
from ontos.core.context import SessionContext, FileOperation, PendingWrite


def _hold_lock(lock_path: str, ready: Event, release: Event) -> None:
    with Path(lock_path).open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        ready.set()
        release.wait(timeout=5.0)
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class TestSessionContext:
    """Tests for SessionContext dataclass."""
    
    def test_buffer_write(self):
        """Buffer write should add pending operation."""
        ctx = SessionContext(repo_root=Path('/tmp'), config={})
        ctx.buffer_write(Path('/tmp/test.md'), 'content')
        assert len(ctx.pending_writes) == 1
        assert ctx.pending_writes[0].operation == FileOperation.WRITE

    def test_buffer_delete(self):
        """Buffer delete should add pending operation."""
        ctx = SessionContext(repo_root=Path('/tmp'), config={})
        ctx.buffer_delete(Path('/tmp/test.md'))
        assert len(ctx.pending_writes) == 1
        assert ctx.pending_writes[0].operation == FileOperation.DELETE

    def test_buffer_move(self):
        """Buffer move should add pending operation."""
        ctx = SessionContext(repo_root=Path('/tmp'), config={})
        ctx.buffer_move(Path('/tmp/old.md'), Path('/tmp/new.md'))
        assert len(ctx.pending_writes) == 1
        assert ctx.pending_writes[0].operation == FileOperation.MOVE
        assert ctx.pending_writes[0].destination == Path('/tmp/new.md')

    def test_commit_creates_file(self, tmp_path):
        """Commit should create buffered files."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        test_file = tmp_path / 'test.md'
        ctx.buffer_write(test_file, 'content')
        modified = ctx.commit()
        assert test_file.read_text() == 'content'
        assert len(modified) == 1

    def test_commit_clears_buffer(self, tmp_path):
        """Commit should clear pending writes."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        test_file = tmp_path / 'test.md'
        ctx.buffer_write(test_file, 'content')
        ctx.commit()
        assert len(ctx.pending_writes) == 0

    def test_commit_keeps_move_and_delete_behavior(self, tmp_path):
        source = tmp_path / "source.md"
        destination = tmp_path / "nested" / "destination.md"
        deleted = tmp_path / "deleted.md"
        source.write_text("move me", encoding="utf-8")
        deleted.write_text("delete me", encoding="utf-8")

        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_move(source, destination)
        ctx.buffer_delete(deleted)

        assert ctx.commit() == [destination.resolve(), deleted.resolve()]
        assert destination.read_text(encoding="utf-8") == "move me"
        assert not source.exists()
        assert not deleted.exists()

    def test_commit_does_not_follow_predictable_temp_symlink(self, tmp_path):
        """A pre-created ``<target>.tmp`` symlink must remain untouched."""
        outside = tmp_path.parent / f"{tmp_path.name}-outside.md"
        outside.write_text("outside", encoding="utf-8")
        target = tmp_path / "doc.md"
        predictable = tmp_path / "doc.md.tmp"
        try:
            predictable.symlink_to(outside)
        except OSError as exc:  # pragma: no cover - platform capability.
            pytest.skip(f"symlinks unavailable: {exc}")

        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(target, "replacement")
        assert ctx.commit() == [target]

        assert target.read_text(encoding="utf-8") == "replacement"
        assert outside.read_text(encoding="utf-8") == "outside"
        assert predictable.is_symlink()

    def test_commit_preserves_preexisting_predictable_temp_file(self, tmp_path):
        target = tmp_path / "doc.md"
        predictable = tmp_path / "doc.md.tmp"
        predictable.write_text("sentinel", encoding="utf-8")

        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(target, "replacement")
        ctx.commit()

        assert predictable.read_text(encoding="utf-8") == "sentinel"
        assert target.read_text(encoding="utf-8") == "replacement"

    def test_commit_rejects_symlink_destination(self, tmp_path):
        outside = tmp_path.parent / f"{tmp_path.name}-outside-destination.md"
        outside.write_text("outside", encoding="utf-8")
        target = tmp_path / "doc.md"
        try:
            target.symlink_to(outside)
        except OSError as exc:  # pragma: no cover - platform capability.
            pytest.skip(f"symlinks unavailable: {exc}")

        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(target, "replacement")
        with pytest.raises(ValueError, match="must not be a symlink"):
            ctx.commit()

        assert outside.read_text(encoding="utf-8") == "outside"
        assert target.is_symlink()

    def test_commit_rejects_outside_workspace_destination(self, tmp_path):
        outside = tmp_path.parent / f"{tmp_path.name}-escape.md"
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(outside, "replacement")

        with pytest.raises(ValueError, match="outside the workspace"):
            ctx.commit()
        assert not outside.exists()

    def test_commit_rejects_duplicate_buffered_paths_before_writing(self, tmp_path):
        target = tmp_path / "doc.md"
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(target, "first")
        ctx.buffer_write(target, "second")

        with pytest.raises(ValueError, match="Multiple buffered operations"):
            ctx.commit()
        assert not target.exists()

    def test_commit_rejects_move_to_same_path(self, tmp_path):
        target = tmp_path / "doc.md"
        target.write_text("unchanged", encoding="utf-8")
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_move(target, target)

        with pytest.raises(ValueError, match="identical"):
            ctx.commit()
        assert target.read_text(encoding="utf-8") == "unchanged"

    def test_commit_rolls_back_earlier_writes_when_later_replace_fails(
        self, tmp_path, monkeypatch
    ):
        first = tmp_path / "first.md"
        second = tmp_path / "second.md"
        first.write_text("old first", encoding="utf-8")
        second.write_text("old second", encoding="utf-8")

        real_replace = os.replace
        failed = False

        def fail_second_temp_once(src, dst, **kwargs):  # noqa: ANN001
            nonlocal failed
            source = Path(src)
            destination = Path(dst)
            if (
                not failed
                and destination.name == second.name
                and source.suffix == ".tmp"
            ):
                failed = True
                raise OSError("induced second replace failure")
            return real_replace(src, dst, **kwargs)

        monkeypatch.setattr(context_module.os, "replace", fail_second_temp_once)
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(first, "new first")
        ctx.buffer_write(second, "new second")

        with pytest.raises(OSError, match="induced second replace failure"):
            ctx.commit()

        assert first.read_text(encoding="utf-8") == "old first"
        assert second.read_text(encoding="utf-8") == "old second"
        assert not list(tmp_path.glob(".*.tmp"))
        assert not list(tmp_path.glob(".*.bak"))

    @pytest.mark.skipif(os.name != "posix", reason="POSIX dir-fd race regression")
    def test_commit_parent_swap_after_validation_cannot_escape_workspace(
        self, tmp_path, monkeypatch
    ):
        """A parent exchanged after validation cannot redirect a staged write."""
        safe_parent = tmp_path / "safe"
        (safe_parent / "nested").mkdir(parents=True)
        displaced_parent = tmp_path / "safe-original"

        outside = tmp_path.parent / f"{tmp_path.name}-outside-parent"
        (outside / "nested").mkdir(parents=True)
        outside_target = outside / "nested" / "doc.md"
        outside_target.write_text("external sentinel", encoding="utf-8")

        target = safe_parent / "nested" / "doc.md"
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(target, "replacement")

        real_create = ctx._create_unique_file
        exchanged = False

        def exchange_parent_then_create(anchor, *, prefix, suffix):  # noqa: ANN001
            nonlocal exchanged
            if not exchanged:
                exchanged = True
                safe_parent.rename(displaced_parent)
                try:
                    safe_parent.symlink_to(outside, target_is_directory=True)
                except OSError as exc:  # pragma: no cover - platform capability.
                    pytest.skip(f"symlinks unavailable: {exc}")
            return real_create(anchor, prefix=prefix, suffix=suffix)

        monkeypatch.setattr(ctx, "_create_unique_file", exchange_parent_then_create)

        with pytest.raises((RuntimeError, ValueError, OSError)):
            ctx.commit()

        assert outside_target.read_text(encoding="utf-8") == "external sentinel"
        assert not list(outside.rglob(".*.tmp"))
        assert not list(outside.rglob(".*.bak"))
        assert not list(displaced_parent.rglob(".*.tmp"))
        assert not list(displaced_parent.rglob(".*.bak"))

    def test_failed_restore_preserves_only_recovery_backup(
        self, tmp_path, monkeypatch
    ):
        """A restore error must retain and report the backup containing user data."""
        first = tmp_path / "first.md"
        second = tmp_path / "second.md"
        first.write_text("old first", encoding="utf-8")
        second.write_text("old second", encoding="utf-8")
        outside = tmp_path.parent / f"{tmp_path.name}-rollback-sentinel.md"
        outside.write_text("external sentinel", encoding="utf-8")

        real_replace = os.replace
        primary_failed = False
        restore_failed = False

        def fail_commit_and_restore(src, dst, **kwargs):  # noqa: ANN001
            nonlocal primary_failed, restore_failed
            source = Path(src)
            destination = Path(dst)
            if (
                not primary_failed
                and source.suffix == ".tmp"
                and destination.name == second.name
            ):
                primary_failed = True
                raise OSError("induced commit failure")
            if (
                primary_failed
                and not restore_failed
                and source.suffix == ".bak"
                and destination.name == first.name
            ):
                restore_failed = True
                raise OSError("induced restore failure")
            return real_replace(src, dst, **kwargs)

        monkeypatch.setattr(context_module.os, "replace", fail_commit_and_restore)
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(first, "new first")
        ctx.buffer_write(second, "new second")

        with pytest.raises(OSError, match="induced commit failure"):
            ctx.commit()

        recovery_backups = list(tmp_path.glob(".first.md.*.bak"))
        assert len(recovery_backups) == 1
        assert recovery_backups[0].read_text(encoding="utf-8") == "old first"
        assert "recovery backup preserved at" in ctx.errors[-1]
        assert "induced restore failure" in ctx.errors[-1]
        assert second.read_text(encoding="utf-8") == "old second"
        assert outside.read_text(encoding="utf-8") == "external sentinel"
        assert not list(tmp_path.glob(".*.tmp"))

    @pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits")
    def test_commit_preserves_existing_file_mode(self, tmp_path):
        target = tmp_path / "doc.md"
        target.write_text("old", encoding="utf-8")
        target.chmod(0o640)
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(target, "new")
        ctx.commit()
        assert stat.S_IMODE(target.stat().st_mode) == 0o640

    def test_rollback_clears_buffer(self):
        """Rollback should clear pending writes without executing."""
        ctx = SessionContext(repo_root=Path('/tmp'), config={})
        ctx.buffer_write(Path('/tmp/test.md'), 'content')
        ctx.rollback()
        assert len(ctx.pending_writes) == 0

    def test_warn_collects_warnings(self):
        """Warn should add to warnings list."""
        ctx = SessionContext(repo_root=Path('/tmp'), config={})
        ctx.warn("Test warning")
        assert "Test warning" in ctx.warnings

    def test_from_repo_factory(self, tmp_path):
        """from_repo factory should create context with repo root."""
        (tmp_path / '.ontos').mkdir()
        ctx = SessionContext.from_repo(tmp_path)
        assert ctx.repo_root == tmp_path

    def test_session_context_docstring_describes_buffered_commit_behavior(self):
        docstring = inspect.getdoc(SessionContext) or ""
        module_docstring = inspect.getdoc(context_module) or ""
        assert "two-phase commit" not in docstring.lower()
        assert "atomic writes" not in docstring.lower()
        assert "sequentially" in module_docstring.lower()


class TestFileLocking:
    """Tests for file locking behavior."""
    
    def test_acquire_lock_success(self, tmp_path):
        """Should successfully acquire lock when none exists."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        lock_path = tmp_path / ".ontos.lock"
        
        assert ctx._acquire_lock(lock_path)
        assert lock_path.exists()
        assert ctx._lock_handle is not None
        ctx._release_lock(lock_path)
        assert ctx._lock_handle is None

    def test_acquire_lock_timeout_when_busy(self, tmp_path):
        """Lock acquisition should timeout while another process holds flock."""
        lock_path = tmp_path / ".ontos.lock"
        ready = Event()
        release = Event()
        proc = Process(target=_hold_lock, args=(str(lock_path), ready, release))
        proc.start()
        try:
            assert ready.wait(timeout=2.0)

            ctx = SessionContext(repo_root=tmp_path, config={})
            assert ctx._acquire_lock(lock_path, timeout=0.2) is False
        finally:
            release.set()
            proc.join(timeout=2.0)
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=1.0)


class TestNewImportPaths:
    """Tests that new import paths work correctly (v3.0+ only, shim removed)."""
    
    def test_new_import_parse_frontmatter(self):
        """New import paths should work."""
        from ontos.core.frontmatter import parse_frontmatter
        assert callable(parse_frontmatter)
    
    def test_new_import_session_context(self):
        """SessionContext import should work."""
        from ontos.core.context import SessionContext
        assert SessionContext is not None
    
    def test_new_import_validate_describes(self):
        """validate_describes_field should work."""
        from ontos.core.staleness import validate_describes_field
        assert callable(validate_describes_field)
    
    def test_new_import_check_staleness(self):
        """check_staleness should work."""
        from ontos.core.staleness import check_staleness
        assert callable(check_staleness)
    
    def test_new_import_generate_decision_history(self):
        """generate_decision_history should work."""
        from ontos.core.history import generate_decision_history
        assert callable(generate_decision_history)
    
    def test_new_import_blocked_branch_names(self):
        """BLOCKED_BRANCH_NAMES should work."""
        from ontos.core.config import BLOCKED_BRANCH_NAMES
        assert isinstance(BLOCKED_BRANCH_NAMES, (set, list, tuple))
