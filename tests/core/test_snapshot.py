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
