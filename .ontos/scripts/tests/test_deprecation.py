"""Tests for deprecation warning behavior (v2.9.2).

Note: TestOntosLibWarning removed in v3.0.1 after ontos_lib.py shim was deleted.
"""

import subprocess
import sys
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class TestDirectScriptWarning:
    """Test that direct script execution emits deprecation notice."""

    def test_direct_execution_emits_warning(self):
        """Running script directly should emit [DEPRECATION] notice."""
        # Clear the env var to ensure warning is shown
        env = {**os.environ}
        env.pop('ONTOS_CLI_DISPATCH', None)
        env.pop('ONTOS_NO_DEPRECATION_WARNINGS', None)
        
        result = subprocess.run(
            [sys.executable, '.ontos/scripts/ontos_end_session.py', '--help'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            env=env
        )
        assert '[DEPRECATION]' in result.stderr, \
            f"Expected [DEPRECATION] in stderr, got: {result.stderr}"

    def test_cli_dispatch_no_warning(self):
        """Running via ontos.py should NOT emit deprecation notice."""
        result = subprocess.run(
            [sys.executable, 'ontos.py', 'log', '--help'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        assert '[DEPRECATION]' not in result.stderr, \
            f"Did not expect [DEPRECATION] in stderr when using unified CLI, got: {result.stderr}"

    def test_suppression_env_var(self):
        """ONTOS_NO_DEPRECATION_WARNINGS=1 should suppress notice."""
        env = {**os.environ, 'ONTOS_NO_DEPRECATION_WARNINGS': '1'}
        env.pop('ONTOS_CLI_DISPATCH', None)  # Ensure not set via CLI
        
        result = subprocess.run(
            [sys.executable, '.ontos/scripts/ontos_end_session.py', '--help'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            env=env
        )
        assert '[DEPRECATION]' not in result.stderr, \
            f"ONTOS_NO_DEPRECATION_WARNINGS should suppress [DEPRECATION], got: {result.stderr}"


class TestMultipleScriptsDeprecation:
    """Test deprecation notice across multiple scripts."""
    
    @pytest.mark.parametrize("script,command", [
        ("ontos_generate_context_map.py", "map"),
        ("ontos_maintain.py", "maintain"),
        ("ontos_query.py", "query"),
    ])
    def test_script_deprecation_pattern(self, script, command):
        """Multiple scripts follow the deprecation pattern."""
        env = {**os.environ}
        env.pop('ONTOS_CLI_DISPATCH', None)
        env.pop('ONTOS_NO_DEPRECATION_WARNINGS', None)
        
        result = subprocess.run(
            [sys.executable, f'.ontos/scripts/{script}', '--help'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            env=env
        )
        
        # Should emit deprecation notice
        assert '[DEPRECATION]' in result.stderr
        # Should mention the proper command
        assert command in result.stderr
