"""Tests for migration-report command."""

import json
import subprocess
import sys
import pytest
from pathlib import Path


class TestMigrationReportCommand:
    """Tests for ontos migration-report command."""

    def test_migration_report_markdown(self, tmp_path):
        """Generate markdown report."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "k.md").write_text("---\nid: k1\ntype: kernel\nstatus: active\n---\n")
        (docs / "a.md").write_text("---\nid: a1\ntype: atom\nstatus: active\n---\n")

        output = tmp_path / "report.md"

        result = subprocess.run(
            [sys.executable, "-m", "ontos", "migration-report", "-o", str(output)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0
        assert output.exists()
        content = output.read_text()
        assert "# Migration Report" in content
        assert "Safe to migrate" in content or "Safe to Migrate" in content

    def test_migration_report_json(self, tmp_path):
        """Generate JSON report."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "k.md").write_text("---\nid: k1\ntype: kernel\nstatus: active\n---\n")

        output = tmp_path / "report.json"

        result = subprocess.run(
            [sys.executable, "-m", "ontos", "migration-report", "--format", "json", "-o", str(output)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0
        data = json.loads(output.read_text())
        assert data["schema_version"] == "ontos-migration-report-v1"
        assert "summary" in data
        assert "classifications" in data

    def test_global_json_flag_returns_structured_report_payload(self, tmp_path):
        """Global --json must not suppress the default Markdown payload."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "k.md").write_text(
            "---\nid: k1\ntype: kernel\nstatus: active\n---\n"
        )

        result = subprocess.run(
            [sys.executable, "-m", "ontos", "--json", "migration-report"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )

        assert result.returncode == 0, result.stderr
        assert result.stderr == ""
        envelope = json.loads(result.stdout)
        assert envelope["schema_version"] == "4.0"
        assert envelope["command"] == "migration-report"
        assert envelope["result"]["kind"] == "diagnostic"
        assert envelope["data"]["schema_version"] == "ontos-migration-report-v1"
        assert "summary" in envelope["data"]
        assert "classifications" in envelope["data"]

    def test_global_json_preserves_markdown_format_for_output_file(self, tmp_path):
        """Envelope JSON must not silently change an explicit file artifact."""
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "k.md").write_text(
            "---\nid: k1\ntype: kernel\nstatus: active\n---\n"
        )
        output = tmp_path / "report.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ontos",
                "--json",
                "migration-report",
                "--output",
                str(output),
            ],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )

        assert result.returncode == 0, result.stderr
        envelope = json.loads(result.stdout)
        assert envelope["data"] == {"output_path": str(output)}
        assert output.read_text().startswith("# Migration Report")


class TestMigrateConvenienceCommand:
    """Tests for ontos migrate convenience command."""

    def test_migrate_creates_artifacts(self, tmp_path):
        """Migrate creates both files."""
        config = tmp_path / ".ontos.toml"
        config.write_text("[ontos]\nversion = '3.2'\n")
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("---\nid: test\ntype: atom\nstatus: active\n---\n")

        out_dir = tmp_path / "migration"

        result = subprocess.run(
            [sys.executable, "-m", "ontos", "migrate", "--out-dir", str(out_dir)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0
        assert (out_dir / "snapshot.json").exists()
        assert (out_dir / "analysis.md").exists()
