"""Tests for v2.7 immutable history generation.

Tests the decision_history.md generation:
- get_log_date() extraction
- parse_log_for_history()
- sort_logs_deterministically()
- generate_decision_history()
"""

import os
import sys
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.ontos', 'scripts'))

from ontos_lib import (
    get_log_date,
    ParsedLog,
    parse_log_for_history,
    sort_logs_deterministically,
    generate_decision_history,
)


class TestGetLogDate:
    """Tests for get_log_date function."""
    
    def test_frontmatter_date_preferred(self, tmp_path):
        """Frontmatter date should be preferred over filename."""
        log_file = tmp_path / "2025-01-01_test.md"
        log_file.write_text("""---
id: test_log
type: log
date: 2025-12-19
---
# Test Log
""")
        result = get_log_date(str(log_file))
        assert result == date(2025, 12, 19)  # From frontmatter, not filename
    
    def test_filename_date_fallback(self, tmp_path):
        """Should fall back to filename date when frontmatter is missing."""
        log_file = tmp_path / "2025-06-15_session.md"
        log_file.write_text("""---
id: test_log
type: log
---
# Test Log
""")
        result = get_log_date(str(log_file))
        assert result == date(2025, 6, 15)  # From filename
    
    def test_datetime_in_frontmatter(self, tmp_path):
        """Should handle datetime objects in frontmatter."""
        log_file = tmp_path / "test.md"
        log_file.write_text("""---
id: test_log
date: 2025-03-10 14:30:00
---
# Test
""")
        # YAML parses this as a datetime
        result = get_log_date(str(log_file))
        assert result is not None


class TestParseLogForHistory:
    """Tests for parse_log_for_history function."""
    
    def test_parses_valid_log(self, tmp_path):
        """Should parse a valid session log."""
        log_file = tmp_path / "2025-12-19_feature.md"
        log_file.write_text("""---
id: log_20251219_feature
type: log
event: feature
impacts: [schema, ontos_lib]
concepts: [describes, staleness]
date: 2025-12-19
---
# Feature Implementation

Implemented the describes field for staleness tracking.
""")
        result = parse_log_for_history(str(log_file))
        
        assert result is not None
        assert result.id == "log_20251219_feature"
        assert result.event_type == "feature"
        assert "schema" in result.impacts
        assert "describes" in result.concepts
        assert result.date == date(2025, 12, 19)
    
    def test_returns_none_for_missing_frontmatter(self, tmp_path):
        """Should return None for files without frontmatter."""
        log_file = tmp_path / "2025-01-01_test.md"
        log_file.write_text("# Just a header\n\nNo frontmatter here.")
        
        result = parse_log_for_history(str(log_file))
        assert result is None
    
    def test_extracts_summary(self, tmp_path):
        """Should extract first paragraph as summary."""
        log_file = tmp_path / "2025-01-01_test.md"
        log_file.write_text("""---
id: test
date: 2025-01-01
---
# Header

This is the summary paragraph.

More content here.
""")
        result = parse_log_for_history(str(log_file))
        assert result is not None
        assert "This is the summary paragraph" in result.summary


