"""Bulk-apply computed frontmatter fields to existing documents.

``ontos retrofit --obsidian`` writes the already-computed ``tags`` and
``aliases`` fields (from ``normalize_tags`` / ``normalize_aliases``) into
on-disk frontmatter so existing vaults become browsable through
Obsidian's tag and alias panes without hand-editing every block.

Structure mirrors ``ontos/commands/rename.py``:

* Dry-run by default; ``--apply`` writes changes.
* ``--apply`` requires a clean git working tree.
* Atomic commit via :class:`ontos.core.context.SessionContext`.
* Surgical YAML patching — inserts/replaces just the target fields and
  preserves all other lines, comments, and formatting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ontos.core.context import SessionContext
from ontos.core.frontmatter import normalize_aliases, normalize_tags
from ontos.core.frontmatter_edit import (
    _check_clean_git_state,
    _index_top_level_fields,
    _read_decoded_content,
    _split_frontmatter,
)
from ontos.core.types import DocumentData
from ontos.io.config import load_project_config
from ontos.io.files import DocumentLoadIssue, find_project_root, load_documents
from ontos.io.scan_scope import ScanScope, collect_scoped_documents, resolve_scan_scope
from ontos.io.yaml import parse_frontmatter_content
from ontos.ui.json_output import emit_command_error, emit_command_success


REASON_DUPLICATE_TOP_LEVEL = "duplicate_top_level_field"
REASON_BLOCK_SCALAR = "block_scalar_value"
REASON_ANCHOR_ALIAS = "anchor_or_alias"
REASON_UNPATCHABLE_FORMAT = "unpatchable_field_format"

POST_APPLY_WARNING = "Run 'ontos map' to regenerate derived artifacts."

_TARGET_FIELDS: Tuple[str, ...] = ("tags", "aliases")
_DATE_LIKE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?")


@dataclass
class RetrofitOptions:
    """Options for the ``retrofit`` command."""

    obsidian: bool = False
    apply: bool = False
    scope: Optional[str] = None
    json_output: bool = False
    quiet: bool = False


@dataclass(frozen=True)
class RetrofitEdit:
    field: str  # "tags" | "aliases"
    action: str  # "insert" | "replace" | "remove"
    old_value: Optional[List[str]]
    new_value: List[str]


@dataclass(frozen=True)
class RetrofitWarning:
    path: Path
    field: Optional[str]
    reason_code: str
    reason_message: str
    blocking: bool = False


@dataclass
class FilePlan:
    path: Path
    new_content: str
    edits: List[RetrofitEdit] = field(default_factory=list)
    warnings: List[RetrofitWarning] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.edits)


@dataclass(frozen=True)
class RetrofitSummary:
    files_scanned: int
    documents_loaded: int
    planned_files: int
    inserts: int
    replaces: int
    warnings: int


@dataclass
class RetrofitPlan:
    mode: str
    scope: ScanScope
    summary: RetrofitSummary
    files: List[FilePlan]
    warnings: List[RetrofitWarning]

    def blocking_warnings(self) -> List[RetrofitWarning]:
        return [w for w in self.warnings if w.blocking]


@dataclass(frozen=True)
class RetrofitError:
    code: str
    message: str


@dataclass
class _LoadedScope:
    repo_root: Path
    scope: ScanScope
    doc_paths: List[Path]
    docs: Dict[str, DocumentData]


@dataclass(frozen=True)
class _PreparedPlan:
    scope: ScanScope
    plan: RetrofitPlan
    scope_data: _LoadedScope


def retrofit_command(options: RetrofitOptions) -> int:
    """Execute the retrofit command."""

    if not options.obsidian:
        _emit_error(
            options=options,
            mode="dry_run",
            scope=ScanScope.DOCS,
            error=RetrofitError(
                code="missing_mode",
                message="retrofit requires --obsidian (the only supported mode in v4.3.0).",
            ),
            warnings=[],
            partial_commit=False,
        )
        return 1

    mode = "apply" if options.apply else "dry_run"
    prepared, error = _prepare_plan(options, mode=mode)
    if error is not None:
        _emit_error(
            options=options,
            mode=mode,
            scope=prepared.scope if prepared is not None else ScanScope.DOCS,
            error=error,
            warnings=[],
            partial_commit=False,
        )
        return 1

    assert prepared is not None
    plan = prepared.plan

    if mode == "dry_run":
        _emit_dry_run(options, plan)
        return 0

    blocking = plan.blocking_warnings()
    if blocking:
        _emit_error(
            options=options,
            mode=mode,
            scope=plan.scope,
            error=RetrofitError(
                code="unsupported_target_format",
                message="Retrofit plan contains unsupported frontmatter formats. Apply is blocked.",
            ),
            warnings=blocking,
            partial_commit=False,
        )
        return 1

    files_to_apply = [item for item in plan.files if item.has_changes]
    if not files_to_apply:
        _emit_apply_success(options, plan, [])
        return 0

    ctx = SessionContext.from_repo(prepared.scope_data.repo_root)
    for file_plan in files_to_apply:
        ctx.buffer_write(file_plan.path, file_plan.new_content)

    try:
        modified_paths = ctx.commit()
    except Exception as exc:
        _emit_error(
            options=options,
            mode=mode,
            scope=plan.scope,
            error=RetrofitError(
                code="commit_failed",
                message=(
                    "commit failed after staging; repository may be partially updated: "
                    f"{exc}"
                ),
            ),
            warnings=plan.warnings,
            partial_commit=True,
        )
        return 1

    _emit_apply_success(options, plan, modified_paths)
    return 0


def _prepare_plan(
    options: RetrofitOptions, *, mode: str
) -> Tuple[Optional[_PreparedPlan], Optional[RetrofitError]]:
    try:
        repo_root = find_project_root()
    except FileNotFoundError as exc:
        return None, RetrofitError(code="project_root_not_found", message=str(exc))

    try:
        config = load_project_config(repo_root=repo_root)
    except Exception as exc:  # pragma: no cover - config failure path
        return None, RetrofitError(code="config_error", message=f"Config error: {exc}")

    scope = resolve_scan_scope(options.scope, config.scanning.default_scope)

    if mode == "apply":
        clean, git_error = _check_clean_git_state(repo_root)
        if not clean:
            return None, RetrofitError(
                code="dirty_git_state",
                message=git_error or "Git working tree must be clean for --apply.",
            )

    doc_paths = collect_scoped_documents(
        repo_root,
        config,
        scope,
        base_skip_patterns=list(config.scanning.skip_patterns),
    )
    load_result = load_documents(doc_paths, parse_frontmatter_content)
    docs = load_result.documents

    file_plans: List[FilePlan] = []
    all_warnings: List[RetrofitWarning] = _loader_issues_to_warnings(load_result.issues)
    for doc in sorted(docs.values(), key=lambda item: str(item.filepath)):
        file_plan = _build_file_plan(doc)
        if file_plan is None:
            continue
        file_plans.append(file_plan)
        all_warnings.extend(file_plan.warnings)

    inserts = sum(
        1 for fp in file_plans for edit in fp.edits if edit.action == "insert"
    )
    replaces = sum(
        1 for fp in file_plans for edit in fp.edits if edit.action == "replace"
    )
    summary = RetrofitSummary(
        files_scanned=len(doc_paths),
        documents_loaded=len(docs),
        planned_files=len([fp for fp in file_plans if fp.has_changes]),
        inserts=inserts,
        replaces=replaces,
        warnings=len(all_warnings),
    )

    plan = RetrofitPlan(
        mode=mode,
        scope=scope,
        summary=summary,
        files=file_plans,
        warnings=all_warnings,
    )

    return _PreparedPlan(
        scope=scope,
        plan=plan,
        scope_data=_LoadedScope(
            repo_root=repo_root,
            scope=scope,
            doc_paths=doc_paths,
            docs=docs,
        ),
    ), None


def _build_file_plan(doc: DocumentData) -> Optional[FilePlan]:
    path = doc.filepath
    decoded = _read_decoded_content(path)
    split = _split_frontmatter(decoded.normalized)
    warnings: List[RetrofitWarning] = []

    if not split.has_frontmatter:
        return None

    normalized_doc = f"---{split.frontmatter}---"
    try:
        parsed_frontmatter, _ = parse_frontmatter_content(normalized_doc)
    except ValueError:
        return FilePlan(
            path=path,
            new_content=decoded.original,
            edits=[],
            warnings=[
                RetrofitWarning(
                    path=path,
                    field=None,
                    reason_code=REASON_UNPATCHABLE_FORMAT,
                    reason_message="Frontmatter could not be reparsed for targeted patching.",
                    blocking=True,
                )
            ],
        )

    computed: Dict[str, List[str]] = {
        "tags": _compute_retrofit_tags(parsed_frontmatter),
        "aliases": list(doc.aliases),
    }

    lines = split.frontmatter.splitlines(keepends=True)
    line_ending = _detect_dominant_line_ending(lines)
    top_level = _index_top_level_fields(lines)

    edits: List[RetrofitEdit] = []

    for field_name in _TARGET_FIELDS:
        new_value = computed[field_name]
        occurrences = [item for item in top_level if item.key == field_name]
        if len(occurrences) > 1:
            warnings.append(
                RetrofitWarning(
                    path=path,
                    field=field_name,
                    reason_code=REASON_DUPLICATE_TOP_LEVEL,
                    reason_message=(
                        f"Field '{field_name}' appears more than once at top level."
                    ),
                    blocking=True,
                )
            )
            continue

        parsed_value = parsed_frontmatter.get(field_name)
        on_disk = _coerce_on_disk_list(parsed_value)

        if len(occurrences) == 0 and _has_nonempty_parsed_value(
            parsed_frontmatter, field_name, on_disk
        ):
            warnings.append(
                RetrofitWarning(
                    path=path,
                    field=field_name,
                    reason_code=REASON_UNPATCHABLE_FORMAT,
                    reason_message=(
                        f"Field '{field_name}' is present but cannot be targeted for patching."
                    ),
                    blocking=True,
                )
            )
            continue

        should_remove = len(occurrences) == 1 and bool(on_disk) and not new_value
        if not new_value and not should_remove:
            continue

        if len(occurrences) == 1:
            if on_disk is None:
                warnings.append(
                    RetrofitWarning(
                        path=path,
                        field=field_name,
                        reason_code=REASON_UNPATCHABLE_FORMAT,
                        reason_message=(
                            f"Field '{field_name}' has a non-list/non-scalar value."
                        ),
                        blocking=True,
                    )
                )
                continue

            occurrence = occurrences[0]
            block_lines = lines[occurrence.line_index : occurrence.end_line_index]
            if _block_contains_anchor(block_lines):
                warnings.append(
                    RetrofitWarning(
                        path=path,
                        field=field_name,
                        reason_code=REASON_ANCHOR_ALIAS,
                        reason_message=(
                            f"Field '{field_name}' contains a YAML anchor or alias."
                        ),
                        blocking=True,
                    )
                )
                continue

            value_token = occurrence.value_text.strip()
            if value_token.startswith("|") or value_token.startswith(">"):
                warnings.append(
                    RetrofitWarning(
                        path=path,
                        field=field_name,
                        reason_code=REASON_BLOCK_SCALAR,
                        reason_message=(
                            f"Field '{field_name}' uses block scalar syntax."
                        ),
                        blocking=True,
                    )
                )
                continue
            if value_token.startswith("!"):
                warnings.append(
                    RetrofitWarning(
                        path=path,
                        field=field_name,
                        reason_code=REASON_UNPATCHABLE_FORMAT,
                        reason_message=(
                            f"Field '{field_name}' uses YAML tag syntax."
                        ),
                        blocking=True,
                    )
                )
                continue

            if should_remove:
                del lines[occurrence.line_index : occurrence.end_line_index]
                top_level = _index_top_level_fields(lines)
                edits.append(
                    RetrofitEdit(
                        field=field_name,
                        action="remove",
                        old_value=on_disk,
                        new_value=[],
                    )
                )
                continue

            if sorted(on_disk) == sorted(new_value):
                continue

            replacement = _format_field_block(field_name, new_value, line_ending)
            del lines[occurrence.line_index : occurrence.end_line_index]
            for offset, replacement_line in enumerate(replacement):
                lines.insert(occurrence.line_index + offset, replacement_line)
            top_level = _index_top_level_fields(lines)
            edits.append(
                RetrofitEdit(
                    field=field_name,
                    action="replace",
                    old_value=on_disk,
                    new_value=list(new_value),
                )
            )
            continue

        replacement = _format_field_block(field_name, new_value, line_ending)
        if lines and not lines[-1].endswith(("\n", "\r")):
            lines[-1] = lines[-1] + line_ending
        insertion_index = len(lines)
        for offset, replacement_line in enumerate(replacement):
            lines.insert(insertion_index + offset, replacement_line)
        top_level = _index_top_level_fields(lines)
        edits.append(
            RetrofitEdit(
                field=field_name,
                action="insert",
                old_value=None,
                new_value=list(new_value),
            )
        )

    if not edits and not warnings:
        return None

    new_frontmatter = "".join(lines)
    if edits:
        new_frontmatter = _ensure_trailing_newline(new_frontmatter, line_ending)
    normalized_new = f"---{new_frontmatter}---{split.body}"
    new_content = decoded.leading_prefix + normalized_new

    if not edits:
        new_content = decoded.original

    return FilePlan(
        path=path,
        new_content=new_content,
        edits=edits,
        warnings=warnings,
    )


def _coerce_on_disk_list(parsed_value: object) -> Optional[List[str]]:
    if parsed_value is None:
        return []
    if isinstance(parsed_value, str):
        stripped = parsed_value.strip()
        return [stripped] if stripped else []
    if isinstance(parsed_value, list):
        items: List[str] = []
        for item in parsed_value:
            if isinstance(item, (dict, list, tuple, set)):
                return None
            if item is None:
                continue
            items.append(str(item).strip())
        return [item for item in items if item]
    return None


def _compute_retrofit_tags(parsed_frontmatter: Dict[str, object]) -> List[str]:
    computed_frontmatter = dict(parsed_frontmatter)
    computed_frontmatter.pop("tags", None)
    return normalize_tags(computed_frontmatter)


def _has_nonempty_parsed_value(
    parsed_frontmatter: Dict[str, object], field_name: str, on_disk: Optional[List[str]]
) -> bool:
    if field_name not in parsed_frontmatter:
        return False
    if on_disk is not None:
        return bool(on_disk)

    parsed_value = parsed_frontmatter[field_name]
    if isinstance(parsed_value, str):
        return bool(parsed_value.strip())
    if isinstance(parsed_value, list):
        return any(str(item).strip() for item in parsed_value if item is not None)
    return parsed_value is not None


def _loader_issues_to_warnings(issues: Sequence[DocumentLoadIssue]) -> List[RetrofitWarning]:
    return [
        RetrofitWarning(
            path=issue.path,
            field=None,
            reason_code=issue.code,
            reason_message=issue.message,
            blocking=False,
        )
        for issue in issues
    ]


def _block_contains_anchor(block_lines: Sequence[str]) -> bool:
    for line in block_lines:
        if "&" in line or "*" in line:
            for index, char in enumerate(line):
                if char not in {"&", "*"}:
                    continue
                prev = line[index - 1] if index > 0 else ""
                nxt = line[index + 1] if index + 1 < len(line) else ""
                if prev in {"", " ", "\t", ":", "-", "[", ",", "\n"} and nxt.isalnum():
                    return True
    return False


def _detect_dominant_line_ending(lines: Sequence[str]) -> str:
    crlf_count = sum(1 for line in lines if line.endswith("\r\n"))
    lf_count = sum(
        1 for line in lines if line.endswith("\n") and not line.endswith("\r\n")
    )
    if crlf_count > lf_count:
        return "\r\n"
    return "\n"


def _format_field_block(field_name: str, values: Sequence[str], line_ending: str) -> List[str]:
    out = [f"{field_name}:{line_ending}"]
    for value in values:
        out.append(f"  - {_serialize_item(value)}{line_ending}")
    return out


def _serialize_item(value: str) -> str:
    needs_quote = False
    if value == "" or value != value.strip():
        needs_quote = True
    elif any(ch in value for ch in ":#&*!|>%@`,[]{}"):
        needs_quote = True
    elif value.lower() in {"true", "false", "yes", "no", "null", "on", "off", "~"}:
        needs_quote = True
    elif _DATE_LIKE_RE.match(value):
        needs_quote = True
    else:
        try:
            float(value)
            needs_quote = True
        except ValueError:
            pass
    if not needs_quote:
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _ensure_trailing_newline(frontmatter_text: str, line_ending: str) -> str:
    if not frontmatter_text:
        return line_ending
    if frontmatter_text.endswith(("\n", "\r")):
        return frontmatter_text
    return frontmatter_text + line_ending


# ----------------------------------------------------------------------------
# Output emitters
# ----------------------------------------------------------------------------


def _summary_to_json(summary: RetrofitSummary, *, applied_files: int = 0) -> Dict[str, int]:
    return {
        "files_scanned": summary.files_scanned,
        "documents_loaded": summary.documents_loaded,
        "planned_files": summary.planned_files,
        "applied_files": applied_files,
        "inserts": summary.inserts,
        "replaces": summary.replaces,
        "warnings": summary.warnings,
    }


def _file_plan_to_json(file_plan: FilePlan) -> Dict[str, object]:
    return {
        "path": str(file_plan.path),
        "edits": [
            {
                "field": edit.field,
                "action": edit.action,
                "old_value": edit.old_value,
                "new_value": edit.new_value,
            }
            for edit in file_plan.edits
        ],
        "warnings": [_warning_to_json(warning) for warning in file_plan.warnings],
    }


def _warning_to_json(warning: RetrofitWarning) -> Dict[str, object]:
    return {
        "path": str(warning.path),
        "field": warning.field,
        "reason_code": warning.reason_code,
        "reason_message": warning.reason_message,
        "blocking": warning.blocking,
    }


def _emit_dry_run(options: RetrofitOptions, plan: RetrofitPlan) -> None:
    if options.json_output:
        emit_command_success(
            command="retrofit",
            exit_code=0,
            message="dry_run",
            data={
                "mode": "dry_run",
                "scope": plan.scope.value,
                "summary": _summary_to_json(plan.summary),
                "files": [_file_plan_to_json(item) for item in plan.files],
                "warnings": [_warning_to_json(item) for item in plan.warnings],
            },
            warnings=[_warning_to_json(item) for item in plan.warnings],
        )
        return

    header = f"DRY RUN: ontos retrofit --obsidian --scope {plan.scope.value}"
    print(header)
    print()
    print("Summary")
    print(f"  Files scanned: {plan.summary.files_scanned}")
    print(f"  Documents loaded: {plan.summary.documents_loaded}")
    print(f"  Planned file edits: {plan.summary.planned_files}")
    print(f"  Inserts: {plan.summary.inserts}")
    print(f"  Replaces: {plan.summary.replaces}")
    if plan.summary.warnings:
        print(f"  Warnings: {plan.summary.warnings}")
    print()

    if not options.quiet:
        for file_plan in plan.files:
            if not (file_plan.edits or file_plan.warnings):
                continue
            print(f"File: {file_plan.path}")
            for edit in file_plan.edits:
                new_preview = ", ".join(edit.new_value)
                old_preview = (
                    ", ".join(edit.old_value) if edit.old_value is not None else "<absent>"
                )
                print(
                    f"    - {edit.action} {edit.field}: {old_preview} -> {new_preview}"
                )
            for warning in file_plan.warnings:
                field_part = f" field={warning.field}" if warning.field else ""
                print(
                    f"    ! {warning.reason_code}{field_part}: {warning.reason_message}"
                )
            print()

    reported_warning_keys = {
        (
            str(warning.path),
            warning.field,
            warning.reason_code,
            warning.reason_message,
            warning.blocking,
        )
        for file_plan in plan.files
        for warning in file_plan.warnings
    }
    external_warnings = [
        warning
        for warning in plan.warnings
        if (
            str(warning.path),
            warning.field,
            warning.reason_code,
            warning.reason_message,
            warning.blocking,
        )
        not in reported_warning_keys
    ]
    for warning in external_warnings:
        field_part = f" field={warning.field}" if warning.field else ""
        print(f"warning ({warning.reason_code}){field_part}: {warning.reason_message} [{warning.path}]")

    print("No files written. Re-run with --apply to execute.")


def _emit_apply_success(
    options: RetrofitOptions,
    plan: RetrofitPlan,
    modified_paths: Sequence[Path],
) -> None:
    if options.json_output:
        emit_command_success(
            command="retrofit",
            exit_code=0,
            message="apply",
            data={
                "mode": "apply",
                "scope": plan.scope.value,
                "summary": _summary_to_json(
                    plan.summary, applied_files=len(modified_paths)
                ),
                "files": [_file_plan_to_json(item) for item in plan.files],
                "warnings": [_warning_to_json(item) for item in plan.warnings],
                "applied_paths": [str(path) for path in sorted(modified_paths)],
                "post_apply_warning": POST_APPLY_WARNING,
                "partial_commit": {"detected": False, "message": None},
            },
            warnings=[_warning_to_json(item) for item in plan.warnings],
        )
        return

    print(
        f"Applied retrofit: tags + aliases "
        f"({len(modified_paths)} file(s) updated)."
    )
    if not options.quiet:
        for path in sorted(modified_paths):
            print(f"  - {path}")
    print(POST_APPLY_WARNING)


def _emit_error(
    *,
    options: RetrofitOptions,
    mode: str,
    scope: ScanScope,
    error: RetrofitError,
    warnings: Sequence[RetrofitWarning],
    partial_commit: bool,
) -> None:
    if options.json_output:
        emit_command_error(
            command="retrofit",
            exit_code=1,
            code=error.code,
            message=error.message,
            data={
                "mode": mode,
                "scope": scope.value,
                "summary": _summary_to_json(
                    RetrofitSummary(
                        files_scanned=0,
                        documents_loaded=0,
                        planned_files=0,
                        inserts=0,
                        replaces=0,
                        warnings=len(warnings),
                    )
                ),
                "files": [],
                "warnings": [_warning_to_json(item) for item in warnings],
                "applied_paths": [],
                "post_apply_warning": POST_APPLY_WARNING if mode == "apply" else None,
                "partial_commit": {
                    "detected": partial_commit,
                    "message": error.message if partial_commit else None,
                },
            },
            warnings=[_warning_to_json(item) for item in warnings],
        )
        return

    print(f"Error [{error.code}]: {error.message}")
    for warning in warnings:
        field_part = f" field={warning.field}" if warning.field else ""
        print(
            f"  warning ({warning.reason_code}){field_part}: "
            f"{warning.reason_message} [{warning.path}]"
        )
