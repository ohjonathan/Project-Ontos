"""Single source of truth for Ontos type and field definitions.

This module defines the ontology schema used throughout Ontos:
- TypeDefinition: Document types (core hierarchy plus lifecycle artifacts)
- FieldDefinition: Frontmatter fields (id, type, status, etc.)

All other modules should import from here to ensure consistency.

NOTE ON FIELD_DEFINITIONS:
    The `required` flag indicates whether a field is structurally required
    at the schema validation level (schema.py SCHEMA_DEFINITIONS).
    Curation-level requirements (L2 enforcement) are handled separately
    in curation.py validate_at_level().

    Example: `depends_on` is optional at schema level but required at
    Level 2 curation for strategy/product/atom documents.

Usage:
    from ontos.core.ontology import TYPE_DEFINITIONS, get_valid_types
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

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
    """Document type in the Ontos ontology."""
    name: str
    rank: int
    description: str
    can_depend_on: Tuple[str, ...]  # truly immutable with frozen=True
    valid_statuses: Tuple[str, ...]  # truly immutable with frozen=True
    uses_impacts: bool = False  # True only for log


@dataclass(frozen=True)
class FieldDefinition:
    """Frontmatter field definition."""
    name: str
    field_type: str  # "string", "list", "enum"
    required: bool
    description: str
    valid_values: Optional[Tuple[str, ...]] = None  # For enums
    applies_to: Optional[Tuple[str, ...]] = None  # None = all types


# Curation meta-statuses apply to all types during L0/L1 processing.
_CURATION_STATUSES: Tuple[str, ...] = ("scaffold", "pending_curation")
_BASE_STATUSES: Tuple[str, ...] = ("active", "draft", "deprecated")
_LIFECYCLE_STATUSES: Tuple[str, ...] = (
    "proposed",
    "ready",
    "completed",
    "revised",
    "in-lifecycle",
)
_HISTORICAL_STATUSES: Tuple[str, ...] = (
    "archived",
    "rejected",
    "complete",
    "auto-generated",
    "in_progress",
)
_ALL_DOCUMENT_STATUSES: Tuple[str, ...] = (
    _BASE_STATUSES
    + _HISTORICAL_STATUSES
    + _LIFECYCLE_STATUSES
    + _CURATION_STATUSES
)
_ANY_DOCUMENT_TYPE: Tuple[str, ...] = (
    "kernel",
    "strategy",
    "product",
    "atom",
    "log",
    "reference",
    "concept",
    "handoff",
    "tracker",
    "retro",
    "review",
    "spec",
    "report",
    "adr",
    "policy",
)

TYPE_DEFINITIONS: Dict[str, TypeDefinition] = {
    "kernel": TypeDefinition(
        name="kernel",
        rank=0,
        description="Foundational principles - mission, values, core identity",
        can_depend_on=("kernel",),  # kernel can depend on other kernels
        valid_statuses=("active", "draft", "deprecated") + _CURATION_STATUSES,
    ),
    "strategy": TypeDefinition(
        name="strategy",
        rank=1,
        description="Goals, direction, roadmap - business decisions",
        can_depend_on=("kernel",),
        valid_statuses=("active", "draft", "deprecated", "rejected", "complete") + _CURATION_STATUSES,
    ),
    "product": TypeDefinition(
        name="product",
        rank=2,
        description="User-facing specifications - features, requirements",
        can_depend_on=("kernel", "strategy"),
        valid_statuses=("active", "draft", "deprecated") + _CURATION_STATUSES,
    ),
    "atom": TypeDefinition(
        name="atom",
        rank=3,
        description="Technical specs, architecture, implementation details",
        can_depend_on=("kernel", "strategy", "product", "atom"),
        valid_statuses=("active", "draft", "deprecated", "complete") + _CURATION_STATUSES,
    ),
    "log": TypeDefinition(
        name="log",
        rank=4,
        description="Session history - temporal records of work",
        can_depend_on=(),
        # BEHAVIOR FIX: Added auto-generated (used in practice, was missing from VALID_TYPE_STATUS)
        valid_statuses=("active", "archived", "auto-generated", "complete", "completed") + _CURATION_STATUSES,
        uses_impacts=True,
    ),
    "reference": TypeDefinition(
        name="reference",
        rank=5,
        description="External or internal reference material that supports the graph",
        can_depend_on=_ANY_DOCUMENT_TYPE,
        valid_statuses=_ALL_DOCUMENT_STATUSES,
    ),
    "concept": TypeDefinition(
        name="concept",
        rank=5,
        description="Vocabulary, taxonomy, or glossary material",
        can_depend_on=_ANY_DOCUMENT_TYPE,
        valid_statuses=_ALL_DOCUMENT_STATUSES,
    ),
    "handoff": TypeDefinition(
        name="handoff",
        rank=5,
        description="Lifecycle handoff packet for agents or maintainers",
        can_depend_on=_ANY_DOCUMENT_TYPE,
        valid_statuses=_ALL_DOCUMENT_STATUSES,
    ),
    "tracker": TypeDefinition(
        name="tracker",
        rank=5,
        description="Lifecycle tracker for workstreams, issues, or release gates",
        can_depend_on=_ANY_DOCUMENT_TYPE,
        valid_statuses=_ALL_DOCUMENT_STATUSES,
    ),
    "retro": TypeDefinition(
        name="retro",
        rank=5,
        description="Retrospective or lessons-learned lifecycle record",
        can_depend_on=_ANY_DOCUMENT_TYPE,
        valid_statuses=_ALL_DOCUMENT_STATUSES,
    ),
    "review": TypeDefinition(
        name="review",
        rank=5,
        description="Peer, alignment, adversarial, or verification review artifact",
        can_depend_on=_ANY_DOCUMENT_TYPE,
        valid_statuses=_ALL_DOCUMENT_STATUSES,
    ),
    "spec": TypeDefinition(
        name="spec",
        rank=5,
        description="Implementation or behavior specification",
        can_depend_on=_ANY_DOCUMENT_TYPE,
        valid_statuses=_ALL_DOCUMENT_STATUSES,
    ),
    "report": TypeDefinition(
        name="report",
        rank=5,
        description="Final report, status report, or synthesized analysis",
        can_depend_on=_ANY_DOCUMENT_TYPE,
        valid_statuses=_ALL_DOCUMENT_STATUSES,
    ),
    "adr": TypeDefinition(
        name="adr",
        rank=5,
        description="Architecture decision record",
        can_depend_on=_ANY_DOCUMENT_TYPE,
        valid_statuses=_ALL_DOCUMENT_STATUSES,
    ),
    "policy": TypeDefinition(
        name="policy",
        rank=5,
        description="Policy, rule, or operating constraint",
        can_depend_on=_ANY_DOCUMENT_TYPE,
        valid_statuses=_ALL_DOCUMENT_STATUSES,
    ),
}

# FIELD_DEFINITIONS: Metadata for documentation generation.
# NOT consumed by runtime validation (that uses SCHEMA_DEFINITIONS in schema.py).
# Future work (v3.0) may wire this into validators.
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
        valid_values=_ANY_DOCUMENT_TYPE,
    ),
    "status": FieldDefinition(
        name="status",
        field_type="enum",
        required=True,
        description="Document lifecycle state",
        valid_values=_ALL_DOCUMENT_STATUSES,
    ),
    "depends_on": FieldDefinition(
        name="depends_on",
        field_type="list",
        required=False,  # optional at schema level, L2 curation enforces
        description="Referenced document IDs (required at L2 for strategy/product/atom)",
        applies_to=(
            "strategy",
            "product",
            "atom",
            "reference",
            "concept",
            "handoff",
            "tracker",
            "retro",
            "review",
            "spec",
            "report",
            "adr",
            "policy",
        ),  # kernel/log excluded per curation.py
    ),
    "impacts": FieldDefinition(
        name="impacts",
        field_type="list",
        required=False,
        description="Document IDs modified in this session",
        applies_to=("log",),
    ),
    "event_type": FieldDefinition(
        name="event_type",
        field_type="enum",
        required=False,  # not enforced by schema.py or curation.py
        description="Session type",
        valid_values=("feature", "fix", "refactor", "exploration", "chore", "decision"),
        applies_to=("log",),
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
        valid_values=("1.0", "2.0", "2.1", "2.2", "3.0"),
    ),
    "curation_level": FieldDefinition(
        name="curation_level",
        field_type="enum",
        required=False,
        description="Level of human curation",
        valid_values=("L0", "L1", "L2"),
    ),
    "describes": FieldDefinition(
        name="describes",
        field_type="list",
        required=False,
        description="Source files this doc describes",
        applies_to=("atom",),
    ),
}


# Backward-compatible exports for ontos_config_defaults.py
def get_type_hierarchy() -> Dict[str, int]:
    """Return TYPE_HIERARCHY dict for backward compatibility."""
    return {name: td.rank for name, td in TYPE_DEFINITIONS.items()}


def get_valid_types() -> set:
    """Return VALID_TYPES set for backward compatibility."""
    return set(TYPE_DEFINITIONS.keys())


def get_valid_type_status() -> Dict[str, set]:
    """Return VALID_TYPE_STATUS dict for backward compatibility."""
    return {name: set(td.valid_statuses) for name, td in TYPE_DEFINITIONS.items()}
