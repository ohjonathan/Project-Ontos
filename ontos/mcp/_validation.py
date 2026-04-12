"""Shared validation helpers for MCP tools.

Consolidates workspace_id validation used by both read and write tools so a
single helper replaces the duplicated guards at ``server.py:478`` and
``tools.py:513-525`` (addendum item m-8 / m-14). Write tools call
``validate_workspace_id`` prior to mutating anything in the workspace.
"""

from __future__ import annotations

from typing import Any, Optional

from ontos.core.errors import OntosUserError


def validate_workspace_id(
    portfolio_index: Any,
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

    projects = portfolio_index.get_projects()
    slugs = [project["slug"] for project in projects]
    if workspace_id not in slugs:
        sorted_slugs = ", ".join(sorted(slugs))
        raise OntosUserError(
            f"Unknown workspace '{workspace_id}'. "
            f"Valid workspace slugs: {sorted_slugs}. "
            "Use project_registry() to discover available workspaces.",
            code="E_UNKNOWN_WORKSPACE",
        )
