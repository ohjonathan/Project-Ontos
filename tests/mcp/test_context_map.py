import pytest

from ontos.commands.map import CompactMode, GenerateMapOptions, generate_context_map
from ontos.core.types import ValidationErrorType
from ontos.mcp import tools

from tests.mcp_helpers import (
    build_cache,
    create_empty_workspace,
    create_workspace,
    write_file,
)


def _map_config(cache):
    from ontos.io.scan_scope import resolve_scan_scope

    return {
        "project_root": str(cache.workspace_root),
        "project_name": cache.workspace_root.name,
        "scope": resolve_scan_scope(None, cache.config.scanning.default_scope).value,
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


@pytest.mark.parametrize(("configured_max", "expected_depth_warnings"), [(10, 0), (0, 8)])
def test_context_map_honors_snapshot_dependency_depth(
    tmp_path,
    configured_max,
    expected_depth_warnings,
):
    root = tmp_path / "depth-workspace"
    root.mkdir()
    write_file(
        root / ".ontos.toml",
        f"""
        [ontos]
        version = "4.0"

        [validation]
        max_dependency_depth = {configured_max}
        """,
    )
    for index in range(9):
        dependency = f"depends_on: [doc_{index + 1}]" if index < 8 else ""
        write_file(
            root / f"docs/doc_{index}.md",
            f"""
            ---
            id: doc_{index}
            type: atom
            status: active
            {dependency}
            ---
            """,
        )
    cache = build_cache(root)

    payload = tools.context_map(cache, compact="full")
    snapshot_depth = [
        warning
        for warning in cache.snapshot.validation_result.warnings
        if warning.error_type == ValidationErrorType.DEPTH
    ]
    map_depth = [
        warning
        for warning in payload["validation"]["warnings"]
        if warning["rule_id"] == "depth"
    ]

    assert len(snapshot_depth) == expected_depth_warnings
    assert len(map_depth) == expected_depth_warnings
