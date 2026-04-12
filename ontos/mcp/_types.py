"""Shared structural types for the MCP layer.

Kept deliberately minimal: only the surface area that MCP tools and the MCP
server actually rely on when they accept a portfolio index. Callers who need
richer behavior should import :class:`ontos.mcp.portfolio.PortfolioIndex`
directly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Protocol


class PortfolioIndexLike(Protocol):
    """Structural type for objects consumed as a portfolio index.

    Matches :class:`ontos.mcp.portfolio.PortfolioIndex`. Kept narrow to the
    methods invoked from :mod:`ontos.mcp.server` and :mod:`ontos.mcp.tools`
    so that typing stays honest (m-11: replace blanket ``Any``).
    """

    def get_projects(self) -> list[dict[str, Any]]:
        """Return portfolio project metadata rows."""
        ...

    def search_fts(
        self,
        query: str,
        workspace: Optional[str],
        offset: int,
        limit: int,
    ) -> dict[str, Any]:
        """Execute BM25-ranked full-text search over indexed documents."""
        ...

    def rebuild_workspace(self, slug: str, workspace_root: Path) -> None:
        """Rebuild the portfolio index rows for a single workspace."""
        ...

    def close(self) -> None:
        """Release any resources held by the index."""
        ...
