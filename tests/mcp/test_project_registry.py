import json

from ontos.mcp import tools
from ontos.mcp.schemas import validate_success_payload


class FakePortfolioIndex:
    def __init__(self, projects):
        self._projects = projects

    def get_projects(self):
        return list(self._projects)


def test_project_registry_output_shape_and_tag_parsing():
    portfolio = FakePortfolioIndex(
        [
            {
                "slug": "alpha",
                "path": "/tmp/alpha",
                "status": "active",
                "doc_count": 12,
                "last_scanned": "2026-04-11T00:00:00Z",
                "tags": json.dumps(["backend", "api"]),
                "has_ontos": 1,
            },
            {
                "slug": "beta",
                "path": "/tmp/beta",
                "status": "undocumented",
                "doc_count": 0,
                "last_scanned": None,
                "tags": "",
                "has_ontos": 0,
            },
        ]
    )

    payload = tools.project_registry(portfolio)
    normalized = validate_success_payload("project_registry", payload)

    assert normalized["project_count"] == 2
    assert normalized["projects"][0]["tags"] == ["backend", "api"]
    assert normalized["projects"][1]["tags"] == []
    assert normalized["projects"][0]["has_ontos"] is True
    assert normalized["projects"][1]["has_ontos"] is False
    assert normalized["summary"] == "Portfolio contains 2 projects."


def test_project_registry_empty_portfolio():
    portfolio = FakePortfolioIndex([])
    payload = tools.project_registry(portfolio)

    assert payload["project_count"] == 0
    assert payload["projects"] == []
    assert payload["summary"] == "Portfolio contains 0 projects."
