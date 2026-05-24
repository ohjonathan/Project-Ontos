"""Tests for snapshot primitive."""

import pytest
from pathlib import Path
from ontos.core.snapshot import SnapshotFilters, DocumentSnapshot
from ontos.io.snapshot import create_snapshot


class TestCreateSnapshot:
    """Tests for create_snapshot function."""

    def test_create_snapshot_empty_project(self, tmp_path):
        """Snapshot of empty project has no documents."""
        # Create minimal config
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        (tmp_path / "docs").mkdir()

        snapshot = create_snapshot(tmp_path)

        assert isinstance(snapshot, DocumentSnapshot)
        assert len(snapshot.documents) == 0

    def test_create_snapshot_with_documents(self, tmp_path):
        """Snapshot includes parsed documents."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()

        doc = docs / "test.md"
        doc.write_text("""---
id: test_doc
type: atom
status: active
---
# Test Document
Content here.
""")

        snapshot = create_snapshot(tmp_path)

        assert "test_doc" in snapshot.documents
        assert snapshot.documents["test_doc"].content == "# Test Document\nContent here.\n"

    def test_create_snapshot_no_content(self, tmp_path):
        """Snapshot without content strips document bodies."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()

        doc = docs / "test.md"
        doc.write_text("""---
id: test_doc
type: atom
status: active
---
# Test Document
""")

        snapshot = create_snapshot(tmp_path, include_content=False)

        assert "test_doc" in snapshot.documents
        assert snapshot.documents["test_doc"].content == ""

    def test_create_snapshot_type_filter(self, tmp_path):
        """Filter by document type."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()

        (docs / "kernel.md").write_text("---\nid: k1\ntype: kernel\nstatus: active\n---\n")
        (docs / "atom.md").write_text("---\nid: a1\ntype: atom\nstatus: active\n---\n")

        filters = SnapshotFilters(types=["kernel"])
        snapshot = create_snapshot(tmp_path, filters=filters)

        assert "k1" in snapshot.documents
        assert "a1" not in snapshot.documents

    def test_create_snapshot_default_scope_excludes_internal_docs(self, tmp_path):
        """Default snapshot scope (docs) excludes .ontos-internal docs."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()
        internal = tmp_path / ".ontos-internal"
        internal.mkdir()

        (docs / "docs.md").write_text("---\nid: docs_doc\ntype: atom\nstatus: active\n---\n")
        (internal / "internal.md").write_text("---\nid: internal_doc\ntype: atom\nstatus: active\n---\n")

        snapshot = create_snapshot(tmp_path)

        assert "docs_doc" in snapshot.documents
        assert "internal_doc" not in snapshot.documents

    def test_create_snapshot_minimal_config_tolerates_orphan_log(self, tmp_path):
        """Minimal `[ontos]`-only config must NOT surface a standalone log
        doc as orphan. Snapshots back doctor and the MCP cache; preserving the
        pre-v4.7 default (``["atom", "log"]``) keeps the "default behavior
        unless .ontos.toml opts in" contract for those surfaces.
        """
        from ontos.core.types import ValidationErrorType

        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "session.md").write_text(
            "---\n"
            "id: log_session_abc\n"
            "type: log\n"
            "status: active\n"
            "event_type: chore\n"
            "source: pytest\n"
            "branch: main\n"
            "concepts: [docs]\n"
            "---\n"
        )

        snapshot = create_snapshot(tmp_path)

        orphan_warnings = [
            w for w in snapshot.validation_result.warnings
            if w.error_type == ValidationErrorType.ORPHAN
        ]
        assert orphan_warnings == [], (
            "log-type docs should be tolerated as orphans by default in the "
            "snapshot path; otherwise doctor/MCP would warn on every clean "
            "session log in projects without an explicit allowed_orphan_types."
        )

    def test_create_snapshot_library_scope_includes_internal_docs(self, tmp_path):
        """Library scope snapshot includes .ontos-internal docs."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()
        internal = tmp_path / ".ontos-internal"
        internal.mkdir()

        (docs / "docs.md").write_text("---\nid: docs_doc\ntype: atom\nstatus: active\n---\n")
        (internal / "internal.md").write_text("---\nid: internal_doc\ntype: atom\nstatus: active\n---\n")

        snapshot = create_snapshot(tmp_path, scope="library")

        assert "docs_doc" in snapshot.documents
        assert "internal_doc" in snapshot.documents


class TestSnapshotProperties:
    """Tests for DocumentSnapshot properties."""

    def test_by_type_groups_documents(self, tmp_path):
        """by_type property groups documents correctly."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()

        (docs / "k1.md").write_text("---\nid: k1\ntype: kernel\nstatus: active\n---\n")
        (docs / "k2.md").write_text("---\nid: k2\ntype: kernel\nstatus: active\n---\n")
        (docs / "a1.md").write_text("---\nid: a1\ntype: atom\nstatus: active\n---\n")

        snapshot = create_snapshot(tmp_path)

        assert len(snapshot.by_type.get("kernel", [])) == 2
        assert len(snapshot.by_type.get("atom", [])) == 1
