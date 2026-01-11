"""Ontos Ontology Definitions - Single Source of Truth.

This module defines the canonical document types, frontmatter fields,
and their relationships. All other code should import from here.

Per v2.9.6 Implementation Specification:
- TypeDefinition and FieldDefinition are frozen dataclasses
- Backward-compatible helper functions derive legacy dict formats
- This module is the ONLY place where types and fields are defined

STDLIB ONLY: This module uses only Python standard library (3.9+).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

__all__ = [
    'TypeDefinition',
    'FieldDefinition',
    'TYPE_DEFINITIONS',
    'FIELD_DEFINITIONS',
    'get_type_hierarchy',
    'get_valid_types',
    'get_valid_type_status',
]


@dataclass(frozen=True)
class TypeDefinition:
    """Document type in the Ontos ontology.

    Attributes:
        name: Type identifier (kernel, strategy, product, atom, log)
        rank: Hierarchy rank (0=kernel, 4=log)
        description: Human-readable description
        can_depend_on: List of types this type can depend on
        valid_statuses: List of valid status values for this type
        uses_impacts: True if type uses impacts field instead of depends_on (logs only)
    """
    name: str
    rank: int
    description: str
    can_depend_on: List[str]
    valid_statuses: List[str]
    uses_impacts: bool = False


@dataclass(frozen=True)
class FieldDefinition:
    """Frontmatter field definition.

    Attributes:
        name: Field name as it appears in frontmatter
        field_type: Data type ("string", "list", "enum")
        required: Whether field is required
        description: Human-readable description
        valid_values: For enums, the list of valid values
        applies_to: List of types this field applies to (None = all types)
    """
    name: str
    field_type: str  # "string", "list", "enum"
    required: bool
    description: str
    valid_values: Optional[List[str]] = None
    applies_to: Optional[List[str]] = None


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================
# Curation meta-statuses apply to all types during L0/L1 processing
_CURATION_STATUSES = ["scaffold", "pending_curation"]

TYPE_DEFINITIONS: Dict[str, TypeDefinition] = {
    "kernel": TypeDefinition(
        name="kernel",
        rank=0,
        description="Foundational principles - mission, values, core identity",
        can_depend_on=["kernel"],  # kernel can depend on other kernels
        valid_statuses=["active", "draft", "deprecated"] + _CURATION_STATUSES,
    ),
    "strategy": TypeDefinition(
        name="strategy",
        rank=1,
        description="Goals, direction, roadmap - business decisions",
        can_depend_on=["kernel"],
        valid_statuses=["active", "draft", "deprecated", "rejected", "complete"] + _CURATION_STATUSES,
    ),
    "product": TypeDefinition(
        name="product",
        rank=2,
        description="User-facing specifications - features, requirements",
        can_depend_on=["kernel", "strategy"],
        valid_statuses=["active", "draft", "deprecated"] + _CURATION_STATUSES,
    ),
    "atom": TypeDefinition(
        name="atom",
        rank=3,
        description="Technical specs, architecture, implementation details",
        can_depend_on=["kernel", "strategy", "product", "atom"],
        valid_statuses=["active", "draft", "deprecated", "complete"] + _CURATION_STATUSES,
    ),
    "log": TypeDefinition(
        name="log",
        rank=4,
        description="Session history - temporal records of work",
        can_depend_on=[],
        # BEHAVIOR FIX (v2.9.6): Added auto-generated (used in practice, was missing from VALID_TYPE_STATUS)
        valid_statuses=["active", "archived", "auto-generated"] + _CURATION_STATUSES,
        uses_impacts=True,
    ),
}


# =============================================================================
# FIELD DEFINITIONS
# =============================================================================
FIELD_DEFINITIONS: Dict[str, FieldDefinition] = {
    "id": FieldDefinition(
        name="id",
        field_type="string",
        required=True,
        description="Unique identifier (snake_case, immutable)",
    ),
    "type": FieldDefinition(
        name="type",
        field_type="enum",
        required=True,
        description="Document type in hierarchy",
        valid_values=["kernel", "strategy", "product", "atom", "log"],
    ),
    "status": FieldDefinition(
        name="status",
        field_type="enum",
        required=True,
        description="Document lifecycle state",
        valid_values=[
            "active", "draft", "deprecated", "archived",
            "rejected", "complete", "auto-generated",
            "scaffold", "pending_curation"
        ],
    ),
    "depends_on": FieldDefinition(
        name="depends_on",
        field_type="list",
        required=True,
        description="Referenced document IDs",
        applies_to=["kernel", "strategy", "product", "atom"],
    ),
    "impacts": FieldDefinition(
        name="impacts",
        field_type="list",
        required=False,
        description="Document IDs modified in this session",
        applies_to=["log"],
    ),
    "event_type": FieldDefinition(
        name="event_type",
        field_type="enum",
        required=True,
        description="Session type",
        valid_values=["feature", "fix", "refactor", "exploration", "chore", "decision"],
        applies_to=["log"],
    ),
    "concepts": FieldDefinition(
        name="concepts",
        field_type="list",
        required=False,
        description="Abstract concepts discussed",
    ),
    "ontos_schema": FieldDefinition(
        name="ontos_schema",
        field_type="string",
        required=False,
        description="Schema version",
        valid_values=["1.0", "2.0", "2.1", "2.2", "3.0"],
    ),
    "curation_level": FieldDefinition(
        name="curation_level",
        field_type="enum",
        required=False,
        description="Level of human curation",
        valid_values=["L0", "L1", "L2"],
    ),
    "describes": FieldDefinition(
        name="describes",
        field_type="list",
        required=False,
        description="Source files this doc describes",
        applies_to=["atom"],
    ),
}


# =============================================================================
# BACKWARD-COMPATIBLE EXPORTS
# =============================================================================
def get_type_hierarchy() -> Dict[str, int]:
    """Return TYPE_HIERARCHY dict for backward compatibility.

    Returns:
        Dict mapping type name to rank (e.g., {'kernel': 0, 'log': 4})
    """
    return {name: td.rank for name, td in TYPE_DEFINITIONS.items()}


def get_valid_types() -> Set[str]:
    """Return VALID_TYPES set for backward compatibility.

    Returns:
        Set of valid type names
    """
    return set(TYPE_DEFINITIONS.keys())


def get_valid_type_status() -> Dict[str, Set[str]]:
    """Return VALID_TYPE_STATUS dict for backward compatibility.

    Returns:
        Dict mapping type name to set of valid statuses
    """
    return {name: set(td.valid_statuses) for name, td in TYPE_DEFINITIONS.items()}
