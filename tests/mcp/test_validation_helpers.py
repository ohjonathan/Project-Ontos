from __future__ import annotations

from pathlib import Path
from typing import get_args, get_type_hints

from ontos.mcp import tools as tool_impl
from ontos.mcp._types import PortfolioIndexLike
from ontos.mcp._validation import resolve_workspace_slug


class _FakePortfolioIndex:
    def __init__(self, projects: list[dict[str, str]]) -> None:
        self._projects = projects

    def get_projects(self) -> list[dict[str, str]]:
        return list(self._projects)


def test_resolve_workspace_slug_handles_exact_match_and_collision_fallback(tmp_path: Path) -> None:
    first_root = tmp_path / "a" / "workspace"
    second_root = tmp_path / "b" / "workspace"
    first_root.mkdir(parents=True)
    second_root.mkdir(parents=True)

    exact_index = _FakePortfolioIndex(
        [
            {"slug": "workspace", "path": str(first_root)},
            {"slug": "workspace-2", "path": str(second_root)},
        ]
    )
    fallback_index = _FakePortfolioIndex(
        [
            {"slug": "workspace", "path": str(first_root)},
        ]
    )

    assert resolve_workspace_slug(second_root, exact_index) == "workspace-2"
    assert resolve_workspace_slug(second_root, fallback_index) == "workspace-2"


def test_validate_workspace_id_wrapper_annotations_match_shared_contract() -> None:
    hints = get_type_hints(tool_impl._validate_workspace_id)

    assert set(get_args(hints["portfolio_index"])) == {PortfolioIndexLike, type(None)}
    assert set(get_args(hints["workspace_id"])) == {str, type(None)}
