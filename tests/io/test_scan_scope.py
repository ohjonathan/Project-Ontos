"""Tests for shared scan scope utilities."""

from pathlib import Path

import pytest

from ontos.core.config import default_config
from ontos.io.scan_scope import (
    ScanScope,
    build_scope_roots,
    collect_scoped_documents,
    resolve_scan_scope,
)


def test_resolve_scan_scope_precedence_cli_over_config():
    assert resolve_scan_scope("library", "docs") == ScanScope.LIBRARY


def test_resolve_scan_scope_uses_config_default():
    assert resolve_scan_scope(None, "library") == ScanScope.LIBRARY


def test_resolve_scan_scope_falls_back_to_docs():
    assert resolve_scan_scope(None, None) == ScanScope.DOCS


def test_resolve_scan_scope_invalid_falls_back_with_warning():
    with pytest.warns(RuntimeWarning):
        scope = resolve_scan_scope(None, "not-a-scope")
    assert scope == ScanScope.DOCS


def test_build_scope_roots_docs_and_scan_paths():
    config = default_config()
    config.paths.docs_dir = "manual"
    config.scanning.scan_paths = ["custom_docs", "more/docs"]

    roots = build_scope_roots(Path("/repo"), config, ScanScope.DOCS)
    assert roots == [
        Path("/repo/manual"),
        Path("/repo/custom_docs"),
        Path("/repo/more/docs"),
    ]


def test_build_scope_roots_library_adds_internal():
    config = default_config()
    roots = build_scope_roots(Path("/repo"), config, ScanScope.LIBRARY)
    assert Path("/repo/.ontos-internal") in roots


def test_collect_scoped_documents_docs_mode(tmp_path: Path):
    config = default_config()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# a")
    (tmp_path / ".ontos-internal").mkdir()
    (tmp_path / ".ontos-internal" / "b.md").write_text("# b")

    files = collect_scoped_documents(tmp_path, config, ScanScope.DOCS)

    assert [p.name for p in files] == ["a.md"]


def test_collect_scoped_documents_library_mode_includes_internal(tmp_path: Path):
    config = default_config()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# a")
    (tmp_path / ".ontos-internal").mkdir()
    (tmp_path / ".ontos-internal" / "b.md").write_text("# b")

    files = collect_scoped_documents(tmp_path, config, ScanScope.LIBRARY)

    assert {p.name for p in files} == {"a.md", "b.md"}


def test_collect_scoped_documents_library_mode_missing_internal_is_ok(tmp_path: Path):
    config = default_config()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# a")

    files = collect_scoped_documents(tmp_path, config, ScanScope.LIBRARY)

    assert [p.name for p in files] == ["a.md"]


def test_collect_scoped_documents_explicit_dirs_override_scope(tmp_path: Path):
    config = default_config()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# a")
    (tmp_path / "other").mkdir()
    (tmp_path / "other" / "x.md").write_text("# x")

    files = collect_scoped_documents(
        tmp_path,
        config,
        ScanScope.DOCS,
        explicit_dirs=[Path("other")],
    )

    assert [p.name for p in files] == ["x.md"]


def test_collect_scoped_documents_respects_docs_path_override(tmp_path: Path):
    config = default_config()
    config.paths.docs_dir = "knowledge"
    (tmp_path / "knowledge").mkdir()
    (tmp_path / "knowledge" / "a.md").write_text("# a")

    files = collect_scoped_documents(tmp_path, config, ScanScope.DOCS)

    assert [p.name for p in files] == ["a.md"]
