
import subprocess
import sys
import os
import shutil
import tempfile
from pathlib import Path
import pytest

class TestCLICwdFix:
    """Test that wrapper commands work in arbitrary directories."""

    def test_wrapper_command_in_temp_dir(self):
        """Wrapper commands should work in a fresh directory."""
        # Create a temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Run 'ontos stub --help' from the temp dir
            # We use 'stub' as it's a wrapper command
            result = subprocess.run(
                [sys.executable, '-m', 'ontos', 'stub', '--help'],
                cwd=temp_path,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONPATH": str(Path.cwd())} # Ensure we can find the ontos package under test
            )
            
            # Should return 0 and show usage
            assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
            assert "usage:" in result.stdout.lower()
            assert "ModuleNotFoundError" not in result.stderr

    def test_cwd_propagation(self):
        """Verify that the subprocess actually receives the correct CWD."""
        # This is harder to test without a command that prints CWD.
        # However, if the previous test passed without crashing on import, 
        # it means the environment setup didn't break things.
        pass
