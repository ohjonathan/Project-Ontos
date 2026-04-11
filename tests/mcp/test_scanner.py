from __future__ import annotations

import json
from pathlib import Path

from ontos.mcp.scanner import discover_projects, slugify


def test_slugify_normalizes_name():
    assert slugify("My.Project Name") == "my-project-name"
    assert slugify("___") == "workspace"


def test_discover_projects_classifies_and_excludes(tmp_path):
    scan_root = tmp_path / "Dev"
    scan_root.mkdir()

    documented = _make_project(scan_root / "documented", with_ontos=True, with_readme=True, doc_count=5)
    partial = _make_project(scan_root / "partial", with_ontos=False, with_readme=True, doc_count=0)
    undocumented = _make_project(scan_root / "undocumented", with_ontos=False, with_readme=False, doc_count=0)
    excluded = _make_project(scan_root / "skip-me", with_ontos=True, with_readme=True, doc_count=5)

    projects = discover_projects(
        scan_roots=[scan_root],
        exclude=[str(excluded)],
        registry_path=None,
    )

    by_path = {entry.path: entry for entry in projects}
    assert documented in by_path
    assert partial in by_path
    assert undocumented in by_path
    assert excluded not in by_path

    assert by_path[documented].status == "documented"
    assert by_path[partial].status == "partial"
    assert by_path[undocumented].status == "undocumented"


def test_discover_projects_merges_registry_metadata(tmp_path):
    scan_root = tmp_path / "Dev"
    scan_root.mkdir()
    project_path = _make_project(scan_root / "alpha", with_ontos=True, with_readme=True, doc_count=5)

    registry_path = tmp_path / ".dev-hub" / "registry" / "projects.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "projects": [
                    {
                        "path": str(project_path),
                        "status": "archived",
                        "tags": ["legacy"],
                        "metadata": {"owner": "core"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    projects = discover_projects(
        scan_roots=[scan_root],
        exclude=[],
        registry_path=registry_path,
    )
    assert len(projects) == 1
    project = projects[0]
    assert project.status == "archived"
    assert project.tags == ["legacy"]
    assert project.metadata == {"owner": "core"}


def test_discover_projects_resolves_registry_paths_from_dev_root(tmp_path):
    dev_root = tmp_path / "Dev"
    dev_root.mkdir()
    project_path = _make_project(dev_root / "alpha", with_ontos=True, with_readme=True, doc_count=5)

    registry_path = tmp_path / ".dev-hub" / "registry" / "projects.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "dev_root": str(dev_root),
                "projects": [
                    {
                        "path": "alpha",
                        "status": "documented",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    projects = discover_projects(
        scan_roots=[],
        exclude=[],
        registry_path=registry_path,
    )

    assert len(projects) == 1
    assert projects[0].path == project_path


def test_discover_projects_handles_slug_collisions(tmp_path):
    root_one = tmp_path / "DevA"
    root_two = tmp_path / "DevB"
    root_one.mkdir()
    root_two.mkdir()

    _make_project(root_one / "sample-app", with_ontos=True, with_readme=True, doc_count=5)
    _make_project(root_two / "sample-app", with_ontos=True, with_readme=True, doc_count=5)

    projects = discover_projects(
        scan_roots=[root_one, root_two],
        exclude=[],
        registry_path=None,
    )

    slugs = sorted(entry.slug for entry in projects)
    assert slugs == ["sample-app", "sample-app-2"]


def _make_project(path: Path, *, with_ontos: bool, with_readme: bool, doc_count: int) -> Path:
    path.mkdir(parents=True)
    (path / ".git").mkdir()

    if with_readme:
        (path / "README.md").write_text("# Example\n", encoding="utf-8")

    if with_ontos:
        (path / ".ontos.toml").write_text(
            """
            [ontos]
            version = "4.0"

            [scanning]
            skip_patterns = ["_template.md", "archive/*"]
            """,
            encoding="utf-8",
        )
        docs_dir = path / "docs"
        docs_dir.mkdir()
        for index in range(doc_count):
            (docs_dir / f"doc-{index}.md").write_text(
                f"""
                ---
                id: doc_{index}
                type: atom
                status: active
                ---
                Body {index}.
                """,
                encoding="utf-8",
            )

    return path.resolve()
