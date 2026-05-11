"""Tests for v4.1 Track B single-file MCP write tools (Dev 2).

Covers:
* scaffold_document — create a new markdown file with scaffold frontmatter.
* log_session — create a dated session log under logs_dir.
* session_end — create a structured session-end log under logs_dir.
* promote_document — mutate frontmatter-only curation_level change.
* read_only refusal (m-2 consumer).
* workspace_id validation (m-14 consumer via shared helper).
* Contention inside workspace_lock — a second writer process times out.
* A3 post-commit-failure rebuild path (commit raises → rebuild_workspace
  re-invoked, original exception not masked).

References: addendum v1.2 §A1/§A2/§A3, C.0 findings Q1+Q3, verdict m-2/m-7/m-14/m-15.
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from multiprocessing import Event, Process, Queue
from pathlib import Path
from typing import Any

import pytest
from mcp.types import CallToolResult

from ontos.mcp.portfolio import PortfolioIndex
from tests.mcp import build_cache, build_server, create_workspace, list_tools


# ---------------------------------------------------------------------------
# Fake portfolio index (records invocations so we can assert on A3 recovery).
# ---------------------------------------------------------------------------


class RecordingPortfolioIndex:
    def __init__(self) -> None:
        self.rebuild_calls: list[tuple[str, str]] = []
        self.raise_on_rebuild = False

    def get_projects(self) -> list[dict[str, Any]]:
        return [
            {
                "slug": "workspace",
                "path": "/tmp/workspace",
                "status": "documented",
                "doc_count": 0,
                "last_scanned": "2026-04-11T00:00:00Z",
                "tags": [],
                "has_ontos": 1,
            }
        ]

    def rebuild_workspace(self, slug: str, root: Path) -> None:
        self.rebuild_calls.append((slug, str(root)))
        if self.raise_on_rebuild:
            raise RuntimeError("induced rebuild failure")


def _git_init_clean(root: Path) -> None:
    """Initialise a git repo with a clean tree for write-tool tests."""
    (root / ".gitignore").write_text(".ontos.lock\n", encoding="utf-8")
    subprocess.run(
        ["git", "init", "--initial-branch=main"],
        cwd=str(root),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(root), capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(root), capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
        cwd=str(root), capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "add", "-A"], cwd=str(root), capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(root),
        capture_output=True,
        check=True,
    )


def _build_same_basename_portfolio(tmp_path: Path) -> tuple[Path, Path, PortfolioIndex]:
    left_parent = tmp_path / "left"
    right_parent = tmp_path / "right"
    left_root = create_workspace(left_parent)
    right_root = create_workspace(right_parent)
    _git_init_clean(left_root)
    _git_init_clean(right_root)

    index = PortfolioIndex(tmp_path / "portfolio.db")
    index.rebuild_all(
        scan_roots=[left_parent, right_parent],
        exclude=[],
        registry_path=None,
    )
    return left_root, right_root, index


# ---------------------------------------------------------------------------
# scaffold_document
# ---------------------------------------------------------------------------


def _call(server, name: str, args: dict[str, Any]) -> CallToolResult:
    return asyncio.run(server.call_tool(name, args))


def test_scaffold_document_creates_file_with_scaffold_frontmatter(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(
        server,
        "scaffold_document",
        {"path": "docs/new_feature.md", "content": ""},
    )

    assert result.isError is False, result.content[0].text
    payload = result.structuredContent
    assert payload["success"] is True
    assert payload["path"] == "docs/new_feature.md"
    assert payload["curation_level"] == "L0"

    created = root / "docs" / "new_feature.md"
    assert created.exists()
    text = created.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "status: scaffold" in text
    assert "curation_level: 0" in text


def test_scaffold_document_rejects_existing_path(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    # docs/kernel.md is seeded by create_workspace — collision.
    result = _call(
        server,
        "scaffold_document",
        {"path": "docs/kernel.md"},
    )

    assert result.isError is True
    assert "E_FILE_EXISTS" in result.structuredContent["error"]["error_code"]


def test_scaffold_document_rejects_path_outside_workspace(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(
        server,
        "scaffold_document",
        {"path": "../escape.md"},
    )

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_PATH_OUTSIDE_WORKSPACE"


def test_scaffold_document_rebuild_uses_canonical_slug_under_basename_collision(tmp_path):
    left_root, right_root, index = _build_same_basename_portfolio(tmp_path)

    before_left_ids = {doc["id"] for doc in index.get_workspace_documents("workspace")}
    before_right_ids = {doc["id"] for doc in index.get_workspace_documents("workspace-2")}
    assert index.is_workspace_stale("workspace") is False
    assert index.is_workspace_stale("workspace-2") is False

    server = build_server(right_root, portfolio_index=index)
    result = _call(
        server,
        "scaffold_document",
        {"path": "docs/second_only.md", "content": ""},
    )

    assert result.isError is False, result.content[0].text
    assert (right_root / "docs" / "second_only.md").exists()

    after_left_ids = {doc["id"] for doc in index.get_workspace_documents("workspace")}
    after_right_ids = {doc["id"] for doc in index.get_workspace_documents("workspace-2")}

    assert after_left_ids == before_left_ids
    assert after_right_ids == before_right_ids | {"second_only"}
    assert "second_only" not in after_left_ids
    assert index.is_workspace_stale("workspace") is False
    assert index.is_workspace_stale("workspace-2") is False


# ---------------------------------------------------------------------------
# log_session
# ---------------------------------------------------------------------------


def test_log_session_creates_dated_log_at_logs_dir(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(
        server,
        "log_session",
        {
            "title": "Refactor cache layer",
            "event_type": "refactor",
            "source": "mcp",
            "branch": "feature/cache",
            "body": "Replaced snapshot cache with SnapshotCacheView.",
        },
    )

    assert result.isError is False, result.content[0].text
    payload = result.structuredContent
    assert payload["success"] is True
    # logs_dir defaults to docs/logs per workspace config.
    assert payload["path"].startswith("docs/logs/")
    assert payload["path"].endswith("_refactor-cache-layer.md")
    assert payload["id"].startswith("log_")

    log_file = root / payload["path"]
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "event_type: refactor" in content
    assert "# Refactor cache layer" in content


def test_log_session_rejects_empty_title(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(server, "log_session", {"title": "   "})

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_INVALID_TITLE"


def test_session_end_creates_structured_log(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(
        server,
        "session_end",
        {
            "title": "Agentic Activation Resilience",
            "goal": "Close activation resilience work.",
            "key_decisions": "Use activate first in MCP sessions.",
            "alternatives_considered": "Keep relying on passive instructions.",
            "impacts": "Agents get structured activation state.",
            "testing": "Targeted MCP tests.",
        },
    )

    assert result.isError is False, result.content[0].text
    payload = result.structuredContent
    log_file = root / payload["path"]
    content = log_file.read_text(encoding="utf-8")

    assert payload["success"] is True
    assert payload["path"].startswith("docs/logs/")
    assert "## Goal" in content
    assert "Close activation resilience work." in content
    assert "## Key Decisions" in content
    assert "Use activate first in MCP sessions." in content
    assert "## Alternatives Considered" in content
    assert "## Impacts" in content
    assert "## Testing" in content


def test_session_end_rejects_empty_goal(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(server, "session_end", {"title": "Wrap", "goal": "  "})

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_INVALID_GOAL"


# ---------------------------------------------------------------------------
# promote_document
# ---------------------------------------------------------------------------


def test_promote_document_mutates_curation_level_only(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    # kernel_doc exists in the seeded workspace. Give it curation_level=0.
    kernel_path = root / "docs" / "kernel.md"
    original_body = "Kernel body.\n"
    kernel_path.write_text(
        "---\n"
        "id: kernel_doc\n"
        "type: kernel\n"
        "status: active\n"
        "curation_level: 0\n"
        "---\n\n"
        f"{original_body}",
        encoding="utf-8",
    )
    # Rebuild cache so snapshot sees the new file.
    server = build_server(root)

    result = _call(
        server,
        "promote_document",
        {"document_id": "kernel_doc", "new_level": 2},
    )

    assert result.isError is False, result.content[0].text
    payload = result.structuredContent
    assert payload["success"] is True
    assert payload["document_id"] == "kernel_doc"
    assert payload["old_level"] == "L0"
    assert payload["new_level"] == "L2"

    text = kernel_path.read_text(encoding="utf-8")
    assert "curation_level: 2" in text
    # Body preserved, frontmatter-only mutation.
    assert original_body.strip() in text


def test_promote_document_rejects_unknown_id(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(
        server,
        "promote_document",
        {"document_id": "nonexistent_doc", "new_level": 1},
    )

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_DOCUMENT_NOT_FOUND"


def test_promote_document_rejects_invalid_level(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(
        server,
        "promote_document",
        {"document_id": "kernel_doc", "new_level": 5},
    )

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_INVALID_LEVEL"


# ---------------------------------------------------------------------------
# read_only enforcement (closes m-2)
# ---------------------------------------------------------------------------


def test_read_only_refuses_scaffold_document(tmp_path):
    """Under CB-B2, write tools are NOT REGISTERED when read_only=True — the
    client can no longer invoke them. Invoking raises ``ToolError`` (unknown
    tool). The filesystem must remain untouched.

    See also tests/mcp/test_read_only_registration.py for the
    registration-absence check.
    """
    from mcp.server.fastmcp.exceptions import ToolError

    root = create_workspace(tmp_path)
    server = build_server(root, read_only=True)

    with pytest.raises(ToolError, match="scaffold_document"):
        _call(server, "scaffold_document", {"path": "docs/should_not_exist.md"})
    assert not (root / "docs" / "should_not_exist.md").exists()


def test_read_only_refuses_log_session(tmp_path):
    """Counterpart of test_read_only_refuses_scaffold_document — log_session
    is also unregistered under read_only=True (CB-B2).
    """
    from mcp.server.fastmcp.exceptions import ToolError

    root = create_workspace(tmp_path)
    server = build_server(root, read_only=True)

    with pytest.raises(ToolError, match="log_session"):
        _call(server, "log_session", {"title": "banned write"})


def test_read_only_refuses_session_end(tmp_path):
    from mcp.server.fastmcp.exceptions import ToolError

    root = create_workspace(tmp_path)
    server = build_server(root, read_only=True)

    with pytest.raises(ToolError, match="session_end"):
        _call(server, "session_end", {"title": "banned write", "goal": "No writes."})


def test_read_only_refuses_promote_document(tmp_path):
    """Counterpart — promote_document unregistered under read_only=True (CB-B2)."""
    from mcp.server.fastmcp.exceptions import ToolError

    root = create_workspace(tmp_path)
    server = build_server(root, read_only=True)

    with pytest.raises(ToolError, match="promote_document"):
        _call(server, "promote_document", {"document_id": "kernel_doc", "new_level": 2})


# ---------------------------------------------------------------------------
# workspace_id cross-workspace refusal (m-14 consumer via shared helper)
# ---------------------------------------------------------------------------


def test_write_tool_rejects_cross_workspace_id(tmp_path):
    root = create_workspace(tmp_path)
    server = build_server(root)

    result = _call(
        server,
        "scaffold_document",
        {
            "path": "docs/nope.md",
            "workspace_id": "some-other-workspace",
        },
    )

    assert result.isError is True
    # In non-portfolio mode the shared helper raises E_PORTFOLIO_REQUIRED.
    assert result.structuredContent["error"]["error_code"] == "E_PORTFOLIO_REQUIRED"


def test_write_tool_without_workspace_id_targets_served_workspace_in_portfolio_mode(tmp_path, capsys):
    left_root, right_root, index = _build_same_basename_portfolio(tmp_path)
    capsys.readouterr()
    server = build_server(right_root, portfolio_index=index)

    before_left_ids = {doc["id"] for doc in index.get_workspace_documents("workspace")}
    before_right_ids = {doc["id"] for doc in index.get_workspace_documents("workspace-2")}

    result = _call(
        server,
        "scaffold_document",
        {"path": "docs/current_workspace_only.md", "content": ""},
    )

    assert result.isError is False, result.content[0].text
    assert (right_root / "docs" / "current_workspace_only.md").exists()

    after_left_ids = {doc["id"] for doc in index.get_workspace_documents("workspace")}
    after_right_ids = {doc["id"] for doc in index.get_workspace_documents("workspace-2")}
    captured = capsys.readouterr()
    assert after_left_ids == before_left_ids
    assert after_right_ids == before_right_ids | {"current_workspace_only"}
    assert "current_workspace_only" not in after_left_ids
    assert not (left_root / "docs" / "current_workspace_only.md").exists()
    assert captured.err == ""


def test_write_tool_rejects_unknown_workspace_id_in_portfolio_mode(tmp_path):
    _, right_root, index = _build_same_basename_portfolio(tmp_path)
    server = build_server(right_root, portfolio_index=index)

    result = _call(
        server,
        "scaffold_document",
        {
            "path": "docs/nope.md",
            "workspace_id": "missing-workspace",
        },
    )

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_UNKNOWN_WORKSPACE"


def test_write_tool_rejects_cross_workspace_id_in_portfolio_mode(tmp_path):
    _, right_root, index = _build_same_basename_portfolio(tmp_path)
    server = build_server(right_root, portfolio_index=index)

    result = _call(
        server,
        "scaffold_document",
        {
            "path": "docs/nope.md",
            "workspace_id": "workspace",
        },
    )

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_CROSS_WORKSPACE_NOT_SUPPORTED"


# ---------------------------------------------------------------------------
# A1 — workspace_lock contention inside the write tool.
# ---------------------------------------------------------------------------


def _hold_workspace_lock(workspace: str, ready, release, result: Queue) -> None:
    """Hold workspace_lock() from another process until told to release."""
    from ontos.mcp.locking import workspace_lock

    try:
        with workspace_lock(Path(workspace), timeout=5.0):
            ready.set()
            release.wait(timeout=30.0)
        result.put(("ok", None))
    except BaseException as exc:  # pragma: no cover — surfaced via Queue
        result.put(("error", repr(exc)))


def test_write_tool_under_contention_returns_structured_error(tmp_path):
    """An outer process holds workspace_lock → write tool must fail cleanly.

    The internal ``workspace_lock`` timeout is 5s; the tool surfaces a
    structured ``E_WORKSPACE_BUSY`` error envelope rather than raising.
    """
    root = create_workspace(tmp_path)
    server = build_server(root)

    ready = Event()
    release = Event()
    q: Queue = Queue()
    holder = Process(
        target=_hold_workspace_lock,
        args=(str(root), ready, release, q),
    )
    holder.start()
    try:
        assert ready.wait(timeout=5.0), "holder never signalled ready"

        start = time.monotonic()
        result = _call(
            server,
            "scaffold_document",
            {"path": "docs/contended.md"},
        )
        elapsed = time.monotonic() - start

        assert result.isError is True, result.content[0].text
        # workspace_lock raises OntosUserError(code=E_WORKSPACE_BUSY).
        assert result.structuredContent["error"]["error_code"] == "E_WORKSPACE_BUSY"
        # Confirm the retry window is observed (addendum A1 timeout = 5s).
        assert 4.5 <= elapsed <= 15.0, f"unexpected elapsed={elapsed:.2f}s"

        assert not (root / "docs" / "contended.md").exists()
    finally:
        release.set()
        holder.join(timeout=5.0)
        if holder.is_alive():  # pragma: no cover
            holder.terminate()
            holder.join(timeout=2.0)


# ---------------------------------------------------------------------------
# Py 3.14 catch-inside-lock regression.
# ---------------------------------------------------------------------------


def test_write_tool_preserves_user_error_code_when_raised_inside_lock(monkeypatch, tmp_path):
    from ontos.core.errors import OntosUserError
    from ontos.mcp import writes as write_impl

    root = create_workspace(tmp_path)
    cache = build_cache(root)

    def exploding_impl(**kwargs):
        raise OntosUserError("forced inside lock", code="E_FORCED_INSIDE_LOCK")

    monkeypatch.setattr(write_impl, "_scaffold_document_impl", exploding_impl)

    result = write_impl.scaffold_document(
        cache,
        portfolio_index=None,
        read_only=False,
        path="docs/unused.md",
        content="",
    )

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_FORCED_INSIDE_LOCK"


# ---------------------------------------------------------------------------
# A3 — post-commit-failure rebuild path.
# ---------------------------------------------------------------------------


def test_a3_rebuild_invoked_when_commit_raises(monkeypatch, tmp_path):
    """If commit() raises, the exception path re-invokes rebuild_workspace.

    The rebuild call is best-effort: its failure must NOT mask the
    original commit exception. See addendum v1.2 §A3.
    """
    from ontos.core.context import SessionContext
    from ontos.mcp import writes as write_impl

    root = create_workspace(tmp_path)
    cache = build_cache(root)

    portfolio = RecordingPortfolioIndex()

    real_commit = SessionContext.commit

    def exploding_commit(self):
        # Simulate a mid-commit rename failure AFTER tmp staging.
        raise IOError("induced commit failure")

    monkeypatch.setattr(SessionContext, "commit", exploding_commit)

    result = write_impl.scaffold_document(
        cache,
        portfolio_index=portfolio,
        read_only=False,
        path="docs/should_rebuild.md",
        content="",
    )

    # Restore (not strictly needed under monkeypatch).
    SessionContext.commit = real_commit  # type: ignore[method-assign]

    assert result.isError is True
    # Original commit exception is surfaced — not masked by rebuild.
    assert "induced commit failure" in result.content[0].text
    # A3 recovery ran exactly once (rebuild-on-error path).
    assert len(portfolio.rebuild_calls) == 1
    slug, recorded_root = portfolio.rebuild_calls[0]
    assert slug == "workspace"
    assert Path(recorded_root) == root


def test_a3_rebuild_failure_does_not_mask_original_exception(monkeypatch, tmp_path):
    """A rebuild failure in the exception path is swallowed, not re-raised.

    Mirrors the guard at ``core/context.py:189-199`` — the commit failure
    must propagate as the user-visible error.
    """
    from ontos.core.context import SessionContext
    from ontos.mcp import writes as write_impl

    root = create_workspace(tmp_path)
    cache = build_cache(root)

    portfolio = RecordingPortfolioIndex()
    portfolio.raise_on_rebuild = True

    def exploding_commit(self):
        raise IOError("induced commit failure")

    monkeypatch.setattr(SessionContext, "commit", exploding_commit)

    result = write_impl.scaffold_document(
        cache,
        portfolio_index=portfolio,
        read_only=False,
        path="docs/should_rebuild_fail.md",
        content="",
    )

    assert result.isError is True
    assert "induced commit failure" in result.content[0].text
    assert len(portfolio.rebuild_calls) == 1


def test_a3_single_file_rollback_then_rebuild_reverts_partial_write(monkeypatch, tmp_path):
    """SF-B7: single-file write tools roll back the partial write BEFORE
    rebuilding the portfolio index (addendum A3).

    Synthetic failure scenario: ``SessionContext.commit`` is monkeypatched
    to write a partial payload to the target path and then raise. Pre-SF-B7
    code left that partial file on disk and called rebuild — the DB then
    pointed at content the commit never successfully applied. Post-SF-B7,
    ``rollback_path`` unlinks the untracked partial write (the target is
    new, not in HEAD), and THEN rebuild runs against a reverted filesystem.

    Assertions:
      * The partial write is gone from disk.
      * ``rebuild_workspace`` was invoked exactly once (the recovery path).
      * The original commit exception propagates — rollback/rebuild
        failures must not mask it.

    Regression signal: remove the ``rollback_path`` call from
    ``writes._commit_with_a3_rollback_and_rebuild`` and the
    ``target.exists()`` assertion below flips — the file survives because
    rebuild-only doesn't touch the filesystem.
    """
    import subprocess

    from ontos.core.context import SessionContext
    from ontos.mcp import writes as write_impl

    root = create_workspace(tmp_path)
    # rollback_path uses git; give it a real repo so ``git checkout --`` has
    # somewhere to report "did not match any file" for our new target path.
    _git_init_clean(root)
    cache = build_cache(root)
    portfolio = RecordingPortfolioIndex()
    target = root / "docs" / "partial_commit.md"

    def partially_writing_commit(self):
        target.write_text("partially applied\n", encoding="utf-8")
        raise IOError("induced commit failure after partial write")

    monkeypatch.setattr(SessionContext, "commit", partially_writing_commit)

    result = write_impl.scaffold_document(
        cache,
        portfolio_index=portfolio,
        read_only=False,
        path="docs/partial_commit.md",
        content="",
    )

    assert result.isError is True
    assert "induced commit failure after partial write" in result.content[0].text
    # Rollback deleted the untracked partial write.
    assert not target.exists(), (
        "SF-B7: rollback must unlink untracked partial writes before rebuild"
    )
    # Rebuild ran exactly once — the A3 recovery invocation.
    assert len(portfolio.rebuild_calls) == 1


def test_a3_single_file_rollback_reverts_tracked_path_to_head(monkeypatch, tmp_path):
    """SF-B7 complement: ``promote_document`` mutates an EXISTING file.
    Commit failure must leave the file at its HEAD content, not the partial
    mutation. Covers the tracked-path branch of ``rollback_path``.
    """
    from ontos.core.context import SessionContext
    from ontos.mcp import writes as write_impl

    root = create_workspace(tmp_path)
    _git_init_clean(root)

    # kernel.md is seeded by create_workspace + committed by _git_init_clean.
    kernel = root / "docs" / "kernel.md"
    head_content = kernel.read_text(encoding="utf-8")
    assert "id: kernel_doc" in head_content

    cache = build_cache(root)
    portfolio = RecordingPortfolioIndex()

    def partially_writing_commit(self):
        # Simulate commit writing a corrupted version before raising.
        kernel.write_text("CORRUPTED PARTIAL WRITE\n", encoding="utf-8")
        raise IOError("induced commit failure after partial mutation")

    monkeypatch.setattr(SessionContext, "commit", partially_writing_commit)

    result = write_impl.promote_document(
        cache,
        portfolio_index=portfolio,
        read_only=False,
        document_id="kernel_doc",
        new_level=1,
    )

    assert result.isError is True
    # Rollback restored HEAD content for the tracked file.
    assert kernel.read_text(encoding="utf-8") == head_content, (
        "SF-B7: rollback must ``git checkout --`` tracked paths to HEAD"
    )
    assert len(portfolio.rebuild_calls) == 1


def test_rebuild_is_called_in_happy_path(tmp_path):
    """Happy path also rebuilds the workspace index after commit."""
    from ontos.mcp import writes as write_impl

    root = create_workspace(tmp_path)
    cache = build_cache(root)
    portfolio = RecordingPortfolioIndex()

    result = write_impl.scaffold_document(
        cache,
        portfolio_index=portfolio,
        read_only=False,
        path="docs/new_doc.md",
        content="",
    )

    assert result.isError is False, result.content[0].text
    # Exactly one rebuild in the happy path (from _rebuild_safely).
    assert len(portfolio.rebuild_calls) == 1


# ---------------------------------------------------------------------------
# Shared workspace_id validator lookup (m-8 consolidation).
# ---------------------------------------------------------------------------


def test_shared_validate_workspace_id_helper_exists_and_is_reused():
    """Dev 2 adds ontos.mcp._validation — Dev 3's rename_document must reuse it."""
    import inspect

    from ontos.mcp import _validation
    from ontos.mcp import tools as read_tools
    from ontos.mcp import writes as write_tools

    assert hasattr(_validation, "validate_workspace_id")

    # The legacy tools._validate_workspace_id now delegates to the shared
    # helper so we don't have two implementations to diverge.
    src = inspect.getsource(read_tools._validate_workspace_id)
    assert "_validation" in src or "validate_workspace_id" in src

    # The write tools import the shared helper directly.
    assert _validation.validate_workspace_id is write_tools.validate_workspace_id
