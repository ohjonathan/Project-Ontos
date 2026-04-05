from tests.mcp import build_cache, create_workspace

from ontos.mcp import tools
from ontos.mcp.schemas import output_schema_for, validate_success_payload


def test_success_payloads_validate_against_declared_schemas(tmp_path):
    cache = build_cache(create_workspace(tmp_path))
    payloads = {
        "workspace_overview": tools.workspace_overview(cache),
        "context_map": tools.context_map(cache),
        "get_document": tools.get_document(cache, document_id="atom_doc"),
        "list_documents": tools.list_documents(cache),
        "export_graph": tools.export_graph(cache, summary_only=True),
        "query": tools.query(cache, entity_id="atom_doc"),
        "health": tools.health(cache),
        "refresh": tools.refresh(cache),
    }

    for name, payload in payloads.items():
        normalized = validate_success_payload(name, payload)
        assert isinstance(normalized, dict)
        assert output_schema_for(name)


def test_export_graph_schema_is_one_of():
    schema = output_schema_for("export_graph")
    assert "oneOf" in schema
    assert len(schema["oneOf"]) == 3
