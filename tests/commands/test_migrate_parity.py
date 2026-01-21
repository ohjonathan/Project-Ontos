"""Parity tests for migrate command."""

import subprocess
import os
from pathlib import Path

import pytest


def test_migrate_help_parity():
    """Native --help matches legacy."""
    result = subprocess.run(
        ["python3", "-m", "ontos.cli", "migrate", "--help"],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    assert "--check" in result.stdout
    assert "--apply" in result.stdout
    assert "migrate" in result.stdout.lower()


def test_migrate_check_parity(tmp_path):
    """Migrate check identifies legacy documents."""
    # Create a legacy doc (no ontos_schema)
    legacy_file = tmp_path / "legacy.md"
    legacy_file.write_text("---\nid: legacy_doc\ntype: atom\n---\n")

    # Run native command
    result = subprocess.run(
        ["python3", "-m", "ontos.cli", "migrate", "--check", "--dirs", str(tmp_path)],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )

    assert result.returncode == 1 # Exit code 1 when migrations needed
    assert "Need migration: 1" in result.stdout
    assert "legacy.md" in result.stdout
