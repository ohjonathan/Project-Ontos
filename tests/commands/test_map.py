
import pytest
import sys
from pathlib import Path
from ontos.commands.map import (
    _format_critical_path,
    map_command,
    MapOptions,
    GenerateMapOptions,
    generate_context_map,
)

def test_map_sync_agents_flag_exists():
    """--sync-agents flag is recognized."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "ontos", "map", "--help"],
        capture_output=True,
        text=True
    )
    assert "--sync-agents" in result.stdout


def test_map_sync_agents_updates_agents_md(tmp_path, monkeypatch):
    """When --sync-agents is set and AGENTS.md exists, it gets updated."""
    # Setup: Create minimal ontos project
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ontos.toml").write_text("[project]\nname = 'test'\n")
    (tmp_path / ".ontos-internal").mkdir()

    # Create initial AGENTS.md
    agents_path = tmp_path / "AGENTS.md"
    agents_path.write_text("# Old content")
    
    # We need to make sure the stats can be gathered
    (tmp_path / ".git").mkdir()

    import time
    old_mtime = agents_path.stat().st_mtime
    time.sleep(0.1)  # Ensure mtime difference

    # Run map with --sync-agents
    map_command(MapOptions(sync_agents=True))

    # Verify AGENTS.md was updated
    new_content = agents_path.read_text()
    assert "Current Project State" in new_content
    assert agents_path.stat().st_mtime > old_mtime


def test_map_sync_agents_no_create_if_missing(tmp_path, monkeypatch):
    """When --sync-agents is set but AGENTS.md doesn't exist, don't create it."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ontos.toml").write_text("[project]\nname = 'test'\n")
    (tmp_path / ".ontos-internal").mkdir()

    agents_path = tmp_path / "AGENTS.md"
    assert not agents_path.exists()

    map_command(MapOptions(sync_agents=True))

    # AGENTS.md should NOT be created
    assert not agents_path.exists()


def test_tiered_context_map_has_tier_markers(tmp_path, monkeypatch):
    """Context map includes Tier 1, 2, 3 section markers."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ontos.toml").write_text("[project]\nname = 'test'\n")
    (tmp_path / ".ontos-internal").mkdir()

    map_command(MapOptions())

    content = (tmp_path / "Ontos_Context_Map.md").read_text()
    assert "## Tier 1: Essential Context" in content
    assert "## Tier 2: Document Index" in content
    assert "## Tier 3: Full Graph Details" in content


def test_tier1_contains_project_summary(tmp_path, monkeypatch):
    """Tier 1 includes project summary section."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ontos.toml").write_text("[project]\nname = 'TestProject'\n")
    (tmp_path / ".ontos-internal").mkdir()

    map_command(MapOptions())

    content = (tmp_path / "Ontos_Context_Map.md").read_text()
    assert "### Project Summary" in content
    assert "TestProject" in content or "Doc Count" in content


def test_tier1_key_documents_format(tmp_path, monkeypatch):
    """Key Documents lists top dependents with rel path format."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ontos.toml").write_text("[project]\nname = 'TestProject'\n")
    (tmp_path / ".ontos-internal").mkdir()
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "b.md").write_text("---\nid: b\ntype: atom\nstatus: active\n---\n")
    (docs_dir / "a.md").write_text("---\nid: a\ntype: atom\nstatus: active\ndepends_on: [b]\n---\n")
    (docs_dir / "c.md").write_text("---\nid: c\ntype: atom\nstatus: active\ndepends_on: [b]\n---\n")

    map_command(MapOptions())

    content = (tmp_path / "Ontos_Context_Map.md").read_text()
    assert "### Key Documents" in content
    assert "- `b` (2 dependents) — docs/b.md" in content


def test_tier1_key_documents_omitted_when_empty(tmp_path, monkeypatch):
    """Key Documents section omitted when no dependents exist."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ontos.toml").write_text("[project]\nname = 'TestProject'\n")
    (tmp_path / ".ontos-internal").mkdir()
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "solo.md").write_text("---\nid: solo\ntype: atom\nstatus: active\n---\n")

    map_command(MapOptions())

    content = (tmp_path / "Ontos_Context_Map.md").read_text()
    assert "### Key Documents" not in content