class TestSortLogsDeterministically:
    """Tests for sort_logs_deterministically function."""
    
    def test_sorts_by_date_descending(self):
        """Logs should be sorted newest first."""
        logs = [
            ParsedLog("a", "/a", date(2025, 1, 1), "feature", "", [], []),
            ParsedLog("b", "/b", date(2025, 12, 1), "feature", "", [], []),
            ParsedLog("c", "/c", date(2025, 6, 1), "feature", "", [], []),
        ]
        
        sorted_logs = sort_logs_deterministically(logs)
        
        assert sorted_logs[0].id == "b"  # Dec (newest)
        assert sorted_logs[1].id == "c"  # Jun
        assert sorted_logs[2].id == "a"  # Jan (oldest)
    
    def test_sorts_by_event_type_secondary(self):
        """Same date logs should be sorted by event type alphabetically."""
        logs = [
            ParsedLog("a", "/a", date(2025, 1, 1), "feature", "", [], []),
            ParsedLog("b", "/b", date(2025, 1, 1), "chore", "", [], []),
            ParsedLog("c", "/c", date(2025, 1, 1), "fix", "", [], []),
        ]
        
        sorted_logs = sort_logs_deterministically(logs)
        
        assert sorted_logs[0].event_type == "chore"
        assert sorted_logs[1].event_type == "feature"
        assert sorted_logs[2].event_type == "fix"
    
    def test_sorts_by_id_tertiary(self):
        """Same date and type logs should be sorted by ID."""
        logs = [
            ParsedLog("z_log", "/z", date(2025, 1, 1), "feature", "", [], []),
            ParsedLog("a_log", "/a", date(2025, 1, 1), "feature", "", [], []),
            ParsedLog("m_log", "/m", date(2025, 1, 1), "feature", "", [], []),
        ]
        
        sorted_logs = sort_logs_deterministically(logs)
        
        assert sorted_logs[0].id == "a_log"
        assert sorted_logs[1].id == "m_log"
        assert sorted_logs[2].id == "z_log"
    
    def test_deterministic_output(self):
        """Same input should always produce same output."""
        logs = [
            ParsedLog("b", "/b", date(2025, 1, 1), "fix", "", [], []),
            ParsedLog("a", "/a", date(2025, 1, 1), "feature", "", [], []),
        ]
        
        result1 = sort_logs_deterministically(logs.copy())
        result2 = sort_logs_deterministically(logs.copy())
        
        assert [l.id for l in result1] == [l.id for l in result2]


class TestGenerateDecisionHistory:
    """Tests for generate_decision_history function."""
    
    def test_generates_from_logs(self, tmp_path):
        """Should generate markdown from log files."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        
        log1 = logs_dir / "2025-12-19_feature.md"
        log1.write_text("""---
id: log_20251219_feature
event: feature
date: 2025-12-19
---
# Feature

Test feature.
""")
        
        content, warnings = generate_decision_history([str(logs_dir)])
        
        assert "decision_history" in content
        assert "GENERATED FILE" in content
        assert "2025-12-19" in content
        assert "feature" in content
        assert len(warnings) == 0
    
    def test_skips_malformed_logs(self, tmp_path):
        """Should skip malformed logs with warnings."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        
        # Good log
        good_log = logs_dir / "2025-01-01_good.md"
        good_log.write_text("""---
id: good_log
date: 2025-01-01
---
Good log.
""")
        
        # Bad log (no frontmatter)
        bad_log = logs_dir / "2025-01-02_bad.md"
        bad_log.write_text("No frontmatter here")
        
        content, warnings = generate_decision_history([str(logs_dir)])
        
        assert "good_log" in content
        assert len(warnings) == 1
        assert "Skipping malformed log" in warnings[0]
    
    def test_combines_active_and_archived(self, tmp_path):
        """Should combine logs from multiple directories."""
        active_dir = tmp_path / "logs"
        active_dir.mkdir()
        archive_dir = tmp_path / "archive" / "logs"
        archive_dir.mkdir(parents=True)
        
        active_log = active_dir / "2025-12-01_active.md"
        active_log.write_text("""---
id: active_log
date: 2025-12-01
---
Active.
""")
        
        archived_log = archive_dir / "2025-06-01_archived.md"
        archived_log.write_text("""---
id: archived_log
date: 2025-06-01
---
Archived.
""")
        
        content, warnings = generate_decision_history([str(active_dir), str(archive_dir)])
        
        assert "active_log" in content
        assert "archived_log" in content
        # Active should come first (December > June)
        assert content.index("2025-12-01") < content.index("2025-06-01")
    
    def test_writes_to_output_path(self, tmp_path):
        """Should write to output path when specified."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        output_path = output_dir / "decision_history.md"
        
        log = logs_dir / "2025-01-01_test.md"
        log.write_text("""---
id: test
date: 2025-01-01
---
Test.
""")
        
        generate_decision_history([str(logs_dir)], str(output_path))
        
        assert output_path.exists()
        assert "GENERATED FILE" in output_path.read_text()
