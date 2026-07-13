from tests.mcp_helpers import build_cache, create_empty_workspace, create_workspace

from ontos.core.ontology import get_valid_types
from ontos.mcp import tools


def _zeroed_canonical_types():
    return {doc_type: 0 for doc_type in get_valid_types()}


def test_workspace_overview_counts_and_titles(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    payload = tools.workspace_overview(cache)

    assert payload["graph_stats"]["total"] == 8
    expected_by_type = _zeroed_canonical_types()
    expected_by_type.update(
        {
            "kernel": 1,
            "strategy": 1,
            "product": 1,
            "atom": 1,
            "log": 1,
            "reference": 1,
            "concept": 1,
            "unknown": 1,
        }
    )
    assert payload["graph_stats"]["by_type"] == expected_by_type
    assert (
        sum(payload["graph_stats"]["by_type"].values())
        == payload["graph_stats"]["total"]
    )
    assert payload["key_documents"][0]["id"] == "kernel_doc"
    assert payload["key_documents"][0]["title"] == "Kernel Doc"
    assert "canonical documents in docs scope" in payload["summary"]


def test_workspace_overview_zero_document_behavior(tmp_path):
    cache = build_cache(create_empty_workspace(tmp_path))

    payload = tools.workspace_overview(cache)

    assert payload["graph_stats"]["total"] == 0
    assert payload["key_documents"] == []
    assert payload["graph_stats"]["by_type"] == _zeroed_canonical_types()
    assert (
        sum(payload["graph_stats"]["by_type"].values())
        == payload["graph_stats"]["total"]
    )
