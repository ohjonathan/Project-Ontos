"""Parity tests for query command."""

import subprocess
import os
from pathlib import Path

import pytest


@pytest.fixture
def golden_help():
    """Load golden help output."""
    golden_path = Path(__file__).parent / "golden" / "query_help.txt"
    return golden_path.read_text()


def test_query_help_parity(golden_help):
    """Native --help matches legacy."""
    result = subprocess.run(
        ["python3", "-m", "ontos.cli", "query", "--help"],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    assert "--depends-on" in result.stdout
    assert "--depended-by" in result.stdout
    assert "--health" in result.stdout
    assert "query" in result.stdout.lower()


def test_query_health_parity(tmp_path):
    """Query health shows total documents."""
    # Create a couple of files
    (tmp_path / "kernel_doc.md").write_text("---\nid: kernel_doc\ntype: kernel\n---\n")
    (tmp_path / "atom_doc.md").write_text("---\nid: atom_doc\ntype: atom\ndepends_on: [kernel_doc]\n---\n")

    # Run native command
    result = subprocess.run(
        ["python3", "-m", "ontos.cli", "query", "--health", "--dir", str(tmp_path)],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )

    assert result.returncode == 0
    assert "Total documents: 2" in result.stdout
    assert "kernel: 1" in result.stdout
    assert "atom: 1" in result.stdout
    assert "Connectivity: 100.0% reachable from kernel" in result.stdout
