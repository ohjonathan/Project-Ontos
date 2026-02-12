"""Atomic document ID rename command (`ontos rename`)."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ontos.core.body_refs import MatchType, ZoneType, scan_body_references
from ontos.core.context import SessionContext
from ontos.core.types import DocumentData
from ontos.io.config import load_project_config
from ontos.io.files import DocumentLoadIssue, find_project_root, load_documents, scan_documents
from ontos.io.scan_scope import ScanScope, collect_scoped_documents, resolve_scan_scope
from ontos.io.yaml import parse_frontmatter_content
from ontos.ui.json_output import emit_command_error, emit_command_success

_ID_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$")
_RESERVED_YAML_WORDS = {"true", "false", "yes", "no", "null", "on", "off"}
_TOP_LEVEL_FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:(.*)$")
_ANCHOR_ALIAS_RE = re.compile(r"(^|[\s,\[\]-])(?:&[A-Za-z0-9_-]+|\*[A-Za-z0-9_-]+)")

REASON_DUPLICATE_TOP_LEVEL = "duplicate_top_level_field"
REASON_BLOCK_SCALAR = "block_scalar_value"
REASON_NON_SCALAR_LIST = "non_scalar_list"
REASON_ANCHOR_ALIAS = "anchor_or_alias"
REASON_NESTED_INLINE = "nested_inline_collection"
REASON_UNPATCHABLE_FORMAT = "unpatchable_field_format"

POST_APPLY_WARNING = "Derived artifacts may be stale. Run `ontos map` and `ontos agents` to regenerate."


@dataclass
class RenameOptions:
    """Options for rename command."""

    old_id: str
    new_id: str
    apply: bool = False
    scope: Optional[str] = None
    json_output: bool = False
    quiet: bool = False


@dataclass(frozen=True)
class FrontmatterEdit:
    field: str
    line: int
    old: str
    new: str


@dataclass(frozen=True)
class BodyEdit:
    line: int
    zone: str
    match_type: str
    rewritable: bool
    old: str
    new: str
    context_before: str
    context_line: str
    context_after: str
    skip_reason: Optional[str] = None


@dataclass(frozen=True)
class RenameWarning:
    path: Path
    reason_code: str
    reason_message: str
    field: Optional[str] = None
    blocking: bool = False


@dataclass
class FilePlan:
    path: Path
    new_content: str
    frontmatter_edits: List[FrontmatterEdit] = field(default_factory=list)
    body_edits: List[BodyEdit] = field(default_factory=list)
    warnings: List[RenameWarning] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.frontmatter_edits or any(edit.rewritable for edit in self.body_edits))


@dataclass(frozen=True)
class RenameSummary:
    files_scanned: int
    documents_loaded: int
    planned_files: int
    frontmatter_edits: int
    body_edits: int
    skipped_zone_sightings: int
    warnings: int


@dataclass
class RenamePlan:
    mode: str
    scope: ScanScope
    old_id: str
    new_id: str
    summary: RenameSummary
    files: List[FilePlan]
    warnings: List[RenameWarning]
    no_op: bool = False

    def blocking_warnings(self) -> List[RenameWarning]:
        return [warning for warning in self.warnings if warning.blocking]


@dataclass(frozen=True)
class RenameError:
    code: str
    message: str


@dataclass
class _LoadedScope:
    repo_root: Path
    scope: ScanScope
    doc_paths: List[Path]
    load_result: object
    docs: Dict[str, DocumentData]


@dataclass(frozen=True)
class _DecodedContent:
    original: str
    leading_prefix: str
    normalized: str
    leading_line_offset: int


@dataclass(frozen=True)
class _FrontmatterSplit:
    has_frontmatter: bool
    frontmatter: str
    body: str
    body_abs_offset: int


@dataclass(frozen=True)
class _TopLevelField:
    key: str
    line_index: int
    line_text: str
    colon_index: int
    value_text: str
    end_line_index: int


@dataclass(frozen=True)
class _ParseFailedSighting:
    path: Path
    line: int
    match_type: str


@dataclass
class _FrontmatterPatchResult:
    patched_frontmatter: str
    edits: List[FrontmatterEdit]
    warnings: List[RenameWarning]
    unsupported: bool


def rename_command(options: RenameOptions) -> int:
    """Execute rename command."""

    mode = "apply" if options.apply else "dry_run"
    prepared, error = _prepare_plan(options, mode=mode)
    if error is not None:
        _emit_error(
            options=options,
            mode=mode,
            scope=prepared.scope if prepared is not None else ScanScope.DOCS,
            old_id=options.old_id,
            new_id=options.new_id,
            error=error,
            warnings=[],
            partial_commit=False,
        )
        return 1

    assert prepared is not None
    plan = prepared.plan
    if plan.no_op:
        _emit_noop(options, plan)
        return 0

    if mode == "dry_run":
        _emit_dry_run(options, plan)
        return 0

    blocking = plan.blocking_warnings()
    if blocking:
        _emit_error(
            options=options,
            mode=mode,
            scope=plan.scope,
            old_id=plan.old_id,
            new_id=plan.new_id,
            error=RenameError(
                code="unsupported_target_format",
                message="Rename plan contains unsupported frontmatter formats. Apply is blocked.",
            ),
            warnings=blocking,
            partial_commit=False,
        )
        return 1

    files_to_apply = [item for item in plan.files if item.has_changes]
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
            old_id=plan.old_id,
            new_id=plan.new_id,
            error=RenameError(
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

    planned_paths = {item.path.resolve() for item in files_to_apply}
    committed_paths = {path.resolve() for path in modified_paths}
    if planned_paths != committed_paths:
        _emit_error(
            options=options,
            mode=mode,
            scope=plan.scope,
            old_id=plan.old_id,
            new_id=plan.new_id,
            error=RenameError(
                code="partial_commit_mismatch",
                message=(
                    "Commit result does not match planned file set. "
                    "Repository may be partially updated."
                ),
            ),
            warnings=plan.warnings,
            partial_commit=True,
            applied_paths=sorted(str(path) for path in committed_paths),
            summary=plan.summary,
        )
        return 1

    _emit_apply_success(options, plan, modified_paths)
    return 0


@dataclass(frozen=True)
class _PreparedPlan:
    scope: ScanScope
    plan: RenamePlan
    scope_data: _LoadedScope


def _prepare_plan(options: RenameOptions, *, mode: str) -> Tuple[Optional[_PreparedPlan], Optional[RenameError]]:
    old_id = options.old_id.strip()
    new_id = options.new_id.strip()

    try:
        repo_root = find_project_root()
    except FileNotFoundError as exc:
        return None, RenameError(code="project_root_not_found", message=str(exc))

    try:
        config = load_project_config(repo_root=repo_root)
    except Exception as exc:  # pragma: no cover - configuration failure path
        return None, RenameError(code="config_error", message=f"Config error: {exc}")

    scope = resolve_scan_scope(options.scope, config.scanning.default_scope)

    if old_id == new_id:
        empty_plan = RenamePlan(
            mode=mode,
            scope=scope,
            old_id=old_id,
            new_id=new_id,
            summary=RenameSummary(
                files_scanned=0,
                documents_loaded=0,
                planned_files=0,
                frontmatter_edits=0,
                body_edits=0,
                skipped_zone_sightings=0,
                warnings=0,
            ),
            files=[],
            warnings=[],
            no_op=True,
        )
        return _PreparedPlan(
            scope=scope,
            plan=empty_plan,
            scope_data=_LoadedScope(
                repo_root=repo_root,
                scope=scope,
                doc_paths=[],
                load_result=None,
                docs={},
            ),
        ), None

    if not _ID_PATTERN.match(new_id):
        return None, RenameError(
            code="invalid_new_id",
            message="new_id must match ^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$",
        )
    if new_id.lower() in _RESERVED_YAML_WORDS:
        return None, RenameError(
            code="reserved_new_id",
            message=(
                "new_id cannot be a YAML reserved word: "
                f"{', '.join(sorted(_RESERVED_YAML_WORDS))}"
            ),
        )

    if mode == "apply":
        clean, git_error = _check_clean_git_state(repo_root)
        if not clean:
            return None, RenameError(
                code="dirty_git_state",
                message=git_error
                or "Git working tree must be clean for --apply.",
            )

    doc_paths = collect_scoped_documents(
        repo_root,
        config,
        scope,
        base_skip_patterns=list(config.scanning.skip_patterns),
    )
    load_result = load_documents(doc_paths, parse_frontmatter_content)
    docs = load_result.documents

    if load_result.duplicate_ids:
        details = []
        for doc_id, paths in sorted(load_result.duplicate_ids.items()):
            joined = ", ".join(str(path) for path in paths)
            details.append(f"{doc_id}: {joined}")
        return None, RenameError(
            code="duplicate_ids",
            message="Duplicate IDs detected in scope: " + "; ".join(details),
        )

    old_docs = [
        doc
        for doc in docs.values()
        if _frontmatter_id_value(doc.frontmatter) == old_id
    ]
    if len(old_docs) != 1:
        return None, RenameError(
            code="old_id_not_found",
            message=(
                f"old_id '{old_id}' must exist exactly once as an explicit frontmatter id. "
                f"Found {len(old_docs)}."
            ),
        )

    if any(_frontmatter_id_value(doc.frontmatter) == new_id for doc in docs.values()):
        return None, RenameError(
            code="new_id_exists",
            message=f"new_id '{new_id}' already exists in active scope.",
        )

    if scope == ScanScope.DOCS:
        external_ids = _load_external_ids(repo_root, config)
        if old_id in external_ids or new_id in external_ids:
            return None, RenameError(
                code="cross_scope_collision",
                message=(
                    "docs-scope rename is unsafe because old_id or new_id exists in "
                    ".ontos-internal. Use --scope library."
                ),
            )

    sightings = _scan_parse_failed_files_for_target(
        issues=load_result.issues,
        old_id=old_id,
    )
    if sightings:
        first = sightings[0]
        return None, RenameError(
            code="parse_failed_target_sighting",
            message=(
                "Found target ID in parse-failed file(s), cannot guarantee safe rewrite: "
                f"{first.path}:{first.line} ({first.match_type})."
            ),
        )

    file_plans: List[FilePlan] = []
    all_warnings: List[RenameWarning] = []
    for doc in sorted(docs.values(), key=lambda item: str(item.filepath)):
        file_plan = _build_file_plan(
            path=doc.filepath,
            old_id=old_id,
            new_id=new_id,
        )
        if file_plan is None:
            continue
        file_plans.append(file_plan)
        all_warnings.extend(file_plan.warnings)

    summary = RenameSummary(
        files_scanned=len(doc_paths),
        documents_loaded=len(docs),
        planned_files=len([item for item in file_plans if item.has_changes]),
        frontmatter_edits=sum(len(item.frontmatter_edits) for item in file_plans),
        body_edits=sum(
            len([edit for edit in item.body_edits if edit.rewritable])
            for item in file_plans
        ),
        skipped_zone_sightings=sum(
            len([edit for edit in item.body_edits if not edit.rewritable])
            for item in file_plans
        ),
        warnings=len(all_warnings),
    )

    plan = RenamePlan(
        mode=mode,
        scope=scope,
        old_id=old_id,
        new_id=new_id,
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
            load_result=load_result,
            docs=docs,
        ),
    ), None


def _check_clean_git_state(repo_root: Path) -> Tuple[bool, Optional[str]]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"Unable to check git state: {exc}"

    if result.returncode != 0:
        return False, "Git working tree must be clean for --apply."
    if result.stdout.strip():
        return False, "Git working tree must be clean for --apply."
    return True, None


def _frontmatter_id_value(frontmatter: Dict[str, object]) -> Optional[str]:
    value = frontmatter.get("id")
    if isinstance(value, str):
        return value.strip()
    return None


def _load_external_ids(repo_root: Path, config) -> set[str]:
    external_root = repo_root / ".ontos-internal"
    if not external_root.exists():
        return set()
    paths = scan_documents([external_root], skip_patterns=list(config.scanning.skip_patterns))
    result = load_documents(paths, parse_frontmatter_content)
    return set(result.documents.keys())


def _scan_parse_failed_files_for_target(
    *,
    issues: Sequence[DocumentLoadIssue],
    old_id: str,
) -> List[_ParseFailedSighting]:
    candidate_paths = sorted(
        {
            issue.path
            for issue in issues
            if issue.code in {"parse_error", "io_error"}
        }
    )

    sightings: List[_ParseFailedSighting] = []
    for path in candidate_paths:
        content = _decode_file_lenient(path)
        if content is None:
            continue
        scan = scan_body_references(
            path=path,
            body=content,
            rename_target=old_id,
            include_skipped=True,
        )
        for match in scan.matches:
            sightings.append(
                _ParseFailedSighting(
                    path=path,
                    line=match.line,
                    match_type=match.match_type.value,
                )
            )
    return sightings


def _decode_file_lenient(path: Path) -> Optional[str]:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8", errors="replace")


def _build_file_plan(*, path: Path, old_id: str, new_id: str) -> Optional[FilePlan]:
    decoded = _read_decoded_content(path)
    split = _split_frontmatter(decoded.normalized)

    warnings: List[RenameWarning] = []
    frontmatter_edits: List[FrontmatterEdit] = []
    frontmatter_block = split.frontmatter
    unsupported = False

    if split.has_frontmatter:
        patched = _patch_frontmatter(
            path=path,
            frontmatter=split.frontmatter,
            old_id=old_id,
            new_id=new_id,
            leading_line_offset=decoded.leading_line_offset,
        )
        frontmatter_block = patched.patched_frontmatter
        frontmatter_edits = patched.edits
        warnings.extend(patched.warnings)
        unsupported = patched.unsupported

    if unsupported:
        return FilePlan(
            path=path,
            new_content=decoded.original,
            frontmatter_edits=[],
            body_edits=[],
            warnings=warnings,
        )

    body_text = split.body
    body_scan = scan_body_references(
        path=path,
        body=body_text,
        rename_target=old_id,
        include_skipped=True,
    )

    body_base_line = decoded.leading_line_offset + _count_pre_body_lines(split)
    body_edits: List[BodyEdit] = []
    replacements: List[Tuple[int, int, str]] = []
    for match in body_scan.matches:
        replacement = (
            _replacement_for_match(match, old_id=old_id, new_id=new_id)
            if match.rewritable
            else match.raw_match
        )
        body_edits.append(
            BodyEdit(
                line=body_base_line + match.line,
                zone=match.zone.value,
                match_type=match.match_type.value,
                rewritable=match.rewritable,
                old=match.raw_match,
                new=replacement,
                context_before=match.context_before,
                context_line=match.line_text,
                context_after=match.context_after,
                skip_reason=match.skip_reason,
            )
        )
        if match.rewritable:
            replacements.append((match.abs_start, match.abs_end, replacement))

    new_body = body_text
    for start, end, replacement in sorted(replacements, key=lambda item: item[0], reverse=True):
        new_body = new_body[:start] + replacement + new_body[end:]

    if split.has_frontmatter:
        normalized_new = f"---{frontmatter_block}---{new_body}"
    else:
        normalized_new = new_body
    new_content = decoded.leading_prefix + normalized_new

    if (
        not frontmatter_edits
        and not body_edits
        and not warnings
        and new_content == decoded.original
    ):
        return None

    return FilePlan(
        path=path,
        new_content=new_content,
        frontmatter_edits=frontmatter_edits,
        body_edits=body_edits,
        warnings=warnings,
    )


def _read_decoded_content(path: Path) -> _DecodedContent:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    decoded = raw.decode("utf-8", errors="replace")
    prefix_len = len(decoded) - len(decoded.lstrip())
    leading_prefix = decoded[:prefix_len]
    normalized = decoded[prefix_len:]
    return _DecodedContent(
        original=decoded,
        leading_prefix=leading_prefix,
        normalized=normalized,
        leading_line_offset=leading_prefix.count("\n"),
    )


def _split_frontmatter(normalized: str) -> _FrontmatterSplit:
    if not normalized.startswith("---"):
        return _FrontmatterSplit(
            has_frontmatter=False,
            frontmatter="",
            body=normalized,
            body_abs_offset=0,
        )
    parts = normalized.split("---", 2)
    if len(parts) < 3:
        return _FrontmatterSplit(
            has_frontmatter=False,
            frontmatter="",
            body=normalized,
            body_abs_offset=0,
        )
    frontmatter = parts[1]
    body = parts[2]
    body_abs_offset = len(f"---{frontmatter}---")
    return _FrontmatterSplit(
        has_frontmatter=True,
        frontmatter=frontmatter,
        body=body,
        body_abs_offset=body_abs_offset,
    )


def _patch_frontmatter(
    *,
    path: Path,
    frontmatter: str,
    old_id: str,
    new_id: str,
    leading_line_offset: int,
) -> _FrontmatterPatchResult:
    normalized_doc = f"---{frontmatter}---"
    try:
        parsed_frontmatter, _ = parse_frontmatter_content(normalized_doc)
    except ValueError:
        warning = RenameWarning(
            path=path,
            field=None,
            reason_code=REASON_UNPATCHABLE_FORMAT,
            reason_message="Frontmatter could not be reparsed for targeted patching.",
            blocking=True,
        )
        return _FrontmatterPatchResult(
            patched_frontmatter=frontmatter,
            edits=[],
            warnings=[warning],
            unsupported=True,
        )

    lines = frontmatter.splitlines(keepends=True)
    top_level = _index_top_level_fields(lines)
    edits: List[FrontmatterEdit] = []
    warnings: List[RenameWarning] = []

    target_fields = ("id", "depends_on", "impacts", "describes")
    for field_name in target_fields:
        parsed_value = parsed_frontmatter.get(field_name)
        needs_patch = _needs_patch(field_name, parsed_value, old_id)
        if not needs_patch:
            continue

        occurrences = [field for field in top_level if field.key == field_name]
        if len(occurrences) != 1:
            warnings.append(
                _unsupported_warning(
                    path=path,
                    field=field_name,
                    reason_code=REASON_DUPLICATE_TOP_LEVEL,
                    message=f"Field '{field_name}' appears more than once at top level.",
                )
            )
            continue
        occurrence = occurrences[0]

        reason = _unsupported_reason_for_parsed_value(field_name, parsed_value)
        if reason is not None:
            warnings.append(
                _unsupported_warning(
                    path=path,
                    field=field_name,
                    reason_code=reason[0],
                    message=reason[1],
                )
            )
            continue

        patch_result = _patch_single_field(
            lines=lines,
            occurrence=occurrence,
            field_name=field_name,
            parsed_value=parsed_value,
            old_id=old_id,
            new_id=new_id,
            leading_line_offset=leading_line_offset,
        )
        edits.extend(patch_result[0])
        warnings.extend(
            _unsupported_warning(
                path=path,
                field=field_name,
                reason_code=reason_code,
                message=message,
            )
            for reason_code, message in patch_result[1]
        )

    unsupported = any(item.blocking for item in warnings)
    return _FrontmatterPatchResult(
        patched_frontmatter="".join(lines),
        edits=edits,
        warnings=warnings,
        unsupported=unsupported,
    )


def _index_top_level_fields(lines: Sequence[str]) -> List[_TopLevelField]:
    top_level_entries: List[Tuple[str, int, str, int, str]] = []
    for index, line in enumerate(lines):
        no_newline = line.rstrip("\r\n")
        if not no_newline:
            continue
        if no_newline.startswith((" ", "\t")):
            continue
        stripped = no_newline.strip()
        if stripped.startswith("#"):
            continue
        match = _TOP_LEVEL_FIELD_RE.match(no_newline)
        if match is None:
            continue
        key = match.group(1)
        colon_index = no_newline.find(":")
        value_text = no_newline[colon_index + 1:]
        top_level_entries.append((key, index, line, colon_index, value_text))

    results: List[_TopLevelField] = []
    for pos, entry in enumerate(top_level_entries):
        next_line_index = top_level_entries[pos + 1][1] if pos + 1 < len(top_level_entries) else len(lines)
        results.append(
            _TopLevelField(
                key=entry[0],
                line_index=entry[1],
                line_text=entry[2],
                colon_index=entry[3],
                value_text=entry[4],
                end_line_index=next_line_index,
            )
        )
    return results


def _needs_patch(field_name: str, parsed_value: object, old_id: str) -> bool:
    if field_name == "id":
        return isinstance(parsed_value, str) and parsed_value == old_id
    if isinstance(parsed_value, str):
        return parsed_value == old_id
    if isinstance(parsed_value, list):
        return any(isinstance(item, str) and item == old_id for item in parsed_value)
    return False


def _unsupported_reason_for_parsed_value(field_name: str, parsed_value: object) -> Optional[Tuple[str, str]]:
    if field_name == "id":
        if not isinstance(parsed_value, str):
            return REASON_UNPATCHABLE_FORMAT, "Field 'id' must be a scalar string."
        return None
    if isinstance(parsed_value, str):
        return None
    if isinstance(parsed_value, list):
        for item in parsed_value:
            if isinstance(item, (dict, list, tuple, set)):
                return REASON_NON_SCALAR_LIST, f"Field '{field_name}' contains non-scalar list members."
        return None
    return REASON_NON_SCALAR_LIST, f"Field '{field_name}' must be a scalar or list of scalars."


def _patch_single_field(
    *,
    lines: List[str],
    occurrence: _TopLevelField,
    field_name: str,
    parsed_value: object,
    old_id: str,
    new_id: str,
    leading_line_offset: int,
) -> Tuple[List[FrontmatterEdit], List[Tuple[str, str]]]:
    issues: List[Tuple[str, str]] = []
    edits: List[FrontmatterEdit] = []

    line_index = occurrence.line_index
    line = lines[line_index]
    body, newline = _split_line_ending(line)
    after_colon = body[occurrence.colon_index + 1:]
    value_part, _ = _split_comment_unquoted(after_colon)
    value_token = value_part.strip()

    if value_token.startswith("|") or value_token.startswith(">"):
        issues.append((REASON_BLOCK_SCALAR, f"Field '{field_name}' uses block scalar syntax."))
        return edits, issues

    if isinstance(parsed_value, list):
        if value_token.startswith("["):
            patched_after, changed, reason = _patch_inline_list_after_colon(after_colon, old_id, new_id)
            if reason is not None:
                issues.append(reason)
                return edits, issues
            if changed:
                lines[line_index] = body[: occurrence.colon_index + 1] + patched_after + newline
                edits.append(
                    FrontmatterEdit(
                        field=field_name,
                        line=_frontmatter_line_number(lines, line_index, leading_line_offset),
                        old=old_id,
                        new=new_id,
                    )
                )
            return edits, issues

        if value_token:
            patched_after, changed, reason = _patch_scalar_after_colon(after_colon, old_id, new_id)
            if reason is not None:
                issues.append(reason)
                return edits, issues
            if changed:
                lines[line_index] = body[: occurrence.colon_index + 1] + patched_after + newline
                edits.append(
                    FrontmatterEdit(
                        field=field_name,
                        line=_frontmatter_line_number(lines, line_index, leading_line_offset),
                        old=old_id,
                        new=new_id,
                    )
                )
            return edits, issues

        for item_index in range(occurrence.line_index + 1, occurrence.end_line_index):
            item_line = lines[item_index]
            item_body, item_newline = _split_line_ending(item_line)
            if not item_body.strip():
                continue
            stripped = item_body.lstrip(" ")
            if stripped.startswith("#"):
                continue
            if not stripped.startswith("-"):
                issues.append((REASON_UNPATCHABLE_FORMAT, f"Field '{field_name}' list contains non-item lines."))
                return edits, issues

            dash_index = item_body.find("-")
            after_dash = item_body[dash_index + 1 :]
            patched_after_dash, changed, reason = _patch_scalar_after_colon(after_dash, old_id, new_id)
            if reason is not None:
                issues.append(reason)
                return edits, issues
            if changed:
                lines[item_index] = item_body[: dash_index + 1] + patched_after_dash + item_newline
                edits.append(
                    FrontmatterEdit(
                        field=field_name,
                        line=_frontmatter_line_number(lines, item_index, leading_line_offset),
                        old=old_id,
                        new=new_id,
                    )
                )
        if not edits:
            issues.append((REASON_UNPATCHABLE_FORMAT, f"Field '{field_name}' could not be patched as a list."))
        return edits, issues

    patched_after, changed, reason = _patch_scalar_after_colon(after_colon, old_id, new_id)
    if reason is not None:
        issues.append(reason)
        return edits, issues
    if changed:
        lines[line_index] = body[: occurrence.colon_index + 1] + patched_after + newline
        edits.append(
            FrontmatterEdit(
                field=field_name,
                line=_frontmatter_line_number(lines, line_index, leading_line_offset),
                old=old_id,
                new=new_id,
            )
        )
    else:
        issues.append((REASON_UNPATCHABLE_FORMAT, f"Field '{field_name}' could not be patched as a scalar."))
    return edits, issues


def _patch_scalar_after_colon(after_colon: str, old_id: str, new_id: str) -> Tuple[str, bool, Optional[Tuple[str, str]]]:
    if _ANCHOR_ALIAS_RE.search(after_colon):
        return after_colon, False, (REASON_ANCHOR_ALIAS, "Scalar contains YAML anchor or alias.")

    value_part, comment_part = _split_comment_unquoted(after_colon)
    value_token = value_part.strip()
    if not value_token:
        return after_colon, False, None
    decoded, quote = _decode_scalar_token(value_token)
    if decoded != old_id:
        return after_colon, False, None

    replacement_token = f"{quote}{new_id}{quote}" if quote is not None else new_id
    replaced = _replace_preserving_padding(value_part, replacement_token)
    return replaced + comment_part, True, None


def _patch_inline_list_after_colon(
    after_colon: str,
    old_id: str,
    new_id: str,
) -> Tuple[str, bool, Optional[Tuple[str, str]]]:
    if _ANCHOR_ALIAS_RE.search(after_colon):
        return after_colon, False, (REASON_ANCHOR_ALIAS, "Inline list contains YAML anchor or alias.")

    value_part, comment_part = _split_comment_unquoted(after_colon)
    token = value_part.strip()
    if not token.startswith("[") or not token.endswith("]"):
        return after_colon, False, (REASON_UNPATCHABLE_FORMAT, "Inline list is malformed.")

    inner = token[1:-1]
    segments: List[str] = []
    cursor = 0
    quote: Optional[str] = None
    escaped = False
    for index, char in enumerate(inner):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if quote is not None:
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            continue
        if char in {"[", "{"}:
            return after_colon, False, (REASON_NESTED_INLINE, "Inline list contains nested collection.")
        if char == ",":
            segments.append(inner[cursor:index])
            cursor = index + 1
    segments.append(inner[cursor:])

    changed = False
    for index, segment in enumerate(segments):
        segment_token = segment.strip()
        if not segment_token:
            continue
        decoded, quote_char = _decode_scalar_token(segment_token)
        if decoded != old_id:
            continue
        replacement_token = f"{quote_char}{new_id}{quote_char}" if quote_char is not None else new_id
        segments[index] = _replace_preserving_padding(segment, replacement_token)
        changed = True

    if not changed:
        return after_colon, False, None

    new_token = "[" + ",".join(segments) + "]"
    replaced = _replace_preserving_padding(value_part, new_token)
    return replaced + comment_part, True, None


def _decode_scalar_token(token: str) -> Tuple[str, Optional[str]]:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1], token[0]
    return token, None


def _split_comment_unquoted(text: str) -> Tuple[str, str]:
    quote: Optional[str] = None
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if quote is not None:
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            continue
        if char == "#":
            return text[:index], text[index:]
    return text, ""


def _replace_preserving_padding(original: str, replacement: str) -> str:
    leading = len(original) - len(original.lstrip())
    trailing = len(original) - len(original.rstrip())
    suffix = original[len(original) - trailing :] if trailing > 0 else ""
    return original[:leading] + replacement + suffix


def _split_line_ending(line: str) -> Tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1], line[-1]
    return line, ""


def _frontmatter_line_number(lines: Sequence[str], line_index: int, leading_line_offset: int) -> int:
    before = "".join(lines[:line_index])
    return leading_line_offset + 1 + ("---" + before).count("\n")


def _unsupported_warning(path: Path, field: Optional[str], reason_code: str, message: str) -> RenameWarning:
    return RenameWarning(
        path=path,
        field=field,
        reason_code=reason_code,
        reason_message=message,
        blocking=True,
    )


def _count_pre_body_lines(split: _FrontmatterSplit) -> int:
    if not split.has_frontmatter:
        return 0
    return len(f"---{split.frontmatter}---".splitlines())


def _replacement_for_match(match, *, old_id: str, new_id: str) -> str:
    if match.match_type == MatchType.BARE_ID_TOKEN:
        return new_id
    return _rewrite_markdown_target(match.raw_match, old_id=old_id, new_id=new_id)


def _rewrite_markdown_target(raw_target: str, *, old_id: str, new_id: str) -> str:
    target = raw_target
    has_angle = target.startswith("<") and target.endswith(">")
    if has_angle:
        target = target[1:-1]

    if "#" in target:
        base, fragment = target.split("#", 1)
        fragment_part = "#" + fragment
    else:
        base = target
        fragment_part = ""

    if "/" in base:
        separator = "/"
    elif "\\" in base:
        separator = "\\"
    else:
        separator = ""

    prefix = ""
    leaf = base
    if separator:
        parts = base.split(separator)
        prefix = separator.join(parts[:-1]) + separator if len(parts) > 1 else ""
        leaf = parts[-1]

    extension = ""
    if leaf.lower().endswith(".md"):
        extension = leaf[-3:]
        stem = leaf[:-3]
    else:
        stem = leaf

    if stem == old_id:
        leaf = f"{new_id}{extension}"

    rewritten = f"{prefix}{leaf}{fragment_part}"
    if has_angle:
        return f"<{rewritten}>"
    return rewritten


def _emit_noop(options: RenameOptions, plan: RenamePlan) -> None:
    if options.json_output:
        emit_command_success(
            command="rename",
            exit_code=0,
            message="nothing_to_do",
            data={
                "mode": plan.mode,
                "scope": plan.scope.value,
                "old_id": plan.old_id,
                "new_id": plan.new_id,
                "summary": _summary_to_json(plan.summary),
                "files": [],
            },
        )
        return
    print("Rename no-op: old_id and new_id are identical (nothing_to_do).")


def _emit_dry_run(options: RenameOptions, plan: RenamePlan) -> None:
    if options.json_output:
        emit_command_success(
            command="rename",
            exit_code=0,
            message="dry_run",
            data={
                "mode": "dry_run",
                "scope": plan.scope.value,
                "old_id": plan.old_id,
                "new_id": plan.new_id,
                "summary": _summary_to_json(plan.summary),
                "files": [_file_plan_to_json(item) for item in plan.files],
            },
            warnings=[_warning_to_json(item) for item in plan.warnings],
        )
        return

    header = (
        f"DRY RUN: ontos rename {plan.old_id} {plan.new_id} --scope {plan.scope.value}"
    )
    print(header)
    print()
    print("Summary")
    print(f"  Files scanned: {plan.summary.files_scanned}")
    print(f"  Documents loaded: {plan.summary.documents_loaded}")
    print(f"  Planned file edits: {plan.summary.planned_files}")
    print(f"  Frontmatter edits: {plan.summary.frontmatter_edits}")
    print(f"  Body edits (rewritable): {plan.summary.body_edits}")
    print(f"  Body sightings skipped (code zones): {plan.summary.skipped_zone_sightings}")
    if plan.summary.warnings:
        print(f"  Warnings: {plan.summary.warnings}")
    print()

    if not options.quiet:
        for file_plan in plan.files:
            if not (file_plan.frontmatter_edits or file_plan.body_edits or file_plan.warnings):
                continue
            print(f"File: {file_plan.path}")
            if file_plan.frontmatter_edits:
                print("  Frontmatter")
                for edit in file_plan.frontmatter_edits:
                    print(f"    - line {edit.line} field={edit.field}: {edit.old} -> {edit.new}")
            if file_plan.body_edits:
                print("  Body")
                for edit in file_plan.body_edits:
                    marker = " [SKIPPED]" if not edit.rewritable else ""
                    print(
                        "    - "
                        f"line {edit.line} zone={edit.zone} match={edit.match_type}{marker}"
                    )
                    if edit.context_before:
                        for context_line in edit.context_before.split("\n"):
                            print(f"      {context_line}")
                    print(f"      {edit.context_line}")
                    if edit.context_after:
                        for context_line in edit.context_after.split("\n"):
                            print(f"      {context_line}")
                    if edit.rewritable:
                        print(f"      replace: {edit.old} -> {edit.new}")
                    else:
                        print(f"      reason: {edit.skip_reason}")
            if file_plan.warnings:
                print("  Warnings")
                for warning in file_plan.warnings:
                    field_part = f" field={warning.field}" if warning.field else ""
                    print(
                        "    - "
                        f"{warning.reason_code}{field_part}: {warning.reason_message}"
                    )
            print()

    print("No files written. Re-run with --apply to execute.")


def _emit_apply_success(options: RenameOptions, plan: RenamePlan, modified_paths: Sequence[Path]) -> None:
    if options.json_output:
        emit_command_success(
            command="rename",
            exit_code=0,
            message="apply",
            data={
                "mode": "apply",
                "scope": plan.scope.value,
                "old_id": plan.old_id,
                "new_id": plan.new_id,
                "summary": _summary_to_json(plan.summary, applied_files=len(modified_paths)),
                "applied_paths": [str(path) for path in sorted(modified_paths)],
                "post_apply_warning": POST_APPLY_WARNING,
                "partial_commit": {"detected": False, "message": None},
            },
            warnings=[_warning_to_json(item) for item in plan.warnings],
        )
        return

    print(
        f"Applied rename: {plan.old_id} -> {plan.new_id} "
        f"({len(modified_paths)} file(s) updated)."
    )
    if not options.quiet:
        for path in sorted(modified_paths):
            print(f"  - {path}")
    print(POST_APPLY_WARNING)


def _emit_error(
    *,
    options: RenameOptions,
    mode: str,
    scope: ScanScope,
    old_id: str,
    new_id: str,
    error: RenameError,
    warnings: Sequence[RenameWarning],
    partial_commit: bool,
    applied_paths: Optional[Sequence[str]] = None,
    summary: Optional[RenameSummary] = None,
) -> None:
    if options.json_output:
        emit_command_error(
            command="rename",
            exit_code=1,
            code=error.code,
            message=error.message,
            data={
                "mode": mode,
                "scope": scope.value,
                "old_id": old_id,
                "new_id": new_id,
                "summary": _summary_to_json(
                    summary
                    or RenameSummary(
                        files_scanned=0,
                        documents_loaded=0,
                        planned_files=0,
                        frontmatter_edits=0,
                        body_edits=0,
                        skipped_zone_sightings=0,
                        warnings=len(warnings),
                    ),
                    applied_files=len(applied_paths or []),
                ),
                "files": [],
                "applied_paths": list(applied_paths or []),
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
            f"  warning ({warning.reason_code}){field_part}: {warning.reason_message} [{warning.path}]"
        )


def _summary_to_json(summary: RenameSummary, applied_files: int = 0) -> Dict[str, int]:
    return {
        "files_scanned": summary.files_scanned,
        "documents_loaded": summary.documents_loaded,
        "planned_files": summary.planned_files,
        "applied_files": applied_files,
        "frontmatter_edits": summary.frontmatter_edits,
        "body_edits": summary.body_edits,
        "skipped_zone_sightings": summary.skipped_zone_sightings,
        "warnings": summary.warnings,
    }


def _file_plan_to_json(file_plan: FilePlan) -> Dict[str, object]:
    return {
        "path": str(file_plan.path),
        "frontmatter_edits": [
            {
                "field": edit.field,
                "line": edit.line,
                "old": edit.old,
                "new": edit.new,
            }
            for edit in file_plan.frontmatter_edits
        ],
        "body_edits": [
            {
                "line": edit.line,
                "zone": edit.zone,
                "match_type": edit.match_type,
                "rewritable": edit.rewritable,
                "old": edit.old,
                "new": edit.new,
                "context_before": edit.context_before,
                "context_line": edit.context_line,
                "context_after": edit.context_after,
                "skip_reason": edit.skip_reason,
            }
            for edit in file_plan.body_edits
        ],
        "warnings": [_warning_to_json(warning) for warning in file_plan.warnings],
    }


def _warning_to_json(warning: RenameWarning) -> Dict[str, object]:
    return {
        "path": str(warning.path),
        "field": warning.field,
        "reason_code": warning.reason_code,
        "reason_message": warning.reason_message,
        "blocking": warning.blocking,
    }
