"""Tests for ontos.io.config module (Phase 3)."""
import pytest
from pathlib import Path

from ontos.core.config import ConfigError, default_config
from ontos.io.config import (
    find_config,
    load_project_config,
    save_project_config,
    config_exists,
    CONFIG_FILENAME,
)


class TestConfigFilename:
    """Tests for CONFIG_FILENAME constant."""

    def test_config_filename_is_ontos_toml(self):
        """Config filename is .ontos.toml."""
        assert CONFIG_FILENAME == ".ontos.toml"


class TestFindConfig:
    """Tests for find_config() function."""

    def test_find_config_returns_none_if_missing(self, tmp_path):
        """find_config returns None if no .ontos.toml exists."""
        assert find_config(tmp_path) is None

    def test_find_config_finds_in_current_dir(self, tmp_path):
        """find_config finds .ontos.toml in current directory."""
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text("[ontos]\nversion = '3.0'\n")
        assert find_config(tmp_path) == config_file

    def test_find_config_finds_in_parent_dir(self, tmp_path):
        """find_config walks up to parent to find .ontos.toml."""
        # Create config in parent
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text("[ontos]\nversion = '3.0'\n")

        # Search from child directory
        child_dir = tmp_path / "subdir" / "nested"
        child_dir.mkdir(parents=True)
        assert find_config(child_dir) == config_file


class TestLoadProjectConfig:
    """Tests for load_project_config() function."""

    def test_load_project_config_returns_defaults_if_missing(self, tmp_path):
        """Missing config returns default values."""
        config = load_project_config(config_path=tmp_path / "nonexistent.toml")
        assert config.paths.docs_dir == "docs"
        assert config.workflow.log_retention_count == 20

    def test_load_project_config_loads_values(self, tmp_path):
        """load_project_config loads values from file."""
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text("""
[ontos]
version = "3.0"

[paths]
docs_dir = "documentation"

[workflow]
log_retention_count = 50
""")
        config = load_project_config(config_path=config_file)
        assert config.paths.docs_dir == "documentation"
        assert config.workflow.log_retention_count == 50

    def test_load_project_config_uses_defaults_for_missing_fields(self, tmp_path):
        """Partial config uses defaults for missing fields."""
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text("""
[ontos]
version = "3.0"
""")
        config = load_project_config(config_path=config_file)
        assert config.paths.docs_dir == "docs"  # Default

    def test_load_project_config_raises_on_malformed_toml(self, tmp_path):
        """Malformed TOML raises ConfigError (M2 test)."""
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text("this is not valid TOML [[[")

        with pytest.raises(ConfigError, match="Failed to parse"):
            load_project_config(config_path=config_file)


class TestSaveProjectConfig:
    """Tests for save_project_config() function."""

    def test_save_project_config_creates_file(self, tmp_path):
        """save_project_config creates the config file."""
        config_path = tmp_path / CONFIG_FILENAME
        config = default_config()
        save_project_config(config, config_path)
        assert config_path.exists()

    def test_save_project_config_writes_valid_toml(self, tmp_path):
        """save_project_config writes valid TOML."""
        config_path = tmp_path / CONFIG_FILENAME
        config = default_config()
        save_project_config(config, config_path)

        content = config_path.read_text()
        assert "[ontos]" in content
        assert 'version = "3.0"' in content
        assert "[workflow]" in content
        assert "log_retention_count = 20" in content

    def test_save_and_load_roundtrip(self, tmp_path):
        """save_project_config and load_project_config roundtrip."""
        config_path = tmp_path / CONFIG_FILENAME
        original = default_config()
        save_project_config(original, config_path)

        loaded = load_project_config(config_path=config_path)
        assert loaded.workflow.log_retention_count == 20
        assert loaded.paths.docs_dir == "docs"


class TestConfigExists:
    """Tests for config_exists() function."""

    def test_config_exists_returns_false_if_missing(self, tmp_path):
        """config_exists returns False when file doesn't exist."""
        assert config_exists(tmp_path / CONFIG_FILENAME) is False

    def test_config_exists_returns_true_if_present(self, tmp_path):
        """config_exists returns True when file exists."""
        config_path = tmp_path / CONFIG_FILENAME
        config_path.write_text("[ontos]\n")
        assert config_exists(config_path) is True
