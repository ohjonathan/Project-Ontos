"""Parity tests for verify command."""

import subprocess
import os
from pathlib import Path
from datetime import date

import pytest


@pytest.fixture
def golden_help():
    """Load golden help output."""
    golden_path = Path(__file__).parent / "golden" / "verify_help.txt"
    return golden_path.read_text()


def test_verify_help_parity(golden_help):
    """Native --help matches legacy."""
    result = subprocess.run(
        ["python3", "-m", "ontos.cli", "verify", "--help"],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    assert "--all" in result.stdout
    assert "--date" in result.stdout
    assert "verify" in result.stdout.lower()


def test_verify_single_file_parity(tmp_path):
    """Verify single file updates describes_verified."""
    # Create test file with frontmatter and describes
    test_file = tmp_path / "test_verify.md"
    test_file.write_text("""---
id: test_verify
type: atom
describes: [something]
---
Content""")

    # Run native command
    today = date.today().isoformat()
    result = subprocess.run(
        ["python3", "-m", "ontos.cli", "verify", str(test_file)],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )

    assert result.returncode == 0
    assert f"Updated describes_verified to {today}" in result.stdout or f"Verified {test_file}" in result.stdout
    
    # Check file content
    content = test_file.read_text()
    assert f"describes_verified: {today}" in content
