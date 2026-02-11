"""Tests for runtime root resolution in core.paths."""

from pathlib import Path

import pytest

from ontos.core import paths as paths_module


def _init_project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    (root / ".ontos.toml").write_text(
        "[project]\nname = 'test'\n[paths]\ndocs_dir = 'docs'\nlogs_dir = 'docs/logs'\n",
        encoding="utf-8",
    )
    (root / "docs" / "logs").mkdir(parents=True)
    return root


def test_get_logs_dir_resolves_runtime_root_from_subdirectory(tmp_path, monkeypatch):
    root = _init_project(tmp_path)
    nested = root / "docs" / "nested" / "deep"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    paths_module._discover_runtime_root_cached.cache_clear()

    logs_dir = paths_module.get_logs_dir()

    assert logs_dir == str(root / "docs" / "logs")


def test_get_logs_dir_raises_outside_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths_module._discover_runtime_root_cached.cache_clear()

    with pytest.raises(FileNotFoundError):
        paths_module.get_logs_dir()


def test_get_logs_dir_accepts_explicit_repo_root(tmp_path, monkeypatch):
    root = _init_project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)

    logs_dir = paths_module.get_logs_dir(repo_root=root)

    assert logs_dir == str(root / "docs" / "logs")


def test_runtime_root_discovery_uses_cache(tmp_path, monkeypatch):
    root = _init_project(tmp_path)
    nested = root / "x" / "y"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    paths_module._discover_runtime_root_cached.cache_clear()

    _ = paths_module.resolve_project_root()
    first = paths_module._discover_runtime_root_cached.cache_info()
    _ = paths_module.resolve_project_root()
    second = paths_module._discover_runtime_root_cached.cache_info()

    assert second.hits >= first.hits + 1
