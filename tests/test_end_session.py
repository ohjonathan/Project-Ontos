
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
    """Test that create_log_file buffers a write via SessionContext.
    
    v2.8.3: With _owns_ctx pattern, commit should NOT be called when ctx is passed.
    The caller (main()) is responsible for committing.
    """
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
        # v2.8.3: With _owns_ctx pattern, commit should NOT be called when ctx is passed
        mock_ctx.commit.assert_not_called() 

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


# ============================================================================
# v2.8.3 Transaction Composability Tests (per Chief Architect)
# ============================================================================

def test_main_commits_all_files_atomically():
    """main() should create SessionContext and commit all buffered writes atomically."""
    import ontos_end_session
    
    mock_ctx = MagicMock()
    mock_ctx.buffer_write = MagicMock()
    mock_ctx.commit = MagicMock()
    mock_ctx.rollback = MagicMock()
    
    with patch("ontos_end_session.SessionContext") as MockSessionContext, \
         patch("ontos_end_session.OutputHandler") as MockOutput, \
         patch("os.path.exists", return_value=False), \
         patch("os.makedirs"), \
         patch("ontos_end_session.get_session_git_log", return_value="abc123 - test"), \
         patch("ontos_end_session._create_archive_marker"), \
         patch.object(sys, 'argv', ['ontos_end_session.py', 'test-topic', '-s', 'test', '-e', 'chore', '-q']):
        
        MockSessionContext.from_repo.return_value = mock_ctx
        mock_output = MagicMock()
        MockOutput.return_value = mock_output
        
        # Should complete without error when commit succeeds
        try:
            ontos_end_session.main()
        except SystemExit:
            pass  # Expected for normal exit
        
        # Should have called commit
        mock_ctx.commit.assert_called()


def test_main_rollback_on_commit_failure():
    """main() should call rollback when commit fails."""
    import ontos_end_session
    
    mock_ctx = MagicMock()
    mock_ctx.buffer_write = MagicMock()
    mock_ctx.commit = MagicMock(side_effect=IOError("Disk full"))
    mock_ctx.rollback = MagicMock()
    
    with patch("ontos_end_session.SessionContext") as MockSessionContext, \
         patch("ontos_end_session.OutputHandler") as MockOutput, \
         patch("os.path.exists", return_value=False), \
         patch("os.makedirs"), \
         patch("ontos_end_session.get_session_git_log", return_value="abc123 - test"), \
         patch("ontos_end_session._create_archive_marker"), \
         patch.object(sys, 'argv', ['ontos_end_session.py', 'test-topic', '-s', 'test', '-e', 'chore', '-q']):
        
        MockSessionContext.from_repo.return_value = mock_ctx
        mock_output = MagicMock()
        MockOutput.return_value = mock_output
        
        with pytest.raises(SystemExit) as exc_info:
            ontos_end_session.main()
        
        # Should exit with error code
        assert exc_info.value.code == 1
        # Should have called rollback
        mock_ctx.rollback.assert_called()


def test_graduate_proposal_uses_buffer_write(tmp_path):
    """graduate_proposal() should use buffer_write and buffer_delete, not direct I/O."""
    from ontos_end_session import graduate_proposal
    
    # Setup mock proposal
    proposals_dir = tmp_path / "proposals"
    proposals_dir.mkdir()
    proposal_file = proposals_dir / "test_proposal.md"
    proposal_file.write_text("---\nid: test\nstatus: draft\n---\n# Test")
    
    mock_ctx = MagicMock()
    mock_ctx.buffer_write = MagicMock()
    mock_ctx.buffer_delete = MagicMock()
    mock_ctx.commit = MagicMock()
    
    with patch("ontos_end_session.get_proposals_dir", return_value=str(proposals_dir)), \
         patch("ontos_end_session.get_decision_history_path", return_value=None):
        
        result = graduate_proposal(
            {'id': 'test', 'filepath': str(proposal_file), 'version': '1.0'},
            quiet=True,
            ctx=mock_ctx
        )
    
    assert result is True
    # Should use buffer_write for new file
    mock_ctx.buffer_write.assert_called()
    # Should use buffer_delete for original file
    mock_ctx.buffer_delete.assert_called_once()
    # Should NOT commit (ctx was passed, so _owns_ctx is False)
    mock_ctx.commit.assert_not_called()


def test_append_to_log_uses_buffer_write(tmp_path):
    """append_to_log() should buffer writes, not write directly."""
    from ontos_end_session import append_to_log
    from ontos.ui.output import OutputHandler
    
    # Create test log file
    log_file = tmp_path / "test.md"
    log_file.write_text("""## Raw Session History
```text
abc123 - old commit
```
""")
    
    mock_ctx = MagicMock()
    mock_ctx.buffer_write = MagicMock()
    mock_ctx.commit = MagicMock()
    
    output = OutputHandler(quiet=True)
    
    result = append_to_log(
        str(log_file),
        ['def456 - new commit'],
        output=output,
        ctx=mock_ctx
    )
    
    assert result is True
    mock_ctx.buffer_write.assert_called_once()
    # Should NOT commit when ctx is passed
    mock_ctx.commit.assert_not_called()


def test_create_changelog_uses_buffer_write():
    """create_changelog() should buffer writes, not write directly."""
    from ontos_end_session import create_changelog
    from ontos.ui.output import OutputHandler
    
    mock_ctx = MagicMock()
    mock_ctx.buffer_write = MagicMock()
    mock_ctx.commit = MagicMock()
    
    output = OutputHandler(quiet=True)
    
    result = create_changelog(output=output, ctx=mock_ctx)
    
    assert result == "CHANGELOG.md"
    mock_ctx.buffer_write.assert_called_once()
    # Should NOT commit when ctx is passed
    mock_ctx.commit.assert_not_called()
