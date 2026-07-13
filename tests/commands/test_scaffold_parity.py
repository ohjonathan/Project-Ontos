"""Parity tests for scaffold command."""
import json
import sys

import subprocess
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


def _init_scaffold_workspace(root: Path) -> None:
    (root / ".ontos.toml").write_text(
        "[ontos]\nversion = '5.0.0'\n",
        encoding="utf-8",
    )
    (root / "docs").mkdir()


@pytest.fixture
def golden_help():
    """Load golden help output."""
    golden_path = Path(__file__).parent / "golden" / "scaffold_help.txt"
    return golden_path.read_text()


def test_scaffold_help_parity(golden_help, assert_help_parity):
    """Native --help matches legacy."""
    # Run the native command through the main entry point
    # We use 'python3 -m ontos.cli' to ensure we run the package code
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "scaffold", "--help"],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    assert_help_parity(result.stdout, golden_help)
    # Compare key elements (flags, descriptions)
    # The wording might be slightly different in the new implementation (help vs title)
    # but the functional coverage should be the same.
    assert "--apply" in result.stdout
    assert "--dry-run" in result.stdout
    assert "frontmatter" in result.stdout.lower()


def test_scaffold_dry_run_parity(tmp_path):
    """Dry-run output matches legacy format."""
    # Create test file without frontmatter
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test\n\nContent here.")

    # Run native command
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "scaffold", str(test_file), "--dry-run"],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )

    assert result.returncode == 0
    assert result.returncode == 0
    # Legacy format check
    assert "id: test" in result.stdout
    assert "status: scaffold" in result.stdout


def test_scaffold_tolerates_duplicate_ids(tmp_path):
    """OBS-03: Scaffold should continue despite duplicate IDs."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "a.md").write_text("---\nid: collision\ntype: atom\n---\n")
    (docs_dir / "b.md").write_text("---\nid: collision\ntype: atom\n---\n")
    (docs_dir / "untagged.md").write_text("# No frontmatter\nJust content")

    # scaffold should still find untagged.md despite the duplicate collision
    from ontos.commands.scaffold import find_untagged_files
    untagged = find_untagged_files(paths=[docs_dir], root=tmp_path)
    
    assert any("untagged.md" in str(p) for p in untagged)


def test_scaffold_missing_user_path_returns_usage(tmp_path: Path) -> None:
    from ontos.commands.scaffold import ScaffoldOptions, _run_scaffold_command

    _init_scaffold_workspace(tmp_path)
    options = ScaffoldOptions(
        paths=[Path("missing.md")],
        repo_root=tmp_path,
        quiet=True,
    )

    exit_code, message = _run_scaffold_command(options)

    assert exit_code == 2
    assert message == "Scaffold discovery failed"
    assert len(options.runtime_failures) == 1
    assert "missing.md" in options.runtime_failures[0]


def test_scaffold_parse_failure_returns_usage(tmp_path: Path) -> None:
    from ontos.commands.scaffold import ScaffoldOptions, _run_scaffold_command

    _init_scaffold_workspace(tmp_path)
    invalid = tmp_path / "docs" / "invalid.md"
    invalid.write_bytes(b"---\nid: \xff\n---\n")
    options = ScaffoldOptions(
        paths=[invalid],
        repo_root=tmp_path,
        quiet=True,
    )

    exit_code, _ = _run_scaffold_command(options)

    assert exit_code == 2
    assert options.runtime_failures


def test_scaffold_discovery_io_failure_returns_internal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ontos.commands.scaffold import ScaffoldOptions, _run_scaffold_command
    from ontos.io.files import DocumentLoadIssue, DocumentLoadResult

    _init_scaffold_workspace(tmp_path)
    document = tmp_path / "docs" / "doc.md"
    document.write_text("# Document\n", encoding="utf-8")
    monkeypatch.setattr(
        "ontos.commands.scaffold.load_documents",
        lambda *_args, **_kwargs: DocumentLoadResult(
            documents={},
            issues=[
                DocumentLoadIssue(
                    code="io_error",
                    path=document,
                    message="disk read failed",
                )
            ],
            duplicate_ids={},
        ),
    )
    options = ScaffoldOptions(
        paths=[document],
        repo_root=tmp_path,
        quiet=True,
    )

    exit_code, _ = _run_scaffold_command(options)

    assert exit_code == 5
    assert options.runtime_failures
    assert "disk read failed" in options.runtime_failures[0]


def test_scaffold_usage_json_has_one_error_envelope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from ontos.cli import _cmd_scaffold

    _init_scaffold_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    args = SimpleNamespace(
        paths=[Path("missing.md")],
        apply=False,
        dry_run=True,
        quiet=False,
        json=True,
        scope=None,
    )

    exit_code = _cmd_scaffold(args)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out.count("\n") == 1
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["status"] == "error"
    assert payload["exit_code"] == 2
    assert payload["error"]["code"] == "E_USER_INPUT"
    assert payload["result"]["exit_category"] == "usage"


def test_scaffold_commit_failure_json_is_internal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from ontos.cli import _cmd_scaffold
    from ontos.core.context import SessionContext

    _init_scaffold_workspace(tmp_path)
    document = tmp_path / "docs" / "doc.md"
    document.write_text("# Document\n", encoding="utf-8")
    original = document.read_bytes()
    monkeypatch.chdir(tmp_path)

    def fail_commit(_self) -> None:
        raise OSError("disk unavailable")

    monkeypatch.setattr(SessionContext, "commit", fail_commit)
    args = SimpleNamespace(
        paths=[document],
        apply=True,
        dry_run=False,
        quiet=False,
        json=True,
        scope=None,
    )

    exit_code = _cmd_scaffold(args)

    captured = capsys.readouterr()
    assert exit_code == 5
    assert captured.out.count("\n") == 1
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["status"] == "error"
    assert payload["exit_code"] == 5
    assert payload["error"]["code"] == "E_COMMAND_FAILED"
    assert payload["result"]["exit_category"] == "internal"
    assert "commit: disk unavailable" in payload["data"]["failures"]
    assert document.read_bytes() == original
