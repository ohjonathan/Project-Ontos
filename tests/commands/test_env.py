import json
from pathlib import Path
import pytest
from ontos.commands.env import env_command, EnvOptions, detect_manifests


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for environment detection tests."""
    return tmp_path


def test_detect_pyproject_toml(temp_workspace):
    """Test detection of pyproject.toml (poetry)."""
    pyproject = temp_workspace / "pyproject.toml"
    pyproject.write_text("""
[tool.poetry]
name = "test-project"
dependencies = { python = "^3.9", requests = "^2.25" }
dev-dependencies = { pytest = "^7.0" }
""")
    
    manifests, warnings = detect_manifests(temp_workspace)
    assert len(manifests) == 1
    assert manifests[0].path.name == "pyproject.toml"
    assert manifests[0].manifest_type == "python_deps"
    assert manifests[0].package_manager == "poetry"
    assert manifests[0].dependency_count == {"runtime": 1, "dev": 1}
    assert not warnings


def test_detect_package_json(temp_workspace):
    """Test detection of package.json."""
    pkg_json = temp_workspace / "package.json"
    pkg_json.write_text(json.dumps({
        "name": "test-node",
        "dependencies": { "express": "^4.17" },
        "devDependencies": { "jest": "^27.0" }
    }))
    
    manifests, warnings = detect_manifests(temp_workspace)
    assert len(manifests) == 1
    assert manifests[0].path.name == "package.json"
    assert manifests[0].dependency_count == {"runtime": 1, "dev": 1}
    assert not warnings


def test_detect_tool_versions(temp_workspace):
    """Test detection of .tool-versions (asdf)."""
    tool_versions = temp_workspace / ".tool-versions"
    tool_versions.write_text("python 3.9.6\nnode 16.5.0")
    
    manifests, warnings = detect_manifests(temp_workspace)
    assert len(manifests) == 1
    assert manifests[0].path.name == ".tool-versions"
    assert manifests[0].details["runtimes"] == {"python": "3.9.6", "node": "16.5.0"}


def test_multiple_manifests(temp_workspace):
    """Test detection of multiple manifests."""
    (temp_workspace / "pyproject.toml").write_text("[project]\ndependencies = ['requests']")
    (temp_workspace / "package.json").write_text("{}")
    
    manifests, warnings = detect_manifests(temp_workspace)
    assert len(manifests) == 2
    types = [m.manifest_type for m in manifests]
    assert "python_deps" in types
    assert "npm_deps" in types


def test_no_manifests(temp_workspace):
    """Test behavior when no manifests are present."""
    manifests, warnings = detect_manifests(temp_workspace)
    assert len(manifests) == 0
    assert not warnings


def test_env_command_text_output(temp_workspace):
    """Test CLI text format output."""
    (temp_workspace / "requirements.txt").write_text("requests\npytest")
    
    options = EnvOptions(path=temp_workspace, format="text")
    exit_code, output = env_command(options)
    
    assert exit_code == 0
    assert "Environment Manifest Detection" in output
    assert "requirements.txt" in output
    assert "2 packages" in output


def test_env_command_json_output(temp_workspace):
    """Test CLI JSON format output."""
    (temp_workspace / "requirements.txt").write_text("requests")
    
    options = EnvOptions(path=temp_workspace, format="json")
    exit_code, output = env_command(options)
    
    assert exit_code == 0
    data = json.loads(output)
    assert data["$schema"] == "ontos-env-v1"
    assert len(data["manifests"]) == 1
    assert data["manifests"][0]["path"] == "requirements.txt"


def test_env_command_write_creates_file(temp_workspace):
    """Test --write flag creates environment.md."""
    (temp_workspace / ".tool-versions").write_text("python 3.9")
    
    options = EnvOptions(path=temp_workspace, write=True)
    exit_code, output = env_command(options)
    
    assert exit_code == 0
    env_md = temp_workspace / ".ontos" / "environment.md"
    assert env_md.exists()
    assert "# Environment Setup" in env_md.read_text()


def test_env_command_write_force_overwrites(temp_workspace):
    """Test --force flag (v1.1)."""
    ontos_dir = temp_workspace / ".ontos"
    ontos_dir.mkdir()
    env_md = ontos_dir / "environment.md"
    env_md.write_text("original content")
    
    # Try without force
    options = EnvOptions(path=temp_workspace, write=True, force=False)
    exit_code, output = env_command(options)
    assert exit_code == 1
    assert "already exists" in output
    assert env_md.read_text() == "original content"
    
    # Try with force
    options.force = True
    exit_code, output = env_command(options)
    assert exit_code == 0
    assert env_md.read_text() != "original content"


def test_parse_warnings_in_output(temp_workspace):
    """Test that parse warnings are surfaced (v1.1)."""
    # Malformed package.json
    pkg_json = temp_workspace / "package.json"
    pkg_json.write_text("{ malformed json }")
    
    options = EnvOptions(path=temp_workspace, format="text")
    exit_code, output = env_command(options)
    
    assert exit_code == 0
    assert "Parse Warnings:" in output
    assert "package.json: parse failed" in output
