import os
import sys
import subprocess
import pytest
from pathlib import Path

def test_consolidate_cli_no_crash(tmp_path):
    """B1 Regression: Ensure consolidate CLI invocation doesn't crash on imports."""
    # Setup mock ontos project
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".ontos").mkdir()
    
    # Run consolidate --dry-run
    # We use PYTHONPATH to make sure the package is found
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    result = subprocess.run(
        [sys.executable, "-m", "ontos", "consolidate", "--dry-run"],
        cwd=str(project_root),
        env=env,
        capture_output=True,
        text=True
    )
    
    # Should not crash (exit code 0 or 1 if no logs found, but not a crash)
    assert "Found 0 log(s) to consolidate" in result.stdout or result.returncode == 0
    assert "ModuleNotFoundError" not in result.stderr
    assert "No module named 'ontos_config_defaults'" not in result.stderr
