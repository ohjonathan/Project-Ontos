#!/usr/bin/env python3
"""Unit tests for install.py security-critical functions.

Tests cover:
- Path traversal detection (POSIX and Windows)
- SHA256 checksum computation
- Installation detection
- Config merge and write
"""

import hashlib
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path to import install.py functions
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from install import (
    is_path_traversal,
    sha256_file,
    detect_existing_installation,
    merge_configs,
    write_user_config,
    read_user_config,
    check_python_version,
)


# =============================================================================
# PATH TRAVERSAL DETECTION TESTS
# =============================================================================

class TestPathTraversal:
    """Tests for is_path_traversal() security function."""

    def test_posix_absolute_path_blocked(self):
        """POSIX absolute paths starting with / must be blocked."""
        assert is_path_traversal("/etc/passwd") is True
        assert is_path_traversal("/usr/bin/python") is True

    def test_parent_directory_traversal_blocked(self):
        """Parent directory traversal with .. must be blocked."""
        assert is_path_traversal("../etc/passwd") is True
        assert is_path_traversal("foo/../../../etc/passwd") is True
        assert is_path_traversal("..") is True

    def test_windows_drive_letter_blocked(self):
        """Windows drive letter paths (C:, D:) must be blocked."""
        assert is_path_traversal("C:\\Windows\\System32") is True
        assert is_path_traversal("D:\\Users\\evil") is True
        assert is_path_traversal("c:\\temp") is True  # lowercase

    def test_windows_unc_path_blocked(self):
        """Windows UNC paths (\\\\server\\share) must be blocked."""
        assert is_path_traversal("\\\\server\\share\\file") is True
        assert is_path_traversal("//server/share/file") is True

    def test_windows_single_backslash_blocked(self):
        """Windows absolute paths with single backslash must be blocked."""
        assert is_path_traversal("\\Windows\\System32") is True
        assert is_path_traversal("\\Users\\Startup\\evil.bat") is True

    def test_relative_paths_allowed(self):
        """Normal relative paths should be allowed."""
        assert is_path_traversal(".ontos/scripts/lib.py") is False
        assert is_path_traversal("ontos.py") is False
        assert is_path_traversal("docs/reference/Manual.md") is False

    def test_dotfile_allowed(self):
        """Single dot files (not ..) should be allowed."""
        assert is_path_traversal(".gitignore") is False
        assert is_path_traversal(".ontos") is False


# =============================================================================
# CHECKSUM TESTS
# =============================================================================

class TestChecksum:
    """Tests for SHA256 checksum computation."""

    def test_sha256_file_correct(self):
        """SHA256 computation should match expected hash."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"test content")
            f.flush()
            temp_path = Path(f.name)

        try:
            # Pre-computed SHA256 of "test content"
            expected = hashlib.sha256(b"test content").hexdigest()
            actual = sha256_file(temp_path)
            assert actual == expected
        finally:
            temp_path.unlink()

    def test_sha256_empty_file(self):
        """SHA256 of empty file should be valid."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            temp_path = Path(f.name)

        try:
            expected = hashlib.sha256(b"").hexdigest()
            actual = sha256_file(temp_path)
            assert actual == expected
        finally:
            temp_path.unlink()


# =============================================================================
# INSTALLATION DETECTION TESTS
# =============================================================================

class TestInstallationDetection:
    """Tests for detect_existing_installation()."""

    def test_no_installation(self, tmp_path, monkeypatch):
        """Empty directory should show no installation."""
        monkeypatch.chdir(tmp_path)
        result = detect_existing_installation()
        assert result["installed"] is False
        assert result["incomplete"] is False
        assert result["version"] is None

    def test_existing_installation(self, tmp_path, monkeypatch):
        """Directory with .ontos should show installed."""
        monkeypatch.chdir(tmp_path)
        ontos_dir = tmp_path / ".ontos"
        ontos_dir.mkdir()
        (tmp_path / "ontos.py").touch()

        result = detect_existing_installation()
        assert result["installed"] is True
        assert ".ontos/" in result["files"]
        assert "ontos.py" in result["files"]

    def test_incomplete_installation(self, tmp_path, monkeypatch):
        """Directory with sentinel file should show incomplete."""
        monkeypatch.chdir(tmp_path)
        ontos_dir = tmp_path / ".ontos"
        ontos_dir.mkdir()
        (ontos_dir / ".install_incomplete").touch()

        result = detect_existing_installation()
        assert result["installed"] is True
        assert result["incomplete"] is True

    def test_version_detection(self, tmp_path, monkeypatch):
        """Should extract version from ontos_config_defaults.py."""
        monkeypatch.chdir(tmp_path)
        ontos_dir = tmp_path / ".ontos" / "scripts"
        ontos_dir.mkdir(parents=True)
        (ontos_dir / "ontos_config_defaults.py").write_text(
            'ONTOS_VERSION = "2.9.4"\n'
        )

        result = detect_existing_installation()
        assert result["version"] == "2.9.4"


# =============================================================================
# CONFIG MERGE TESTS
# =============================================================================

class TestConfigMerge:
    """Tests for merge_configs() and write_user_config()."""

    def test_merge_preserves_old_values(self):
        """Old config values should override new defaults."""
        new_config = {"KEY1": '"default1"', "KEY2": '"default2"', "KEY3": '"new_key"'}
        old_config = {"KEY1": '"custom1"', "KEY2": '"custom2"'}

        merged = merge_configs(new_config, old_config)

        assert merged["KEY1"] == '"custom1"'
        assert merged["KEY2"] == '"custom2"'
        assert merged["KEY3"] == '"new_key"'  # New key preserved

    def test_merge_ignores_removed_keys(self):
        """Old keys not in new config should be dropped."""
        new_config = {"KEY1": '"value1"'}
        old_config = {"KEY1": '"custom"', "DEPRECATED": '"old"'}

        merged = merge_configs(new_config, old_config)

        assert merged["KEY1"] == '"custom"'
        assert "DEPRECATED" not in merged

    def test_write_user_config(self, tmp_path, monkeypatch):
        """write_user_config should update values in file."""
        monkeypatch.chdir(tmp_path)
        # Config file is at project root (not .ontos/scripts/)
        config_file = tmp_path / "ontos_config.py"

        # Create initial config
        config_file.write_text(
            '# Config file\n'
            'KEY1 = "original1"\n'
            'KEY2 = "original2"\n'
            '# Comment line\n'
            'KEY3 = "original3"\n'
        )

        # Write new values
        result = write_user_config({"KEY1": '"updated1"', "KEY3": '"updated3"'})

        assert result is True
        content = config_file.read_text()
        assert '"updated1"' in content
        assert '"original2"' in content  # Unchanged
        assert '"updated3"' in content
        assert '# Config file' in content  # Comments preserved
        assert '# Comment line' in content

    def test_write_user_config_missing_file(self, tmp_path, monkeypatch):
        """write_user_config should return False if file missing."""
        monkeypatch.chdir(tmp_path)
        result = write_user_config({"KEY": "value"})
        assert result is False


# =============================================================================
# PYTHON VERSION CHECK
# =============================================================================

class TestPythonVersion:
    """Tests for check_python_version()."""

    def test_current_version_passes(self):
        """Current Python should pass version check."""
        # We're running tests with a valid Python, so this should pass
        result = check_python_version()
        assert result is True
