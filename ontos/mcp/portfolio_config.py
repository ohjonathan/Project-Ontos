"""Portfolio-mode configuration loading for Ontos MCP."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:  # Python 3.11+
    import tomllib
except ImportError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore


@dataclass(frozen=True)
class PortfolioConfig:
    scan_roots: List[str] = field(default_factory=lambda: ["~/Dev"])
    exclude: List[str] = field(default_factory=lambda: ["~/Dev/.dev-hub", "~/Dev/archive"])
    registry_path: Optional[str] = "~/Dev/.dev-hub/registry/projects.json"
    bundle_token_budget: int = 8000
    bundle_max_logs: int = 20
    bundle_log_window_days: int = 30


PORTFOLIO_CONFIG_PATH = Path.home() / ".config" / "ontos" / "portfolio.toml"

_DEFAULT_CONFIG_TEXT = """[portfolio]
scan_roots = ["~/Dev"]
exclude = ["~/Dev/.dev-hub", "~/Dev/archive"]
registry_path = "~/Dev/.dev-hub/registry/projects.json"

[bundle]
token_budget = 8000
max_logs = 20
log_window_days = 30
"""


def ensure_portfolio_config() -> Path:
    """Ensure the portfolio config file exists on disk; create from defaults if missing.

    This is the *write* path. Callers that only want to read the config should
    either call :func:`ensure_portfolio_config` explicitly first (for init flows)
    or call :func:`load_portfolio_config` directly (which raises if absent).
    """
    PORTFOLIO_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not PORTFOLIO_CONFIG_PATH.exists():
        PORTFOLIO_CONFIG_PATH.write_text(_DEFAULT_CONFIG_TEXT, encoding="utf-8")
    return PORTFOLIO_CONFIG_PATH


def load_portfolio_config() -> PortfolioConfig:
    """Load portfolio config from ~/.config/ontos/portfolio.toml.

    Pure read path: this function never writes to disk. Raises
    :class:`FileNotFoundError` if the config file is absent. Callers that need
    auto-init semantics should call :func:`ensure_portfolio_config` first.
    """
    if not PORTFOLIO_CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Portfolio config not found at {PORTFOLIO_CONFIG_PATH}. "
            "Call ensure_portfolio_config() to write the default, or create it manually."
        )
    with PORTFOLIO_CONFIG_PATH.open("rb") as handle:
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
        bundle_token_budget=_coerce_int(bundle.get("token_budget"), 8000),
        bundle_max_logs=_coerce_int(bundle.get("max_logs"), 20),
        bundle_log_window_days=_coerce_int(bundle.get("log_window_days"), 30),
    )


def _coerce_str_list(value: object, default: List[str]) -> List[str]:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return list(default)


def _coerce_optional_str(value: object, default: Optional[str]) -> Optional[str]:
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
