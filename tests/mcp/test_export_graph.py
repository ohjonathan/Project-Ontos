import json

from ontos.mcp import tools

from tests.mcp import build_cache, create_workspace


def test_export_graph_summary_and_full_payloads(tmp_path):
    cache = build_cache(create_workspace(tmp_path))

    summary_payload = tools.export_graph(cache, summary_only=True)
    full_payload = tools.export_graph(cache, summary_only=False)

    assert isinstance(summary_payload, dict)
    assert summary_payload["summary"]["total_documents"] == 8
    assert isinstance(summary_payload["graph"]["nodes"][0], dict)
    assert "validation" in full_payload
    assert full_payload["schema_version"] == "ontos-export-v1"


def test_export_graph_file_write_takes_precedence(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)

    payload = tools.export_graph(
        cache,
        summary_only=False,
        export_to_file="exports/graph.json",
    )

    export_path = root / "exports/graph.json"
    assert payload == {
        "success": True,
        "path": "exports/graph.json",
        "doc_count": 8,
    }
    written = json.loads(export_path.read_text(encoding="utf-8"))
    assert written["schema_version"] == "ontos-export-v1"
