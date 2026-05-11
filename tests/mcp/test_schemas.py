from ontos.mcp import tools
from ontos.mcp.schemas import (
    ActivateResponse,
    LogSessionResponse,
    PromoteDocumentResponse,
    RenameDocumentResponse,
    ScaffoldDocumentResponse,
    SessionEndResponse,
    TOOL_ERROR_SCHEMA,
    TOOL_SUCCESS_MODELS,
    WriteToolErrorEnvelope,
    output_schema_for,
    validate_success_payload,
)

from tests.mcp import build_cache, create_workspace


class FakePortfolioIndex:
    def __init__(self, projects, results):
        self._projects = projects
        self._results = results

    def get_projects(self):
        return list(self._projects)

    def search_fts(self, query, workspace, offset, limit):
        filtered = self._results
        if workspace:
            filtered = [row for row in filtered if row["workspace_slug"] == workspace]
        return {
            "total_hits": len(filtered),
            "results": filtered[offset:offset + limit],
        }


def test_success_payloads_validate_against_declared_schemas(tmp_path):
    root = create_workspace(tmp_path)
    cache = build_cache(root)
    portfolio = FakePortfolioIndex(
        projects=[
            {
                "slug": "workspace",
                "path": str(root),
                "status": "active",
                "doc_count": 8,
                "last_scanned": "2026-04-11T00:00:00Z",
                "tags": '["core"]',
                "has_ontos": 1,
            }
        ],
        results=[
            {
                "doc_id": "atom_doc",
                "workspace_slug": "workspace",
                "type": "atom",
                "status": "active",
                "path": "docs/atom.md",
                "snippet": "Atom <mark>body</mark>",
                "score": -1.2,
            }
        ],
    )
    payloads = {
        "activate": tools.activate(cache),
        "workspace_overview": tools.workspace_overview(cache),
        "context_map": tools.context_map(cache),
        "get_document": tools.get_document(cache, document_id="atom_doc"),
        "list_documents": tools.list_documents(cache),
        "export_graph": tools.export_graph(cache, summary_only=True),
        "query": tools.query(cache, entity_id="atom_doc"),
        "health": tools.health(cache),
        "refresh": tools.refresh(cache),
        "project_registry": tools.project_registry(portfolio),
        "search": tools.search(portfolio, query_string="body"),
        "get_context_bundle": tools.get_context_bundle(None, cache, token_budget=2048),
    }

    for name, payload in payloads.items():
        normalized = validate_success_payload(name, payload)
        assert isinstance(normalized, dict)
        schema = output_schema_for(name)
        assert schema is None or schema.get("type") == "object"


def test_export_graph_schema_is_omitted():
    # See schemas.output_schema_for: export_graph advertises no outputSchema
    # because its three response shapes can't be expressed as a single object
    # schema without a breaking change to the return type.
    assert output_schema_for("export_graph") is None


def test_every_advertised_output_schema_is_object_typed():
    for name in TOOL_SUCCESS_MODELS:
        schema = output_schema_for(name)
        assert schema is None or schema["type"] == "object", (
            f"Tool '{name}' advertises a non-object outputSchema; MCP clients "
            "validate structuredContent as an object and will reject the "
            "entire tools/list response."
        )


def test_write_tool_models_validate_success_payload_shapes():
    ActivateResponse.model_validate(
        {
            "status": "usable",
            "workspace": "workspace",
            "workspace_path": "/tmp/workspace",
            "doc_count": 1,
            "loaded_ids": ["doc_1"],
            "warnings": [],
            "recommendation": "continue",
        }
    )
    ScaffoldDocumentResponse.model_validate(
        {
            "success": True,
            "path": "docs/new.md",
            "id": "new_doc",
            "type": "atom",
            "status": "scaffold",
            "curation_level": "L0",
        }
    )
    RenameDocumentResponse.model_validate(
        {
            "success": True,
            "old_id": "old_doc",
            "new_id": "new_doc",
            "path": "docs/old.md",
            "references_updated": 2,
            "updated_files": ["docs/old.md", "docs/strategy.md"],
        }
    )
    LogSessionResponse.model_validate(
        {
            "success": True,
            "path": "docs/logs/2026-04-11_session.md",
            "id": "2026-04-11_session",
            "date": "2026-04-11",
        }
    )
    SessionEndResponse.model_validate(
        {
            "success": True,
            "path": "docs/logs/2026-04-11_session-end.md",
            "id": "2026-04-11_session-end",
            "date": "2026-04-11",
        }
    )
    PromoteDocumentResponse.model_validate(
        {
            "success": True,
            "document_id": "doc_1",
            "old_level": "L1",
            "new_level": "L2",
        }
    )


def test_error_schema_supports_write_tool_error_envelope():
    envelope = WriteToolErrorEnvelope.model_validate(
        {
            "isError": True,
            "error": {
                "error_code": "E_DUPLICATE_ID",
                "what": "Document already exists",
                "why": "Document IDs must be unique",
                "fix": "Choose a different ID",
            },
            "content": [{"type": "text", "text": "Document already exists."}],
        }
    )
    assert envelope.isError is True
    assert "oneOf" in TOOL_ERROR_SCHEMA
    assert len(TOOL_ERROR_SCHEMA["oneOf"]) == 2
