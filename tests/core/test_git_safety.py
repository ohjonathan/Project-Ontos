from __future__ import annotations

from subprocess import CompletedProcess

from ontos.core import git as git_core


def test_rollback_never_unlinks_tracked_path_when_checkout_fails(tmp_path, monkeypatch) -> None:
    target = tmp_path / "tracked.md"
    target.write_text("user content", encoding="utf-8")

    def fake_run(argv, **kwargs):
        if argv[1] == "ls-files":
            return CompletedProcess(argv, 0, stdout="tracked.md\n", stderr="")
        return CompletedProcess(argv, 128, stdout="", stderr="unrelated git failure")

    monkeypatch.setattr(git_core.subprocess, "run", fake_run)
    assert git_core.rollback_path(tmp_path, target) == "unrelated git failure"
    assert target.read_text(encoding="utf-8") == "user content"


def test_rollback_unlinks_only_proven_untracked_file(tmp_path, monkeypatch) -> None:
    target = tmp_path / "new.md"
    target.write_text("partial", encoding="utf-8")
    monkeypatch.setattr(
        git_core.subprocess,
        "run",
        lambda argv, **kwargs: CompletedProcess(argv, 1, stdout="", stderr="no match"),
    )
    assert git_core.rollback_path(tmp_path, target) is None
    assert not target.exists()


def test_workspace_clean_fails_closed_when_git_is_unavailable(tmp_path, monkeypatch) -> None:
    def missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(git_core.subprocess, "run", missing)
    clean, reason = git_core.is_workspace_clean(tmp_path)
    assert clean is False
    assert "not found" in (reason or "")
