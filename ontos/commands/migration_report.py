"""
Migration report command — analyze documents for migration safety.
"""

from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from ontos.core.snapshot import SnapshotFilters
from ontos.io.snapshot import create_snapshot
from ontos.core.migration import classify_documents, MigrationReport
from ontos.io.files import find_project_root


@dataclass
class MigrationReportOptions:
    """Options for migration-report command."""
    output_path: Optional[Path] = None
    format: str = "md"  # md or json
    force: bool = False
    quiet: bool = False
    json_output: bool = False
    scope: Optional[str] = None


def _generate_markdown_report(report: MigrationReport, project_name: str) -> str:
    """Generate markdown migration report."""
    import ontos

    lines = [
        "# Migration Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Project:** {project_name}",
        f"**Ontos Version:** {ontos.__version__}",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Classification | Count | Action |",
        "|----------------|-------|--------|",
        f"| Safe to migrate | {report.summary.get('safe', 0)} | Copy to new project |",
        f"| Needs review | {report.summary.get('review', 0)} | Update references |",
        f"| Needs rewrite | {report.summary.get('rewrite', 0)} | Preserve intent, reimplement |",
        "",
        "---",
        "",
    ]

    # Safe documents
    safe_docs = [c for c in report.classifications.values() if c.effective_status == "safe"]
    if safe_docs:
        lines.extend([
            "## Safe to Migrate",
            "",
            "These documents have no dependencies on implementation-specific atoms.",
            "",
            "| ID | Type | Path |",
            "|----|------|------|",
        ])
        for c in sorted(safe_docs, key=lambda x: x.id):
            lines.append(f"| {c.id} | {c.doc_type} | {c.path} |")
        lines.extend(["", "---", ""])

    # Review documents
    review_docs = [c for c in report.classifications.values() if c.effective_status == "review"]
    if review_docs:
        lines.extend([
            "## Needs Review",
            "",
            "These documents depend on atoms (directly or indirectly).",
            "",
            "| ID | Type | Atom Dependencies | Reason |",
            "|----|------|-------------------|--------|",
        ])
        for c in sorted(review_docs, key=lambda x: x.id):
            deps = ", ".join(c.atom_dependencies) if c.atom_dependencies else "-"
            reason = "Depends on atom" if c.atom_dependencies else "-"
            lines.append(f"| {c.id} | {c.doc_type} | {deps} | {reason} |")
        lines.extend(["", "---", ""])

    # Rewrite documents
    rewrite_docs = [c for c in report.classifications.values() if c.effective_status == "rewrite"]
    if rewrite_docs:
        lines.extend([
            "## Needs Rewrite",
            "",
            "These are atoms—implementation-specific documents.",
            "",
            "| ID | Type | Intent to Preserve |",
            "|----|------|-------------------|",
        ])
        for c in sorted(rewrite_docs, key=lambda x: x.id):
            lines.append(f"| {c.id} | {c.doc_type} | (extract from content) |")
        lines.extend(["", "---", ""])

    # Warnings (S3)
    if report.warnings:
        lines.extend([
            "## Warnings",
            "",
            "The following issues were identified during analysis:",
            "",
            "| ID | Type | Message |",
            "|----|------|---------|",
        ])
        for w in report.warnings:
            doc_id = w.get("id", "-")
            w_type = w.get("type", "warning")
            message = w.get("message", "-")
            
            # Special handling for override_downgrade to be more descriptive
            if w_type == "override_downgrade":
                inferred = w.get("inferred", "?")
                override = w.get("override", "?")
                message = f"Manual override ({override}) downgrades inferred status ({inferred})"
            
            lines.append(f"| {doc_id} | {w_type} | {message} |")
        
        lines.extend([
            "",
            "**Note:** Please review all warnings to ensure migration safety.",
        ])

    return "\n".join(lines)


def _generate_json_report(report: MigrationReport, project_root: Path) -> Dict[str, Any]:
    """Generate JSON migration report."""
    import ontos

    classifications = []
    for c in sorted(report.classifications.values(), key=lambda x: x.id):
        classifications.append({
            "id": c.id,
            "type": c.doc_type,
            "path": c.path,
            "inferred_migration_status": c.inferred_status,
            "effective_migration_status": c.effective_status,
            "override": c.override,
            "override_reason": c.override_reason,
            "atom_dependencies": c.atom_dependencies,
        })

    return {
        "schema_version": "ontos-migration-report-v1",
        "provenance": {
            "generated_at": datetime.now().isoformat(),
            "ontos_version": ontos.__version__,
            "project_root": str(project_root),
        },
        "summary": report.summary,
        "classifications": classifications,
        "warnings": report.warnings,
    }


def _run_migration_report_command(options: MigrationReportOptions) -> Tuple[int, str]:
    """
    Generate migration analysis report.

    Returns:
        Tuple of (exit_code, message)
    """
    try:
        root = find_project_root()
    except Exception as e:
        return 1, f"Error: {e}"

    # Check output file
    if options.output_path:
        if options.output_path.exists() and not options.force:
            return 1, f"Error: Output file exists: {options.output_path}. Use --force to overwrite."

    # Create snapshot and classify
    snapshot = create_snapshot(root, scope=options.scope)
    report = classify_documents(snapshot)

    # Generate report
    project_name = root.name
    if options.format == "json":
        data = _generate_json_report(report, root)
        output = json.dumps(data, indent=2)
    else:
        output = _generate_markdown_report(report, project_name)

    # Output
    if options.output_path:
        try:
            options.output_path.parent.mkdir(parents=True, exist_ok=True)
            options.output_path.write_text(output, encoding='utf-8')
        except (IOError, OSError) as e:
            # S1: Improved error handling
            return 1, f"Error writing migration report to {options.output_path}: {e}"
        return 0, f"Generated migration report: {options.output_path}"
    else:
        return 0, output


def migration_report_command(options: MigrationReportOptions) -> int:
    """Generate migration report and return exit code only."""
    exit_code, _ = _run_migration_report_command(options)
    return exit_code
