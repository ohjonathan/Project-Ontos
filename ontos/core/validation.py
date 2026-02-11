"""
Validation orchestration for context map generation.

Extracts validation logic from ontos_generate_context_map.py and provides
a unified interface that collects all errors before returning (no hard exits).

Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.5
"""

from __future__ import annotations
from typing import Dict, List, Set, Tuple, Optional, Any

from ontos.core.types import (
    DocumentData,
    ValidationError,
    ValidationResult,
    ValidationErrorType,
)
from ontos.core.graph import (
    build_graph,
    detect_cycles,
    detect_orphans,
    calculate_depths,
    DEPENDS_ON_SEVERITY_DEFAULT,
    IMPACTS_SEVERITY_DEFAULT,
    DESCRIBES_SEVERITY_DEFAULT,
)

# SEVERITY RATIONALE (v3.3 Track A1)
# ---------------------------------
# - ERROR: Circular dependencies or duplicate IDs (breaking graph integrity).
# - WARNING: Orphan documents, depth exceedance, or missing/invalid descriptive metadata.
# - NOTE: depends_on is structural (error); impacts/describes are informational (warning).
REFERENCE_SEVERITY_DEFAULT = {
    "depends_on": DEPENDS_ON_SEVERITY_DEFAULT,
    "impacts": IMPACTS_SEVERITY_DEFAULT,
    "describes": DESCRIBES_SEVERITY_DEFAULT,
    "circular": DEPENDS_ON_SEVERITY_DEFAULT,
    "orphan": "warning",
    "depth": "warning",
    "schema": "warning",
    "concepts": "warning"
}


def validate_describes_field(
    doc: DocumentData,
    valid_targets: Set[str],
    severity: str = DESCRIBES_SEVERITY_DEFAULT
) -> List[ValidationError]:
    """Validate describes field references valid targets (list-safe).
    
    Args:
        doc: Document with list of described atoms
        valid_targets: Set of valid target doc_ids
        
    Returns:
        List of ValidationErrors for invalid references
    """
    errors = []
    # Use the normalized describes list from DocumentData
    for target in doc.describes:
        if target not in valid_targets:
            errors.append(ValidationError(
                error_type=ValidationErrorType.SCHEMA,
                doc_id=doc.id,
                filepath=str(doc.filepath),
                message=f"describes '{target}' not found",
                fix_suggestion=f"Update describes to valid target or remove",
                severity=severity
            ))
    return errors


