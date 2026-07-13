"""Parity tests for verify command."""

import json
import subprocess
import os
import sys
from pathlib import Path
from datetime import date

import pytest

from ontos.io.yaml import parse_frontmatter_content


@pytest.fixture
def golden_help():
    """Load golden help output."""
    golden_path = Path(__file__).parent / "golden" / "verify_help.txt"
    return golden_path.read_text()


def test_verify_help_parity(golden_help, assert_help_parity):
    """Native --help matches legacy."""
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "verify", "--help"],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    assert_help_parity(result.stdout, golden_help)
    assert "--all" in result.stdout
    assert "--date" in result.stdout
    assert "--portfolio" in result.stdout
    assert "verify" in result.stdout.lower()


def test_verify_single_file_parity(tmp_path):
    """Verify single file updates describes_verified."""
    (tmp_path / ".ontos").mkdir()
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
        [sys.executable, "-m", "ontos.cli", "verify", str(test_file)],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        cwd=tmp_path,
    )

    assert result.returncode == 0
    assert f"Updated describes_verified to {today}" in result.stdout or f"Verified {test_file}" in result.stdout
    
    # Check file content
    content = test_file.read_text()
    frontmatter, _ = parse_frontmatter_content(content)
    assert frontmatter["describes_verified"] == today

def test_verify_all_fails_on_duplicates(tmp_path):
    """VUL-03: verify --all command must fail on duplicate IDs."""
    (tmp_path / ".ontos").mkdir()
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "doc1.md").write_text("---\nid: collision\ntype: atom\n---\n")
    (docs_dir / "doc2.md").write_text("---\nid: collision\ntype: atom\n---\n")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    result = subprocess.run(
        # We use --all to trigger the scan that calls load_documents
        [sys.executable, "-m", "ontos.cli", "verify", "--all"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(tmp_path)
    )
    
    assert result.returncode != 0
    assert "Duplicate ID 'collision' found" in result.stderr


def test_verify_invalid_utf8_refuses_without_rewrite(tmp_path):
    (tmp_path / ".ontos").mkdir()
    target = tmp_path / "bad.md"
    original = (
        b"---\nid: bad_doc\ntype: atom\nstatus: active\n"
        b"describes: [something]\n---\n\ninvalid: \xff\n"
    )
    target.write_bytes(original)

    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "--json", "verify", str(target)],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2])},
        cwd=tmp_path,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "E_USER_INPUT"
    assert payload["result"]["exit_category"] == "usage"
    assert result.stderr == ""
    assert str(target) in payload["message"]
    assert "Re-save the file as UTF-8" in payload["message"]
    assert target.read_bytes() == original


def test_verify_json_invalid_date_is_one_usage_envelope(tmp_path):
    (tmp_path / ".ontos").mkdir()
    target = tmp_path / "doc.md"
    target.write_text(
        "---\nid: doc\ntype: atom\nstatus: active\ndescribes: [thing]\n---\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ontos.cli",
            "--json",
            "verify",
            str(target),
            "--date",
            "not-a-date",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2])},
        cwd=tmp_path,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == payload["exit_code"] == 2
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "E_USER_INPUT"
    assert payload["result"]["exit_category"] == "usage"
    assert result.stdout.count("\n") == 1
    assert result.stderr == ""


def test_verify_all_json_refuses_interactive_prompt_with_usage_envelope(tmp_path):
    (tmp_path / ".ontos").mkdir()

    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "--json", "verify", "--all"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2])},
        cwd=tmp_path,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == payload["exit_code"] == 2
    assert "interactive" in payload["message"]
    assert payload["result"]["exit_category"] == "usage"
    assert result.stdout.count("\n") == 1
    assert result.stderr == ""
