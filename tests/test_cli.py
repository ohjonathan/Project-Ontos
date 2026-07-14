"""Tests for unified CLI dispatcher (v3.0)."""

import json
import subprocess
import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


class TestUnifiedCLI:
    """Test the ontos CLI dispatcher."""

    def run_cli(self, *args):
        """Helper to run ontos CLI with given arguments."""
        result = subprocess.run(
            [sys.executable, '-m', 'ontos'] + list(args),
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result

    def test_no_args_shows_help(self):
        """Running with no arguments should show help."""
        result = self.run_cli()
        assert result.returncode == 2
        assert 'usage:' in result.stdout.lower() or 'usage:' in result.stderr.lower()

    def test_no_args_json_returns_envelope(self):
        """No command in JSON mode should return E_NO_COMMAND envelope."""
        result = self.run_cli('--json')
        assert result.returncode == 2
        payload = result.stdout.strip()
        assert payload
        data = json.loads(payload)
        assert data["status"] == "error"
        assert data["exit_code"] == 2
        assert data["error"]["code"] == "E_NO_COMMAND"

    def test_version_flag(self):
        """--version should show version and return 0."""
        result = self.run_cli('--version')
        assert result.returncode == 0
        # Version output goes to stdout
        assert '3.0' in result.stdout or 'ontos' in result.stdout.lower()

    def test_version_short_flag(self):
        """-V should also show version."""
        result = self.run_cli('-V')
        assert result.returncode == 0

    def test_unknown_command(self):
        """Unknown command should return non-zero with error message."""
        result = self.run_cli('nonexistent')
        assert result.returncode != 0
        # argparse outputs to stderr
        assert 'invalid choice' in result.stderr


class TestCLIArgumentPassthrough:
    """Test that arguments are passed through to subcommands correctly."""

    def run_cli(self, *args, cwd=None):
        """Helper to run ontos CLI with given arguments."""
        result = subprocess.run(
            [sys.executable, '-m', 'ontos'] + list(args),
            cwd=cwd or Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result

    def test_map_quiet_flag_passthrough(self, tmp_path):
        """--quiet flag should pass through to map command."""
        (tmp_path / ".ontos.toml").write_text(
            "[ontos]\nversion = '3.0'\n",
            encoding="utf-8",
        )
        (tmp_path / "docs").mkdir()
        result = self.run_cli('map', '--quiet', cwd=tmp_path)
        # Should not error on the flag (may fail for other reasons like no git repo)
        assert 'unrecognized arguments: --quiet' not in result.stderr.lower()

class TestCLIModuleStructure:
    """Test that the CLI module is structured correctly."""

    def test_ontos_cli_exists_in_package(self):
        """ontos/cli.py should exist in the ontos package."""
        cli_path = PROJECT_ROOT / 'ontos' / 'cli.py'
        assert cli_path.exists(), "ontos/cli.py should exist in ontos package"

    def test_ontos_main_exists(self):
        """ontos/__main__.py should exist for python -m ontos."""
        main_path = PROJECT_ROOT / 'ontos' / '__main__.py'
        assert main_path.exists(), "ontos/__main__.py should exist"

    def test_cli_has_main_function(self):
        """ontos.cli should have a main() function."""
        from ontos.cli import main
        assert callable(main), "ontos.cli.main should be callable"

    def test_cli_has_parser(self):
        """ontos.cli should have argument parser setup."""
        from ontos import cli
        assert hasattr(cli, 'main'), "cli module should have main function"


class TestCLICommands:
    """Test that all expected v3.0 commands are available."""

    def run_cli(self, *args):
        """Helper to run ontos CLI with given arguments."""
        result = subprocess.run(
            [sys.executable, '-m', 'ontos'] + list(args),
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result


class TestLegacyScriptExecution:
    """Test that fixed legacy scripts execute without ModuleNotFoundError.

    These tests verify the v3.0.2 fixes for sys.path shadowing issues where
    ontos/_scripts/ontos.py was shadowing the ontos package.
    """

    def run_cli(self, *args):
        """Helper to run ontos CLI with given arguments."""
        result = subprocess.run(
            [sys.executable, '-m', 'ontos'] + list(args),
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result

    def test_scaffold_executes(self):
        """scaffold command should execute without import errors."""
        result = self.run_cli('scaffold')
        # Should NOT have ModuleNotFoundError
        assert 'ModuleNotFoundError' not in result.stderr
        assert "'ontos' is not a package" not in result.stderr

    def test_promote_executes(self):
        """promote command should execute without import errors."""
        result = self.run_cli('promote', '--check')
        assert 'ModuleNotFoundError' not in result.stderr
        assert "'ontos' is not a package" not in result.stderr

    def test_migrate_executes(self):
        """migrate command should execute without import errors."""
        result = self.run_cli('migrate', '--check')
        assert 'ModuleNotFoundError' not in result.stderr
        assert "'ontos' is not a package" not in result.stderr
