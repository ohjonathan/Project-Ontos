"""Tests for schema versioning module.

These tests cover:
- Version parsing and validation
- Schema detection from frontmatter
- Compatibility checking
- Frontmatter serialization (stdlib only)
"""

import pytest
from pathlib import Path

# Import schema module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from ontos.core.schema import (
    parse_version,
    detect_schema_version,
    check_compatibility,
    validate_frontmatter,
    serialize_frontmatter,
    add_schema_to_frontmatter,
    get_schema_info,
    SchemaCompatibility,
    CURRENT_SCHEMA_VERSION,
    SCHEMA_DEFINITIONS,
)


class TestParseVersion:
    """Tests for parse_version function."""

    def test_parse_valid_version(self):
        """Parse standard version strings."""
        assert parse_version("2.1") == (2, 1)
        assert parse_version("3.0") == (3, 0)
        assert parse_version("1.0") == (1, 0)

    def test_parse_version_with_whitespace(self):
        """Handle whitespace in version strings."""
        assert parse_version(" 2.1 ") == (2, 1)
        assert parse_version("2.1\n") == (2, 1)

    def test_parse_invalid_format(self):
        """Reject invalid formats."""
        with pytest.raises(ValueError):
            parse_version("2")
        with pytest.raises(ValueError):
            parse_version("2.1.0")  # Patch version not allowed in schema
        with pytest.raises(ValueError):
            parse_version("two.one")

    def test_parse_empty_or_none(self):
        """Reject empty or None values."""
        with pytest.raises(ValueError):
            parse_version("")
        with pytest.raises(ValueError):
            parse_version(None)

    def test_parse_negative_version(self):
        """Reject negative version numbers."""
        with pytest.raises(ValueError):
            parse_version("-1.0")
        with pytest.raises(ValueError):
            parse_version("2.-1")


class TestDetectSchemaVersion:
    """Tests for detect_schema_version function."""

    def test_explicit_schema(self):
        """Explicit ontos_schema field takes priority."""
        fm = {"id": "test", "type": "atom", "ontos_schema": "2.2"}
        assert detect_schema_version(fm) == "2.2"

    def test_explicit_schema_with_inferrable_fields(self):
        """Explicit schema overrides inference."""
        # Has describes (v2.1 field) but declares v2.2
        fm = {"id": "test", "describes": ["foo"], "ontos_schema": "2.2"}
        assert detect_schema_version(fm) == "2.2"

    def test_infer_v3_from_implements(self):
        """Infer v3.0 from implements field."""
        fm = {"id": "test", "type": "atom", "implements": ["some_spec"]}
        assert detect_schema_version(fm) == "3.0"

    def test_infer_v3_from_tests(self):
        """Infer v3.0 from tests field."""
        fm = {"id": "test", "type": "atom", "tests": ["test_module"]}
        assert detect_schema_version(fm) == "3.0"

    def test_infer_v21_from_describes(self):
        """Infer v2.1 from describes field."""
        fm = {"id": "test", "type": "atom", "describes": ["foo"]}
        assert detect_schema_version(fm) == "2.1"

    def test_infer_v21_from_describes_verified(self):
        """Infer v2.1 from describes_verified field."""
        fm = {"id": "test", "describes_verified": "2025-01-01"}
        assert detect_schema_version(fm) == "2.1"

    def test_infer_v22_from_curation_level(self):
        """Infer v2.2 from curation_level field."""
        fm = {"id": "test", "type": "atom", "curation_level": 2}
        assert detect_schema_version(fm) == "2.2"

    def test_infer_v20_from_event_type(self):
        """Infer v2.0 from event_type (log documents)."""
        fm = {"id": "log_test", "type": "log", "event_type": "feature"}
        assert detect_schema_version(fm) == "2.0"

    def test_infer_v20_from_type_field(self):
        """Infer v2.0 from presence of type field."""
        fm = {"id": "test", "type": "atom"}
        assert detect_schema_version(fm) == "2.0"

    def test_default_v10_minimal(self):
        """Default to v1.0 for minimal frontmatter."""
        fm = {"id": "test"}
        assert detect_schema_version(fm) == "1.0"

    def test_empty_frontmatter(self):
        """Empty frontmatter defaults to v1.0."""
        assert detect_schema_version({}) == "1.0"
        assert detect_schema_version(None) == "1.0"


class TestCheckCompatibility:
    """Tests for check_compatibility function."""

    def test_compatible_same_version(self):
        """Same version is compatible."""
        result = check_compatibility("2.1", "2.9.0")
        assert result.compatibility == SchemaCompatibility.COMPATIBLE

    def test_compatible_older_document(self):
        """Older document version is compatible with newer tool."""
        result = check_compatibility("1.0", "2.9.0")
        assert result.compatibility == SchemaCompatibility.COMPATIBLE

    def test_read_only_future_minor(self):
        """Future minor version within same major is read-only."""
        result = check_compatibility("2.5", "2.2.0")
        assert result.compatibility == SchemaCompatibility.READ_ONLY

    def test_incompatible_future_major(self):
        """Future major version is incompatible."""
        result = check_compatibility("3.0", "2.9.0")
        assert result.compatibility == SchemaCompatibility.INCOMPATIBLE

    def test_incompatible_invalid_document_version(self):
        """Invalid document version is incompatible."""
        result = check_compatibility("invalid", "2.9.0")
        assert result.compatibility == SchemaCompatibility.INCOMPATIBLE

    def test_result_contains_message(self):
        """Result includes descriptive message."""
        result = check_compatibility("3.0", "2.9.0")
        assert "3.0" in result.message
        assert result.document_version == "3.0"
        assert result.tool_version == "2.9.0"


