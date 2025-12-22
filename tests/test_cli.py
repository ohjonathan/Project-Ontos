"""Tests for unified CLI dispatcher (v2.8.5)."""

import subprocess
import sys
import os
import pytest
from pathlib import Path

# Project root where ontos.py lives
PROJECT_ROOT = Path(__file__).parent.parent


class TestUnifiedCLI:
    """Test the ontos.py CLI dispatcher."""

    def run_cli(self, *args):
        """Helper to run ontos.py with given arguments."""
        result = subprocess.run(
            [sys.executable, 'ontos.py'] + list(args),
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
        assert 'Usage:' in result.stdout
        assert 'Commands:' in result.stdout
        assert 'log' in result.stdout
        assert 'map' in result.stdout

    def test_help_short_flag(self):
        """-h should also show help."""
        result = self.run_cli('-h')
        assert result.returncode == 0
        assert 'Usage:' in result.stdout

    def test_no_args_shows_help(self):
        """Running with no arguments should show help."""
        result = self.run_cli()
        assert result.returncode == 0
        assert 'Usage:' in result.stdout

    def test_version_flag(self):
        """--version should show version and return 0."""
        result = self.run_cli('--version')
        assert result.returncode == 0
        assert 'Ontos' in result.stdout

    def test_version_short_flag(self):
        """-V should also show version."""
        result = self.run_cli('-V')
        assert result.returncode == 0
        assert 'Ontos' in result.stdout

    def test_unknown_command(self):
        """Unknown command should return 1 with error message."""
        result = self.run_cli('nonexistent')
        assert result.returncode == 1
        assert 'Unknown command' in result.stdout
        assert 'Available commands' in result.stdout

    def test_alias_archive_to_log(self):
        """'archive' alias should resolve to 'log' command."""
        # Just test that it doesn't fail as "unknown command"
        result = self.run_cli('archive', '--help')
        assert result.returncode == 0
        # Should show the end_session help, not "unknown command"
        assert 'Unknown command' not in result.stdout

    def test_alias_session_to_log(self):
        """'session' alias should resolve to 'log' command."""
        result = self.run_cli('session', '--help')
        assert result.returncode == 0
        assert 'Unknown command' not in result.stdout

    def test_alias_context_to_map(self):
        """'context' alias should resolve to 'map' command."""
        result = self.run_cli('context', '--help')
        assert result.returncode == 0
        assert 'Unknown command' not in result.stdout

    def test_alias_generate_to_map(self):
        """'generate' alias should resolve to 'map' command."""
        result = self.run_cli('generate', '--help')
        assert result.returncode == 0
        assert 'Unknown command' not in result.stdout

    def test_alias_check_to_verify(self):
        """'check' alias should resolve to 'verify' command."""
        result = self.run_cli('check', '--help')
        assert result.returncode == 0
        assert 'Unknown command' not in result.stdout

    def test_alias_maintenance_to_maintain(self):
        """'maintenance' alias should resolve to 'maintain' command."""
        result = self.run_cli('maintenance', '--help')
        assert result.returncode == 0
        assert 'Unknown command' not in result.stdout

    def test_alias_archive_old_to_consolidate(self):
        """'archive-old' alias should resolve to 'consolidate' command."""
        result = self.run_cli('archive-old', '--help')
        assert result.returncode == 0
        assert 'Unknown command' not in result.stdout

    def test_alias_search_to_query(self):
        """'search' alias should resolve to 'query' command."""
        result = self.run_cli('search', '--help')
        assert result.returncode == 0
        assert 'Unknown command' not in result.stdout

    def test_alias_find_to_query(self):
        """'find' alias should resolve to 'query' command."""
        result = self.run_cli('find', '--help')
        assert result.returncode == 0
        assert 'Unknown command' not in result.stdout

    def test_alias_upgrade_to_update(self):
        """'upgrade' alias should resolve to 'update' command."""
        result = self.run_cli('upgrade', '--help')
        assert result.returncode == 0
        assert 'Unknown command' not in result.stdout

    def test_command_log_help(self):
        """'log' command should respond to --help."""
        result = self.run_cli('log', '--help')
        assert result.returncode == 0
        # Should show ontos_end_session.py help text
        assert 'session' in result.stdout.lower() or 'log' in result.stdout.lower()

    def test_command_map_help(self):
        """'map' command should respond to --help."""
        result = self.run_cli('map', '--help')
        assert result.returncode == 0
        assert 'context' in result.stdout.lower() or 'map' in result.stdout.lower()

    def test_command_verify_help(self):
        """'verify' command should respond to --help."""
        result = self.run_cli('verify', '--help')
        assert result.returncode == 0

    def test_command_maintain_help(self):
        """'maintain' command should respond to --help."""
        result = self.run_cli('maintain', '--help')
        assert result.returncode == 0

    def test_command_consolidate_help(self):
        """'consolidate' command should respond to --help."""
        result = self.run_cli('consolidate', '--help')
        assert result.returncode == 0

    def test_command_query_help(self):
        """'query' command should respond to --help."""
        result = self.run_cli('query', '--help')
        assert result.returncode == 0

    def test_command_update_help(self):
        """'update' command should respond to --help."""
        result = self.run_cli('update', '--help')
        assert result.returncode == 0

    def test_all_aliases_resolve(self):
        """All defined aliases should resolve without 'unknown command' error."""
        aliases = [
            'archive', 'session',      # → log
            'context', 'generate',      # → map
            'check',                    # → verify
            'maintenance',              # → maintain
            'archive-old',              # → consolidate
            'search', 'find',           # → query
            'upgrade',                  # → update
        ]
        for alias in aliases:
            result = self.run_cli(alias, '--help')
            assert result.returncode == 0, f"Alias '{alias}' failed"
            assert 'Unknown command' not in result.stdout, f"Alias '{alias}' not resolved"


class TestCLIArgumentPassthrough:
    """Test that arguments are passed through to subcommands correctly."""

    def run_cli(self, *args):
        """Helper to run ontos.py with given arguments."""
        result = subprocess.run(
            [sys.executable, 'ontos.py'] + list(args),
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result

    def test_map_strict_flag_passthrough(self):
        """--strict flag should pass through to map command."""
        # This should run but may fail validation - we just check it doesn't error on the flag
        result = self.run_cli('map', '--strict', '--quiet')
        # Return code depends on validation results, but should not be a CLI error
        # Just verify it attempted to run (no import error, no unknown flag error)
        assert 'Unknown command' not in result.stdout
        assert 'unrecognized arguments' not in result.stderr.lower()

    def test_map_quiet_flag_passthrough(self):
        """--quiet flag should pass through to map command."""
        result = self.run_cli('map', '--quiet')
        assert 'Unknown command' not in result.stdout
        assert 'unrecognized arguments' not in result.stderr.lower()

    def test_verify_all_flag_passthrough(self):
        """--all flag should pass through to verify command."""
        result = self.run_cli('verify', '--all')
        # verify --all will interactively verify, but should not error
        assert 'Unknown command' not in result.stdout
        assert 'unrecognized arguments' not in result.stderr.lower()

    def test_consolidate_dry_run_passthrough(self):
        """--dry-run flag should pass through to consolidate command."""
        result = self.run_cli('consolidate', '--dry-run')
        assert 'Unknown command' not in result.stdout
        assert 'unrecognized arguments' not in result.stderr.lower()


class TestCLIModuleStructure:
    """Test that the CLI module is structured correctly."""

    def test_ontos_py_exists_in_project_root(self):
        """ontos.py should exist in the project root."""
        ontos_path = PROJECT_ROOT / 'ontos.py'
        assert ontos_path.exists(), "ontos.py should be in project root"

    def test_ontos_py_not_in_scripts(self):
        """ontos.py should NOT be in .ontos/scripts/."""
        scripts_path = PROJECT_ROOT / '.ontos' / 'scripts' / 'ontos.py'
        assert not scripts_path.exists(), "ontos.py should NOT be in .ontos/scripts/"

    def test_all_eleven_commands_defined(self):
        """All 11 commands should be defined in COMMANDS."""
        # Use importlib to explicitly load ontos.py from project root
        # (avoids conflict with .ontos/scripts/ontos/ package)
        import importlib.util
        spec = importlib.util.spec_from_file_location("ontos_cli", PROJECT_ROOT / "ontos.py")
        ontos_cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ontos_cli)
        
        expected_commands = {
            'log', 'map', 'verify', 'maintain', 'consolidate', 'query', 'update',
            'migrate',   # v2.9: schema migration
            'scaffold',  # v2.9.1: L0 scaffolding
            'stub',      # v2.9.1: L1 stub creation
            'promote',   # v2.9.1: L0/L1 to L2 promotion
        }
        actual_commands = set(ontos_cli.COMMANDS.keys())
        
        assert actual_commands == expected_commands, f"Commands mismatch: {actual_commands} != {expected_commands}"

    def test_all_thirteen_aliases_defined(self):
        """All 13 aliases should be defined in ALIASES."""
        # Use importlib to explicitly load ontos.py from project root
        import importlib.util
        spec = importlib.util.spec_from_file_location("ontos_cli", PROJECT_ROOT / "ontos.py")
        ontos_cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ontos_cli)
        
        expected_aliases = {
            'archive', 'session',       # → log
            'context', 'generate',      # → map
            'check',                    # → verify
            'maintenance',              # → maintain
            'archive-old',              # → consolidate
            'search', 'find',           # → query
            'upgrade',                  # → update
            'schema',                   # → migrate (v2.9)
            'curate',                   # → scaffold (v2.9.1)
        }
        actual_aliases = set(ontos_cli.ALIASES.keys())
        
        assert actual_aliases == expected_aliases, f"Aliases mismatch: {actual_aliases} != {expected_aliases}"
