"""Parity tests for stub command."""

import subprocess
import os
from pathlib import Path

import pytest


def test_stub_help_parity():
    """Native --help matches legacy."""
    result = subprocess.run(
        ["python3", "-m", "ontos.cli", "stub", "--help"],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    assert "--goal" in result.stdout
    assert "--type" in result.stdout
    assert "--output" in result.stdout
    assert "stub" in result.stdout.lower()


def test_stub_file_creation_parity(tmp_path):
    """Stub command creates file with correct frontmatter."""
    output_file = tmp_path / "test_stub.md"
    
    # Run native command
    result = subprocess.run(
        ["python3", "-m", "ontos.cli", "stub", 
         "--id", "test_stub", 
         "--type", "atom", 
         "--goal", "Test Goal",
         "--output", str(output_file)],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )

    assert result.returncode == 0
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "id: test_stub" in content
    assert "type: atom" in content
    assert "status: pending_curation" in content
    assert "curation_level: 1" in content
    assert "goal: Test Goal" in content
    assert "# Test Stub" in content
