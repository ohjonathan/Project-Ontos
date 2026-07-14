"""Tests for export data command."""

import json
import subprocess
import sys
import pytest
from pathlib import Path


class TestExportDataCommand:
    """Tests for ontos export data command."""

    def test_export_data_to_file(self, tmp_path):
        """Export documents to JSON file."""
        # Setup project
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("---\nid: test\ntype: atom\nstatus: active\n---\n# Test\n")

        output = tmp_path / "export.json"

        result = subprocess.run(
            [sys.executable, "-m", "ontos", "export", "data", "-o", str(output)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0
        assert output.exists()

        data = json.loads(output.read_text())
        assert data["schema_version"] == "ontos-export-v1"
        assert len(data["documents"]) == 1
        assert data["documents"][0]["id"] == "test"

    def test_export_data_deterministic(self, tmp_path):
        """Deterministic mode produces stable output."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text("---\nid: aaa\ntype: atom\nstatus: active\n---\n")
        (docs / "b.md").write_text("---\nid: bbb\ntype: atom\nstatus: active\n---\n")

        out1 = tmp_path / "out1.json"
        out2 = tmp_path / "out2.json"

        # Run twice
        for out in [out1, out2]:
            subprocess.run(
                [sys.executable, "-m", "ontos", "export", "data", "--deterministic", "-o", str(out)],
                cwd=str(tmp_path)
            )

        # Should be identical
        assert out1.read_text() == out2.read_text()

    def test_export_data_type_filter(self, tmp_path):
        """Type filter restricts output."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "k.md").write_text("---\nid: k1\ntype: kernel\nstatus: active\n---\n")
        (docs / "a.md").write_text("---\nid: a1\ntype: atom\nstatus: active\n---\n")

        output = tmp_path / "export.json"

        result = subprocess.run(
            [sys.executable, "-m", "ontos", "export", "data", "--type", "kernel", "-o", str(output)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0
        data = json.loads(output.read_text())
        assert len(data["documents"]) == 1
        assert data["documents"][0]["type"] == "kernel"


class TestExportClaudeCommand:
    """Tests for ontos export claude command."""

    def test_export_claude_creates_file(self, tmp_path):
        """Export claude creates CLAUDE.md."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        (tmp_path / ".git").mkdir()  # Fake git repo

        result = subprocess.run(
            [sys.executable, "-m", "ontos", "export", "claude"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0
        assert (tmp_path / "CLAUDE.md").exists()


class TestExportDeprecation:
    """Tests for deprecated bare export command."""

    def test_bare_export_warns(self, tmp_path):
        """Bare 'ontos export' prints deprecation warning."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        (tmp_path / ".git").mkdir()

        result = subprocess.run(
            [sys.executable, "-m", "ontos", "export"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )

        # Should warn in stderr
        assert "deprecated" in result.stderr.lower()
        assert "export claude" in result.stderr
        assert "export data" in result.stderr
        assert "v3.4" not in result.stderr
