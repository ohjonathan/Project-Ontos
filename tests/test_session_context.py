"""Tests for SessionContext and backwards compatibility.

Tests the v2.8 refactoring deliverables:
- SessionContext buffer/commit/rollback operations
- File locking with stale detection
- Backwards compatibility (old imports reference same objects as new)
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from ontos.core.context import SessionContext, FileOperation, PendingWrite


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


class TestFileLocking:
    """Tests for file locking behavior."""
    
    def test_acquire_lock_success(self, tmp_path):
        """Should successfully acquire lock when none exists."""
        ctx = SessionContext(repo_root=tmp_path, config={})
        lock_path = tmp_path / '.ontos' / 'write.lock'
        lock_path.parent.mkdir(parents=True)
        
        assert ctx._acquire_lock(lock_path)
        assert lock_path.exists()
        assert lock_path.read_text() == str(os.getpid())
        ctx._release_lock(lock_path)
        assert not lock_path.exists()

    def test_stale_lock_detection(self, tmp_path):
        """Lock held by dead process should be removed."""
        lock_path = tmp_path / '.ontos' / 'write.lock'
        lock_path.parent.mkdir(parents=True)
        lock_path.write_text('99999999')  # Non-existent PID

        ctx = SessionContext(repo_root=tmp_path, config={})
        assert ctx._acquire_lock(lock_path, timeout=1.0)
        ctx._release_lock(lock_path)


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
