from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ontos.core.errors import OntosUserError
from ontos.mcp.portfolio import PortfolioIndex
from tests.mcp import create_workspace, write_file


def test_open_creates_schema_and_sets_user_version(tmp_path):
    db_path = tmp_path / "portfolio.db"
    index = PortfolioIndex(db_path)

    index.open()
    index.close()

    with sqlite3.connect(db_path) as conn:
        user_version = conn.execute("PRAGMA user_version;").fetchone()[0]
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        table_names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
            ).fetchall()
        }

    assert user_version == 1
    assert journal_mode == "wal"
    assert {"projects", "documents", "edges", "scan_state", "fts_content"}.issubset(table_names)


def test_open_recovers_from_corrupt_database(tmp_path):
    db_path = tmp_path / "portfolio.db"
    db_path.write_text("not a sqlite database", encoding="utf-8")

    index = PortfolioIndex(db_path)
    index.open()

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("PRAGMA user_version;").fetchone()[0] == 1


def test_rebuild_workspace_indexes_documents_and_projects(tmp_path):
    workspace_root = create_workspace(tmp_path)
    index = PortfolioIndex(tmp_path / "portfolio.db")

    index.rebuild_workspace("workspace", workspace_root)

    projects = index.get_projects()
    documents = index.get_workspace_documents("workspace")
    search = index.search_fts("Atom", workspace="workspace", offset=0, limit=10)

    assert len(projects) == 1
    assert projects[0]["slug"] == "workspace"
    assert projects[0]["doc_count"] == 8
    assert projects[0]["status"] == "documented"
    assert len(documents) == 8
    assert search["total_hits"] >= 1
    assert any(row["doc_id"] == "atom_doc" for row in search["results"])


def test_workspace_staleness_detection(tmp_path):
    workspace_root = create_workspace(tmp_path)
    index = PortfolioIndex(tmp_path / "portfolio.db")

    index.rebuild_workspace("workspace", workspace_root)
    assert index.is_workspace_stale("workspace") is False

    write_file(
        workspace_root / "docs/atom.md",
        """
        ---
        id: atom_doc
        type: atom
        status: active
        depends_on: [product_doc]
        ---
        Atom body changed.
        """,
    )
    assert index.is_workspace_stale("workspace") is True


def test_search_fts_returns_ranked_results(tmp_path):
    workspace_root = create_workspace(tmp_path)
    index = PortfolioIndex(tmp_path / "portfolio.db")

    index.rebuild_workspace("workspace", workspace_root)
    result = index.search_fts("body", workspace="workspace", offset=0, limit=10)
    scores = [row["score"] for row in result["results"]]

    assert result["total_hits"] > 0
    assert scores == sorted(scores)


def test_search_fts_rejects_malformed_queries(tmp_path):
    workspace_root = create_workspace(tmp_path)
    index = PortfolioIndex(tmp_path / "portfolio.db")
    index.rebuild_workspace("workspace", workspace_root)

    with pytest.raises(OntosUserError) as exc_info:
        index.search_fts('"unterminated', workspace=None, offset=0, limit=10)

    assert exc_info.value.code == "E_INVALID_QUERY"


def test_rebuild_workspace_keeps_fts_row_parity(tmp_path):
    workspace_root = create_workspace(tmp_path)
    db_path = tmp_path / "portfolio.db"
    index = PortfolioIndex(db_path)
    index.rebuild_workspace("workspace", workspace_root)

    with sqlite3.connect(db_path) as conn:
        docs_count = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE workspace = ?",
            ("workspace",),
        ).fetchone()[0]
        fts_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM fts_content
            JOIN documents ON documents.rowid = fts_content.rowid
            WHERE documents.workspace = ?
            """,
            ("workspace",),
        ).fetchone()[0]

    assert docs_count == fts_count


def test_search_fts_snippet_uses_body_column(tmp_path):
    workspace_root = _make_custom_workspace(
        tmp_path,
        workspace_name="snippet-workspace",
        docs={
            "alpha.md": """
            ---
            id: alpha_doc
            type: atom
            status: active
            concepts: [conceptonly]
            ---
            This body does not contain that concept token.
            """,
        },
    )
    index = PortfolioIndex(tmp_path / "portfolio.db")
    index.rebuild_workspace("snippet", workspace_root)

    result = index.search_fts("conceptonly", workspace="snippet", offset=0, limit=10)

    assert result["total_hits"] == 1
    snippet = result["results"][0]["snippet"]
    assert "<mark>conceptonly</mark>" not in snippet.lower()


def test_rebuild_all_discovers_projects_and_handles_slug_collisions(tmp_path):
    root_one = tmp_path / "DevA"
    root_two = tmp_path / "DevB"
    root_one.mkdir()
    root_two.mkdir()

    workspace_one = _make_custom_workspace(
        root_one,
        workspace_name="sample-app",
        docs={"doc-a.md": _doc_content("doc_a", "Alpha body")},
    )
    workspace_two = _make_custom_workspace(
        root_two,
        workspace_name="sample-app",
        docs={"doc-b.md": _doc_content("doc_b", "Beta body")},
    )
    (workspace_one / ".git").mkdir()
    (workspace_two / ".git").mkdir()

    index = PortfolioIndex(tmp_path / "portfolio.db")
    index.rebuild_all([root_one, root_two], exclude=[], registry_path=None)
    projects = index.get_projects()

    assert [project["slug"] for project in projects] == ["sample-app", "sample-app-2"]
    assert all(project["doc_count"] == 1 for project in projects)


def _make_custom_workspace(tmp_path: Path, *, workspace_name: str, docs: dict[str, str]) -> Path:
    root = tmp_path / workspace_name
    root.mkdir(parents=True, exist_ok=True)
    write_file(
        root / ".ontos.toml",
        """
        [ontos]
        version = "4.0"

        [scanning]
        skip_patterns = ["_template.md", "archive/*"]
        """,
    )
    for filename, content in docs.items():
        write_file(root / "docs" / filename, content)
    return root


def _doc_content(doc_id: str, body: str) -> str:
    return f"""
    ---
    id: {doc_id}
    type: atom
    status: active
    ---
    {body}
    """
