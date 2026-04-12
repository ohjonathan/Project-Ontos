"""Multi-file MCP ``rename_document`` tool for Ontos v4.1 Track B (Dev 3).

This module implements the one Track B write tool whose mutation surface
spans N files: renaming a document ID updates every referencing file in
the workspace. It sits next to the single-file tools in
``ontos.mcp.writes`` and reuses the same substrate (workspace_lock + A1
``owns_lock=False`` pattern, shared ``validate_workspace_id``, shared
``WriteToolErrorEnvelope`` shapes) but keeps the multi-file control flow
separate so Dev 2's single-file surface is untouched.

A6 semantics — verified (TrackB-Design §9, v1.1 §4.8.2):
    ``ontos/commands/rename.py:221`` writes new content with
    ``ctx.buffer_write(path, new_content)`` — no ``os.rename`` / no
    ``buffer_move``. The MCP tool matches exactly: "rename" edits file
    content in place and rewrites references via
    ``scan_body_references``; filenames are NOT changed.

A3 post-rollback rebuild (addendum v1.2 §A3):
    If ``ctx.commit()`` raises, the DB may be out of sync with the
    filesystem. This tool performs ``git checkout -- .`` to revert
    uncommitted writes (the git clean-state precondition guarantees this
    is safe), then re-invokes ``rebuild_workspace(slug, root)`` so the
    index re-converges with the reverted files. Rebuild failures are
    recorded via ``ctx.error(...)`` but never mask the original commit
    exception.

m-13 — FTS5 parity recoverable rebuild:
    The parity check in ``portfolio.py:410-422`` raises after
    ``conn.commit()`` has already mutated the DB. Because
    ``rebuild_workspace`` starts with a ``DELETE FROM documents`` it is
    idempotent; a single retry re-converges on success. This module
    retries once on parity-mismatch ``RuntimeError`` before surfacing
    failure. See PR description for rationale.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import traceback
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult, TextContent

from ontos.commands.rename import (
    RenameError,
    build_rename_plan,
)
from ontos.core.context import SessionContext
from ontos.core.errors import OntosInternalError, OntosUserError
from ontos.core.git import is_workspace_clean
from ontos.io.config import load_project_config
from ontos.io.scan_scope import resolve_scan_scope
from ontos.mcp._validation import validate_workspace_id
from ontos.mcp.cache import SnapshotCache
from ontos.mcp.locking import workspace_lock
from ontos.mcp.scanner import slugify as slugify_workspace_identity
from ontos.mcp.schemas import (
    ToolErrorTextItem,
    WriteToolError,
    WriteToolErrorEnvelope,
    validate_success_payload,
)


# Mapping from shared-orchestrator ``RenameError.code`` to the MCP
# write-tool error taxonomy. The orchestrator is source-of-truth for
# validation + collision logic; this helper preserves the stable MCP
# envelope codes the existing tests assert.
_RENAME_ERROR_TO_USER_CODE: Dict[str, str] = {
    "invalid_new_id": "E_INVALID_ID",
    "reserved_new_id": "E_INVALID_ID",
    "old_id_not_found": "E_DOCUMENT_NOT_FOUND",
    "new_id_exists": "E_DUPLICATE_ID",
    "cross_scope_collision": "E_CROSS_SCOPE_COLLISION",
    "duplicate_ids": "E_DUPLICATE_ID",
    "parse_failed_target_sighting": "E_UNSUPPORTED_TARGET_FORMAT",
    "config_error": "E_CONFIG_ERROR",
    "dirty_git_state": "E_DIRTY_WORKSPACE",
    "project_root_not_found": "E_PROJECT_ROOT_NOT_FOUND",
}


def _rename_error_to_user_exc(error: RenameError) -> OntosUserError:
    """Translate a shared ``RenameError`` into an ``OntosUserError``.

    Unknown codes fall back to ``E_USER_INPUT`` (the ``OntosUserError``
    default) so new orchestrator codes surface as user errors by default
    rather than crashing the MCP dispatcher.
    """
    return OntosUserError(
        error.message,
        code=_RENAME_ERROR_TO_USER_CODE.get(error.code, "E_USER_INPUT"),
    )


# ---------------------------------------------------------------------------
# Envelope helpers (mirror Dev 2's writes.py so error shapes stay uniform).
# ---------------------------------------------------------------------------


def _success_result(tool_name: str, payload: Dict[str, Any]) -> CallToolResult:
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
    return _write_error_result(
        error_code=getattr(exc, "code", "E_USER_ERROR") or "E_USER_ERROR",
        what=str(exc),
        why=str(exc),
        fix="See error message for remediation guidance.",
    )


# ---------------------------------------------------------------------------
# Preflight + A3/m-13 helpers.
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
    if read_only:
        raise OntosUserError(
            "Write tools are disabled because the MCP server is running in "
            "read-only mode. Restart without --read-only to enable writes.",
            code="E_READ_ONLY",
        )

    # Shared helper — closes m-8 by reusing Dev 2's single guard.
    validate_workspace_id(portfolio_index, workspace_id)

    workspace_root = cache.workspace_root
    slug = slugify_workspace_identity(workspace_root.name)
    if workspace_id is not None and workspace_id != slug:
        raise OntosUserError(
            "Cross-workspace writes are not supported. "
            "Start a separate `ontos serve` in the target workspace.",
            code="E_CROSS_WORKSPACE_NOT_SUPPORTED",
        )

    # Git clean-state precondition (§4.8.2 Step 4).
    #
    # This runs BEFORE ``workspace_lock()`` because the lock context
    # materialises ``.ontos.lock`` as an untracked file; checking dirty
    # state after the lock is held would always see at least that file
    # and trigger false-positive E_DIRTY_WORKSPACE for any caller that
    # hasn't added ``.ontos.lock`` to ``.gitignore``. Untracked files
    # elsewhere also count as dirty: the recovery action is ``git
    # checkout -- .``, which only restores tracked files, so untracked
    # state we'd write during the tool run would linger after rollback.
    clean, reason = is_workspace_clean(workspace_root)
    if not clean:
        raise OntosUserError(
            "Workspace has uncommitted changes. "
            "Commit or stash before renaming so you can recover with "
            "`git checkout -- .` if needed. "
            f"(Reason: {reason})",
            code="E_DIRTY_WORKSPACE",
        )

    return _Preflight(slug=slug, workspace_root=workspace_root)


def _rebuild_with_m13_retry(
    portfolio_index: Any,
    slug: str,
    workspace_root: Path,
    *,
    ctx: Optional[SessionContext] = None,
) -> None:
    """Best-effort rebuild that retries once on FTS5 parity mismatch.

    Because ``rebuild_workspace`` begins with a ``DELETE FROM documents``,
    it is fully idempotent: a second invocation re-converges. The retry
    only runs for parity-mismatch ``RuntimeError``s raised by the
    post-commit check at ``portfolio.py:410-422``. Other exceptions are
    re-raised so they don't get silently swallowed.
    """
    if portfolio_index is None:
        return

    try:
        portfolio_index.rebuild_workspace(slug, workspace_root)
    except RuntimeError as exc:
        if "FTS parity mismatch" not in str(exc):
            raise
        # m-13: retry once. If the second pass also fails, surface it.
        try:
            portfolio_index.rebuild_workspace(slug, workspace_root)
        except Exception as retry_exc:
            if ctx is not None:
                ctx.error(
                    f"Portfolio rebuild failed after retry: {retry_exc}"
                )
            raise


def _rebuild_safely(
    portfolio_index: Any,
    slug: str,
    workspace_root: Path,
    *,
    ctx: Optional[SessionContext] = None,
) -> None:
    """Same contract as Dev 2's ``_rebuild_safely``: swallow + log."""
    if portfolio_index is None:
        return
    try:
        _rebuild_with_m13_retry(
            portfolio_index, slug, workspace_root, ctx=ctx
        )
    except Exception:
        traceback.print_exc(file=sys.stderr)


