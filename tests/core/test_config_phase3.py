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
    required_version_incompatibility,
    version_satisfies_requirement,
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

    def test_validate_types_rejects_non_string_required_version(self):
        with pytest.raises(ConfigError, match="ontos.required_version must be str"):
            _validate_types({"ontos": {"required_version": 47}})

    def test_validate_types_rejects_invalid_required_version_range(self):
        with pytest.raises(ConfigError, match="semantic version"):
            _validate_types({"ontos": {"required_version": "=>4.7"}})


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


@pytest.mark.parametrize(
    ("requirement", "compatible"),
    [
        ("", True),
        (">=4.7.0, <5.0.0", True),
        ("~4.7", True),
        ("4.7.x", True),
        ("=4.7", True),
        (">4.7.0", False),
        ("<4.7.0", False),
        ("4.6.*", False),
    ],
)
def test_version_satisfies_required_version_ranges(requirement, compatible):
    assert version_satisfies_requirement("4.7.0", requirement) is compatible


def test_required_version_incompatibility_is_actionable():
    message = required_version_incompatibility(">=99.0.0", "4.7.0")

    assert message is not None
    assert message.startswith("Incompatible Ontos version:")
    assert "running 4.7.0" in message
    assert ">=99.0.0" in message
    assert "Migration_v3_to_v4.md#audit-remediation-compatibility-contracts" in message


@pytest.mark.parametrize("requirement", ["not-a-range", ">=", "4.x.5"])
def test_invalid_required_version_clause_is_reported_once(requirement):
    message = required_version_incompatibility(requirement, "4.7.0")

    assert message is not None
    assert message.startswith("Invalid [ontos].required_version:")
    assert message.count(repr(requirement)) == 1
    assert "Migration_v3_to_v4.md#audit-remediation-compatibility-contracts" in message


@pytest.mark.parametrize(
    ("requirement", "offending_clause"),
    [
        (">=4.7.0, not-a-range, <5.0.0", "not-a-range"),
        (">=4.7.0, >=, <5.0.0", ">="),
        (">=4.7.0, 4.x.5, <5.0.0", "4.x.5"),
    ],
)
def test_multi_clause_invalid_required_version_identifies_offender_once(
    requirement,
    offending_clause,
):
    message = required_version_incompatibility(requirement, "4.7.0")

    assert message is not None
    assert message.startswith("Invalid [ontos].required_version:")
    assert f"clause {offending_clause!r}" in message
    assert message.count(repr(offending_clause)) == 1
    assert "Migration_v3_to_v4.md#audit-remediation-compatibility-contracts" in message


def test_incompatible_earlier_clause_does_not_hide_malformed_later_clause():
    requirement = ">=99.0.0, not-a-range"

    message = required_version_incompatibility(requirement, "4.7.0")

    assert message is not None
    assert message.startswith("Invalid [ontos].required_version:")
    assert message.count(repr("not-a-range")) == 1


def test_config_validation_does_not_short_circuit_before_malformed_later_clause():
    # Config-load validation uses 0.0.0 as a parser-only sentinel.  The first
    # clause is false for that sentinel and previously hid the malformed one.
    with pytest.raises(ConfigError) as exc_info:
        _validate_types(
            {"ontos": {"required_version": ">0.0.0, not-a-range"}}
        )

    assert str(exc_info.value).count(repr("not-a-range")) == 1


@pytest.mark.parametrize(
    "data, message",
    [
        ({"paths": {"docs_dir": ["docs"]}}, r"paths\.docs_dir must be str"),
        ({"scanning": {"skip_patterns": "archive/*"}}, r"scanning\.skip_patterns must be list"),
        ({"scanning": {"scan_paths": ["docs", 7]}}, r"scanning\.scan_paths\[1\] must be str"),
        ({"scanning": {"default_scope": "everything"}}, r"default_scope"),
        ({"validation": {"max_dependency_depth": True}}, r"max_dependency_depth must be int"),
        ({"workflow": {"log_retention_count": 0}}, r"log_retention_count must be >= 1"),
        ({"paths": "docs"}, r"section 'paths' must be a table"),
    ],
)
def test_config_validation_rejects_opaque_crash_inputs(data, message):
    with pytest.raises(ConfigError, match=message):
        dict_to_config(data)
