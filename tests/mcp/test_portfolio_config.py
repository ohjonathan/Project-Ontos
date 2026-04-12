from __future__ import annotations

from pathlib import Path

import pytest

import ontos.mcp.portfolio_config as portfolio_config_module
from ontos.mcp.portfolio_config import ensure_portfolio_config, load_portfolio_config


def test_load_portfolio_config_creates_defaults_when_missing(tmp_path, monkeypatch):
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    cfg = load_portfolio_config()

    assert config_path.exists()
    assert cfg.scan_roots == ["~/Dev"]
    assert cfg.exclude == ["~/Dev/.dev-hub", "~/Dev/archive"]
    assert cfg.registry_path == "~/Dev/.dev-hub/registry/projects.json"
    assert cfg.bundle_token_budget == 8192
    assert cfg.bundle_max_logs == 5
    assert cfg.bundle_log_window_days == 14


def test_load_portfolio_config_custom_values(tmp_path, monkeypatch):
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """
        [portfolio]
        scan_roots = ["~/Dev", "~/Work"]
        exclude = ["~/Dev/archive"]
        registry_path = "~/Dev/.dev-hub/registry/projects.json"

        [bundle]
        token_budget = 4000
        max_logs = 7
        log_window_days = 3
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    cfg = load_portfolio_config()

    assert cfg.scan_roots == ["~/Dev", "~/Work"]
    assert cfg.exclude == ["~/Dev/archive"]
    assert cfg.registry_path == "~/Dev/.dev-hub/registry/projects.json"
    assert cfg.bundle_token_budget == 4000
    assert cfg.bundle_max_logs == 7
    assert cfg.bundle_log_window_days == 3


def test_load_portfolio_config_invalid_toml_raises(tmp_path, monkeypatch):
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("[portfolio\nscan_roots = [\"~/Dev\"]\n", encoding="utf-8")
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    with pytest.raises(ValueError):
        load_portfolio_config()


def test_ensure_portfolio_config_is_idempotent(tmp_path, monkeypatch):
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    first = ensure_portfolio_config()
    second = ensure_portfolio_config()

    assert first == Path(config_path)
    assert second == Path(config_path)
    assert config_path.exists()

