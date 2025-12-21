
import sys
import os
import pytest
from unittest.mock import patch, mock_open

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../.ontos/scripts')))

from ontos_consolidate import (
    extract_summary,
    append_to_decision_history,
    HISTORY_LEDGER_HEADER
)

def test_extract_summary_from_goal_section():
    content = "## Goal\nSummary line.\n\n## Next"
    with patch("builtins.open", mock_open(read_data=content)):
        summary = extract_summary("dummy.md")
        assert summary == "Summary line."

def test_extract_summary_different_numbering():
    content = "## 1. Goal\nSummary line.\n\n## 2. Next"
    with patch("builtins.open", mock_open(read_data=content)):
        summary = extract_summary("dummy.md")
        assert summary == "Summary line."

def test_extract_summary_missing_returns_none():
    content = "No goal section"
    with patch("builtins.open", mock_open(read_data=content)):
        summary = extract_summary("dummy.md")
        assert summary is None

def test_validate_decision_history_missing():
    with patch("os.path.exists", return_value=False):
        from ontos_consolidate import validate_decision_history
        assert validate_decision_history() is False

def test_append_targets_history_ledger_not_consolidation_log():
    """Test that new rows are inserted into History Ledger, not Consolidation Log.
    
    v2.8.4: Updated to mock buffer_write since append_to_decision_history now
    uses SessionContext transactional writes instead of direct file writes.
    """
    from unittest.mock import MagicMock
    
    # Setup content with both tables
    content = """# Decision History

## History Ledger

| Date | Slug | Event | Decision / Outcome |
|:---|:---|:---|:---|
| 2023-01-01 | old | chore | old |

## Consolidation Log

| Date | Sessions |
|:---|:---|
"""
    mock_ctx = MagicMock()
    mock_ctx.buffer_write = MagicMock()
    mock_ctx.commit = MagicMock()
    
    with patch("ontos_consolidate.validate_decision_history", return_value=True), \
         patch("builtins.open", mock_open(read_data=content)):
        
        # Pass ctx so _owns_ctx is False (no commit called by function)
        append_to_decision_history("2025-01-01", "new", "chore", "summary", [], "archive/new.md", ctx=mock_ctx)
        
        # Verify buffer_write was called
        mock_ctx.buffer_write.assert_called_once()
        
        # Get the written content
        written = mock_ctx.buffer_write.call_args[0][1]
        
        # New row should be inserted after the last row of History Ledger
        # i.e., before ## Consolidation Log
        expected_row = "| 2025-01-01 | new | chore | summary | — | `archive/new.md` |"
        assert expected_row in written
        
        # Ensure it's in the right place (simple check: it appears before Consolidation Log header)
        pos_row = written.find(expected_row)
        pos_header = written.find("## Consolidation Log")
        assert pos_row < pos_header
        
        # Verify commit was NOT called (we passed ctx, so it's not owned)
        mock_ctx.commit.assert_not_called()

