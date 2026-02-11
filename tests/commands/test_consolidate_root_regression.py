import subprocess
import sys
import os
import warnings
from pathlib import Path
from ontos.commands import consolidate as consolidate_module

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


def test_consolidate_non_dry_run_updates_history_and_archives(tmp_path):
    """Regression test: non-dry-run consolidate should archive and update history."""
    project_root = tmp_path / "my_project"
    project_root.mkdir()
    (project_root / ".ontos.toml").write_text(
        "[project]\nname = 'test'\n[paths]\ndocs_dir = 'docs'\nlogs_dir = 'docs/logs'\n"
    )

    logs_dir = project_root / "docs" / "logs"
    logs_dir.mkdir(parents=True)
    original_log = logs_dir / "2020-01-01-test.md"
    original_log.write_text(
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

    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    result = subprocess.run(
        [sys.executable, "-m", "ontos.cli", "consolidate", "--all", "--by-age", "--days", "0"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        env=env,
    )

    archived_log = project_root / "docs" / "archive" / "logs" / "2020-01-01-test.md"
    assert result.returncode == 0
    assert "Consolidated 1 log(s)." in result.stdout
    assert archived_log.exists()
    assert not original_log.exists()
    assert (
        "| 2020-01-01 | test | chore | Test log content | — | `docs/archive/logs/2020-01-01-test.md` |"
        in history_file.read_text(encoding="utf-8")
    )
    assert "Error archiving" not in result.stderr


def test_consolidate_warns_on_legacy_user_layout_fallbacks(tmp_path, monkeypatch):
    """Consolidate should warn when falling back to pre-v2.5.2 user layouts."""
    project_root = tmp_path / "legacy_project"
    project_root.mkdir()
    (project_root / ".ontos.toml").write_text(
        "[project]\nname = 'test'\n[paths]\ndocs_dir = 'docs'\nlogs_dir = 'docs/logs'\n"
    )

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

    # Legacy layouts present, new layouts absent.
    (project_root / "docs" / "archive").mkdir(parents=True)
    (project_root / "docs" / "decision_history.md").write_text(
        "# Decision History\n\n"
        "## History Ledger\n\n"
        "| Date | Slug | Event | Decision / Outcome | Impacts | Archive Path |\n"
        "|:---|:---|:---|:---|:---|:---|\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(project_root)
    from ontos.core import paths as paths_module
    paths_module._deprecation_warned.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exit_code, _ = consolidate_module.consolidate_command(
            consolidate_module.ConsolidateOptions(
                by_age=True,
                days=0,
                dry_run=True,
                all=True,
                quiet=True,
            )
        )

    warning_messages = [str(w.message) for w in caught]
    assert exit_code == 0
    assert any("deprecated path 'docs/archive/'" in m for m in warning_messages)
    assert any("deprecated path 'docs/decision_history.md'" in m for m in warning_messages)
