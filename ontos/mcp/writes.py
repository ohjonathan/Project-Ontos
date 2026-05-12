"""Single-file MCP write tools for Ontos v4.1 Track B (Dev 2).

This module implements the three MCP write tools whose mutation surface is
a single markdown file:

* ``scaffold_document`` — create a new ``.md`` in the target workspace.
* ``log_session`` — create ``{logs_dir}/{date}_{slug}.md``.
* ``session_end`` — create a structured session-end log.
* ``promote_document`` — mutate document frontmatter only (no rename,
  no move).

Cross-cutting behavior (addendum v1.2):

* **A1 single-lock discipline.** All three tools wrap the entire mutation
  (``buffer_write`` + ``commit`` + ``rebuild_workspace``) inside
  ``workspace_lock()``. The inner ``SessionContext`` is constructed with
  ``owns_lock=False`` so it does not re-acquire the flock.
* **A2 slugifier binding.** Workspace identity slugs use
  ``ontos.mcp.scanner.slugify``; titles that become filename components
  use ``ontos.commands.log._slugify``. No third slugifier is introduced.
* **A3 post-commit-failure rollback-then-rebuild (SF-B7).** If
  ``ctx.commit()`` raises, the target path is first rolled back via
  ``ontos.core.git.rollback_path`` (which does ``git checkout --`` for
  tracked paths and unlinks untracked partial writes), *then* the
  portfolio index is rebuilt so the DB re-converges with the reverted
  filesystem. Previously this path did rebuild-only, which left the DB
  pointing at file content that had been partially clobbered. Rollback
  and rebuild failures are both recorded via ``ctx.error(...)`` but
  never mask the original commit exception.
* **read_only enforcement.** Every write tool checks the server-level
  ``read_only`` flag and returns a structured
  ``WriteToolErrorEnvelope`` when mutations are disallowed. This closes
  m-2 (``_ = read_only``).
* **workspace_id validation.** Routed through
  ``ontos.mcp._validation.validate_workspace_id`` (closes m-8 / m-14).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sys
import traceback
from typing import Any, Callable, Dict, List, Optional

from mcp.types import CallToolResult, TextContent

from ontos.commands.log import _slugify as slugify_title
from ontos.core.context import SessionContext
from ontos.core.curation import create_scaffold
from ontos.core.errors import OntosInternalError, OntosUserError
from ontos.core.git import rollback_path
from ontos.core.schema import serialize_frontmatter
from ontos.io.yaml import parse_frontmatter_content
from ontos.mcp._validation import resolve_workspace_slug, validate_workspace_id
from ontos.mcp.cache import SnapshotCache
from ontos.mcp.locking import workspace_lock
from ontos.mcp.schemas import (
    ToolErrorTextItem,
    WriteToolError,
    WriteToolErrorEnvelope,
    validate_success_payload,
)


# ---------------------------------------------------------------------------
# Envelope + result helpers.
# ---------------------------------------------------------------------------


def _success_result(tool_name: str, payload: Dict[str, Any]) -> CallToolResult:
    """Validate ``payload`` against the tool schema and wrap it for MCP."""
    import json

    validated = validate_success_payload(tool_name, payload)
    return CallToolResult(
        isError=False,
        structuredContent=validated,
        content=[
            TextContent(
                type="text",
                text=json.dumps(validated, ensure_ascii=True),
            )
        ],
    )


def _write_error_result(
    *,
    error_code: str,
    what: str,
    why: str,
    fix: str,
) -> CallToolResult:
    """Produce a ``WriteToolErrorEnvelope`` shaped ``CallToolResult``."""
    envelope = WriteToolErrorEnvelope(
        isError=True,
        error=WriteToolError(
            error_code=error_code,
            what=what,
            why=why,
            fix=fix,
        ),
        content=[ToolErrorTextItem(type="text", text=what)],
    ).model_dump(mode="json", by_alias=True)
    return CallToolResult(
        isError=True,
        structuredContent=envelope,
        content=[TextContent(type="text", text=what)],
    )


def _user_error_result(exc: OntosUserError) -> CallToolResult:
    """Convert an ``OntosUserError`` into a ``WriteToolErrorEnvelope``."""
    return _write_error_result(
        error_code=getattr(exc, "code", "E_USER_ERROR") or "E_USER_ERROR",
        what=str(exc),
        why=str(exc),
        fix="See error message for remediation guidance.",
    )


# ---------------------------------------------------------------------------
# Shared preflight.
# ---------------------------------------------------------------------------


@dataclass
class _Preflight:
    slug: str
    workspace_root: Path


def _preflight(
    cache: SnapshotCache,
    portfolio_index: Any,
    workspace_id: Optional[str],
    read_only: bool,
) -> _Preflight:
    """Run read_only + workspace_id checks and resolve the target workspace."""
    if read_only:
        raise OntosUserError(
            "Write tools are disabled because the MCP server is running in "
            "read-only mode. Restart without --read-only to enable writes.",
            code="E_READ_ONLY",
        )

    validate_workspace_id(portfolio_index, workspace_id)

    workspace_root = cache.workspace_root
    slug = resolve_workspace_slug(workspace_root, portfolio_index)
    if workspace_id is not None and workspace_id != slug:
        # Write tools mutate the workspace served by this MCP process.
        # Cross-workspace writes are not supported — addendum keeps the
        # behavior symmetric with the read-tool guard at server.py.
        raise OntosUserError(
            "Cross-workspace writes are not supported. "
            "Start a separate `ontos serve` in the target workspace.",
            code="E_CROSS_WORKSPACE_NOT_SUPPORTED",
        )

    return _Preflight(slug=slug, workspace_root=workspace_root)


def _rebuild_safely(
    portfolio_index: Any,
    slug: str,
    workspace_root: Path,
) -> None:
    """Best-effort rebuild. Logs and swallows failures."""
    if portfolio_index is None:
        return
    try:
        portfolio_index.rebuild_workspace(slug, workspace_root)
    except Exception:
        traceback.print_exc(file=sys.stderr)


def _commit_with_a3_rollback_and_rebuild(
    ctx: SessionContext,
    portfolio_index: Any,
    slug: str,
    workspace_root: Path,
    target_path: Path,
) -> List[Path]:
    """Commit, or rollback-then-rebuild on failure (addendum v1.2 §A3, SF-B7).

    On ``ctx.commit()`` exception:
      1. Roll back the ``target_path`` — ``git checkout --`` for tracked
         paths, ``unlink`` for untracked partial writes. Scoped rollback
         avoids clobbering unrelated dirty state in the worktree.
      2. Call ``rebuild_workspace(slug, root)`` so the portfolio DB
         re-converges with the reverted filesystem.
      3. Re-raise the original commit exception.

    Rollback and rebuild failures are both recorded via ``ctx.error(...)``
    but never mask the original exception.

    Mirrors the pattern at ``rename_tool.py::_commit_with_a3_rollback_and_rebuild``
    but uses scoped rollback because single-file write tools do NOT require
    a clean-worktree precondition, so whole-workspace ``git checkout -- .``
    would be destructive to unrelated uncommitted state.
    """
    try:
        return ctx.commit()
    except Exception:
        reason = rollback_path(workspace_root, target_path)
        if reason is not None:
            ctx.error(f"Post-commit rollback failed: {reason}")
        _rebuild_safely(portfolio_index, slug, workspace_root)
        raise


# ---------------------------------------------------------------------------
# Tool entry points.
# ---------------------------------------------------------------------------


def scaffold_document(
    cache: SnapshotCache,
    *,
    portfolio_index: Any = None,
    read_only: bool = False,
    path: str,
    content: str = "",
    workspace_id: Optional[str] = None,
) -> CallToolResult:
    """Create a new ``.md`` file with a Level-0 scaffold frontmatter."""
    return _dispatch(
        "scaffold_document",
        _scaffold_document_impl,
        cache=cache,
        portfolio_index=portfolio_index,
        read_only=read_only,
        workspace_id=workspace_id,
        path=path,
        content=content,
    )


def log_session(
    cache: SnapshotCache,
    *,
    portfolio_index: Any = None,
    read_only: bool = False,
    title: str,
    event_type: str = "chore",
    source: str = "mcp",
    branch: str = "unknown",
    body: str = "",
    workspace_id: Optional[str] = None,
) -> CallToolResult:
    """Create a session log at ``{logs_dir}/{date}_{slug}.md``."""
    return _dispatch(
        "log_session",
        _log_session_impl,
        cache=cache,
        portfolio_index=portfolio_index,
        read_only=read_only,
        workspace_id=workspace_id,
        title=title,
        event_type=event_type,
        source=source,
        branch=branch,
        body=body,
    )


def session_end(
    cache: SnapshotCache,
    *,
    portfolio_index: Any = None,
    read_only: bool = False,
    title: str,
    goal: str,
    key_decisions: str = "",
    alternatives_considered: str = "",
    impacts: str = "",
    testing: str = "",
    source: str = "mcp",
    branch: str = "unknown",
    workspace_id: Optional[str] = None,
) -> CallToolResult:
    """Create a structured session-end log."""
    return _dispatch(
        "session_end",
        _session_end_impl,
        cache=cache,
        portfolio_index=portfolio_index,
        read_only=read_only,
        workspace_id=workspace_id,
        title=title,
        goal=goal,
        key_decisions=key_decisions,
        alternatives_considered=alternatives_considered,
        impacts=impacts,
        testing=testing,
        source=source,
        branch=branch,
    )


def promote_document(
    cache: SnapshotCache,
    *,
    portfolio_index: Any = None,
    read_only: bool = False,
    document_id: str,
    new_level: int,
    workspace_id: Optional[str] = None,
) -> CallToolResult:
    """Mutate frontmatter to change ``curation_level`` (no rename/move)."""
    return _dispatch(
        "promote_document",
        _promote_document_impl,
        cache=cache,
        portfolio_index=portfolio_index,
        read_only=read_only,
        workspace_id=workspace_id,
        document_id=document_id,
        new_level=new_level,
    )


def _dispatch(
    tool_name: str,
    impl: Callable[..., Dict[str, Any]],
    *,
    cache: SnapshotCache,
    portfolio_index: Any,
    read_only: bool,
    workspace_id: Optional[str],
    **kwargs: Any,
) -> CallToolResult:
    # Preflight runs outside the workspace lock — no file state is
    # mutated yet, and read_only / workspace_id errors should not pay
    # the lock acquisition cost.
    try:
        plan = _preflight(cache, portfolio_index, workspace_id, read_only)
    except OntosUserError as exc:
        return _user_error_result(exc)

    # NOTE on exception flow:
    # OntosUserError / OntosInternalError are frozen dataclasses, which on
    # Python 3.14+ can't have ``__traceback__`` reassigned by the stdlib
    # contextlib machinery. Catching them INSIDE the lock prevents
    # ``workspace_lock()`` from re-raising and tripping that assignment.
    # See https://github.com/python/cpython (contextmanager __exit__).
    result: Optional[CallToolResult] = None
    try:
        with workspace_lock(plan.workspace_root):
            try:
                payload = impl(
                    cache=cache,
                    portfolio_index=portfolio_index,
                    plan=plan,
                    **kwargs,
                )
                result = _success_result(tool_name, payload)
            except OntosUserError as exc:
                result = _user_error_result(exc)
            except OntosInternalError as exc:
                print(f"[ontos-mcp] {exc.code}: {exc}", file=sys.stderr)
                if exc.details:
                    print(exc.details, file=sys.stderr)
                result = _write_error_result(
                    error_code=exc.code or "E_INTERNAL",
                    what=f"Internal error: {exc}",
                    why="The server encountered an unexpected error.",
                    fix="Check server logs and retry.",
                )
            except Exception as exc:
                traceback.print_exc(file=sys.stderr)
                result = _write_error_result(
                    error_code="E_INTERNAL",
                    what=f"Internal error in {tool_name}: {exc}",
                    why="Unexpected exception while executing the write tool.",
                    fix="Check server logs and retry.",
                )
    except OntosUserError as exc:
        # Raised by workspace_lock itself (E_WORKSPACE_BUSY) when the
        # flock timeout is exceeded.
        return _user_error_result(exc)

    assert result is not None  # for type-checkers
    return result


# ---------------------------------------------------------------------------
# scaffold_document implementation.
# ---------------------------------------------------------------------------


def _scaffold_document_impl(
    *,
    cache: SnapshotCache,
    portfolio_index: Any,
    plan: _Preflight,
    path: str,
    content: str,
) -> Dict[str, Any]:
    if not path or not str(path).strip():
        raise OntosUserError(
            "path must be non-empty.",
            code="E_INVALID_PATH",
        )

    resolved = _resolve_inside_workspace(plan.workspace_root, path)
    if resolved.suffix != ".md":
        raise OntosUserError(
            "scaffold_document only accepts .md targets.",
            code="E_INVALID_PATH",
        )
    if resolved.exists():
        raise OntosUserError(
            f"File already exists: {resolved.relative_to(plan.workspace_root).as_posix()}",
            code="E_FILE_EXISTS",
        )

    # Assemble scaffold frontmatter. ``create_scaffold`` handles ID/type
    # inference from path + body content.
    frontmatter = create_scaffold(resolved, content=content)
    body = content if content else f"# {frontmatter['id']}\n\nTODO: expand this scaffold.\n"
    document = f"---\n{serialize_frontmatter(frontmatter)}\n---\n\n{body}"
    if not document.endswith("\n"):
        document += "\n"

    ctx = SessionContext(
        repo_root=plan.workspace_root,
        config={},
        owns_lock=False,
    )
    ctx.buffer_write(resolved, document)
    _commit_with_a3_rollback_and_rebuild(
        ctx, portfolio_index, plan.slug, plan.workspace_root, resolved
    )
    _rebuild_safely(portfolio_index, plan.slug, plan.workspace_root)

    return {
        "success": True,
        "path": resolved.relative_to(plan.workspace_root).as_posix(),
        "id": str(frontmatter["id"]),
        "type": str(frontmatter["type"]),
        "status": str(frontmatter["status"]),
        "curation_level": f"L{int(frontmatter['curation_level'])}",
    }


# ---------------------------------------------------------------------------
# log_session implementation.
# ---------------------------------------------------------------------------


def _log_session_impl(
    *,
    cache: SnapshotCache,
    portfolio_index: Any,
    plan: _Preflight,
    title: str,
    event_type: str,
    source: str,
    branch: str,
    body: str,
) -> Dict[str, Any]:
    if not title or not str(title).strip():
        raise OntosUserError(
            "title must be non-empty.",
            code="E_INVALID_TITLE",
        )

    title_slug = slugify_title(str(title))  # addendum A2 — title slugifier
    date_str = datetime.now().strftime("%Y-%m-%d")
    logs_dir_raw = cache.config.paths.logs_dir or "docs/logs"
    logs_dir = Path(logs_dir_raw)
    if not logs_dir.is_absolute():
        logs_dir = plan.workspace_root / logs_dir

    filename = f"{date_str}_{title_slug}.md"
    target = (logs_dir / filename).resolve(strict=False)
    if not target.is_relative_to(plan.workspace_root.resolve()):
        raise OntosUserError(
            "Resolved log path escapes the workspace root.",
            code="E_PATH_OUTSIDE_WORKSPACE",
        )
    if target.exists():
        raise OntosUserError(
            f"Log already exists: {target.relative_to(plan.workspace_root).as_posix()}",
            code="E_FILE_EXISTS",
        )

    log_id = f"log_{date_str.replace('-', '')}_{title_slug}"
    frontmatter = {
        "id": log_id,
        "type": "log",
        "status": "active",
        "event_type": event_type,
        "source": source,
        "branch": branch,
        "created": date_str,
    }
    heading = str(title).strip()
    document = (
        f"---\n{serialize_frontmatter(frontmatter)}\n---\n\n"
        f"# {heading}\n\n"
    )
    if body.strip():
        document += f"{body.rstrip()}\n"

    ctx = SessionContext(
        repo_root=plan.workspace_root,
        config={},
        owns_lock=False,
    )
    ctx.buffer_write(target, document)
    _commit_with_a3_rollback_and_rebuild(
        ctx, portfolio_index, plan.slug, plan.workspace_root, target
    )
    _rebuild_safely(portfolio_index, plan.slug, plan.workspace_root)

    return {
        "success": True,
        "path": target.relative_to(plan.workspace_root).as_posix(),
        "id": log_id,
        "date": date_str,
    }


def _session_end_impl(
    *,
    cache: SnapshotCache,
    portfolio_index: Any,
    plan: _Preflight,
    title: str,
    goal: str,
    key_decisions: str,
    alternatives_considered: str,
    impacts: str,
    testing: str,
    source: str,
    branch: str,
) -> Dict[str, Any]:
    """Build the typed session-end body and delegate to log_session."""
    if not goal or not str(goal).strip():
        raise OntosUserError(
            "goal must be non-empty.",
            code="E_INVALID_GOAL",
        )

    body = "\n\n".join(
        [
            "## Goal\n\n" + str(goal).strip(),
            "## Key Decisions\n\n" + _session_end_section(key_decisions, "None recorded."),
            (
                "## Alternatives Considered\n\n"
                + _session_end_section(alternatives_considered, "None recorded.")
            ),
            "## Impacts\n\n" + _session_end_section(impacts, "None recorded."),
            "## Testing\n\n" + _session_end_section(testing, "Not run."),
        ]
    )
    return _log_session_impl(
        cache=cache,
        portfolio_index=portfolio_index,
        plan=plan,
        title=title,
        event_type="chore",
        source=source,
        branch=branch,
        body=body,
    )


def _session_end_section(value: str, fallback: str) -> str:
    text = str(value).strip()
    return text if text else fallback


# ---------------------------------------------------------------------------
# promote_document implementation.
# ---------------------------------------------------------------------------


def _promote_document_impl(
    *,
    cache: SnapshotCache,
    portfolio_index: Any,
    plan: _Preflight,
    document_id: str,
    new_level: int,
) -> Dict[str, Any]:
    if not document_id or not str(document_id).strip():
        raise OntosUserError(
            "document_id must be non-empty.",
            code="E_INVALID_DOCUMENT_ID",
        )
    if new_level not in (0, 1, 2):
        raise OntosUserError(
            "new_level must be 0, 1, or 2.",
            code="E_INVALID_LEVEL",
        )

    snapshot = cache.get_fresh_snapshot()
    doc = snapshot.documents.get(document_id)
    if doc is None:
        raise OntosUserError(
            f"Document not found: {document_id}",
            code="E_DOCUMENT_NOT_FOUND",
        )

    target = Path(doc.filepath)
    original = target.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter_content(original)
    if not frontmatter:
        raise OntosUserError(
            f"Document {document_id} has no frontmatter to mutate.",
            code="E_MISSING_FRONTMATTER",
        )

    old_level_raw = frontmatter.get("curation_level", 0)
    try:
        old_level = int(old_level_raw)
    except (TypeError, ValueError):
        old_level = 0

    frontmatter["curation_level"] = int(new_level)
    document = f"---\n{serialize_frontmatter(frontmatter)}\n---\n\n{body}"
    if not document.endswith("\n"):
        document += "\n"

    ctx = SessionContext(
        repo_root=plan.workspace_root,
        config={},
        owns_lock=False,
    )
    ctx.buffer_write(target, document)
    _commit_with_a3_rollback_and_rebuild(
        ctx, portfolio_index, plan.slug, plan.workspace_root, target
    )
    _rebuild_safely(portfolio_index, plan.slug, plan.workspace_root)

    return {
        "success": True,
        "document_id": document_id,
        "old_level": f"L{old_level}",
        "new_level": f"L{int(new_level)}",
    }


# ---------------------------------------------------------------------------
# Utilities.
# ---------------------------------------------------------------------------


def _resolve_inside_workspace(workspace_root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if str(raw_path).startswith("~"):
        candidate = candidate.expanduser()
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    resolved = candidate.resolve(strict=False)
    ws_resolved = workspace_root.resolve()
    if not resolved.is_relative_to(ws_resolved):
        raise OntosUserError(
            "Path must resolve inside the workspace root.",
            code="E_PATH_OUTSIDE_WORKSPACE",
        )
    return resolved
