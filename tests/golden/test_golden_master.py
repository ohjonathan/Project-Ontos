"""Pytest wrapper for golden master tests.

This module makes golden master tests discoverable by pytest.
The actual golden master comparison is done by compare_golden_master.py.
"""

import subprocess
import sys
from pathlib import Path

import pytest


GOLDEN_DIR = Path(__file__).parent


class TestGoldenMaster:
    """Golden master test suite."""

    def test_golden_small_fixture(self):
        """Validate golden master for small fixture."""
        result = subprocess.run(
            [sys.executable, str(GOLDEN_DIR / 'compare_golden_master.py'), '--fixture', 'small'],
            capture_output=True,
            text=True,
            cwd=str(GOLDEN_DIR.parent.parent)  # Project root
        )
        if result.returncode != 0:
            pytest.fail(f"Golden master comparison failed for 'small' fixture:\n{result.stdout}\n{result.stderr}")

    def test_golden_medium_fixture(self):
        """Validate golden master for medium fixture."""
        result = subprocess.run(
            [sys.executable, str(GOLDEN_DIR / 'compare_golden_master.py'), '--fixture', 'medium'],
            capture_output=True,
            text=True,
            cwd=str(GOLDEN_DIR.parent.parent)  # Project root
        )
        if result.returncode != 0:
            pytest.fail(f"Golden master comparison failed for 'medium' fixture:\n{result.stdout}\n{result.stderr}")
