"""Shared link diagnostics orchestration for link-check and maintain."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from ontos.core.body_refs import MatchType, scan_body_references
from ontos.core.config import OntosConfig
from ontos.core.graph import build_graph, detect_orphans
from ontos.core.suggestions import suggest_candidates_for_broken_ref
from ontos.core.types import DocumentData, ValidationErrorType
from ontos.core.validation import ValidationOrchestrator
from ontos.io.files import DocumentLoadIssue, DocumentLoadResult, load_documents, scan_documents
from ontos.io.scan_scope import ScanScope
from ontos.io.yaml import parse_frontmatter_content

_QUOTED_VALUE_RE = re.compile(r"'([^']+)'")
_LINK_CHECK_SEVERITY = {
    "broken_link": "error",
    "depends_on": "error",
    "impacts": "error",
    "describes": "error",
}


@dataclass(frozen=True)
class ReferenceSuggestion:
    """Candidate fix for a broken reference."""

    candidate: str
    confidence: float
    reason: str


@dataclass(frozen=True)
class ReferenceLocation:
    """Optional body-reference location data."""

    line: int
    col_start: int
    col_end: int
    zone: str
    match_type: str


@dataclass
class BrokenReference:
    """Broken reference finding."""

    source_doc_id: str
    source_path: Path
    field: str
    value: str
    severity: str = "error"
    location: Optional[ReferenceLocation] = None
    suggestions: List[ReferenceSuggestion] = field(default_factory=list)


@dataclass
class ExternalReference:
    """Reference that resolves outside active scope."""

    source_doc_id: str
    source_path: Path
    field: str
    value: str
    resolved_external_id: str


@dataclass(frozen=True)
class ParseFailedCandidate:
    """Reference candidate found in parse-failed raw scan."""

    path: Path
    line: int
    match_type: str
    candidate: str


@dataclass(frozen=True)
class OrphanDocument:
    """Scope-relative orphan output."""

    doc_id: str
    path: Path
    doc_type: str


@dataclass(frozen=True)
class LinkDiagnosticsSummary:
    """Summary counters for result output."""

    files_scanned: int
    documents_loaded: int
    load_warnings: int
    duplicate_ids: int
    broken_references: int
    broken_frontmatter: int
    broken_body: int
    external_references: int
    parse_failed_candidates: int
    orphans: int


@dataclass
class LinkDiagnosticsResult:
    """Unified diagnostics output."""

    status: str
    scope: ScanScope
    exit_code: int
    summary: LinkDiagnosticsSummary
    duplicates: Dict[str, List[Path]]
    broken_references: List[BrokenReference]
    external_references: List[ExternalReference]
    parse_failed_candidates: List[ParseFailedCandidate]
    orphans: List[OrphanDocument]
    load_warnings: List[DocumentLoadIssue]

    def to_json(self) -> Dict[str, object]:
        """Convert diagnostics to JSON-compatible payload."""

        duplicates = [
            {
                "id": doc_id,
                "paths": [str(path) for path in sorted(paths)],
            }
            for doc_id, paths in sorted(self.duplicates.items())
        ]

        broken = []
        for finding in self.broken_references:
            if finding.location is None:
                location: Optional[Dict[str, object]] = None
            else:
                location = {
                    "line": finding.location.line,
                    "col_start": finding.location.col_start,
                    "col_end": finding.location.col_end,
                    "zone": finding.location.zone,
                    "match_type": finding.location.match_type,
                }

            broken.append(
                {
                    "source_doc_id": finding.source_doc_id,
                    "source_path": str(finding.source_path),
                    "field": finding.field,
                    "value": finding.value,
                    "severity": finding.severity,
                    "location": location,
                    "suggestions": [
                        {
                            "candidate": suggestion.candidate,
                            "confidence": suggestion.confidence,
                            "reason": suggestion.reason,
                        }
                        for suggestion in finding.suggestions
                    ],
                }
            )

        payload = {
            "status": self.status,
            "scope": self.scope.value,
            "exit_code": self.exit_code,
            "summary": {
                "files_scanned": self.summary.files_scanned,
                "documents_loaded": self.summary.documents_loaded,
                "load_warnings": self.summary.load_warnings,
                "duplicate_ids": self.summary.duplicate_ids,
                "broken_references": self.summary.broken_references,
                "broken_frontmatter": self.summary.broken_frontmatter,
                "broken_body": self.summary.broken_body,
                "external_references": self.summary.external_references,
                "parse_failed_candidates": self.summary.parse_failed_candidates,
                "orphans": self.summary.orphans,
            },
            "duplicates": duplicates,
            "broken_references": broken,
            "external_references": [
                {
                    "source_doc_id": finding.source_doc_id,
                    "source_path": str(finding.source_path),
                    "field": finding.field,
                    "value": finding.value,
                    "resolved_external_id": finding.resolved_external_id,
                }
                for finding in self.external_references
            ],
            "parse_failed_candidates": [
                {
                    "path": str(item.path),
                    "line": item.line,
                    "match_type": item.match_type,
                    "candidate": item.candidate,
                }
                for item in self.parse_failed_candidates
            ],
            "orphans": [
                {
                    "doc_id": orphan.doc_id,
                    "path": str(orphan.path),
                    "type": orphan.doc_type,
                }
                for orphan in self.orphans
            ],
            "load_warnings": [
                {
                    "code": issue.code,
                    "path": str(issue.path),
                    "message": issue.message,
                }
                for issue in self.load_warnings
            ],
        }
        return payload

    def to_json_text(self) -> str:
        return json.dumps(self.to_json(), ensure_ascii=False)


@dataclass(frozen=True)
class _ExternalScopeInfo:
    external_ids: Set[str]
    external_depends_on_index: Set[str]


def run_link_diagnostics(
    *,
    repo_root: Path,
    config: OntosConfig,
    doc_paths: Sequence[Path],
    scope: ScanScope,
    include_body: bool = True,
    include_external_scope_resolution: bool = True,
    include_suggestions: bool = True,
    load_result: Optional[DocumentLoadResult] = None,
) -> LinkDiagnosticsResult:
    """Run shared link diagnostics for a loaded scope."""

    if load_result is None:
        load_result = load_documents(list(doc_paths), parse_frontmatter_content)

    docs = load_result.documents
    active_ids = set(docs.keys())
    external_scope = _load_external_scope_info(
        repo_root=repo_root,
        config=config,
        scope=scope,
        include_external_scope_resolution=include_external_scope_resolution,
    )
    external_ids = external_scope.external_ids

    broken_references: List[BrokenReference] = []
    external_references: List[ExternalReference] = []
    broken_seen: Set[Tuple[str, str, str, Optional[int], Optional[int], Optional[str]]] = set()
    external_seen: Set[Tuple[str, str, str, str]] = set()

    graph, broken_depends_on = build_graph(docs, severity_map=_LINK_CHECK_SEVERITY)
    for error in broken_depends_on:
        value = _extract_reference_value(error.message)
        if value is None:
            continue
        _classify_reference(
            source_doc_id=error.doc_id,
            source_path=Path(error.filepath),
            field="depends_on",
            value=value,
            severity=error.severity,
            location=None,
            active_ids=active_ids,
            external_ids=external_ids,
            all_docs=docs,
            include_suggestions=include_suggestions,
            broken_references=broken_references,
            external_references=external_references,
            broken_seen=broken_seen,
            external_seen=external_seen,
        )

    orchestrator = ValidationOrchestrator(
        docs,
        config={"severity_map": _LINK_CHECK_SEVERITY},
    )
    orchestrator.validate_impacts(severity="error")
    orchestrator.validate_describes(severity="error")
    for validation_error in [*orchestrator.errors, *orchestrator.warnings]:
        if validation_error.error_type == ValidationErrorType.IMPACTS:
            field = "impacts"
        elif (
            validation_error.error_type == ValidationErrorType.SCHEMA
            and validation_error.message.startswith("describes ")
        ):
            field = "describes"
        else:
            continue
        value = _extract_reference_value(validation_error.message)
        if value is None:
            continue
        _classify_reference(
            source_doc_id=validation_error.doc_id,
            source_path=Path(validation_error.filepath),
            field=field,
            value=value,
            severity=validation_error.severity,
            location=None,
            active_ids=active_ids,
            external_ids=external_ids,
            all_docs=docs,
            include_suggestions=include_suggestions,
            broken_references=broken_references,
            external_references=external_references,
            broken_seen=broken_seen,
            external_seen=external_seen,
        )

    if include_body:
        for doc in docs.values():
            # Pass 1: Known-ID scan — bypasses _looks_like_doc_id filters,
            # ensuring references to existing docs with filtered-pattern
            # names (e.g., "v3.2", "depends_on") are always detected.
            known_scan = scan_body_references(
                path=doc.filepath,
                body=doc.content,
                known_ids=active_ids,
                include_skipped=False,
            )
            # Pass 2: Generic unknown scan — finds references to IDs that
            # don't exist (broken reference detection).  Uses the
            # _looks_like_doc_id filter to suppress false positives.
            generic_scan = scan_body_references(
                path=doc.filepath,
                body=doc.content,
                include_skipped=False,
            )
            # Merge both passes, deduplicating by position.
            seen_positions: set[tuple[int, int]] = set()
            all_body_matches = []
            for body_match in known_scan.matches:
                pos_key = (body_match.abs_start, body_match.abs_end)
                if pos_key not in seen_positions:
                    seen_positions.add(pos_key)
                    all_body_matches.append(body_match)
            for body_match in generic_scan.matches:
                pos_key = (body_match.abs_start, body_match.abs_end)
                if pos_key not in seen_positions:
                    seen_positions.add(pos_key)
                    all_body_matches.append(body_match)

            for body_match in all_body_matches:
                field = (
                    "body.markdown_link_target"
                    if body_match.match_type == MatchType.MARKDOWN_LINK_TARGET
                    else "body.bare_id_token"
                )
                location = ReferenceLocation(
                    line=body_match.line,
                    col_start=body_match.col_start,
                    col_end=body_match.col_end,
                    zone=body_match.zone.value,
                    match_type=body_match.match_type.value,
                )
                _classify_reference(
                    source_doc_id=doc.id,
                    source_path=doc.filepath,
                    field=field,
                    value=body_match.normalized_id,
                    severity="error",
                    location=location,
                    active_ids=active_ids,
                    external_ids=external_ids,
                    all_docs=docs,
                    include_suggestions=include_suggestions,
                    broken_references=broken_references,
                    external_references=external_references,
                    broken_seen=broken_seen,
                    external_seen=external_seen,
                )

    parse_failed_candidates = _collect_parse_failed_candidates(
        issues=load_result.issues,
        known_ids=active_ids | external_ids,
    )

    allowed_orphan_types = set(config.validation.allowed_orphan_types)
    orphan_ids = detect_orphans(graph, allowed_orphan_types)
    if scope == ScanScope.DOCS and external_scope.external_depends_on_index:
        orphan_ids = [
            orphan_id
            for orphan_id in orphan_ids
            if orphan_id not in external_scope.external_depends_on_index
        ]

    orphans = [
        OrphanDocument(
            doc_id=doc_id,
            path=docs[doc_id].filepath,
            doc_type=docs[doc_id].type.value,
        )
        for doc_id in sorted(orphan_ids)
        if doc_id in docs
    ]

    broken_frontmatter = len(
        [
            finding
            for finding in broken_references
            if finding.field in {"depends_on", "impacts", "describes"}
        ]
    )
    broken_body = len(broken_references) - broken_frontmatter

    duplicates = {doc_id: sorted(paths) for doc_id, paths in load_result.duplicate_ids.items()}

    exit_code = _resolve_exit_code(
        duplicate_count=len(duplicates),
        broken_count=len(broken_references),
        orphan_count=len(orphans),
    )

    summary = LinkDiagnosticsSummary(
        files_scanned=len(doc_paths),
        documents_loaded=len(docs),
        load_warnings=len(load_result.issues),
        duplicate_ids=len(duplicates),
        broken_references=len(broken_references),
        broken_frontmatter=broken_frontmatter,
        broken_body=broken_body,
        external_references=len(external_references),
        parse_failed_candidates=len(parse_failed_candidates),
        orphans=len(orphans),
    )

    return LinkDiagnosticsResult(
        status="success",
        scope=scope,
        exit_code=exit_code,
        summary=summary,
        duplicates=duplicates,
        broken_references=broken_references,
        external_references=external_references,
        parse_failed_candidates=parse_failed_candidates,
        orphans=orphans,
        load_warnings=load_result.issues,
    )


def _classify_reference(
    *,
    source_doc_id: str,
    source_path: Path,
    field: str,
    value: str,
    severity: str,
    location: Optional[ReferenceLocation],
    active_ids: Set[str],
    external_ids: Set[str],
    all_docs: Dict[str, DocumentData],
    include_suggestions: bool,
    broken_references: List[BrokenReference],
    external_references: List[ExternalReference],
    broken_seen: Set[Tuple[str, str, str, Optional[int], Optional[int], Optional[str]]],
    external_seen: Set[Tuple[str, str, str, str]],
) -> None:
    if value in active_ids:
        return
    if value in external_ids:
        key = (source_doc_id, str(source_path), field, value)
        if key not in external_seen:
            external_seen.add(key)
            external_references.append(
                ExternalReference(
                    source_doc_id=source_doc_id,
                    source_path=source_path,
                    field=field,
                    value=value,
                    resolved_external_id=value,
                )
            )
        return

    if location is None:
        location_key: Tuple[Optional[int], Optional[int], Optional[str]] = (None, None, None)
    else:
        location_key = (location.line, location.col_start, location.match_type)
    key = (source_doc_id, field, value, *location_key)
    if key in broken_seen:
        return
    broken_seen.add(key)

    suggestions = _build_suggestions(value, all_docs) if include_suggestions else []
    broken_references.append(
        BrokenReference(
            source_doc_id=source_doc_id,
            source_path=source_path,
            field=field,
            value=value,
            severity=severity or "error",
            location=location,
            suggestions=suggestions,
        )
    )


def _build_suggestions(value: str, docs: Dict[str, DocumentData]) -> List[ReferenceSuggestion]:
    candidates = suggest_candidates_for_broken_ref(value, docs)
    return [
        ReferenceSuggestion(candidate=candidate, confidence=confidence, reason=reason)
        for candidate, confidence, reason in candidates
    ]


def _extract_reference_value(message: str) -> Optional[str]:
    match = _QUOTED_VALUE_RE.search(message)
    if match is None:
        return None
    return match.group(1)


def _resolve_exit_code(duplicate_count: int, broken_count: int, orphan_count: int) -> int:
    if duplicate_count > 0 or broken_count > 0:
        return 1
    if orphan_count > 0:
        return 2
    return 0


def _load_external_scope_info(
    *,
    repo_root: Path,
    config: OntosConfig,
    scope: ScanScope,
    include_external_scope_resolution: bool,
) -> _ExternalScopeInfo:
    if scope != ScanScope.DOCS or not include_external_scope_resolution:
        return _ExternalScopeInfo(external_ids=set(), external_depends_on_index=set())

    external_root = repo_root / ".ontos-internal"
    if not external_root.exists():
        return _ExternalScopeInfo(external_ids=set(), external_depends_on_index=set())

    external_paths = scan_documents(
        [external_root],
        skip_patterns=list(config.scanning.skip_patterns),
    )
    external_load = load_documents(external_paths, parse_frontmatter_content)
    external_ids = set(external_load.documents.keys())
    external_depends_on = {
        dependency
        for doc in external_load.documents.values()
        for dependency in doc.depends_on
    }
    return _ExternalScopeInfo(
        external_ids=external_ids,
        external_depends_on_index=external_depends_on,
    )


def _collect_parse_failed_candidates(
    *,
    issues: Sequence[DocumentLoadIssue],
    known_ids: Set[str],
) -> List[ParseFailedCandidate]:
    candidate_paths = sorted(
        {
            issue.path
            for issue in issues
            if issue.code in {"parse_error", "io_error"}
        }
    )
    findings: List[ParseFailedCandidate] = []
    seen: Set[Tuple[Path, int, str, str]] = set()

    for path in candidate_paths:
        content = _decode_file_lenient(path)
        if content is None:
            continue
        scan = scan_body_references(
            path=path,
            body=content,
            rename_target=None,
            known_ids=known_ids,
            include_skipped=True,
        )
        for match in scan.matches:
            key = (path, match.line, match.match_type.value, match.normalized_id)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                ParseFailedCandidate(
                    path=path,
                    line=match.line,
                    match_type=match.match_type.value,
                    candidate=match.normalized_id,
                )
            )
    return findings


def _decode_file_lenient(path: Path) -> Optional[str]:
    try:
        raw_bytes = path.read_bytes()
    except OSError:
        return None
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        raw_bytes = raw_bytes[3:]
    return raw_bytes.decode("utf-8", errors="replace")

