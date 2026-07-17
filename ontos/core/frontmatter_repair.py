"""Frontmatter diagnostics and conservative enum repair planning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from ontos.core.context import SessionContext
from ontos.core.frontmatter_edit import patch_frontmatter_fields, read_utf8_for_mutation
from ontos.core.types import DocumentStatus, DocumentType
from ontos.io.files import DocumentLoadIssue, load_documents
from ontos.io.yaml import parse_frontmatter_content


TYPE_REPAIRS: Dict[str, str] = {
    # (#117) `review`, `retro`, `tracker` are now first-class canonical
    # types in DocumentType — no repair needed. Aliases that aren't
    # canonical map to the closest canonical value.
    "proposal": "strategy",
    "retrospective": "retro",
    "final-report": "report",
    "final_report": "report",
    "verdict": "log",
    "prompt": "log",
    "artifact": "log",
}

STATUS_REPAIRS: Dict[str, str] = {
    # (#117) `completed`, `ready`, `proposed`, `revised`, `in-lifecycle`
    # are now first-class canonical statuses. Remaining repairs cover
    # genuine aliases.
    "passed": "complete",
    "approve": "complete",
    "approved": "complete",
    "final": "complete",
    "done": "complete",
    "pr-open": "active",
    "in-review": "active",
    "halted": "rejected",
    "failed": "rejected",
    # (#178) The canonical status is `in_progress`; the hyphenated spelling
    # is the single most common agent-emitted alias.
    "in-progress": "in_progress",
}


@dataclass(frozen=True)
class EnumRepairEdit:
    path: Path
    field: str
    old_value: str
    new_value: Optional[str]
    line: Optional[int]
    original_field: str
    repairable: bool
    reason: str
    # (#178) Which mapping produced the repair: 'built-in' for the shipped
    # tables, 'config' for [frontmatter.aliases.*]; None when unresolved.
    source: Optional[str] = None

    def to_dict(self, *, root: Optional[Path] = None) -> Dict[str, Any]:
        if root is None:
            path_text = str(self.path)
        else:
            try:
                path_text = (
                    self.path.resolve(strict=False)
                    .relative_to(root.resolve(strict=False))
                    .as_posix()
                )
            except ValueError:
                path_text = str(self.path)
        return {
            "path": path_text,
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "line": self.line,
            "original_field": self.original_field,
            "repairable": self.repairable,
            "reason": self.reason,
            "source": self.source,
        }


@dataclass
class EnumRepairPlan:
    files_scanned: int
    diagnostics: List[DocumentLoadIssue]
    edits: List[EnumRepairEdit]

    @property
    def repairable_edits(self) -> List[EnumRepairEdit]:
        return [edit for edit in self.edits if edit.repairable]

    @property
    def unresolved_edits(self) -> List[EnumRepairEdit]:
        return [edit for edit in self.edits if not edit.repairable]

    def to_dict(self, *, root: Optional[Path] = None) -> Dict[str, Any]:
        return {
            "files_scanned": self.files_scanned,
            "diagnostics": [
                issue.to_dict(root=root) for issue in self.diagnostics
            ],
            "edits": [edit.to_dict(root=root) for edit in self.edits],
            "summary": {
                "diagnostics": len(self.diagnostics),
                "repairable": len(self.repairable_edits),
                "unresolved": len(self.unresolved_edits),
            },
        }


def build_enum_repair_plan(
    paths: Sequence[Path],
    *,
    type_aliases: Optional[Mapping[str, str]] = None,
    status_aliases: Optional[Mapping[str, str]] = None,
) -> EnumRepairPlan:
    """Load documents and build conservative enum repair edits.

    Args:
        paths: Documents to diagnose.
        type_aliases: (#178) Workspace alias table for ``type`` values from
            ``[frontmatter.aliases.type]``. Config loading rejects tables
            that conflict with the built-ins, so at this layer a workspace
            entry can only restate a built-in or add a new mapping;
            programmatic callers passing their own tables get
            workspace-wins precedence.
        status_aliases: (#178) Workspace alias table for ``status`` values
            from ``[frontmatter.aliases.status]``; same contract as
            ``type_aliases``.
    """
    load_result = load_documents(list(paths), parse_frontmatter_content)
    diagnostics = [issue for issue in load_result.issues if issue.code == "invalid_enum"]
    edits = [
        _issue_to_edit(issue, type_aliases or {}, status_aliases or {})
        for issue in diagnostics
    ]
    return EnumRepairPlan(
        files_scanned=len(paths),
        diagnostics=diagnostics,
        edits=edits,
    )


def apply_enum_repair_plan(
    plan: EnumRepairPlan,
    *,
    repo_root: Path,
) -> List[Path]:
    """Apply repairable edits using SessionContext buffered writes."""
    grouped: Dict[Path, List[EnumRepairEdit]] = {}
    for edit in plan.repairable_edits:
        grouped.setdefault(edit.path, []).append(edit)

    ctx = SessionContext.from_repo(repo_root)
    for path, edits in grouped.items():
        new_content = _apply_file_edits(path, edits)
        ctx.buffer_write(path, new_content)
    return ctx.commit()


def enum_issue_summary(
    issues: Iterable[DocumentLoadIssue],
    *,
    root: Optional[Path] = None,
    limit: int = 5,
) -> List[str]:
    """Format top enum diagnostics for human output."""
    lines: List[str] = []
    for issue in list(issues)[:limit]:
        payload = issue.to_dict(root=root)
        line = payload["line"]
        loc = payload["path"] if line is None else f"{payload['path']}:{line}"
        lines.append(
            f"{loc} {payload['field']}={payload['observed_value']!r}: "
            f"{payload['suggested_fix']}"
        )
    return lines


def _issue_to_edit(
    issue: DocumentLoadIssue,
    type_aliases: Mapping[str, str],
    status_aliases: Mapping[str, str],
) -> EnumRepairEdit:
    field = issue.field or ""
    old_value = str(issue.value).strip()
    normalized_value = old_value.lower()
    if field == "type":
        builtin, workspace = TYPE_REPAIRS, type_aliases
    elif field == "status":
        builtin, workspace = STATUS_REPAIRS, status_aliases
    else:
        builtin, workspace = {}, {}
    # (#178) Workspace aliases win over built-ins so a project can override
    # a shipped mapping; both are explicit tables, never guesses.
    new_value: Optional[str] = None
    source: Optional[str] = None
    if normalized_value in workspace:
        new_value, source = workspace[normalized_value], "config"
    elif normalized_value in builtin:
        new_value, source = builtin[normalized_value], "built-in"
    allowed = [item.value for item in DocumentType] if field == "type" else [item.value for item in DocumentStatus]
    if new_value is None:
        return EnumRepairEdit(
            path=issue.path,
            field=field,
            old_value=old_value,
            new_value=None,
            line=issue.line,
            original_field=f"original_{field}",
            repairable=False,
            reason=(
                f"No conservative mapping is known. Allowed values: "
                f"{', '.join(allowed)}. Declare an explicit mapping under "
                f"[frontmatter.aliases.{field or 'status'}] in .ontos.toml "
                f"to make this repairable."
            ),
        )
    return EnumRepairEdit(
        path=issue.path,
        field=field,
        old_value=old_value,
        new_value=new_value,
        line=issue.line,
        original_field=f"original_{field}",
        repairable=True,
        reason=(
            f"Map lifecycle artifact value {old_value!r} to Ontos enum "
            f"{new_value!r} ({source} mapping)."
        ),
        source=source,
    )


def _apply_file_edits(path: Path, edits: Sequence[EnumRepairEdit]) -> str:
    original = read_utf8_for_mutation(path)
    parsed, _ = parse_frontmatter_content(original.removeprefix("\ufeff"))
    if not parsed:
        return original

    updates: Dict[str, Any] = {}
    for edit in sorted(edits, key=lambda item: item.field):
        if edit.new_value is None:
            continue
        if edit.original_field not in parsed:
            updates[edit.original_field] = _extract_raw_scalar(
                original, edit.field, edit.old_value
            )
        updates[edit.field] = edit.new_value
    return patch_frontmatter_fields(original, updates) if updates else original


def _strip_trailing_comment(text: str) -> str:
    """Remove a trailing YAML comment, honoring quotes and the space rule.

    (PR #182 review) A ``#`` inside a quoted scalar is content, and an
    unquoted ``#`` only opens a comment when preceded by whitespace (or at
    the start of the value) — ``qa#blocked`` has no comment at all.
    """
    quote: Optional[str] = None
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if quote is not None:
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            continue
        if char == "#" and (index == 0 or text[index - 1] in " \t"):
            return text[:index]
    return text


def _extract_raw_scalar(original: str, field: str, fallback: str) -> str:
    """Recover the spelled value of a one-line ``field:`` entry.

    Used to preserve the pre-repair spelling as ``original_<field>``.
    Quote-aware (PR #182 review): ``status: "qa#blocked"`` must yield
    ``qa#blocked``, not a truncated ``"qa``. Anything the lexical scan
    cannot interpret unambiguously falls back to the YAML-parsed value.
    """
    match = re.search(
        rf"(?m)^[ \t]*{re.escape(field)}[ \t]*:[ \t]*(.*?)[ \t]*\r?$",
        original,
    )
    if not match:
        return fallback
    raw_value = _strip_trailing_comment(match.group(1)).strip()
    if not raw_value:
        return fallback
    if raw_value[0] in {'"', "'"}:
        quote = raw_value[0]
        if len(raw_value) < 2 or raw_value[-1] != quote:
            # Unterminated or otherwise malformed quoting — trust the
            # parser, not the lexical scan.
            return fallback
        inner = raw_value[1:-1]
        if quote == "'":
            return inner.replace("''", "'")
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    return raw_value
