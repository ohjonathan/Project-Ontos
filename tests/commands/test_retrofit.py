"""Integration tests for `ontos retrofit` command."""

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
    concepts: Optional[str] = None,
    tags: Optional[str] = None,
    aliases: Optional[str] = None,
    extra_lines: Optional[list] = None,
    body: str = "Body",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if doc_id is None:
        path.write_text(body, encoding="utf-8")
        return

    lines = ["---", f"id: {doc_id}", f"type: {doc_type}", f"status: {status}"]
    if concepts is not None:
        lines.append(f"concepts: {concepts}")
    if tags is not None:
        lines.append(f"tags: {tags}")
    if aliases is not None:
        lines.append(f"aliases: {aliases}")
    if extra_lines:
        lines.extend(extra_lines)
    lines.extend(["---", body, ""])
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Required-mode guard
# ---------------------------------------------------------------------------


def test_retrofit_requires_obsidian_flag(tmp_path: Path):
    _init_repo(tmp_path)
    result = _run_ontos(tmp_path, "retrofit")
    assert result.returncode == 1
    assert "missing_mode" in result.stdout


def test_retrofit_missing_obsidian_json_envelope(tmp_path: Path):
    _init_repo(tmp_path)
    result = _run_ontos(tmp_path, "--json", "retrofit")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "missing_mode"


# ---------------------------------------------------------------------------
# Dry-run behavior
# ---------------------------------------------------------------------------


