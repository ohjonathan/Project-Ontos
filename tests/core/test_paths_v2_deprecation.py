"""Compatibility contract for the v2 path API during the Ontos 5.x line."""

import warnings

import pytest

import ontos
import ontos.core
from ontos.core import paths


DEPRECATED_CALLABLES = (
    ("get_logs_dir", lambda root: paths.get_logs_dir(repo_root=root)),
    ("get_log_count", lambda root: paths.get_log_count(repo_root=root)),
    ("get_logs_older_than", lambda root: paths.get_logs_older_than(30, repo_root=root)),
    ("get_archive_dir", lambda root: paths.get_archive_dir(repo_root=root)),
    (
        "get_decision_history_path",
        lambda root: paths.get_decision_history_path(repo_root=root),
    ),
    ("get_proposals_dir", lambda root: paths.get_proposals_dir(repo_root=root)),
    ("get_archive_logs_dir", lambda root: paths.get_archive_logs_dir(repo_root=root)),
    (
        "get_archive_proposals_dir",
        lambda root: paths.get_archive_proposals_dir(repo_root=root),
    ),
    ("get_concepts_path", lambda root: paths.get_concepts_path(repo_root=root)),
    (
        "find_last_session_date",
        lambda root: paths.find_last_session_date(logs_dir=str(root / "missing-logs")),
    ),
)

DEPRECATED_COMPATIBILITY_NAMES = (
    "PROJECT_ROOT",
    *(name for name, _call in DEPRECATED_CALLABLES),
)


def test_legacy_path_import_surface_is_preserved_without_import_warnings():
    """All historically shipped import paths remain usable in v5.0.1."""
    assert len(DEPRECATED_COMPATIBILITY_NAMES) == 11

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")

        assert isinstance(paths.PROJECT_ROOT, str)
        for name, _call in DEPRECATED_CALLABLES:
            assert getattr(ontos, name) is getattr(paths, name)
            assert getattr(ontos.core, name) is getattr(paths, name)

    assert caught == []


@pytest.mark.parametrize(("name", "call"), DEPRECATED_CALLABLES)
def test_legacy_path_call_warns_and_keeps_working(name, call, tmp_path):
    """Callable compatibility APIs warn at use time without changing behavior."""
    with pytest.warns(
        DeprecationWarning,
        match=rf"ontos\.core\.paths\.{name}\(\).*removed in v6\.0\.0",
    ):
        call(tmp_path)


def test_supported_path_api_does_not_emit_v2_deprecation(tmp_path):
    """Current root/config helpers remain supported beyond the v2 cleanup."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)

        assert paths.resolve_project_root(repo_root=tmp_path) == tmp_path.resolve()
        assert paths.is_ontos_repo(repo_root=tmp_path) is False
        assert paths.resolve_config("MISSING_SETTING", "fallback", warn_legacy=False) == "fallback"

    assert [item for item in caught if item.category is DeprecationWarning] == []


def test_legacy_layout_warning_gives_current_manual_remediation(tmp_path):
    """Legacy-layout guidance no longer points at the deleted v2 init script."""
    docs_archive = tmp_path / "docs" / "archive"
    docs_archive.mkdir(parents=True)

    paths._deprecation_warned.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert paths.get_archive_logs_dir(repo_root=tmp_path) == str(docs_archive)

    messages = [str(item.message) for item in caught]
    assert any("pathlib.Path" in message for message in messages)
    assert all("ontos_init.py" not in message for message in messages)
