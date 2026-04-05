from tests.mcp import build_cache, create_empty_workspace, create_workspace

from ontos.mcp import tools


def test_workspace_overview_counts_and_titles(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    payload = tools.workspace_overview(cache)

    assert payload["graph_stats"]["total"] == 8
    assert payload["graph_stats"]["by_type"] == {
        "kernel": 1,
        "strategy": 1,
        "product": 1,
        "atom": 1,
        "log": 1,
    }
    assert payload["key_documents"][0]["id"] == "kernel_doc"
    assert payload["key_documents"][0]["title"] == "Kernel Doc"
    assert "canonical documents in docs scope" in payload["summary"]


def test_workspace_overview_zero_document_behavior(tmp_path):
    cache = build_cache(create_empty_workspace(tmp_path))

    payload = tools.workspace_overview(cache)

    assert payload["graph_stats"]["total"] == 0
    assert payload["key_documents"] == []
    assert payload["graph_stats"]["by_type"] == {
        "kernel": 0,
        "strategy": 0,
        "product": 0,
        "atom": 0,
        "log": 0,
    }
