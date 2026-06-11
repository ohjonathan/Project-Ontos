"""
Dependency graph building and validation.

Extracted from ontos_generate_context_map.py during Phase 2 decomposition.
Implements O(V+E) DFS for cycle detection (NOT O(N²) path.index() pattern).

Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.3
"""

from __future__ import annotations
import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Set, Optional, Tuple, Union

from ontos.core.types import DocumentData, ValidationError, ValidationErrorType
from ontos.core.suggestions import SuggestionIndex, suggest_candidates

# SEVERITY RATIONALE (v3.3 Track A1)
# ---------------------------------
# - ERROR (depends_on): Structural, defines the graph integrity.
# - WARNING (impacts/describes): Informational, broken links don't corrupt traversal.
DEPENDS_ON_SEVERITY_DEFAULT = "error"
IMPACTS_SEVERITY_DEFAULT = "warning"
DESCRIBES_SEVERITY_DEFAULT = "warning"

# (#117) depends_on entries that resolve to a real file outside the loaded
# doc set are downgraded to a soft warning. The constant lives here so
# verify-frontmatter and link-check share the same severity floor.
OUT_OF_SCOPE_DEPENDENCY_SEVERITY = "warning"

# (#134) Resolved-on-disk deps matching allowed_external_dependency_paths
# are intentional doc-to-file edges, not graph damage.
EXTERNAL_FILE_DEPENDENCY_SEVERITY = "info"


def _looks_like_path(dep_id: str) -> bool:
    # A pure doc-id never contains a path separator or '.md' suffix.
    return "/" in dep_id or "\\" in dep_id or dep_id.lower().endswith(".md")


def _resolve_depends_on_path(
    dep_id: str,
    doc: DocumentData,
    docs_by_resolved_path: Dict[Path, str],
    workspace_root: Optional[Path],
    workspace_root_resolved: Optional[Path],
) -> Tuple[Optional[str], Optional[Path], Optional[Path]]:
    """Try to resolve a `depends_on` entry as a filesystem path.

    Returns (resolved_doc_id, external_path, external_resolved):
        (id, None, None) — path resolved to a loaded doc; caller treats as a
                      graph edge.
        (None, p, r) — path exists on disk inside the workspace but is not
                      loaded; caller treats as an out-of-scope dependency
                      (warning). `p` is the matched candidate (kept for
                      message stability), `r` its fully resolved form —
                      allowlist checks must use `r` so symlinked candidates
                      cannot dodge or false-match patterns (#134).
        (None, None, None) — no path resolution OR resolved path escapes the
                       workspace; caller falls back to broken-link.

    Containment: any candidate whose resolved path (with symlinks followed)
    is outside `workspace_root_resolved` is rejected (no fall-through to
    external-dep emission). This is the gemini-B.1-F1 fix — `Path.resolve`
    follows symlinks, so a malicious or buggy `depends_on: '../../etc/passwd'`
    must not leak filesystem state through the activation warnings channel.
    """
    if workspace_root is None or not _looks_like_path(dep_id):
        return None, None, None

    candidates: List[Path] = []
    raw = Path(dep_id)
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.append(workspace_root / raw)
        doc_dir = doc.filepath.parent if doc.filepath else workspace_root
        candidates.append(doc_dir / raw)

    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=False)
        except (OSError, RuntimeError):
            continue
        if workspace_root_resolved is not None:
            try:
                resolved.relative_to(workspace_root_resolved)
            except ValueError:
                continue
        if resolved in docs_by_resolved_path:
            return docs_by_resolved_path[resolved], None, None
        if candidate.exists():
            return None, candidate, resolved
    return None, None, None


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


