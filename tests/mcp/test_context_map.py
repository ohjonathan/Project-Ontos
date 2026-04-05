from ontos.commands.map import CompactMode, GenerateMapOptions, generate_context_map
from ontos.mcp import tools

from tests.mcp import build_cache, create_empty_workspace, create_workspace


def _map_config(cache):
    return {
        "project_root": str(cache.workspace_root),
        "project_name": cache.workspace_root.name,
        "version": cache.config.ontos.version,
        "allowed_orphan_types": cache.config.validation.allowed_orphan_types,
        "docs_dir": str(cache.config.paths.docs_dir),
        "logs_dir": str(cache.config.paths.logs_dir),
        "is_contributor_mode": (cache.workspace_root / ".ontos-internal").is_dir(),
    }


def test_context_map_full_alias_matches_off_mode(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    payload = tools.context_map(cache, compact="full")
    expected_markdown, _ = generate_context_map(
        cache.snapshot.documents,
        _map_config(cache),
        GenerateMapOptions(compact=CompactMode.OFF),
    )

    assert payload["markdown"] == expected_markdown
    assert payload["validation"]["errors"] == []


def test_context_map_zero_document_behavior(tmp_path):
    cache = build_cache(create_empty_workspace(tmp_path))

    payload = tools.context_map(cache, compact="tiered")

    assert "**Doc Count:** 0" in payload["markdown"]
    assert isinstance(payload["validation"], dict)
