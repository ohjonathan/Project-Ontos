"""Tests for schema version detection, validation, compatibility, and serialization."""

import pytest

from ontos.core.schema import (
    SchemaCheckResult,
    SchemaCompatibility,
    check_compatibility,
    detect_schema_version,
    parse_version,
    serialize_frontmatter,
    validate_frontmatter,
)


# ---------------------------------------------------------------------------
# parse_version
# ---------------------------------------------------------------------------

class TestParseVersion:
    def test_valid_versions(self):
        assert parse_version("2.1") == (2, 1)
        assert parse_version("3.0") == (3, 0)
        assert parse_version("1.0") == (1, 0)

    def test_whitespace_stripped(self):
        assert parse_version("  2.1 ") == (2, 1)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            parse_version("2")
        with pytest.raises(ValueError):
            parse_version("2.1.3")
        with pytest.raises(ValueError):
            parse_version("")

    def test_non_integer_raises(self):
        with pytest.raises(ValueError):
            parse_version("a.b")

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            parse_version("-1.0")


# ---------------------------------------------------------------------------
# detect_schema_version
# ---------------------------------------------------------------------------

class TestDetectSchemaVersion:
    def test_explicit_ontos_schema(self):
        assert detect_schema_version({"id": "x", "ontos_schema": "2.2"}) == "2.2"

    def test_infers_v3_from_implements(self):
        assert detect_schema_version({"id": "x", "implements": ["y"]}) == "3.0"

    def test_infers_v22_from_curation_level(self):
        assert detect_schema_version({"id": "x", "curation_level": 1}) == "2.2"

    def test_infers_v21_from_describes(self):
        assert detect_schema_version({"id": "x", "describes": ["y"]}) == "2.1"

    def test_infers_v20_from_type(self):
        assert detect_schema_version({"id": "x", "type": "atom"}) == "2.0"

    def test_default_v10(self):
        assert detect_schema_version({"id": "x"}) == "1.0"

    def test_empty_frontmatter(self):
        assert detect_schema_version({}) == "1.0"
        assert detect_schema_version(None) == "1.0"


# ---------------------------------------------------------------------------
# check_compatibility
# ---------------------------------------------------------------------------

class TestCheckCompatibility:
    def test_compatible(self):
        result = check_compatibility("2.1", "2.9.0")
        assert result.compatibility == SchemaCompatibility.COMPATIBLE

    def test_read_only_future_minor(self):
        result = check_compatibility("2.9", "2.1")
        assert result.compatibility == SchemaCompatibility.READ_ONLY

    def test_incompatible_future_major(self):
        result = check_compatibility("3.0", "2.9.0")
        assert result.compatibility == SchemaCompatibility.INCOMPATIBLE

    def test_invalid_doc_version(self):
        result = check_compatibility("bad", "2.9.0")
        assert result.compatibility == SchemaCompatibility.INCOMPATIBLE


# ---------------------------------------------------------------------------
# validate_frontmatter
# ---------------------------------------------------------------------------

class TestValidateFrontmatter:
    def test_valid_v20(self):
        valid, errors = validate_frontmatter({"id": "test", "type": "atom"}, "2.0")
        assert valid is True
        assert errors == []

    def test_missing_required_field(self):
        valid, errors = validate_frontmatter({"type": "atom"}, "2.0")
        assert valid is False
        assert any("id" in e for e in errors)

    def test_empty_required_field(self):
        valid, errors = validate_frontmatter({"id": "", "type": "atom"}, "2.0")
        assert valid is False

    def test_unknown_schema_passes(self):
        valid, errors = validate_frontmatter({"id": "test"}, "99.0")
        assert valid is True


# ---------------------------------------------------------------------------
# serialize_frontmatter
# ---------------------------------------------------------------------------

class TestSerializeFrontmatter:
    def test_basic_roundtrip(self):
        fm = {"id": "test", "type": "atom", "status": "active"}
        result = serialize_frontmatter(fm)
        assert "id: test" in result
        assert "type: atom" in result
        assert "status: active" in result

    def test_list_serialization(self):
        fm = {"id": "test", "depends_on": ["a", "b"]}
        result = serialize_frontmatter(fm)
        assert "depends_on: [a, b]" in result

    def test_empty_list(self):
        fm = {"id": "test", "depends_on": []}
        result = serialize_frontmatter(fm)
        assert "depends_on: []" in result

    def test_field_ordering(self):
        fm = {"depends_on": [], "type": "atom", "id": "test", "status": "active"}
        result = serialize_frontmatter(fm)
        lines = result.strip().split("\n")
        # id should come before type which comes before status
        id_idx = next(i for i, l in enumerate(lines) if l.startswith("id:"))
        type_idx = next(i for i, l in enumerate(lines) if l.startswith("type:"))
        status_idx = next(i for i, l in enumerate(lines) if l.startswith("status:"))
        assert id_idx < type_idx < status_idx

    def test_unicode_values(self):
        fm = {"id": "test", "type": "atom"}
        result = serialize_frontmatter(fm)
        assert isinstance(result, str)

    def test_null_value(self):
        fm = {"id": "test", "extra": None}
        result = serialize_frontmatter(fm)
        assert "extra: null" in result
