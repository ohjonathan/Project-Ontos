"""SessionContext - Transaction-aware session state.

This module implements the core SessionContext dataclass which captures all
state for an Ontos session and provides transaction support for file operations.

Per v2.8 implementation plan, SessionContext:
- Is the single source of truth for repository configuration
- Buffers file operations for later commit
- Provides atomic writes via two-phase commit
- Uses file locking with stale detection
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum
import os
import time


class FileOperation(Enum):
    """Types of file operations that can be buffered."""
    WRITE = "write"
    DELETE = "delete"
    MOVE = "move"


@dataclass
class PendingWrite:
    """A buffered file operation."""
    operation: FileOperation
    path: Path
    content: Optional[str] = None  # For WRITE
    destination: Optional[Path] = None  # For MOVE


@dataclass
class SessionContext:
    """Captures all state for an Ontos session.

    This is the single source of truth for:
    - Repository configuration
    - Environment state
    - Pending file operations (transaction buffer)

    SCOPE LIMITS (v2.8):
    SessionContext should NOT:
    - Handle output formatting (that's OutputHandler's job)
    - Contain I/O providers (keep git calls as marked impure functions)
    - Cache parsed documents (keep it focused on transaction state)
    - Grow beyond config + env + writes + diagnostics
    """
    # Immutable state (set at creation)
    repo_root: Path
    config: Dict
    cwd: Path = field(default_factory=Path.cwd)
    env: Dict[str, str] = field(default_factory=lambda: dict(os.environ))

    # Mutable state (changes during session)
    pending_writes: List[PendingWrite] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @classmethod
    def from_repo(cls, repo_root: Path) -> 'SessionContext':
        """Factory method to create context from repository path.

        This encapsulates config loading logic.
        
        Args:
            repo_root: Path to the repository root.
            
        Returns:
            SessionContext instance with loaded configuration.
        """
        # Build a config dict from the resolved settings
        config = {}
        config_keys = [
            'DOCS_DIR', 'AUTO_ARCHIVE_ON_PUSH', 'AUTO_CONSOLIDATE',
            'LOG_RETENTION_COUNT', 'ONTOS_MODE', 'DEFAULT_SOURCE',
            'SKIP_PATTERNS', 'LOGS_DIR', 'SCAN_DIRECTORIES'
        ]
        
        # Try to load config values
        try:
            import ontos_config
            for key in config_keys:
                if hasattr(ontos_config, key):
                    config[key] = getattr(ontos_config, key)
        except ImportError:
            pass
            
        return cls(repo_root=repo_root, config=config)

    def buffer_write(self, path: Path, content: str) -> None:
        """Buffer a file write for later commit.
        
        Args:
            path: Target file path.
            content: Content to write.
        """
        self.pending_writes.append(PendingWrite(
            operation=FileOperation.WRITE,
            path=path,
            content=content
        ))

    def buffer_delete(self, path: Path) -> None:
        """Buffer a file deletion for later commit.
        
        Args:
            path: File path to delete.
        """
        self.pending_writes.append(PendingWrite(
            operation=FileOperation.DELETE,
            path=path
        ))

    def buffer_move(self, source: Path, destination: Path) -> None:
        """Buffer a file move for later commit.
        
        Args:
            source: Source file path.
            destination: Destination file path.
        """
        self.pending_writes.append(PendingWrite(
            operation=FileOperation.MOVE,
            path=source,
            destination=destination
        ))

    def commit(self) -> List[Path]:
        """Execute all buffered operations with two-phase commit.

        ATOMICITY: Uses temp-then-rename pattern. If any operation fails,
        previous temp files are cleaned up. Rename is atomic on POSIX.

        Returns:
            List of paths successfully modified.

        Raises:
            IOError: If a write operation fails.
            RuntimeError: If lock cannot be acquired.
        """
        if not self.pending_writes:
            return []

        lock_path = self.repo_root / '.ontos' / 'write.lock'
        if not self._acquire_lock(lock_path):
            raise RuntimeError(
                "Could not acquire write lock. "
                "Another Ontos process may be running."
            )

        staged: List[tuple] = []  # (temp, final)
        modified: List[Path] = []

        try:
            # Phase 1: Write to temp files
            for op in self.pending_writes:
                if op.operation == FileOperation.WRITE:
                    op.path.parent.mkdir(parents=True, exist_ok=True)
                    temp = op.path.with_suffix(op.path.suffix + '.tmp')
                    temp.write_text(op.content)
                    staged.append((temp, op.path))
                elif op.operation == FileOperation.DELETE:
                    if op.path.exists():
                        # For delete, we stage by tracking what to delete
                        staged.append((None, op.path))
                elif op.operation == FileOperation.MOVE:
                    if op.path.exists():
                        staged.append((op.path, op.destination))

            # Phase 2: Atomic rename/apply
            for temp, final in staged:
                if temp is None:
                    # Delete operation
                    final.unlink()
                    modified.append(final)
                elif temp != final:
                    # Write or Move: rename temp to final (atomic on POSIX)
                    final.parent.mkdir(parents=True, exist_ok=True)
                    temp.rename(final)
                    modified.append(final)

        except Exception as e:
            # Cleanup temp files on failure
            for temp, final in staged:
                if temp is not None and temp != final:
                    try:
                        if temp.exists():
                            temp.unlink()
                    except (OSError, FileNotFoundError):
                        pass
            self.error(f"Commit failed: {e}")
            raise

        finally:
            self._release_lock(lock_path)
            self.pending_writes.clear()

        return modified

    def rollback(self) -> None:
        """Discard all buffered operations."""
        self.pending_writes.clear()

    def warn(self, message: str) -> None:
        """Record a warning (does not print).
        
        Args:
            message: Warning message to record.
        """
        self.warnings.append(message)

    def error(self, message: str) -> None:
        """Record an error (does not print).
        
        Args:
            message: Error message to record.
        """
        self.errors.append(message)

    def _acquire_lock(self, lock_path: Path, timeout: float = 5.0) -> bool:
        """Acquire a simple file lock with stale detection.

        Uses atomic file creation (O_CREAT | O_EXCL). If a stale lock
        is detected (holding process is dead), it is automatically removed.

        Args:
            lock_path: Path to lock file
            timeout: Maximum seconds to wait

        Returns:
            True if lock acquired, False if timeout
        """
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        start = time.time()

        while time.time() - start < timeout:
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return True
            except FileExistsError:
                # Check if holding process is still alive
                try:
                    pid = int(lock_path.read_text().strip())
                    os.kill(pid, 0)  # Raises if process doesn't exist
                except (ProcessLookupError, ValueError, OSError):
                    # Stale lock - process is dead, remove it
                    try:
                        lock_path.unlink()
                    except FileNotFoundError:
                        pass
                    continue
                time.sleep(0.1)

        return False

    def _release_lock(self, lock_path: Path) -> None:
        """Release the file lock.
        
        Args:
            lock_path: Path to lock file.
        """
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass  # Already released
