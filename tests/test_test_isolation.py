"""Regression tests for test-runner import isolation."""

import sys
from pathlib import Path

import ontos


REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_SCRIPTS_DIR = (REPO_ROOT / ".ontos" / "scripts").resolve()


def test_legacy_scripts_directory_is_not_on_global_import_path():
    """Compatibility modules must not expose the vendored package globally."""
    resolved_entries = set()
    for entry in sys.path:
        try:
            resolved_entries.add(Path(entry).resolve())
        except (OSError, TypeError, ValueError):
            continue

    assert LEGACY_SCRIPTS_DIR not in resolved_entries


def test_package_under_test_is_not_the_vendored_legacy_copy():
    """The test session must retain one canonical Ontos package identity."""
    package_path = Path(ontos.__file__).resolve()
    assert package_path.is_relative_to(REPO_ROOT / "ontos")


def test_clean_clone_has_a_post_suite_repository_guard():
    source = (REPO_ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert "def pytest_sessionfinish" in source
    assert '"status", "--porcelain=v1", "--untracked-files=all"' in source


def test_mcp_helpers_do_not_shadow_the_external_mcp_package():
    assert not (REPO_ROOT / "tests" / "mcp" / "__init__.py").exists()
    source = (REPO_ROOT / "tests" / "mcp_helpers.py").read_text(encoding="utf-8")
    assert "sys.path" not in source
    assert "sys.modules" not in source
