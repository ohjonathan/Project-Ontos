from ontos.mcp import tools

from tests.mcp import build_cache, create_workspace


def test_list_documents_filters_sort_and_pagination(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    payload = tools.list_documents(cache, offset=1, limit=3)
    filtered = tools.list_documents(cache, type="reference")
    empty_page = tools.list_documents(cache, offset=50, limit=10)

    assert payload["total_count"] == 8
    assert [doc["id"] for doc in payload["documents"]] == [
        "strategy_doc",
        "product_doc",
        "atom_doc",
    ]
    assert filtered["documents"][0]["id"] == "reference_doc"
    assert empty_page["documents"] == []


def test_list_documents_includes_extended_types(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    payload = tools.list_documents(cache)
    ids = {doc["id"] for doc in payload["documents"]}

    assert "_template" not in ids
    assert {"reference_doc", "concept_doc", "unknown_doc"} <= ids
