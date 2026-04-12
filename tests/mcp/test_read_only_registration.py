"""CB-B2 regression: ``read_only=True`` must skip write-tool registration.

v4.1 Track B Phase D verdict flagged that invocation-time refusal (existing
tests at ``test_write_tools.py:244-269``) is insufficient — the tools were
still advertised via ``list_tools()``, surfacing them to clients which then
discovered they couldn't actually call them. This test pins the fix at
``ontos/mcp/server.py:164`` (``if not read_only:`` gating
``_register_write_tools``).
"""

from __future__ import annotations

from pathlib import Path

from tests.mcp import build_server, create_workspace, list_tools


_WRITE_TOOL_NAMES = frozenset(
    {
        "scaffold_document",
        "log_session",
        "promote_document",
        "rename_document",
    }
)


def _tool_names(server) -> set[str]:
    return {tool.name for tool in list_tools(server)}


def test_read_only_server_omits_write_tools(tmp_path: Path) -> None:
    root = create_workspace(tmp_path)
    server = build_server(root, read_only=True)

    advertised = _tool_names(server)

    missing_intersect = _WRITE_TOOL_NAMES & advertised
    assert not missing_intersect, (
        f"read_only=True must not advertise write tools; found: {sorted(missing_intersect)}"
    )


def test_mutable_server_advertises_write_tools(tmp_path: Path) -> None:
    """Counterpart: read_only=False must still advertise the four write tools."""
    root = create_workspace(tmp_path)
    server = build_server(root, read_only=False)

    advertised = _tool_names(server)

    for name in _WRITE_TOOL_NAMES:
        assert name in advertised, (
            f"read_only=False must advertise {name}; full set: {sorted(advertised)}"
        )
