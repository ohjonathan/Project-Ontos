"""Core diagnostics tests for link-check shared engine."""

from pathlib import Path
from typing import Optional

from ontos.core.link_diagnostics import run_link_diagnostics
from ontos.io.config import load_project_config
from ontos.io.files import load_documents
from ontos.io.scan_scope import ScanScope, collect_scoped_documents
from ontos.io.yaml import parse_frontmatter_content


def _init_project(tmp_path: Path, extra_config: str = "") -> None:
    (tmp_path / ".ontos.toml").write_text(
        "[ontos]\nversion='3.2'\n"
        + extra_config,
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(exist_ok=True)


def _write_doc(
    path: Path,
    doc_id: str,
    *,
    doc_type: str = "atom",
    status: str = "active",
    depends_on: Optional[str] = None,
    impacts: Optional[str] = None,
    describes: Optional[str] = None,
    body: str = "Body",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = [
        "---",
        f"id: {doc_id}",
        f"type: {doc_type}",
        f"status: {status}",
    ]
    if depends_on is not None:
        frontmatter.append(f"depends_on: {depends_on}")
    if impacts is not None:
        frontmatter.append(f"impacts: {impacts}")
    if describes is not None:
        frontmatter.append(f"describes: {describes}")
    frontmatter.extend(["---", body, ""])
    path.write_text("\n".join(frontmatter), encoding="utf-8")


def _run(tmp_path: Path, scope: ScanScope):
    config = load_project_config(config_path=tmp_path / ".ontos.toml", repo_root=tmp_path)
    paths = collect_scoped_documents(
        tmp_path,
        config,
        scope,
        base_skip_patterns=list(config.scanning.skip_patterns),
    )
    load_result = load_documents(paths, parse_frontmatter_content)
    return run_link_diagnostics(
        repo_root=tmp_path,
        config=config,
        doc_paths=paths,
        scope=scope,
        load_result=load_result,
    )


def test_clean_library_returns_exit_0(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "a", doc_type="atom")
    _write_doc(tmp_path / "docs" / "b.md", "b", doc_type="atom", depends_on="[a]", body="See a.")

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.exit_code == 0
    assert result.summary.broken_references == 0
    assert result.summary.duplicate_ids == 0


def test_broken_depends_on_returns_exit_1(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(
        tmp_path / "docs" / "broken.md",
        "broken_doc",
        doc_type="strategy",
        depends_on="[missing_doc]",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.exit_code == 1
    assert result.summary.broken_frontmatter == 1
    assert any(finding.field == "depends_on" for finding in result.broken_references)


def test_orphans_only_returns_exit_2(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "orphan.md", "orphan_doc", doc_type="strategy")

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.exit_code == 2
    assert result.summary.broken_references == 0
    assert result.summary.orphans == 1


def test_duplicate_ids_return_exit_1(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "a.md", "duplicate_doc")
    _write_doc(tmp_path / "docs" / "b.md", "duplicate_doc")

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.exit_code == 1
    assert result.summary.duplicate_ids == 1
    assert "duplicate_doc" in result.duplicates


def test_cross_scope_reference_is_external_not_broken(tmp_path: Path):
    _init_project(tmp_path, extra_config="\n[validation]\nallowed_orphan_types=['atom', 'strategy']\n")
    _write_doc(
        tmp_path / "docs" / "doc.md",
        "docs_doc",
        doc_type="strategy",
        depends_on="[internal_doc]",
    )
    _write_doc(tmp_path / ".ontos-internal" / "internal.md", "internal_doc", doc_type="strategy")

    result = _run(tmp_path, ScanScope.DOCS)

    assert result.summary.broken_references == 0
    assert result.summary.external_references == 1
    assert result.exit_code == 0


def test_parse_failed_candidates_reported_without_affecting_exit(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "known.md", "known_doc")
    (tmp_path / "docs" / "broken.md").write_text(
        "---\nid: [\n---\nSee known_doc in body.\n",
        encoding="utf-8",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.summary.parse_failed_candidates >= 1
    assert result.exit_code == 0


def test_body_broken_reference_gets_suggestion(tmp_path: Path):
    _init_project(tmp_path)
    _write_doc(tmp_path / "docs" / "target.md", "v3_2_1")
    _write_doc(
        tmp_path / "docs" / "source.md",
        "source_doc",
        body="See v3_2 for details.",
    )

    result = _run(tmp_path, ScanScope.LIBRARY)

    assert result.exit_code == 1
    body_broken = [finding for finding in result.broken_references if finding.field == "body.bare_id_token"]
    assert body_broken
    assert body_broken[0].suggestions
