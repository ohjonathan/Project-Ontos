"""Portfolio-mode configuration loading for Ontos MCP."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
from typing import List, Optional

try:  # Python 3.11+
    import tomllib
except ImportError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore

__all__ = [
    "DEFAULT_BUNDLE_LOG_WINDOW_DAYS",
    "DEFAULT_BUNDLE_MAX_LOGS",
    "DEFAULT_BUNDLE_TOKEN_BUDGET",
    "PortfolioConfig",
    "PORTFOLIO_CONFIG_PATH",
    "ensure_portfolio_config",
    "load_portfolio_config",
]

logger = logging.getLogger(__name__)

DEFAULT_BUNDLE_TOKEN_BUDGET = 8_000
DEFAULT_BUNDLE_MAX_LOGS = 20
DEFAULT_BUNDLE_LOG_WINDOW_DAYS = 30

_DEFAULT_REGISTRY_PATH: Optional[str] = None
_REGISTRY_PATH_EDGE_CHARS = "\u200b\u200c\u200d\ufeff"
_MISSING = object()


@dataclass(frozen=True)
class PortfolioConfig:
    scan_roots: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)
    registry_path: Optional[str] = _DEFAULT_REGISTRY_PATH
    bundle_token_budget: int = DEFAULT_BUNDLE_TOKEN_BUDGET
    bundle_max_logs: int = DEFAULT_BUNDLE_MAX_LOGS
    bundle_log_window_days: int = DEFAULT_BUNDLE_LOG_WINDOW_DAYS


PORTFOLIO_CONFIG_PATH = Path.home() / ".config" / "ontos" / "portfolio.toml"

_DEFAULT_CONFIG_TEXT = f"""[portfolio]
scan_roots = []
exclude = []
registry_path = ""

[bundle]
token_budget = {DEFAULT_BUNDLE_TOKEN_BUDGET}
max_logs = {DEFAULT_BUNDLE_MAX_LOGS}
log_window_days = {DEFAULT_BUNDLE_LOG_WINDOW_DAYS}
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
        scan_roots=_coerce_str_list(portfolio.get("scan_roots"), []),
        exclude=_coerce_str_list(portfolio.get("exclude"), []),
        registry_path=_coerce_registry_path(
            portfolio.get("registry_path", _MISSING),
            _DEFAULT_REGISTRY_PATH,
        ),
        bundle_token_budget=_coerce_int(
            bundle.get("token_budget"),
            DEFAULT_BUNDLE_TOKEN_BUDGET,
        ),
        bundle_max_logs=_coerce_int(
            bundle.get("max_logs"),
            DEFAULT_BUNDLE_MAX_LOGS,
        ),
        bundle_log_window_days=_coerce_int(
            bundle.get("log_window_days"),
            DEFAULT_BUNDLE_LOG_WINDOW_DAYS,
        ),
    )


def _coerce_str_list(value: object, default: List[str]) -> List[str]:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return list(default)


def _coerce_registry_path(
    value: object,
    default: Optional[str],
) -> Optional[str]:
    if value is _MISSING:
        return default
    if isinstance(value, os.PathLike):
        value = os.fspath(value)
    if isinstance(value, str):
        stripped = _strip_registry_path_edges(value)
        return stripped or None
    logger.warning(
        "Ignoring non-string portfolio.registry_path value %r; using default.",
        value,
    )
    return default


def _strip_registry_path_edges(value: str) -> str:
    start = 0
    end = len(value)

    while start < end and (value[start].isspace() or value[start] in _REGISTRY_PATH_EDGE_CHARS):
        start += 1
    while end > start and (value[end - 1].isspace() or value[end - 1] in _REGISTRY_PATH_EDGE_CHARS):
        end -= 1

    return value[start:end]


def _coerce_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    return default
