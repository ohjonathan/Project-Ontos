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
import tempfile
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

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
    def test_exclusive_create_rejects_symlinked_workspace_root(self, tmp_path):
        external = tmp_path / "external-root"
        external.mkdir()
        workspace_link = tmp_path / "workspace-link"
        try:
            workspace_link.symlink_to(external, target_is_directory=True)
        except OSError as exc:  # pragma: no cover - platform policy.
            pytest.skip(f"symlink creation unavailable: {exc}")

        ctx = SessionContext(repo_root=workspace_link, config={})
        with pytest.raises(ValueError, match="workspace root must not be"):
            ctx.create_text_file_exclusively(
                workspace_link / "created.md",
                "payload",
            )

        assert not (external / "created.md").exists()

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

    def test_commit_rejects_workspace_root_replacement_after_lock(
        self,
        tmp_path,
        monkeypatch,
    ):
        root = tmp_path / "workspace"
        root.mkdir()
        displaced = tmp_path / "workspace-displaced"
        target = root / "doc.md"
        ctx = SessionContext(repo_root=root, config={})
        ctx.buffer_write(target, "payload")
        real_prepare = ctx._prepare_operations

        def replace_root_before_prepare():
            root.rename(displaced)
            root.mkdir()
            return real_prepare()

        monkeypatch.setattr(ctx, "_prepare_operations", replace_root_before_prepare)

        with pytest.raises(RuntimeError, match="workspace root changed"):
            ctx.commit()

        assert not (root / "doc.md").exists()
        assert not (displaced / "doc.md").exists()
        assert (displaced / ".ontos.lock").is_file()
        assert not (root / ".ontos.lock").exists()

    def test_commit_rejects_workspace_root_replacement_after_buffering(
        self,
        tmp_path,
    ):
        root = tmp_path / "workspace"
        root.mkdir()
        displaced = tmp_path / "workspace-displaced"
        target = root / "doc.md"
        ctx = SessionContext(repo_root=root, config={})
        ctx.buffer_write(target, "payload")

        root.rename(displaced)
        root.mkdir()

        with pytest.raises(RuntimeError, match="workspace root changed"):
            ctx.commit()

        assert not (root / "doc.md").exists()
        assert not (displaced / "doc.md").exists()
        assert not (root / ".ontos.lock").exists()
        assert not (displaced / ".ontos.lock").exists()

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

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
    def test_commit_rejects_staged_temp_swap_without_touching_external_file(
        self,
        tmp_path,
        monkeypatch,
    ):
        outside = tmp_path.parent / f"{tmp_path.name}-staged-sentinel.md"
        outside.write_bytes(b"external sentinel")
        before = outside.stat()
        target = tmp_path / "doc.md"

        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(target, "replacement")
        real_stage = ctx._stage_text

        def stage_then_swap(anchor, final_name, content):  # noqa: ANN001
            temp_name, binding = real_stage(anchor, final_name, content)
            staged_path = anchor.path / temp_name
            staged_path.unlink()
            try:
                staged_path.symlink_to(outside)
            except OSError as exc:  # pragma: no cover - Windows policy dependent.
                pytest.skip(f"symlink creation unavailable: {exc}")
            return temp_name, binding

        monkeypatch.setattr(ctx, "_stage_text", stage_then_swap)

        with pytest.raises(RuntimeError, match="staged write.*regular"):
            ctx.commit()

        after = outside.stat()
        assert outside.read_bytes() == b"external sentinel"
        assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
        assert (after.st_size, after.st_mtime_ns) == (
            before.st_size,
            before.st_mtime_ns,
        )
        assert not target.exists()
        retained_temps = list(tmp_path.glob(".*.tmp"))
        assert len(retained_temps) == 1
        assert retained_temps[0].is_symlink()

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
    def test_commit_rejects_backup_reservation_swap_before_rename(
        self,
        tmp_path,
        monkeypatch,
    ):
        outside = tmp_path.parent / f"{tmp_path.name}-backup-sentinel.md"
        outside.write_bytes(b"external sentinel")
        before = outside.stat()
        target = tmp_path / "doc.md"
        target.write_text("original", encoding="utf-8")

        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(target, "replacement")
        real_reserve = ctx._reserve_backup

        def reserve_then_swap(anchor, final_name):  # noqa: ANN001
            backup_name, binding = real_reserve(anchor, final_name)
            backup_path = anchor.path / backup_name
            backup_path.unlink()
            try:
                backup_path.symlink_to(outside)
            except OSError as exc:  # pragma: no cover - Windows policy dependent.
                pytest.skip(f"symlink creation unavailable: {exc}")
            return backup_name, binding

        monkeypatch.setattr(ctx, "_reserve_backup", reserve_then_swap)

        with pytest.raises(RuntimeError, match="backup reservation.*regular"):
            ctx.commit()

        after = outside.stat()
        assert target.read_text(encoding="utf-8") == "original"
        assert outside.read_bytes() == b"external sentinel"
        assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
        assert (after.st_size, after.st_mtime_ns) == (
            before.st_size,
            before.st_mtime_ns,
        )
        assert not list(tmp_path.glob(".*.tmp"))
        retained_backups = list(tmp_path.glob(".*.bak"))
        assert len(retained_backups) == 1
        assert retained_backups[0].is_symlink()

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
    def test_commit_verifies_final_binding_and_restores_original(
        self,
        tmp_path,
        monkeypatch,
    ):
        outside = tmp_path.parent / f"{tmp_path.name}-final-sentinel.md"
        outside.write_bytes(b"external sentinel")
        before = outside.stat()
        target = tmp_path / "doc.md"
        target.write_text("original", encoding="utf-8")

        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(target, "replacement")
        real_replace = ctx._replace_entry
        swapped = False

        def replace_then_swap(
            source_anchor,
            source_name,
            destination_anchor,
            destination_name,
            **kwargs,
        ):  # noqa: ANN001
            nonlocal swapped
            real_replace(
                source_anchor,
                source_name,
                destination_anchor,
                destination_name,
                **kwargs,
            )
            if not swapped and source_name.endswith(".tmp"):
                swapped = True
                target.unlink()
                try:
                    target.symlink_to(outside)
                except OSError as exc:  # pragma: no cover - Windows policy dependent.
                    pytest.skip(f"symlink creation unavailable: {exc}")

        monkeypatch.setattr(ctx, "_replace_entry", replace_then_swap)

        with pytest.raises(RuntimeError, match="committed write.*regular"):
            ctx.commit()

        after = outside.stat()
        assert target.is_symlink()
        assert outside.read_bytes() == b"external sentinel"
        assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
        assert (after.st_size, after.st_mtime_ns) == (
            before.st_size,
            before.st_mtime_ns,
        )
        assert not list(tmp_path.glob(".*.tmp"))
        recovery_backups = list(tmp_path.glob(".*.bak"))
        assert len(recovery_backups) == 1
        assert recovery_backups[0].read_text(encoding="utf-8") == "original"
        assert "recovery backup preserved at" in ctx.errors[-1]

    @pytest.mark.skipif(not hasattr(os, "link"), reason="hard links unavailable")
    @pytest.mark.parametrize("operation", ["delete", "move"])
    def test_commit_rejects_phase_one_source_binding_swap(
        self,
        tmp_path,
        monkeypatch,
        operation,
    ):
        source = tmp_path / "source.md"
        displaced = tmp_path / "source-original.md"
        destination = tmp_path / "destination.md"
        trigger = tmp_path / "trigger.md"
        source.write_text("original source", encoding="utf-8")
        outside = tmp_path.parent / f"{tmp_path.name}-{operation}-sentinel.md"
        outside.write_bytes(b"external sentinel")
        before = outside.stat()

        ctx = SessionContext(repo_root=tmp_path, config={})
        if operation == "delete":
            ctx.buffer_delete(source)
        else:
            ctx.buffer_move(source, destination)
        ctx.buffer_write(trigger, "phase-one trigger")
        real_stage = ctx._stage_text
        swapped = False

        def stage_then_swap_source(anchor, final_name, content):  # noqa: ANN001
            nonlocal swapped
            staged = real_stage(anchor, final_name, content)
            if not swapped:
                swapped = True
                source.rename(displaced)
                os.link(outside, source)
            return staged

        monkeypatch.setattr(ctx, "_stage_text", stage_then_swap_source)

        with pytest.raises(RuntimeError, match=rf"{operation} source changed"):
            ctx.commit()

        after = outside.stat()
        assert outside.read_bytes() == b"external sentinel"
        assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
        assert (after.st_size, after.st_mtime_ns) == (
            before.st_size,
            before.st_mtime_ns,
        )
        assert displaced.read_text(encoding="utf-8") == "original source"
        assert source.stat().st_ino == outside.stat().st_ino
        assert not destination.exists()
        assert not trigger.exists()
        assert not list(tmp_path.glob(".*.tmp"))
        assert not list(tmp_path.glob(".*.bak"))

    @pytest.mark.skipif(not hasattr(os, "link"), reason="hard links unavailable")
    def test_commit_move_verifies_destination_binding_after_rename(
        self,
        tmp_path,
        monkeypatch,
    ):
        source = tmp_path / "source.md"
        displaced = tmp_path / "source-original.md"
        destination = tmp_path / "destination.md"
        source.write_text("original source", encoding="utf-8")
        outside = tmp_path.parent / f"{tmp_path.name}-move-window-sentinel.md"
        outside.write_bytes(b"external sentinel")
        before = outside.stat()

        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_move(source, destination)
        real_replace = ctx._replace_entry
        swapped = False

        def swap_source_in_rename_window(
            source_anchor,
            source_name,
            destination_anchor,
            destination_name,
            **kwargs,
        ):  # noqa: ANN001
            nonlocal swapped
            if not swapped and source_name == source.name:
                swapped = True
                source.rename(displaced)
                os.link(outside, source)
            real_replace(
                source_anchor,
                source_name,
                destination_anchor,
                destination_name,
                **kwargs,
            )

        monkeypatch.setattr(ctx, "_replace_entry", swap_source_in_rename_window)

        with pytest.raises(RuntimeError, match="rename source changed"):
            ctx.commit()

        after = outside.stat()
        assert outside.read_bytes() == b"external sentinel"
        assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
        assert (after.st_size, after.st_mtime_ns) == (
            before.st_size,
            before.st_mtime_ns,
        )
        assert displaced.read_text(encoding="utf-8") == "original source"
        assert source.stat().st_ino == outside.stat().st_ino
        assert not destination.exists()
        assert not list(tmp_path.glob(".*.bak"))

    @pytest.mark.parametrize("operation", ["write", "move"])
    def test_commit_refuses_destination_created_in_rename_window(
        self,
        tmp_path,
        monkeypatch,
        operation,
    ):
        destination = tmp_path / "destination.md"
        ctx = SessionContext(repo_root=tmp_path, config={})
        if operation == "write":
            source = None
            ctx.buffer_write(destination, "transaction payload")
        else:
            source = tmp_path / "source.md"
            source.write_text("move payload", encoding="utf-8")
            ctx.buffer_move(source, destination)

        real_replace = ctx._replace_entry
        raced = False

        def create_destination_before_replace(
            source_anchor,
            source_name,
            destination_anchor,
            destination_name,
            **kwargs,
        ):  # noqa: ANN001
            nonlocal raced
            if not raced and destination_name == destination.name:
                raced = True
                destination.write_text("racer payload", encoding="utf-8")
            return real_replace(
                source_anchor,
                source_name,
                destination_anchor,
                destination_name,
                **kwargs,
            )

        monkeypatch.setattr(ctx, "_replace_entry", create_destination_before_replace)

        with pytest.raises(RuntimeError, match="rename destination appeared"):
            ctx.commit()

        assert destination.read_text(encoding="utf-8") == "racer payload"
        if source is not None:
            assert source.read_text(encoding="utf-8") == "move payload"
        assert not list(tmp_path.glob(".*.tmp"))
        assert not list(tmp_path.glob(".*.bak"))

    def test_commit_delete_detects_recreated_destination_and_preserves_backup(
        self,
        tmp_path,
        monkeypatch,
    ):
        target = tmp_path / "target.md"
        target.write_text("original payload", encoding="utf-8")
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_delete(target)
        real_replace = ctx._replace_entry
        recreated = False

        def recreate_after_backup(
            source_anchor,
            source_name,
            destination_anchor,
            destination_name,
            **kwargs,
        ):  # noqa: ANN001
            nonlocal recreated
            result = real_replace(
                source_anchor,
                source_name,
                destination_anchor,
                destination_name,
                **kwargs,
            )
            if not recreated and source_name == target.name:
                recreated = True
                target.write_text("racer payload", encoding="utf-8")
            return result

        monkeypatch.setattr(ctx, "_replace_entry", recreate_after_backup)

        with pytest.raises(RuntimeError, match="deleted destination appeared"):
            ctx.commit()

        assert target.read_text(encoding="utf-8") == "racer payload"
        recovery_backups = list(tmp_path.glob(".target.md.*.bak"))
        assert len(recovery_backups) == 1
        assert recovery_backups[0].read_text(encoding="utf-8") == "original payload"
        assert "recovery backup preserved at" in ctx.errors[-1]

    def test_ambiguous_completed_backup_rename_restores_original(
        self,
        tmp_path,
        monkeypatch,
    ):
        target = tmp_path / "target.md"
        target.write_text("original payload", encoding="utf-8")
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_write(target, "replacement payload")
        real_replace = ctx._replace_entry
        raised = False

        def replace_then_raise(
            source_anchor,
            source_name,
            destination_anchor,
            destination_name,
            **kwargs,
        ):  # noqa: ANN001
            nonlocal raised
            result = real_replace(
                source_anchor,
                source_name,
                destination_anchor,
                destination_name,
                **kwargs,
            )
            if not raised and source_name == target.name:
                raised = True
                raise OSError("ambiguous rename completion")
            return result

        monkeypatch.setattr(ctx, "_replace_entry", replace_then_raise)

        with pytest.raises(OSError, match="ambiguous rename completion"):
            ctx.commit()

        assert target.read_text(encoding="utf-8") == "original payload"
        assert not list(tmp_path.glob(".*.bak"))
        assert "ambiguous rename completion" in ctx.errors[-1]

    def test_move_rollback_reports_disappeared_applied_destination(
        self,
        tmp_path,
        monkeypatch,
    ):
        source = tmp_path / "source.md"
        destination = tmp_path / "destination.md"
        later = tmp_path / "later.md"
        source.write_text("move payload", encoding="utf-8")
        ctx = SessionContext(repo_root=tmp_path, config={})
        ctx.buffer_move(source, destination)
        ctx.buffer_write(later, "later payload")
        real_replace = ctx._replace_entry
        removed = False

        def disappear_then_fail_later(
            source_anchor,
            source_name,
            destination_anchor,
            destination_name,
            **kwargs,
        ):  # noqa: ANN001
            nonlocal removed
            if source_name.endswith(".tmp") and destination_name == later.name:
                raise OSError("later operation fails")
            result = real_replace(
                source_anchor,
                source_name,
                destination_anchor,
                destination_name,
                **kwargs,
            )
            if not removed and destination_name == destination.name:
                removed = True
                destination.unlink()
            return result

        monkeypatch.setattr(ctx, "_replace_entry", disappear_then_fail_later)

        with pytest.raises(RuntimeError, match="moved destination disappeared"):
            ctx.commit()

        assert not source.exists()
        assert not destination.exists()
        assert not later.exists()
        assert "moved destination disappeared" in ctx.errors[-1]
        assert "rollback failed" in ctx.errors[-1]

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

    def test_release_lock_closes_root_guard_when_handle_close_raises(
        self,
        tmp_path,
        monkeypatch,
    ):
        lock_path = tmp_path / ".ontos.lock"
        real_open = context_module.open_lock_file
        opened = []

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

        monkeypatch.setattr(context_module, "open_lock_file", open_proxy)
        ctx = SessionContext(repo_root=tmp_path, config={})
        assert ctx._acquire_lock(lock_path)
        root_fd = ctx._root_lock_fd
        assert root_fd is not None

        ctx._release_lock(lock_path)

        assert ctx._lock_handle is None
        assert ctx._root_lock_fd is None
        assert opened[0].handle.closed
        with pytest.raises(OSError):
            os.fstat(root_fd)
        assert "Workspace lock cleanup failed" in ctx.errors[-1]

    def test_acquire_lock_preserves_regular_legacy_lock_bytes(self, tmp_path):
        lock_path = tmp_path / ".ontos.lock"
        lock_path.write_bytes(b"legacy lock payload\n")
        before = lock_path.stat()
        ctx = SessionContext(repo_root=tmp_path, config={})

        assert ctx._acquire_lock(lock_path)
        ctx._release_lock(lock_path)

        after = lock_path.stat()
        assert lock_path.read_bytes() == b"legacy lock payload\n"
        assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
        assert (after.st_size, after.st_mtime_ns) == (
            before.st_size,
            before.st_mtime_ns,
        )

    def test_acquire_lock_rejects_visible_lock_replacement(
        self,
        tmp_path,
        monkeypatch,
    ):
        lock_path = tmp_path / ".ontos.lock"
        real_open = context_module.open_lock_file
        orphaned_handles = []

        def open_then_replace(path):  # noqa: ANN001
            handle = real_open(path)
            orphaned_handles.append(handle)
            path.unlink()
            path.write_text("replacement", encoding="utf-8")
            return handle

        monkeypatch.setattr(context_module, "open_lock_file", open_then_replace)
        ctx = SessionContext(repo_root=tmp_path, config={})

        with pytest.raises(
            (RuntimeError, ValueError),
            match="exactly one link|path changed|disappeared",
        ):
            ctx._acquire_lock(lock_path)

        assert len(orphaned_handles) == 1
        assert orphaned_handles[0].closed
        assert lock_path.read_text(encoding="utf-8") == "replacement"
        assert ctx._lock_handle is None

    @pytest.mark.skipif(
        os.name != "posix" or not hasattr(os, "link"),
        reason="POSIX hard-link regression",
    )
    def test_acquire_lock_rejects_hardlink_without_touching_external_file(
        self,
        tmp_path,
    ):
        root = tmp_path / "workspace"
        root.mkdir()
        outside = tmp_path / "external-lock"
        outside.write_bytes(b"external sentinel")
        lock_path = root / ".ontos.lock"
        os.link(outside, lock_path)
        before = outside.stat()

        ctx = SessionContext(repo_root=root, config={})
        with pytest.raises(ValueError, match="multiple hard links"):
            ctx._acquire_lock(lock_path)

        after = outside.stat()
        assert outside.read_bytes() == b"external sentinel"
        assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
        assert (after.st_size, after.st_mtime_ns, after.st_nlink) == (
            before.st_size,
            before.st_mtime_ns,
            before.st_nlink,
        )
        assert lock_path.stat().st_ino == outside.stat().st_ino
        assert ctx._lock_handle is None

    @pytest.mark.skipif(not hasattr(os, "link"), reason="hard links unavailable")
    def test_windows_lock_guard_rejects_hardlink_before_crt_backend_write(
        self,
        tmp_path,
        monkeypatch,
    ):
        """Simulated Windows handle metadata must stop before msvcrt owns it."""
        import ctypes

        import ontos.core.locking as locking_module

        root = tmp_path / "workspace"
        root.mkdir()
        outside = tmp_path / "external-lock"
        outside.write_bytes(b"external sentinel")
        lock_path = root / ".ontos.lock"
        os.link(outside, lock_path)
        before = outside.stat()

        class FakeFunction:
            def __init__(self, implementation):  # noqa: ANN001
                self.implementation = implementation
                self.argtypes = None
                self.restype = None

            def __call__(self, *args):  # noqa: ANN002
                return self.implementation(*args)

        class FakeKernel32:
            def __init__(self):
                self.next_handle = 100
                self.paths = {}
                self.CreateFileW = FakeFunction(self.create_file)
                self.CloseHandle = FakeFunction(self.close_handle)
                self.GetFileInformationByHandle = FakeFunction(
                    self.get_file_information
                )

            @staticmethod
            def _handle_value(handle):  # noqa: ANN001
                return int(getattr(handle, "value", handle))

            def create_file(
                self,
                path,
                access,
                sharing,
                security,
                disposition,
                flags,
                template,
            ):  # noqa: ANN001
                _ = (access, sharing, security, disposition, flags, template)
                handle = self.next_handle
                self.next_handle += 1
                self.paths[handle] = Path(path)
                return handle

            def close_handle(self, handle):  # noqa: ANN001
                self.paths.pop(self._handle_value(handle), None)
                return 1

            def get_file_information(self, handle, information_pointer):  # noqa: ANN001
                path = self.paths[self._handle_value(handle)]
                information = information_pointer._obj
                information.dwFileAttributes = 0x10 if path.is_dir() else 0x80
                information.nNumberOfLinks = path.stat().st_nlink
                return 1

        class FakeMsvcrt:
            def __init__(self):
                self.open_calls = 0

            def open_osfhandle(self, handle, flags):  # noqa: ANN001
                _ = (handle, flags)
                self.open_calls += 1
                outside.write_bytes(b"backend unexpectedly wrote")
                raise AssertionError("CRT backend must not receive a hard-linked lock")

        kernel32 = FakeKernel32()
        msvcrt = FakeMsvcrt()
        monkeypatch.setattr(
            ctypes,
            "WinDLL",
            lambda *args, **kwargs: kernel32,
            raising=False,
        )
        monkeypatch.setattr(locking_module, "_msvcrt", msvcrt)

        with pytest.raises(ValueError, match="multiple hard links"):
            locking_module._open_windows_lock_file(lock_path)

        after = outside.stat()
        assert msvcrt.open_calls == 0
        assert outside.read_bytes() == b"external sentinel"
        assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
        assert (after.st_size, after.st_mtime_ns, after.st_nlink) == (
            before.st_size,
            before.st_mtime_ns,
            before.st_nlink,
        )
        assert lock_path.stat().st_ino == outside.stat().st_ino

    @pytest.mark.skipif(not hasattr(os, "link"), reason="hard links unavailable")
    def test_windows_lock_backend_never_writes_after_late_hardlink(
        self,
        tmp_path,
        monkeypatch,
    ):
        """LockFileEx must not mutate an alias added after the open guard."""
        import ctypes

        import ontos.core.locking as locking_module

        class FakeFunction:
            def __init__(self, implementation):  # noqa: ANN001
                self.implementation = implementation
                self.argtypes = None
                self.restype = None

            def __call__(self, *args):  # noqa: ANN002
                return self.implementation(*args)

        class FakeKernel32:
            LockFileEx = FakeFunction(lambda *args: 1)
            UnlockFileEx = FakeFunction(lambda *args: 1)

        class FakeMsvcrt:
            @staticmethod
            def get_osfhandle(fd):  # noqa: ANN001
                return fd

        lock_path = tmp_path / ".ontos.lock"
        alias = tmp_path / "external-alias"
        lock_path.write_bytes(b"")
        with lock_path.open("a+", encoding="utf-8") as handle:
            os.link(lock_path, alias)
            assert os.fstat(handle.fileno()).st_nlink == 2
            monkeypatch.setattr(locking_module, "_fcntl", None)
            monkeypatch.setattr(locking_module, "_msvcrt", FakeMsvcrt())
            monkeypatch.setattr(
                ctypes,
                "WinDLL",
                lambda *args, **kwargs: FakeKernel32(),
                raising=False,
            )

            with pytest.raises(ValueError, match="multiple hard links"):
                locking_module.try_acquire_exclusive(handle)
            alias.unlink()
            assert locking_module.try_acquire_exclusive(handle) is True
            locking_module.release_exclusive(handle)

        assert lock_path.read_bytes() == b""
        assert not alias.exists()

    def test_acquire_lock_allows_platform_ancestor_aliases(self):
        """System aliases such as macOS /var must not look like root attacks."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ctx = SessionContext(repo_root=root, config={})
            lock_path = root / ".ontos.lock"

            assert ctx._acquire_lock(lock_path)
            ctx._release_lock(lock_path)

            assert lock_path.is_file()

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
    def test_acquire_lock_rejects_external_symlink_without_touching_target(
        self,
        tmp_path,
    ):
        root = tmp_path / "workspace"
        root.mkdir()
        outside = tmp_path / "external-lock"
        outside.write_bytes(b"external sentinel")
        before = outside.stat()
        lock_path = root / ".ontos.lock"
        try:
            lock_path.symlink_to(outside)
        except OSError as exc:  # pragma: no cover - Windows policy dependent.
            pytest.skip(f"symlink creation unavailable: {exc}")

        ctx = SessionContext(repo_root=root, config={})
        with pytest.raises(ValueError, match="symbolic link|reparse point"):
            ctx._acquire_lock(lock_path)

        after = outside.stat()
        assert outside.read_bytes() == b"external sentinel"
        assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
        assert (after.st_size, after.st_mtime_ns) == (
            before.st_size,
            before.st_mtime_ns,
        )
        assert ctx._lock_handle is None

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
    def test_acquire_lock_rejects_symlinked_workspace_root(
        self,
        tmp_path,
    ):
        outside = tmp_path / "outside-workspace"
        outside.mkdir()
        sentinel = outside / "sentinel"
        sentinel.write_bytes(b"external sentinel")
        before = sentinel.stat()
        workspace_link = tmp_path / "workspace-link"
        try:
            workspace_link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:  # pragma: no cover - Windows policy dependent.
            pytest.skip(f"symlink creation unavailable: {exc}")

        ctx = SessionContext(repo_root=workspace_link, config={})
        with pytest.raises(ValueError, match="symbolic link|reparse point"):
            ctx._acquire_lock(workspace_link / ".ontos.lock")

        after = sentinel.stat()
        assert not (outside / ".ontos.lock").exists()
        assert sentinel.read_bytes() == b"external sentinel"
        assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
        assert ctx._lock_handle is None

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
    def test_acquire_lock_does_not_create_parent_through_symlink(
        self,
        tmp_path,
    ):
        outside = tmp_path / "outside-parent"
        outside.mkdir()
        alias = tmp_path / "alias"
        try:
            alias.symlink_to(outside, target_is_directory=True)
        except OSError as exc:  # pragma: no cover - Windows policy dependent.
            pytest.skip(f"symlink creation unavailable: {exc}")
        workspace = alias / "new-workspace"

        ctx = SessionContext(repo_root=workspace, config={})
        with pytest.raises((FileNotFoundError, ValueError)):
            ctx._acquire_lock(workspace / ".ontos.lock")

        assert not (outside / "new-workspace").exists()
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
