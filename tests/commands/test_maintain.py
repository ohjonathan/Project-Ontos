"""Tests for registry-based maintain command."""

import json
import os
import subprocess
import sys
import warnings
from types import SimpleNamespace
from pathlib import Path

from ontos.commands.maintain import (
    MaintainContext,
    MaintainOptions,
    MaintainTask,
    MaintainTaskRegistry,
    TaskResult,
    _condition_agents_stale,
    _condition_auto_consolidate,
    _parse_bool,
    _scan_docs,
    _task_check_links,
    _task_curation_stats,
    _task_promote_check,
    _task_review_proposals,
    list_registered_tasks,
    maintain_command,
)
from ontos.io.config import load_project_config
from ontos.ui.output import OutputHandler


def _init_project(tmp_path: Path) -> None:
    (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'\n", encoding="utf-8")
    (tmp_path / "docs").mkdir(exist_ok=True)


def _build_context(tmp_path: Path, **option_overrides) -> MaintainContext:
    options = MaintainOptions(**option_overrides)
    config = load_project_config(config_path=tmp_path / ".ontos.toml", repo_root=tmp_path)
    return MaintainContext(
        repo_root=tmp_path,
        config=config,
        options=options,
        output=OutputHandler(quiet=True),
    )


def test_maintain_help_contains_flags():
    result = subprocess.run(
        [sys.executable, "-m", "ontos", "maintain", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--dry-run" in result.stdout
    assert "--skip" in result.stdout
    assert "--verbose" in result.stdout


def test_default_registry_has_expected_order():
    assert list_registered_tasks() == [
        "migrate_untagged",
        "regenerate_map",
        "health_check",
        "curation_stats",
        "promote_check",
        "consolidate_logs",
        "review_proposals",
        "check_links",
        "sync_agents",
    ]


def test_maintain_skip_excludes_task(tmp_path, monkeypatch):
    _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    executed = []
    registry = MaintainTaskRegistry()
    registry.register(
        MaintainTask(
            name="first",
            order=10,
            description="first",
            run=lambda _ctx: executed.append("first") or TaskResult("success", "ok"),
        )
    )
    registry.register(
        MaintainTask(
            name="second",
            order=20,
            description="second",
            run=lambda _ctx: executed.append("second") or TaskResult("success", "ok"),
        )
    )

    exit_code = maintain_command(
        MaintainOptions(skip=["first"], quiet=True),
        registry=registry,
    )

    assert exit_code == 0
    assert executed == ["second"]


def test_maintain_error_isolation_runs_remaining_tasks(tmp_path, monkeypatch):
    _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    executed = []
    registry = MaintainTaskRegistry()
    registry.register(
        MaintainTask(
            name="fail_fast",
            order=10,
            description="fail",
            run=lambda _ctx: TaskResult("failed", "boom"),
        )
    )
    registry.register(
        MaintainTask(
            name="still_runs",
            order=20,
            description="runs",
            run=lambda _ctx: executed.append("still_runs") or TaskResult("success", "ok"),
        )
    )

    exit_code = maintain_command(MaintainOptions(quiet=True), registry=registry)

    assert exit_code == 1
    assert executed == ["still_runs"]


def test_maintain_exception_isolation_runs_remaining_tasks(tmp_path, monkeypatch):
    _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    executed = []
    registry = MaintainTaskRegistry()

    def _boom(_ctx):
        raise RuntimeError("unexpected")

    registry.register(
        MaintainTask(
            name="explode",
            order=10,
            description="explode",
            run=_boom,
        )
    )
    registry.register(
        MaintainTask(
            name="still_runs",
            order=20,
            description="runs",
            run=lambda _ctx: executed.append("still_runs") or TaskResult("success", "ok"),
        )
    )

    exit_code = maintain_command(MaintainOptions(quiet=True), registry=registry)

    assert exit_code == 1
    assert executed == ["still_runs"]


def test_auto_consolidate_condition_respects_env(tmp_path, monkeypatch):
    _init_project(tmp_path)
    ctx = _build_context(tmp_path)

    monkeypatch.setenv("AUTO_CONSOLIDATE", "false")
    should_run, reason = _condition_auto_consolidate(ctx)
    assert should_run is False
    assert "disabled" in reason.lower()

    monkeypatch.setenv("AUTO_CONSOLIDATE", "true")
    should_run, _ = _condition_auto_consolidate(ctx)
    assert should_run is True


def test_agents_staleness_condition_only_runs_when_stale(tmp_path, monkeypatch):
    _init_project(tmp_path)
    ctx = _build_context(tmp_path)
    agents_path = tmp_path / "AGENTS.md"
    map_path = tmp_path / "Ontos_Context_Map.md"
    logs_dir = tmp_path / "docs" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    agents_path.write_text("# agents", encoding="utf-8")
    map_path.write_text("# map", encoding="utf-8")
    log_path = logs_dir / "2026-02-10_test.md"
    log_path.write_text("# log", encoding="utf-8")

    os.utime(agents_path, (100, 100))
    os.utime(map_path, (200, 200))
    os.utime(log_path, (150, 150))
    os.utime(tmp_path / ".ontos.toml", (120, 120))
    should_run, reason = _condition_agents_stale(ctx)
    assert should_run is True
    assert "stale" in reason.lower()

    os.utime(agents_path, (300, 300))
    should_run, reason = _condition_agents_stale(ctx)
    assert should_run is False
    assert "up to date" in reason.lower()


def test_check_links_task_reports_broken_dependencies(tmp_path):
    _init_project(tmp_path)
    docs = tmp_path / "docs"
    (docs / "a.md").write_text(
        "---\nid: a\ntype: atom\nstatus: active\ndepends_on: [missing_doc]\n---\n",
        encoding="utf-8",
    )

    ctx = _build_context(tmp_path, quiet=True)
    result = _task_check_links(ctx)

    assert result.status == "failed"
    assert result.metrics["broken_links"] == 1
    assert "broken references" in result.message.lower()


def test_check_links_task_uses_shared_link_diagnostics(tmp_path, monkeypatch):
    _init_project(tmp_path)
    (tmp_path / "docs" / "a.md").write_text("---\nid: a\ntype: atom\nstatus: active\n---\n", encoding="utf-8")
    ctx = _build_context(tmp_path, quiet=True)
    observed = {}

    def _fake_run_link_diagnostics(**kwargs):
        observed.update(kwargs)
        return SimpleNamespace(
            exit_code=0,
            load_warnings=[],
            broken_references=[],
            duplicates={},
            external_references=[],
            parse_failed_candidates=[],
            orphans=[],
            summary=SimpleNamespace(
                broken_references=0,
                orphans=0,
                external_references=0,
                duplicate_ids=0,
                load_warnings=0,
            ),
        )

    monkeypatch.setattr("ontos.commands.maintain.run_link_diagnostics", _fake_run_link_diagnostics)
    result = _task_check_links(ctx)

    assert result.status == "success"
    assert observed["include_body"] is False
    assert observed["include_external_scope_resolution"] is True


def test_maintain_scan_docs_default_scope_excludes_internal(tmp_path):
    _init_project(tmp_path)
    (tmp_path / "docs" / "a.md").write_text("---\nid: docs_only\ntype: atom\nstatus: active\n---\n")
    (tmp_path / ".ontos-internal").mkdir()
    (tmp_path / ".ontos-internal" / "b.md").write_text("---\nid: internal_only\ntype: atom\nstatus: active\n---\n")

    ctx = _build_context(tmp_path, quiet=True)
    paths = _scan_docs(ctx)

    names = {p.name for p in paths}
    assert "a.md" in names
    assert "b.md" not in names


def test_maintain_scan_docs_library_scope_includes_internal(tmp_path):
    _init_project(tmp_path)
    (tmp_path / "docs" / "a.md").write_text("---\nid: docs_only\ntype: atom\nstatus: active\n---\n")
    (tmp_path / ".ontos-internal").mkdir()
    (tmp_path / ".ontos-internal" / "b.md").write_text("---\nid: internal_only\ntype: atom\nstatus: active\n---\n")

    ctx = _build_context(tmp_path, quiet=True, scope="library")
    paths = _scan_docs(ctx)

    names = {p.name for p in paths}
    assert "a.md" in names
    assert "b.md" in names


def test_curation_stats_task_counts_l0_l1_l2(tmp_path):
    _init_project(tmp_path)
    docs = tmp_path / "docs"
    (docs / "untagged.md").write_text("# no frontmatter\n", encoding="utf-8")
    (docs / "stub.md").write_text(
        "---\nid: stub\ntype: atom\nstatus: pending_curation\n---\n",
        encoding="utf-8",
    )
    (docs / "full.md").write_text(
        "---\nid: full\ntype: atom\nstatus: active\ndepends_on: [stub]\n---\n",
        encoding="utf-8",
    )

    ctx = _build_context(tmp_path, quiet=True)
    result = _task_curation_stats(ctx)

    assert result.status == "success"
    assert result.metrics["l0"] == 1
    assert result.metrics["l1"] == 1
    assert result.metrics["l2"] == 1
    assert result.metrics["total"] == 3


def test_curation_stats_dry_run_skips_disk_scan(tmp_path, monkeypatch):
    _init_project(tmp_path)
    ctx = _build_context(tmp_path, quiet=True, dry_run=True)

    def _should_not_scan(_ctx):
        raise AssertionError("dry-run should not scan documents")

    monkeypatch.setattr("ontos.commands.maintain._scan_docs", _should_not_scan)
    result = _task_curation_stats(ctx)

    assert result.status == "success"
    assert "would report" in result.message.lower()


def test_review_proposals_reports_without_prompting(tmp_path, monkeypatch):
    _init_project(tmp_path)
    proposal_dir = tmp_path / ".ontos-internal" / "strategy" / "proposals" / "v3.2.2"
    proposal_dir.mkdir(parents=True, exist_ok=True)
    (proposal_dir / "sample.md").write_text(
        "---\nid: v3_2_2_sample\nstatus: draft\ntype: strategy\n---\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("input() should not be called")),
    )

    ctx = _build_context(tmp_path, quiet=True, dry_run=False)
    result = _task_review_proposals(ctx)

    assert result.status == "success"
    assert result.metrics["draft_proposals"] == 1
    assert "manually" in result.message.lower()


def test_maintain_json_reports_skipped_tasks(tmp_path, monkeypatch, capsys):
    _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    registry = MaintainTaskRegistry()
    registry.register(
        MaintainTask(
            name="conditional",
            order=10,
            description="conditional",
            condition=lambda _ctx: (False, "not needed"),
            run=lambda _ctx: TaskResult("success", "should not run"),
        )
    )

    exit_code = maintain_command(
        MaintainOptions(json_output=True, quiet=True),
        registry=registry,
    )
    assert exit_code == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["data"]["summary"]["skipped"] == 1
    assert payload["data"]["tasks"][0]["status"] == "skipped"
    assert "details" in payload["data"]["tasks"][0]


def test_maintain_skip_accepts_comma_separated_list(tmp_path, monkeypatch):
    _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    executed = []
    registry = MaintainTaskRegistry()
    registry.register(
        MaintainTask(
            name="first",
            order=10,
            description="first",
            run=lambda _ctx: executed.append("first") or TaskResult("success", "ok"),
        )
    )
    registry.register(
        MaintainTask(
            name="second",
            order=20,
            description="second",
            run=lambda _ctx: executed.append("second") or TaskResult("success", "ok"),
        )
    )

    exit_code = maintain_command(
        MaintainOptions(skip=["first,second"], quiet=True),
        registry=registry,
    )

    assert exit_code == 0
    assert executed == []


def test_maintain_dry_run_cli_executes(tmp_path):
    _init_project(tmp_path)
    (tmp_path / "docs" / "doc.md").write_text(
        "---\nid: sample\ntype: atom\nstatus: active\n---\n",
        encoding="utf-8",
    )
    project_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "-m", "ontos", "maintain", "--dry-run"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env={
            "PYTHONPATH": str(project_root),
        },
    )

    assert result.returncode == 0
    assert "maintenance" in result.stdout.lower()


def test_parse_bool_warns_on_empty_and_unknown():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert _parse_bool("", default=True) is True
        assert _parse_bool("maybe", default=False) is False

    messages = [str(item.message) for item in caught]
    assert any("Unrecognized boolean value" in msg and "''" in msg for msg in messages)
    assert any("Unrecognized boolean value" in msg and "'maybe'" in msg for msg in messages)


def test_parse_bool_valid_values_emit_no_warning():
    valid_cases = [
        ("1", True),
        ("true", True),
        ("yes", True),
        ("on", True),
        ("0", False),
        ("false", False),
        ("no", False),
        ("off", False),
    ]

    for raw, expected in valid_cases:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert _parse_bool(raw, default=not expected) is expected
        assert not caught


def test_maintain_invalid_task_status_becomes_failed(tmp_path, monkeypatch, capsys):
    _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    registry = MaintainTaskRegistry()
    registry.register(
        MaintainTask(
            name="bad_status",
            order=10,
            description="bad",
            run=lambda _ctx: TaskResult(status="unexpected", message="oops"),  # type: ignore[arg-type]
        )
    )

    exit_code = maintain_command(
        MaintainOptions(json_output=True, quiet=True),
        registry=registry,
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"]["tasks"][0]["status"] == "failed"
    assert "invalid task status" in payload["data"]["tasks"][0]["details"][0]


def test_promote_check_task_reports_promotable_docs(tmp_path):
    _init_project(tmp_path)
    docs = tmp_path / "docs"
    # L0 scaffold document — promotable
    (docs / "scaffold.md").write_text(
        "---\nid: scaffold_doc\ntype: atom\nstatus: scaffold\n---\n",
        encoding="utf-8",
    )
    # L2 full document — not promotable
    (docs / "full.md").write_text(
        "---\nid: full_doc\ntype: atom\nstatus: active\ndepends_on: [scaffold_doc]\n---\n",
        encoding="utf-8",
    )

    ctx = _build_context(tmp_path, quiet=True)
    result = _task_promote_check(ctx)

    assert result.status == "success"


def test_promote_check_dry_run_skips_scan(tmp_path, monkeypatch):
    _init_project(tmp_path)
    ctx = _build_context(tmp_path, quiet=True, dry_run=True)

    def _should_not_run(_options):
        raise AssertionError("dry-run should not call promote")

    monkeypatch.setattr("ontos.commands.maintain._task_promote_check.__wrapped__", _should_not_run, raising=False)
    result = _task_promote_check(ctx)

    assert result.status == "success"
    assert "would run" in result.message.lower()
