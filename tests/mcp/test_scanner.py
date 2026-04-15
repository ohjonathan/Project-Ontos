from __future__ import annotations

import json
from pathlib import Path

import pytest

from ontos.mcp.scanner import discover_projects, load_registry_records, slugify


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


def test_discover_projects_without_collisions_emits_no_warning(tmp_path, capsys):
    scan_root = tmp_path / "Dev"
    scan_root.mkdir()
    _make_project(scan_root / "alpha", with_ontos=True, with_readme=True, doc_count=1)

    discover_projects(
        scan_roots=[scan_root],
        exclude=[],
        registry_path=None,
    )

    captured = capsys.readouterr()
    assert captured.err == ""


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


def test_discover_projects_handles_slug_collisions(tmp_path, capsys):
    root_one = tmp_path / "DevA"
    root_two = tmp_path / "DevB"
    root_one.mkdir()
    root_two.mkdir()

    _make_project(root_one / "sample-app", with_ontos=True, with_readme=True, doc_count=5)
    collided_path = _make_project(root_two / "sample-app", with_ontos=True, with_readme=True, doc_count=5)

    projects = discover_projects(
        scan_roots=[root_one, root_two],
        exclude=[],
        registry_path=None,
    )

    captured = capsys.readouterr()
    slugs = sorted(entry.slug for entry in projects)
    assert slugs == ["sample-app", "sample-app-2"]
    assert captured.err.strip() == (
        f"[ontos] slug collision: 'sample-app' -> 'sample-app-2' "
        f"for workspace '{collided_path}'"
    )


def test_discover_projects_triple_slug_collision_emits_one_warning_per_suffix(tmp_path, capsys):
    roots = [tmp_path / name for name in ("DevA", "DevB", "DevC")]
    for root in roots:
        root.mkdir()
        _make_project(root / "sample-app", with_ontos=True, with_readme=True, doc_count=1)

    projects = discover_projects(
        scan_roots=roots,
        exclude=[],
        registry_path=None,
    )

    captured = capsys.readouterr()
    warnings = [line for line in captured.err.splitlines() if line]
    assert sorted(entry.slug for entry in projects) == ["sample-app", "sample-app-2", "sample-app-3"]
    assert warnings == [
        f"[ontos] slug collision: 'sample-app' -> 'sample-app-2' for workspace '{(roots[1] / 'sample-app').resolve()}'",
        f"[ontos] slug collision: 'sample-app' -> 'sample-app-3' for workspace '{(roots[2] / 'sample-app').resolve()}'",
    ]


def test_discover_projects_repeated_calls_reemit_collision_warnings(tmp_path, capsys):
    root_one = tmp_path / "DevA"
    root_two = tmp_path / "DevB"
    root_one.mkdir()
    root_two.mkdir()
    _make_project(root_one / "sample-app", with_ontos=True, with_readme=True, doc_count=1)
    collided_path = _make_project(root_two / "sample-app", with_ontos=True, with_readme=True, doc_count=1)

    discover_projects(scan_roots=[root_one, root_two], exclude=[], registry_path=None)
    first = capsys.readouterr()
    discover_projects(scan_roots=[root_one, root_two], exclude=[], registry_path=None)
    second = capsys.readouterr()

    expected = (
        f"[ontos] slug collision: 'sample-app' -> 'sample-app-2' "
        f"for workspace '{collided_path.resolve()}'"
    )
    assert first.err.strip() == expected
    assert second.err.strip() == expected


@pytest.mark.parametrize(
    "payload_factory",
    [
        lambda entry: [entry],
        lambda entry: {"projects": [entry]},
        lambda entry: {"workspaces": [entry]},
        lambda entry: {"entries": [entry]},
        lambda entry: {"items": [entry]},
        lambda entry: {"alpha-project": entry},
    ],
)
def test_load_registry_records_supports_multiple_shapes(tmp_path, payload_factory):
    dev_root = tmp_path / "Dev"
    dev_root.mkdir()
    project_path = _make_project(dev_root / "alpha", with_ontos=True, with_readme=True, doc_count=1)
    entry = {"path": str(project_path), "status": "documented", "has_ontos": "false"}

    registry_path = tmp_path / ".dev-hub" / "registry" / "projects.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(json.dumps(payload_factory(entry)), encoding="utf-8")

    records = load_registry_records(registry_path, tolerate_errors=False)

    assert len(records) == 1
    assert records[0].path == project_path
    assert records[0].status == "documented"
    assert records[0].has_ontos_raw == "false"


def test_load_registry_records_dict_fallback_skips_top_level_metadata(tmp_path):
    """m-1: when the registry is a dict keyed by slug, top-level metadata
    fields must NOT be ingested as projects. Only nested mappings that carry
    a path-shaped field qualify.
    """
    dev_root = tmp_path / "Dev"
    dev_root.mkdir()
    project_path = _make_project(dev_root / "alpha", with_ontos=True, with_readme=True, doc_count=1)
    registry_path = tmp_path / ".dev-hub" / "registry" / "projects.json"
    registry_path.parent.mkdir(parents=True)

    # Mix of a legitimate project entry + reserved top-level keys + a random
    # metadata dict that should NOT be pulled in as a project.
    registry_payload = {
        "dev_root": str(dev_root),
        "version": "1.0",
        "metadata": {"generator": "hand", "generated_at": "2026-01-01T00:00:00Z"},
        "alpha-project": {
            "path": str(project_path),
            "status": "documented",
            "has_ontos": True,
        },
        # Dict-valued entry with no path-like field: previously would have been
        # ingested as a "project" with no path (caller quietly dropped it);
        # the new filter skips it at extraction time instead.
        "broken-entry": {"note": "not a project, no path here"},
    }
    registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

    records = load_registry_records(registry_path, tolerate_errors=False)

    # Exactly one record survives: the real project.
    assert len(records) == 1
    assert records[0].path == project_path


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
