"""Integration tests for `ontos rename` command."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_ontos(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "ontos", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        env=env,
    )


def _run_git(repo_root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(tmp_path: Path, extra_config: str = "") -> None:
    (tmp_path / ".ontos.toml").write_text(
        "[ontos]\nversion='3.2'\n" + extra_config,
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(exist_ok=True)


def _init_git_repo(tmp_path: Path) -> None:
    _run_git(tmp_path, "init")
    _run_git(tmp_path, "config", "user.email", "test@example.com")
    _run_git(tmp_path, "config", "user.name", "Test User")
    _run_git(tmp_path, "add", ".")
    _run_git(tmp_path, "commit", "-m", "baseline")


def _write_doc(
    path: Path,
    doc_id: Optional[str],
    *,
    doc_type: str = "atom",
    status: str = "active",
    depends_on: Optional[str] = None,
    impacts: Optional[str] = None,
    describes: Optional[str] = None,
    body: str = "Body",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if doc_id is None:
        path.write_text(body, encoding="utf-8")
        return

    lines = ["---", f"id: {doc_id}", f"type: {doc_type}", f"status: {status}"]
    if depends_on is not None:
        lines.append(f"depends_on: {depends_on}")
    if impacts is not None:
        lines.append(f"impacts: {impacts}")
    if describes is not None:
        lines.append(f"describes: {describes}")
    lines.extend(["---", body, ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def test_rename_noop_old_equals_new(tmp_path: Path):
    _init_repo(tmp_path)
    result = _run_ontos(tmp_path, "rename", "same_id", "same_id")
    assert result.returncode == 0
    assert "nothing_to_do" in result.stdout


def test_rename_rejects_reserved_new_id(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "old_id")
    result = _run_ontos(tmp_path, "rename", "old_id", "true")
    assert result.returncode == 1
    assert "reserved" in result.stdout.lower()


def test_rename_rejects_invalid_new_id_format(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "old_id")
    result = _run_ontos(tmp_path, "rename", "old_id", "bad id")
    assert result.returncode == 1
    assert "invalid_new_id" in result.stdout


def test_rename_aborts_on_duplicate_ids(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "dup")
    _write_doc(tmp_path / "docs" / "b.md", "dup")
    result = _run_ontos(tmp_path, "rename", "dup", "new_dup")
    assert result.returncode == 1
    assert "duplicate_ids" in result.stdout


def test_rename_aborts_when_old_id_not_found(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "doc_a")
    result = _run_ontos(tmp_path, "rename", "missing", "new_id")
    assert result.returncode == 1
    assert "old_id_not_found" in result.stdout


def test_rename_aborts_when_new_id_exists(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "old_id")
    _write_doc(tmp_path / "docs" / "b.md", "new_id")
    result = _run_ontos(tmp_path, "rename", "old_id", "new_id")
    assert result.returncode == 1
    assert "new_id_exists" in result.stdout


def test_rename_docs_scope_cross_scope_guard(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "old_id")
    _write_doc(tmp_path / ".ontos-internal" / "b.md", "new_id")

    result = _run_ontos(tmp_path, "rename", "old_id", "new_id", "--scope", "docs")
    assert result.returncode == 1
    assert "cross_scope_collision" in result.stdout
    assert "--scope library" in result.stdout


def test_rename_aborts_when_parse_failed_file_contains_target(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "target.md", "old_id")
    (tmp_path / "docs" / "broken.md").write_text(
        "---\nid: [\n---\nSee old_id.\n",
        encoding="utf-8",
    )
    result = _run_ontos(tmp_path, "rename", "old_id", "new_id")
    assert result.returncode == 1
    assert "parse_failed_target_sighting" in result.stdout


def test_rename_dirty_git_apply_rejected_but_dry_run_allowed(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "old_id", body="See old_id.")
    _init_git_repo(tmp_path)

    (tmp_path / "docs" / "a.md").write_text(
        "---\nid: old_id\ntype: atom\nstatus: active\n---\nSee old_id and more.\n",
        encoding="utf-8",
    )

    apply_result = _run_ontos(tmp_path, "rename", "old_id", "new_id", "--apply")
    assert apply_result.returncode == 1
    assert "dirty_git_state" in apply_result.stdout

    dry_run_result = _run_ontos(tmp_path, "rename", "old_id", "new_id")
    assert dry_run_result.returncode == 0
    assert "DRY RUN" in dry_run_result.stdout


def test_rename_dry_run_json_includes_line_context_and_skipped_zones(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "target.md", "old_id")
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        body=(
            "See old_id.\n"
            "Use [ref](old_id#anchor).\n"
            "`old_id`\n"
            "```yaml\nold_id\n```\n"
        ),
    )

    result = _run_ontos(tmp_path, "--json", "rename", "old_id", "new_id")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "dry_run"
    assert payload["status"] == "success"
    assert payload["summary"]["body_edits"] >= 2
    assert payload["summary"]["skipped_zone_sightings"] >= 2

    source_file = next(item for item in payload["files"] if item["path"].endswith("source.md"))
    assert any(item["match_type"] == "bare_id_token" for item in source_file["body_edits"])
    assert any(item["match_type"] == "markdown_link_target" for item in source_file["body_edits"])
    skipped = [item for item in source_file["body_edits"] if not item["rewritable"]]
    assert skipped
    assert skipped[0]["skip_reason"] is not None


def test_rename_frontmatter_comments_and_order_preserved_on_apply(tmp_path: Path):
    _init_repo(tmp_path)
    content = (
        "---\n"
        "id: old_id  # keep-id-comment\n"
        "type: strategy\n"
        "status: active\n"
        "depends_on:\n"
        "  - old_id  # keep-list-comment\n"
        "impacts: [old_id, other]\n"
        "describes: old_id\n"
        "# keep-tail-comment\n"
        "---\n"
        "See old_id.\n"
    )
    path = tmp_path / "docs" / "doc.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _init_git_repo(tmp_path)

    result = _run_ontos(tmp_path, "rename", "old_id", "new_id", "--apply")
    assert result.returncode == 0
    assert "Derived artifacts may be stale" in result.stdout

    updated = path.read_text(encoding="utf-8")
    assert "id: new_id  # keep-id-comment" in updated
    assert "  - new_id  # keep-list-comment" in updated
    assert "impacts: [new_id, other]" in updated
    assert "describes: new_id" in updated
    assert "# keep-tail-comment" in updated
    assert "See new_id." in updated


def test_rename_apply_json_schema_and_post_warning(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "old_id", body="See old_id.")
    _init_git_repo(tmp_path)

    result = _run_ontos(tmp_path, "--json", "rename", "old_id", "new_id", "--apply")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "apply"
    assert payload["status"] == "success"
    assert payload["summary"]["applied_files"] >= 1
    assert payload["partial_commit"]["detected"] is False
    assert payload["error"]["code"] is None
    assert "Derived artifacts may be stale" in payload["post_apply_warning"]


def test_rename_unsupported_frontmatter_warns_in_dry_run_and_blocks_apply(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "doc.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "id: old_id\n"
        "type: strategy\n"
        "status: active\n"
        "depends_on: [old_id, [nested]]\n"
        "---\n"
        "See old_id.\n",
        encoding="utf-8",
    )
    _init_git_repo(tmp_path)

    dry_run = _run_ontos(tmp_path, "--json", "rename", "old_id", "new_id")
    assert dry_run.returncode == 0
    dry_payload = json.loads(dry_run.stdout)
    assert dry_payload["warnings"]
    assert any(w["reason_code"] == "non_scalar_list" for w in dry_payload["warnings"])

    apply_result = _run_ontos(tmp_path, "--json", "rename", "old_id", "new_id", "--apply")
    assert apply_result.returncode == 1
    apply_payload = json.loads(apply_result.stdout)
    assert apply_payload["status"] == "error"
    assert apply_payload["error"]["code"] == "unsupported_target_format"


def test_rename_body_only_rewrite_for_files_without_frontmatter(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "target.md", "old_id")
    _write_doc(tmp_path / "docs" / "notes.md", None, body="Mention old_id and [x](old_id).")

    result = _run_ontos(tmp_path, "--json", "rename", "old_id", "new_id")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    notes = next(item for item in payload["files"] if item["path"].endswith("notes.md"))
    assert notes["frontmatter_edits"] == []
    assert len([item for item in notes["body_edits"] if item["rewritable"]]) >= 2


def test_rename_substring_ids_not_matched(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "target.md", "v3_2")
    _write_doc(
        tmp_path / "docs" / "src.md",
        "src",
        body="v3_2_1 should stay; v3_2.1 should stay; but v3_2 should change.",
    )

    result = _run_ontos(tmp_path, "--json", "rename", "v3_2", "v4_0")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    src = next(item for item in payload["files"] if item["path"].endswith("src.md"))
    rewritable = [item for item in src["body_edits"] if item["rewritable"]]
    assert len(rewritable) == 1
    assert rewritable[0]["old"] == "v3_2"


def test_rename_dot_id_regex_safety(tmp_path: Path):
    _init_repo(tmp_path)
    old_id = "v3.0.4_Code_Review_Claude"
    new_id = "v3.0.4_Code_Review_Renamed"
    _write_doc(tmp_path / "docs" / "target.md", old_id)
    _write_doc(
        tmp_path / "docs" / "src.md",
        "src",
        body=f"{old_id} should change; {old_id}.pdf should not.",
    )

    result = _run_ontos(tmp_path, "--json", "rename", old_id, new_id)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    src = next(item for item in payload["files"] if item["path"].endswith("src.md"))
    rewritable = [item for item in src["body_edits"] if item["rewritable"]]
    assert len(rewritable) == 1
    assert rewritable[0]["old"] == old_id


def test_rename_end_to_end_dry_run_apply_then_link_check(tmp_path: Path):
    _init_repo(
        tmp_path,
        extra_config="\n[validation]\nallowed_orphan_types=['atom','strategy']\n",
    )
    _write_doc(tmp_path / "docs" / "a.md", "old_id", doc_type="strategy")
    _write_doc(
        tmp_path / "docs" / "b.md",
        "b_doc",
        doc_type="strategy",
        depends_on="[old_id]",
        body="See old_id and [r](old_id#next).",
    )
    _init_git_repo(tmp_path)

    dry_run = _run_ontos(tmp_path, "rename", "old_id", "new_id")
    assert dry_run.returncode == 0
    assert "No files written" in dry_run.stdout

    apply_result = _run_ontos(tmp_path, "rename", "old_id", "new_id", "--apply")
    assert apply_result.returncode == 0

    link_check = _run_ontos(tmp_path, "--json", "link-check")
    assert link_check.returncode == 0
    payload = json.loads(link_check.stdout)
    assert payload["summary"]["broken_references"] == 0
    assert payload["summary"]["duplicate_ids"] == 0

