"""Standalone link diagnostics command (`ontos link-check`)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Dict, List, Optional

from ontos.core.link_diagnostics import LinkDiagnosticsResult, run_link_diagnostics
from ontos.io.config import load_project_config
from ontos.io.files import find_project_root
from ontos.io.scan_scope import build_scope_roots, collect_scoped_documents, resolve_scan_scope
from ontos.ui.json_output import emit_command_error, emit_command_success
from ontos.ui.output import OutputHandler


@dataclass
class LinkCheckOptions:
    """Options for link-check command."""

    scope: Optional[str] = None
    json_output: bool = False
    quiet: bool = False
    suggestions: bool = True
    # (#135) Output / work controls.
    summary: bool = False
    limit: Optional[int] = None
    frontmatter_only: bool = False
    include_orphans: bool = True


def link_check_command(options: LinkCheckOptions) -> int:
    """Execute link-check command."""

    try:
        repo_root = find_project_root()
    except FileNotFoundError as exc:
        return _emit_link_check_error(options, str(exc))

    try:
        config = load_project_config(repo_root=repo_root)
    except Exception as exc:
        return _emit_link_check_error(options, f"Config error: {exc}")

    scope = resolve_scan_scope(options.scope, config.scanning.default_scope)
    roots = build_scope_roots(repo_root, config, scope)
    doc_paths = collect_scoped_documents(
        repo_root,
        config,
        scope,
        base_skip_patterns=list(config.scanning.skip_patterns),
    )

    include_suggestions = options.suggestions and not options.summary
    include_body = not options.frontmatter_only

    # Stage markers go to stderr for human runs only — stdout must stay a
    # single parseable JSON document in --json mode (#135).
    progress = None
    if not options.json_output and not options.quiet:
        handler = OutputHandler(quiet=False)
        progress = handler.progress

    result = run_link_diagnostics(
        repo_root=repo_root,
        config=config,
        doc_paths=doc_paths,
        scope=scope,
        include_body=include_body,
        include_external_scope_resolution=True,
        include_suggestions=include_suggestions,
        include_orphans=options.include_orphans,
        progress=progress,
    )

    if options.json_output:
        emit_command_success(
            command="link-check",
            exit_code=result.exit_code,
            message=_status_text(result),
            data=result.to_data_payload(
                limit=options.limit,
                summary_only=options.summary,
                options_echo={
                    "suggestions": include_suggestions,
                    "body_scan": include_body,
                    "orphans": options.include_orphans,
                    "limit": options.limit,
                },
            ),
            # The summary counters describe every phase that actually ran,
            # but omitting either body references or orphan discovery is a
            # deliberately partial diagnostic scan.
            diagnostics_complete=include_body and options.include_orphans,
        )
    else:
        _emit_human_report(
            result,
            roots=roots,
            quiet=options.quiet,
            summary_only=options.summary,
            limit=options.limit,
        )

    return result.exit_code


def _emit_link_check_error(options: LinkCheckOptions, message: str) -> int:
    if options.json_output:
        emit_command_error(
            command="link-check",
            exit_code=2,
            code="E_USER_INPUT",
            message=message,
        )
    else:
        print(f"Error: {message}", file=sys.stderr)
    return 2


def _emit_human_report(
    result: LinkDiagnosticsResult,
    *,
    roots: List[Path],
    quiet: bool,
    summary_only: bool = False,
    limit: Optional[int] = None,
) -> None:
    if quiet:
        _emit_fatal_sections(result)
        print(_status_line(result))
        return

    print("Scope + Census")
    print(f"  scope: {result.scope.value}")
    print("  roots:")
    for root in roots:
        print(f"    - {root}")
    print(f"  files_scanned: {result.summary.files_scanned}")
    print(f"  documents_loaded: {result.summary.documents_loaded}")
    print(f"  load_warnings: {result.summary.load_warnings}")
    print()

    print("Summary")
    print(f"  duplicate_ids: {result.summary.duplicate_ids}")
    print(f"  broken_references: {result.summary.broken_references}")
    print(f"  file_dependencies: {result.summary.file_dependencies}")
    print(
        "  unallowlisted_file_dependencies: "
        f"{result.summary.unallowlisted_file_dependencies}"
    )
    print(f"  external_references: {result.summary.external_references}")
    print(f"  parse_failed_candidates: {result.summary.parse_failed_candidates}")
    print(f"  orphans: {result.summary.orphans}")
    print(f"  exit_code: {result.exit_code}")
    print()

    if not summary_only:
        _emit_duplicates(result, limit=limit)
        _emit_broken_by_field(result, limit=limit)
        _emit_file_dependencies(result, limit=limit)
        _emit_external_refs(result, limit=limit)
        _emit_parse_failed_candidates(result, limit=limit)
        _emit_suggestions(result, limit=limit)
        _emit_orphans(result, limit=limit)
        _emit_load_warnings(result, limit=limit)
    _emit_timings(result)
    print(_status_line(result))


def _emit_timings(result: LinkDiagnosticsResult) -> None:
    if not result.timings_ms:
        return
    print("Timings (ms)")
    for phase, elapsed in result.timings_ms.items():
        print(f"  {phase}: {elapsed}")
    print()


def _emit_fatal_sections(result: LinkDiagnosticsResult) -> None:
    _emit_duplicates(result)
    _emit_broken_by_field(result)


def _capped(items, limit):
    """Return (visible_items, hidden_count) for a section cap (#135)."""
    items = list(items)
    if limit is None or len(items) <= limit:
        return items, 0
    return items[:limit], len(items) - limit


def _emit_duplicates(result: LinkDiagnosticsResult, limit: Optional[int] = None) -> None:
    if not result.duplicates:
        return
    print("Duplicate IDs")
    visible, hidden = _capped(sorted(result.duplicates.items()), limit)
    for doc_id, paths in visible:
        print(f"  - {doc_id}")
        for path in paths:
            print(f"      {path}")
    if hidden:
        print(f"  ... and {hidden} more")
    print()


def _emit_broken_by_field(result: LinkDiagnosticsResult, limit: Optional[int] = None) -> None:
    if not result.broken_references:
        return
    grouped: Dict[str, List[object]] = defaultdict(list)
    for finding in result.broken_references:
        grouped[finding.field].append(finding)

    print("Broken References")
    for field in sorted(grouped.keys()):
        print(f"  {field}")
        visible, hidden = _capped(grouped[field], limit)
        for finding in visible:
            base = f"    - {finding.source_doc_id}: {finding.value}"
            if finding.location is not None:
                base += f" (line {finding.location.line}, {finding.location.match_type})"
            print(base)
        if hidden:
            print(f"    ... and {hidden} more")
    print()


def _emit_file_dependencies(result: LinkDiagnosticsResult, limit: Optional[int] = None) -> None:
    if not result.file_dependencies:
        return
    print("File Dependencies (resolved on disk)")
    visible, hidden = _capped(result.file_dependencies, limit)
    for item in visible:
        marker = "allowlisted" if item.allowlisted else "review"
        print(
            "  - "
            f"{item.source_doc_id} [{item.field}] -> {item.value} "
            f"[{marker}] ({item.resolved_path})"
        )
    if hidden:
        print(f"  ... and {hidden} more")
    print()


def _emit_external_refs(result: LinkDiagnosticsResult, limit: Optional[int] = None) -> None:
    if not result.external_references:
        return
    print("External References (docs scope informational)")
    visible, hidden = _capped(result.external_references, limit)
    for finding in visible:
        print(
            "  - "
            f"{finding.source_doc_id} [{finding.field}] -> {finding.value} "
            "(resolved outside active scope)"
        )
    if hidden:
        print(f"  ... and {hidden} more")
    print()


def _emit_parse_failed_candidates(result: LinkDiagnosticsResult, limit: Optional[int] = None) -> None:
    if not result.parse_failed_candidates:
        return
    print("Parse-Failed Candidate References")
    visible, hidden = _capped(result.parse_failed_candidates, limit)
    for candidate in visible:
        print(
            "  - "
            f"{candidate.path}:{candidate.line} "
            f"{candidate.match_type}={candidate.candidate}"
        )
    if hidden:
        print(f"  ... and {hidden} more")
    print()


def _emit_suggestions(result: LinkDiagnosticsResult, limit: Optional[int] = None) -> None:
    suggested = [finding for finding in result.broken_references if finding.suggestions]
    if not suggested:
        return
    print("Suggestions")
    visible, hidden = _capped(suggested, limit)
    for finding in visible:
        print(f"  - {finding.source_doc_id} [{finding.field}] {finding.value}")
        for suggestion in finding.suggestions:
            print(
                "      "
                f"{suggestion.candidate} "
                f"(confidence={suggestion.confidence:.2f}, {suggestion.reason})"
            )
    if hidden:
        print(f"  ... and {hidden} more")
    print()


def _emit_orphans(result: LinkDiagnosticsResult, limit: Optional[int] = None) -> None:
    if not result.orphans:
        return
    print("Orphans (scope-relative)")
    cap = limit if limit is not None else 20
    for orphan in result.orphans[:cap]:
        print(f"  - {orphan.doc_id} ({orphan.doc_type}) [{orphan.path}]")
    if len(result.orphans) > cap:
        print(f"  ... and {len(result.orphans) - cap} more")
    print()


def _emit_load_warnings(result: LinkDiagnosticsResult, limit: Optional[int] = None) -> None:
    if not result.load_warnings:
        return
    print("Parse/Load Warnings")
    visible, hidden = _capped(result.load_warnings, limit)
    for issue in visible:
        print(f"  - {issue.code}: {issue.message}")
    if hidden:
        print(f"  ... and {hidden} more")
    print()


def _status_text(result: LinkDiagnosticsResult) -> str:
    if result.exit_code == 0:
        label = "clean"
    elif result.exit_code == 1:
        label = "broken references or duplicates found"
    else:
        label = "orphan-only findings"
    return f"{label} (exit {result.exit_code})"


def _status_line(result: LinkDiagnosticsResult) -> str:
    return f"link-check status: {_status_text(result)}"
