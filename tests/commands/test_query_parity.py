"""Parity tests for query command."""
import sys

import subprocess
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import ontos.commands.query as query_module
from ontos.core.types import DocumentData, DocumentStatus, DocumentType


@pytest.fixture
def golden_help():
    """Load golden help output."""
    golden_path = Path(__file__).parent / "golden" / "query_help.txt"
    return golden_path.read_text()


def test_query_help_parity(golden_help, assert_help_parity):
    """Native --help matches legacy."""
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "query", "--help"],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    assert_help_parity(result.stdout, golden_help)
    assert "--depends-on" in result.stdout
    assert "--depended-by" in result.stdout
    assert "--health" in result.stdout
    assert "query" in result.stdout.lower()


def test_help_parity_normalizes_supported_argparse_presentation(assert_help_parity):
    """Supported Python versions may wrap usage and render aliases differently."""
    legacy = (
        "usage: ontos verify [-h] [--date DATE]\n"
        "                    [path]\n\n"
        "optional arguments:\n"
        "  --date DATE, -d DATE  Verification date\n"
    )
    canonical = (
        "usage: ontos verify [-h] [--date DATE] [path]\n\n"
        "options:\n"
        "  --date, -d DATE       Verification date\n"
    )
    assert_help_parity(legacy, canonical)


def test_query_health_parity(tmp_path):
    """Query health shows total documents."""
    # Create a couple of files
    (tmp_path / "kernel_doc.md").write_text("---\nid: kernel_doc\ntype: kernel\n---\n")
    (tmp_path / "atom_doc.md").write_text("---\nid: atom_doc\ntype: atom\ndepends_on: [kernel_doc]\n---\n")

    # Run native command
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "query", "--health", "--dir", str(tmp_path)],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )

    assert result.returncode == 0
    assert "Total documents: 2" in result.stdout
    assert "kernel: 1" in result.stdout
    assert "atom: 1" in result.stdout
    assert "Connectivity: 100.0% reachable from kernel" in result.stdout


def test_query_warns_on_duplicate_ids(tmp_path):
    """VUL-03: query command warns on duplicates but exits successfully (0)."""
    # Create two different files with same ID
    (tmp_path / "doc1.md").write_text("---\nid: same_id\ntype: atom\nstatus: active\n---\nDoc 1")
    (tmp_path / "doc2.md").write_text("---\nid: same_id\ntype: atom\nstatus: active\n---\nDoc 2")
    
    # Run native command
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "query", "--list-ids", "--dir", str(tmp_path)],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    
    assert result.returncode == 0
    assert "Duplicate ID 'same_id' found" in result.stderr or "Duplicate ID 'same_id' found" in result.stdout
    # Should still list the id once
    assert "same_id (atom)" in result.stdout


def test_native_query_stale_uses_git_timestamp(tmp_path, monkeypatch):
    path = tmp_path / "old.md"
    path.write_text("body", encoding="utf-8")
    doc = DocumentData(
        id="old_doc",
        type=DocumentType.ATOM,
        status=DocumentStatus.ACTIVE,
        filepath=path,
        frontmatter={"id": "old_doc", "type": "atom", "status": "active"},
        content="body",
    )
    monkeypatch.setattr(
        query_module,
        "get_git_last_modified",
        lambda *args, **kwargs: datetime.now() - timedelta(days=91),
    )
    assert query_module.query_stale({"old_doc": doc}, 30)[0][0] == "old_doc"
