"""Parity tests for schema-migrate command (renamed from migrate in v3.2)."""

import subprocess
import sys
from pathlib import Path

import pytest


def test_schema_migrate_help_parity():
    """Native --help matches legacy."""
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "schema-migrate", "--help"],
        capture_output=True,
        text=True
    )
    assert "--check" in result.stdout
    assert "--apply" in result.stdout
    assert "migrate" in result.stdout.lower()


def test_schema_migrate_check_parity(tmp_path):
    """Schema-migrate check identifies legacy documents."""
    # Create a legacy doc (no ontos_schema)
    legacy_file = tmp_path / "legacy.md"
    legacy_file.write_text("---\nid: legacy_doc\ntype: atom\n---\n")

    # Run native command
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "schema-migrate", "--check", "--dirs", str(tmp_path)],
        capture_output=True,
        text=True
    )

    assert result.returncode == 1 # Exit code 1 when migrations needed
    assert "Need migration: 1" in result.stdout
    assert "legacy.md" in result.stdout

def test_schema_migrate_fails_on_duplicates(tmp_path):
    """VUL-03: schema-migrate command must fail on duplicate IDs."""
    (tmp_path / "doc1.md").write_text("---\nid: collision\ntype: atom\n---\n")
    (tmp_path / "doc2.md").write_text("---\nid: collision\ntype: atom\n---\n")
    
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "schema-migrate", "--check", "--dirs", str(tmp_path)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0
    assert "Duplicate ID 'collision' found" in result.stderr
