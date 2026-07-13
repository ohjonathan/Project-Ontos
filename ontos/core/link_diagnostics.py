"""Shared link diagnostics orchestration for link-check and maintain."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import unquote

from ontos.core.body_refs import MatchType, scan_body_references
from ontos.core.config import OntosConfig
from ontos.core.graph import _LoadedPathIndex, build_graph, detect_orphans
from ontos.core.suggestions import SuggestionIndex, suggest_candidates
from ontos.core.types import DocumentData, ValidationErrorType
from ontos.core.validation import ValidationOrchestrator
from ontos.io.files import DocumentLoadIssue, DocumentLoadResult, load_documents, scan_documents
from ontos.io.scan_scope import ScanScope
from ontos.io.yaml import parse_frontmatter_content, split_frontmatter_text

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
class FileDependencyReference:
    """Reference target that exists on disk but is not a loaded doc.

    For ``depends_on``, `allowlisted` reflects the project's external-file
    allowlist.  Ordinary Markdown file links are informational and therefore
    use ``allowlisted=True`` so they never drive the dependency exit gate.
    """

    source_doc_id: str
    source_path: Path
    value: str
    resolved_path: str
    allowlisted: bool
    severity: str
    field: str = "depends_on"


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
    # (#134) Resolved-on-disk depends_on targets, re-bucketed out of
    # broken_references. Only the unallowlisted subset drives exit code 1.
    file_dependencies: int = 0
    unallowlisted_file_dependencies: int = 0


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
    timings_ms: Dict[str, int] = field(default_factory=dict)
    file_dependencies: List[FileDependencyReference] = field(default_factory=list)
    # (#133) Basis label for the orphan counter: docs-scope runs that
    # filtered out orphans depended on from .ontos-internal say so.
    orphan_basis: str = "graph_validation"

    @property
    def result_status(self) -> str:
        """Result quality derived from evidence, not only the shell code."""
        if self.exit_code == 1:
            return "failing"
        if self.summary.load_warnings or self.summary.parse_failed_candidates:
            return "incomplete"
        if self.exit_code == 3:
            return "warnings"
        return "clean"

    def to_data_payload(
        self,
        *,
        limit: Optional[int] = None,
        summary_only: bool = False,
        options_echo: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        """Build the `data` payload for the standard JSON envelope (#131/#135).

        Summary counters always reflect FULL totals; ``limit`` caps only the
        findings lists, and ``summary_only`` empties them. Keys are stable in
        every mode so consumers never branch on key presence.
        """

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

        sections: Dict[str, List[object]] = {
            "duplicates": duplicates,
            "broken_references": broken,
            "file_dependencies": [
                {
                    "source_doc_id": item.source_doc_id,
                    "source_path": str(item.source_path),
                    "field": item.field,
                    "value": item.value,
                    "resolved_path": item.resolved_path,
                    "allowlisted": item.allowlisted,
                    "severity": item.severity,
                }
                for item in self.file_dependencies
            ],
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

        truncated_sections: List[str] = []
        for name, items in sections.items():
            if summary_only:
                if items:
                    truncated_sections.append(name)
                sections[name] = []
            elif limit is not None and len(items) > limit:
                truncated_sections.append(name)
                sections[name] = items[:limit]

        payload: Dict[str, object] = {
            "result_status": self.result_status,
            "mode": "summary" if summary_only else "full",
            "scope": self.scope.value,
            "options": dict(options_echo or {}),
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
                "file_dependencies": self.summary.file_dependencies,
                "unallowlisted_file_dependencies": (
                    self.summary.unallowlisted_file_dependencies
                ),
            },
            "timings_ms": dict(self.timings_ms),
            "count_basis": {
                "orphans": self.orphan_basis,
                "broken_references": "frontmatter_plus_body",
                "file_dependencies": "frontmatter_and_body_resolved_on_disk",
            },
            "findings_truncated": bool(truncated_sections),
            "truncated_sections": sorted(truncated_sections),
        }
        payload.update(sections)
        return payload

    def to_json_text(self) -> str:
        """Deprecated: retained for any out-of-tree callers; emits the
        envelope `data` payload, not the pre-3.4 root shape."""
        return json.dumps(self.to_data_payload(), ensure_ascii=False)


@dataclass(frozen=True)
class _ExternalScopeInfo:
    external_ids: Set[str]
    external_depends_on_index: Set[str]
    documents: Dict[str, DocumentData]


@dataclass(frozen=True)
class _ResolvedMarkdownTarget:
    """Filesystem-aware classification of a Markdown link target."""

    document_id: Optional[str] = None
    resolved_path: Optional[str] = None
    ambiguous: bool = False


def run_link_diagnostics(
    *,
    repo_root: Path,
    config: OntosConfig,
    doc_paths: Sequence[Path],
    scope: ScanScope,
    include_body: bool = True,
    include_external_scope_resolution: bool = True,
    include_suggestions: bool = True,
    include_orphans: bool = True,
    progress: Optional[Callable[[str], None]] = None,
    load_result: Optional[DocumentLoadResult] = None,
) -> LinkDiagnosticsResult:
    """Run shared link diagnostics for a loaded scope.

    ``progress`` is invoked with a short stage marker at the start of each
    phase (#135); pass None for silent runs. ``include_orphans=False`` skips
    orphan detection entirely, which also removes the exit-2 possibility.
    Per-phase wall-clock timings land in ``LinkDiagnosticsResult.timings_ms``.
    """

    timings_ms: Dict[str, int] = {}
    total_start = time.perf_counter()

    def _notify(message: str) -> None:
        if progress is not None:
            progress(message)

    phase_start = time.perf_counter()
    if load_result is None:
        _notify(f"Loading {len(doc_paths)} documents...")
        load_result = load_documents(list(doc_paths), parse_frontmatter_content)
        timings_ms["load"] = _elapsed_ms(phase_start)
    else:
        timings_ms["load"] = 0

    docs = load_result.documents
    active_ids = set(docs.keys())
    phase_start = time.perf_counter()
    external_scope = _load_external_scope_info(
        repo_root=repo_root,
        config=config,
        scope=scope,
        include_external_scope_resolution=include_external_scope_resolution,
    )
    timings_ms["external_scope"] = _elapsed_ms(phase_start)
    external_ids = external_scope.external_ids
    active_path_index = _LoadedPathIndex.from_documents(docs)
    external_path_index = _LoadedPathIndex.from_documents(external_scope.documents)

    broken_references: List[BrokenReference] = []
    external_references: List[ExternalReference] = []
    broken_seen: Set[Tuple[str, str, str, Optional[int], Optional[int], Optional[str]]] = set()
    external_seen: Set[Tuple[str, str, str, str]] = set()

    _notify("Checking frontmatter references...")
    phase_start = time.perf_counter()
    # (#117) Thread repo_root through so depends_on entries that resolve to
    # workspace-relative paths can fall back from hard broken-link to either
    # edge-resolution (loaded doc) or soft out-of-scope dependency.
    graph, broken_depends_on = build_graph(
        docs,
        severity_map=_LINK_CHECK_SEVERITY,
        workspace_root=repo_root,
        allowed_external_dependency_paths=(
            config.validation.allowed_external_dependency_paths
        ),
    )
    file_dependencies: List[FileDependencyReference] = []
    file_dep_seen: Set[Tuple[str, str, str]] = set()
    for error in broken_depends_on:
        # (#134) Resolved-on-disk deps carry structured context and land in
        # the file_dependencies bucket instead of broken_references.
        if error.error_type in (
            ValidationErrorType.OUT_OF_SCOPE_DEPENDENCY,
            ValidationErrorType.EXTERNAL_FILE_DEPENDENCY,
        ):
            dep_value = error.context.get("dep_value", "")
            key = (error.doc_id, str(error.filepath), dep_value)
            if key in file_dep_seen:
                continue
            file_dep_seen.add(key)
            file_dependencies.append(
                FileDependencyReference(
                    source_doc_id=error.doc_id,
                    source_path=Path(error.filepath),
                    value=dep_value,
                    resolved_path=error.context.get("resolved_path", ""),
                    allowlisted=bool(error.context.get("allowlisted", False)),
                    severity=error.severity,
                )
            )
            continue
        value = error.context.get("dep_value")
        if not isinstance(value, str):
            # Backward-compatible fallback for ValidationError producers that
            # predate structured context.  build_graph always supplies it.
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
            broken_references=broken_references,
            external_references=external_references,
            broken_seen=broken_seen,
            external_seen=external_seen,
        )
    timings_ms["frontmatter"] = _elapsed_ms(phase_start)

    phase_start = time.perf_counter()
    if include_body:
        _notify(f"Scanning body references in {len(docs)} documents...")
        for doc in docs.values():
            # Generic unknown scan — finds broken references to
            # IDs that don't exist. (#117) The prose-token heuristic
            # (`_looks_like_doc_id`) produced ~11k false positives per
            # 163-doc corpus; it is now disabled by passing
            # include_generic_bare_id_token=False. Broken markdown link
            # targets still surface because link_target detection is
            # independent of the bare-token heuristic. Broken bare
            # references inside explicit `[[id]]` wikilink sigils still
            # surface via _iter_wikilink_id_candidates.
            body_scan = scan_body_references(
                path=doc.filepath,
                body=doc.content,
                include_skipped=False,
                include_generic_bare_id_token=False,
            )
            body_line_offset = _body_line_offset(doc)

            for body_match in body_scan.matches:
                field = (
                    "body.markdown_link_target"
                    if body_match.match_type == MatchType.MARKDOWN_LINK_TARGET
                    else "body.bare_id_token"
                )
                location = ReferenceLocation(
                    line=body_line_offset + body_match.line,
                    col_start=body_match.col_start,
                    col_end=body_match.col_end,
                    zone=body_match.zone.value,
                    match_type=body_match.match_type.value,
                )

                value = body_match.normalized_id
                if (
                    body_match.match_type == MatchType.MARKDOWN_LINK_TARGET
                    and value not in active_ids
                    and value not in external_ids
                ):
                    resolution = _resolve_markdown_target(
                        raw_target=body_match.raw_match,
                        source_path=doc.filepath,
                        repo_root=repo_root,
                        active_paths=active_path_index,
                        external_paths=external_path_index,
                    )
                    if resolution.document_id is not None:
                        value = resolution.document_id
                    elif resolution.resolved_path is not None:
                        key = (doc.id, field, resolution.resolved_path)
                        if key not in file_dep_seen:
                            file_dep_seen.add(key)
                            file_dependencies.append(
                                FileDependencyReference(
                                    source_doc_id=doc.id,
                                    source_path=doc.filepath,
                                    field=field,
                                    value=body_match.raw_match,
                                    resolved_path=resolution.resolved_path,
                                    allowlisted=True,
                                    severity="info",
                                )
                            )
                        continue

                _classify_reference(
                    source_doc_id=doc.id,
                    source_path=doc.filepath,
                    field=field,
                    value=value,
                    severity="error",
                    location=location,
                    active_ids=active_ids,
                    external_ids=external_ids,
                    broken_references=broken_references,
                    external_references=external_references,
                    broken_seen=broken_seen,
                    external_seen=external_seen,
                )
    timings_ms["body_scan"] = _elapsed_ms(phase_start)

    # (#135) Suggestions run as a memoized post-pass over the collected
    # broken references instead of inline per finding, so the phase is
    # timeable, skippable, and never recomputes the same broken value.
    phase_start = time.perf_counter()
    if include_suggestions and broken_references:
        _notify(
            f"Generating suggestions for {len(broken_references)} broken references..."
        )
        _attach_suggestions(broken_references, docs)
    timings_ms["suggestions"] = _elapsed_ms(phase_start)

    phase_start = time.perf_counter()
    if load_result.issues:
        _notify("Scanning parse-failed files...")
    parse_failed_candidates = _collect_parse_failed_candidates(
        issues=load_result.issues,
        known_ids=active_ids | external_ids,
    )
    timings_ms["parse_failed_scan"] = _elapsed_ms(phase_start)

    phase_start = time.perf_counter()
    orphans: List[OrphanDocument] = []
    orphan_basis = "graph_validation"
    if include_orphans:
        _notify("Detecting orphans...")
        allowed_orphan_types = set(config.validation.allowed_orphan_types)
        allowed_orphan_paths = list(config.validation.allowed_orphan_paths)
        orphan_ids = detect_orphans(
            graph,
            allowed_orphan_types,
            allowed_orphan_paths=allowed_orphan_paths,
            workspace_root=repo_root,
        )
        if scope == ScanScope.DOCS and external_scope.external_depends_on_index:
            # (#133 review) Docs-scope orphans depended on from
            # .ontos-internal are filtered here but NOT by activate/query,
            # which never load the external scope — so this surface labels
            # its basis instead of silently disagreeing. The label is set
            # only when the filter actually removed an orphan: the external
            # index also holds path-style deps that match no orphan id, and
            # those must not claim an exclusion that never happened.
            filtered_ids = [
                orphan_id
                for orphan_id in orphan_ids
                if orphan_id not in external_scope.external_depends_on_index
            ]
            if len(filtered_ids) != len(orphan_ids):
                orphan_basis = "graph_validation_excluding_external_dependents"
            orphan_ids = filtered_ids

        orphans = [
            OrphanDocument(
                doc_id=doc_id,
                path=docs[doc_id].filepath,
                doc_type=docs[doc_id].type.value,
            )
            for doc_id in sorted(orphan_ids)
            if doc_id in docs
        ]
    timings_ms["orphans"] = _elapsed_ms(phase_start)

    broken_frontmatter = len(
        [
            finding
            for finding in broken_references
            if finding.field in {"depends_on", "impacts", "describes"}
        ]
    )
    broken_body = len(broken_references) - broken_frontmatter

    duplicates = {doc_id: sorted(paths) for doc_id, paths in load_result.duplicate_ids.items()}

    unallowlisted_file_deps = len(
        [item for item in file_dependencies if not item.allowlisted]
    )

    exit_code = _resolve_exit_code(
        duplicate_count=len(duplicates),
        broken_count=len(broken_references),
        orphan_count=len(orphans),
        unallowlisted_file_dependency_count=unallowlisted_file_deps,
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
        file_dependencies=len(file_dependencies),
        unallowlisted_file_dependencies=unallowlisted_file_deps,
    )

    timings_ms["total"] = _elapsed_ms(total_start)

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
        timings_ms=timings_ms,
        file_dependencies=file_dependencies,
        orphan_basis=orphan_basis,
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

    broken_references.append(
        BrokenReference(
            source_doc_id=source_doc_id,
            source_path=source_path,
            field=field,
            value=value,
            severity=severity or "error",
            location=location,
        )
    )


def _attach_suggestions(
    broken_references: List[BrokenReference],
    docs: Dict[str, DocumentData],
) -> None:
    """Populate suggestions on broken references, memoized per unique value."""
    index = SuggestionIndex(docs)
    memo: Dict[str, List[ReferenceSuggestion]] = {}
    for finding in broken_references:
        if finding.value not in memo:
            memo[finding.value] = [
                ReferenceSuggestion(candidate=candidate, confidence=confidence, reason=reason)
                for candidate, confidence, reason in suggest_candidates(finding.value, index)
            ]
        finding.suggestions = list(memo[finding.value])


def _body_line_offset(doc: DocumentData) -> int:
    """Return the number of physical file lines preceding ``doc.content``.

    The canonical loader stores frontmatter-stripped body text and removes
    leading blank line endings.  Scanner locations are body-relative, so this
    reconstructs the exact offset from the source file without changing the
    loader or the public location shape.
    """

    try:
        raw = doc.filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    # Match the canonical loader: strip an initial BOM and leading whitespace
    # before looking for the first fence, while retaining the stripped prefix
    # so body-relative locations can be restored to physical file lines.
    without_bom = raw[1:] if raw.startswith("\ufeff") else raw
    normalized = without_bom.lstrip()
    leading_prefix = without_bom[: len(without_bom) - len(normalized)]
    split = split_frontmatter_text(normalized)
    if split is None:
        # ``load_document`` applies the same leading-whitespace normalization
        # even when a document has no frontmatter. Restore those physical
        # lines before converting scanner-relative locations.
        return _line_break_count(leading_prefix)

    _, raw_body, body_offset = split
    prefix = normalized[:body_offset]
    if raw_body == doc.content:
        stripped_prefix = ""
    else:
        normalized_body = raw_body.lstrip("\r\n")
        if normalized_body != doc.content:
            # A custom parser/load_result may transform the body.  The
            # frontmatter offset remains correct even when its additional
            # leading-newline behavior cannot be inferred safely.
            return _line_break_count(leading_prefix) + _line_break_count(prefix)
        stripped_prefix = raw_body[: len(raw_body) - len(normalized_body)]
    return (
        _line_break_count(leading_prefix)
        + _line_break_count(prefix)
        + _line_break_count(stripped_prefix)
    )


def _line_break_count(text: str) -> int:
    return len(re.findall(r"\r\n|\r|\n", text))


def _resolve_markdown_target(
    *,
    raw_target: str,
    source_path: Path,
    repo_root: Path,
    active_paths: _LoadedPathIndex,
    external_paths: _LoadedPathIndex,
) -> _ResolvedMarkdownTarget:
    """Resolve a relative Markdown target without filesystem-dependent case.

    Targets are checked source-relative first (Markdown semantics), then
    workspace-relative for the repository-style links Ontos documentation
    supports.  Loaded documents resolve to their frontmatter ID even when the
    filename differs.  Existing non-document files are returned for the
    informational file-reference bucket.  Case-only collisions fail closed.
    """

    try:
        root_resolved = repo_root.resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        return _ResolvedMarkdownTarget()

    for target_text in _markdown_path_variants(raw_target):
        relative_target = Path(target_text)
        if relative_target.is_absolute():
            continue

        source_parent = (
            source_path.parent
            if source_path.is_absolute()
            else root_resolved / source_path.parent
        )
        candidates = [source_parent / relative_target, root_resolved / relative_target]
        seen_candidates: Set[str] = set()
        for candidate in candidates:
            try:
                lexical_resolved = candidate.resolve(strict=False)
                lexical_resolved.relative_to(root_resolved)
            except (OSError, RuntimeError, ValueError):
                continue

            candidate_key = str(lexical_resolved)
            if candidate_key in seen_candidates:
                continue
            seen_candidates.add(candidate_key)

            active_id, active_ambiguous = active_paths.resolve(candidate, lexical_resolved)
            if active_id is not None:
                return _ResolvedMarkdownTarget(document_id=active_id)
            if active_ambiguous:
                return _ResolvedMarkdownTarget(ambiguous=True)

            external_id, external_ambiguous = external_paths.resolve(
                candidate, lexical_resolved
            )
            if external_id is not None:
                return _ResolvedMarkdownTarget(document_id=external_id)
            if external_ambiguous:
                return _ResolvedMarkdownTarget(ambiguous=True)

            existing_path, ambiguous = _resolve_existing_workspace_path(
                lexical_resolved,
                root_resolved,
            )
            if ambiguous:
                return _ResolvedMarkdownTarget(ambiguous=True)
            if existing_path is None:
                continue

            # Recheck inode identities after a case-insensitive filesystem
            # walk; this also recognizes hard-link aliases of loaded docs.
            active_id, active_ambiguous = active_paths.resolve(
                existing_path, existing_path
            )
            if active_id is not None:
                return _ResolvedMarkdownTarget(document_id=active_id)
            if active_ambiguous:
                return _ResolvedMarkdownTarget(ambiguous=True)
            external_id, external_ambiguous = external_paths.resolve(
                existing_path, existing_path
            )
            if external_id is not None:
                return _ResolvedMarkdownTarget(document_id=external_id)
            if external_ambiguous:
                return _ResolvedMarkdownTarget(ambiguous=True)

            try:
                relative = existing_path.relative_to(root_resolved).as_posix()
            except ValueError:
                continue
            return _ResolvedMarkdownTarget(resolved_path=relative)

    return _ResolvedMarkdownTarget()


def _markdown_path_variants(raw_target: str) -> List[str]:
    """Return decoded path candidates, including ``file.py:123`` anchors."""

    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">") and len(target) >= 2:
        target = target[1:-1].strip()
    target = unquote(target.split("#", 1)[0].strip()).replace("\\", "/")
    if not target:
        return []

    variants = [target]
    line_anchor = re.match(r"^(?P<path>.+):\d+(?::\d+)?$", target)
    if line_anchor is not None:
        anchored_path = line_anchor.group("path")
        if anchored_path and anchored_path not in variants:
            variants.append(anchored_path)
    return variants


def _resolve_existing_workspace_path(
    lexical_path: Path,
    workspace_root: Path,
) -> Tuple[Optional[Path], bool]:
    """Resolve an existing path case-insensitively and collision-safely.

    Exact spellings win.  For a missing spelling, each segment is matched by
    ``casefold``; zero matches means missing and multiple matches means
    ambiguous.  The final real path must remain within the workspace so
    symlinks cannot escape containment.
    """

    try:
        relative = lexical_path.relative_to(workspace_root)
    except ValueError:
        return None, False

    current = workspace_root
    for segment in relative.parts:
        exact = current / segment
        if exact.exists():
            current = exact
            continue
        try:
            matches = [
                child
                for child in current.iterdir()
                if child.name.casefold() == segment.casefold()
            ]
        except (OSError, ValueError):
            return None, False
        if not matches:
            return None, False
        if len(matches) > 1:
            return None, True
        current = matches[0]

    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(workspace_root)
    except (OSError, RuntimeError, ValueError):
        return None, False
    return resolved, False


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _extract_reference_value(message: str) -> Optional[str]:
    match = _QUOTED_VALUE_RE.search(message)
    if match is None:
        return None
    return match.group(1)


def _resolve_exit_code(
    duplicate_count: int,
    broken_count: int,
    orphan_count: int,
    unallowlisted_file_dependency_count: int = 0,
) -> int:
    # (#134) Unallowlisted resolved-on-disk deps preserve the pre-rebucketing
    # exit-1 semantics for unconfigured repos; allowlisted ones never drive
    # exit codes.
    if duplicate_count > 0 or broken_count > 0 or unallowlisted_file_dependency_count > 0:
        return 1
    if orphan_count > 0:
        return 3
    return 0


def _load_external_scope_info(
    *,
    repo_root: Path,
    config: OntosConfig,
    scope: ScanScope,
    include_external_scope_resolution: bool,
) -> _ExternalScopeInfo:
    if scope != ScanScope.DOCS or not include_external_scope_resolution:
        return _ExternalScopeInfo(
            external_ids=set(),
            external_depends_on_index=set(),
            documents={},
        )

    external_root = repo_root / ".ontos-internal"
    if not external_root.exists():
        return _ExternalScopeInfo(
            external_ids=set(),
            external_depends_on_index=set(),
            documents={},
        )

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
        documents=external_load.documents,
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
