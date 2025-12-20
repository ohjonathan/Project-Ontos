
import sys
import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../.ontos/scripts')))

import ontos_end_session
from ontos_end_session import TEMPLATES, generate_auto_slug, validate_topic_slug, create_log_file, validate_concepts

def test_adaptive_template_chore_has_two_sections():
    assert len(TEMPLATES['chore']['sections']) == 2
    assert 'Goal' in TEMPLATES['chore']['sections']
    assert 'Changes Made' in TEMPLATES['chore']['sections']

def test_adaptive_template_decision_has_five_sections():
    assert len(TEMPLATES['decision']['sections']) == 5

def test_adaptive_template_feature_has_four_sections():
    assert len(TEMPLATES['feature']['sections']) == 4

def test_validate_topic_slug_valid():
    is_valid, msg = validate_topic_slug("valid-slug-123")
    assert is_valid is True

def test_validate_topic_slug_invalid():
    is_valid, msg = validate_topic_slug("Invalid Slug")
    assert is_valid is False

def test_auto_slug_from_branch_name():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "feature/test-branch"
        slug = generate_auto_slug()
        assert slug == "test-branch"

def test_auto_slug_blocks_main_master_dev():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "main"
        # First call fails (branch blocked), second call (commit fallback) fails (mocked to fail)
        # We need to mock the second subprocess call to fail or return nothing
        
        # Better: check that it calls commit logic if branch logic fails?
        # But here we just want to assert it doesn't return "main"
        # Since we mock only one return value, subsequent calls return same mock unless side_effect used
        # If we use side_effect for multiple calls:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main"), # Branch check
            MagicMock(returncode=1) # Commit check
        ]
        slug = generate_auto_slug()
        assert slug is None

def test_auto_slug_from_commit_message():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=1), # Branch check fails
            MagicMock(returncode=0, stdout="Fix bug #123") # Commit check succeeds
        ]
        slug = generate_auto_slug()
        assert slug == "fix-bug-123"

def test_auto_slug_returns_none_when_all_fail():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        slug = generate_auto_slug()
        assert slug is None

def test_create_log_file_creates_file():
    """Test that create_log_file buffers a write via SessionContext."""
    mock_ctx = MagicMock()
    mock_ctx.buffer_write = MagicMock()
    mock_ctx.commit = MagicMock()
    
    with patch("os.path.exists", return_value=False), \
         patch("os.makedirs"), \
         patch("ontos_end_session.get_session_git_log", return_value="log"), \
         patch("ontos_end_session._create_archive_marker"):
        
        filepath = create_log_file("test-slug", quiet=True, source="test", ctx=mock_ctx)
        assert filepath.endswith("_test-slug.md")
        mock_ctx.buffer_write.assert_called_once()
        mock_ctx.commit.assert_called_once() 

def test_concept_validation_warns_unknown():
    with patch("ontos_end_session.load_common_concepts", return_value={"valid"}), \
         patch("builtins.print") as mock_print:
        
        validated = validate_concepts(["valid", "unknown"], quiet=False)
        assert "valid" in validated
        assert "unknown" in validated # Still includes it
        
        # Check that warning was printed
        # We need to check if any of the print calls contained "Unknown concept"
        warning_printed = any("Unknown concept" in str(arg) for call in mock_print.call_args_list for arg in call[0])
        assert warning_printed

def test_concept_validation_suggests_similar():
    with patch("ontos_end_session.load_common_concepts", return_value={"authentication"}), \
         patch("builtins.print") as mock_print:
        
        validate_concepts(["auth"], quiet=False)
        # Should suggest "authentication"
        suggestion_printed = any("Did you mean: authentication" in str(arg) for call in mock_print.call_args_list for arg in call[0])
        assert suggestion_printed
