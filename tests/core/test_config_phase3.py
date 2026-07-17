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
            _validate_types({"hooks": {"pre_push": "yes"}})

    def test_validate_types_rejects_non_list_allowed_orphan_paths(self):
        with pytest.raises(ConfigError, match=r"validation\.allowed_orphan_paths must be list"):
            _validate_types({"validation": {"allowed_orphan_paths": "docs/logs/**"}})

    def test_validate_types_rejects_non_str_item_in_allowed_orphan_paths(self):
        with pytest.raises(ConfigError, match=r"validation\.allowed_orphan_paths\[0\] must be str"):
            _validate_types({"validation": {"allowed_orphan_paths": [123]}})

    def test_validate_types_rejects_non_list_allowed_orphan_types(self):
        with pytest.raises(ConfigError, match=r"validation\.allowed_orphan_types must be list"):
            _validate_types({"validation": {"allowed_orphan_types": "atom"}})

    def test_validate_types_accepts_correct_types(self):
        """Type validation passes for correct types."""
        # Should not raise
        _validate_types({"workflow": {"log_retention_count": 50}})
        _validate_types({"hooks": {"pre_push": True, "pre_commit": False}})

    def test_legacy_numeric_bounds_are_clamped_without_mutating_input(self):
        data = {
            "validation": {"max_dependency_depth": -4},
            "workflow": {"log_retention_count": 0},
        }

        config = dict_to_config(data)

        assert config.validation.max_dependency_depth == 0
        assert config.workflow.log_retention_count == 1
        assert data == {
            "validation": {"max_dependency_depth": -4},
            "workflow": {"log_retention_count": 0},
        }


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

    def test_dict_to_config_maps_legacy_validation_strict_to_hooks(self):
        """Legacy validation.strict is accepted and preserved via hooks.strict."""
        config = dict_to_config({"validation": {"strict": True}})

        assert config.hooks.strict is True

    def test_dict_to_config_accepts_legacy_project_section(self):
        """Legacy top-level [project] section remains a compatibility no-op."""
        config = dict_to_config(
            {
                "project": {"name": "legacy-project"},
                "paths": {"logs_dir": "docs/logs"},
            }
        )

        assert config.paths.logs_dir == "docs/logs"

    def test_dict_to_config_rejects_unknown_section_key(self):
        """Unknown keys raise ConfigError with the offending dotted key."""
        with pytest.raises(ConfigError, match=r"hooks\.strictt"):
            dict_to_config({"hooks": {"strictt": True}})

    def test_dict_to_config_rejects_unknown_top_level_section(self):
        """Unknown top-level sections raise ConfigError with section name."""
        with pytest.raises(ConfigError, match="hokks"):
            dict_to_config({"hokks": {"strict": True}})


# (#134) allowed_external_dependency_paths type validation — mirrors the
# allowed_orphan_paths checks above.

def test_validate_types_rejects_non_list_allowed_external_dependency_paths():
    with pytest.raises(ConfigError, match="must be list"):
        _validate_types({"validation": {"allowed_external_dependency_paths": "apps/**"}})


def test_validate_types_rejects_non_str_item_in_allowed_external_dependency_paths():
    with pytest.raises(ConfigError, match=r"\[1\] must be str"):
        _validate_types(
            {"validation": {"allowed_external_dependency_paths": ["apps/**", 7]}}
        )


def test_allowed_external_dependency_paths_defaults_to_empty():
    config = dict_to_config({})
    assert config.validation.allowed_external_dependency_paths == []


def test_allowed_external_dependency_paths_round_trips():
    config = dict_to_config(
        {"validation": {"allowed_external_dependency_paths": ["apps/**", "manifests/**"]}}
    )
    assert config.validation.allowed_external_dependency_paths == [
        "apps/**", "manifests/**",
    ]


class TestFrontmatterAliases:
    """(#178) [frontmatter.aliases.*] tables: fail-closed validation and
    lowercase key normalization."""

    def test_valid_alias_tables_load_and_normalize_keys(self):
        config = dict_to_config({
            "frontmatter": {
                "aliases": {
                    "status": {"In-Progress": "in_progress", "provider_done": "complete"},
                    "type": {"runbook": "reference"},
                }
            }
        })
        assert config.frontmatter.aliases["status"] == {
            "in-progress": "in_progress",
            "provider_done": "complete",
        }
        assert config.frontmatter.aliases["type"] == {"runbook": "reference"}

    def test_missing_section_defaults_to_empty(self):
        config = dict_to_config({})
        assert config.frontmatter.aliases == {}

    def test_unknown_alias_table_rejected(self):
        with pytest.raises(ConfigError, match="frontmatter.aliases.severity"):
            dict_to_config({
                "frontmatter": {"aliases": {"severity": {"hi": "active"}}}
            })

    def test_non_canonical_target_rejected(self):
        with pytest.raises(ConfigError, match="not a canonical status value"):
            dict_to_config({
                "frontmatter": {"aliases": {"status": {"waiting": "on-hold"}}}
            })

    def test_unknown_target_rejected(self):
        # 'unknown' is an enum member but never a valid repair target.
        with pytest.raises(ConfigError, match="not a canonical type value"):
            dict_to_config({
                "frontmatter": {"aliases": {"type": {"mystery": "unknown"}}}
            })

    def test_canonical_key_cannot_be_remapped(self):
        with pytest.raises(ConfigError, match="already a canonical"):
            dict_to_config({
                "frontmatter": {"aliases": {"status": {"draft": "active"}}}
            })

    def test_case_normalized_duplicate_rejected(self):
        with pytest.raises(ConfigError, match="more than once"):
            dict_to_config({
                "frontmatter": {
                    "aliases": {
                        "status": {"WIP": "in_progress", "wip": "active"},
                    }
                }
            })

    def test_non_string_target_rejected(self):
        with pytest.raises(ConfigError, match="must be str"):
            dict_to_config({
                "frontmatter": {"aliases": {"status": {"wip": 3}}}
            })

    def test_unknown_frontmatter_key_rejected(self):
        with pytest.raises(ConfigError, match="Unknown config key"):
            dict_to_config({"frontmatter": {"alias": {}}})

    def test_builtin_conflict_rejected(self):
        # PR #182 review: redefining a built-in mapping to a different
        # target is a conflict, not an override.
        with pytest.raises(ConfigError, match="conflicts with the built-in"):
            dict_to_config({
                "frontmatter": {"aliases": {"status": {"in-progress": "complete"}}}
            })

    def test_builtin_restatement_with_same_target_allowed(self):
        config = dict_to_config({
            "frontmatter": {"aliases": {"status": {"in-progress": "in_progress"}}}
        })
        assert config.frontmatter.aliases["status"] == {"in-progress": "in_progress"}

    def test_default_serialization_omits_empty_frontmatter_section(self):
        # PR #182 review: Ontos <= 5.0.2 rejects unknown sections, so a
        # default config must not emit [frontmatter] at all.
        from ontos.core.config import config_to_dict, default_config

        data = config_to_dict(default_config())
        assert "frontmatter" not in data
        # Round trip still yields an equal default config.
        assert dict_to_config(data) == default_config()

    def test_non_empty_aliases_are_serialized(self):
        from ontos.core.config import config_to_dict

        config = dict_to_config({
            "frontmatter": {"aliases": {"type": {"runbook": "reference"}}}
        })
        data = config_to_dict(config)
        assert data["frontmatter"]["aliases"]["type"] == {"runbook": "reference"}
