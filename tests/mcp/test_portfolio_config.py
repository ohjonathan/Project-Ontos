from __future__ import annotations

from pathlib import Path

import pytest

import ontos.mcp.portfolio_config as portfolio_config_module
from ontos.mcp.portfolio_config import ensure_portfolio_config, load_portfolio_config


def test_load_portfolio_config_raises_when_missing(tmp_path, monkeypatch):
    """m-9: load_portfolio_config() is now a pure read path.

    It must never write to disk. If the config file is absent the caller is
    expected to invoke ensure_portfolio_config() explicitly (init flow).
    """
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    with pytest.raises(FileNotFoundError):
        load_portfolio_config()

    # And it must not have been created as a side effect.
    assert not config_path.exists()


def test_ensure_portfolio_config_then_load_returns_addendum_defaults(tmp_path, monkeypatch):
    """m-9 + addendum A4 defaults: init path writes, load path reads."""
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    ensure_portfolio_config()
    cfg = load_portfolio_config()

    assert config_path.exists()
    assert cfg.scan_roots == ["~/Dev"]
    assert cfg.exclude == ["~/Dev/.dev-hub", "~/Dev/archive"]
    assert cfg.registry_path == "~/Dev/.dev-hub/registry/projects.json"
    # Addendum v1.2 §A4 default values (Dev 4 updated these from 8192/5/14).
    assert cfg.bundle_token_budget == 8000
    assert cfg.bundle_max_logs == 20
    assert cfg.bundle_log_window_days == 30


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


def test_load_portfolio_config_missing_registry_path_uses_default(tmp_path, monkeypatch):
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """
        [portfolio]
        scan_roots = ["~/Dev"]
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    cfg = load_portfolio_config()

    assert cfg.registry_path == "~/Dev/.dev-hub/registry/projects.json"


def test_load_portfolio_config_empty_registry_path_disables_merge(tmp_path, monkeypatch):
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """
        [portfolio]
        registry_path = ""
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    cfg = load_portfolio_config()

    assert cfg.registry_path is None


def test_load_portfolio_config_whitespace_registry_path_disables_merge(tmp_path, monkeypatch):
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """
        [portfolio]
        registry_path = "   "
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    cfg = load_portfolio_config()

    assert cfg.registry_path is None


def test_load_portfolio_config_strips_outer_whitespace_from_registry_path(tmp_path, monkeypatch):
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """
        [portfolio]
        registry_path = "   ~/Dev/custom-registry.json   "
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    cfg = load_portfolio_config()

    assert cfg.registry_path == "~/Dev/custom-registry.json"


def test_load_portfolio_config_non_string_registry_path_falls_back_to_default(tmp_path, monkeypatch):
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """
        [portfolio]
        registry_path = 42
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    cfg = load_portfolio_config()

    assert cfg.registry_path == "~/Dev/.dev-hub/registry/projects.json"


def test_load_portfolio_config_non_string_registry_path_warns_and_falls_back_to_default(
    tmp_path,
    monkeypatch,
    caplog,
):
    config_path = tmp_path / ".config" / "ontos" / "portfolio.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """
        [portfolio]
        registry_path = true
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(portfolio_config_module, "PORTFOLIO_CONFIG_PATH", config_path)

    with caplog.at_level("WARNING"):
        cfg = load_portfolio_config()

    assert cfg.registry_path == "~/Dev/.dev-hub/registry/projects.json"
    assert "Ignoring non-string portfolio.registry_path value" in caplog.text


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
