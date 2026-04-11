from datetime import date, timedelta

import pytest

from ontos.core.errors import OntosUserError
from ontos.mcp import tools
from ontos.mcp.schemas import validate_success_payload

from tests.mcp import build_cache, create_workspace, write_file


class FakePortfolioIndex:
    def __init__(self, projects):
        self._projects = projects

    def get_projects(self):
        return list(self._projects)


def test_get_context_bundle_single_workspace_mode_uses_cache_snapshot(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)

    payload = tools.get_context_bundle(None, cache, token_budget=8192, workspace_id="ignored")
    normalized = validate_success_payload("get_context_bundle", payload)

    assert normalized["workspace_slug"] == "workspace"
    assert normalized["workspace_id"] == "workspace"
    assert normalized["document_count"] >= 1
    score_map = {item["id"]: item["score"] for item in normalized["included_documents"]}
    assert "kernel_doc" in score_map
    assert score_map["kernel_doc"] == 1.0


def test_get_context_bundle_budget_bounds(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    with pytest.raises(OntosUserError) as low_budget:
        tools.get_context_bundle(None, cache, token_budget=1000)
    assert low_budget.value.code == "E_INVALID_BUDGET"

    with pytest.raises(OntosUserError) as high_budget:
        tools.get_context_bundle(None, cache, token_budget=200000)
    assert high_budget.value.code == "E_INVALID_BUDGET"


def test_get_context_bundle_portfolio_mode_requires_workspace(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)
    portfolio = FakePortfolioIndex(
        [
            {
                "slug": "alpha",
                "path": str(root),
                "status": "active",
                "doc_count": 8,
                "last_scanned": None,
                "tags": "[]",
                "has_ontos": 1,
            }
        ]
    )

    with pytest.raises(OntosUserError) as exc_info:
        tools.get_context_bundle(portfolio, cache)

    assert exc_info.value.code == "E_MISSING_WORKSPACE"


def test_get_context_bundle_portfolio_mode_rejects_undocumented_workspace(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)
    portfolio = FakePortfolioIndex(
        [
            {
                "slug": "alpha",
                "path": str(root),
                "status": "undocumented",
                "doc_count": 0,
                "last_scanned": None,
                "tags": "[]",
                "has_ontos": 0,
            }
        ]
    )

    with pytest.raises(OntosUserError) as exc_info:
        tools.get_context_bundle(portfolio, cache, workspace_id="alpha")

    assert exc_info.value.code == "E_UNDOCUMENTED_WORKSPACE"


def test_get_context_bundle_log_window_and_score(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)
    today = date.today().isoformat()
    old = (date.today() - timedelta(days=60)).isoformat()
    write_file(
        root / f"docs/{today}_recent-log.md",
        f"""
        ---
        id: {today}_recent_log
        type: log
        status: active
        date: {today}
        depends_on: [atom_doc]
        ---
        Recent log body.
        """,
    )
    write_file(
        root / f"docs/{old}_old-log.md",
        f"""
        ---
        id: {old}_old_log
        type: log
        status: active
        date: {old}
        depends_on: [atom_doc]
        ---
        Old log body.
        """,
    )

    payload = tools.get_context_bundle(None, cache, token_budget=8192)
    score_map = {item["id"]: item["score"] for item in payload["included_documents"]}

    assert score_map[f"{today}_recent_log"] == 0.3
    assert score_map[f"{old}_old_log"] >= 0.5


def test_get_context_bundle_detects_stale_documents(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)
    write_file(
        root / "docs/atom.md",
        """
        ---
        id: atom_doc
        type: atom
        status: active
        depends_on: [product_doc]
        describes: [concept_doc]
        describes_verified: 2000-01-01
        ---
        Atom body for hashing.
        """,
    )

    payload = tools.get_context_bundle(None, cache, token_budget=8192)
    stale_ids = {item["id"] for item in payload["stale_documents"]}

    assert "atom_doc" in stale_ids