def build_graph(
    docs: Dict[str, DocumentData],
    severity_map: Optional[Dict[str, str]] = None,
    workspace_root: Optional[Path] = None,
    allowed_external_dependency_paths: Optional[Sequence[str]] = None,
) -> Tuple[DependencyGraph, List[ValidationError]]:
    """Build dependency graph from document dictionary.

    Args:
        docs: Dictionary mapping doc_id to DocumentData
        severity_map: Optional mapping of error types to severities
        workspace_root: Optional workspace root. When provided, `depends_on`
            entries that don't match a loaded doc id are tried as
            workspace-relative, declaring-doc-relative, or absolute paths
            before being reported as broken (#117). Loaded-doc-path matches
            become normal edges; existing-but-not-loaded paths become a
            soft OUT_OF_SCOPE_DEPENDENCY warning instead of a hard error.
        allowed_external_dependency_paths: (#134) Workspace-relative globs;
            a resolved-on-disk dep matching one is reported as an
            EXTERNAL_FILE_DEPENDENCY at info severity instead of an
            out-of-scope warning.

    Returns:
        Tuple of (DependencyGraph, list of broken/out-of-scope link errors)
    """
    severity_map = severity_map or {}
    graph = DependencyGraph()
    errors: List[ValidationError] = []
    existing_ids = set(docs.keys())
    depends_on_severity = severity_map.get(
        "depends_on",
        severity_map.get("broken_link", DEPENDS_ON_SEVERITY_DEFAULT),
    )
    circular_severity = severity_map.get("circular", depends_on_severity)
    out_of_scope_severity = severity_map.get(
        "out_of_scope_dependency", OUT_OF_SCOPE_DEPENDENCY_SEVERITY
    )
    external_file_severity = severity_map.get(
        "external_file_dependency", EXTERNAL_FILE_DEPENDENCY_SEVERITY
    )
    external_allowlist = list(allowed_external_dependency_paths or [])

    # (#135) One suggestion index per build, with results memoized per unique
    # dep value — the same broken target declared from many docs used to
    # recompute fuzzy matches against the whole corpus each time.
    suggestion_index: Optional[SuggestionIndex] = None
    suggestion_memo: Dict[str, List[Tuple[str, float, str]]] = {}

    docs_by_resolved_path: Dict[Path, str] = {}
    workspace_root_resolved: Optional[Path] = None
    if workspace_root is not None:
        try:
            workspace_root_resolved = workspace_root.resolve()
        except (OSError, RuntimeError):
            workspace_root_resolved = None
        for d in docs.values():
            try:
                docs_by_resolved_path[d.filepath.resolve()] = d.id
            except (OSError, RuntimeError):
                continue

    for doc_id, doc in docs.items():
        depends_on = doc.depends_on
        doc_type = doc.type.value
        # (#117) Resolve each declared dep BEFORE building the graph node so
        # the edges + reverse_edges record doc-id targets, not raw path
        # strings. Doc-id matches and path-resolved-to-loaded-doc both
        # become regular edges; out-of-scope or broken entries are dropped
        # from the edge list and reported as ValidationErrors.
        resolved_depends_on: List[str] = []
        for dep_id in depends_on:
            if dep_id in existing_ids:
                resolved_depends_on.append(dep_id)
                continue

            resolved_id, external_path, external_resolved = _resolve_depends_on_path(
                dep_id, doc, docs_by_resolved_path, workspace_root, workspace_root_resolved
            )
            if resolved_id is not None:
                resolved_depends_on.append(resolved_id)
                continue
            if external_path is not None:
                rel_posix: Optional[str] = None
                if external_resolved is not None and workspace_root_resolved is not None:
                    try:
                        rel_posix = external_resolved.relative_to(
                            workspace_root_resolved
                        ).as_posix()
                    except ValueError:
                        rel_posix = None
                allowlisted = bool(
                    external_allowlist
                    and rel_posix is not None
                    and _path_matches_allowlist(rel_posix, external_allowlist)
                )
                if allowlisted:
                    errors.append(ValidationError(
                        error_type=ValidationErrorType.EXTERNAL_FILE_DEPENDENCY,
                        doc_id=doc_id,
                        filepath=str(doc.filepath),
                        message=(
                            f"External file dependency (allowlisted): '{dep_id}' "
                            f"(declared in {doc_id}) resolved to '{rel_posix}'."
                        ),
                        fix_suggestion="",
                        severity=external_file_severity,
                        context={
                            "dep_value": dep_id,
                            "resolved_path": rel_posix,
                            "allowlisted": True,
                        },
                    ))
                else:
                    errors.append(ValidationError(
                        error_type=ValidationErrorType.OUT_OF_SCOPE_DEPENDENCY,
                        doc_id=doc_id,
                        filepath=str(doc.filepath),
                        message=(
                            f"External dependency resolved from disk: '{dep_id}' "
                            f"(declared in {doc_id}) exists at "
                            f"'{external_path}' but is not a loaded document."
                        ),
                        fix_suggestion=(
                            "If the target should be tracked as a doc, add an "
                            "Ontos frontmatter id; otherwise this can be left as a "
                            "soft external reference."
                        ),
                        severity=out_of_scope_severity,
                        context={
                            "dep_value": dep_id,
                            "resolved_path": (
                                rel_posix if rel_posix is not None else str(external_path)
                            ),
                            "allowlisted": False,
                        },
                    ))
                continue

            if dep_id not in suggestion_memo:
                if suggestion_index is None:
                    suggestion_index = SuggestionIndex(docs)
                suggestion_memo[dep_id] = suggest_candidates(dep_id, suggestion_index)
            candidates = suggestion_memo[dep_id]
            fix_suggestion = f"Remove '{dep_id}' from depends_on or create the missing document"
            if candidates:
                suggestion_text = ", ".join(c[0] for c in candidates)
                fix_suggestion += f". Did you mean: {suggestion_text}?"

            errors.append(ValidationError(
                error_type=ValidationErrorType.BROKEN_LINK,
                doc_id=doc_id,
                filepath=str(doc.filepath),
                message=f"Broken dependency: '{dep_id}' (declared in {doc_id}) does not exist",
                fix_suggestion=fix_suggestion,
                severity=circular_severity if dep_id == doc_id else depends_on_severity
            ))

        graph.add_node(doc_id, doc_type, str(doc.filepath), resolved_depends_on)

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


