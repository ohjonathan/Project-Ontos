from __future__ import annotations

from ontos.mcp import tools
from ontos.mcp.portfolio import PortfolioIndex
from ontos.mcp.schemas import validate_success_payload

from tests.mcp import build_cache, create_workspace


def test_portfolio_index_outputs_validate_against_track_a_tools(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)
    index = PortfolioIndex(tmp_path / "portfolio.db")

    index.rebuild_workspace("workspace", root)

    registry_payload = validate_success_payload("project_registry", tools.project_registry(index))
    search_payload = validate_success_payload(
        "search",
        tools.search(index, query_string="Atom", workspace_id="workspace"),
    )
    bundle_payload = validate_success_payload(
        "get_context_bundle",
        tools.get_context_bundle(index, cache, workspace_id="workspace", token_budget=2048),
    )

    assert registry_payload["project_count"] == 1
    assert registry_payload["projects"][0]["slug"] == "workspace"
    assert search_payload["total_hits"] >= 1
    assert search_payload["results"][0]["workspace_slug"] == "workspace"
    assert bundle_payload["workspace_slug"] == "workspace"
    assert bundle_payload["document_count"] >= 1
