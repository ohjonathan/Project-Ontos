"""Shared health-summary helpers and count-basis labels (#133).

Every health surface (doctor, activate, query --health, link-check, map)
computes from the same primitives and labels the basis of its counts, so
two commands reporting different numbers always explain why instead of
reading as contradictory truths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from ontos.core.graph import DependencyGraph, detect_orphans
from ontos.core.types import DocumentData

# Count-basis labels. A surface reporting counts must say which pipeline
# produced them.
BASIS_ACTIVATION_PIPELINE = "activation_pipeline"
BASIS_GRAPH_VALIDATION = "graph_validation"
BASIS_FRONTMATTER_QUICK_SCAN = "frontmatter_quick_scan"

# Connectivity bases.
CONNECTIVITY_FROM_KERNEL = "reverse_reachability_from_kernel"
CONNECTIVITY_NOT_APPLICABLE = "not_applicable_no_kernel_docs"


def connectivity_summary(
    graph: DependencyGraph,
    files_data: Dict[str, DocumentData],
) -> Dict[str, Any]:
    """Kernel-reachability connectivity with an explicit basis marker.

    A workspace with no kernel documents reports ``connectivity: None`` and
    ``connectivity_basis: not_applicable_no_kernel_docs`` instead of a bare
    0.0 that reads as total graph failure (#133).
    """
    kernels = [
        doc_id for doc_id, node in graph.nodes.items() if node.doc_type == "kernel"
    ]

    if not kernels:
        return {
            "connectivity": None,
            "reachable_from_kernel": None,
            "kernel_docs": 0,
            "connectivity_basis": CONNECTIVITY_NOT_APPLICABLE,
        }

    reachable: set = set()

    def traverse(node: str) -> None:
        if node in reachable:
            return
        reachable.add(node)
        for child in graph.reverse_edges.get(node, []):
            traverse(child)

    for kernel_id in kernels:
        traverse(kernel_id)

    connectivity = len(reachable) / len(files_data) * 100 if files_data else 0.0
    return {
        "connectivity": connectivity,
        "reachable_from_kernel": len(reachable),
        "kernel_docs": len(kernels),
        "connectivity_basis": CONNECTIVITY_FROM_KERNEL,
    }


def orphan_summary(
    graph: DependencyGraph,
    *,
    allowed_orphan_types: Sequence[str],
    allowed_orphan_paths: Sequence[str] = (),
    workspace_root: Optional[Path] = None,
    sample_size: int = 5,
) -> Dict[str, Any]:
    """Orphan counts via the canonical detector, with the config echoed.

    This is the same ``detect_orphans`` call the validator and link-check
    use, so query --health can never disagree with them again (#133).
    """
    orphan_ids = detect_orphans(
        graph,
        set(allowed_orphan_types),
        allowed_orphan_paths=list(allowed_orphan_paths),
        workspace_root=workspace_root,
    )
    ordered = sorted(orphan_ids)
    return {
        "orphans": len(ordered),
        "orphan_ids": ordered[:sample_size],
        "orphan_basis": BASIS_GRAPH_VALIDATION,
        "allowed_orphan_types": list(allowed_orphan_types),
    }
