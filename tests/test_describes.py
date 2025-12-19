"""Tests for v2.7 describes field functionality.

Tests the staleness detection features:
- ModifiedSource enum
- get_file_modification_date() with caching
- normalize_describes() and parse_describes_verified()
- validate_describes_field()
- detect_describes_cycles()
- check_staleness()
"""

import os
import sys
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.ontos', 'scripts'))

from ontos_lib import (
    ModifiedSource,
    clear_git_cache,
    get_file_modification_date,
    normalize_describes,
    parse_describes_verified,
    DescribesValidationError,
    DescribesWarning,
    StalenessInfo,
    validate_describes_field,
    detect_describes_cycles,
    check_staleness,
)


class TestModifiedSource:
    """Tests for ModifiedSource enum."""
    
    def test_enum_values_exist(self):
        """Verify all expected enum values exist."""
        assert ModifiedSource.GIT.value == "git"
        assert ModifiedSource.MTIME.value == "mtime"
        assert ModifiedSource.UNCOMMITTED.value == "uncommitted"
        assert ModifiedSource.MISSING.value == "missing"


class TestNormalizeDescribes:
    """Tests for normalize_describes function."""
    
    def test_none_returns_empty_list(self):
        assert normalize_describes(None) == []
    
    def test_empty_string_returns_empty_list(self):
        assert normalize_describes("") == []
        assert normalize_describes("   ") == []
    
    def test_single_string_returns_list(self):
        assert normalize_describes("atom_id") == ["atom_id"]
    
    def test_list_returns_list(self):
        assert normalize_describes(["a", "b", "c"]) == ["a", "b", "c"]
    
    def test_list_with_none_filters(self):
        assert normalize_describes(["a", None, "b"]) == ["a", "b"]
    
    def test_list_with_empty_strings_filters(self):
        assert normalize_describes(["a", "", "b"]) == ["a", "b"]


class TestParseDescribesVerified:
    """Tests for parse_describes_verified function."""
    
    def test_none_returns_none(self):
        assert parse_describes_verified(None) is None
    
    def test_valid_date_string(self):
        result = parse_describes_verified("2025-12-19")
        assert result == date(2025, 12, 19)
    
    def test_date_object(self):
        d = date(2025, 1, 15)
        assert parse_describes_verified(d) == d
    
    def test_datetime_object_extracts_date(self):
        dt = datetime(2025, 1, 15, 10, 30)
        assert parse_describes_verified(dt) == date(2025, 1, 15)
    
    def test_invalid_date_string_returns_none(self):
        assert parse_describes_verified("not-a-date") is None
        assert parse_describes_verified("Dec 18 2025") is None


class TestValidateDescribesField:
    """Tests for validate_describes_field function."""
    
    def setup_method(self):
        """Create test fixtures."""
        self.all_docs = {
            "atom_a": {"type": "atom", "path": "docs/atom_a.md"},
            "atom_b": {"type": "atom", "path": "docs/atom_b.md"},
            "strategy_x": {"type": "strategy", "path": "docs/strategy_x.md"},
        }
    
    def test_empty_describes_no_errors(self):
        """Empty describes field should not cause errors."""
        errors, warnings = validate_describes_field(
            doc_id="doc1",
            doc_path="docs/doc1.md",
            doc_type="atom",
            describes=[],
            describes_verified=None,
            all_docs=self.all_docs
        )
        assert len(errors) == 0
    
    def test_non_atom_can_use_describes(self):
        """Any document type can use describes field (v2.7 decision)."""
        errors, warnings = validate_describes_field(
            doc_id="strategy_x",
            doc_path="docs/strategy_x.md",
            doc_type="strategy",
            describes=["atom_a"],
            describes_verified=date.today(),
            all_docs=self.all_docs
        )
        # No error - any doc type can use describes
        assert len(errors) == 0
    
    def test_self_reference_error(self):
        """Self-reference in describes should error."""
        errors, warnings = validate_describes_field(
            doc_id="atom_a",
            doc_path="docs/atom_a.md",
            doc_type="atom",
            describes=["atom_a", "atom_b"],
            describes_verified=date.today(),
            all_docs=self.all_docs
        )
        assert len(errors) == 1
        assert errors[0].error_type == "self_reference"
    
    def test_unknown_id_error(self):
        """Unknown ID in describes should error."""
        errors, warnings = validate_describes_field(
            doc_id="doc1",
            doc_path="docs/doc1.md",
            doc_type="atom",
            describes=["nonexistent_id"],
            describes_verified=date.today(),
            all_docs=self.all_docs
        )
        assert len(errors) == 1
        assert errors[0].error_type == "unknown_id"
        assert "nonexistent_id" in errors[0].message
    
    def test_can_only_describe_atoms(self):
        """Can only describe atoms, not strategies."""
        errors, warnings = validate_describes_field(
            doc_id="doc1",
            doc_path="docs/doc1.md",
            doc_type="atom",
            describes=["strategy_x"],
            describes_verified=date.today(),
            all_docs=self.all_docs
        )
        assert len(errors) == 1
        assert errors[0].error_type == "type_constraint"
        assert "Can only describe atoms" in errors[0].message
    
    def test_missing_verified_warning(self):
        """Missing describes_verified should warn."""
        errors, warnings = validate_describes_field(
            doc_id="doc1",
            doc_path="docs/doc1.md",
            doc_type="atom",
            describes=["atom_a"],
            describes_verified=None,
            all_docs=self.all_docs
        )
        assert len(errors) == 0
        assert len(warnings) == 1
        assert warnings[0].warning_type == "missing_verified"
    
    def test_future_date_warning(self):
        """Future describes_verified date should warn."""
        future_date = date.today() + timedelta(days=30)
        errors, warnings = validate_describes_field(
            doc_id="doc1",
            doc_path="docs/doc1.md",
            doc_type="atom",
            describes=["atom_a"],
            describes_verified=future_date,
            all_docs=self.all_docs
        )
        assert len(errors) == 0
        assert len(warnings) == 1
        assert warnings[0].warning_type == "future_date"
    
    def test_valid_describes_no_errors(self):
        """Valid describes should pass without errors."""
        errors, warnings = validate_describes_field(
            doc_id="doc1",
            doc_path="docs/doc1.md",
            doc_type="atom",
            describes=["atom_a", "atom_b"],
            describes_verified=date.today(),
            all_docs=self.all_docs
        )
        assert len(errors) == 0
        assert len(warnings) == 0


