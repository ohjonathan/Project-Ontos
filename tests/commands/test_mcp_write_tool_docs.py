from __future__ import annotations

from pathlib import Path

from ontos.commands.agents import generate_agents_content


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_manual_mentions_mcp_write_tools_and_contracts() -> None:
    content = (REPO_ROOT / "docs" / "reference" / "Ontos_Manual.md").read_text(encoding="utf-8")

    for token in (
        "scaffold_document",
        "log_session",
        "promote_document",
        "rename_document",
        "read_only",
        "workspace_id",
    ):
        assert token in content


def test_generated_agents_mentions_mcp_write_tools_and_contracts(monkeypatch) -> None:
    monkeypatch.chdir(REPO_ROOT)
    content = generate_agents_content()

    for token in (
        "scaffold_document",
        "log_session",
        "promote_document",
        "rename_document",
        "read_only",
        "workspace_id",
    ):
        assert token in content
