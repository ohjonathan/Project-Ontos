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


def test_migrate_mode_guard_rejects_missing_mode(tmp_path, monkeypatch):
    from ontos.commands.migrate import MigrateOptions, migrate_command

    (tmp_path / ".ontos").mkdir()
    (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code, message = migrate_command(MigrateOptions())

    assert exit_code == 1
    assert "Select exactly one mode" in message


def test_migrate_mode_guard_rejects_conflicting_mode(tmp_path, monkeypatch):
    from ontos.commands.migrate import MigrateOptions, migrate_command

    (tmp_path / ".ontos").mkdir()
    (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code, message = migrate_command(MigrateOptions(check=True, apply=True))

    assert exit_code == 1
    assert "Select exactly one mode" in message or "cannot be combined" in message


def test_schema_migrate_check_reports_unsupported_schema(tmp_path):
    (tmp_path / ".ontos").mkdir()
    (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'\n", encoding="utf-8")
    unsupported_file = tmp_path / "unsupported.md"
    unsupported_file.write_text(
        "---\nid: unsupported_doc\ntype: atom\nstatus: active\nontos_schema: 99.0\n---\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "schema-migrate", "--check", "--dirs", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert "unsupported schema" in result.stdout.lower()
    assert "unsupported.md" in result.stdout
    assert "99.0" in result.stdout


def test_schema_migrate_apply_nonzero_with_unsupported_schema(tmp_path):
    (tmp_path / ".ontos").mkdir()
    (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'\n", encoding="utf-8")
    (tmp_path / "unsupported.md").write_text(
        "---\nid: unsupported_doc\ntype: atom\nstatus: active\nontos_schema: 99.0\n---\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "schema-migrate", "--apply", "--dirs", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert result.returncode == 1
    combined = f"{result.stdout}\n{result.stderr}".lower()
    assert "unsupported schema" in combined
