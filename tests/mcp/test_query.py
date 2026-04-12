from ontos.core.content_hash import compute_content_hash
from ontos.mcp import tools

from tests.mcp import build_cache, create_workspace


def test_query_returns_graph_details(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    payload = tools.query(cache, entity_id="atom_doc")

    assert payload["depends_on"] == ["product_doc"]
    assert payload["depended_by"] == ["log_doc"]
    assert payload["depth"] >= 0
    assert payload["content_hash"] == compute_content_hash(
        cache.snapshot.documents["atom_doc"].content
    )
