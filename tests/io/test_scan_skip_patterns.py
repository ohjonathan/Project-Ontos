"""(#181 slice-0) Skip-pattern semantics for document scanning.

Directory patterns such as the default ``archive/*`` must exclude the whole
subtree — including the nested ``docs/archive/logs/`` layout that
``ontos consolidate`` itself writes — not just direct children.
"""

from pathlib import Path

from ontos.core.config import default_config
from ontos.io.files import scan_documents
from ontos.io.scan_scope import ScanScope, collect_scoped_documents


def _touch(root: Path, rel: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {rel}\n")
    return path


DEFAULT_SKIPS = ["_template.md", "archive/*", ".git/*", "node_modules/*", "__pycache__/*"]


def _scanned_names(tmp_path: Path) -> set:
    results = scan_documents([tmp_path / "docs"], skip_patterns=DEFAULT_SKIPS)
    return {p.relative_to(tmp_path).as_posix() for p in results}


class TestArchiveSubtreeExclusion:
    def test_flat_archive_layout_excluded(self, tmp_path):
        _touch(tmp_path, "docs/keep.md")
        _touch(tmp_path, "docs/archive/old.md")

        assert _scanned_names(tmp_path) == {"docs/keep.md"}

    def test_nested_archive_logs_layout_excluded(self, tmp_path):
        # The layout `ontos consolidate` writes by default.
        _touch(tmp_path, "docs/keep.md")
        _touch(tmp_path, "docs/archive/logs/2026-01-01_old-session.md")
        _touch(tmp_path, "docs/archive/logs/deeper/even-older.md")

        assert _scanned_names(tmp_path) == {"docs/keep.md"}

    def test_node_modules_subtree_excluded(self, tmp_path):
        _touch(tmp_path, "docs/keep.md")
        _touch(tmp_path, "docs/node_modules/pkg/README.md")

        assert _scanned_names(tmp_path) == {"docs/keep.md"}

    def test_basename_pattern_stays_exact(self, tmp_path):
        # `_template.md` must not over-match files merely ending in the same
        # suffix.
        _touch(tmp_path, "docs/_template.md")
        _touch(tmp_path, "docs/spec_template.md")

        assert _scanned_names(tmp_path) == {"docs/spec_template.md"}

    def test_archive_named_file_not_excluded(self, tmp_path):
        # A FILE named archive.md is not the archive/ directory.
        _touch(tmp_path, "docs/archive.md")

        assert _scanned_names(tmp_path) == {"docs/archive.md"}

    def test_ancestor_directory_names_never_participate(self, tmp_path):
        # PR #182 review P1: a checkout under an ancestor directory named
        # 'archive' (or node_modules, __pycache__, …) must not have the
        # default patterns wipe out the entire scan.
        workspace = tmp_path / "archive" / "node_modules" / "project"
        _touch(workspace, "docs/keep.md")
        _touch(workspace, "docs/archive/logs/old.md")

        results = scan_documents(
            [workspace / "docs"],
            skip_patterns=DEFAULT_SKIPS,
            workspace_root=workspace,
        )
        names = {p.relative_to(workspace.resolve()).as_posix() for p in results}
        assert names == {"docs/keep.md"}

        # Same guarantee without an explicit workspace_root: the scan root
        # is the relativization base.
        results = scan_documents([workspace / "docs"], skip_patterns=DEFAULT_SKIPS)
        names = {p.relative_to(workspace.resolve()).as_posix() for p in results}
        assert names == {"docs/keep.md"}

    def test_custom_file_patterns_stay_non_recursive(self, tmp_path):
        # PR #182 review P1: 'reviews/*.md' must not silently become
        # recursive — '*' stays within one segment.
        _touch(tmp_path, "docs/reviews/draft.md")
        _touch(tmp_path, "docs/reviews/team/nested.md")

        results = scan_documents(
            [tmp_path / "docs"],
            skip_patterns=["reviews/*.md"],
            workspace_root=tmp_path,
        )
        names = {p.relative_to(tmp_path.resolve()).as_posix() for p in results}
        assert names == {"docs/reviews/team/nested.md"}

    def test_explicit_double_star_matches_subtree(self, tmp_path):
        _touch(tmp_path, "docs/reviews/draft.md")
        _touch(tmp_path, "docs/reviews/team/nested.md")
        _touch(tmp_path, "docs/keep.md")

        results = scan_documents(
            [tmp_path / "docs"],
            skip_patterns=["reviews/**"],
            workspace_root=tmp_path,
        )
        names = {p.relative_to(tmp_path.resolve()).as_posix() for p in results}
        assert names == {"docs/keep.md"}

    def test_default_config_scope_excludes_nested_archive(self, tmp_path):
        # End-to-end through the shared scope collector with the shipped
        # default configuration.
        config = default_config()
        _touch(tmp_path, "docs/keep.md")
        _touch(tmp_path, "docs/archive/logs/2026-01-01_old.md")

        documents = collect_scoped_documents(
            tmp_path,
            config,
            ScanScope.DOCS,
            base_skip_patterns=config.scanning.skip_patterns,
        )

        names = {p.relative_to(tmp_path.resolve()).as_posix() for p in documents}
        assert names == {"docs/keep.md"}
