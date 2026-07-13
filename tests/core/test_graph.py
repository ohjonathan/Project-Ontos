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
# build_graph — #117 depends_on path-fallback resolution
# ---------------------------------------------------------------------------


class TestDependsOnPathFallback:
    """`depends_on` entries that don't match a doc id but resolve against the
    workspace filesystem should be either repaired silently (when they
    point at a loaded doc) or downgraded to a soft OUT_OF_SCOPE_DEPENDENCY
    warning (when they point at an existing non-loaded file). Hard
    broken-link errors are reserved for genuinely missing targets. (#117)"""

    def _docs(self, tmp_path, layout):
        """Build a doc dict whose filepaths sit inside `tmp_path`.

        `layout` is a sequence of (doc_id, rel_path, depends_on) tuples.
        Each rel_path file is created so `.exists()` is true.
        """
        docs = {}
        for doc_id, rel_path, depends_on in layout:
            abs_path = tmp_path / rel_path
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text(f"# {doc_id}\n")
            docs[doc_id] = DocumentData(
                id=doc_id,
                type=DocumentType.ATOM,
                status=DocumentStatus.ACTIVE,
                filepath=abs_path,
                frontmatter={"id": doc_id, "type": "atom"},
                content="",
                depends_on=list(depends_on),
            )
        return docs

    def test_workspace_relative_path_resolves_to_loaded_doc(self, tmp_path):
        docs = self._docs(
            tmp_path,
            [
                ("kernel", "docs/kernel.md", []),
                ("strategy", "docs/strategy.md", ["docs/kernel.md"]),
            ],
        )
        graph, errors = build_graph(docs, workspace_root=tmp_path)
        assert errors == []
        # Edge was repaired to point at the doc id; the raw path string
        # must NOT appear as a graph edge (claude-opus B.1 F1 — doc-id
        # graph cleanliness).
        assert graph.edges["strategy"] == ["kernel"]
        assert "docs/kernel.md" not in graph.edges["strategy"]
        assert "strategy" in graph.reverse_edges["kernel"]
        assert "docs/kernel.md" not in graph.reverse_edges

    def test_declaring_doc_relative_path_resolves_to_loaded_doc(self, tmp_path):
        docs = self._docs(
            tmp_path,
            [
                ("a", "docs/sub/a.md", []),
                ("b", "docs/sub/b.md", ["a.md"]),
            ],
        )
        graph, errors = build_graph(docs, workspace_root=tmp_path)
        assert errors == []
        assert "a" in graph.edges["b"]

    def test_existing_non_loaded_path_is_out_of_scope_warning(self, tmp_path):
        # Create the dep target on disk but do not load it.
        (tmp_path / ".llm-dev/framework").mkdir(parents=True, exist_ok=True)
        (tmp_path / ".llm-dev/framework/framework.md").write_text("framework")
        docs = self._docs(
            tmp_path,
            [("orchestrator", "docs/orchestrator.md", [".llm-dev/framework/framework.md"])],
        )
        graph, errors = build_graph(docs, workspace_root=tmp_path)
        assert len(errors) == 1
        assert errors[0].error_type.value == "out_of_scope_dependency"
        assert errors[0].severity == "warning"
        assert ".llm-dev/framework/framework.md" in errors[0].message

    def test_missing_path_falls_through_to_broken_link(self, tmp_path):
        docs = self._docs(
            tmp_path,
            [("a", "docs/a.md", ["docs/does-not-exist.md"])],
        )
        graph, errors = build_graph(docs, workspace_root=tmp_path)
        assert len(errors) == 1
        assert errors[0].error_type.value == "broken_link"
        assert errors[0].severity == "error"

    def test_no_workspace_root_preserves_legacy_behavior(self, tmp_path):
        # Without workspace_root, a path-shaped dep is reported as broken-link
        # exactly as before (back-compat for existing call sites).
        docs = self._docs(
            tmp_path,
            [("a", "docs/a.md", ["docs/does-not-exist.md"])],
        )
        graph, errors = build_graph(docs)
        assert len(errors) == 1
        assert errors[0].error_type.value == "broken_link"

    def test_path_traversal_outside_workspace_is_treated_as_broken(self, tmp_path):
        # gemini B.1 F1 — depends_on entries that resolve outside the workspace
        # root (e.g., `../../etc/passwd`) must NOT leak through the
        # activation warnings channel as out-of-scope dependencies. They
        # fall through to broken-link severity instead.
        outside = tmp_path.parent / "secrets"
        outside.mkdir(parents=True, exist_ok=True)
        (outside / "vault.md").write_text("nope")

        docs = self._docs(
            tmp_path,
            [
                ("a", "docs/a.md", ["../secrets/vault.md"]),
            ],
        )
        graph, errors = build_graph(docs, workspace_root=tmp_path)
        # The traversal-escaping path is reported as broken (error), not as
        # an out-of-scope dependency (warning that would otherwise leak the
        # external filesystem state).
        assert len(errors) == 1
        assert errors[0].error_type.value == "broken_link"
        assert errors[0].severity == "error"
        assert "vault.md" in errors[0].message

    def test_doc_id_match_takes_precedence_over_path(self, tmp_path):
        # An entry that matches a loaded doc id is NEVER tried as a path
        # (back-compat for the canonical doc-id depends_on usage).
        docs = self._docs(
            tmp_path,
            [
                ("kernel", "docs/kernel.md", []),
                ("strategy", "docs/strategy.md", ["kernel"]),
            ],
        )
        graph, errors = build_graph(docs, workspace_root=tmp_path)
        assert errors == []
        assert "kernel" in graph.edges["strategy"]

    def test_case_only_path_resolves_identically_on_every_filesystem(self, tmp_path):
        docs = self._docs(
            tmp_path,
            [
                ("kernel", "docs/Kernel.md", []),
                ("strategy", "docs/strategy.md", ["docs/KERNEL.md"]),
            ],
        )

        graph, errors = build_graph(docs, workspace_root=tmp_path)

        assert errors == []
        assert graph.edges["strategy"] == ["kernel"]

    def test_casefold_collision_fails_closed_instead_of_picking_a_doc(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        source_path = docs_dir / "source.md"
        source_path.write_text("source", encoding="utf-8")

        docs = {
            "upper": _make_doc("upper"),
            "lower": _make_doc("lower"),
            "source": _make_doc("source", depends_on=["docs/TARGET.md"]),
        }
        # These paths need not exist: the collision is in the loaded-document
        # registry and must be handled consistently even on case-insensitive
        # filesystems that cannot create both names.
        docs["upper"].filepath = docs_dir / "Target.md"
        docs["lower"].filepath = docs_dir / "target.md"
        docs["source"].filepath = source_path

        graph, errors = build_graph(docs, workspace_root=tmp_path)

        assert graph.edges["source"] == []
        assert len(errors) == 1
        assert errors[0].error_type.value == "broken_link"
        assert errors[0].context["dep_value"] == "docs/TARGET.md"

    def test_same_physical_path_collision_fails_closed(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        target = docs_dir / "target.md"
        target.write_text("target", encoding="utf-8")
        source = docs_dir / "source.md"
        source.write_text("source", encoding="utf-8")

        docs = {
            "first": _make_doc("first"),
            "second": _make_doc("second"),
            "source": _make_doc("source", depends_on=["docs/target.md"]),
        }
        docs["first"].filepath = target
        docs["second"].filepath = target
        docs["source"].filepath = source

        graph, errors = build_graph(docs, workspace_root=tmp_path)

        assert graph.edges["source"] == []
        assert [error.error_type.value for error in errors] == ["broken_link"]

    def test_broken_dependency_preserves_quoted_value_in_context(self, tmp_path):
        docs = self._docs(
            tmp_path,
            [("source", "docs/source.md", ["don't-exist"])],
        )

        _, errors = build_graph(docs, workspace_root=tmp_path)

        assert errors[0].context == {"dep_value": "don't-exist"}


# ---------------------------------------------------------------------------
# (#117) README / *_template.md loader skip
# ---------------------------------------------------------------------------


def test_readme_files_are_skipped_unless_they_declare_explicit_id(tmp_path):
    """README.md and *_template.md sit alongside data docs but rarely carry
    valid frontmatter; the loader must skip them unless they opt back in via
    an explicit `id:` field (escape hatch)."""
    from ontos.io.files import load_documents
    from ontos.io.yaml import parse_frontmatter_content

    readme_no_id = tmp_path / "docs/logs/README.md"
    readme_no_id.parent.mkdir(parents=True, exist_ok=True)
    readme_no_id.write_text("# Logs README\n\nNo frontmatter here.\n")

    template_no_id = tmp_path / "docs/notes_template.md"
    template_no_id.write_text("# Notes Template\n")

    explicit_readme = tmp_path / "docs/explicit/README.md"
    explicit_readme.parent.mkdir(parents=True, exist_ok=True)
    explicit_readme.write_text("---\nid: explicit_readme\ntype: log\n---\n")

    regular = tmp_path / "docs/regular.md"
    regular.write_text("---\nid: regular_doc\ntype: log\n---\n")

    result = load_documents(
        [readme_no_id, template_no_id, explicit_readme, regular],
        parse_frontmatter_content,
    )

    assert set(result.documents.keys()) == {"regular_doc", "explicit_readme"}


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

    def test_deep_cycle_is_iterative_and_canonical(self):
        graph = DependencyGraph()
        node_count = 1500
        for index in range(node_count):
            dependency = [f"node_{(index + 1) % node_count:04d}"]
            graph.add_node(f"node_{index:04d}", "atom", "", dependency)

        cycles = detect_cycles(graph)

        assert len(cycles) == 1
        assert cycles[0][0] == "node_0000"
        assert cycles[0][-1] == "node_0000"
        assert len(cycles[0]) == node_count + 1

    def test_cycle_output_is_independent_of_insertion_and_edge_order(self):
        first = DependencyGraph()
        first.add_node("a", "atom", "", ["c", "b"])
        first.add_node("b", "atom", "", ["a"])
        first.add_node("c", "atom", "", ["a"])

        second = DependencyGraph()
        second.add_node("c", "atom", "", ["a"])
        second.add_node("b", "atom", "", ["a"])
        second.add_node("a", "atom", "", ["b", "c"])

        assert detect_cycles(first) == detect_cycles(second)


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

    def test_allowed_orphan_paths_filters_by_directory(self, tmp_path):
        ws = tmp_path
        log_file = ws / "docs" / "logs" / "2026-05-23_session.md"
        log_file.parent.mkdir(parents=True)
        log_file.write_text("---\nid: log_a\n---\n")
        review_file = ws / "docs" / "reviews" / "proj-x" / "B.1.md"
        review_file.parent.mkdir(parents=True)
        review_file.write_text("---\nid: review_b\n---\n")
        loose_file = ws / "docs" / "specs" / "loose.md"
        loose_file.parent.mkdir(parents=True)
        loose_file.write_text("---\nid: loose_c\n---\n")

        docs = {
            "log_a": DocumentData(
                id="log_a",
                type=DocumentType("kernel"),
                status=DocumentStatus.ACTIVE,
                filepath=log_file,
                frontmatter={"id": "log_a"},
                content="",
                depends_on=[],
            ),
            "review_b": DocumentData(
                id="review_b",
                type=DocumentType("kernel"),
                status=DocumentStatus.ACTIVE,
                filepath=review_file,
                frontmatter={"id": "review_b"},
                content="",
                depends_on=[],
            ),
            "loose_c": DocumentData(
                id="loose_c",
                type=DocumentType("kernel"),
                status=DocumentStatus.ACTIVE,
                filepath=loose_file,
                frontmatter={"id": "loose_c"},
                content="",
                depends_on=[],
            ),
        }
        graph, _ = build_graph(docs)
        orphans = detect_orphans(
            graph,
            allowed_orphan_types=set(),
            allowed_orphan_paths=["docs/logs/**", "docs/reviews/**"],
            workspace_root=ws,
        )
        assert orphans == ["loose_c"]

    def test_allowed_orphan_paths_glob_pattern(self, tmp_path):
        ws = tmp_path
        match_file = ws / "docs" / "reference" / "Migration_v3_to_v4.md"
        match_file.parent.mkdir(parents=True)
        match_file.write_text("---\nid: migration_a\n---\n")
        miss_file = ws / "docs" / "reference" / "Glossary.md"
        miss_file.write_text("---\nid: glossary_b\n---\n")

        docs = {
            "migration_a": DocumentData(
                id="migration_a",
                type=DocumentType("kernel"),
                status=DocumentStatus.ACTIVE,
                filepath=match_file,
                frontmatter={"id": "migration_a"},
                content="",
                depends_on=[],
            ),
            "glossary_b": DocumentData(
                id="glossary_b",
                type=DocumentType("kernel"),
                status=DocumentStatus.ACTIVE,
                filepath=miss_file,
                frontmatter={"id": "glossary_b"},
                content="",
                depends_on=[],
            ),
        }
        graph, _ = build_graph(docs)
        orphans = detect_orphans(
            graph,
            allowed_orphan_types=set(),
            allowed_orphan_paths=["docs/reference/Migration_*.md"],
            workspace_root=ws,
        )
        assert orphans == ["glossary_b"]

    def test_allowed_orphan_paths_star_is_segment_local(self, tmp_path):
        """`*` must not span `/` — `docs/reference/Migration_*.md` must NOT
        match `docs/reference/Migration_v5/foo.md`. Otherwise the allowlist
        becomes wider than documented and silently hides orphan docs that
        happen to live under a `Migration_*` subdirectory.
        """
        ws = tmp_path
        nested = ws / "docs" / "reference" / "Migration_v5" / "foo.md"
        nested.parent.mkdir(parents=True)
        nested.write_text("---\nid: nested_a\n---\n")

        docs = {
            "nested_a": DocumentData(
                id="nested_a",
                type=DocumentType("kernel"),
                status=DocumentStatus.ACTIVE,
                filepath=nested,
                frontmatter={"id": "nested_a"},
                content="",
                depends_on=[],
            ),
        }
        graph, _ = build_graph(docs)
        orphans = detect_orphans(
            graph,
            allowed_orphan_types=set(),
            allowed_orphan_paths=["docs/reference/Migration_*.md"],
            workspace_root=ws,
        )
        assert orphans == ["nested_a"]


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

    def test_deep_chain_does_not_depend_on_python_recursion_limit(self):
        graph = DependencyGraph()
        node_count = 2000
        for index in range(node_count):
            dependencies = [] if index == 0 else [f"node_{index - 1:04d}"]
            graph.add_node(f"node_{index:04d}", "atom", "", dependencies)

        assert detect_cycles(graph) == []
        depths = calculate_depths(graph)

        assert depths["node_0000"] == 0
        assert depths[f"node_{node_count - 1:04d}"] == node_count - 1

    def test_cycle_component_has_stable_shared_depth(self):
        graph = DependencyGraph()
        graph.add_node("a", "atom", "", ["b", "leaf"])
        graph.add_node("b", "atom", "", ["a"])
        graph.add_node("leaf", "atom", "", [])
        graph.add_node("parent", "atom", "", ["a"])

        depths = calculate_depths(graph)

        assert depths["a"] == depths["b"] == 1
        assert depths["parent"] == 2


class TestExternalDependencyAllowlist:
    """(#134) Resolved-on-disk deps matching allowed_external_dependency_paths
    are reported as EXTERNAL_FILE_DEPENDENCY at info severity; non-matching
    ones keep today's OUT_OF_SCOPE_DEPENDENCY warning; missing paths stay
    broken-link errors."""

    def _docs(self, tmp_path, layout):
        docs = {}
        for doc_id, rel_path, depends_on in layout:
            abs_path = tmp_path / rel_path
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text(f"# {doc_id}\n")
            docs[doc_id] = DocumentData(
                id=doc_id,
                type=DocumentType.ATOM,
                status=DocumentStatus.ACTIVE,
                filepath=abs_path,
                frontmatter={"id": doc_id, "type": "atom"},
                content="",
                depends_on=list(depends_on),
            )
        return docs

    def test_allowlisted_dep_is_info_with_context(self, tmp_path):
        (tmp_path / "apps/audio/src").mkdir(parents=True, exist_ok=True)
        (tmp_path / "apps/audio/src/embed.py").write_text("code")
        docs = self._docs(
            tmp_path,
            [("handoff", "docs/handoff.md", ["apps/audio/src/embed.py"])],
        )

        graph, errors = build_graph(
            docs,
            workspace_root=tmp_path,
            allowed_external_dependency_paths=["apps/**"],
        )

        assert len(errors) == 1
        error = errors[0]
        assert error.error_type.value == "external_file_dependency"
        assert error.severity == "info"
        assert error.context == {
            "dep_value": "apps/audio/src/embed.py",
            "resolved_path": "apps/audio/src/embed.py",
            "allowlisted": True,
        }

    def test_non_allowlisted_dep_keeps_exact_out_of_scope_message(self, tmp_path):
        (tmp_path / "tools").mkdir(parents=True, exist_ok=True)
        (tmp_path / "tools/script.py").write_text("code")
        docs = self._docs(
            tmp_path,
            [("handoff", "docs/handoff.md", ["tools/script.py"])],
        )

        graph, errors = build_graph(
            docs,
            workspace_root=tmp_path,
            allowed_external_dependency_paths=["apps/**"],
        )

        assert len(errors) == 1
        error = errors[0]
        assert error.error_type.value == "out_of_scope_dependency"
        assert error.severity == "warning"
        # Message stays byte-identical to the pre-#134 text.
        assert error.message == (
            "External dependency resolved from disk: 'tools/script.py' "
            "(declared in handoff) exists at "
            f"'{tmp_path / 'tools/script.py'}' but is not a loaded document."
        )
        assert error.context["allowlisted"] is False

    def test_missing_path_still_broken_link(self, tmp_path):
        docs = self._docs(
            tmp_path,
            [("a", "docs/a.md", ["apps/does-not-exist.py"])],
        )

        graph, errors = build_graph(
            docs,
            workspace_root=tmp_path,
            allowed_external_dependency_paths=["apps/**"],
        )

        assert len(errors) == 1
        assert errors[0].error_type.value == "broken_link"

    def test_glob_is_segment_local(self, tmp_path):
        # apps/*.py must NOT match apps/sub/x.py (segment-local *).
        (tmp_path / "apps/sub").mkdir(parents=True, exist_ok=True)
        (tmp_path / "apps/sub/x.py").write_text("code")
        docs = self._docs(
            tmp_path,
            [("a", "docs/a.md", ["apps/sub/x.py"])],
        )

        graph, errors = build_graph(
            docs,
            workspace_root=tmp_path,
            allowed_external_dependency_paths=["apps/*.py"],
        )

        assert errors[0].error_type.value == "out_of_scope_dependency"

    def test_symlink_matches_on_resolved_path(self, tmp_path):
        # A dep declared through a symlink must be allowlisted by its
        # RESOLVED location, not the symlink's apparent path.
        (tmp_path / "real").mkdir(parents=True, exist_ok=True)
        (tmp_path / "real/target.py").write_text("code")
        (tmp_path / "apps").mkdir(parents=True, exist_ok=True)
        (tmp_path / "apps/linked.py").symlink_to(tmp_path / "real/target.py")
        docs = self._docs(
            tmp_path,
            [("a", "docs/a.md", ["apps/linked.py"])],
        )

        graph, errors = build_graph(
            docs,
            workspace_root=tmp_path,
            allowed_external_dependency_paths=["apps/**"],
        )

        # Resolves to real/target.py which is NOT under apps/ -> not allowlisted.
        assert errors[0].error_type.value == "out_of_scope_dependency"
        assert errors[0].context["allowlisted"] is False
