import warnings

from ontos.core.proposals import find_draft_proposals, load_decision_history_entries


def test_load_decision_history_entries_uses_runtime_root(tmp_path, monkeypatch):
    project_root = tmp_path / "runtime_project"
    project_root.mkdir()
    (project_root / ".ontos.toml").write_text(
        "[project]\nname = 'test'\n[paths]\ndocs_dir = 'docs'\nlogs_dir = 'docs/logs'\n"
    )
    history_file = project_root / "docs" / "strategy" / "decision_history.md"
    history_file.parent.mkdir(parents=True)
    history_file.write_text(
        "# Decision History\n\n"
        "## History Ledger\n\n"
        "| Date | Slug | Event | Decision / Outcome | Impacts | Archive Path |\n"
        "|:---|:---|:---|:---|:---|:---|\n"
        "| 2026-01-01 | my_slug | chore | APPROVED proposal | none | `docs/archive/proposals/my.md` |\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(project_root)
    entries = load_decision_history_entries()

    assert "my_slug" in entries["slugs"]
    assert entries["archive_paths"]["docs/archive/proposals/my.md"] == "my_slug"
    assert "my_slug" in entries["approved_slugs"]


def test_find_draft_proposals_uses_runtime_root(tmp_path, monkeypatch):
    project_root = tmp_path / "runtime_project"
    project_root.mkdir()
    (project_root / ".ontos.toml").write_text(
        "[project]\nname = 'test'\n[paths]\ndocs_dir = 'docs'\nlogs_dir = 'docs/logs'\n"
    )
    proposal_file = project_root / "docs" / "strategy" / "proposals" / "v3.3" / "draft.md"
    proposal_file.parent.mkdir(parents=True)
    proposal_file.write_text(
        "---\n"
        "id: draft_proposal_test\n"
        "type: strategy\n"
        "status: draft\n"
        "---\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(project_root)
    proposals = find_draft_proposals()

    assert any(p["id"] == "draft_proposal_test" for p in proposals)
    assert any("runtime_project" in p["filepath"] for p in proposals)


def test_load_decision_history_entries_warns_on_legacy_layout(tmp_path, monkeypatch):
    project_root = tmp_path / "legacy_project"
    project_root.mkdir()
    (project_root / ".ontos.toml").write_text(
        "[project]\nname = 'test'\n[paths]\ndocs_dir = 'docs'\nlogs_dir = 'docs/logs'\n"
    )
    legacy_history = project_root / "docs" / "decision_history.md"
    legacy_history.parent.mkdir(parents=True)
    legacy_history.write_text(
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
        load_decision_history_entries()

    warning_messages = [str(w.message) for w in caught]
    assert any("deprecated path 'docs/decision_history.md'" in m for m in warning_messages)