def _git_checkout_rollback(root: Path) -> Optional[str]:
    """Revert all uncommitted changes via ``git checkout -- .``.

    Returns ``None`` on success or a reason string on failure.
    """
    try:
        result = subprocess.run(
            ["git", "checkout", "--", "."],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10.0,
            check=False,
        )
    except FileNotFoundError:
        return "git executable not found on PATH"
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Unable to run git checkout: {exc}"
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        return stderr or "git checkout failed"
    return None


def _commit_with_a3_rollback_and_rebuild(
    ctx: SessionContext,
    portfolio_index: Any,
    slug: str,
    workspace_root: Path,
) -> List[Path]:
    """Commit, or rollback + rebuild on failure (addendum v1.2 §A3).

    This is the multi-file mainline: the git clean-state precondition
    guarantees ``git checkout -- .`` is a safe recovery action. After
    reverting, we re-invoke ``rebuild_workspace`` so the portfolio DB
    re-converges with the reverted filesystem state.
    """
    try:
        return ctx.commit()
    except Exception:
        # Rollback the working tree. The precondition (clean at entry)
        # means "revert to HEAD" restores the pre-mutation state.
        reason = _git_checkout_rollback(workspace_root)
        if reason is not None:
            ctx.error(f"Post-commit rollback failed: {reason}")
        # Now reconcile the DB with the reverted filesystem.
        _rebuild_safely(portfolio_index, slug, workspace_root, ctx=ctx)
        raise


