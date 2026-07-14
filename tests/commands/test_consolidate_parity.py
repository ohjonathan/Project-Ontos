"""Parity tests for consolidate command."""

import subprocess
import os
import sys
from pathlib import Path

import pytest


@pytest.fixture
def test_setup(tmp_path):
    """Setup test environment with decision_history.md."""
    history_dir = tmp_path / "strategy"
    history_dir.mkdir()
    history_file = history_dir / "decision_history.md"
    history_file.write_text("# Decision History\n\n## History Ledger\n\n| Date | Slug | Event | Decision / Outcome | Impacts | Archive Path |\n|:---|:---|:---|:---|:---|:---|\n")
    
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    return tmp_path


def test_consolidate_count_parity(test_setup):
    """Consolidation moves logs and updates history."""
    tmp_path = test_setup
    logs_dir = tmp_path / "logs"
    history_file = tmp_path / "strategy" / "decision_history.md"
    
    # Create 3 logs
    for i in range(1, 4):
        f = logs_dir / f"2023-01-0{i}-test.md"
        f.write_text(f"""---
id: test_{i}
event_type: feature
impacts: [doc_{i}]
---
## Goal
Test log {i}
""")

    # The command needs a project marker before it resolves the root.
    (tmp_path / ".ontos").mkdir()
    (tmp_path / ".ontos.toml").write_text(
        "[ontos]\nversion='3.0'\n[paths]\ndocs_dir='.'\nlogs_dir='logs'\n",
        encoding="utf-8",
    )

    # Run native command, keeping only the newest log.
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "consolidate", "--count", "1", "--all"],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        cwd=str(tmp_path)
    )

    assert result.returncode == 0, result.stderr
    assert "Consolidated 2 log(s)" in result.stdout
    assert len(list(logs_dir.glob("*.md"))) == 1
    assert len(list((tmp_path / "archive" / "logs").glob("*.md"))) == 2
    history = history_file.read_text(encoding="utf-8")
    assert "| 2023-01-01 | test | feature | Test log 1" in history
    assert "| 2023-01-02 | test | feature | Test log 2" in history

def test_consolidate_fails_on_duplicates(test_setup):
    """VUL-03: consolidate command must fail on duplicate IDs."""
    tmp_path = test_setup
    logs_dir = tmp_path / "docs" / "logs"
    logs_dir.mkdir(parents=True)
    (tmp_path / ".ontos").mkdir()
    
    # Create two different files with same ID in logs dir
    (logs_dir / "2023-01-01-doc1.md").write_text("---\nid: collision\ntype: log\n---\n## Goal\nTest 1")
    (logs_dir / "2023-01-01-doc2.md").write_text("---\nid: collision\ntype: log\n---\n## Goal\nTest 2")

    # Ensure command resolves logs against this temp project.
    (tmp_path / "ontos_config.py").write_text(f'LOGS_DIR = r"{logs_dir}"\n', encoding="utf-8")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{tmp_path}:{os.getcwd()}"
    
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "consolidate", "--all"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(tmp_path)
    )
    
    assert result.returncode != 0
    assert "Duplicate ID 'collision' found" in result.stderr
