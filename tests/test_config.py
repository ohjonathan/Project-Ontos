
import sys
import os
import pytest
from unittest.mock import patch

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../.ontos/scripts')))

from ontos_config import PROJECT_ROOT, SKIP_PATTERNS
from ontos_config_defaults import is_ontos_repo

def test_is_ontos_repo_contributor_mode():
    with patch("os.path.exists") as mock_exists:
        # Mock .ontos-internal existing
        def side_effect(path):
            return '.ontos-internal' in path
        mock_exists.side_effect = side_effect
        assert is_ontos_repo() is True

def test_is_ontos_repo_user_mode():
    with patch("os.path.exists", return_value=False):
        assert is_ontos_repo() is False

def test_skip_patterns_contains_archive():
    assert any('archive/' in p for p in SKIP_PATTERNS)
