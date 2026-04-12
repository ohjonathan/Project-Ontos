"""Tests for bundle-config wiring (SF-3 / addendum v1.2 §A4).

Covers:
- ``get_context_bundle`` consumes all three bundle fields from the loaded
  :class:`PortfolioConfig` (max_logs, log_window_days, token_budget).
- Integration: all three fields applied together.
- ``_DEFAULT_CONFIG_TEXT`` TOML template agrees with the dataclass defaults.
- Tail-first truncation: when the token budget is exceeded, the newest logs
  are preserved and older logs are dropped first.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

import ontos.mcp.portfolio_config as portfolio_config_module
from ontos.io.snapshot import create_snapshot
from ontos.mcp import tools as tool_impl
from ontos.mcp.bundler import build_context_bundle
from ontos.mcp.cache import SnapshotCache
from ontos.mcp.portfolio_config import PortfolioConfig, _DEFAULT_CONFIG_TEXT

from tests.mcp import build_cache, create_empty_workspace, create_workspace, write_file


# ---------------------------------------------------------------------------
# Defaults parity: dataclass vs TOML template
# ---------------------------------------------------------------------------


def test_portfolio_config_dataclass_defaults_match_toml_template():
    """The generated-on-first-run TOML template must reflect the dataclass
    defaults exactly, or the first-run user ends up with a config whose numbers
    silently disagree with the in-code defaults.
    """
    parsed = tomllib.loads(_DEFAULT_CONFIG_TEXT)
    bundle = parsed.get("bundle", {})
    portfolio_block = parsed.get("portfolio", {})

    defaults = PortfolioConfig()

    # Bundle block.
    assert bundle.get("token_budget") == defaults.bundle_token_budget == 8000
    assert bundle.get("max_logs") == defaults.bundle_max_logs == 20
    assert bundle.get("log_window_days") == defaults.bundle_log_window_days == 30

    # Portfolio block scalars/lists.
    assert portfolio_block.get("scan_roots") == defaults.scan_roots
    assert portfolio_block.get("exclude") == defaults.exclude
    assert portfolio_block.get("registry_path") == defaults.registry_path


# ---------------------------------------------------------------------------
# Helpers for log-heavy fixtures
# ---------------------------------------------------------------------------


def _write_log(root: Path, log_date: date, slug: str = "log") -> str:
    """Write a simple log doc and return its ID."""
    iso = log_date.isoformat()
    doc_id = f"{iso.replace('-', '_')}_{slug}"
    write_file(
        root / f"docs/{iso}_{slug}.md",
        f"""
        ---
        id: {doc_id}
        type: log
        status: active
        date: {iso}
        depends_on: [atom_doc]
        ---
        Log body for {slug} on {iso}.
        """,
    )
    return doc_id


def _snapshot(root: Path):
    return create_snapshot(
        root=root,
        include_content=True,
        filters=None,
        git_commit_provider=None,
        scope=None,
    )


# ---------------------------------------------------------------------------
# Per-field unit tests at the bundler layer (SF-3 wiring verification)
# ---------------------------------------------------------------------------


def test_bundler_max_logs_caps_number_of_log_entries(tmp_path):
    """`max_logs` must cap the number of log entries in the bundle regardless
    of token budget.
    """
    root = create_empty_workspace(tmp_path)
    # Provide a kernel doc so there's something non-trivial to bundle.
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
    ids = []
    # Seven fresh logs, well inside any plausible default window, each with
    # a distinct ISO date so there are no tie-break ambiguities.
    for day_offset in range(7):
        ids.append(
            _write_log(root, date.today() - timedelta(days=day_offset), slug=f"n{day_offset}")
        )
    snapshot = _snapshot(root)

    # Only 2 logs should survive the cap.
    payload = build_context_bundle(
        snapshot, root, "workspace", max_logs=2, log_window_days=30, token_budget=128000
    )
    log_ids = {item["id"] for item in payload["included_documents"] if item["type"] == "log"}
    assert len(log_ids) == 2, log_ids
    # The two most-recent logs should survive (tail-first truncation: older
    # ones are dropped first).
    assert ids[0] in log_ids
    assert ids[1] in log_ids


def test_bundler_log_window_days_excludes_logs_outside_window(tmp_path):
    """Logs dated more than ``log_window_days`` in the past must be excluded
    from the recent-logs pool.
    """
    root = create_workspace(tmp_path)
    fresh_id = _write_log(root, date.today() - timedelta(days=2), slug="fresh")
    stale_id = _write_log(root, date.today() - timedelta(days=45), slug="stale")
    snapshot = _snapshot(root)

    payload = build_context_bundle(
        snapshot, root, "workspace", max_logs=20, log_window_days=14, token_budget=128000
    )
    log_ids = {item["id"] for item in payload["included_documents"] if item["type"] == "log"}

    # Fresh log scored as a recent log (0.3).
    scored = {item["id"]: item["score"] for item in payload["included_documents"]}
    assert fresh_id in log_ids
    assert scored.get(fresh_id) == 0.3
    # Stale log does not get the recent-log boost.
    assert scored.get(stale_id) != 0.3


def test_bundler_token_budget_hard_caps_total_tokens(tmp_path):
    """A small ``token_budget`` must drop non-kernel docs to respect the cap.

    Also demonstrates tail-first truncation: when the budget is tight, the
    older log is dropped before the newer one is.
    """
    root = create_empty_workspace(tmp_path)
    # One kernel doc — always included.
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
    new_id = _write_log(root, date.today(), slug="new")
    old_id = _write_log(root, date.today() - timedelta(days=5), slug="old")
    # Pad the logs with content so only one of them can fit alongside the
    # kernel. estimate_tokens() uses len(content) // 4, so ~4000 chars per
    # log keeps each log at ~1000 tokens; with a 1500-token budget only the
    # newest log can fit.
    for iso, slug in ((date.today().isoformat(), "new"), ((date.today() - timedelta(days=5)).isoformat(), "old")):
        path = root / f"docs/{iso}_{slug}.md"
        path.write_text(
            path.read_text(encoding="utf-8") + ("x " * 2000),
            encoding="utf-8",
        )
    snapshot = _snapshot(root)

    payload = build_context_bundle(
        snapshot,
        root,
        "workspace",
        token_budget=1500,  # Enough for kernel + ~one padded log.
        max_logs=20,
        log_window_days=30,
    )

    included_ids = {item["id"] for item in payload["included_documents"]}
    assert "kernel_doc" in included_ids
    # Tail-first truncation: the newer log survives, the older log is dropped.
    assert new_id in included_ids, included_ids
    assert old_id not in included_ids, included_ids
    # The budget is actually respected (hard cap).
    assert payload["token_estimate"] <= 1500
    assert payload["excluded_count"] >= 1


def test_bundler_integration_all_three_fields_respected(tmp_path):
    """Integration: max_logs + log_window_days + token_budget applied together."""
    root = create_workspace(tmp_path)
    # Inside window (fresh): 4 logs.
    for i in range(4):
        _write_log(root, date.today() - timedelta(days=i), slug=f"fresh{i}")
    # Outside window: 3 old logs.
    for i in range(3):
        _write_log(root, date.today() - timedelta(days=60 + i), slug=f"old{i}")
    snapshot = _snapshot(root)

    payload = build_context_bundle(
        snapshot,
        root,
        "workspace",
        token_budget=128000,
        max_logs=2,
        log_window_days=14,
    )

    log_entries = [item for item in payload["included_documents"] if item["type"] == "log"]
    included_ids = {item["id"] for item in payload["included_documents"]}
    log_scores = {item["id"]: item["score"] for item in log_entries}
    # max_logs cap applies: exactly two logs at the recent-log score.
    recent_scored = [lid for lid, score in log_scores.items() if score == 0.3]
    assert len(recent_scored) == 2
    # log_window_days filter applies: none of the explicitly-dated "old*"
    # logs (60+ days back) should have survived, regardless of their
    # scoring bucket.
    for old_slug in ("old0", "old1", "old2"):
        assert not any(old_slug in doc_id for doc_id in included_ids), included_ids
    # And because we tightened `_build_priority_order` so that logs only
    # enter the bundle via the recent-logs pool, the total log count in the
    # bundle is bounded by max_logs.
    assert len(log_entries) <= 2


# ---------------------------------------------------------------------------
# End-to-end: MCP tool layer consumes the PortfolioConfig
# ---------------------------------------------------------------------------


def test_get_context_bundle_consumes_portfolio_config(tmp_path, monkeypatch):
    """``get_context_bundle`` must pull ``max_logs`` / ``log_window_days`` /
    ``bundle_token_budget`` from the loaded portfolio config (SF-3 / A4).
    """
    root = create_workspace(tmp_path)
    # 5 fresh logs in the workspace (within any reasonable window).
    for i in range(5):
        _write_log(root, date.today() - timedelta(days=i), slug=f"n{i}")

    # Override the portfolio config path with one that caps logs at 1.
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """
        [portfolio]
        scan_roots = ["~/Dev"]
        exclude = []
        registry_path = "~/Dev/.dev-hub/registry/projects.json"

        [bundle]
        token_budget = 128000
        max_logs = 1
        log_window_days = 7
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    cache = build_cache(root)
    payload = tool_impl.get_context_bundle(None, cache)
    log_entries = [item for item in payload["included_documents"] if item["score"] == 0.3]
    # The config's max_logs=1 is honored by the tool layer.
    assert len(log_entries) == 1


def test_get_context_bundle_falls_back_to_dataclass_defaults_when_config_absent(tmp_path, monkeypatch):
    """If the portfolio config file is absent, ``get_context_bundle`` must
    fall back to the dataclass defaults rather than crashing (read-only path
    does not write the config — see m-9).
    """
    root = create_workspace(tmp_path)
    missing = tmp_path / ".config-missing" / "ontos" / "portfolio.toml"
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", missing)

    cache = build_cache(root)
    payload = tool_impl.get_context_bundle(None, cache)

    assert "included_documents" in payload
    # File must not have been written as a side effect of a read tool.
    assert not missing.exists()