def test_critical_paths_user_mode_excludes_ontos_internal(tmp_path, monkeypatch):
    """User mode should not expose .ontos-internal strategy path."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ontos.toml").write_text("[project]\nname = 'TestProject'\n")
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "doc.md").write_text("---\nid: doc\ntype: atom\nstatus: active\n---\n")

    map_command(MapOptions())

    content = (tmp_path / "Ontos_Context_Map.md").read_text()
    assert "### Critical Paths" in content
    assert ".ontos-internal/strategy/" not in content


def test_critical_paths_contributor_mode_includes_strategy(tmp_path, monkeypatch):
    """Contributor mode should include .ontos-internal strategy path."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ontos.toml").write_text("[project]\nname = 'TestProject'\n")
    (tmp_path / ".ontos-internal" / "strategy").mkdir(parents=True)
    (tmp_path / ".ontos-internal" / "reference").mkdir(parents=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "doc.md").write_text("---\nid: doc\ntype: atom\nstatus: active\n---\n")

    map_command(MapOptions())

    content = (tmp_path / "Ontos_Context_Map.md").read_text()
    assert ".ontos-internal/strategy/" in content
    assert ".ontos-internal/reference/" in content


def test_critical_paths_uses_custom_logs_dir(tmp_path, monkeypatch):
    """Critical Paths should reflect custom logs_dir from config."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ontos.toml").write_text(
        "[project]\nname = 'TestProject'\n[paths]\nlogs_dir = 'custom/logs'\n"
    )
    (tmp_path / "custom" / "logs").mkdir(parents=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "doc.md").write_text("---\nid: doc\ntype: atom\nstatus: active\n---\n")

    map_command(MapOptions())

    content = (tmp_path / "Ontos_Context_Map.md").read_text()
    assert "custom/logs/" in content


def test_critical_paths_missing_annotation(tmp_path, monkeypatch):
    """Missing paths should be annotated as (missing)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ontos.toml").write_text(
        "[project]\nname = 'TestProject'\n[paths]\nlogs_dir = 'custom/logs'\n"
    )
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "doc.md").write_text("---\nid: doc\ntype: atom\nstatus: active\n---\n")

    map_command(MapOptions())

    content = (tmp_path / "Ontos_Context_Map.md").read_text()
    logs_line = next(
        line for line in content.splitlines() if line.startswith("- **Logs:**")
    )
    assert "custom/logs/" in logs_line
    assert logs_line.endswith("(missing)")


def test_critical_paths_sanitizes_backticks(tmp_path, monkeypatch):
    """Backticks in config paths should be sanitized."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ontos.toml").write_text(
        "[project]\nname = 'TestProject'\n[paths]\ndocs_dir = 'docs`evil'\n"
    )
    docs_dir = tmp_path / "docs`evil"
    docs_dir.mkdir()
    (docs_dir / "doc.md").write_text("---\nid: doc\ntype: atom\nstatus: active\n---\n")

    map_command(MapOptions())

    content = (tmp_path / "Ontos_Context_Map.md").read_text()
    docs_root_line = next(
        line for line in content.splitlines() if line.startswith("- **Docs Root:**")
    )
    assert "docs`evil" not in docs_root_line
    assert "docs'evil/" in docs_root_line


def test_critical_paths_uses_custom_docs_dir(tmp_path, monkeypatch):
    """Docs root should reflect custom docs_dir from config."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ontos.toml").write_text(
        "[project]\nname = 'TestProject'\n[paths]\ndocs_dir = 'custom/docs'\n"
    )
    docs_dir = tmp_path / "custom" / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / "doc.md").write_text("---\nid: doc\ntype: atom\nstatus: active\n---\n")

    map_command(MapOptions())

    content = (tmp_path / "Ontos_Context_Map.md").read_text()
    assert "custom/docs/" in content


def test_critical_paths_rejects_absolute_path(tmp_path):
    """Absolute paths should be marked invalid."""
    root_path = tmp_path.resolve()
    assert _format_critical_path("/etc", root_path) == "`(invalid path)`"


def test_critical_paths_rejects_traversal_path(tmp_path):
    """Traversal paths should be marked invalid."""
    root_path = tmp_path.resolve()
    assert _format_critical_path("../escape", root_path) == "`(invalid path)`"


def test_critical_paths_unset_values(tmp_path):
    """Unset paths should be marked as (unset)."""
    root_path = tmp_path.resolve()
    assert _format_critical_path(None, root_path) == "`(unset)`"
    assert _format_critical_path("", root_path) == "`(unset)`"
    assert _format_critical_path("   ", root_path) == "`(unset)`"


def test_critical_paths_root_path_none():
    """Without root_path, formatting should still be safe."""
    assert _format_critical_path("docs", None) == "`docs/`"
