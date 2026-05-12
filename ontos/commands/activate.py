"""Agent-friendly best-effort activation command."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ontos.commands.map import GenerateMapOptions, generate_context_map
from ontos.core.frontmatter_repair import enum_issue_summary
from ontos.core.types import DocumentData
from ontos.io.config import load_project_config
from ontos.io.files import DocumentLoadIssue, find_project_root, load_documents
from ontos.io.scan_scope import collect_scoped_documents, resolve_scan_scope
from ontos.io.yaml import parse_frontmatter_content
from ontos.ui.json_output import emit_command_error, emit_command_success


@dataclass
class ActivateOptions:
    json_output: bool = False
    quiet: bool = False
    scope: Optional[str] = None


def activate_command(options: ActivateOptions) -> int:
    exit_code, payload = run_activation(options.scope, write_map=True)
    if options.json_output:
        if exit_code == 0:
            emit_command_success(
                command="activate",
                exit_code=0,
                message="Activation context available",
                data=payload,
            )
        else:
            emit_command_error(
                command="activate",
                exit_code=exit_code,
                code="E_ACTIVATION_UNUSABLE",
                message="Activation context unavailable",
                data=payload,
            )
    elif not options.quiet:
        for line in format_activation_output(payload):
            print(line)
    return exit_code


def run_activation(
    scope: Optional[str],
    *,
    write_map: bool,
    root: Optional[Path] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Return best-effort activation payload and exit code."""
    try:
        project_root = root or find_project_root()
    except FileNotFoundError as exc:
        return 1, _not_usable(str(exc))

    try:
        config = load_project_config(repo_root=project_root)
    except Exception as exc:
        return 1, _not_usable(f"Config error: {exc}", project_root=project_root)

    effective_scope = resolve_scan_scope(scope, config.scanning.default_scope)
    output_path = project_root / config.paths.context_map
    doc_paths = collect_scoped_documents(
        project_root,
        config,
        effective_scope,
        base_skip_patterns=[*config.scanning.skip_patterns, str(output_path.resolve())],
    )
    load_result = load_documents(doc_paths, parse_frontmatter_content)
    docs = load_result.documents

    if not docs and not output_path.exists():
        return 1, _not_usable(
            "No Ontos documents loaded and no existing context map is available.",
            project_root=project_root,
            files_scanned=len(doc_paths),
            issues=load_result.issues,
        )

    gen_config = {
        "project_name": project_root.name,
        "version": config.ontos.version,
        "allowed_orphan_types": config.validation.allowed_orphan_types,
        "project_root": str(project_root),
        "docs_dir": str(config.paths.docs_dir),
        "logs_dir": str(config.paths.logs_dir),
        "is_contributor_mode": (project_root / ".ontos-internal").is_dir(),
    }
    map_refreshed = False
    validation_errors = []
    validation_warnings = []
    if docs:
        content, validation = generate_context_map(
            docs,
            gen_config,
            GenerateMapOptions(max_dependency_depth=config.validation.max_dependency_depth),
        )
        validation_errors = [issue.message for issue in validation.errors]
        validation_warnings = [issue.message for issue in validation.warnings]
        if write_map:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            map_refreshed = True

    warning_count = len(load_result.issues) + len(validation_warnings) + len(validation_errors)
    status = "usable" if warning_count == 0 else "usable_with_warnings"
    loaded_ids = _select_loaded_ids(docs)
    payload = {
        "status": status,
        "map": {
            "path": str(output_path),
            "refreshed": map_refreshed,
            "exists": output_path.exists(),
        },
        "scope": effective_scope.value,
        "files_scanned": len(doc_paths),
        "documents": len(docs),
        "loaded_ids": loaded_ids,
        "diagnostics": [issue.to_dict(root=project_root) for issue in load_result.issues],
        "validation": {
            "errors": validation_errors,
            "warnings": validation_warnings,
        },
        "summary": {
            "load_issues": len(load_result.issues),
            "validation_errors": len(validation_errors),
            "validation_warnings": len(validation_warnings),
        },
        "recommendation": (
            "continue; use direct reads for task-critical docs"
            if status == "usable_with_warnings"
            else "continue"
        ),
    }
    return 0, payload


def format_activation_output(payload: Dict[str, Any]) -> List[str]:
    lines = [
        f"Activation status: {payload['status']}",
        f"Map: {'refreshed' if payload['map']['refreshed'] else 'existing'}",
        f"Docs scanned: {payload.get('files_scanned', 0)}",
        f"Documents loaded: {payload.get('documents', 0)}",
    ]
    summary = payload.get("summary", {})
    if summary:
        lines.append(
            "Issues: "
            f"load={summary.get('load_issues', 0)}, "
            f"validation_errors={summary.get('validation_errors', 0)}, "
            f"validation_warnings={summary.get('validation_warnings', 0)}"
        )
    diagnostics = payload.get("diagnostics", [])
    enum_diagnostics = [
        _dict_to_issue(item) for item in diagnostics if item.get("code") == "invalid_enum"
    ]
    if enum_diagnostics:
        lines.append("Top enum diagnostics:")
        lines.extend(f"  - {item}" for item in enum_issue_summary(enum_diagnostics, limit=5))
    lines.append(f"Recommended agent action: {payload.get('recommendation', 'continue')}")
    lines.append(f"Loaded: {payload.get('loaded_ids', [])}")
    return lines


def _select_loaded_ids(docs: Dict[str, DocumentData]) -> List[str]:
    in_degree: Dict[str, int] = {}
    for doc in docs.values():
        for dep_id in doc.depends_on:
            if dep_id in docs:
                in_degree[dep_id] = in_degree.get(dep_id, 0) + 1
    ranked = sorted(docs.values(), key=lambda doc: (-in_degree.get(doc.id, 0), doc.id))
    return [doc.id for doc in ranked[:5]]


def _not_usable(
    reason: str,
    *,
    project_root: Optional[Path] = None,
    files_scanned: int = 0,
    issues: Optional[List[DocumentLoadIssue]] = None,
) -> Dict[str, Any]:
    return {
        "status": "not_usable",
        "reason": reason,
        "map": {"path": None, "refreshed": False, "exists": False},
        "files_scanned": files_scanned,
        "documents": 0,
        "loaded_ids": [],
        "diagnostics": [
            issue.to_dict(root=project_root) for issue in (issues or [])
        ],
        "validation": {"errors": [], "warnings": []},
        "summary": {
            "load_issues": len(issues or []),
            "validation_errors": 0,
            "validation_warnings": 0,
        },
        "recommendation": "halt; no usable Ontos context is available",
    }


def _dict_to_issue(item: Dict[str, Any]) -> DocumentLoadIssue:
    return DocumentLoadIssue(
        code=item["code"],
        path=Path(item["path"]),
        message=item["message"],
        doc_id=item.get("doc_id"),
        field=item.get("field"),
        value=item.get("observed_value"),
        line=item.get("line"),
        allowed_values=item.get("allowed_values"),
        suggested_fix=item.get("suggested_fix"),
        severity=item.get("severity", "warning"),
        blocking=bool(item.get("blocking", False)),
    )
