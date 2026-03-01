import pytest
from collections import namedtuple
from ontos.commands.map import _generate_compact_output, CompactMode

Doc = namedtuple('Doc', ['type', 'status', 'frontmatter'])

def test_compact_output_basic():
    docs = {
        "doc1": Doc(type="atom", status="active", frontmatter={}),
        "doc2": Doc(type="kernel", status="stable", frontmatter={})
    }
    output = _generate_compact_output(docs, CompactMode.BASIC)
    expected = "doc1:atom:active\ndoc2:kernel:stable"
    assert output == expected

def test_compact_output_rich_with_escaping():
    docs = {
        "doc1": Doc(type="atom", status="active", frontmatter={"summary": "Line 1\nLine 2 with \"quotes\" and \\backslash"}),
    }
    output = _generate_compact_output(docs, CompactMode.RICH)
    expected = 'doc1:atom:active:"Line 1\\nLine 2 with \\"quotes\\" and \\\\backslash"'
    assert output == expected

def test_compact_output_rich_non_string_summary():
    docs = {
        "doc1": Doc(type="atom", status="active", frontmatter={"summary": ["Line 1", "Line 2"]}),
    }
    output = _generate_compact_output(docs, CompactMode.RICH)
    # ["Line 1", "Line 2"] as string is "['Line 1', 'Line 2']"
    expected = 'doc1:atom:active:"[\'Line 1\', \'Line 2\']"'
    assert output == expected

def test_compact_output_off():
    docs = {"a": Doc(type="t", status="s", frontmatter={})}
    assert _generate_compact_output(docs, CompactMode.OFF) == ""


# === Tiered mode tests ===

from ontos.commands.map import (
    _generate_tiered_compact_output,
    GenerateMapOptions,
    generate_context_map,
)
from ontos.core.types import DocumentData, DocumentType, DocumentStatus
from pathlib import Path


def _make_doc(doc_id, doc_type, status="active", summary="", date=""):
    """Helper to create minimal DocumentData for tiered tests."""
    fm = {}
    if summary:
        fm["summary"] = summary
    if date:
        fm["date"] = date
    return DocumentData(
        id=doc_id,
        type=DocumentType(doc_type) if isinstance(doc_type, str) else doc_type,
        status=DocumentStatus(status) if isinstance(status, str) else status,
        filepath=Path(f"docs/{doc_id}.md"),
        frontmatter=fm,
        content="",
        depends_on=[],
        impacts=[],
        tags=[],
        aliases=[],
        describes=[],
    )


_MINIMAL_CONFIG = {
    "project_name": "Test",
    "project_root": "/tmp/test",
    "docs_dir": "docs",
    "logs_dir": "docs/logs",
}


def test_tiered_output_partitions_by_rank():
    docs = {
        "kern1": _make_doc("kern1", "kernel", summary="Core kernel"),
        "strat1": _make_doc("strat1", "strategy", summary="Growth plan"),
        "prod1": _make_doc("prod1", "product"),
        "atom1": _make_doc("atom1", "atom"),
        "log1": _make_doc("log1", "log", date="2026-01-01"),
    }
    opts = GenerateMapOptions()
    output = _generate_tiered_compact_output(docs, _MINIMAL_CONFIG, opts)

    # Kernel + Strategy section should contain kernel/strategy IDs in RICH format
    assert "### Kernel + Strategy" in output
    assert "kern1:kernel:active" in output
    assert "strat1:strategy:active" in output

    # Product + Atom section should contain product/atom IDs in BASIC format
    assert "### Product + Atom" in output
    assert "prod1:product:active" in output
    assert "atom1:atom:active" in output

    # Logs section
    assert "### Logs" in output
    assert "logs:1" in output
    assert "latest:log1:active" in output


def test_tiered_output_empty_partitions():
    docs = {
        "kern1": _make_doc("kern1", "kernel"),
    }
    opts = GenerateMapOptions()
    output = _generate_tiered_compact_output(docs, _MINIMAL_CONFIG, opts)

    assert "### Kernel + Strategy" in output
    assert "kern1:kernel:active" in output

    # Product + Atom and Logs should show "(none)" / "logs:0"
    assert "### Product + Atom" in output
    assert "(none)" in output
    assert "logs:0" in output


def test_tiered_log_ordering():
    docs = {
        "log_a": _make_doc("log_a", "log", date="2026-01-01"),
        "log_b": _make_doc("log_b", "log", date="2026-03-15"),
        "log_c": _make_doc("log_c", "log", date="2026-02-10"),
    }
    opts = GenerateMapOptions()
    output = _generate_tiered_compact_output(docs, _MINIMAL_CONFIG, opts)

    assert "logs:3" in output
    # Most recent date is 2026-03-15 => log_b
    assert "latest:log_b:active" in output


def test_tiered_unknown_type_goes_to_other():
    docs = {
        "ref1": _make_doc("ref1", DocumentType.REFERENCE),
    }
    opts = GenerateMapOptions()
    output = _generate_tiered_compact_output(docs, _MINIMAL_CONFIG, opts)

    assert "### Other" in output
    assert "ref1:reference:active" in output
    # Should NOT appear in Kernel+Strategy or Product+Atom
    assert "### Kernel + Strategy" in output
    ks_section = output.split("### Kernel + Strategy")[1].split("### Product")[0]
    assert "ref1" not in ks_section


def test_compact_mode_enum_tiered():
    assert CompactMode("tiered") == CompactMode.TIERED


def test_generate_context_map_dispatches_tiered():
    """Integration test: generate_context_map with TIERED mode."""
    docs = {
        "kern1": _make_doc("kern1", "kernel", summary="Core doc"),
        "log1": _make_doc("log1", "log", date="2026-01-01"),
    }
    config = dict(_MINIMAL_CONFIG)
    config["allowed_orphan_types"] = ["atom", "log"]
    opts = GenerateMapOptions(compact=CompactMode.TIERED)

    content, result = generate_context_map(docs, config, opts)

    # Should contain tiered sections
    assert "### Kernel + Strategy" in content
    assert "### Logs" in content

    # Should NOT contain full Tier 2 document index table
    assert "## Tier 2: Document Index" not in content
    assert "| Path | ID | Type | Status |" not in content