class TestDetectDescribesCycles:
    """Tests for detect_describes_cycles function."""
    
    def test_no_cycles(self):
        """Should return empty list when no cycles."""
        docs = [
            ("doc_a", ["doc_b"]),
            ("doc_b", ["doc_c"]),
        ]
        cycles = detect_describes_cycles(docs)
        assert len(cycles) == 0
    
    def test_direct_cycle(self):
        """Should detect A→B, B→A cycle."""
        docs = [
            ("doc_a", ["doc_b"]),
            ("doc_b", ["doc_a"]),
        ]
        cycles = detect_describes_cycles(docs)
        assert len(cycles) == 1
        assert set(cycles[0]) == {"doc_a", "doc_b"}
    
    def test_multiple_cycles(self):
        """Should detect multiple independent cycles."""
        docs = [
            ("a", ["b"]),
            ("b", ["a"]),
            ("x", ["y"]),
            ("y", ["x"]),
        ]
        cycles = detect_describes_cycles(docs)
        assert len(cycles) == 2


class TestCheckStaleness:
    """Tests for check_staleness function."""
    
    def test_no_describes_returns_none(self):
        """No describes field means no staleness check."""
        result = check_staleness(
            doc_id="doc1",
            doc_path="docs/doc1.md",
            describes=[],
            describes_verified=date.today(),
            id_to_path={}
        )
        assert result is None
    
    def test_no_verified_date_returns_none(self):
        """Missing verified date means no staleness check."""
        result = check_staleness(
            doc_id="doc1",
            doc_path="docs/doc1.md",
            describes=["atom_a"],
            describes_verified=None,
            id_to_path={"atom_a": "docs/atom_a.md"}
        )
        assert result is None
    
    @patch('ontos_lib.get_file_modification_date')
    def test_stale_when_atom_newer(self, mock_git):
        """Doc is stale when described atom was modified after verification."""
        mock_git.return_value = (date(2025, 12, 18), ModifiedSource.GIT)
        
        result = check_staleness(
            doc_id="doc1",
            doc_path="docs/doc1.md",
            describes=["atom_a"],
            describes_verified=date(2025, 12, 15),
            id_to_path={"atom_a": "docs/atom_a.md"}
        )
        
        assert result is not None
        assert result.is_stale
        assert len(result.stale_atoms) == 1
        assert result.stale_atoms[0][0] == "atom_a"
    
    @patch('ontos_lib.get_file_modification_date')
    def test_current_when_atom_older(self, mock_git):
        """Doc is current when described atom was modified before verification."""
        mock_git.return_value = (date(2025, 12, 10), ModifiedSource.GIT)
        
        result = check_staleness(
            doc_id="doc1",
            doc_path="docs/doc1.md",
            describes=["atom_a"],
            describes_verified=date(2025, 12, 15),
            id_to_path={"atom_a": "docs/atom_a.md"}
        )
        
        assert result is None  # Not stale


class TestGitCaching:
    """Tests for git date caching behavior."""
    
    def setup_method(self):
        """Clear cache before each test."""
        clear_git_cache()
    
    @patch('ontos_lib._fetch_last_modified')
    def test_cache_prevents_duplicate_calls(self, mock_fetch):
        """Cache should prevent duplicate git calls for same file."""
        mock_fetch.return_value = (date(2025, 12, 19), ModifiedSource.GIT)
        
        # Call twice
        result1 = get_file_modification_date("/path/to/file.md")
        result2 = get_file_modification_date("/path/to/file.md")
        
        # Should only call _fetch_last_modified once
        assert mock_fetch.call_count == 1
        assert result1 == result2
    
    def test_clear_cache_works(self):
        """clear_git_cache should reset the cache."""
        clear_git_cache()
        # This just verifies the function doesn't error
