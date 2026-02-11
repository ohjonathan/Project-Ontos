"""Tests for migration classification."""

import pytest
from pathlib import Path
from ontos.io.snapshot import create_snapshot
from ontos.core.migration import classify_documents, MigrationReport


class TestClassifyDocuments:
    """Tests for classify_documents function."""

    def test_atom_classified_as_rewrite(self, tmp_path):
        """Atom documents are classified as rewrite."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()

        (docs / "atom.md").write_text("---\nid: a1\ntype: atom\nstatus: active\n---\n")

        snapshot = create_snapshot(tmp_path)
        report = classify_documents(snapshot)

        assert report.classifications["a1"].inferred_status == "rewrite"
        assert report.classifications["a1"].effective_status == "rewrite"

    def test_kernel_classified_as_safe(self, tmp_path):
        """Kernel documents are classified as safe."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()

        (docs / "kernel.md").write_text("---\nid: k1\ntype: kernel\nstatus: active\n---\n")

        snapshot = create_snapshot(tmp_path)
        report = classify_documents(snapshot)

        assert report.classifications["k1"].inferred_status == "safe"

    def test_doc_depending_on_atom_classified_as_review(self, tmp_path):
        """Documents depending on atoms are classified as review."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()

        (docs / "atom.md").write_text("---\nid: a1\ntype: atom\nstatus: active\n---\n")
        (docs / "product.md").write_text("---\nid: p1\ntype: product\nstatus: active\ndepends_on: [a1]\n---\n")

        snapshot = create_snapshot(tmp_path)
        report = classify_documents(snapshot)

        assert report.classifications["p1"].inferred_status == "review"
        assert "a1" in report.classifications["p1"].atom_dependencies

    def test_override_respected(self, tmp_path):
        """migration_status override is respected."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()

        (docs / "atom.md").write_text("---\nid: a1\ntype: atom\nstatus: active\n---\n")
        (docs / "product.md").write_text("""---
id: p1
type: product
status: active
depends_on: [a1]
migration_status: safe
migration_status_reason: API is abstract enough
---
""")

        snapshot = create_snapshot(tmp_path)
        report = classify_documents(snapshot)

        assert report.classifications["p1"].inferred_status == "review"
        assert report.classifications["p1"].effective_status == "safe"
        assert report.classifications["p1"].override == "safe"

    def test_downgrade_warning(self, tmp_path):
        """Downgrade override emits warning."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()

        (docs / "atom.md").write_text("---\nid: a1\ntype: atom\nstatus: active\n---\n")
        (docs / "product.md").write_text("""---
id: p1
type: product
status: active
depends_on: [a1]
migration_status: safe
---
""")

        snapshot = create_snapshot(tmp_path)
        report = classify_documents(snapshot)

        # Should have warning about downgrade
        assert len(report.warnings) > 0
        assert any(w["type"] == "override_downgrade" for w in report.warnings)

    def test_summary_counts(self, tmp_path):
        """Summary has correct counts."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()

        (docs / "k1.md").write_text("---\nid: k1\ntype: kernel\nstatus: active\n---\n")
        (docs / "k2.md").write_text("---\nid: k2\ntype: kernel\nstatus: active\n---\n")
        (docs / "a1.md").write_text("---\nid: a1\ntype: atom\nstatus: active\n---\n")

        snapshot = create_snapshot(tmp_path)
        report = classify_documents(snapshot)

        assert report.summary["safe"] == 2
        assert report.summary["rewrite"] == 1
