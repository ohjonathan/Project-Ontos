"""Tests for v2.8.4 refactoring.

Verifies:
1. Write functions use buffer_write instead of direct file writes
2. Code deduplication - functions imported rather than duplicated
"""

import sys
import os
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../.ontos/scripts')))


class TestUpdateDescribesVerifiedUsesBufferWrite:
    """Test that update_describes_verified uses buffer_write (v2.8 pattern)."""
    
    def test_update_describes_verified_uses_buffer_write(self, tmp_path):
        """Verify update_describes_verified uses ctx.buffer_write instead of direct file write."""
        from ontos_verify import update_describes_verified
        from datetime import date
        
        # Setup: create a test document with frontmatter
        test_content = """---
id: test_doc
describes:
  - some_code
---

# Test Document
"""
        test_file = tmp_path / "test_doc.md"
        test_file.write_text(test_content)
        
        mock_ctx = MagicMock()
        mock_ctx.buffer_write = MagicMock()
        mock_ctx.commit = MagicMock()
        
        # Act: call update_describes_verified with mock context
        result = update_describes_verified(
            str(test_file),
            date(2025, 1, 15),
            ctx=mock_ctx
        )
        
        # Assert: buffer_write was called, not direct file write
        assert result is True
        mock_ctx.buffer_write.assert_called_once()
        
        # Verify the content contains the new date
        written_content = mock_ctx.buffer_write.call_args[0][1]
        assert "describes_verified: 2025-01-15" in written_content
        
        # Verify commit was NOT called (ctx was passed, so function doesn't own it)
        mock_ctx.commit.assert_not_called()
    
    def test_update_describes_verified_owns_ctx_when_none_passed(self, tmp_path):
        """Verify _owns_ctx pattern: commits when ctx is None."""
        from ontos_verify import update_describes_verified
        from datetime import date
        
        test_content = """---
id: test_doc
describes:
  - some_code
---

# Test Document
"""
        test_file = tmp_path / "test_doc.md"
        test_file.write_text(test_content)
        
        # Mock SessionContext.from_repo to return our mock
        mock_ctx = MagicMock()
        mock_ctx.buffer_write = MagicMock()
        mock_ctx.commit = MagicMock()
        
        with patch('ontos_verify.SessionContext.from_repo', return_value=mock_ctx):
            result = update_describes_verified(
                str(test_file),
                date(2025, 1, 15),
                ctx=None  # Function should create and own context
            )
        
        assert result is True
        mock_ctx.buffer_write.assert_called_once()
        # When _owns_ctx is True, commit should be called
        mock_ctx.commit.assert_called_once()


class TestGraduateProposalDeduplication:
    """Test that graduate_proposal is imported from ontos_end_session, not duplicated."""
    
    def test_graduate_proposal_is_imported_not_duplicated(self):
        """Verify ontos_maintain imports graduate_proposal from ontos_end_session."""
        import ontos_maintain
        import ontos_end_session
        
        # The function should be the same object (imported, not defined separately)
        assert hasattr(ontos_maintain, 'graduate_proposal')
        assert hasattr(ontos_end_session, 'graduate_proposal')
        
        # Verify they are the same function (not just same name)
        assert ontos_maintain.graduate_proposal is ontos_end_session.graduate_proposal
    
    def test_add_graduation_to_ledger_not_in_maintain(self):
        """Verify add_graduation_to_ledger is NOT duplicated in ontos_maintain."""
        import ontos_maintain
        
        # add_graduation_to_ledger should NOT be defined in ontos_maintain
        # (it's called internally by graduate_proposal in ontos_end_session)
        assert not hasattr(ontos_maintain, 'add_graduation_to_ledger')


class TestAppendToDecisionHistoryBufferWrite:
    """Test that append_to_decision_history uses buffer_write."""
    
    def test_append_to_decision_history_uses_buffer_write(self, tmp_path):
        """Verify append_to_decision_history uses ctx.buffer_write."""
        from ontos_consolidate import append_to_decision_history
        
        # Create minimal decision_history.md
        history_content = """# Decision History

## History Ledger
| Date | Slug | Event | Decision / Outcome |
|:---|:---|:---|:---|
"""
        history_file = tmp_path / "decision_history.md"
        history_file.write_text(history_content)
        
        mock_ctx = MagicMock()
        mock_ctx.buffer_write = MagicMock()
        mock_ctx.commit = MagicMock()
        
        with patch('ontos_consolidate.DECISION_HISTORY_FILE', str(history_file)), \
             patch('ontos_consolidate.validate_decision_history', return_value=True):
            
            result = append_to_decision_history(
                "2025-01-01", "test-slug", "chore", "Test summary",
                ["impact1"], "archive/test.md",
                ctx=mock_ctx
            )
        
        assert result is True
        mock_ctx.buffer_write.assert_called_once()
        mock_ctx.commit.assert_not_called()  # ctx was passed, so no commit