def _path_matches_allowlist(rel_path: str, patterns: Sequence[str]) -> bool:
    """Return True if rel_path matches any allowlist glob pattern.

    Patterns use POSIX-style forward slashes. A trailing ``/**`` is treated as
    "any file at any depth under this directory" (prefix match). Otherwise the
    path is matched segment-by-segment with ``fnmatch.fnmatchcase`` so ``*``
    and ``?`` stay segment-local and do not span ``/``. Patterns and paths must
    have the same number of segments for a non-``/**`` match to succeed.
    Python 3.9+ compatible (no dependency on ``PurePath.full_match`` from 3.13).
    """
    rel = rel_path.replace("\\", "/")
    rel_parts = rel.split("/")
    for pattern in patterns:
        pat = pattern.replace("\\", "/")
        if pat.endswith("/**"):
            prefix = pat[:-3]
            if rel == prefix or rel.startswith(prefix + "/"):
                return True
            continue
        pat_parts = pat.split("/")
        if len(pat_parts) != len(rel_parts):
            continue
        if all(
            fnmatch.fnmatchcase(seg, pat_seg)
            for seg, pat_seg in zip(rel_parts, pat_parts)
        ):
            return True
    return False


def detect_orphans(
    graph: DependencyGraph,
    allowed_orphan_types: Set[str],
    allowed_orphan_paths: Optional[Sequence[str]] = None,
    workspace_root: Optional[Path] = None,
) -> List[str]:
    """Find documents with no incoming edges (not depended on by anyone).

    Args:
        graph: DependencyGraph to analyze
        allowed_orphan_types: Document types that are allowed to be orphans
        allowed_orphan_paths: Optional glob patterns (workspace-relative) that
            exempt their matches from the orphan check. See
            :func:`_path_matches_allowlist` for pattern semantics.
        workspace_root: Repository root used to compute relative paths for
            ``allowed_orphan_paths`` matching. Required when
            ``allowed_orphan_paths`` is non-empty.

    Returns:
        List of orphan doc_ids
    """
    orphans = []
    patterns = list(allowed_orphan_paths or ())
    ws_root = workspace_root.resolve() if workspace_root is not None else None

    for doc_id, node in graph.nodes.items():
        if node.doc_type in allowed_orphan_types:
            continue
        if patterns and ws_root is not None:
            try:
                rel = Path(node.filepath).resolve().relative_to(ws_root)
            except (ValueError, OSError):
                rel = None
            if rel is not None and _path_matches_allowlist(rel.as_posix(), patterns):
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
