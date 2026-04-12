"""Portfolio-mode configuration loading for Ontos MCP."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ImportError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore


@dataclass(frozen=True)
class PortfolioConfig:
    scan_roots: list[str] = field(default_factory=lambda: ["~/Dev"])
    exclude: list[str] = field(default_factory=lambda: ["~/Dev/.dev-hub", "~/Dev/archive"])
    registry_path: str | None = "~/Dev/.dev-hub/registry/projects.json"
    bundle_token_budget: int = 8192
    bundle_max_logs: int = 5
    bundle_log_window_days: int = 14


PORTFOLIO_CONFIG_PATH = Path.home() / ".config" / "ontos" / "portfolio.toml"

_DEFAULT_CONFIG_TEXT = """[portfolio]
scan_roots = ["~/Dev"]
exclude = ["~/Dev/.dev-hub", "~/Dev/archive"]
registry_path = "~/Dev/.dev-hub/registry/projects.json"

[bundle]
token_budget = 8192
max_logs = 5
log_window_days = 14
"""


def ensure_portfolio_config() -> Path:
    """Ensure the portfolio config file exists and return its path."""
    PORTFOLIO_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not PORTFOLIO_CONFIG_PATH.exists():
        PORTFOLIO_CONFIG_PATH.write_text(_DEFAULT_CONFIG_TEXT, encoding="utf-8")
    return PORTFOLIO_CONFIG_PATH


def load_portfolio_config() -> PortfolioConfig:
    """Load portfolio config from ~/.config/ontos/portfolio.toml."""
    config_path = ensure_portfolio_config()
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)

    portfolio = data.get("portfolio", {}) if isinstance(data, dict) else {}
    bundle = data.get("bundle", {}) if isinstance(data, dict) else {}
    if not isinstance(portfolio, dict):
        portfolio = {}
    if not isinstance(bundle, dict):
        bundle = {}

    return PortfolioConfig(
        scan_roots=_coerce_str_list(portfolio.get("scan_roots"), ["~/Dev"]),
        exclude=_coerce_str_list(portfolio.get("exclude"), ["~/Dev/.dev-hub", "~/Dev/archive"]),
        registry_path=_coerce_optional_str(portfolio.get("registry_path"), "~/Dev/.dev-hub/registry/projects.json"),
        bundle_token_budget=_coerce_int(bundle.get("token_budget"), 8192),
        bundle_max_logs=_coerce_int(bundle.get("max_logs"), 5),
        bundle_log_window_days=_coerce_int(bundle.get("log_window_days"), 14),
    )


def _coerce_str_list(value: object, default: list[str]) -> list[str]:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return list(default)


def _coerce_optional_str(value: object, default: str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return default


def _coerce_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    return default