def test_retrofit_dry_run_plans_inserts_and_writes_nothing(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "auth.md"
    _write_doc(path, "auth_flow", concepts="[a, b]")
    original = path.read_text(encoding="utf-8")

    result = _run_ontos(tmp_path, "retrofit", "--obsidian")
    assert result.returncode == 0
    assert "DRY RUN" in result.stdout
    assert "No files written" in result.stdout
    assert path.read_text(encoding="utf-8") == original


def test_retrofit_dry_run_json_envelope(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "auth.md", "auth_flow", concepts="[a, b]")

    result = _run_ontos(tmp_path, "--json", "retrofit", "--obsidian")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "success"
    data = payload["data"]
    assert data["mode"] == "dry_run"
    assert data["summary"]["planned_files"] == 1
    assert data["summary"]["inserts"] >= 2  # tags + aliases
    file_entry = data["files"][0]
    assert any(
        e["field"] == "tags"
        and e["action"] == "insert"
        and e["path"].endswith("auth.md")
        for e in file_entry["edits"]
    )
    assert any(
        e["field"] == "aliases"
        and e["action"] == "insert"
        and e["path"].endswith("auth.md")
        for e in file_entry["edits"]
    )


# ---------------------------------------------------------------------------
# Apply behavior — inserts
# ---------------------------------------------------------------------------


def test_retrofit_apply_inserts_tags_and_aliases(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "auth.md"
    _write_doc(path, "auth_flow", concepts="[a, b]")
    _init_git_repo(tmp_path)

    result = _run_ontos(tmp_path, "retrofit", "--obsidian", "--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Run 'ontos map'" in result.stdout

    updated = path.read_text(encoding="utf-8")
    assert "tags:" in updated
    assert "  - a" in updated
    assert "  - b" in updated
    assert "aliases:" in updated
    assert "Auth Flow" in updated
    assert "auth-flow" in updated

    # Round-trip through YAML parser
    import yaml
    parts = updated.split("---", 2)
    parsed = yaml.safe_load(parts[1])
    assert parsed["id"] == "auth_flow"
    assert parsed["tags"] == ["a", "b"]
    assert sorted(parsed["aliases"]) == ["Auth Flow", "auth-flow"]


def test_retrofit_apply_auto_aliases_only_when_no_tags(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "note.md"
    _write_doc(path, "auth_flow")  # no concepts, no tags
    _init_git_repo(tmp_path)

    result = _run_ontos(tmp_path, "retrofit", "--obsidian", "--apply")
    assert result.returncode == 0, result.stdout

    updated = path.read_text(encoding="utf-8")
    assert "aliases:" in updated
    assert "Auth Flow" in updated
    assert "auth-flow" in updated
    # No tags block should be written — nothing to put in it.
    import yaml
    parts = updated.split("---", 2)
    parsed = yaml.safe_load(parts[1])
    assert "tags" not in parsed or not parsed.get("tags")


# ---------------------------------------------------------------------------
# Apply behavior — no-op when matching
# ---------------------------------------------------------------------------


def test_retrofit_apply_noop_when_fields_match_computed(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "stable.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Pre-write a doc with tags + aliases already matching what normalize would compute.
    path.write_text(
        "---\n"
        "id: auth_flow\n"
        "type: atom\n"
        "status: active\n"
        "tags:\n"
        "  - a\n"
        "  - b\n"
        "aliases:\n"
        "  - Auth Flow\n"
        "  - auth-flow\n"
        "concepts:\n"
        "  - a\n"
        "  - b\n"
        "---\n"
        "Body\n",
        encoding="utf-8",
    )
    _init_git_repo(tmp_path)

    result = _run_ontos(tmp_path, "--json", "retrofit", "--obsidian", "--apply")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    data = payload["data"]
    assert data["summary"]["planned_files"] == 0
    assert data["summary"]["inserts"] == 0
    assert data["summary"]["replaces"] == 0
    assert data["summary"]["removes"] == 0
    file_entry = next(item for item in data["files"] if item["path"].endswith("stable.md"))
    assert file_entry["edits"] == []


# ---------------------------------------------------------------------------
# Apply behavior — replace when drifting
# ---------------------------------------------------------------------------


def test_retrofit_apply_replaces_drifted_tags(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "drift.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "id: drift_doc\n"
        "type: atom\n"
        "status: active\n"
        "concepts:\n"
        "  - alpha\n"
        "  - beta\n"
        "tags:\n"
        "  - stale\n"
        "---\n"
        "Body\n",
        encoding="utf-8",
    )
    _init_git_repo(tmp_path)

    result = _run_ontos(tmp_path, "retrofit", "--obsidian", "--apply")
    assert result.returncode == 0, result.stdout + result.stderr

    updated = path.read_text(encoding="utf-8")
    import yaml
    parts = updated.split("---", 2)
    parsed = yaml.safe_load(parts[1])
    assert parsed["tags"] == ["alpha", "beta"]


def test_retrofit_apply_replace_preserves_inter_field_comment(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "commented.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "id: commented_doc\n"
        "type: atom\n"
        "status: active\n"
        "concepts:\n"
        "  - fresh\n"
        "tags:\n"
        "  - old-tag\n"
        "# This comment must survive\n"
        "aliases:\n"
        "  - Test Alias\n"
        "---\n"
        "Body\n",
        encoding="utf-8",
    )
    _init_git_repo(tmp_path)

    result = _run_ontos(tmp_path, "retrofit", "--obsidian", "--apply")
    assert result.returncode == 0, result.stdout + result.stderr

    updated = path.read_text(encoding="utf-8")
    assert "# This comment must survive\naliases:\n" in updated


def test_retrofit_apply_rewrites_tags_from_concepts_only(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "merge.md"
    _write_doc(path, "merge_doc", concepts="[a, b]", tags="[c]")
    _init_git_repo(tmp_path)

    result = _run_ontos(tmp_path, "retrofit", "--obsidian", "--apply")
    assert result.returncode == 0

    updated = path.read_text(encoding="utf-8")
    import yaml
    parts = updated.split("---", 2)
    parsed = yaml.safe_load(parts[1])
    assert parsed["tags"] == ["a", "b"]


def test_retrofit_apply_quotes_date_like_tag_values(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "dated.md"
    _write_doc(path, "dated_doc", concepts="['2026-01-01']")
    _init_git_repo(tmp_path)

    result = _run_ontos(tmp_path, "retrofit", "--obsidian", "--apply")
    assert result.returncode == 0, result.stdout + result.stderr

    updated = path.read_text(encoding="utf-8")
    assert '  - "2026-01-01"' in updated

    from ontos.io.yaml import parse_frontmatter_content

    parsed, _ = parse_frontmatter_content(updated)
    assert parsed["tags"] == ["2026-01-01"]
    assert isinstance(parsed["tags"][0], str)


# ---------------------------------------------------------------------------
# Dirty git guard
# ---------------------------------------------------------------------------


def test_retrofit_apply_aborts_on_dirty_git(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "some_id", concepts="[x]")
    _init_git_repo(tmp_path)

    (tmp_path / "docs" / "a.md").write_text(
        "---\nid: some_id\ntype: atom\nstatus: active\nconcepts: [x]\n---\nEdited\n",
        encoding="utf-8",
    )

    result = _run_ontos(tmp_path, "retrofit", "--obsidian", "--apply")
    assert result.returncode == 1
    assert "dirty_git_state" in result.stdout


# ---------------------------------------------------------------------------
# Unpatchable frontmatter — skipped but other files still apply
# ---------------------------------------------------------------------------


def test_retrofit_apply_skips_duplicate_top_level_field(tmp_path: Path):
    _init_repo(tmp_path)
    # Doc with duplicate top-level `tags:` block (blocking warning).
    duplicate = tmp_path / "docs" / "dup.md"
    duplicate.parent.mkdir(parents=True, exist_ok=True)
    duplicate.write_text(
        "---\n"
        "id: dup_doc\n"
        "type: atom\n"
        "status: active\n"
        "tags:\n"
        "  - one\n"
        "tags:\n"
        "  - two\n"
        "---\n"
        "Body\n",
        encoding="utf-8",
    )

    dry_run = _run_ontos(tmp_path, "--json", "retrofit", "--obsidian")
    assert dry_run.returncode == 0
    dry_payload = json.loads(dry_run.stdout)
    assert any(
        w["reason_code"] == "duplicate_top_level_field"
        for w in dry_payload["warnings"]
    )

    _init_git_repo(tmp_path)
    apply_result = _run_ontos(tmp_path, "--json", "retrofit", "--obsidian", "--apply")
    assert apply_result.returncode == 1
    apply_payload = json.loads(apply_result.stdout)
    assert apply_payload["error"]["code"] == "unsupported_target_format"


def test_retrofit_dry_run_warns_on_merge_derived_tags_without_duplicate_insert(
    tmp_path: Path,
):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "merge-derived.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "id: merge_doc\n"
        "type: atom\n"
        "status: active\n"
        "concepts:\n"
        "  - merged\n"
        "shared: &shared\n"
        "  tags:\n"
        "    - merged\n"
        "<<: *shared\n"
        "---\n"
        "Body\n",
        encoding="utf-8",
    )
    original = path.read_text(encoding="utf-8")

    first = _run_ontos(tmp_path, "--json", "retrofit", "--obsidian")
    assert first.returncode == 0
    payload = json.loads(first.stdout)
    assert any(
        w["field"] == "tags" and w["reason_code"] == "unpatchable_field_format"
        for w in payload["warnings"]
    )
    file_entry = next(item for item in payload["data"]["files"] if item["path"].endswith("merge-derived.md"))
    assert not any(
        edit["field"] == "tags" and edit["action"] == "insert"
        for edit in file_entry["edits"]
    )
    assert any(
        edit["field"] == "aliases" and edit["action"] == "insert"
        for edit in file_entry["edits"]
    )
    assert path.read_text(encoding="utf-8") == original

    second = _run_ontos(tmp_path, "--json", "retrofit", "--obsidian")
    assert second.returncode == 0
    second_payload = json.loads(second.stdout)
    second_entry = next(
        item for item in second_payload["data"]["files"] if item["path"].endswith("merge-derived.md")
    )
    assert not any(
        edit["field"] == "tags" and edit["action"] == "insert"
        for edit in second_entry["edits"]
    )


def test_retrofit_dry_run_warns_on_tag_prefixed_tags_field(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "tagged.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "id: tagged_doc\n"
        "type: atom\n"
        "status: active\n"
        "concepts:\n"
        "  - a\n"
        "tags: !!seq\n"
        "  - a\n"
        "---\n"
        "Body\n",
        encoding="utf-8",
    )
    original = path.read_text(encoding="utf-8")

    result = _run_ontos(tmp_path, "--json", "retrofit", "--obsidian")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert any(
        w["field"] == "tags" and w["reason_code"] == "unpatchable_field_format"
        for w in payload["warnings"]
    )
    file_entry = next(item for item in payload["data"]["files"] if item["path"].endswith("tagged.md"))
    assert not any(edit["field"] == "tags" for edit in file_entry["edits"])
    assert any(
        edit["field"] == "aliases" and edit["action"] == "insert"
        for edit in file_entry["edits"]
    )
    assert path.read_text(encoding="utf-8") == original


def test_retrofit_removes_stale_tags_when_computed_value_is_empty(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "stale-tags.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "id: stale_doc\n"
        "type: atom\n"
        "status: active\n"
        "tags:\n"
        "  - stale-tag\n"
        "aliases:\n"
        "  - Stale Doc\n"
        "  - stale-doc\n"
        "---\n"
        "Body\n",
        encoding="utf-8",
    )
    _init_git_repo(tmp_path)

    dry_run = _run_ontos(tmp_path, "--json", "retrofit", "--obsidian")
    assert dry_run.returncode == 0
    dry_payload = json.loads(dry_run.stdout)
    file_entry = next(item for item in dry_payload["data"]["files"] if item["path"].endswith("stale-tags.md"))
    assert any(
        edit["field"] == "tags" and edit["action"] == "remove"
        for edit in file_entry["edits"]
    )

    apply_result = _run_ontos(tmp_path, "retrofit", "--obsidian", "--apply")
    assert apply_result.returncode == 0, apply_result.stdout + apply_result.stderr

    updated = path.read_text(encoding="utf-8")
    assert "tags:" not in updated

    second = _run_ontos(tmp_path, "--json", "retrofit", "--obsidian")
    assert second.returncode == 0
    second_payload = json.loads(second.stdout)
    assert second_payload["data"]["summary"]["planned_files"] == 0


def test_retrofit_apply_preserves_crlf_line_endings(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "crlf.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        (
            "---\r\n"
            "id: crlf_doc\r\n"
            "type: atom\r\n"
            "status: active\r\n"
            "concepts:\r\n"
            "  - alpha\r\n"
            "---\r\n"
            "Body\r\n"
        ).encode("utf-8")
    )
    _init_git_repo(tmp_path)

    result = _run_ontos(tmp_path, "retrofit", "--obsidian", "--apply")
    assert result.returncode == 0, result.stdout + result.stderr

    updated = path.read_bytes()
    assert b"tags:\r\n  - alpha\r\n" in updated
    assert b"aliases:\r\n" in updated
    assert b"\n" not in updated.replace(b"\r\n", b"")


def test_retrofit_apply_surfaces_loader_issues_without_blocking_valid_files(
    tmp_path: Path,
):
    _init_repo(tmp_path)
    valid = tmp_path / "docs" / "valid.md"
    broken = tmp_path / "docs" / "broken.md"
    _write_doc(valid, "valid_doc", concepts="[x]")
    broken.write_text("---\nid: [\n---\nBroken\n", encoding="utf-8")
    _init_git_repo(tmp_path)

    result = _run_ontos(tmp_path, "--json", "retrofit", "--obsidian", "--apply")
    assert result.returncode == 0, result.stdout + result.stderr

    payload = json.loads(result.stdout)
    warning_codes = [warning["reason_code"] for warning in payload["warnings"]]
    assert "parse_error" in warning_codes
    data_warning_codes = [warning["reason_code"] for warning in payload["data"]["warnings"]]
    assert "parse_error" in data_warning_codes

    file_entry = next(item for item in payload["data"]["files"] if item["path"].endswith("valid.md"))
    assert any(edit["field"] == "tags" for edit in file_entry["edits"])

    updated = valid.read_text(encoding="utf-8")
    assert "tags:" in updated


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------


def test_retrofit_scope_library_covers_internal(tmp_path: Path):
    _init_repo(tmp_path)
    internal = tmp_path / ".ontos-internal" / "internal.md"
    _write_doc(internal, "internal_doc", concepts="[x, y]")
    _init_git_repo(tmp_path)

    result = _run_ontos(
        tmp_path, "retrofit", "--obsidian", "--scope", "library", "--apply"
    )
    assert result.returncode == 0
    updated = internal.read_text(encoding="utf-8")
    import yaml
    parts = updated.split("---", 2)
    parsed = yaml.safe_load(parts[1])
    assert parsed["tags"] == ["x", "y"]


def test_retrofit_scope_docs_leaves_internal_alone(tmp_path: Path):
    _init_repo(tmp_path)
    internal = tmp_path / ".ontos-internal" / "internal.md"
    docs_doc = tmp_path / "docs" / "public.md"
    _write_doc(internal, "internal_doc", concepts="[x]")
    _write_doc(docs_doc, "public_doc", concepts="[y]")
    _init_git_repo(tmp_path)

    result = _run_ontos(tmp_path, "--json", "retrofit", "--obsidian")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    file_paths = [f["path"] for f in payload["data"]["files"]]
    assert any(p.endswith("public.md") for p in file_paths)
    assert not any("internal.md" in p for p in file_paths)


# ---------------------------------------------------------------------------
# Idempotence — second dry-run after apply is a no-op
# ---------------------------------------------------------------------------


def test_retrofit_second_run_is_idempotent(tmp_path: Path):
    _init_repo(tmp_path)
    path = tmp_path / "docs" / "auth.md"
    _write_doc(path, "auth_flow", concepts="[a, b]")
    _init_git_repo(tmp_path)

    apply_result = _run_ontos(tmp_path, "retrofit", "--obsidian", "--apply")
    assert apply_result.returncode == 0, apply_result.stdout

    second = _run_ontos(tmp_path, "--json", "retrofit", "--obsidian")
    assert second.returncode == 0
    payload = json.loads(second.stdout)
    assert payload["data"]["summary"]["planned_files"] == 0