# ---------------------------------------------------------------------------
# Public entry point.
# ---------------------------------------------------------------------------


def rename_document(
    cache: SnapshotCache,
    *,
    portfolio_index: Any = None,
    read_only: bool = False,
    document_id: str,
    new_id: str,
    workspace_id: Optional[str] = None,
) -> CallToolResult:
    """Rename a document ID and rewrite all references across the workspace.

    Matches ``ontos/commands/rename.py:221`` semantics — ID-only rename,
    no filesystem moves, all edits flow through ``ctx.buffer_write``.
    """
    try:
        plan = _preflight(cache, portfolio_index, workspace_id, read_only)
    except OntosUserError as exc:
        return _user_error_result(exc)

    # Result holder so we can shape error returns outside the lock while
    # keeping OntosUserError/OntosInternalError caught INSIDE the lock
    # (Python 3.14 frozen-dataclass __traceback__ gotcha documented in
    # writes.py dispatcher comments).
    result: Optional[CallToolResult] = None
    try:
        with workspace_lock(plan.workspace_root):
            try:
                payload = _rename_document_impl(
                    cache=cache,
                    portfolio_index=portfolio_index,
                    plan=plan,
                    document_id=document_id,
                    new_id=new_id,
                )
                result = _success_result("rename_document", payload)
            except OntosUserError as exc:
                result = _user_error_result(exc)
            except OntosInternalError as exc:
                print(
                    f"[ontos-mcp] {exc.code}: {exc}", file=sys.stderr
                )
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
                    what=f"Internal error in rename_document: {exc}",
                    why="Unexpected exception while executing the write tool.",
                    fix="Check server logs and retry.",
                )
    except OntosUserError as exc:
        # workspace_lock E_WORKSPACE_BUSY escapes as documented.
        return _user_error_result(exc)

    assert result is not None  # for type-checkers
    return result


# ---------------------------------------------------------------------------
# Implementation.
# ---------------------------------------------------------------------------


