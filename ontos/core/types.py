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

# CurationLevel moved here to prevent circular imports
class CurationLevel(IntEnum):
    """Document curation levels."""
    SCAFFOLD = 0  # Auto-generated placeholder
    STUB = 1      # User provides goal only
    FULL = 2      # Complete Ontos document

# =============================================================================
# ENUMS (new)
# =============================================================================

class DocumentType(str, Enum):
    """Document types in the Ontos ontology.

    Canonical types: kernel/strategy/product/atom/log/reference/concept.
    (#117) Lifecycle artifact types added so real engineering workspaces
    (handoffs, trackers, retros, reviews, specs, reports, ADRs, policies)
    are not silently demoted to `unknown`. Conservative repair still
    falls back to `unknown` when the value matches nothing.
    """
    KERNEL = "kernel"
    STRATEGY = "strategy"
    PRODUCT = "product"
    ATOM = "atom"
    LOG = "log"
    REFERENCE = "reference"
    CONCEPT = "concept"
    HANDOFF = "handoff"
    TRACKER = "tracker"
    RETRO = "retro"
    REVIEW = "review"
    SPEC = "spec"
    REPORT = "report"
    ADR = "adr"
    POLICY = "policy"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    """Document lifecycle status.

    Canonical statuses: draft/active/deprecated/archived/rejected/complete/
    auto-generated/scaffold/pending_curation/in_progress.
    (#117) Lifecycle workflow statuses (proposed, ready, completed,
    revised, in-lifecycle) added for non-kernel artifacts; `completed` is
    an alias of `complete` retained to preserve real-world variation.
    """
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    REJECTED = "rejected"
    COMPLETE = "complete"
    AUTO_GENERATED = "auto-generated"
    SCAFFOLD = "scaffold"
    PENDING_CURATION = "pending_curation"
    IN_PROGRESS = "in_progress"
    PROPOSED = "proposed"
    READY = "ready"
    COMPLETED = "completed"
    REVISED = "revised"
    IN_LIFECYCLE = "in-lifecycle"
    UNKNOWN = "unknown"


class ValidationErrorType(Enum):
    """Categories of validation errors."""
    DUPLICATE_ID = "duplicate_id"
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
    # (#117) depends_on entry resolved as a path against the filesystem but
    # the target is not a loaded doc — treat as a soft external dependency
    # rather than a hard broken-link error.
    OUT_OF_SCOPE_DEPENDENCY = "out_of_scope_dependency"
    # (#134) Same resolution as OUT_OF_SCOPE_DEPENDENCY but the path matches
    # the project's allowed_external_dependency_paths allowlist — an
    # intentional doc-to-file edge, reported at info severity.
    EXTERNAL_FILE_DEPENDENCY = "external_file_dependency"


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
    describes: List[str] = field(default_factory=list)


@dataclass
class ValidationError:
    """A single validation error or warning."""
    error_type: ValidationErrorType
    doc_id: str
    filepath: str
    message: str
    fix_suggestion: str
    severity: str  # 'error', 'warning', 'info'
    # (#134) Structured machine context (e.g. dep_value / resolved_path /
    # allowlisted) so consumers never parse messages. Deliberately NOT
    # serialized by to_dict(): the public record shape {severity, message,
    # rule_id, document_id, file_path} is asserted byte-for-byte by CLI/MCP
    # parity tests and must stay stable.
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        record: Dict[str, Any] = {"severity": self.severity, "message": self.message}
        rule_id = getattr(self.error_type, "value", None) if self.error_type else None
        if rule_id:
            record["rule_id"] = rule_id
        if self.doc_id:
            record["document_id"] = self.doc_id
        if self.filepath:
            record["file_path"] = self.filepath
        return record


@dataclass
class ValidationResult:
    """Result of running all validations."""
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    # (#134) Info-severity records (e.g. allowlisted external file deps) are
    # kept out of warnings so they never flip activation status.
    infos: List[ValidationError] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 1 if self.errors else 0

    def add_error(self, error: ValidationError) -> None:
        """Add an error to the result."""
        if error.severity == "error":
            self.errors.append(error)
        elif error.severity == "info":
            self.infos.append(error)
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