class ValidationOrchestrator:
    """Orchestrates all validation checks and collects errors."""

    def __init__(
        self,
        docs: Dict[str, DocumentData],
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize with documents and optional config.

        Args:
            docs: Dictionary mapping doc_id to DocumentData
            config: Optional configuration dict
        """
        self.docs = docs
        self.config = config or {}
        self.severity_map = {
            **REFERENCE_SEVERITY_DEFAULT,
            **self.config.get("severity_map", {}),
        }
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def _report(self, error: ValidationError) -> None:
        """Report an error or warning based on its severity."""
        if error.severity == "error":
            self.errors.append(error)
        else:
            self.warnings.append(error)

    def validate_all(self) -> ValidationResult:
        """Run all validations and return collected results.

        Returns:
            ValidationResult with all errors and warnings
        """
        self.validate_graph()
        self.validate_log_schema()
        self.validate_impacts()
        self.validate_describes()
        self.validate_concepts()

        return ValidationResult(
            errors=self.errors,
            warnings=self.warnings
        )

    def validate_graph(self) -> None:
        """Validate dependency graph: broken links, cycles, orphans, depth."""
        graph, broken_link_errors = build_graph(self.docs, severity_map=self.severity_map)
        self.errors.extend([e for e in broken_link_errors if e.severity == "error"])
        self.warnings.extend([e for e in broken_link_errors if e.severity == "warning"])

        # Detect cycles
        cycles = detect_cycles(graph)
        for cycle in cycles:
            cycle_str = " -> ".join(cycle)
            self.errors.append(ValidationError(
                error_type=ValidationErrorType.CYCLE,
                doc_id=cycle[0],
                filepath=str(self.docs[cycle[0]].filepath) if cycle[0] in self.docs else "",
                message=f"Circular dependency: {cycle_str}",
                fix_suggestion="Break the cycle by removing one dependency",
                severity="error"
            ))

        # Detect orphans
        allowed_orphans = set(self.config.get("allowed_orphan_types", ["atom", "log"]))
        orphans = detect_orphans(graph, allowed_orphans)
        for orphan_id in orphans:
            if orphan_id in self.docs:
                self.warnings.append(ValidationError(
                    error_type=ValidationErrorType.ORPHAN,
                    doc_id=orphan_id,
                    filepath=str(self.docs[orphan_id].filepath),
                    message=f"Document has no incoming dependencies",
                    fix_suggestion="Add this document to another document's depends_on",
                    severity="warning"
                ))

        # Check depth
        max_depth = self.config.get("max_dependency_depth", 5)
        depths = calculate_depths(graph)
        for doc_id, depth in depths.items():
            if depth > max_depth:
                self.warnings.append(ValidationError(
                    error_type=ValidationErrorType.DEPTH,
                    doc_id=doc_id,
                    filepath=str(self.docs[doc_id].filepath) if doc_id in self.docs else "",
                    message=f"Dependency depth {depth} exceeds max {max_depth}",
                    fix_suggestion="Consider flattening the dependency chain",
                    severity="warning"
                ))

    def validate_log_schema(self) -> None:
        """Validate log documents have required v2.0 fields."""
        required_fields = {"branch", "event_type", "source"}

        for doc_id, doc in self.docs.items():
            # Handle both enum and string types
            doc_type = doc.type.value
            if doc_type != "log":
                continue

            missing = required_fields - set(doc.frontmatter.keys())
            if missing:
                self.warnings.append(ValidationError(
                    error_type=ValidationErrorType.SCHEMA,
                    doc_id=doc_id,
                    filepath=str(doc.filepath),
                    message=f"Log missing fields: {', '.join(sorted(missing))}",
                    fix_suggestion="Add missing fields to frontmatter",
                    severity="warning"
                ))

    def validate_impacts(self, severity: Optional[str] = None) -> None:
        """Validate impacts[] references exist.

        Args:
            severity: Optional override ("error" or "warning"). Defaults to severity map.
        """
        valid_ids = set(self.docs.keys())
        effective_severity = (
            severity
            if severity is not None
            else self.severity_map.get("impacts", IMPACTS_SEVERITY_DEFAULT)
        )

        for doc_id, doc in self.docs.items():
            for impact in doc.impacts:
                if impact not in valid_ids:
                    self._report(ValidationError(
                        error_type=ValidationErrorType.IMPACTS,
                        doc_id=doc_id,
                        filepath=str(doc.filepath),
                        message=f"Impact reference '{impact}' not found",
                        fix_suggestion=f"Remove '{impact}' or create the document",
                        severity=effective_severity
                    ))

    def validate_describes(self, severity: Optional[str] = None) -> None:
        """Validate describes field references.

        Args:
            severity: Optional override ("error" or "warning"). Defaults to severity map.
        """
        valid_ids = set(self.docs.keys())
        effective_severity = (
            severity
            if severity is not None
            else self.severity_map.get("describes", DESCRIBES_SEVERITY_DEFAULT)
        )
 
        for doc_id, doc in self.docs.items():
            errors = validate_describes_field(
                doc, 
                valid_ids, 
                severity=effective_severity
            )
            for error in errors:
                self._report(error)

    def validate_concepts(self) -> None:
        """Validate concept field usage and structure (#42)."""
        known_concepts = self.config.get("known_concepts", set())
        
        for doc_id, doc in self.docs.items():
            concepts = doc.frontmatter.get("concepts")
            
            # Structural check: empty list
            if isinstance(concepts, list) and not concepts:
                self._report(ValidationError(
                    error_type=ValidationErrorType.CURATION,
                    doc_id=doc_id,
                    filepath=str(doc.filepath),
                    message="Empty 'concepts' list",
                    fix_suggestion="Add concepts or remove the field",
                    severity=self.severity_map.get("concepts", "warning")
                ))

            if concepts:
                if not isinstance(concepts, list):
                    self._report(ValidationError(
                        error_type=ValidationErrorType.CURATION,
                        doc_id=doc_id,
                        filepath=str(doc.filepath),
                        message=f"Invalid 'concepts' type: {type(concepts).__name__} (expected list)",
                        fix_suggestion="Convert concepts to a YAML list",
                        severity=self.severity_map.get("concepts", "warning")
                    ))
                else:
                    # Structural check: non-string elements
                    non_strings = [str(c) for c in concepts if not isinstance(c, str)]
                    if non_strings:
                        self._report(ValidationError(
                            error_type=ValidationErrorType.CURATION,
                            doc_id=doc_id,
                            filepath=str(doc.filepath),
                            message=f"Non-string items in concepts: {', '.join(non_strings)}",
                            fix_suggestion="Ensure all concepts are strings",
                            severity=self.severity_map.get("concepts", "warning")
                        ))

                    # Structural check: duplicates
                    # Guard against unhashable members (dicts, lists) during set conversion (VUL-01)
                    hashable_concepts = [c for c in concepts if isinstance(c, (str, int, float, bool))]
                    if len(hashable_concepts) != len(set(hashable_concepts)):
                        dupes = [c for c in set(hashable_concepts) if hashable_concepts.count(c) > 1]
                        self._report(ValidationError(
                            error_type=ValidationErrorType.CURATION,
                            doc_id=doc_id,
                            filepath=str(doc.filepath),
                            message=f"Duplicate concepts: {', '.join(map(str, dupes))}",
                            fix_suggestion="Remove duplicate concepts",
                            severity=self.severity_map.get("concepts", "warning")
                        ))

                    # Vocabulary check (#42)
                    if known_concepts:
                        unknown = [c for c in concepts if isinstance(c, str) and c not in known_concepts]
                        for u in unknown:
                            self._report(ValidationError(
                                error_type=ValidationErrorType.CURATION,
                                doc_id=doc_id,
                                filepath=str(doc.filepath),
                                message=f"Unknown concept: '{u}'",
                                fix_suggestion=f"Add '{u}' to vocabulary or use an existing concept",
                                severity=self.severity_map.get("concepts", "warning")
                            ))

            # Role-based check: log requirement
            if doc.type.value == "log" and concepts is None:
                self._report(ValidationError(
                    error_type=ValidationErrorType.CURATION,
                    doc_id=doc_id,
                    filepath=str(doc.filepath),
                    message="Log document missing 'concepts' field (required at L2)",
                    fix_suggestion="Add a concepts: list to the frontmatter",
                    severity=self.severity_map.get("concepts", "warning")
                ))
