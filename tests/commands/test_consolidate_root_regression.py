"""Regression test for consolidate root initialization."""

from ontos.commands import consolidate as consolidate_module


def test_consolidate_dry_run_with_logs_does_not_raise_name_error(tmp_path, monkeypatch):
    """consolidate_command should define root before SessionContext.from_repo(root)."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".ontos").mkdir()

    logs_dir = project_root / "logs"
    logs_dir.mkdir()
    (logs_dir / "2020-01-01-test.md").write_text(
        "---\n"
        "id: log_test\n"
        "event_type: chore\n"
        "impacts: []\n"
        "---\n"
        "## Goal\n"
        "Test log\n",
        encoding="utf-8",
    )

    archive_dir = project_root / "archive"
    history_file = project_root / "decision_history.md"
    history_file.write_text(
        "# Decision History\n\n"
        "## History Ledger\n\n"
        "| Date | Slug | Event | Decision / Outcome | Impacts | Archive Path |\n"
        "|:---|:---|:---|:---|:---|:---|\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(project_root)
    monkeypatch.setattr(consolidate_module, "get_logs_dir", lambda: str(logs_dir))
    monkeypatch.setattr(consolidate_module, "get_archive_logs_dir", lambda: str(archive_dir))
    monkeypatch.setattr(consolidate_module, "get_decision_history_path", lambda: str(history_file))

    exit_code, _ = consolidate_module.consolidate_command(
        consolidate_module.ConsolidateOptions(
            by_age=True,
            days=0,
            dry_run=True,
            all=True,
            quiet=True,
        )
    )

    assert exit_code == 0
