"""Pydantic models and JSON Schema helpers for the Ontos MCP surface."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel, TypeAdapter


class StrictModel(BaseModel):
    """Base model for MCP payloads."""

    model_config = ConfigDict(extra="forbid")


class ValidationIssue(StrictModel):
    severity: str
    message: str


class ValidationPayload(StrictModel):
    errors: List[ValidationIssue]
    warnings: List[ValidationIssue]


class GraphNodeSummary(StrictModel):
    id: str
    type: str
    status: str


class GraphEdge(StrictModel):
    from_: str = Field(alias="from")
    to: str
    type: Literal["depends_on"]

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class DocumentListItem(StrictModel):
    id: str
    type: str
    status: str
    path: str


class ToolErrorTextItem(StrictModel):
    type: Literal["text"]
    text: str


class ToolErrorEnvelope(StrictModel):
    isError: Literal[True]
    content: List[ToolErrorTextItem]


class WriteToolError(StrictModel):
    error_code: str
    what: str
    why: str
    fix: str


class WriteToolErrorEnvelope(StrictModel):
    isError: Literal[True]
    error: WriteToolError
    content: List[ToolErrorTextItem]


class KeyDocumentItem(StrictModel):
    id: str
    title: str
    type: str
    status: str


class GraphStatsByType(StrictModel):
    kernel: int
    strategy: int
    product: int
    atom: int
    log: int


class GraphStats(StrictModel):
    total: int
    by_type: GraphStatsByType


class WorkspaceOverviewResponse(StrictModel):
    summary: str
    key_documents: List[KeyDocumentItem]
    graph_stats: GraphStats
    warnings: List[ValidationIssue]


class ContextMapResponse(StrictModel):
    markdown: str
    validation: ValidationPayload


class GetDocumentMetadata(StrictModel):
    content_hash: Optional[str]
    word_count: int
    depended_by: List[str]


class GetDocumentResponse(StrictModel):
    id: str
    type: str
    status: str
    frontmatter: Dict[str, Any]
    metadata: GetDocumentMetadata
    content: Optional[str] = None


class ListDocumentsResponse(StrictModel):
    total_count: int
    offset: int
    documents: List[DocumentListItem]


class ExportGraphSummary(StrictModel):
    total_documents: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    warnings: Optional[List[str]] = None


class ExportGraphSummaryGraph(StrictModel):
    nodes: List[GraphNodeSummary]
    edges: List[GraphEdge]


class ExportGraphFullGraph(StrictModel):
    nodes: List[str]
    edges: List[GraphEdge]


class ExportGraphSummaryResponse(StrictModel):
    summary: ExportGraphSummary
    graph: ExportGraphSummaryGraph


class ExportGraphFullResponse(StrictModel):
    schema_version: Literal["ontos-export-v1"]
    provenance: Dict[str, Any]
    filters: Dict[str, Any]
    summary: ExportGraphSummary
    documents: List[Dict[str, Any]]
    graph: ExportGraphFullGraph
    validation: ValidationPayload


class ExportGraphFileResponse(StrictModel):
    success: Literal[True]
    path: str
    doc_count: int


class ExportGraphResponse(RootModel[Union[
    ExportGraphSummaryResponse,
    ExportGraphFullResponse,
    ExportGraphFileResponse,
]]):
    pass


class QueryResponse(StrictModel):
    id: str
    type: str
    status: str
    depends_on: List[str]
    depended_by: List[str]
    depth: int
    content_hash: Optional[str]


class HealthResponse(StrictModel):
    server_uptime: int
    workspace: str
    workspace_path: str
    doc_count: int
    last_indexed: str
    ontos_version: str
    snapshot_revision: int
    freshness_mode: str


class RefreshResponse(StrictModel):
    refreshed: Literal[True]
    doc_count: int
    duration_ms: int


class ProjectItem(StrictModel):
    slug: str
    path: str
    status: str
    doc_count: int
    last_updated: Optional[str]
    tags: List[str]
    has_ontos: bool


class ProjectRegistryResponse(StrictModel):
    project_count: int
    projects: List[ProjectItem]
    summary: str


class SearchResultItem(StrictModel):
    doc_id: str
    workspace_slug: str
    type: str
    status: str
    path: str
    snippet: str
    score: float


class SearchResponse(StrictModel):
    total_hits: int
    results: List[SearchResultItem]


class BundleDocumentItem(StrictModel):
    id: str
    type: str
    score: float
    token_estimate: int


class StaleDocumentItem(StrictModel):
    id: str
    reason: str


class GetContextBundleResponse(StrictModel):
    workspace_id: str
    workspace_slug: str
    token_estimate: int
    document_count: int
    bundle_text: str
    included_documents: List[BundleDocumentItem]
    excluded_count: int
    stale_documents: List[StaleDocumentItem]
    warnings: List[str]


class ScaffoldDocumentResponse(StrictModel):
    success: Literal[True]
    path: str
    id: str
    type: str
    status: str
    curation_level: str


class RenameDocumentResponse(StrictModel):
    success: Literal[True]
    old_id: str
    new_id: str
    path: str
    references_updated: int
    updated_files: List[str]


class LogSessionResponse(StrictModel):
    success: Literal[True]
    path: str
    id: str
    date: str


class PromoteDocumentResponse(StrictModel):
    success: Literal[True]
    document_id: str
    old_level: str
    new_level: str


TOOL_SUCCESS_MODELS: Dict[str, Type[BaseModel]] = {
    "workspace_overview": WorkspaceOverviewResponse,
    "context_map": ContextMapResponse,
    "get_document": GetDocumentResponse,
    "list_documents": ListDocumentsResponse,
    "export_graph": ExportGraphResponse,
    "query": QueryResponse,
    "health": HealthResponse,
    "refresh": RefreshResponse,
    "project_registry": ProjectRegistryResponse,
    "search": SearchResponse,
    "get_context_bundle": GetContextBundleResponse,
    "scaffold_document": ScaffoldDocumentResponse,
    "log_session": LogSessionResponse,
    "promote_document": PromoteDocumentResponse,
}

TOOL_OUTPUT_SCHEMAS: Dict[str, Dict[str, Any]] = {
    name: model.model_json_schema(by_alias=True)
    for name, model in TOOL_SUCCESS_MODELS.items()
}

TOOL_ERROR_SCHEMA: Dict[str, Any] = {
    "oneOf": [
        ToolErrorEnvelope.model_json_schema(by_alias=True),
        WriteToolErrorEnvelope.model_json_schema(by_alias=True),
    ]
}
EXPORT_GRAPH_ADAPTER = TypeAdapter(
    Union[ExportGraphSummaryResponse, ExportGraphFullResponse, ExportGraphFileResponse]
)


def validate_success_payload(tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize one tool success payload."""
    if tool_name == "export_graph":
        validated = EXPORT_GRAPH_ADAPTER.validate_python(payload)
        return validated.model_dump(mode="json", by_alias=True)
    model = TOOL_SUCCESS_MODELS[tool_name]
    validated = model.model_validate(payload)
    normalized = validated.model_dump(mode="json", by_alias=True)
    if tool_name == "get_document" and "content" not in payload:
        normalized.pop("content", None)
    return normalized


def output_schema_for(tool_name: str) -> Dict[str, Any]:
    """Return the JSON Schema advertised for one tool."""
    if tool_name == "export_graph":
        return {
            "oneOf": [
                ExportGraphSummaryResponse.model_json_schema(by_alias=True),
                ExportGraphFullResponse.model_json_schema(by_alias=True),
                ExportGraphFileResponse.model_json_schema(by_alias=True),
            ]
        }
    return TOOL_OUTPUT_SCHEMAS[tool_name]
