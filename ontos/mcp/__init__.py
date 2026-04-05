"""Lazy public entry point for the Ontos MCP server."""

from __future__ import annotations

from pathlib import Path


def serve(workspace_root: Path) -> int:
    """Start the Ontos MCP server for one workspace."""
    from ontos.mcp.server import serve as _serve

    return _serve(workspace_root)
