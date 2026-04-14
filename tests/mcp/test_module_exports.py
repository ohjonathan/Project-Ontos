from __future__ import annotations

import ontos.mcp.bundler as bundler_module
import ontos.mcp.portfolio as portfolio_module
import ontos.mcp.portfolio_config as portfolio_config_module
import ontos.mcp.scanner as scanner_module


def test_portfolio_module_all_exports_public_surface():
    assert sorted(portfolio_module.__all__) == ["PortfolioIndex"]
    assert "_sanitize_fts_query" not in portfolio_module.__all__


def test_scanner_module_all_exports_public_surface():
    assert sorted(scanner_module.__all__) == sorted(
        [
            "ProjectEntry",
            "RegistryRecord",
            "slugify",
            "discover_projects",
            "load_registry_records",
            "allocate_slug",
        ]
    )
    assert "_allocate_slug" not in scanner_module.__all__
    assert "_load_registry_records" not in scanner_module.__all__


def test_bundler_module_all_exports_public_surface():
    assert sorted(bundler_module.__all__) == sorted(["BundleDocument", "build_context_bundle"])
    assert "_build_priority_order" not in bundler_module.__all__
    assert "_to_bundle_doc" not in bundler_module.__all__


def test_portfolio_config_module_all_exports_public_surface():
    assert sorted(portfolio_config_module.__all__) == sorted(
        [
            "PortfolioConfig",
            "PORTFOLIO_CONFIG_PATH",
            "ensure_portfolio_config",
            "load_portfolio_config",
        ]
    )
