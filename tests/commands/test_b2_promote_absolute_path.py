import os
import sys
import subprocess
import pytest
from pathlib import Path

def test_promote_absolute_path_no_crash(tmp_path):
    """B2 Regression: Ensure promote handles absolute paths outside root without crashing."""
    # Setup mock ontos project
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".ontos").mkdir()
    
    # Create a file outside the project root
    external_file = tmp_path / "external_doc.md"
    external_file.write_text("---\nid: external\ntype: reference\nstatus: draft\n---\nBody")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    result = subprocess.run(
        [sys.executable, "-m", "ontos", "promote", str(external_file), "--check"],
        cwd=str(project_root),
        env=env,
        capture_output=True,
        text=True
    )
    
    # Should not crash
    assert "Found 1 document(s) that can be promoted" in result.stdout
    assert "test_b2" not in result.stdout # Ensure it didn't find the other test file if any
    assert result.returncode == 0
    assert "relative_to" not in result.stderr
    assert "ValueError" not in result.stderr
