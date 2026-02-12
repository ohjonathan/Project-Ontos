"""Pytest configuration for legacy scripts tests."""

import warnings

import pytest


def pytest_configure(config):
    """Configure pytest warning filters for deprecation tests."""
    # v2.9.2: Show FutureWarnings from ontos modules
    warnings.filterwarnings(
        "always",
        category=FutureWarning,
        module=r"ontos.*"
    )

    # Suppress the ontos_lib deprecation warning in tests
    # (tests may intentionally import from ontos_lib to test the shim)
    warnings.filterwarnings(
        "ignore",
        message="Importing from 'ontos_lib' is deprecated",
        category=FutureWarning,
    )


def pytest_collection_modifyitems(items):
    """Auto-mark all tests in this directory as legacy."""
    legacy_marker = pytest.mark.legacy
    for item in items:
        item.add_marker(legacy_marker)
