"""Parity tests for promote command."""
import json
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
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    l0_file = docs_dir / "scaffold.md"
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
    assert "Found 1 candidate" in result.stdout
    assert "scaffold_doc" in result.stdout
    assert "[L0]" in result.stdout

def test_promote_fails_on_duplicates(tmp_path):
    """VUL-03: promote command must fail on duplicate IDs."""
    (tmp_path / ".ontos").mkdir()
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "doc1.md").write_text("---\nid: collision\ntype: atom\n---\n")
    (docs_dir / "doc2.md").write_text("---\nid: collision\ntype: atom\n---\n")
    
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


def test_promote_invalid_utf8_refuses_without_rewrite(tmp_path):
    (tmp_path / ".ontos").mkdir()
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    target = docs_dir / "bad.md"
    original = (
        b"---\nid: bad_doc\ntype: atom\nstatus: scaffold\n"
        b"curation_level: 0\n---\n\ninvalid: \xff\n"
    )
    target.write_bytes(original)

    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "--json", "promote", "--all-ready"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": os.getcwd()},
        cwd=tmp_path,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "E_COMMAND_FAILED"
    assert str(target) in payload["message"]
    assert "Re-save the file as UTF-8" in payload["message"]
    assert target.read_bytes() == original


def test_promote_updates_quoted_curation_key_without_duplicate(tmp_path):
    (tmp_path / ".ontos").mkdir()
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    target = docs_dir / "quoted.md"
    target.write_text(
        "---\n"
        "id: quoted_promotion\n"
        "type: atom\n"
        "status: scaffold\n"
        "'curation_level': 0\n"
        "ontos_schema: '2.2'\n"
        "---\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "promote", "--all-ready"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": os.getcwd()},
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    updated = target.read_text(encoding="utf-8")
    assert "'curation_level': 0" not in updated
    assert updated.count("curation_level:") == 1
