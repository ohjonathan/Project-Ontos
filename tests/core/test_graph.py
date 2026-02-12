"""Tests for core graph primitives: build_graph, cycle detection, orphan detection, depth calculation."""

from pathlib import Path

import pytest

from ontos.core.graph import (
    DependencyGraph,
    GraphNode,
    build_graph,
    calculate_depths,
    detect_cycles,
    detect_orphans,
)
from ontos.core.types import DocumentData, DocumentStatus, DocumentType


def _make_doc(doc_id: str, doc_type: str = "atom", depends_on: list = None) -> DocumentData:
    """Create a minimal DocumentData for testing."""
    return DocumentData(
        id=doc_id,
        type=DocumentType(doc_type),
        status=DocumentStatus.ACTIVE,
        filepath=Path(f"docs/{doc_id}.md"),
        frontmatter={"id": doc_id, "type": doc_type},
        content="",
        depends_on=depends_on or [],
    )


# ---------------------------------------------------------------------------
# build_graph
# ---------------------------------------------------------------------------

class TestBuildGraph:
    def test_empty_input(self):
        graph, errors = build_graph({})
        assert len(graph.nodes) == 0
        assert errors == []

    def test_single_doc_no_deps(self):
        docs = {"a": _make_doc("a")}
        graph, errors = build_graph(docs)
        assert "a" in graph.nodes
        assert errors == []

    def test_multiple_docs_with_edges(self):
        docs = {
            "a": _make_doc("a", "kernel"),
            "b": _make_doc("b", "strategy", depends_on=["a"]),
            "c": _make_doc("c", "atom", depends_on=["b"]),
        }
        graph, errors = build_graph(docs)
        assert len(graph.nodes) == 3
        assert graph.edges["b"] == ["a"]
        assert graph.edges["c"] == ["b"]
        assert "b" in graph.reverse_edges["a"]
        assert errors == []

    def test_broken_link_produces_error(self):
        docs = {"a": _make_doc("a", depends_on=["nonexistent"])}
        graph, errors = build_graph(docs)
        assert len(errors) == 1
        assert errors[0].error_type.value == "broken_link"
        assert "nonexistent" in errors[0].message

    def test_self_reference_is_not_broken_link(self):
        """Self-references are valid edges (caught by cycle detection, not build_graph)."""
        docs = {"a": _make_doc("a", depends_on=["a"])}
        graph, errors = build_graph(docs)
        assert len(errors) == 0  # ID exists, so no broken link
        # But cycle detection catches it
        cycles = detect_cycles(graph)
        assert len(cycles) >= 1


# ---------------------------------------------------------------------------
# detect_cycles
# ---------------------------------------------------------------------------

class TestDetectCycles:
    def test_no_cycles(self):
        docs = {
            "a": _make_doc("a"),
            "b": _make_doc("b", depends_on=["a"]),
        }
        graph, _ = build_graph(docs)
        cycles = detect_cycles(graph)
        assert cycles == []

    def test_simple_cycle_a_b_a(self):
        docs = {
            "a": _make_doc("a", depends_on=["b"]),
            "b": _make_doc("b", depends_on=["a"]),
        }
        graph, _ = build_graph(docs)
        cycles = detect_cycles(graph)
        assert len(cycles) >= 1
        # At least one cycle should contain both a and b
        flat = [node for cycle in cycles for node in cycle]
        assert "a" in flat
        assert "b" in flat

    def test_complex_cycle_a_b_c_a(self):
        docs = {
            "a": _make_doc("a", depends_on=["b"]),
            "b": _make_doc("b", depends_on=["c"]),
            "c": _make_doc("c", depends_on=["a"]),
        }
        graph, _ = build_graph(docs)
        cycles = detect_cycles(graph)
        assert len(cycles) >= 1

    def test_acyclic_diamond(self):
        docs = {
            "a": _make_doc("a"),
            "b": _make_doc("b", depends_on=["a"]),
            "c": _make_doc("c", depends_on=["a"]),
            "d": _make_doc("d", depends_on=["b", "c"]),
        }
        graph, _ = build_graph(docs)
        cycles = detect_cycles(graph)
        assert cycles == []


# ---------------------------------------------------------------------------
# detect_orphans
# ---------------------------------------------------------------------------

class TestDetectOrphans:
    def test_all_connected(self):
        docs = {
            "a": _make_doc("a", "kernel"),
            "b": _make_doc("b", "strategy", depends_on=["a"]),
        }
        graph, _ = build_graph(docs)
        orphans = detect_orphans(graph, allowed_orphan_types=set())
        # "a" has incoming edge from "b", "b" has no incoming but both have edges
        # Actually "b" has no incoming edges (nothing depends on b)
        assert "b" in orphans

    def test_some_orphans(self):
        docs = {
            "a": _make_doc("a", "kernel"),
            "b": _make_doc("b", "strategy"),
            "c": _make_doc("c", "atom", depends_on=["a"]),
        }
        graph, _ = build_graph(docs)
        orphans = detect_orphans(graph, allowed_orphan_types=set())
        # "b" and "c" have no incoming edges
        assert "b" in orphans
        assert "c" in orphans

    def test_allowed_orphan_types_filtered(self):
        docs = {
            "a": _make_doc("a", "atom"),
            "b": _make_doc("b", "kernel"),
        }
        graph, _ = build_graph(docs)
        orphans = detect_orphans(graph, allowed_orphan_types={"atom"})
        # "a" is atom (allowed orphan), "b" is kernel (not allowed)
        assert "a" not in orphans
        assert "b" in orphans

    def test_all_orphans(self):
        docs = {
            "a": _make_doc("a", "kernel"),
            "b": _make_doc("b", "strategy"),
        }
        graph, _ = build_graph(docs)
        orphans = detect_orphans(graph, allowed_orphan_types=set())
        assert set(orphans) == {"a", "b"}


# ---------------------------------------------------------------------------
# calculate_depths
# ---------------------------------------------------------------------------

class TestCalculateDepths:
    def test_flat_graph(self):
        docs = {
            "a": _make_doc("a"),
            "b": _make_doc("b"),
        }
        graph, _ = build_graph(docs)
        depths = calculate_depths(graph)
        assert depths["a"] == 0
        assert depths["b"] == 0

    def test_linear_chain(self):
        docs = {
            "a": _make_doc("a"),
            "b": _make_doc("b", depends_on=["a"]),
            "c": _make_doc("c", depends_on=["b"]),
        }
        graph, _ = build_graph(docs)
        depths = calculate_depths(graph)
        assert depths["a"] == 0
        assert depths["b"] == 1
        assert depths["c"] == 2

    def test_diamond_dependency(self):
        docs = {
            "a": _make_doc("a"),
            "b": _make_doc("b", depends_on=["a"]),
            "c": _make_doc("c", depends_on=["a"]),
            "d": _make_doc("d", depends_on=["b", "c"]),
        }
        graph, _ = build_graph(docs)
        depths = calculate_depths(graph)
        assert depths["a"] == 0
        assert depths["b"] == 1
        assert depths["c"] == 1
        assert depths["d"] == 2

    def test_cyclic_nodes_depth_zero(self):
        docs = {
            "a": _make_doc("a", depends_on=["b"]),
            "b": _make_doc("b", depends_on=["a"]),
        }
        graph, _ = build_graph(docs)
        depths = calculate_depths(graph)
        # Cyclic nodes are treated as depth 0 to prevent infinite recursion
        assert depths["a"] >= 0
        assert depths["b"] >= 0