def _rename_document_impl(
    *,
    cache: SnapshotCache,
    portfolio_index: Any,
    plan: _Preflight,
    document_id: str,
    new_id: str,
) -> Dict[str, Any]:
    old_id = str(document_id).strip() if document_id is not None else ""
    target_id = str(new_id).strip() if new_id is not None else ""

    if not old_id:
        raise OntosUserError(
            "document_id must be non-empty.",
            code="E_INVALID_DOCUMENT_ID",
        )
    if not target_id:
        raise OntosUserError(
            "new_id must be non-empty.",
            code="E_INVALID_ID",
        )

    # Route through the shared orchestrator. It performs ID validation,
    # old/new collision checks, the docs-scope cross-scope guard, and the
    # sorted per-file plan loop. The CLI and MCP now share this single
    # plan-builder — closing the CB-6-style divergence risk where each
    # call site had its own hand-rolled orchestration loop.
    snapshot = cache.get_fresh_snapshot()
    try:
        config = load_project_config(repo_root=plan.workspace_root)
    except Exception as exc:  # pragma: no cover - config failure path
        raise OntosUserError(
            f"Config error: {exc}",
            code="E_CONFIG_ERROR",
        )
    # Use the same scope resolution the snapshot cache used, so the docs
    # dict and the scope parameter stay consistent. This keeps MCP's
    # pre-refactor behaviour (whatever scope the snapshot was built with)
    # while gaining the docs-scope cross-scope collision check whenever
    # the effective scope is DOCS.
    scope = resolve_scan_scope(None, config.scanning.default_scope)

    rename_plan, error = build_rename_plan(
        repo_root=plan.workspace_root,
        config=config,
        scope=scope,
        docs=snapshot.documents,
        load_issues=None,
        old_id=old_id,
        new_id=target_id,
        mode="apply",
        # Git clean-state was already enforced by ``_preflight`` before
        # we acquired ``workspace_lock()``. Re-checking here would
        # false-positive because ``.ontos.lock`` is now an untracked file.
        check_git=False,
    )
    if error is not None:
        raise _rename_error_to_user_exc(error)
    assert rename_plan is not None

    # No-op rename: report success without touching files or acquiring any
    # further write-side state.
    if rename_plan.no_op:
        doc = snapshot.documents.get(old_id)
        rel = (
            _rel_to_workspace(plan.workspace_root, Path(doc.filepath))
            if doc is not None
            else ""
        )
        return {
            "success": True,
            "old_id": old_id,
            "new_id": target_id,
            "path": rel,
            "references_updated": 0,
            "updated_files": [],
        }

    target_doc = snapshot.documents[old_id]
    target_rel = _rel_to_workspace(plan.workspace_root, Path(target_doc.filepath))

    # Blocking-warning gate (unsupported frontmatter formats). Mirrors the
    # CLI's ``plan.blocking_warnings()`` check.
    blocking = rename_plan.blocking_warnings()
    if blocking:
        first = blocking[0]
        raise OntosUserError(
            "Rename plan contains unsupported frontmatter formats. "
            f"First blocker: {first.path} — {first.reason_message}",
            code="E_UNSUPPORTED_TARGET_FORMAT",
        )

    files_to_apply = [fp for fp in rename_plan.files if fp.has_changes]
    if not files_to_apply:
        # Target exists but no references anywhere — treat as a no-op.
        return {
            "success": True,
            "old_id": old_id,
            "new_id": target_id,
            "path": target_rel,
            "references_updated": 0,
            "updated_files": [],
        }

    # Count body edits that actually rewrite (matches CLI summary).
    references_updated = 0
    for fp in files_to_apply:
        references_updated += len(fp.frontmatter_edits)
        references_updated += sum(1 for edit in fp.body_edits if edit.rewritable)

    ctx = SessionContext(
        repo_root=plan.workspace_root,
        config={},
        owns_lock=False,  # addendum v1.2 §A1
    )
    for fp in files_to_apply:
        ctx.buffer_write(fp.path, fp.new_content)

    # Commit + A3 rollback+rebuild path. On failure we re-raise so the
    # outer dispatcher turns it into a WriteToolErrorEnvelope.
    modified_paths = _commit_with_a3_rollback_and_rebuild(
        ctx, portfolio_index, plan.slug, plan.workspace_root
    )

    # Verify planned vs actual commit set (matches rename.py guard).
    planned = {p.path.resolve() for p in files_to_apply}
    committed = {p.resolve() for p in modified_paths}
    if planned != committed:
        # Best-effort rollback — git checkout even here, then rebuild.
        rollback_reason = _git_checkout_rollback(plan.workspace_root)
        if rollback_reason is not None:
            ctx.error(f"Partial-commit rollback failed: {rollback_reason}")
        _rebuild_safely(
            portfolio_index, plan.slug, plan.workspace_root, ctx=ctx
        )
        raise OntosInternalError(
            "Commit result does not match planned file set. "
            "Repository has been rolled back via `git checkout -- .`.",
            code="E_PARTIAL_COMMIT_MISMATCH",
        )

    # Happy-path post-commit rebuild with m-13 retry.
    _rebuild_safely(
        portfolio_index, plan.slug, plan.workspace_root, ctx=ctx
    )

    updated_files = sorted(
        _rel_to_workspace(plan.workspace_root, p) for p in committed
    )
    return {
        "success": True,
        "old_id": old_id,
        "new_id": target_id,
        "path": target_rel,
        "references_updated": references_updated,
        "updated_files": updated_files,
    }


def _rel_to_workspace(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


# Public symbol used by tests that assert the shared helper binding.
# (Mirrors writes.py's re-export of validate_workspace_id.)
__all__ = ["rename_document", "validate_workspace_id"]
