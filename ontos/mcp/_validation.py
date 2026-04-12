"""Shared validation helpers for MCP tools.

Consolidates workspace_id validation used by both read and write tools so a
single helper replaces the duplicated guards at ``server.py:478`` and
``tools.py:513-525`` (addendum item m-8 / m-14). Write tools call
``validate_workspace_id`` prior to mutating anything in the workspace.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ontos.core.errors import OntosUserError
from ontos.mcp._types import PortfolioIndexLike
from ontos.mcp.scanner import allocate_slug, slugify


def _project_rows(
    portfolio_index: Optional[PortfolioIndexLike],
) -> list[tuple[str, Path]]:
    """Return normalized ``(slug, path)`` rows from the portfolio index."""
    if portfolio_index is None:
        return []

    rows: list[tuple[str, Path]] = []
    for project in portfolio_index.get_projects():
        slug = project.get("slug")
        raw_path = project.get("path")
        if not isinstance(slug, str) or not slug:
            continue
        try:
            normalized_path = Path(raw_path).expanduser().resolve(strict=False)
        except (TypeError, ValueError):
            continue
        rows.append((slug, normalized_path))
    return rows


def _project_slugs(portfolio_index: Optional[PortfolioIndexLike]) -> list[str]:
    """Return workspace slugs without requiring path metadata."""
    if portfolio_index is None:
        return []

    slugs: list[str] = []
    for project in portfolio_index.get_projects():
        slug = project.get("slug")
        if isinstance(slug, str) and slug:
            slugs.append(slug)
    return slugs


def resolve_workspace_slug(
    workspace_root: Path,
    portfolio_index: Optional[PortfolioIndexLike],
) -> str:
    """Resolve the canonical workspace slug for write-tool rebuilds.

    Resolution order:
    1. Exact path match against the portfolio index.
    2. Recomputed ``slugify`` + ``allocate_slug`` when basename collisions
       are visible in the indexed project set.
    3. Plain ``slugify`` fallback for non-portfolio mode.
    """
    normalized_root = workspace_root.expanduser().resolve(strict=False)
    project_rows = _project_rows(portfolio_index)

    for slug, project_path in project_rows:
        if project_path == normalized_root:
            return slug

    existing_paths = {path for _, path in project_rows if path.exists()}
    existing_paths.add(normalized_root)
    same_name_paths = {path for path in existing_paths if path.name == normalized_root.name}
    if len(same_name_paths) > 1:
        used_slugs: dict[str, int] = {}
        for candidate_path in sorted(existing_paths):
            candidate_slug = allocate_slug(slugify(candidate_path.name), used_slugs)
            if candidate_path == normalized_root:
                return candidate_slug

    return slugify(normalized_root.name)


def validate_workspace_id(
    portfolio_index: Optional[PortfolioIndexLike],
    workspace_id: Optional[str],
    *,
    require: bool = False,
) -> None:
    """Validate ``workspace_id`` against the portfolio index.

    Args:
        portfolio_index: Portfolio index instance (may be ``None`` in
            non-portfolio mode).
        workspace_id: Caller-supplied workspace slug. ``None`` is
            tolerated unless ``require=True``.
        require: When True, raise if ``workspace_id`` is missing.

    Raises:
        OntosUserError: If the id is missing and required, if portfolio
            mode is required but not active, or if the id does not match
            any known workspace slug.
    """
    if workspace_id is None:
        if require:
            raise OntosUserError(
                "workspace_id is required in portfolio mode. "
                "Use project_registry() to discover available workspaces.",
                code="E_MISSING_WORKSPACE",
            )
        return

    if portfolio_index is None:
        raise OntosUserError(
            "workspace_id requires portfolio mode.",
            code="E_PORTFOLIO_REQUIRED",
        )

    slugs = _project_slugs(portfolio_index)
    if workspace_id not in slugs:
        sorted_slugs = ", ".join(sorted(slugs))
        raise OntosUserError(
            f"Unknown workspace '{workspace_id}'. "
            f"Valid workspace slugs: {sorted_slugs}. "
            "Use project_registry() to discover available workspaces.",
            code="E_UNKNOWN_WORKSPACE",
        )
