import sqlite3

import pytest

from ontos.core.errors import OntosUserError
from ontos.mcp import tools
from ontos.mcp.scanner import slugify
from ontos.mcp.schemas import validate_success_payload


class FakePortfolioIndex:
    def __init__(self, projects, results):
        self._projects = projects
        self._results = results
        self.calls = []

    def get_projects(self):
        return list(self._projects)

    def search_fts(self, query, workspace, offset, limit):
        self.calls.append((query, workspace, offset, limit))
        if query == "bad:[query":
            raise sqlite3.OperationalError("malformed MATCH expression")

        filtered = self._results
        if workspace is not None:
            filtered = [row for row in filtered if row["workspace_slug"] == workspace]

        return {
            "total_hits": len(filtered),
            "results": filtered[offset:offset + limit],
        }


def _portfolio():
    return FakePortfolioIndex(
        projects=[
            {"slug": "alpha"},
            {"slug": "beta"},
        ],
        results=[
            {
                "doc_id": "alpha_doc_1",
                "workspace_slug": "alpha",
                "type": "atom",
                "status": "active",
                "path": "docs/a1.md",
                "snippet": "Alpha <mark>query</mark> one",
                "score": -2.5,
            },
            {
                "doc_id": "beta_doc_1",
                "workspace_slug": "beta",
                "type": "strategy",
                "status": "active",
                "path": "docs/b1.md",
                "snippet": "Beta <mark>query</mark> two",
                "score": -1.5,
            },
            {
                "doc_id": "alpha_doc_2",
                "workspace_slug": "alpha",
                "type": "kernel",
                "status": "active",
                "path": "docs/a2.md",
                "snippet": "Alpha <mark>query</mark> three",
                "score": -0.9,
            },
        ],
    )


def test_search_basic_query_and_schema_validation():
    portfolio = _portfolio()
    payload = tools.search(portfolio, query_string="query")
    normalized = validate_success_payload("search", payload)

    assert normalized["total_hits"] == 3
    assert len(normalized["results"]) == 3
    assert portfolio.calls[-1] == ("query", None, 0, 20)


def test_search_workspace_filter_and_pagination():
    portfolio = _portfolio()

    payload = tools.search(
        portfolio,
        query_string="query",
        workspace_id="alpha",
        offset=1,
        limit=1,
    )

    assert payload["total_hits"] == 2
    assert len(payload["results"]) == 1
    assert payload["results"][0]["doc_id"] == "alpha_doc_2"
    assert portfolio.calls[-1] == ("query", "alpha", 1, 1)


def test_search_empty_results():
    portfolio = FakePortfolioIndex(
        projects=[{"slug": "alpha"}],
        results=[],
    )

    payload = tools.search(portfolio, query_string="nothing")
    assert payload == {"total_hits": 0, "results": []}


def test_search_invalid_workspace_raises_user_error():
    portfolio = _portfolio()

    with pytest.raises(OntosUserError) as exc_info:
        tools.search(portfolio, query_string="query", workspace_id="missing")

    assert exc_info.value.code == "E_UNKNOWN_WORKSPACE"


def test_search_rejects_invalid_args():
    portfolio = _portfolio()

    with pytest.raises(OntosUserError) as empty_query:
        tools.search(portfolio, query_string="   ")
    assert empty_query.value.code == "E_EMPTY_QUERY"

    with pytest.raises(OntosUserError) as invalid_limit:
        tools.search(portfolio, query_string="query", limit=0)
    assert invalid_limit.value.code == "E_INVALID_LIMIT"

    with pytest.raises(OntosUserError) as invalid_offset:
        tools.search(portfolio, query_string="query", offset=-1)
    assert invalid_offset.value.code == "E_INVALID_OFFSET"


def test_search_maps_sqlite_syntax_errors_to_ontos_user_error():
    portfolio = _portfolio()

    with pytest.raises(OntosUserError) as exc_info:
        tools.search(portfolio, query_string="bad:[query")

    assert exc_info.value.code == "E_INVALID_QUERY"


def test_search_preserves_snippets_and_bm25_ordering():
    portfolio = _portfolio()
    payload = tools.search(portfolio, query_string="query")

    assert [result["doc_id"] for result in payload["results"]] == [
        "alpha_doc_1",
        "beta_doc_1",
        "alpha_doc_2",
    ]
    assert all("<mark>" in result["snippet"] for result in payload["results"])


def test_tools_slugify_workspace_name_matches_scanner():
    assert tools._slugify_workspace_name("my--project") == slugify("my--project")
