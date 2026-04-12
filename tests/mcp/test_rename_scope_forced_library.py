"""CB-B3 regression: ``rename_document`` MCP tool uses LIBRARY scope unconditionally.

Phase D verdict flagged that Dev 3's refactor introduced a scope-tracks-config
behavior at ``rename_tool.py:429`` — ``scope = resolve_scan_scope(None,
config.scanning.default_scope)``. With a workspace configured for DOCS scope,
the cross-scope external-IDs collision check would fire, making the MCP surface
behave differently depending on a CLI-surface configuration knob. Spec
correction (per CA ruling): MCP rename ignores ``default_scope`` and always
uses ``ScanScope.LIBRARY``. This test pins that contract at
``rename_tool.py:429``.

The discriminator: seed ``.ontos-internal/`` with a document whose ID would
collide if the rename ran at DOCS scope. Pre-fix (with ``default_scope =
"docs"``) this produced ``E_CROSS_SCOPE_COLLISION``. Post-fix the cross-scope
check is skipped and the rename succeeds.
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from textwrap import dedent
from typing import Any

from mcp.types import CallToolResult

from tests.mcp import build_server, create_workspace


def _git_init_clean(root: Path) -> None:
    (root / ".gitignore").write_text(".ontos.lock\n", encoding="utf-8")
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=str(root),
                   capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.test"], cwd=str(root),
                   capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(root),
                   capture_output=True, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=str(root),
                   capture_output=True, check=True)
    subprocess.run(["git", "add", "-A"], cwd=str(root),
                   capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(root),
                   capture_output=True, check=True)


def _call(server, name: str, args: dict[str, Any]) -> CallToolResult:
    return asyncio.run(server.call_tool(name, args))


def test_rename_document_uses_library_scope_regardless_of_default_scope_config(tmp_path: Path) -> None:
    """rename_document ignores workspace ``default_scope`` and uses LIBRARY.

    Pre-fix (scope-tracks-config): with ``default_scope = "docs"`` this
    triggered the DOCS-scope external-IDs check and returned
    ``E_CROSS_SCOPE_COLLISION`` because ``external_target_id`` existed in
    ``.ontos-internal/``.

    Post-fix (unconditional LIBRARY): cross-scope check is skipped; the
    rename proceeds against the LIBRARY-scoped snapshot (which under this
    test's DOCS-scoped cache does not include the ``.ontos-internal/``
    doc), so the rename succeeds.

    Either way, ``E_CROSS_SCOPE_COLLISION`` must NOT be the outcome.
    """
    root = create_workspace(tmp_path)

    # Override the workspace config to pin DOCS scope — this is the config
    # state that pre-fix code honored via resolve_scan_scope.
    (root / ".ontos.toml").write_text(
        dedent(
            """
            [ontos]
            version = "4.0"

            [scanning]
            skip_patterns = ["_template.md", "archive/*"]
            default_scope = "docs"

            [mcp]
            usage_logging = false
            usage_log_path = "~/.config/ontos/usage.jsonl"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    # Seed an external doc in .ontos-internal/ with the target id that the
    # MCP rename will be asked to produce. This is the cross-scope "landmine."
    external_dir = root / ".ontos-internal"
    external_dir.mkdir()
    (external_dir / "external.md").write_text(
        dedent(
            """
            ---
            id: external_target_id
            type: kernel
            status: active
            ---
            External body — must not block a DOCS-scoped rename under the fix.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    _git_init_clean(root)

    server = build_server(root)
    result = _call(
        server,
        "rename_document",
        {"document_id": "kernel_doc", "new_id": "external_target_id"},
    )

    # The critical assertion: must NOT be a cross-scope collision error.
    # Pre-fix returned E_CROSS_SCOPE_COLLISION because DOCS scope ran the
    # external-IDs check.
    payload = result.structuredContent
    if result.isError:
        observed_code = payload["error"]["error_code"]
    else:
        observed_code = None

    assert observed_code != "E_CROSS_SCOPE_COLLISION", (
        "rename_document must use ScanScope.LIBRARY unconditionally; "
        f"pre-fix code would return E_CROSS_SCOPE_COLLISION here (got: {observed_code})."
    )

    # Stronger guarantee — the cache is DOCS-scoped so .ontos-internal/
    # documents aren't in the snapshot; the rename should actually succeed
    # under the fix. Assert that outcome too.
    assert result.isError is False, (
        f"rename_document should succeed under the fix; got error: "
        f"{result.content[0].text if result.content else '<no content>'}"
    )
    assert payload["success"] is True
    assert payload["new_id"] == "external_target_id"
