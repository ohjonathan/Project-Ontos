"""
Dependency graph building and validation.

Extracted from ontos_generate_context_map.py during Phase 2 decomposition.
Implements O(V+E) DFS for cycle detection (NOT O(N²) path.index() pattern).

Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.3
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple, Union

from ontos.core.types import DocumentData, ValidationError, ValidationErrorType
from ontos.core.suggestions import suggest_candidates_for_broken_ref


@dataclass
class GraphNode:
    """A node in the dependency graph."""
    doc_id: str
    doc_type: str
    filepath: str
    depends_on: List[str] = field(default_factory=list)


@dataclass
class DependencyGraph:
    """Represents document dependency relationships."""
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: Dict[str, List[str]] = field(default_factory=dict)  # id -> depends_on
    reverse_edges: Dict[str, List[str]] = field(default_factory=dict)  # id -> depended_by

    def add_node(self, doc_id: str, doc_type: str, filepath: str, depends_on: List[str]) -> None:
        """Add a document node to the graph."""
        self.nodes[doc_id] = GraphNode(doc_id, doc_type, filepath, depends_on)
        self.edges[doc_id] = depends_on
        for dep in depends_on:
            if dep not in self.reverse_edges:
                self.reverse_edges[dep] = []
            self.reverse_edges[dep].append(doc_id)


def build_graph(docs: Dict[str, DocumentData]) -> Tuple[DependencyGraph, List[ValidationError]]:
    """Build dependency graph from document dictionary.

    Args:
        docs: Dictionary mapping doc_id to DocumentData

    Returns:
        Tuple of (DependencyGraph, list of broken link errors)
    """
    graph = DependencyGraph()
    errors = []
    existing_ids = set(docs.keys())

    for doc_id, doc in docs.items():
        depends_on = doc.depends_on if hasattr(doc, 'depends_on') else []
        # Handle enum types
        doc_type = doc.type.value if hasattr(doc.type, 'value') else str(doc.type)
        graph.add_node(doc_id, doc_type, str(doc.filepath), depends_on)

        # Check for broken links
        for dep_id in depends_on:
            if dep_id not in existing_ids:
                # Generate candidate suggestions (v3.2)
                candidates = suggest_candidates_for_broken_ref(dep_id, docs)
                fix_suggestion = f"Remove '{dep_id}' from depends_on or create the missing document"
                
                if candidates:
                    suggestion_text = ", ".join(c[0] for c in candidates)
                    fix_suggestion += f". Did you mean: {suggestion_text}?"

                errors.append(ValidationError(
                    error_type=ValidationErrorType.BROKEN_LINK,
                    doc_id=doc_id,
                    filepath=str(doc.filepath),
                    message=f"Broken dependency: '{dep_id}' does not exist",
                    fix_suggestion=fix_suggestion,
                    severity="error"
                ))

    return graph, errors


def detect_cycles(graph: DependencyGraph) -> List[List[str]]:
    """Detect circular dependencies using DFS.

    Uses O(V+E) algorithm with visited and in_stack sets.

    Args:
        graph: DependencyGraph to analyze

    Returns:
        List of cycles (each cycle is a list of doc_ids)
    """
    visited: Set[str] = set()
    in_stack: Set[str] = set()
    cycles: List[List[str]] = []

    def dfs(node: str, path: List[str]) -> None:
        if node in in_stack:
            # Found cycle - extract it from path
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return

        if node in visited:
            return

        visited.add(node)
        in_stack.add(node)
        path.append(node)

        for neighbor in graph.edges.get(node, []):
            if neighbor in graph.nodes:  # Only follow valid edges
                dfs(neighbor, path)

        path.pop()
        in_stack.remove(node)

    for node in graph.nodes:
        if node not in visited:
            dfs(node, [])

    return cycles


def detect_orphans(graph: DependencyGraph, allowed_orphan_types: Set[str]) -> List[str]:
    """Find documents with no incoming edges (not depended on by anyone).

    Args:
        graph: DependencyGraph to analyze
        allowed_orphan_types: Document types that are allowed to be orphans

    Returns:
        List of orphan doc_ids
    """
    orphans = []
    for doc_id, node in graph.nodes.items():
        if node.doc_type in allowed_orphan_types:
            continue
        if doc_id not in graph.reverse_edges or not graph.reverse_edges[doc_id]:
            orphans.append(doc_id)
    return orphans


def calculate_depths(graph: DependencyGraph) -> Dict[str, int]:
    """Calculate dependency depth for each node.

    Depth is the longest path to a leaf node (document with no dependencies).

    Args:
        graph: DependencyGraph to analyze

    Returns:
        Dictionary mapping doc_id to depth
    """
    depths: Dict[str, int] = {}
    computing: Set[str] = set()  # Prevent infinite recursion on cycles

    def get_depth(node: str) -> int:
        if node in depths:
            return depths[node]
        if node in computing:
            return 0  # Cycle detected, treat as leaf
        if node not in graph.nodes:
            return 0

        computing.add(node)
        deps = graph.edges.get(node, [])
        if not deps:
            depth = 0
        else:
            valid_deps = [d for d in deps if d in graph.nodes]
            depth = 1 + max((get_depth(d) for d in valid_deps), default=0)
        computing.remove(node)
        depths[node] = depth
        return depth

    for node in graph.nodes:
        get_depth(node)

    return depths
