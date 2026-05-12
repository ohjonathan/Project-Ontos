"""Frontmatter diagnostics and conservative enum repair planning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from ontos.core.context import SessionContext
from ontos.core.frontmatter_edit import (
    _index_top_level_fields,
    _read_decoded_content,
    _split_frontmatter,
)
from ontos.core.types import DocumentStatus, DocumentType
from ontos.io.files import DocumentLoadIssue, load_documents
from ontos.io.yaml import parse_frontmatter_content


TYPE_REPAIRS: Dict[str, str] = {
    "proposal": "strategy",
    "review": "log",
    "retro": "log",
    "retrospective": "log",
    "tracker": "log",
    "final-report": "log",
    "final_report": "log",
    "verdict": "log",
    "prompt": "log",
    "artifact": "log",
}

STATUS_REPAIRS: Dict[str, str] = {
    "completed": "complete",
    "passed": "complete",
    "approve": "complete",
    "approved": "complete",
    "final": "complete",
    "ready": "complete",
    "done": "complete",
    "pr-open": "active",
    "in-review": "active",
    "halted": "rejected",
    "failed": "rejected",
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


def build_enum_repair_plan(paths: Sequence[Path]) -> EnumRepairPlan:
    """Load documents and build conservative enum repair edits."""
    load_result = load_documents(list(paths), parse_frontmatter_content)
    diagnostics = [issue for issue in load_result.issues if issue.code == "invalid_enum"]
    edits = [_issue_to_edit(issue) for issue in diagnostics]
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


def _issue_to_edit(issue: DocumentLoadIssue) -> EnumRepairEdit:
    field = issue.field or ""
    old_value = str(issue.value).strip().lower()
    mapping = TYPE_REPAIRS if field == "type" else STATUS_REPAIRS if field == "status" else {}
    new_value = mapping.get(old_value)
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
            reason=f"No conservative mapping is known. Allowed values: {', '.join(allowed)}.",
        )
    return EnumRepairEdit(
        path=issue.path,
        field=field,
        old_value=old_value,
        new_value=new_value,
        line=issue.line,
        original_field=f"original_{field}",
        repairable=True,
        reason=f"Map lifecycle artifact value {old_value!r} to Ontos enum {new_value!r}.",
    )


def _apply_file_edits(path: Path, edits: Sequence[EnumRepairEdit]) -> str:
    decoded = _read_decoded_content(path)
    split = _split_frontmatter(decoded.normalized)
    if not split.has_frontmatter:
        return decoded.original

    lines = split.frontmatter.splitlines(keepends=True)
    line_ending = "\r\n" if sum(1 for line in lines if line.endswith("\r\n")) > sum(1 for line in lines if line.endswith("\n") and not line.endswith("\r\n")) else "\n"

    for edit in sorted(edits, key=lambda item: item.field):
        top_level = _index_top_level_fields(lines)
        fields = {item.key: item for item in top_level}
        target = fields.get(edit.field)
        if target is None or edit.new_value is None:
            continue

        original_field = fields.get(edit.original_field)
        if original_field is None:
            insert_at = target.line_index + 1
            lines.insert(insert_at, f"{edit.original_field}: {edit.old_value}{line_ending}")

        top_level = _index_top_level_fields(lines)
        target = next((item for item in top_level if item.key == edit.field), None)
        if target is None:
            continue
        lines[target.line_index] = f"{edit.field}: {edit.new_value}{line_ending}"

    new_frontmatter = "".join(lines)
    normalized_new = f"---{new_frontmatter}---{split.body}"
    return decoded.leading_prefix + normalized_new
