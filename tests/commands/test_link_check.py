"""Integration tests for `ontos link-check` command."""

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


def _init_repo(tmp_path: Path, extra_config: str = "") -> None:
    (tmp_path / ".ontos.toml").write_text(
        "[ontos]\nversion='3.2'\n" + extra_config,
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(exist_ok=True)


def _write_doc(
    path: Path,
    doc_id: str,
    *,
    doc_type: str = "atom",
    depends_on: Optional[str] = None,
    impacts: Optional[str] = None,
    describes: Optional[str] = None,
    body: str = "Body",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"id: {doc_id}",
        f"type: {doc_type}",
        "status: active",
    ]
    if depends_on is not None:
        lines.append(f"depends_on: {depends_on}")
    if impacts is not None:
        lines.append(f"impacts: {impacts}")
    if describes is not None:
        lines.append(f"describes: {describes}")
    lines.extend(["---", body, ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def test_link_check_clean_library_exit_0(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "a")
    _write_doc(tmp_path / "docs" / "b.md", "b", depends_on="[a]", body="See a.")

    result = _run_ontos(tmp_path, "link-check")

    assert result.returncode == 0
    assert "clean" in result.stdout.lower()


def test_link_check_broken_refs_exit_1(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "broken.md", "broken_doc", doc_type="strategy", depends_on="[missing_doc]")

    result = _run_ontos(tmp_path, "link-check")

    assert result.returncode == 1
    assert "broken" in result.stdout.lower()


def test_link_check_orphans_only_exit_2(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "orphan.md", "orphan_doc", doc_type="strategy")

    result = _run_ontos(tmp_path, "link-check")

    assert result.returncode == 2
    assert "orphan" in result.stdout.lower()


def test_link_check_duplicates_exit_1(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "dup")
    _write_doc(tmp_path / "docs" / "b.md", "dup")

    result = _run_ontos(tmp_path, "link-check")

    assert result.returncode == 1
    assert "duplicate" in result.stdout.lower()


def test_link_check_cross_scope_reference_is_external(tmp_path: Path):
    _init_repo(tmp_path, extra_config="\n[validation]\nallowed_orphan_types=['atom','strategy']\n")
    _write_doc(
        tmp_path / "docs" / "docs.md",
        "docs_doc",
        doc_type="strategy",
        depends_on="[internal_doc]",
    )
    _write_doc(tmp_path / ".ontos-internal" / "internal.md", "internal_doc", doc_type="strategy")

    result = _run_ontos(tmp_path, "--json", "link-check")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["external_references"] == 1
    assert payload["summary"]["broken_references"] == 0


def test_link_check_json_schema_locations(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "target.md", "target_doc")
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        depends_on="[missing_doc]",
        body="See missing_doc and [bad](missing_doc).",
    )

    result = _run_ontos(tmp_path, "--json", "link-check")
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["status"] == "success"
    assert payload["scope"] == "docs"
    assert "summary" in payload
    assert "broken_references" in payload

    frontmatter_items = [item for item in payload["broken_references"] if item["field"] == "depends_on"]
    body_items = [item for item in payload["broken_references"] if item["field"].startswith("body.")]
    assert frontmatter_items
    assert body_items
    assert frontmatter_items[0]["location"] is None
    assert body_items[0]["location"]["line"] >= 1


def test_link_check_quiet_suppresses_sections(tmp_path: Path):
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "broken.md", "broken_doc", doc_type="strategy", depends_on="[missing_doc]")

    result = _run_ontos(tmp_path, "link-check", "--quiet")
    assert result.returncode == 1
    assert "Scope + Census" not in result.stdout
    assert "status:" in result.stdout


def test_link_check_uses_config_default_scope_without_cli(tmp_path: Path):
    _init_repo(tmp_path, extra_config="\n[scanning]\ndefault_scope='library'\n")
    _write_doc(tmp_path / "docs" / "a.md", "a")
    _write_doc(tmp_path / ".ontos-internal" / "b.md", "b")

    result = _run_ontos(tmp_path, "--json", "link-check")
    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["scope"] == "library"
    assert payload["summary"]["documents_loaded"] == 2
