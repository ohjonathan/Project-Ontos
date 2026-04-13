from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_readme_mentions_antigravity_native_mcp_setup() -> None:
    content = _read("README.md")

    for token in (
        "Antigravity native agents",
        "~/.gemini/antigravity/mcp_config.json",
        "ontos mcp install --client antigravity",
    ):
        assert token in content


def test_manual_and_migration_guide_mention_antigravity_native_mcp_setup() -> None:
    for path in ("docs/reference/Ontos_Manual.md", "docs/reference/Migration_v3_to_v4.md"):
        content = _read(path)
        for token in (
            "~/.gemini/antigravity/mcp_config.json",
            "ontos mcp install --client antigravity",
            '"mcpServers"',
        ):
            assert token in content, f"Missing {token!r} from {path}"


def test_v413_release_notes_cover_issue_99_antigravity_fix() -> None:
    content = _read("docs/releases/v4.1.3.md")
    assert "#99" in content
    assert "Antigravity" in content
    assert "ontos mcp install --client antigravity" in content
