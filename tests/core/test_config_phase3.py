"""Tests for ontos.core.config module (Phase 3)."""
import pytest
from pathlib import Path

from ontos.core.config import (
    ConfigError,
    OntosConfig,
    WorkflowConfig,
    PathsConfig,
    default_config,
    config_to_dict,
    dict_to_config,
    _validate_types,
    _validate_path,
)


class TestDefaultConfig:
    """Tests for default_config() function."""

    def test_default_config_returns_ontos_config(self):
        """Default config returns OntosConfig instance."""
        config = default_config()
        assert isinstance(config, OntosConfig)

    def test_default_config_has_expected_version(self):
        """Default config has version 3.0."""
        config = default_config()
        assert config.ontos.version == "3.0"

    def test_default_config_has_expected_paths(self):
        """Default config has expected path values."""
        config = default_config()
        assert config.paths.docs_dir == "docs"
        assert config.paths.logs_dir == "docs/logs"
        assert config.paths.context_map == "Ontos_Context_Map.md"

    def test_default_config_has_log_retention_count(self):
        """Default config has log_retention_count = 20 (per Roadmap)."""
        config = default_config()
        assert config.workflow.log_retention_count == 20

    def test_default_config_has_scan_scope_default(self):
        """Default scanning scope is docs."""
        config = default_config()
        assert config.scanning.default_scope == "docs"


class TestConfigToDict:
    """Tests for config_to_dict() function."""

    def test_config_to_dict_returns_dict(self):
        """config_to_dict returns a dictionary."""
        config = default_config()
        data = config_to_dict(config)
        assert isinstance(data, dict)

    def test_config_to_dict_preserves_values(self):
        """config_to_dict preserves all values."""
        config = default_config()
        data = config_to_dict(config)
        assert data["workflow"]["log_retention_count"] == 20
        assert data["paths"]["docs_dir"] == "docs"

    def test_config_to_dict_roundtrip(self):
        """config_to_dict and dict_to_config are inverse operations."""
        original = default_config()
        data = config_to_dict(original)
        restored = dict_to_config(data)
        assert restored.workflow.log_retention_count == original.workflow.log_retention_count
        assert restored.paths.docs_dir == original.paths.docs_dir


class TestValidateTypes:
    """Tests for _validate_types() function."""

    def test_validate_types_rejects_string_for_int(self):
        """Type validation rejects wrong types with ConfigError."""
        with pytest.raises(ConfigError, match="must be int"):
            _validate_types({"workflow": {"log_retention_count": "twenty"}})

    def test_validate_types_rejects_string_for_bool(self):
        """Type validation rejects string for bool with ConfigError."""
        with pytest.raises(ConfigError, match="must be bool"):
            _validate_types({"workflow": {"enforce_archive_before_push": "yes"}})

    def test_validate_types_accepts_correct_types(self):
        """Type validation passes for correct types."""
        # Should not raise
        _validate_types({"workflow": {"log_retention_count": 50}})
        _validate_types({"workflow": {"enforce_archive_before_push": True}})
        _validate_types({"validation": {"strict": False}})
        _validate_types({"hooks": {"pre_push": True, "pre_commit": False}})


class TestValidatePath:
    """Tests for _validate_path() function."""

    def test_validate_path_accepts_relative_path(self, tmp_path):
        """Path validation accepts relative paths within repo."""
        assert _validate_path("docs", tmp_path) is True
        assert _validate_path("docs/logs", tmp_path) is True

    def test_validate_path_rejects_traversal(self, tmp_path):
        """Path validation rejects paths outside repo root."""
        assert _validate_path("../outside", tmp_path) is False
        assert _validate_path("../../etc/passwd", tmp_path) is False

    def test_validate_path_accepts_absolute_within_repo(self, tmp_path):
        """Path validation handles paths that resolve within repo."""
        # A path that includes .. but still stays within repo
        (tmp_path / "subdir").mkdir()
        assert _validate_path("subdir/../docs", tmp_path) is True


class TestDictToConfig:
    """Tests for dict_to_config() function."""

    def test_dict_to_config_missing_sections(self):
        """Missing sections use defaults."""
        config = dict_to_config({})  # Empty dict
        assert config.paths.docs_dir == "docs"  # Default value
        assert config.workflow.log_retention_count == 20

    def test_dict_to_config_partial_section(self):
        """Partial section values are merged with defaults."""
        config = dict_to_config({
            "workflow": {"log_retention_count": 50}
        })
        assert config.workflow.log_retention_count == 50
        assert config.workflow.enforce_archive_before_push is True  # Default

    def test_dict_to_config_path_validation(self, tmp_path):
        """dict_to_config validates paths when repo_root provided."""
        with pytest.raises(ConfigError, match="must resolve within repository root"):
            dict_to_config(
                {"paths": {"docs_dir": "../outside"}},
                repo_root=tmp_path
            )

    def test_dict_to_config_type_validation(self):
        """dict_to_config validates types."""
        with pytest.raises(ConfigError, match="must be int"):
            dict_to_config({"workflow": {"log_retention_count": "bad"}})
