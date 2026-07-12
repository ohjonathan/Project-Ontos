from __future__ import annotations

from subprocess import CompletedProcess

from ontos.core.suggestions import suggest_impacts
from ontos.io import git as git_io


def test_empty_git_diffs_return_no_sentinel_path(monkeypatch) -> None:
    monkeypatch.setattr(
        git_io.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(args[0], 0, stdout="", stderr=""),
    )
    assert git_io.get_changed_files_since_push() == []


def test_empty_commit_history_returns_no_empty_message(monkeypatch) -> None:
    monkeypatch.setattr(
        git_io.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(args[0], 0, stdout="", stderr=""),
    )
    assert git_io.get_commits_since_push() == []


def test_empty_change_set_does_not_suggest_every_document() -> None:
    index = {"docs/alpha.md": "alpha_doc", "docs/beta.md": "beta_doc"}
    assert suggest_impacts([], index, []) == []
