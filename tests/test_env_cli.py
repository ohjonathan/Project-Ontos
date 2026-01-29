import subprocess
import sys
import json
from pathlib import Path
import pytest

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


class TestEnvIntegration:
    """Integration tests for 'ontos env' command."""

    def run_cli(self, *args, cwd=None):
        """Helper to run ontos CLI."""
        result = subprocess.run(
            [sys.executable, '-m', 'ontos'] + list(args),
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result

    def test_env_basic_detection(self, tmp_path):
        """Test basic detection in a temporary directory."""
        # Create a mock project
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")
        
        result = self.run_cli('env', cwd=tmp_path)
        assert result.returncode == 0
        assert "Environment Manifest Detection" in result.stdout
        assert "pyproject.toml" in result.stdout

    def test_env_json_output(self, tmp_path):
        """Test --format json output."""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        
        result = self.run_cli('env', '--format', 'json', cwd=tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["$schema"] == "ontos-env-v1"
        assert len(data["manifests"]) == 1
        assert data["manifests"][0]["path"] == "package.json"

    def test_env_write_flag(self, tmp_path):
        """Test --write flag creates the file."""
        (tmp_path / ".tool-versions").write_text("python 3.9")
        
        result = self.run_cli('env', '--write', cwd=tmp_path)
        assert result.returncode == 0
        
        env_md = tmp_path / ".ontos" / "environment.md"
        assert env_md.exists()
        assert "# Environment Setup" in env_md.read_text()

    def test_env_force_flag(self, tmp_path):
        """Test --force flag for overwriting."""
        ontos_dir = tmp_path / ".ontos"
        ontos_dir.mkdir()
        env_md = ontos_dir / "environment.md"
        env_md.write_text("old content")
        
        # Should fail without --force
        result = self.run_cli('env', '--write', cwd=tmp_path)
        assert result.returncode == 1
        assert "already exists" in result.stdout or "already exists" in result.stderr
        
        # Should succeed with --force
        result = self.run_cli('env', '--write', '--force', cwd=tmp_path)
        assert result.returncode == 0
        assert env_md.read_text() != "old content"

    def test_env_parse_warnings(self, tmp_path):
        """Test that parse warnings are shown."""
        (tmp_path / "package.json").write_text("{ malformed }")
        
        result = self.run_cli('env', cwd=tmp_path)
        assert result.returncode == 0
        assert "Parse Warnings:" in result.stdout
        assert "package.json" in result.stdout
