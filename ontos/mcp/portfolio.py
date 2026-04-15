"""SQLite-backed portfolio index for cross-workspace MCP reads."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import threading
from typing import Any, Optional

from ontos.core.content_hash import compute_content_hash
from ontos.core.errors import OntosUserError
from ontos.io.config import load_project_config
from ontos.io.scan_scope import collect_scoped_documents, resolve_scan_scope
from ontos.io.snapshot import create_snapshot
from ontos.mcp.scanner import ProjectEntry, discover_projects

__all__ = ["PortfolioIndex"]

# Keep keyword detection case-sensitive and word-boundary-aware.
# Naive substring matching would misclassify plain words like FORD, ANDROID,
# NOTES, and NEARBY as explicit FTS syntax.
_FTS_SYNTAX_MARKERS = re.compile(r'\b(?:AND|OR|NOT|NEAR)\b|["*:()]')
_INVALID_FTS_QUERY_FRAGMENTS = (
    "fts5",
    "malformed match expression",
    "syntax error",
    "unterminated string",
    "unknown special query",
    # Explicit FTS column selectors like foo:bar surface as "no such column"
    # when SQLite parses "foo" as an unknown FTS column name.
    "no such column",
)
_MAX_FTS_QUERY_LENGTH = 10_000


class PortfolioIndex:
    """SQLite-backed portfolio index for cross-project queries."""

    SCHEMA_VERSION = 1
    CONNECT_TIMEOUT_SECONDS = 5.0
    PRAGMA_BLOCK = """
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = NORMAL;
        PRAGMA cache_size = -16000;
        PRAGMA mmap_size = 67108864;
        PRAGMA temp_store = MEMORY;
        PRAGMA busy_timeout = 5000;
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path.expanduser().resolve(strict=False)
        self._write_lock = threading.Lock()
        self._opened = False

    def open(self) -> None:
        """Prepare the backing DB and ensure schema compatibility."""
        with self._write_lock:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with self._connect() as conn:
                    self._initialize_db(conn)
                    conn.execute("PRAGMA optimize = 0x10002;")
            except sqlite3.DatabaseError:
                self._reset_db_file()
                with self._connect() as conn:
                    self._initialize_db(conn)
                    conn.execute("PRAGMA optimize = 0x10002;")
            self._opened = True

    def close(self) -> None:
        """No-op API for compatibility with context-managed callers."""
        self._opened = False

    def rebuild_all(
        self,
        scan_roots: list[Path],
        exclude: list[str],
        registry_path: Path | None = None,
    ) -> None:
        """Rebuild all discovered workspaces from scratch."""
        self.open()
        projects = discover_projects(
            scan_roots=scan_roots,
            exclude=exclude,
            registry_path=registry_path,
        )

        with self._write_lock:
            with self._connect() as conn:
                conn.execute("BEGIN IMMEDIATE;")
                conn.execute("DELETE FROM edges;")
                conn.execute("DELETE FROM documents;")
                conn.execute("DELETE FROM projects;")
                conn.execute("DELETE FROM scan_state;")
                conn.execute("DELETE FROM fts_content;")
                conn.commit()

        for project in projects:
            self._rebuild_workspace(project.slug, project.path, project=project)

        with self._connect() as conn:
            conn.execute("INSERT INTO fts_content(fts_content) VALUES('optimize');")
            try:
                conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
            except sqlite3.OperationalError:
                pass

    def rebuild_workspace(self, slug: str, workspace_root: Path) -> None:
        """Rebuild one workspace in a serialized write transaction."""
        self.open()
        self._rebuild_workspace(slug, workspace_root, project=None)

    def is_workspace_stale(self, slug: str) -> bool:
        """Return True when tracked file fingerprints drift from scan_state."""
        self.open()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT p.path AS path, s.fingerprint AS fingerprint
                FROM projects p
                LEFT JOIN scan_state s ON s.workspace = p.slug
                WHERE p.slug = ?
                """,
                (slug,),
            ).fetchone()

        if row is None:
            return True

        workspace_path = Path(row["path"])
        if not workspace_path.exists():
            return True

        stored_raw = row["fingerprint"]
        if not isinstance(stored_raw, str):
            return True

        try:
            stored = json.loads(stored_raw)
        except ValueError:
            return True

        current = self._workspace_fingerprint(workspace_path)
        return stored != current

    def get_projects(self) -> list[dict[str, Any]]:
        """Return portfolio project metadata rows."""
        self.open()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT slug, path, status, doc_count, has_ontos, has_readme,
                       last_scanned, last_modified, tags, metadata
                FROM projects
                ORDER BY slug
                """
            ).fetchall()

        payload: list[dict[str, Any]] = []
        for row in rows:
            payload.append(
                {
                    "slug": row["slug"],
                    "path": row["path"],
                    "status": row["status"],
                    "doc_count": int(row["doc_count"] or 0),
                    "has_ontos": bool(row["has_ontos"]),
                    "has_readme": bool(row["has_readme"]),
                    "last_scanned": row["last_scanned"],
                    "last_modified": row["last_modified"],
                    "tags": self._safe_json_array(row["tags"]),
                    "metadata": self._safe_json_object(row["metadata"]),
                }
            )
        return payload

    def search_fts(
        self,
        query: str,
        workspace: str | None,
        offset: int,
        limit: int,
    ) -> dict[str, Any]:
        """Execute BM25-ranked full-text search over indexed documents."""
        self.open()
        if offset < 0:
            raise OntosUserError("offset must be >= 0.", code="E_INVALID_OFFSET")
        if limit <= 0:
            raise OntosUserError("limit must be > 0.", code="E_INVALID_LIMIT")
        if not query:
            raise OntosUserError("query must be non-empty.", code="E_INVALID_QUERY")
        sanitized_query = _sanitize_fts_query(query)
        if not sanitized_query:
            raise OntosUserError("query must be non-empty.", code="E_INVALID_QUERY")

        with self._connect() as conn:
            try:
                conn.execute("BEGIN;")
                where = "fts_content MATCH ?"
                params: list[Any] = [sanitized_query]
                if workspace:
                    where += " AND documents.workspace = ?"
                    params.append(workspace)

                total_count = conn.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM fts_content
                    JOIN documents ON documents.rowid = fts_content.rowid
                    WHERE {where}
                    """,
                    tuple(params),
                ).fetchone()[0]

                rows = conn.execute(
                    f"""
                    SELECT
                        documents.workspace AS workspace,
                        documents.id AS id,
                        documents.type AS type,
                        documents.status AS status,
                        documents.path AS path,
                        documents.title AS title,
                        bm25(fts_content, 10.0, 3.0, 1.0) AS rank,
                        snippet(fts_content, 2, '<mark>', '</mark>', '...', 32) AS snippet
                    FROM fts_content
                    JOIN documents ON documents.rowid = fts_content.rowid
                    WHERE {where}
                    ORDER BY rank
                    LIMIT ? OFFSET ?
                    """,
                    tuple(params + [limit, offset]),
                ).fetchall()
                conn.commit()
            except sqlite3.OperationalError as exc:
                conn.rollback()
                if self._is_invalid_fts_query(exc):
                    raise OntosUserError("Malformed full-text query.", code="E_INVALID_QUERY") from exc
                if self._is_busy_error(exc):
                    raise OntosUserError(
                        "Portfolio index is busy. Please retry.",
                        code="E_PORTFOLIO_BUSY",
                    ) from exc
                raise
            except Exception:
                conn.rollback()
                raise

        return {
            "total_hits": int(total_count),
            "results": [
                {
                    "doc_id": row["id"],
                    "workspace_slug": row["workspace"],
                    "type": row["type"],
                    "status": row["status"],
                    "path": row["path"],
                    "snippet": row["snippet"] or "",
                    "score": float(row["rank"]) if row["rank"] is not None else 0.0,
                }
                for row in rows
            ],
        }

    def get_workspace_documents(self, slug: str) -> list[dict[str, Any]]:
        """Return indexed document rows for one workspace."""
        self.open()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    id, workspace, type, status, path, title, curation,
                    content_hash, word_count, concepts, last_modified
                FROM documents
                WHERE workspace = ?
                ORDER BY id
                """,
                (slug,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _rebuild_workspace(
        self,
        slug: str,
        workspace_root: Path,
        *,
        project: ProjectEntry | None,
    ) -> None:
        root = workspace_root.expanduser().resolve(strict=False)
        has_ontos = (root / ".ontos.toml").exists()
        has_readme = (root / "README.md").exists() or (root / "readme.md").exists()
        snapshot = create_snapshot(
            root=root,
            include_content=True,
            filters=None,
            git_commit_provider=None,
            scope=None,
        )

        with self._write_lock:
            with self._connect() as conn:
                conn.execute("BEGIN IMMEDIATE;")
                rowids = [
                    row[0]
                    for row in conn.execute(
                        "SELECT rowid FROM documents WHERE workspace = ?",
                        (slug,),
                    ).fetchall()
                ]
                if rowids:
                    conn.executemany(
                        "DELETE FROM fts_content WHERE rowid = ?",
                        [(rowid,) for rowid in rowids],
                    )
                conn.execute(
                    "DELETE FROM edges WHERE from_workspace = ? OR to_workspace = ?",
                    (slug, slug),
                )
                conn.execute("DELETE FROM documents WHERE workspace = ?", (slug,))

                doc_count = len(snapshot.documents)
                status = project.status if project else self._classify_workspace(has_ontos, has_readme, doc_count)
                tags = project.tags if project else []
                metadata = project.metadata if project else {}

                conn.execute(
                    """
                    INSERT INTO projects(
                        slug, path, status, doc_count, has_ontos, has_readme,
                        last_scanned, last_modified, tags, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(slug) DO UPDATE SET
                        path = excluded.path,
                        status = excluded.status,
                        doc_count = excluded.doc_count,
                        has_ontos = excluded.has_ontos,
                        has_readme = excluded.has_readme,
                        last_scanned = excluded.last_scanned,
                        last_modified = excluded.last_modified,
                        tags = excluded.tags,
                        metadata = excluded.metadata
                    """,
                    (
                        slug,
                        str(root),
                        status,
                        doc_count,
                        int(has_ontos),
                        int(has_readme),
                        self._iso_now(),
                        self._path_mtime_iso(root),
                        json.dumps(tags),
                        json.dumps(metadata),
                    ),
                )

                for doc in sorted(snapshot.documents.values(), key=lambda item: item.id):
                    doc_path = doc.filepath.resolve(strict=False)
                    try:
                        rel_path = doc_path.relative_to(root).as_posix()
                    except ValueError:
                        rel_path = doc_path.name
                    concepts = " ".join(term for term in doc.tags if term)
                    cursor = conn.execute(
                        """
                        INSERT INTO documents(
                            id, workspace, type, status, path, title, curation,
                            content_hash, word_count, concepts, body, last_modified
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            doc.id,
                            slug,
                            doc.type.value,
                            doc.status.value,
                            rel_path,
                            self._extract_title(doc.frontmatter),
                            self._extract_curation(doc.frontmatter),
                            compute_content_hash(doc.content) if doc.content else None,
                            len(doc.content.split()) if doc.content else 0,
                            concepts,
                            doc.content,
                            self._path_mtime_iso(doc_path),
                        ),
                    )
                    conn.execute(
                        """
                        INSERT INTO fts_content(rowid, title, concepts, body)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            cursor.lastrowid,
                            self._extract_title(doc.frontmatter) or "",
                            concepts,
                            doc.content or "",
                        ),
                    )

                    for depends_id in sorted(set(doc.depends_on)):
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO edges(
                                from_workspace, from_id, to_workspace, to_id, type
                            ) VALUES (?, ?, ?, ?, 'depends_on')
                            """,
                            (slug, doc.id, slug, depends_id),
                        )

                conn.execute(
                    """
                    INSERT INTO scan_state(workspace, fingerprint, scanned_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(workspace) DO UPDATE SET
                        fingerprint = excluded.fingerprint,
                        scanned_at = excluded.scanned_at
                    """,
                    (
                        slug,
                        json.dumps(self._workspace_fingerprint(root), sort_keys=True),
                        self._iso_now(),
                    ),
                )
                conn.commit()

                docs_count = conn.execute(
                    "SELECT COUNT(*) FROM documents WHERE workspace = ?",
                    (slug,),
                ).fetchone()[0]
                fts_count = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM fts_content
                    JOIN documents ON documents.rowid = fts_content.rowid
                    WHERE documents.workspace = ?
                    """,
                    (slug,),
                ).fetchone()[0]
                if docs_count != fts_count:
                    raise RuntimeError(
                        f"FTS parity mismatch for {slug}: documents={docs_count}, fts={fts_count}"
                    )

                conn.execute("PRAGMA wal_checkpoint(PASSIVE);")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=self.CONNECT_TIMEOUT_SECONDS,
        )
        conn.row_factory = sqlite3.Row
        self._apply_pragmas(conn)
        conn.execute("PRAGMA wal_autocheckpoint = 0;")
        return conn

    def _initialize_db(self, conn: sqlite3.Connection) -> None:
        version = int(conn.execute("PRAGMA user_version;").fetchone()[0])
        table_count = int(
            conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%';"
            ).fetchone()[0]
        )
        if version == self.SCHEMA_VERSION:
            return
        if version == 0 and table_count == 0:
            self._create_schema(conn)
            return
        raise sqlite3.DatabaseError(
            f"Schema version mismatch: expected {self.SCHEMA_VERSION}, got {version}. "
            "The caller (PortfolioIndex.open) recovers by invoking "
            "_reset_db_file() to delete the on-disk database and recreate the "
            "schema from scratch; no manual migration is performed."
        )

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE projects (
                slug         TEXT PRIMARY KEY,
                path         TEXT NOT NULL UNIQUE,
                status       TEXT NOT NULL,
                doc_count    INTEGER DEFAULT 0,
                has_ontos    BOOLEAN DEFAULT FALSE,
                has_readme   BOOLEAN DEFAULT FALSE,
                last_scanned TEXT,
                last_modified TEXT,
                tags         TEXT,
                metadata     TEXT
            );

            CREATE TABLE documents (
                id            TEXT NOT NULL,
                workspace     TEXT NOT NULL REFERENCES projects(slug),
                type          TEXT NOT NULL,
                status        TEXT NOT NULL,
                path          TEXT NOT NULL,
                title         TEXT,
                curation      TEXT,
                content_hash  TEXT,
                word_count    INTEGER,
                concepts      TEXT,
                body          TEXT,
                last_modified TEXT,
                PRIMARY KEY (workspace, id)
            );

            CREATE TABLE edges (
                from_workspace TEXT NOT NULL,
                from_id        TEXT NOT NULL,
                to_workspace   TEXT NOT NULL,
                to_id          TEXT NOT NULL,
                type           TEXT NOT NULL DEFAULT 'depends_on',
                PRIMARY KEY (from_workspace, from_id, to_workspace, to_id, type)
            );

            CREATE TABLE scan_state (
                workspace   TEXT PRIMARY KEY REFERENCES projects(slug),
                fingerprint TEXT NOT NULL,
                scanned_at  TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE fts_content USING fts5(
                title,
                concepts,
                body,
                tokenize='porter unicode61',
                prefix='2,3'
            );

            INSERT INTO fts_content(fts_content, rank) VALUES('rank', 'bm25(10.0, 3.0, 1.0)');

            CREATE INDEX idx_documents_workspace ON documents(workspace);
            CREATE INDEX idx_documents_type ON documents(type);
            CREATE INDEX idx_documents_status ON documents(status);
            CREATE INDEX idx_edges_to ON edges(to_workspace, to_id);

            PRAGMA user_version = 1;
            """
        )

    def _reset_db_file(self) -> None:
        candidates = (
            self.db_path,
            self.db_path.with_name(f"{self.db_path.name}-wal"),
            self.db_path.with_name(f"{self.db_path.name}-shm"),
        )
        for path in candidates:
            try:
                path.unlink()
            except FileNotFoundError:
                continue

    def _apply_pragmas(self, conn: sqlite3.Connection) -> None:
        for statement in self.PRAGMA_BLOCK.splitlines():
            line = statement.strip()
            if not line:
                continue
            conn.execute(line)

    @staticmethod
    def _path_mtime_iso(path: Path) -> str | None:
        try:
            stat = path.stat()
        except OSError:
            return None
        return datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

    @staticmethod
    def _iso_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _extract_title(frontmatter: dict[str, Any]) -> Optional[str]:
        title = frontmatter.get("title")
        return str(title) if isinstance(title, str) and title.strip() else None

    @staticmethod
    def _extract_curation(frontmatter: dict[str, Any]) -> Optional[str]:
        value = frontmatter.get("curation")
        return str(value) if value is not None else None

    @staticmethod
    def _classify_workspace(has_ontos: bool, has_readme: bool, doc_count: int) -> str:
        if has_ontos and doc_count >= 5:
            return "documented"
        if (has_readme and not has_ontos) or (has_ontos and doc_count < 5):
            return "partial"
        return "undocumented"

    @staticmethod
    def _safe_json_array(raw_value: Any) -> list[str]:
        if isinstance(raw_value, str):
            try:
                parsed = json.loads(raw_value)
            except ValueError:
                return []
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, str)]
        return []

    @staticmethod
    def _safe_json_object(raw_value: Any) -> dict[str, Any]:
        if isinstance(raw_value, str):
            try:
                parsed = json.loads(raw_value)
            except ValueError:
                return {}
            if isinstance(parsed, dict):
                return parsed
        return {}

    @staticmethod
    def _is_invalid_fts_query(exc: sqlite3.OperationalError) -> bool:
        message = str(exc).lower()
        return any(fragment in message for fragment in _INVALID_FTS_QUERY_FRAGMENTS)

    @staticmethod
    def _is_busy_error(exc: sqlite3.OperationalError) -> bool:
        message = str(exc).lower()
        return "database is locked" in message or "database table is locked" in message

    @staticmethod
    def _stat_fingerprint(path: Path) -> tuple[int, int] | None:
        try:
            stat = path.stat()
        except OSError:
            return None
        return stat.st_mtime_ns, stat.st_size

    def _workspace_fingerprint(self, workspace_root: Path) -> dict[str, list[int] | None]:
        root = workspace_root.resolve(strict=False)
        try:
            config = load_project_config(config_path=root / ".ontos.toml", repo_root=root)
            effective_scope = resolve_scan_scope(None, config.scanning.default_scope)
            paths = collect_scoped_documents(
                root,
                config,
                effective_scope,
                base_skip_patterns=config.scanning.skip_patterns,
            )
        except Exception:
            docs_dir = root / "docs"
            if not docs_dir.is_dir():
                return {}
            paths = sorted(path for path in docs_dir.rglob("*.md") if path.is_file())

        fingerprint: dict[str, list[int] | None] = {}
        for path in sorted(paths):
            rel_path = path.resolve(strict=False).relative_to(root).as_posix()
            stat = self._stat_fingerprint(path)
            fingerprint[rel_path] = [stat[0], stat[1]] if stat is not None else None
        return fingerprint


def _sanitize_fts_query(query: str) -> str:
    if len(query) > _MAX_FTS_QUERY_LENGTH:
        raise OntosUserError(
            f"Query exceeds maximum length of {_MAX_FTS_QUERY_LENGTH} characters.",
            code="E_INVALID_QUERY",
        )
    trimmed = query.strip()
    # Keep ":" on the explicit-syntax path; literal-colon queries like
    # user:alice remain a known limitation and surface as E_INVALID_QUERY.
    if _FTS_SYNTAX_MARKERS.search(trimmed):
        return trimmed
    return " ".join(f'"{term}"' for term in trimmed.split())
