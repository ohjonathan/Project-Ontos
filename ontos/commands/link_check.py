"""Standalone link diagnostics command (`ontos link-check`)."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from ontos.core.link_diagnostics import LinkDiagnosticsResult, run_link_diagnostics
from ontos.io.config import load_project_config
from ontos.io.files import find_project_root
from ontos.io.scan_scope import build_scope_roots, collect_scoped_documents, resolve_scan_scope


@dataclass
class LinkCheckOptions:
    """Options for link-check command."""

    scope: Optional[str] = None
    json_output: bool = False
    quiet: bool = False
    suggestions: bool = True


def link_check_command(options: LinkCheckOptions) -> int:
    """Execute link-check command."""

    try:
        repo_root = find_project_root()
    except FileNotFoundError as exc:
        return _emit_command_error(options, str(exc))

    try:
        config = load_project_config(repo_root=repo_root)
    except Exception as exc:
        return _emit_command_error(options, f"Config error: {exc}")

    scope = resolve_scan_scope(options.scope, config.scanning.default_scope)
    roots = build_scope_roots(repo_root, config, scope)
    doc_paths = collect_scoped_documents(
        repo_root,
        config,
        scope,
        base_skip_patterns=list(config.scanning.skip_patterns),
    )

    result = run_link_diagnostics(
        repo_root=repo_root,
        config=config,
        doc_paths=doc_paths,
        scope=scope,
        include_body=True,
        include_external_scope_resolution=True,
        include_suggestions=options.suggestions,
    )

    if options.json_output:
        print(result.to_json_text())
    else:
        _emit_human_report(result, roots=roots, quiet=options.quiet)

    return result.exit_code


def _emit_command_error(options: LinkCheckOptions, message: str) -> int:
    if options.json_output:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": message,
                }
            )
        )
    else:
        print(f"Error: {message}")
    return 1


def _emit_human_report(result: LinkDiagnosticsResult, *, roots: List[Path], quiet: bool) -> None:
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
    print(f"  external_references: {result.summary.external_references}")
    print(f"  parse_failed_candidates: {result.summary.parse_failed_candidates}")
    print(f"  orphans: {result.summary.orphans}")
    print(f"  exit_code: {result.exit_code}")
    print()

    _emit_duplicates(result)
    _emit_broken_by_field(result)
    _emit_external_refs(result)
    _emit_parse_failed_candidates(result)
    _emit_suggestions(result)
    _emit_orphans(result)
    _emit_load_warnings(result)
    print(_status_line(result))


def _emit_fatal_sections(result: LinkDiagnosticsResult) -> None:
    _emit_duplicates(result)
    _emit_broken_by_field(result)


def _emit_duplicates(result: LinkDiagnosticsResult) -> None:
    if not result.duplicates:
        return
    print("Duplicate IDs")
    for doc_id, paths in sorted(result.duplicates.items()):
        print(f"  - {doc_id}")
        for path in paths:
            print(f"      {path}")
    print()


def _emit_broken_by_field(result: LinkDiagnosticsResult) -> None:
    if not result.broken_references:
        return
    grouped: Dict[str, List[object]] = defaultdict(list)
    for finding in result.broken_references:
        grouped[finding.field].append(finding)

    print("Broken References")
    for field in sorted(grouped.keys()):
        print(f"  {field}")
        for finding in grouped[field]:
            base = f"    - {finding.source_doc_id}: {finding.value}"
            if finding.location is not None:
                base += f" (line {finding.location.line}, {finding.location.match_type})"
            print(base)
    print()


def _emit_external_refs(result: LinkDiagnosticsResult) -> None:
    if not result.external_references:
        return
    print("External References (docs scope informational)")
    for finding in result.external_references:
        print(
            "  - "
            f"{finding.source_doc_id} [{finding.field}] -> {finding.value} "
            "(resolved outside active scope)"
        )
    print()


def _emit_parse_failed_candidates(result: LinkDiagnosticsResult) -> None:
    if not result.parse_failed_candidates:
        return
    print("Parse-Failed Candidate References")
    for candidate in result.parse_failed_candidates:
        print(
            "  - "
            f"{candidate.path}:{candidate.line} "
            f"{candidate.match_type}={candidate.candidate}"
        )
    print()


def _emit_suggestions(result: LinkDiagnosticsResult) -> None:
    suggested = [finding for finding in result.broken_references if finding.suggestions]
    if not suggested:
        return
    print("Suggestions")
    for finding in suggested:
        print(f"  - {finding.source_doc_id} [{finding.field}] {finding.value}")
        for suggestion in finding.suggestions:
            print(
                "      "
                f"{suggestion.candidate} "
                f"(confidence={suggestion.confidence:.2f}, {suggestion.reason})"
            )
    print()


def _emit_orphans(result: LinkDiagnosticsResult) -> None:
    if not result.orphans:
        return
    print("Orphans (scope-relative)")
    for orphan in result.orphans[:20]:
        print(f"  - {orphan.doc_id} ({orphan.doc_type}) [{orphan.path}]")
    if len(result.orphans) > 20:
        print(f"  ... and {len(result.orphans) - 20} more")
    print()


def _emit_load_warnings(result: LinkDiagnosticsResult) -> None:
    if not result.load_warnings:
        return
    print("Parse/Load Warnings")
    for issue in result.load_warnings:
        print(f"  - {issue.code}: {issue.message}")
    print()


def _status_line(result: LinkDiagnosticsResult) -> str:
    if result.exit_code == 0:
        return "link-check status: clean (exit 0)"
    if result.exit_code == 1:
        return "link-check status: broken references or duplicates found (exit 1)"
    return "link-check status: orphan-only findings (exit 2)"

