"""Parity tests for promote command."""
import sys

import subprocess
import os
from pathlib import Path

import pytest


def test_promote_help_parity():
    """Native --help matches legacy."""
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "promote", "--help"],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    assert "--check" in result.stdout
    assert "--all-ready" in result.stdout
    assert "promote" in result.stdout.lower()


def test_promote_check_parity(tmp_path):
    """Promote check identifies L0/L1 documents."""
    # Initialize mock repo
    (tmp_path / ".ontos").mkdir()
    l0_file = tmp_path / "scaffold.md"
    l0_file.write_text("---\nid: scaffold_doc\ntype: atom\nstatus: scaffold\ncuration_level: 0\nontos_schema: '2.2'\n---\n")

    # Run native command
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() # Project root
    
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "promote", "--check"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(tmp_path)
    )

    assert result.returncode == 0
    assert "Found 1 document" in result.stdout
    assert "scaffold_doc" in result.stdout
    assert "[L0]" in result.stdout

def test_promote_fails_on_duplicates(tmp_path):
    """VUL-03: promote command must fail on duplicate IDs."""
    (tmp_path / ".ontos").mkdir()
    (tmp_path / "doc1.md").write_text("---\nid: collision\ntype: atom\n---\n")
    (tmp_path / "doc2.md").write_text("---\nid: collision\ntype: atom\n---\n")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "promote", "--check"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(tmp_path)
    )
    
    assert result.returncode != 0
    assert "Duplicate ID 'collision' found" in result.stderr
