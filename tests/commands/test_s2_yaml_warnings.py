import json
import pytest
from pathlib import Path
from ontos.commands.export_data import export_data_command, ExportDataOptions
from ontos.io.files import find_project_root

def test_export_data_yaml_warning(tmp_path):
    """S2 Gap Verification: Ensure invalid YAML produces a warning in export JSON."""
    # Setup mock ontos project
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".ontos.toml").write_text("[ontos]\nversion = '3.2'\n[paths]\ndocs_dir = 'docs'\n")
    
    docs_dir = project_root / "docs"
    docs_dir.mkdir()
    
    # Create file with invalid YAML
    # Note the second colon makes it invalid YAML
    (docs_dir / "bad.md").write_text("---\ninvalid: yaml: here\n---\n# Bad\n")
    (docs_dir / "good.md").write_text("---\ntitle: Good\n---\n# Good\n")
    
    # Run export data command
    output_file = tmp_path / "export.json"
    options = ExportDataOptions(
        output_path=output_file,
        force=True,
        quiet=True
    )
    
    # We need to be in the project root for find_project_root()
    import os
    old_cwd = os.getcwd()
    os.chdir(project_root)
    try:
        exit_code, message = export_data_command(options)
        assert exit_code == 0
    finally:
        os.chdir(old_cwd)
    
    # Verify JSON content
    data = json.loads(output_file.read_text())
    
    # Summary should contain warnings
    assert "warnings" in data["summary"]
    warnings = data["summary"]["warnings"]
    assert any("bad.md" in w and "Invalid YAML" in w for w in warnings)
    
    # Should still include the good document
    assert len(data["documents"]) == 1
    assert data["documents"][0]["id"] == "good"
