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

    # Kernel + Strategy section should contain kernel/strategy IDs in RICH format (with summaries)
    assert "### Kernel + Strategy" in output
    assert 'kern1:kernel:active:"Core kernel"' in output
    assert 'strat1:strategy:active:"Growth plan"' in output

    # Product + Atom section should contain product/atom IDs in BASIC format
    assert "### Product + Atom" in output
    assert "prod1:product:active" in output
    assert "atom1:atom:active" in output

    # Logs section — contract: count + latest ID only (no status)
    assert "### Logs" in output
    assert "logs:1" in output
    assert "latest:log1" in output
    assert "latest:log1:" not in output  # no status appended


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
    assert "latest:log_b" in output
    assert "latest:log_b:" not in output  # no status appended


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


def test_tiered_project_root_fallback():
    """Tiered mode must see normalized config (project_root fallback)."""
    docs = {
        "kern1": _make_doc("kern1", "kernel", summary="Core doc"),
    }
    # Config WITHOUT project_root — must still work like full mode
    config = {
        "project_name": "Test",
        "docs_dir": "nonexistent_docs",
        "logs_dir": "nonexistent_logs",
        "allowed_orphan_types": ["atom", "log"],
    }
    opts = GenerateMapOptions(compact=CompactMode.TIERED)

    content, result = generate_context_map(docs, config, opts)

    # Critical Paths should still render (project_root falls back to CWD)
    assert "### Critical Paths" in content
    # The nonexistent dirs should be marked missing
    assert "(missing)" in content


def test_tiered_null_summary_renders_fallback():
    """summary: null in frontmatter should render as 'No summary', not 'None'."""
    docs = {
        "log1": _make_doc("log1", "log", date="2026-01-01"),
    }
    # Inject None summary (simulates YAML `summary: null` or `summary:`)
    docs["log1"].frontmatter["summary"] = None
    opts = GenerateMapOptions()
    output = _generate_tiered_compact_output(docs, _MINIMAL_CONFIG, opts)

    assert "### Recent Activity" in output
    assert "No summary" in output
    assert "None" not in output.split("### Recent Activity")[1].split("### Kernel")[0]


def test_tiered_empty_string_summary_is_preserved():
    """An explicit empty-string summary should stay empty, not become fallback text."""
    docs = {
        "log1": _make_doc("log1", "log", date="2026-01-01"),
    }
    docs["log1"].frontmatter["summary"] = ""
    opts = GenerateMapOptions()
    output = _generate_tiered_compact_output(docs, _MINIMAL_CONFIG, opts)

    activity = output.split("### Recent Activity")[1].split("### Kernel")[0]
    assert "| log1 | active |  |" in activity
    assert "No summary" not in activity


def test_tiered_output_empty_docs():
    """S3: True zero-doc case — every section should be empty/none."""
    docs = {}
    opts = GenerateMapOptions()
    output = _generate_tiered_compact_output(docs, _MINIMAL_CONFIG, opts)

    assert "### Kernel + Strategy" in output
    assert "### Product + Atom" in output
    assert "### Other" in output
    assert "### Logs" in output
    # All ranked sections should show (none)
    ks_section = output.split("### Kernel + Strategy")[1].split("### Product")[0]
    assert "(none)" in ks_section
    pa_section = output.split("### Product + Atom")[1].split("### Other")[0]
    assert "(none)" in pa_section
    other_section = output.split("### Other")[1].split("### Logs")[0]
    assert "(none)" in other_section
    assert "logs:0" in output


def test_tiered_log_ordering_mixed_dated_undated():
    """Dated logs must always sort above undated logs in both Tier 1 and footer."""
    docs = {
        "z_undated": _make_doc("z_undated", "log"),  # no date, ID sorts high
        "a_undated": _make_doc("a_undated", "log"),  # no date, ID sorts low
        "dated_old": _make_doc("dated_old", "log", date="2025-01-01"),
        "dated_mid": _make_doc("dated_mid", "log", date="2025-06-15"),
        "dated_new": _make_doc("dated_new", "log", date="2026-06-01"),
    }
    opts = GenerateMapOptions()
    output = _generate_tiered_compact_output(docs, _MINIMAL_CONFIG, opts)

    assert "logs:5" in output
    # Tiered footer: the dated entry with the newest date must be latest
    assert "latest:dated_new" in output
    # Tier 1 Recent Activity: dated_new must appear first in the log table
    assert "### Recent Activity" in output
    activity = output.split("### Recent Activity")[1].split("### Kernel")[0]
    assert "dated_new" in activity
    # z_undated should NOT appear in Tier 1 top-3 (dated entries take priority)
    assert "z_undated" not in activity


def test_full_map_timeline_uses_date_aware_log_ordering():
    """Full map timeline should stay aligned with Tier 1 log ordering."""
    docs = {
        "z_undated": _make_doc("z_undated", "log"),
        "a_undated": _make_doc("a_undated", "log"),
        "dated_old": _make_doc("dated_old", "log", date="2025-01-01"),
        "dated_mid": _make_doc("dated_mid", "log", date="2025-06-15"),
        "dated_new": _make_doc("dated_new", "log", date="2026-06-01"),
    }
    config = dict(_MINIMAL_CONFIG)
    config["allowed_orphan_types"] = ["atom", "log"]

    content, _ = generate_context_map(docs, config, GenerateMapOptions())

    timeline = content.rsplit("## Recent Activity", 1)[1]
    timeline_lines = [line for line in timeline.splitlines() if line.startswith("- `")]
    assert timeline_lines[0] == "- `dated_new`"


def test_tiered_non_string_summary_no_crash():
    """Non-string log summary must not crash Tier 1 log table rendering."""
    docs = {
        "log1": _make_doc("log1", "log", date="2026-01-01"),
    }
    # Inject non-string summary into frontmatter — exercises Tier 1 log table path
    docs["log1"].frontmatter["summary"] = ["list", "summary"]
    opts = GenerateMapOptions()
    # Should not raise — str() coercion prevents .replace() crash
    output = _generate_tiered_compact_output(docs, _MINIMAL_CONFIG, opts)
    assert "### Recent Activity" in output
    assert "log1" in output
    # The stringified list summary should appear somewhere in Tier 1
    assert "['list', 'summary']" in output


def test_cli_parser_compact_default_is_basic():
    """S2: --compact bare defaults to 'basic'."""
    from ontos.cli import create_parser
    parser = create_parser()
    args = parser.parse_args(["map", "--compact"])
    assert args.compact == "basic"


def test_cli_parser_compact_tiered_accepted():
    """S2: --compact tiered is accepted by map parser."""
    from ontos.cli import create_parser
    parser = create_parser()
    args = parser.parse_args(["map", "--compact", "tiered"])
    assert args.compact == "tiered"


def test_cli_parser_tree_compact_tiered_accepted():
    """S2: --compact tiered is accepted by deprecated tree parser."""
    from ontos.cli import create_parser
    parser = create_parser(include_hidden=True)
    args = parser.parse_args(["tree", "--compact", "tiered"])
    assert args.compact == "tiered"
