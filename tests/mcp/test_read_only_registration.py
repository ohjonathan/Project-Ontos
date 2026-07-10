"""CB-B2 regression: ``read_only=True`` must skip write-tool registration.

v4.1 Track B Phase D verdict flagged that invocation-time refusal (existing
tests at ``test_write_tools.py:244-269``) is insufficient — the tools were
still advertised via ``list_tools()``, surfacing them to clients which then
discovered they couldn't actually call them. This test pins the fix at
``ontos/mcp/server.py:164`` (``if not read_only:`` gating
``_register_write_tools``).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.mcp_helpers import build_server, create_workspace, list_tools


_WRITE_TOOL_NAMES = frozenset(
    {
        "scaffold_document",
        "log_session",
        "session_end",
        "promote_document",
        "rename_document",
    }
)


def _tool_names(server) -> set[str]:
    return {tool.name for tool in list_tools(server)}


def _tools_by_name(server):
    return {tool.name: tool for tool in list_tools(server)}


def test_read_only_server_omits_write_tools(tmp_path: Path) -> None:
    root = create_workspace(tmp_path)
    server = build_server(root, read_only=True)

    advertised = _tool_names(server)

    missing_intersect = _WRITE_TOOL_NAMES & advertised
    assert not missing_intersect, (
        f"read_only=True must not advertise write tools; found: {sorted(missing_intersect)}"
    )
    assert "activate" in advertised
    assert "ontos log" in server.instructions
    assert _tools_by_name(server)["export_graph"].annotations.readOnlyHint is True


def test_mutable_server_advertises_write_tools(tmp_path: Path) -> None:
    """Counterpart: read_only=False must still advertise the four write tools."""
    root = create_workspace(tmp_path)
    server = build_server(root, read_only=False)

    advertised = _tool_names(server)

    for name in _WRITE_TOOL_NAMES:
        assert name in advertised, (
            f"read_only=False must advertise {name}; full set: {sorted(advertised)}"
        )
    assert _tools_by_name(server)["export_graph"].annotations.readOnlyHint is False


def test_read_only_server_rejects_persistent_graph_export(tmp_path: Path) -> None:
    root = create_workspace(tmp_path)
    server = build_server(root, read_only=True)

    result = asyncio.run(
        server.call_tool("export_graph", {"export_to_file": "exports/graph.json"})
    )

    assert result.isError is True
    assert "read-only mode" in result.content[0].text
    assert not (root / "exports" / "graph.json").exists()

    in_memory = asyncio.run(server.call_tool("export_graph", {"summary_only": True}))
    assert in_memory.isError is False
    assert in_memory.structuredContent["summary"]["total_documents"] == 8


def test_read_only_server_suppresses_usage_log_writes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    root = create_workspace(tmp_path, usage_logging=True)
    server = build_server(root, read_only=True)

    result = asyncio.run(server.call_tool("workspace_overview", {}))

    assert result.isError is False
    assert not (home / ".config" / "ontos" / "usage.jsonl").exists()


def test_read_only_portfolio_requires_existing_snapshot_without_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ontos.mcp import portfolio_config
    from ontos.mcp import server as server_module

    config_path = tmp_path / "state" / "portfolio.toml"
    db_path = tmp_path / "state" / "portfolio.db"
    monkeypatch.setattr(portfolio_config, "PORTFOLIO_CONFIG_PATH", config_path)
    monkeypatch.setattr(server_module, "DEFAULT_PORTFOLIO_DB_PATH", db_path)

    with pytest.raises(FileNotFoundError):
        server_module._build_portfolio_index(read_only=True)

    assert not config_path.exists()
    assert not db_path.exists()
    assert not db_path.with_name("portfolio.db-wal").exists()
    assert not db_path.with_name("portfolio.db-shm").exists()


def test_read_only_portfolio_queries_existing_snapshot_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ontos.mcp.portfolio import PortfolioIndex
    from ontos.mcp import portfolio_config
    from ontos.mcp import server as server_module

    state = tmp_path / "state"
    state.mkdir()
    config_path = state / "portfolio.toml"
    config_path.write_text("[portfolio]\nscan_roots=[]\nexclude=[]\n", encoding="utf-8")
    db_path = state / "portfolio.db"
    writable = PortfolioIndex(db_path)
    writable.rebuild_all(scan_roots=[], exclude=[])
    writable.close()

    monkeypatch.setattr(portfolio_config, "PORTFOLIO_CONFIG_PATH", config_path)
    monkeypatch.setattr(server_module, "DEFAULT_PORTFOLIO_DB_PATH", db_path)
    before = {path.name: path.read_bytes() for path in state.iterdir() if path.is_file()}

    read_only = server_module._build_portfolio_index(read_only=True)
    assert read_only.get_projects() == []
    read_only.close()

    after = {path.name: path.read_bytes() for path in state.iterdir() if path.is_file()}
    assert after == before


def test_serve_threads_read_only_into_portfolio_builder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ontos.mcp import server as server_module

    calls: list[bool] = []

    class FakeIndex:
        def close(self) -> None:
            return None

    class FakeServer:
        def run(self, *, transport: str) -> None:
            assert transport == "stdio"

    monkeypatch.setattr(server_module, "_build_cache", lambda root: object())
    monkeypatch.setattr(
        server_module,
        "_build_portfolio_index",
        lambda *, read_only: calls.append(read_only) or FakeIndex(),
    )
    monkeypatch.setattr(server_module, "create_server", lambda *args, **kwargs: FakeServer())

    assert server_module.serve(tmp_path, portfolio=True, read_only=True) == 0
    assert calls == [True]