class TestValidateFrontmatter:
    """Tests for validate_frontmatter function."""

    def test_valid_v20_frontmatter(self):
        """Valid v2.0 frontmatter passes."""
        fm = {"id": "test", "type": "atom"}
        valid, errors = validate_frontmatter(fm, "2.0")
        assert valid is True
        assert errors == []

    def test_missing_required_field(self):
        """Missing required field fails validation."""
        fm = {"type": "atom"}  # Missing id
        valid, errors = validate_frontmatter(fm, "2.0")
        assert valid is False
        assert any("id" in e for e in errors)

    def test_empty_required_field(self):
        """Empty required field fails validation."""
        fm = {"id": "", "type": "atom"}
        valid, errors = validate_frontmatter(fm, "2.0")
        assert valid is False
        assert any("id" in e for e in errors)

    def test_auto_detect_schema_for_validation(self):
        """Schema is auto-detected if not specified."""
        fm = {"id": "test", "type": "atom", "describes": ["foo"]}
        valid, _ = validate_frontmatter(fm)  # Should detect v2.1
        assert valid is True

    def test_unknown_schema_passes(self):
        """Unknown schema version passes (can't validate)."""
        fm = {"id": "test"}
        valid, errors = validate_frontmatter(fm, "9.9")
        assert valid is True
        assert errors == []


class TestSerializeFrontmatter:
    """Tests for serialize_frontmatter function."""

    def test_simple_fields(self):
        """Serialize simple string fields."""
        fm = {"id": "test", "type": "atom"}
        result = serialize_frontmatter(fm)
        assert "id: test" in result
        assert "type: atom" in result

    def test_list_field_inline(self):
        """Serialize simple list as inline."""
        fm = {"id": "test", "depends_on": ["foo", "bar"]}
        result = serialize_frontmatter(fm)
        assert "depends_on: [foo, bar]" in result

    def test_empty_list(self):
        """Serialize empty list."""
        fm = {"id": "test", "depends_on": []}
        result = serialize_frontmatter(fm)
        assert "depends_on: []" in result

    def test_boolean_field(self):
        """Serialize boolean values."""
        fm = {"id": "test", "active": True, "deprecated": False}
        result = serialize_frontmatter(fm)
        assert "active: true" in result
        assert "deprecated: false" in result

    def test_integer_field(self):
        """Serialize integer values."""
        fm = {"id": "test", "curation_level": 2}
        result = serialize_frontmatter(fm)
        assert "curation_level: 2" in result

    def test_null_field(self):
        """Serialize null values."""
        fm = {"id": "test", "optional": None}
        result = serialize_frontmatter(fm)
        assert "optional: null" in result

    def test_field_ordering(self):
        """Fields are output in standard order."""
        fm = {"depends_on": ["foo"], "id": "test", "type": "atom"}
        result = serialize_frontmatter(fm)
        lines = result.split('\n')
        # id should come before type, which comes before depends_on
        id_pos = next(i for i, l in enumerate(lines) if l.startswith('id:'))
        type_pos = next(i for i, l in enumerate(lines) if l.startswith('type:'))
        deps_pos = next(i for i, l in enumerate(lines) if l.startswith('depends_on:'))
        assert id_pos < type_pos < deps_pos

    def test_value_with_colon(self):
        """Values with colons are quoted."""
        fm = {"id": "test", "description": "Note: important"}
        result = serialize_frontmatter(fm)
        assert 'description: "Note: important"' in result


class TestAddSchemaToFrontmatter:
    """Tests for add_schema_to_frontmatter function."""

    def test_add_explicit_schema(self):
        """Add explicit schema version."""
        fm = {"id": "test", "type": "atom"}
        result = add_schema_to_frontmatter(fm, "2.2")
        assert result["ontos_schema"] == "2.2"

    def test_add_auto_detected_schema(self):
        """Add auto-detected schema version."""
        fm = {"id": "test", "type": "atom", "describes": ["foo"]}
        result = add_schema_to_frontmatter(fm)
        assert result["ontos_schema"] == "2.1"

    def test_does_not_modify_original(self):
        """Original dict is not modified."""
        fm = {"id": "test", "type": "atom"}
        result = add_schema_to_frontmatter(fm, "2.2")
        assert "ontos_schema" not in fm
        assert "ontos_schema" in result


class TestSchemaDefinitions:
    """Tests for schema definitions and constants."""

    def test_current_schema_version_defined(self):
        """Current schema version is defined."""
        assert CURRENT_SCHEMA_VERSION is not None
        assert parse_version(CURRENT_SCHEMA_VERSION)  # Should not raise

    def test_all_schema_versions_have_definitions(self):
        """All schema versions have definitions."""
        for version in ["1.0", "2.0", "2.1", "2.2", "3.0"]:
            assert version in SCHEMA_DEFINITIONS

    def test_get_schema_info(self):
        """get_schema_info returns schema definition."""
        info = get_schema_info("2.0")
        assert "required" in info
        assert "optional" in info
        assert "id" in info["required"]
        assert "type" in info["required"]

    def test_get_schema_info_unknown(self):
        """get_schema_info returns None for unknown version."""
        assert get_schema_info("9.9") is None
