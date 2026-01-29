"""
Shared type definitions for Ontos core modules.

This module has NO dependencies on other ontos modules (except re-exports)
to prevent circular imports. Import this first when building other core modules.

Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.1
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# =============================================================================
# RE-EXPORTS (consolidate existing types here)
# =============================================================================

# Re-export CurationLevel from its canonical location
from ontos.core.curation import CurationLevel

# =============================================================================
# ENUMS (new)
# =============================================================================

class DocumentType(Enum):
    """Document types in the Ontos ontology."""
    KERNEL = "kernel"
    STRATEGY = "strategy"
    PRODUCT = "product"
    ATOM = "atom"
    LOG = "log"
    REFERENCE = "reference"


class DocumentStatus(Enum):
    """Document lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"
    COMPLETE = "complete"


class ValidationErrorType(Enum):
    """Categories of validation errors."""
    BROKEN_LINK = "broken_link"
    CYCLE = "cycle"
    ORPHAN = "orphan"
    ARCHITECTURE = "architecture"
    SCHEMA = "schema"
    STATUS = "status"
    STALENESS = "staleness"
    CURATION = "curation"
    IMPACTS = "impacts"
    DEPTH = "depth"


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class DocumentData:
    """Parsed document with frontmatter and content."""
    id: str
    type: DocumentType
    status: DocumentStatus
    filepath: Path
    frontmatter: Dict[str, Any]
    content: str
    depends_on: List[str] = field(default_factory=list)
    impacts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)


@dataclass
class ValidationError:
    """A single validation error or warning."""
    error_type: ValidationErrorType
    doc_id: str
    filepath: str
    message: str
    fix_suggestion: str
    severity: str  # 'error', 'warning', 'info'


@dataclass
class ValidationResult:
    """Result of running all validations."""
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 1 if self.errors else 0

    def add_error(self, error: ValidationError) -> None:
        """Add an error to the result."""
        if error.severity == "error":
            self.errors.append(error)
        else:
            self.warnings.append(error)


# =============================================================================
# CONSTANTS (from ontos_end_session.py lines 779-846)
# =============================================================================

VALID_SLUG_PATTERN = r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$"
MAX_SLUG_LENGTH = 50

CHANGELOG_CATEGORIES = [
    "Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"
]

DEFAULT_CHANGELOG = "CHANGELOG.md"

# Event type templates for session logs
TEMPLATES = {
    "chore": "## Summary\n\n## Changes Made\n\n## Testing",
    "fix": "## Summary\n\n## Root Cause\n\n## Fix Applied\n\n## Testing",
    "feature": "## Summary\n\n## Implementation\n\n## Testing\n\n## Documentation",
    "refactor": "## Summary\n\n## Changes\n\n## Rationale\n\n## Testing",
    "exploration": "## Objective\n\n## Findings\n\n## Conclusions\n\n## Next Steps",
    "decision": "## Context\n\n## Decision\n\n## Rationale\n\n## Consequences",
}

SECTION_TEMPLATES = {
    "Summary": "<!-- Brief description of what was done -->",
    "Changes Made": "<!-- List of changes -->",
    "Testing": "<!-- How this was tested -->",
    "Root Cause": "<!-- What caused the issue -->",
    "Fix Applied": "<!-- How the fix works -->",
}
