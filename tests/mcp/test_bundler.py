from datetime import date, timedelta

from ontos.io.snapshot import create_snapshot
from ontos.mcp.bundler import build_context_bundle

from tests.mcp import create_empty_workspace, create_workspace, write_file


def test_build_context_bundle_scores_kernels_highest(tmp_path):
    root = create_workspace(tmp_path)
    snapshot = create_snapshot(root=root, include_content=True, filters=None, git_commit_provider=None, scope=None)

    payload = build_context_bundle(snapshot, root, "workspace")
    scores = {item["id"]: item["score"] for item in payload["included_documents"]}

    assert scores["kernel_doc"] == 1.0
    assert all(0.0 <= score <= 1.0 for score in scores.values())


def test_build_context_bundle_greedy_packing_excludes_over_budget_docs(tmp_path):
    root = create_workspace(tmp_path)
    write_file(
        root / "docs/heavy.md",
        f"""
        ---
        id: heavy_doc
        type: reference
        status: active
        depends_on: [kernel_doc]
        ---
        {"heavy " * 2000}
        """,
    )
    snapshot = create_snapshot(root=root, include_content=True, filters=None, git_commit_provider=None, scope=None)

    payload = build_context_bundle(snapshot, root, "workspace", token_budget=1024)

    included_ids = {item["id"] for item in payload["included_documents"]}
    assert "kernel_doc" in included_ids
    assert "heavy_doc" not in included_ids
    assert payload["excluded_count"] >= 1


def test_build_context_bundle_empty_workspace(tmp_path):
    root = create_empty_workspace(tmp_path)
    snapshot = create_snapshot(root=root, include_content=True, filters=None, git_commit_provider=None, scope=None)

    payload = build_context_bundle(snapshot, root, "empty")

    assert payload["document_count"] == 0
    assert payload["included_documents"] == []
    assert payload["token_estimate"] == 0


def test_build_context_bundle_budget_smaller_than_kernel_still_includes_kernel(tmp_path):
    root = create_workspace(tmp_path)
    write_file(
        root / "docs/kernel.md",
        f"""
        ---
        id: kernel_doc
        type: kernel
        status: active
        ---
        {"kernel " * 1000}
        """,
    )
    snapshot = create_snapshot(root=root, include_content=True, filters=None, git_commit_provider=None, scope=None)

    payload = build_context_bundle(snapshot, root, "workspace", token_budget=10)

    ids = [item["id"] for item in payload["included_documents"]]
    assert "kernel_doc" in ids


def test_build_context_bundle_recent_logs_scored_lower(tmp_path):
    root = create_workspace(tmp_path)
    today = date.today().isoformat()
    old = (date.today() - timedelta(days=40)).isoformat()
    write_file(
        root / f"docs/{today}_recent-log.md",
        f"""
        ---
        id: {today}_recent_log
        type: log
        status: active
        date: {today}
        depends_on: [atom_doc]
        ---
        Recent log body.
        """,
    )
    write_file(
        root / f"docs/{old}_old-log.md",
        f"""
        ---
        id: {old}_old_log
        type: log
        status: active
        date: {old}
        depends_on: [atom_doc]
        ---
        Old log body.
        """,
    )
    snapshot = create_snapshot(root=root, include_content=True, filters=None, git_commit_provider=None, scope=None)

    payload = build_context_bundle(snapshot, root, "workspace")
    score_map = {item["id"]: item["score"] for item in payload["included_documents"]}

    assert score_map[f"{today}_recent_log"] == 0.3
    assert score_map[f"{old}_old_log"] >= 0.5
