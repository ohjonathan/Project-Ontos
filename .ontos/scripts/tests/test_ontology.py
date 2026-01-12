"""Tests for the ontology module (v2.9.6+).

These tests verify the single source of truth for Ontos type and field definitions.
"""

import pytest
from ontos.core.ontology import (
    TYPE_DEFINITIONS,
    FIELD_DEFINITIONS,
    get_type_hierarchy,
    get_valid_types,
    get_valid_type_status,
)


class TestTypeDefinitions:
    """Tests for TYPE_DEFINITIONS."""

    def test_type_definitions_complete(self):
        """All 5 types defined."""
        assert set(TYPE_DEFINITIONS.keys()) == {"kernel", "strategy", "product", "atom", "log"}

    def test_type_ranks_ordered(self):
        """Ranks are 0-4 in hierarchy order."""
        ranks = [td.rank for td in TYPE_DEFINITIONS.values()]
        assert sorted(ranks) == [0, 1, 2, 3, 4]

    def test_kernel_can_depend_on_kernel(self):
        """Kernel can depend on other kernels (e.g., constitution->mission)."""
        assert "kernel" in TYPE_DEFINITIONS["kernel"].can_depend_on

    def test_log_uses_impacts(self):
        """Log type uses impacts, not depends_on."""
        assert TYPE_DEFINITIONS["log"].uses_impacts is True
        assert TYPE_DEFINITIONS["log"].can_depend_on == ()

    def test_strategy_has_complete_status(self):
        """Strategy can have 'complete' status (for reviews)."""
        assert "complete" in TYPE_DEFINITIONS["strategy"].valid_statuses

    def test_all_types_have_curation_statuses(self):
        """All types support scaffold and pending_curation (curation meta-statuses)."""
        for type_name, td in TYPE_DEFINITIONS.items():
            assert "scaffold" in td.valid_statuses, f"{type_name} missing scaffold"
            assert "pending_curation" in td.valid_statuses, f"{type_name} missing pending_curation"

    def test_log_has_auto_generated(self):
        """Log type supports auto-generated status (behavior fix)."""
        assert "auto-generated" in TYPE_DEFINITIONS["log"].valid_statuses


class TestFieldDefinitions:
    """Tests for FIELD_DEFINITIONS."""

    def test_field_definitions_complete(self):
        """All required fields defined."""
        required = {"id", "type", "status", "depends_on"}
        assert required.issubset(FIELD_DEFINITIONS.keys())

    def test_depends_on_applies_to_non_logs(self):
        """depends_on applies to strategy, product, atom (not kernel or log)."""
        fd = FIELD_DEFINITIONS["depends_on"]
        assert "log" not in fd.applies_to
        assert "kernel" not in fd.applies_to  # kernel docs have no dependencies
        assert fd.applies_to == ("strategy", "product", "atom")
        assert isinstance(fd.applies_to, tuple)  # verify immutability

    def test_impacts_applies_to_log_only(self):
        """impacts applies only to log type."""
        fd = FIELD_DEFINITIONS["impacts"]
        assert fd.applies_to == ("log",)
        assert isinstance(fd.applies_to, tuple)  # verify immutability

    def test_valid_values_is_tuple(self):
        """valid_values must be tuple for immutability."""
        fd = FIELD_DEFINITIONS["event_type"]
        assert isinstance(fd.valid_values, tuple)
        assert fd.valid_values == ("feature", "fix", "refactor", "exploration", "chore", "decision")


class TestBackwardCompatHelpers:
    """Tests for backward-compatibility helper functions."""

    def test_get_type_hierarchy(self):
        """get_type_hierarchy returns correct dict."""
        hierarchy = get_type_hierarchy()
        assert hierarchy["kernel"] == 0
        assert hierarchy["log"] == 4

    def test_get_valid_types(self):
        """get_valid_types returns all type names."""
        types = get_valid_types()
        assert "kernel" in types
        assert "log" in types
        assert len(types) == 5

    def test_get_valid_type_status(self):
        """get_valid_type_status returns correct status sets."""
        status_map = get_valid_type_status()
        assert "active" in status_map["kernel"]
        assert "archived" in status_map["log"]
        assert "auto-generated" in status_map["log"]


class TestIntegrationWithConfigDefaults:
    """Tests for integration with ontos_config_defaults."""

    def test_config_defaults_uses_ontology(self):
        """ontos_config_defaults imports from ontology.py."""
        from ontos_config_defaults import TYPE_DEFINITIONS, TYPE_HIERARCHY
        assert TYPE_DEFINITIONS["kernel"]["rank"] == 0
        assert TYPE_HIERARCHY["kernel"] == 0


class TestGeneratorFieldCategorization:
    """Tests for field categorization (bug fix from Codex PR #38 review)."""

    def test_required_universal_fields(self):
        """Required fields with applies_to=None are universal."""
        universal = [n for n, fd in FIELD_DEFINITIONS.items() 
                     if fd.required and fd.applies_to is None]
        assert set(universal) == {"id", "type", "status"}

    def test_required_type_specific_fields(self):
        """No fields are required at type-specific level (L2 enforcement is in curation.py)."""
        type_specific = [n for n, fd in FIELD_DEFINITIONS.items()
                         if fd.required and fd.applies_to is not None]
        assert set(type_specific) == set()  # Empty: L2 requirements in curation.py

    def test_optional_fields(self):
        """All type-specific fields are optional at schema level."""
        optional = [n for n, fd in FIELD_DEFINITIONS.items() if not fd.required]
        assert set(optional) == {"depends_on", "impacts", "concepts", "ontos_schema", 
                                  "curation_level", "describes", "event_type"}


class TestOntologySchemaAlignment:
    """Tests to detect drift between ontology.py and schema.py/curation.py."""

    def test_universal_required_matches_schema(self):
        """Ontology universal required fields must match schema v2.2 required."""
        from ontos.core.schema import SCHEMA_DEFINITIONS

        schema_required = set(SCHEMA_DEFINITIONS["2.2"]["required"])
        ontology_required = {
            name for name, fd in FIELD_DEFINITIONS.items()
            if fd.required and fd.applies_to is None
        }

        assert ontology_required == schema_required, (
            f"Mismatch: ontology={ontology_required}, schema={schema_required}"
        )

    def test_no_type_specific_required_fields(self):
        """No type-specific required fields (curation.py handles L2 enforcement)."""
        type_specific_required = [
            name for name, fd in FIELD_DEFINITIONS.items()
            if fd.required and fd.applies_to is not None
        ]
        assert type_specific_required == [], (
            f"Type-specific required fields found: {type_specific_required}. "
            "L2 requirements should be in curation.py, not ontology.py."
        )


class TestGeneratedSpec:
    """Tests for the generated ontology_spec.md content."""

    def test_spec_includes_schema_requirements_section(self):
        """Generated spec must include schema requirements section."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from ontos_generate_ontology_spec import generate_spec

        spec = generate_spec()
        assert "## 3. Schema Requirements by Version" in spec

