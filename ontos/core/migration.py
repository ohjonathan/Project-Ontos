"""
Migration classification logic.

Classifies documents as safe/review/rewrite based on atom dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from ontos.core.snapshot import DocumentSnapshot
from ontos.core.graph import DependencyGraph


# Classification severity order (for downgrade detection)
SEVERITY_ORDER = {"safe": 0, "review": 1, "rewrite": 2}


@dataclass
class MigrationClassification:
    """Classification result for a single document."""
    id: str
    doc_type: str
    path: str
    inferred_status: str  # 'safe', 'review', 'rewrite'
    effective_status: str
    override: Optional[str] = None
    override_reason: Optional[str] = None
    atom_dependencies: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class MigrationReport:
    """Complete migration classification report."""
    classifications: Dict[str, MigrationClassification]
    summary: Dict[str, int]  # safe/review/rewrite counts
    warnings: List[Dict[str, str]]  # Global warnings


def _find_transitive_atom_deps(
    doc_id: str,
    graph: DependencyGraph,
    atoms: Set[str],
    visited: Optional[Set[str]] = None
) -> Set[str]:
    """Find all atoms this document depends on (transitively)."""
    if visited is None:
        visited = set()

    if doc_id in visited:
        return set()  # Cycle detected
    visited.add(doc_id)

    result = set()
    for dep_id in graph.edges.get(doc_id, []):
        if dep_id in atoms:
            result.add(dep_id)
        # Recurse into dependencies
        result.update(_find_transitive_atom_deps(dep_id, graph, atoms, visited))

    return result


def classify_documents(snapshot: DocumentSnapshot) -> MigrationReport:
    """
    Classify all documents for migration.

    Algorithm:
    1. Identify all atoms
    2. Build transitive atom dependency map
    3. Classify each document:
       - type == 'atom' → inferred = 'rewrite'
       - has transitive atom dependency → inferred = 'review'
       - otherwise → inferred = 'safe'
    4. Apply overrides, emit warnings for downgrades
    """
    # Step 1: Identify all atoms
    atoms = set()
    for doc_id, doc in snapshot.documents.items():
        doc_type = doc.type.value
        if doc_type == "atom":
            atoms.add(doc_id)

    # Step 2 & 3: Classify each document
    classifications: Dict[str, MigrationClassification] = {}
    global_warnings: List[Dict[str, str]] = []

    for doc_id, doc in snapshot.documents.items():
        doc_type = doc.type.value

        # Find transitive atom dependencies
        atom_deps = list(_find_transitive_atom_deps(doc_id, snapshot.graph, atoms))

        # Determine inferred status
        if doc_type == "atom":
            inferred = "rewrite"
        elif atom_deps:
            inferred = "review"
        else:
            inferred = "safe"

        # Check for override in frontmatter
        override = doc.frontmatter.get("migration_status")
        override_reason = doc.frontmatter.get("migration_status_reason")

        # Validate override value
        if override and override not in ("safe", "review", "rewrite"):
            global_warnings.append({
                "id": doc_id,
                "type": "invalid_override",
                "message": f"Invalid migration_status '{override}', ignoring"
            })
            override = None

        # Determine effective status
        effective = override if override else inferred

        # Warn on downgrade
        warnings = []
        if override and SEVERITY_ORDER.get(override, 0) < SEVERITY_ORDER.get(inferred, 0):
            warning_msg = f"Override downgrades inferred classification from '{inferred}' to '{override}'"
            warnings.append(warning_msg)
            global_warnings.append({
                "id": doc_id,
                "type": "override_downgrade",
                "message": warning_msg
            })

        classifications[doc_id] = MigrationClassification(
            id=doc_id,
            doc_type=doc_type,
            path=str(doc.filepath),
            inferred_status=inferred,
            effective_status=effective,
            override=override,
            override_reason=override_reason,
            atom_dependencies=sorted(atom_deps),
            warnings=warnings,
        )

    # Build summary
    summary = {"safe": 0, "review": 0, "rewrite": 0}
    for c in classifications.values():
        summary[c.effective_status] = summary.get(c.effective_status, 0) + 1

    return MigrationReport(
        classifications=classifications,
        summary=summary,
        warnings=global_warnings,
    )
