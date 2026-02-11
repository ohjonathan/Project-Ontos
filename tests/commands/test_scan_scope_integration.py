"""CLI and command integration tests for unified scan scope."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_ontos(repo_root: Path, *args: str, input_text: Optional[str] = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "ontos", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        input=input_text,
        env=env,
    )


def _write_doc(
    path: Path,
    doc_id: str,
    doc_type: str = "atom",
    *,
    status: str = "active",
    extra_frontmatter: str = "",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = f"---\nid: {doc_id}\ntype: {doc_type}\nstatus: {status}\n{extra_frontmatter}---\nBody\n"
    path.write_text(frontmatter, encoding="utf-8")


def _init_repo(tmp_path: Path) -> None:
    (tmp_path / ".ontos.toml").write_text("[ontos]\nversion='3.2'\n", encoding="utf-8")
    (tmp_path / "docs").mkdir(exist_ok=True)


@pytest.mark.parametrize(
    "args",
    [
        ("map", "--help"),
        ("maintain", "--help"),
        ("query", "--help"),
        ("verify", "--help"),
        ("scaffold", "--help"),
        ("promote", "--help"),
        ("schema-migrate", "--help"),
        ("agents", "--help"),
        ("doctor", "--help"),
        ("export", "data", "--help"),
        ("migration-report", "--help"),
        ("migrate", "--help"),
        ("tree", "--help"),
        ("validate", "--help"),
        ("agent-export", "--help"),
        ("link-check", "--help"),
        ("rename", "--help"),
    ],
)
def test_scope_flag_registered_for_migrated_commands(tmp_path: Path, args: tuple[str, ...]) -> None:
    _init_repo(tmp_path)
    result = _run_ontos(tmp_path, *args)
    assert result.returncode == 0
    assert "--scope" in result.stdout


def test_export_claude_help_has_no_scope(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    result = _run_ontos(tmp_path, "export", "claude", "--help")
    assert result.returncode == 0
    assert "--scope" not in result.stdout


def test_query_scope_library_includes_internal(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "doc_a")
    _write_doc(tmp_path / ".ontos-internal" / "b.md", "internal_b")

    default_result = _run_ontos(tmp_path, "query", "--list-ids")
    assert default_result.returncode == 0
    assert "doc_a" in default_result.stdout
    assert "internal_b" not in default_result.stdout

    library_result = _run_ontos(tmp_path, "query", "--list-ids", "--scope", "library")
    assert library_result.returncode == 0
    assert "doc_a" in library_result.stdout
    assert "internal_b" in library_result.stdout


def test_query_uses_config_default_scope_library_without_cli_flag(tmp_path: Path) -> None:
    (tmp_path / ".ontos.toml").write_text(
        "[ontos]\nversion='3.2'\n[scanning]\ndefault_scope='library'\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(exist_ok=True)
    _write_doc(tmp_path / "docs" / "a.md", "doc_a")
    _write_doc(tmp_path / ".ontos-internal" / "b.md", "internal_b")

    result = _run_ontos(tmp_path, "query", "--list-ids")
    assert result.returncode == 0
    assert "doc_a" in result.stdout
    assert "internal_b" in result.stdout


def test_verify_scope_library_detects_cross_scope_duplicate(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "dup_id")
    _write_doc(tmp_path / ".ontos-internal" / "b.md", "dup_id")

    default_result = _run_ontos(tmp_path, "verify", "--all")
    assert default_result.returncode == 0

    library_result = _run_ontos(tmp_path, "verify", "--all", "--scope", "library")
    assert library_result.returncode != 0
    combined = library_result.stdout + library_result.stderr
    assert "Duplicate ID 'dup_id'" in combined


def test_schema_migrate_scope_library_includes_internal(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "already.md", "docs_ok", extra_frontmatter="ontos_schema: '3.2'\n")
    _write_doc(tmp_path / ".ontos-internal" / "needs.md", "internal_needs")

    default_result = _run_ontos(tmp_path, "schema-migrate", "--check")
    assert default_result.returncode == 0
    assert "Need migration: 0" in default_result.stdout

    library_result = _run_ontos(tmp_path, "schema-migrate", "--check", "--scope", "library")
    assert library_result.returncode == 1
    assert "Need migration: 1" in library_result.stdout
    assert "needs.md" in library_result.stdout


def test_export_data_scope_library_includes_internal(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "doc_a")
    _write_doc(tmp_path / ".ontos-internal" / "b.md", "internal_b")

    out_default = tmp_path / "default.json"
    out_library = tmp_path / "library.json"

    default_result = _run_ontos(tmp_path, "export", "data", "-o", str(out_default))
    assert default_result.returncode == 0

    library_result = _run_ontos(tmp_path, "export", "data", "-o", str(out_library), "--scope", "library")
    assert library_result.returncode == 0

    default_payload = json.loads(out_default.read_text(encoding="utf-8"))
    library_payload = json.loads(out_library.read_text(encoding="utf-8"))

    assert default_payload["summary"]["total_documents"] == 1
    assert library_payload["summary"]["total_documents"] == 2


def test_migration_report_scope_library_includes_internal(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "doc_a")
    _write_doc(tmp_path / ".ontos-internal" / "b.md", "internal_b")

    out_default = tmp_path / "report-default.json"
    out_library = tmp_path / "report-library.json"

    default_result = _run_ontos(
        tmp_path,
        "migration-report",
        "--format",
        "json",
        "-o",
        str(out_default),
    )
    assert default_result.returncode == 0

    library_result = _run_ontos(
        tmp_path,
        "migration-report",
        "--format",
        "json",
        "-o",
        str(out_library),
        "--scope",
        "library",
    )
    assert library_result.returncode == 0

    default_payload = json.loads(out_default.read_text(encoding="utf-8"))
    library_payload = json.loads(out_library.read_text(encoding="utf-8"))

    assert len(default_payload["classifications"]) == 1
    assert len(library_payload["classifications"]) == 2


def test_doctor_scope_library_integration(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "doc_a")
    _write_doc(tmp_path / ".ontos-internal" / "b.md", "internal_b")

    default_result = _run_ontos(tmp_path, "--json", "doctor")
    library_result = _run_ontos(tmp_path, "--json", "doctor", "--scope", "library")

    assert default_result.stdout
    assert library_result.stdout
    default_payload = json.loads(default_result.stdout)
    library_payload = json.loads(library_result.stdout)

    default_docs_check = next(c for c in default_payload["checks"] if c["name"] == "docs_directory")
    library_docs_check = next(c for c in library_payload["checks"] if c["name"] == "docs_directory")

    assert "1 documents" in default_docs_check["message"]
    assert "2 documents" in library_docs_check["message"]


def test_promote_scope_library_includes_internal(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "doc_a", status="scaffold", extra_frontmatter="curation_level: 0\n")
    _write_doc(
        tmp_path / ".ontos-internal" / "b.md",
        "internal_b",
        status="scaffold",
        extra_frontmatter="curation_level: 0\n",
    )

    default_result = _run_ontos(tmp_path, "promote", "--check")
    assert default_result.returncode == 0
    assert "Found 1 document" in default_result.stdout

    library_result = _run_ontos(tmp_path, "promote", "--check", "--scope", "library")
    assert library_result.returncode == 0
    assert "Found 2 document" in library_result.stdout


def test_scaffold_scope_library_includes_internal(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "docs" / "untagged.md").write_text("# docs\n", encoding="utf-8")
    (tmp_path / ".ontos-internal").mkdir()
    (tmp_path / ".ontos-internal" / "internal.md").write_text("# internal\n", encoding="utf-8")

    default_result = _run_ontos(tmp_path, "scaffold", "--dry-run")
    assert default_result.returncode == 0
    assert "docs/untagged.md" in default_result.stdout
    assert ".ontos-internal/internal.md" not in default_result.stdout

    library_result = _run_ontos(tmp_path, "scaffold", "--dry-run", "--scope", "library")
    assert library_result.returncode == 0
    assert "docs/untagged.md" in library_result.stdout
    assert ".ontos-internal/internal.md" in library_result.stdout


def test_migrate_convenience_scope_library_includes_internal(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "doc_a")
    _write_doc(tmp_path / ".ontos-internal" / "b.md", "internal_b")

    out_default = tmp_path / "mig-default"
    out_library = tmp_path / "mig-library"

    default_result = _run_ontos(tmp_path, "migrate", "--out-dir", str(out_default))
    assert default_result.returncode == 0
    default_snapshot = json.loads((out_default / "snapshot.json").read_text(encoding="utf-8"))
    assert default_snapshot["summary"]["total_documents"] == 1

    library_result = _run_ontos(
        tmp_path,
        "migrate",
        "--out-dir",
        str(out_library),
        "--scope",
        "library",
    )
    assert library_result.returncode == 0
    library_snapshot = json.loads((out_library / "snapshot.json").read_text(encoding="utf-8"))
    assert library_snapshot["summary"]["total_documents"] == 2


def test_agents_scope_library_updates_doc_count(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "doc_a")
    _write_doc(tmp_path / ".ontos-internal" / "b.md", "internal_b")

    default_result = _run_ontos(tmp_path, "agents")
    assert default_result.returncode == 0
    default_agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")

    library_result = _run_ontos(tmp_path, "agents", "--force", "--scope", "library")
    assert library_result.returncode == 0
    library_agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")

    default_count = re.search(r"\| Doc Count \| (.+?) \|", default_agents)
    library_count = re.search(r"\| Doc Count \| (.+?) \|", library_agents)

    assert default_count
    assert library_count
    assert default_count.group(1) == "1"
    assert library_count.group(1) == "2"
