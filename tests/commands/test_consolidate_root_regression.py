import subprocess
import sys
import os
from pathlib import Path

def test_consolidate_runtime_root_resolution(tmp_path):
    """Regression test: consolidate must use runtime project root, not package root."""
    # Setup temp project
    project_root = tmp_path / "my_project"
    project_root.mkdir()
    # Create .ontos.toml to mark as project root
    (project_root / ".ontos.toml").write_text("[project]\nname = 'test'\n[paths]\ndocs_dir = 'docs'\nlogs_dir = 'docs/logs'\n")
    
    # Create logs
    logs_dir = project_root / "docs" / "logs"
    logs_dir.mkdir(parents=True)
    (logs_dir / "2020-01-01-test.md").write_text(
        "---\n"
        "id: log_test\n"
        "type: log\n"
        "event_type: chore\n"
        "impacts: []\n"
        "---\n"
        "## Goal\n"
        "Test log content\n",
        encoding="utf-8",
    )
    
    # Create decision history in the local project
    strategy_dir = project_root / "docs" / "strategy"
    strategy_dir.mkdir(parents=True)
    history_file = strategy_dir / "decision_history.md"
    history_file.write_text(
        "# Decision History\n\n"
        "## History Ledger\n\n"
        "| Date | Slug | Event | Decision / Outcome | Impacts | Archive Path |\n"
        "|:---|:---|:---|:---|:---|:---|\n",
        encoding="utf-8",
    )

    # Run command via subprocess to ensure it discovers project_root at runtime
    # and doesn't rely on package-anchored PROJECT_ROOT for the command logic.
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() # Ensure ontos package is findable
    
    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "consolidate", "--dry-run", "--all", "--by-age", "--days", "0"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        env=env
    )

    # Verification
    assert result.returncode == 0
    assert "log_test" in result.stdout
    assert "Would consolidate 1 log(s)" in result.stdout
    # Ensure it didn't crash searching for logs in the package root
    assert "Document load failed" not in result.stderr
