from __future__ import annotations

import sqlite3
from pathlib import Path
import threading
import time

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
    wal_path = tmp_path / "portfolio.db-wal"
    shm_path = tmp_path / "portfolio.db-shm"
    db_path.write_text("not a sqlite database", encoding="utf-8")
    wal_path.write_text("stale wal", encoding="utf-8")
    shm_path.write_text("stale shm", encoding="utf-8")

    index = PortfolioIndex(db_path)
    index.open()

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("PRAGMA user_version;").fetchone()[0] == 1
    expected_markers = {
        wal_path: "stale wal",
        shm_path: "stale shm",
    }
    for sidecar, marker in expected_markers.items():
        if sidecar.exists():
            assert sidecar.read_text(encoding="utf-8", errors="ignore") != marker


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


def test_connect_uses_nonzero_timeout(tmp_path, monkeypatch):
    db_path = tmp_path / "portfolio.db"
    index = PortfolioIndex(db_path)

    captured: dict[str, float | None] = {"timeout": None}
    real_connect = sqlite3.connect

    def recording_connect(*args, **kwargs):
        captured["timeout"] = kwargs.get("timeout")
        return real_connect(*args, **kwargs)

    monkeypatch.setattr("ontos.mcp.portfolio.sqlite3.connect", recording_connect)

    with index._connect() as conn:
        conn.execute("SELECT 1;")

    assert isinstance(captured["timeout"], (int, float))
    assert float(captured["timeout"]) > 0.0


def test_search_fts_waits_for_concurrent_writer_and_succeeds(tmp_path):
    workspace_root = create_workspace(tmp_path)
    db_path = tmp_path / "portfolio.db"
    index = PortfolioIndex(db_path)
    index.rebuild_workspace("workspace", workspace_root)

    holder_started = threading.Event()
    release_writer = threading.Event()
    outcome: dict[str, object] = {}

    def hold_writer_lock() -> None:
        locker = sqlite3.connect(db_path)
        try:
            locker.execute("BEGIN IMMEDIATE;")
            locker.execute(
                "UPDATE projects SET status = status WHERE slug = ?",
                ("workspace",),
            )
            holder_started.set()
            release_writer.wait(timeout=2.0)
            locker.rollback()
        finally:
            locker.close()

    def run_search() -> None:
        try:
            outcome["value"] = index.search_fts("Atom", workspace="workspace", offset=0, limit=10)
        except Exception as exc:  # pragma: no cover - assertion below validates no exception
            outcome["error"] = exc

    writer = threading.Thread(target=hold_writer_lock, daemon=True)
    reader = threading.Thread(target=run_search, daemon=True)
    writer.start()
    assert holder_started.wait(timeout=1.0)
    reader.start()
    time.sleep(0.1)
    release_writer.set()
    writer.join(timeout=2.0)
    reader.join(timeout=2.0)
    assert not writer.is_alive()
    assert not reader.is_alive()

    assert "error" not in outcome
    payload = outcome.get("value")
    assert isinstance(payload, dict)
    assert payload["total_hits"] >= 1


def test_search_fts_translates_busy_errors_to_user_error(tmp_path, monkeypatch):
    workspace_root = create_workspace(tmp_path)
    db_path = tmp_path / "portfolio.db"
    index = PortfolioIndex(db_path)
    index.rebuild_workspace("workspace", workspace_root)

    class FakeBusyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, statement, params=()):  # noqa: ARG002
            if "fts_content MATCH ?" in statement:
                raise sqlite3.OperationalError("database is locked")
            if statement == "BEGIN;":
                return None

            class _Cursor:
                @staticmethod
                def fetchone():
                    return [1]

                @staticmethod
                def fetchall():
                    return []

            return _Cursor()

        @staticmethod
        def rollback():
            return None

        @staticmethod
        def commit():
            return None

    monkeypatch.setattr(index, "_connect", lambda: FakeBusyConnection())

    with pytest.raises(OntosUserError) as exc_info:
        index.search_fts("Atom", workspace="workspace", offset=0, limit=10)

    assert exc_info.value.code == "E_PORTFOLIO_BUSY"


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
