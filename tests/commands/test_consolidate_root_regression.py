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
        exit_code, _ = consolidate_module._run_consolidate_command(
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


def _write_user_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".ontos.toml").write_text(
        "[project]\nname = 'test'\n[paths]\ndocs_dir = 'docs'\nlogs_dir = 'docs/logs'\n",
        encoding="utf-8",
    )
    (project_root / "docs" / "logs").mkdir(parents=True)
    history_file = project_root / "docs" / "strategy" / "decision_history.md"
    history_file.parent.mkdir(parents=True)
    history_file.write_text(
        "# Decision History\n\n"
        "## History Ledger\n\n"
        "| Date | Slug | Event | Decision / Outcome | Impacts | Archive Path |\n"
        "|:---|:---|:---|:---|:---|:---|\n",
        encoding="utf-8",
    )
    return project_root


def test_consolidate_rejects_count_zero(tmp_path, monkeypatch):
    project_root = _write_user_project(tmp_path)
    monkeypatch.chdir(project_root)

    exit_code, message = consolidate_module._run_consolidate_command(
        consolidate_module.ConsolidateOptions(count=0, by_age=False, dry_run=True, all=True, quiet=True)
    )

    assert exit_code == 1
    assert "count must be >= 1" in message


def test_consolidate_append_failure_does_not_move_log(tmp_path, monkeypatch):
    project_root = _write_user_project(tmp_path)
    log_path = project_root / "docs" / "logs" / "2020-01-01-broken.md"
    log_path.write_text(
        "---\n"
        "id: log_broken\n"
        "type: log\n"
        "event_type: chore\n"
        "impacts: []\n"
        "---\n"
        "## Goal\n"
        "Broken\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(project_root)
    monkeypatch.setattr(consolidate_module, "append_to_decision_history", lambda *args, **kwargs: False)

    exit_code, message = consolidate_module._run_consolidate_command(
        consolidate_module.ConsolidateOptions(by_age=True, days=0, dry_run=False, all=True, quiet=True)
    )

    assert exit_code == 1
    assert "failures" in message
    assert log_path.exists()
    assert not (project_root / "docs" / "archive" / "logs" / log_path.name).exists()


def test_consolidate_commit_failure_reports_partial_results(tmp_path, monkeypatch):
    project_root = _write_user_project(tmp_path)
    (project_root / "docs" / "logs" / "2020-01-01-a.md").write_text(
        "---\nid: log_a\ntype: log\nevent_type: chore\nimpacts: []\n---\n## Goal\nA\n",
        encoding="utf-8",
    )
    (project_root / "docs" / "logs" / "2020-01-02-b.md").write_text(
        "---\nid: log_b\ntype: log\nevent_type: chore\nimpacts: []\n---\n## Goal\nB\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(project_root)
    original_commit = consolidate_module.SessionContext.commit
    commit_calls = {"count": 0}

    def _flaky_commit(self):
        commit_calls["count"] += 1
        if commit_calls["count"] == 1:
            raise RuntimeError("simulated commit failure")
        return original_commit(self)

    monkeypatch.setattr(consolidate_module.SessionContext, "commit", _flaky_commit)

    exit_code, message = consolidate_module._run_consolidate_command(
        consolidate_module.ConsolidateOptions(by_age=True, days=0, dry_run=False, all=True, quiet=True)
    )

    assert exit_code == 1
    assert "1 failures" in message
    archived_logs = list((project_root / "docs" / "archive" / "logs").glob("*.md"))
    remaining_logs = list((project_root / "docs" / "logs").glob("*.md"))
    assert len(archived_logs) == 1
    assert len(remaining_logs) == 1


def test_consolidate_normalizes_scalar_impacts(tmp_path, monkeypatch):
    project_root = _write_user_project(tmp_path)
    log_path = project_root / "docs" / "logs" / "2020-01-01-impacts.md"
    log_path.write_text(
        "---\n"
        "id: log_impacts\n"
        "type: log\n"
        "event_type: chore\n"
        "impacts: foo\n"
        "---\n"
        "## Goal\n"
        "Scalar impacts test\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(project_root)

    exit_code, _ = consolidate_module._run_consolidate_command(
        consolidate_module.ConsolidateOptions(by_age=True, days=0, dry_run=False, all=True, quiet=True)
    )

    history = (project_root / "docs" / "strategy" / "decision_history.md").read_text(encoding="utf-8")
    assert exit_code == 0
    assert "| foo |" in history
    assert "f, o, o" not in history
