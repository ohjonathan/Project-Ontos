"""Pytest configuration for scripts tests."""

import warnings


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
