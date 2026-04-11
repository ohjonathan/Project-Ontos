"""Lazy public entry point for the Ontos MCP server."""

from __future__ import annotations

from pathlib import Path


def serve(
    workspace_root: Path,
    *,
    portfolio: bool = False,
    read_only: bool = False,
) -> int:
    """Start the Ontos MCP server for one workspace."""
    from ontos.mcp.server import serve as _serve

    return _serve(workspace_root, portfolio=portfolio, read_only=read_only)
