"""Shared helpers for MCP tests."""

from __future__ import annotations

import asyncio
import importlib
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "ontos"
REPO_ROOT_REALPATH = os.path.realpath(str(REPO_ROOT))
PACKAGE_ROOT_REALPATH = os.path.realpath(str(PACKAGE_ROOT))
if str(REPO_ROOT) in sys.path:
    sys.path.remove(str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT))


def _normalize_realpath(value: object) -> str:
    if value is None:
        return ""
    try:
        text = os.fspath(value)
    except TypeError:
        return ""
    if not text:
        return ""
    return os.path.realpath(text)


def _is_under_path(path: str, root: str) -> bool:
    return bool(path) and (path == root or path.startswith(root + os.sep))


def _is_external_package_entry(entry: object) -> bool:
    real_entry = _normalize_realpath(entry)
    if not real_entry:
        return False
    path_parts = real_entry.split(os.sep)
    if "site-packages" in path_parts or "dist-packages" in path_parts:
        return True
    return not _is_under_path(real_entry, REPO_ROOT_REALPATH)


def _ensure_repo_ontos_package() -> None:
    module = sys.modules.get("ontos")
    module_file = _normalize_realpath(getattr(module, "__file__", None)) if module else ""
    if _is_under_path(module_file, PACKAGE_ROOT_REALPATH):
        return

    for name in list(sys.modules):
        if name == "ontos" or name.startswith("ontos."):
            del sys.modules[name]


_ensure_repo_ontos_package()

from ontos.io.config import load_project_config
from ontos.io.snapshot import create_snapshot
from ontos.mcp.cache import SnapshotCache


def _ensure_real_mcp_package() -> None:
    module = sys.modules.get("mcp")
    module_file = _normalize_realpath(getattr(module, "__file__", None)) if module is not None else ""
    if module is not None and not _is_under_path(module_file, REPO_ROOT_REALPATH):
        try:
            importlib.import_module("mcp.server.fastmcp")
            return
        except Exception:
            pass

    for name in list(sys.modules):
        if name == "mcp" or name.startswith("mcp."):
            del sys.modules[name]

    for entry in sys.path:
        if not _is_external_package_entry(entry):
            continue
        spec = importlib.machinery.PathFinder.find_spec("mcp", [entry])
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules["mcp"] = module
        spec.loader.exec_module(module)
        importlib.import_module("mcp.server.fastmcp")
        return

    raise ImportError("Unable to load the external 'mcp' package from site-packages")


_ensure_real_mcp_package()


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip(), encoding="utf-8")


def create_workspace(tmp_path: Path, *, usage_logging: bool = False) -> Path:
    root = tmp_path / "workspace"
    root.mkdir(parents=True)
    write_file(
        root / ".ontos.toml",
        f"""
        [ontos]
        version = "4.0"

        [scanning]
        skip_patterns = ["_template.md", "archive/*"]

        [mcp]
        usage_logging = {"true" if usage_logging else "false"}
        usage_log_path = "~/.config/ontos/usage.jsonl"
        """,
    )
    write_file(
        root / "docs/kernel.md",
        """
        ---
        id: kernel_doc
        type: kernel
        status: active
        ---
        Kernel body.
        """,
    )
    write_file(
        root / "docs/strategy.md",
        """
        ---
        id: strategy_doc
        type: strategy
        status: active
        depends_on: [kernel_doc]
        ---
        Strategy body.
        """,
    )
    write_file(
        root / "docs/product.md",
        """
        ---
        id: product_doc
        type: product
        status: active
        depends_on: [strategy_doc]
        ---
        Product body.
        """,
    )
    write_file(
        root / "docs/atom.md",
        """
        ---
        id: atom_doc
        type: atom
        status: active
        depends_on: [product_doc]
        describes: [concept_doc, src/foo.py, src/never_existed.py]
        ---
        Atom body for hashing.
        """,
    )
    write_file(
        root / "docs/log.md",
        """
        ---
        id: log_doc
        type: log
        status: active
        depends_on: [atom_doc]
        impacts: [atom_doc]
        ---
        Log body.
        """,
    )
    write_file(
        root / "docs/reference.md",
        """
        ---
        id: reference_doc
        type: reference
        status: active
        depends_on: [kernel_doc]
        ---
        Reference body.
        """,
    )
    write_file(
        root / "docs/concept.md",
        """
        ---
        id: concept_doc
        type: concept
        status: active
        depends_on: [kernel_doc]
        ---
        Concept body.
        """,
    )
    write_file(
        root / "docs/unknown.md",
        """
        ---
        id: unknown_doc
        type: unknown
        status: active
        depends_on: [kernel_doc]
        ---
        Unknown body.
        """,
    )
    write_file(
        root / "docs/_template.md",
        """
        ---
        id: _template
        type: atom
        status: active
        depends_on: [kernel_doc]
        ---
        Template body.
        """,
    )
    write_file(root / "src/foo.py", "print('hello')\n")
    return root


def create_empty_workspace(tmp_path: Path) -> Path:
    root = tmp_path / "empty-workspace"
    root.mkdir(parents=True)
    write_file(
        root / ".ontos.toml",
        """
        [ontos]
        version = "4.0"

        [scanning]
        skip_patterns = ["_template.md", "archive/*"]
        """,
    )
    (root / "docs").mkdir()
    return root


def build_cache(root: Path) -> SnapshotCache:
    config = load_project_config(config_path=root / ".ontos.toml", repo_root=root)
    snapshot = create_snapshot(
        root=root,
        include_content=True,
        filters=None,
        git_commit_provider=None,
        scope=None,
    )
    return SnapshotCache(
        root,
        config,
        snapshot,
        started_at=datetime.now(timezone.utc),
    )


def build_server(root: Path, **kwargs: Any):
    from ontos.mcp.server import create_server

    return create_server(build_cache(root), **kwargs)


def invoke_tool(*args: Any, **kwargs: Any):
    from ontos.mcp.server import _invoke_tool

    return _invoke_tool(*args, **kwargs)


def log_usage(cache: SnapshotCache, tool_name: str) -> None:
    from ontos.mcp.server import _log_usage

    _log_usage(cache, tool_name)


def list_tools(server) -> list[Any]:
    return asyncio.run(server.list_tools())


def call_payload(result: Any) -> dict[str, Any]:
    return result.structuredContent


def run_base_cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        ["python3", "-m", "ontos", *args],
        cwd=root,
        text=True,
        capture_output=True,
        env=env,
    )


def run_mcp_cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ontos", *args],
        cwd=root,
        text=True,
        capture_output=True,
    )


def parse_json_text(result: Any) -> dict[str, Any]:
    return json.loads(result.content[0].text)
