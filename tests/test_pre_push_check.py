
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../.ontos/scripts')))

from ontos_pre_push_check import (
    MARKER_FILE,
    get_change_stats,
    suggest_related_docs,
    main
)

def test_marker_exists_allows_push():
    with patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove:
        assert main() == 0
        mock_remove.assert_called_with(MARKER_FILE)

def test_change_stats_parses_git_diff():
    output = " file1.py | 10 +\n file2.md | 5 -\n 2 files changed, 10 insertions(+), 5 deletions(-)"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = output
        files, lines, changed = get_change_stats()
        assert files == 2
        assert lines == 15
        assert "file1.py" in changed
        assert "file2.md" in changed

def test_change_stats_git_fail():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        files, lines, changed = get_change_stats()
        assert files == 0

def test_suggest_related_docs_from_filenames():
    suggestions = suggest_related_docs(["docs/auth.md", "src/auth_handler.py"])
    assert "auth" in suggestions
    assert "auth_handler" in suggestions

def test_small_change_shows_soft_message():
    # Mock small change and check if it returns 1 (since default is blocking mode)
    # But wait, pre-push hook logic:
    # if lines < threshold: print_small_change_message; return 1
    # unless advisory mode. Default ENFORCE_ARCHIVE_BEFORE_PUSH is True.
    # So it should return 1.
    with patch("os.path.exists", return_value=False), \
         patch("ontos_pre_push_check.get_change_stats", return_value=(1, 5, ["file"])), \
         patch("ontos_pre_push_check.SMALL_CHANGE_THRESHOLD", 20):
        # We also need to patch open or such if main does print? 
        # main calls print functions. We don't need to assert output, just return code.
        assert main() == 1

def test_advisory_mode_always_allows():
    with patch("os.path.exists", return_value=False), \
         patch("ontos_pre_push_check.get_change_stats", return_value=(1, 100, ["file"])), \
         patch("ontos_pre_push_check.ENFORCE_ARCHIVE_BEFORE_PUSH", False):
        assert main() == 0
