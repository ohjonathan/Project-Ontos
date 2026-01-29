"""Tests for unified CLI dispatcher (v3.0)."""

import subprocess
import sys
import pytest
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

    def test_help_flag(self):
        """--help should show usage and return 0."""
        result = self.run_cli('--help')
        assert result.returncode == 0
        assert 'usage:' in result.stdout.lower()
        assert 'log' in result.stdout
        assert 'map' in result.stdout

    def test_help_short_flag(self):
        """-h should also show help."""
        result = self.run_cli('-h')
        assert result.returncode == 0
        assert 'usage:' in result.stdout.lower()

    def test_no_args_shows_help(self):
        """Running with no arguments should show help."""
        result = self.run_cli()
        # argparse may return non-zero for no args, but should show usage
        assert 'usage:' in result.stdout.lower() or 'usage:' in result.stderr.lower()

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

    # Test all v3.0 commands respond to --help
    @pytest.mark.parametrize("command", [
        'init', 'map', 'log', 'doctor', 'agents', 'export', 'hook',
        'verify', 'query', 'migrate', 'consolidate', 'promote', 'scaffold', 'stub', 'env'
    ])
    def test_command_help(self, command):
        """Each command should respond to --help."""
        result = self.run_cli(command, '--help')
        assert result.returncode == 0, f"Command '{command}' --help failed"
        assert 'usage:' in result.stdout.lower(), f"Command '{command}' didn't show usage"


class TestCLIArgumentPassthrough:
    """Test that arguments are passed through to subcommands correctly."""

    def run_cli(self, *args):
        """Helper to run ontos CLI with given arguments."""
        result = subprocess.run(
            [sys.executable, '-m', 'ontos'] + list(args),
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result

    def test_map_quiet_flag_passthrough(self):
        """--quiet flag should pass through to map command."""
        result = self.run_cli('map', '--quiet')
        # Should not error on the flag (may fail for other reasons like no git repo)
        assert 'unrecognized arguments: --quiet' not in result.stderr.lower()

    def test_global_quiet_flag(self):
        """Global --quiet flag should work."""
        result = self.run_cli('--quiet', 'map', '--help')
        assert result.returncode == 0


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

    def test_all_commands_listed_in_help(self):
        """All v3.0 commands should appear in --help output."""
        result = self.run_cli('--help')
        expected_commands = [
            'init', 'map', 'log', 'doctor', 'agents', 'export', 'hook',
            'verify', 'query', 'migrate', 'consolidate', 'promote', 'scaffold', 'stub', 'env'
        ]
        for cmd in expected_commands:
            assert cmd in result.stdout, f"Command '{cmd}' not in help output"

    def test_doctor_runs(self):
        """doctor command should run without crashing."""
        result = self.run_cli('doctor', '--help')
        assert result.returncode == 0

    def test_agents_runs(self):
        """agents command should run without crashing."""
        result = self.run_cli('agents', '--help')
        assert result.returncode == 0


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

    def test_stub_executes(self):
        """stub command should execute without import errors."""
        result = self.run_cli('stub', '--help')
        assert 'ModuleNotFoundError' not in result.stderr
        assert result.returncode == 0

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
