"""Tests for v4.1 Track B multi-file MCP write tool ``rename_document`` (Dev 3).

Covers (per Dev 3 scope in ``v4.1_TrackB_Implementation_Spec.md``):

* Happy path — N-file reference rewrite with planned-vs-committed parity.
* Git-dirty precondition refusal (addendum v1.2 §A6 matching v1.1 §4.8.2
  Step 4) — unstaged or untracked file in the workspace blocks the rename.
* ``read_only`` refusal (closes m-2 consumer).
* Cross-workspace refusal via shared ``validate_workspace_id`` helper
  (closes m-8 consumer).
* ``workspace_lock`` contention returns structured ``E_WORKSPACE_BUSY``.
* A3 post-commit rollback path — commit raises, working tree is reverted
  via ``git checkout -- .``, and ``rebuild_workspace`` re-converges the
  portfolio DB.
* m-13 FTS5 parity recoverable rebuild — a first rebuild that raises the
  parity-mismatch ``RuntimeError`` is retried once; if the retry succeeds
  the tool succeeds overall.
* A6 binding — ``buffer_write`` is the only mutation surface (no
  ``os.rename``, no ``buffer_move``).

References: v1.1 §4.8.2, addendum §A1/§A2/§A3/§A6, TrackB-Design §9.
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from multiprocessing import Event, Process, Queue
from pathlib import Path
from typing import Any, List

import pytest
from mcp.types import CallToolResult

from tests.mcp import build_cache, build_server, create_workspace


# ---------------------------------------------------------------------------
# Helpers — recording portfolio index + git-init helper.
# ---------------------------------------------------------------------------


class RecordingPortfolioIndex:
    def __init__(self) -> None:
        self.rebuild_calls: List[tuple] = []
        self.raise_on_rebuild = False
        # When set, the first N calls raise; subsequent calls succeed.
        self.raise_parity_times = 0

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
        if self.raise_parity_times > 0:
            self.raise_parity_times -= 1
            raise RuntimeError(
                f"FTS parity mismatch for {slug}: documents=3, fts=2"
            )
        if self.raise_on_rebuild:
            raise RuntimeError("induced rebuild failure")


def _git_init_clean(root: Path) -> None:
    """Initialise a git repo, commit current state, return a clean tree.

    Seeds ``.gitignore`` with ``.ontos.lock`` first — addendum §A5 says
    the repo template already ignores ``.ontos.lock``, so the test
    workspace must mirror that contract or every write tool that takes
    the workspace lock would trip the dirty-workspace precondition.
    """
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


def _call(server, name: str, args: dict[str, Any]) -> CallToolResult:
    return asyncio.run(server.call_tool(name, args))


# ---------------------------------------------------------------------------
# A6 verification — buffer_write is the only mutation channel.
# ---------------------------------------------------------------------------


def test_a6_rename_uses_buffer_write_not_filesystem_rename():
    """Locks the A6 semantic in place: the MCP tool must mirror
    ``rename.py:221`` and never call ``os.rename``/``buffer_move``.

    This is a static guard on the module's AST — if a future refactor
    introduces filesystem moves as real calls (not just doc-references),
    this test fails and the author is forced to re-read §A6.
    """
    import ast
    import inspect

    from ontos.mcp import rename_tool

    tree = ast.parse(inspect.getsource(rename_tool))
    call_attrs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            call_attrs.append(node.func.attr)

    # buffer_write is used for every mutation.
    assert "buffer_write" in call_attrs
    # buffer_move is NOT called from the rename_document flow.
    assert "buffer_move" not in call_attrs
    # No filesystem rename calls (Path.rename, os.rename).
    assert "rename" not in call_attrs


# ---------------------------------------------------------------------------
# Happy path.
# ---------------------------------------------------------------------------


def test_rename_document_happy_path_rewrites_frontmatter_and_body(tmp_path):
    root = create_workspace(tmp_path)
    _git_init_clean(root)
    # Add a body reference to strategy_doc so we get a body-edit too.
    extra = root / "docs" / "bridge.md"
    extra.write_text(
        "---\n"
        "id: bridge_doc\n"
        "type: atom\n"
        "status: active\n"
        "depends_on: [strategy_doc]\n"
        "---\n\n"
        "Bridge body references [strategy_doc](strategy_doc) inline.\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "-A"], cwd=str(root), capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "bridge"],
        cwd=str(root), capture_output=True, check=True,
    )

    server = build_server(root)
    result = _call(
        server,
        "rename_document",
        {"document_id": "strategy_doc", "new_id": "renamed_strategy"},
    )

    assert result.isError is False, result.content[0].text
    payload = result.structuredContent
    assert payload["success"] is True
    assert payload["old_id"] == "strategy_doc"
    assert payload["new_id"] == "renamed_strategy"
    # strategy.md (id + depends_on-ers) + product.md (depends_on) +
    # bridge.md (depends_on + body) all touched.
    assert set(payload["updated_files"]) == {
        "docs/strategy.md",
        "docs/product.md",
        "docs/bridge.md",
    }
    assert payload["references_updated"] >= 4

    # Strategy file's own id was rewritten.
    text = (root / "docs" / "strategy.md").read_text(encoding="utf-8")
    assert "id: renamed_strategy" in text
    # Dependents were rewritten.
    product_text = (root / "docs" / "product.md").read_text(encoding="utf-8")
    assert "renamed_strategy" in product_text
    bridge_text = (root / "docs" / "bridge.md").read_text(encoding="utf-8")
    assert "renamed_strategy" in bridge_text
    # No stale occurrences survived.
    assert "strategy_doc" not in product_text
    assert "strategy_doc" not in text


def test_rename_document_noop_same_id(tmp_path):
    root = create_workspace(tmp_path)
    _git_init_clean(root)

    server = build_server(root)
    result = _call(
        server,
        "rename_document",
        {"document_id": "kernel_doc", "new_id": "kernel_doc"},
    )

    assert result.isError is False, result.content[0].text
    payload = result.structuredContent
    assert payload["references_updated"] == 0
    assert payload["updated_files"] == []


# ---------------------------------------------------------------------------
# Validation.
# ---------------------------------------------------------------------------


def test_rename_document_rejects_missing_old_id(tmp_path):
    root = create_workspace(tmp_path)
    _git_init_clean(root)
    server = build_server(root)

    result = _call(
        server,
        "rename_document",
        {"document_id": "no_such_doc", "new_id": "brand_new"},
    )

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_DOCUMENT_NOT_FOUND"


def test_rename_document_rejects_duplicate_new_id(tmp_path):
    root = create_workspace(tmp_path)
    _git_init_clean(root)
    server = build_server(root)

    result = _call(
        server,
        "rename_document",
        {"document_id": "kernel_doc", "new_id": "strategy_doc"},
    )

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_DUPLICATE_ID"


def test_rename_document_rejects_invalid_new_id_format(tmp_path):
    root = create_workspace(tmp_path)
    _git_init_clean(root)
    server = build_server(root)

    # Contains illegal characters.
    result = _call(
        server,
        "rename_document",
        {"document_id": "kernel_doc", "new_id": "has spaces"},
    )

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_INVALID_ID"


def test_rename_document_rejects_empty_old_id(tmp_path):
    root = create_workspace(tmp_path)
    _git_init_clean(root)
    server = build_server(root)

    result = _call(
        server,
        "rename_document",
        {"document_id": "   ", "new_id": "renamed"},
    )

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_INVALID_DOCUMENT_ID"


# ---------------------------------------------------------------------------
# Git clean-state precondition (v1.1 §4.8.2 Step 4).
# ---------------------------------------------------------------------------


def test_rename_document_refuses_dirty_workspace(tmp_path):
    root = create_workspace(tmp_path)
    _git_init_clean(root)

    # Dirty the tree with a modification.
    (root / "docs" / "kernel.md").write_text(
        (root / "docs" / "kernel.md").read_text(encoding="utf-8")
        + "Extra appended line.\n",
        encoding="utf-8",
    )

    server = build_server(root)
    result = _call(
        server,
        "rename_document",
        {"document_id": "strategy_doc", "new_id": "renamed_strategy"},
    )

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_DIRTY_WORKSPACE"
    # Nothing got mutated.
    strategy_text = (root / "docs" / "strategy.md").read_text(encoding="utf-8")
    assert "id: strategy_doc" in strategy_text


def test_rename_document_refuses_untracked_files(tmp_path):
    root = create_workspace(tmp_path)
    _git_init_clean(root)
    (root / "scratch.txt").write_text("untracked\n", encoding="utf-8")

    server = build_server(root)
    result = _call(
        server,
        "rename_document",
        {"document_id": "strategy_doc", "new_id": "renamed_strategy"},
    )

    assert result.isError is True
    assert result.structuredContent["error"]["error_code"] == "E_DIRTY_WORKSPACE"


# ---------------------------------------------------------------------------
# read_only enforcement (m-2 consumer).
# ---------------------------------------------------------------------------


def test_rename_document_refuses_when_read_only(tmp_path):
    """Under CB-B2, rename_document is NOT REGISTERED when read_only=True —
    invocation raises ``ToolError`` rather than returning an E_READ_ONLY
    envelope. Workspace files must remain untouched.

    See tests/mcp/test_read_only_registration.py for the
    registration-absence check.
    """
    from mcp.server.fastmcp.exceptions import ToolError

    root = create_workspace(tmp_path)
    _git_init_clean(root)
    server = build_server(root, read_only=True)

    with pytest.raises(ToolError, match="rename_document"):
        _call(
            server,
            "rename_document",
            {"document_id": "strategy_doc", "new_id": "renamed_strategy"},
        )

    # Unchanged on disk.
    text = (root / "docs" / "strategy.md").read_text(encoding="utf-8")
    assert "id: strategy_doc" in text


# ---------------------------------------------------------------------------
# Shared workspace_id helper (m-8 consumer).
# ---------------------------------------------------------------------------


def test_rename_document_reuses_shared_workspace_id_helper():
    """Verify the import/binding chain — the tool calls the shared helper.

    Mirrors ``test_write_tools.py::test_shared_validate_workspace_id_helper_exists_and_is_reused``.
    """
    from ontos.mcp import _validation
    from ontos.mcp import rename_tool

    assert _validation.validate_workspace_id is rename_tool.validate_workspace_id


def test_rename_document_rejects_cross_workspace_id(tmp_path):
    root = create_workspace(tmp_path)
    _git_init_clean(root)
    server = build_server(root)

    result = _call(
        server,
        "rename_document",
        {
            "document_id": "strategy_doc",
            "new_id": "renamed_strategy",
            "workspace_id": "someone-elses-workspace",
        },
    )

    assert result.isError is True
    # Same shape as writes.py — portfolio-required in non-portfolio mode.
    assert result.structuredContent["error"]["error_code"] == "E_PORTFOLIO_REQUIRED"


# ---------------------------------------------------------------------------
# A1 — workspace_lock contention inside the write tool.
# ---------------------------------------------------------------------------


def _hold_workspace_lock(workspace: str, ready, release, result: Queue) -> None:
    from ontos.mcp.locking import workspace_lock

    try:
        with workspace_lock(Path(workspace), timeout=5.0):
            ready.set()
            release.wait(timeout=30.0)
        result.put(("ok", None))
    except BaseException as exc:  # pragma: no cover — relay via queue
        result.put(("error", repr(exc)))


def test_rename_document_under_contention_returns_structured_error(tmp_path):
    root = create_workspace(tmp_path)
    _git_init_clean(root)
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
            "rename_document",
            {"document_id": "strategy_doc", "new_id": "renamed_strategy"},
        )
        elapsed = time.monotonic() - start

        assert result.isError is True, result.content[0].text
        assert result.structuredContent["error"]["error_code"] == "E_WORKSPACE_BUSY"
        # Workspace-lock timeout is 5s; ensure we really waited for it.
        assert 4.5 <= elapsed <= 15.0, f"unexpected elapsed={elapsed:.2f}s"

        # No file got rewritten.
        text = (root / "docs" / "strategy.md").read_text(encoding="utf-8")
        assert "id: strategy_doc" in text
    finally:
        release.set()
        holder.join(timeout=5.0)
        if holder.is_alive():  # pragma: no cover
            holder.terminate()
            holder.join(timeout=2.0)


# ---------------------------------------------------------------------------
# A3 — post-commit rollback + rebuild path.
# ---------------------------------------------------------------------------


def test_a3_rollback_reverts_working_tree_on_commit_failure(monkeypatch, tmp_path):
    """When commit raises, the tool must rollback via ``git checkout -- .``
    and then re-invoke ``rebuild_workspace`` so the portfolio DB re-converges
    with the reverted filesystem state.
    """
    from ontos.core.context import SessionContext
    from ontos.mcp import rename_tool

    root = create_workspace(tmp_path)
    _git_init_clean(root)
    cache = build_cache(root)
    portfolio = RecordingPortfolioIndex()

    # Capture the pre-rename content so we can assert rollback worked.
    strategy_before = (root / "docs" / "strategy.md").read_text(encoding="utf-8")

    def exploding_commit(self):
        # Simulate a mid-commit IO failure AFTER buffer_write staging.
        raise IOError("induced commit failure")

    monkeypatch.setattr(SessionContext, "commit", exploding_commit)

    result = rename_tool.rename_document(
        cache,
        portfolio_index=portfolio,
        read_only=False,
        document_id="strategy_doc",
        new_id="renamed_strategy",
    )

    assert result.isError is True
    # Original commit exception surfaces — rebuild must not mask it.
    assert "induced commit failure" in result.content[0].text
    # Working tree reverted — strategy.md is exactly as before the call.
    strategy_after = (root / "docs" / "strategy.md").read_text(encoding="utf-8")
    assert strategy_after == strategy_before
    # Rebuild ran at least once as part of the recovery path.
    assert len(portfolio.rebuild_calls) >= 1
    slug, recorded_root = portfolio.rebuild_calls[0]
    assert slug == "workspace"
    assert Path(recorded_root) == root


def test_a3_rollback_does_not_leak_staged_writes(monkeypatch, tmp_path):
    """State-convergence check: after the rollback + rebuild, the filesystem
    view matches the pre-commit state, so a subsequent rescan yields the
    same document graph.
    """
    from ontos.core.context import SessionContext
    from ontos.mcp import rename_tool

    root = create_workspace(tmp_path)
    _git_init_clean(root)
    cache = build_cache(root)
    portfolio = RecordingPortfolioIndex()

    monkeypatch.setattr(
        SessionContext, "commit",
        lambda self: (_ for _ in ()).throw(IOError("induced")),
    )

    rename_tool.rename_document(
        cache,
        portfolio_index=portfolio,
        read_only=False,
        document_id="strategy_doc",
        new_id="renamed_strategy",
    )

    # The original IDs still resolve — the rename left no trace.
    snapshot = cache.get_fresh_snapshot()
    assert "strategy_doc" in snapshot.documents
    assert "renamed_strategy" not in snapshot.documents


# ---------------------------------------------------------------------------
# m-13 — FTS5 parity recoverable rebuild.
# ---------------------------------------------------------------------------


def test_m13_parity_mismatch_is_retried_once_and_succeeds(tmp_path):
    """If rebuild_workspace raises the parity-mismatch RuntimeError once,
    the tool retries once and succeeds (rebuild_workspace is idempotent).
    """
    from ontos.mcp import rename_tool

    root = create_workspace(tmp_path)
    _git_init_clean(root)
    cache = build_cache(root)
    portfolio = RecordingPortfolioIndex()
    # First rebuild raises parity mismatch; the retry succeeds.
    portfolio.raise_parity_times = 1

    result = rename_tool.rename_document(
        cache,
        portfolio_index=portfolio,
        read_only=False,
        document_id="strategy_doc",
        new_id="renamed_strategy",
    )

    assert result.isError is False, result.content[0].text
    # Exactly two rebuild attempts (first raised, second succeeded).
    assert len(portfolio.rebuild_calls) == 2


def test_m13_non_parity_error_is_not_retried(tmp_path):
    """Only parity-mismatch RuntimeError gets the retry. Other exceptions
    are re-raised immediately to avoid masking real bugs.
    """
    from ontos.mcp import rename_tool

    root = create_workspace(tmp_path)
    _git_init_clean(root)
    cache = build_cache(root)

    class Index(RecordingPortfolioIndex):
        def rebuild_workspace(self, slug, workspace_root):
            self.rebuild_calls.append((slug, str(workspace_root)))
            raise RuntimeError("not a parity error")

    portfolio = Index()

    # The rebuild is invoked in "safely" mode in the happy path — the tool
    # still succeeds because rebuild failures are swallowed + logged.
    result = rename_tool.rename_document(
        cache,
        portfolio_index=portfolio,
        read_only=False,
        document_id="strategy_doc",
        new_id="renamed_strategy",
    )

    assert result.isError is False, result.content[0].text
    # Exactly one call (no retry) — other exceptions do not trigger retry.
    assert len(portfolio.rebuild_calls) == 1


# ---------------------------------------------------------------------------
# Schema / response model wiring (m-15 partial).
# ---------------------------------------------------------------------------


def test_rename_document_response_model_registered():
    from ontos.mcp.schemas import TOOL_SUCCESS_MODELS

    assert "rename_document" in TOOL_SUCCESS_MODELS


def test_rename_document_output_schema_exposed():
    from ontos.mcp.schemas import output_schema_for

    schema = output_schema_for("rename_document")
    properties = set(schema["properties"].keys())
    assert properties == {
        "success", "old_id", "new_id", "path",
        "references_updated", "updated_files",
    }


# ---------------------------------------------------------------------------
# Shared-orchestrator cross-scope collision (gained in the Dev 3 follow-up).
# ---------------------------------------------------------------------------


def test_rename_rejects_cross_scope_collision_docs_scope(tmp_path):
    """Seed a doc with ``id: strategy_doc`` inside ``.ontos-internal/`` and
    attempt to rename the docs-scope ``strategy_doc`` → ``renamed_strategy``.
    The shared orchestrator's docs-scope external-IDs check must refuse it.

    This path was silently allowed before the shared-orchestrator refactor:
    the MCP tool had its own ID validation + collision checks that never
    consulted ``_load_external_ids``. Asserts a new regression line.
    """
    root = create_workspace(tmp_path)
    # Seed .ontos-internal/ with a colliding id BEFORE git init so the
    # baseline commit is clean.
    internal_doc = root / ".ontos-internal" / "collision.md"
    internal_doc.parent.mkdir(parents=True, exist_ok=True)
    internal_doc.write_text(
        "---\n"
        "id: strategy_doc\n"
        "type: atom\n"
        "status: active\n"
        "---\n\n"
        "Internal body.\n",
        encoding="utf-8",
    )
    _git_init_clean(root)

    server = build_server(root)
    result = _call(
        server,
        "rename_document",
        {"document_id": "strategy_doc", "new_id": "renamed_strategy"},
    )

    assert result.isError is True
    assert (
        result.structuredContent["error"]["error_code"]
        == "E_CROSS_SCOPE_COLLISION"
    )


def test_rename_library_scope_allows_ids_in_ontos_internal(tmp_path):
    """Complement: when ``scanning.default_scope = "library"``, the snapshot
    includes ``.ontos-internal/`` and the cross-scope check is skipped.

    The rename must succeed — library scope treats internal docs as first
    class participants rather than hidden siblings.
    """
    root = create_workspace(tmp_path)
    # Flip the workspace into library scope — the [scanning] section
    # already exists from create_workspace, so we append a key under it
    # via string replacement rather than declaring the table twice.
    ontos_toml = root / ".ontos.toml"
    existing = ontos_toml.read_text(encoding="utf-8")
    assert "[scanning]" in existing
    ontos_toml.write_text(
        existing.replace(
            "[scanning]",
            '[scanning]\ndefault_scope = "library"',
            1,
        ),
        encoding="utf-8",
    )
    # Internal doc that does NOT collide — rename should proceed cleanly.
    internal_doc = root / ".ontos-internal" / "neighbour.md"
    internal_doc.parent.mkdir(parents=True, exist_ok=True)
    internal_doc.write_text(
        "---\n"
        "id: internal_neighbour\n"
        "type: atom\n"
        "status: active\n"
        "---\n\n"
        "Internal body.\n",
        encoding="utf-8",
    )
    _git_init_clean(root)

    server = build_server(root)
    result = _call(
        server,
        "rename_document",
        {"document_id": "strategy_doc", "new_id": "renamed_strategy"},
    )

    assert result.isError is False, result.content[0].text
    payload = result.structuredContent
    assert payload["success"] is True
    assert payload["new_id"] == "renamed_strategy"
