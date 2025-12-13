"""Tests for data quality lint functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import sys
import os

# Add scripts dir to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../.ontos/scripts'))

from ontos_generate_context_map import lint_data_quality

class TestLintDataQuality:
    """Tests for lint_data_quality function."""

    def test_lint_empty_impacts(self):
        """Test that empty impacts on active logs triggers warning."""
        files_data = {
            'log_20251213_test': {
                'filepath': 'logs/2025-12-13_test.md',
                'filename': '2025-12-13_test.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'chore',
                'concepts': ['testing'],
                'impacts': [],
            }
        }
        
        warnings = lint_data_quality(files_data, set())
        assert any('Empty impacts' in w for w in warnings)

    def test_lint_no_warning_for_archived_empty_impacts(self):
        """Test that archived logs with empty impacts don't trigger warning."""
        files_data = {
            'log_20251213_test': {
                'filepath': 'logs/2025-12-13_test.md',
                'filename': '2025-12-13_test.md',
                'type': 'log',
                'status': 'archived',
                'event_type': 'chore',
                'concepts': ['testing'],
                'impacts': [],
            }
        }
        
        warnings = lint_data_quality(files_data, set())
        assert not any('Empty impacts' in w for w in warnings)

    def test_lint_unknown_concept(self):
        """Test that non-vocabulary concepts trigger warning."""
        files_data = {
            'log_20251213_test': {
                'filepath': 'logs/2025-12-13_test.md',
                'filename': '2025-12-13_test.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'feature',
                'concepts': ['authentication'],  # Should be 'auth'
                'impacts': ['some_doc'],
            }
        }
        
        known_concepts = {'auth', 'api', 'db'}
        warnings = lint_data_quality(files_data, known_concepts)
        assert any('Unknown concept' in w and 'authentication' in w for w in warnings)

    def test_lint_no_warning_for_known_concept(self):
        """Test that vocabulary concepts don't trigger warning."""
        files_data = {
            'log_20251213_test': {
                'filepath': 'logs/2025-12-13_test.md',
                'filename': '2025-12-13_test.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'feature',
                'concepts': ['auth', 'api'],
                'impacts': ['some_doc'],
            }
        }
        
        known_concepts = {'auth', 'api', 'db'}
        warnings = lint_data_quality(files_data, known_concepts)
        assert not any('Unknown concept' in w for w in warnings)

    def test_lint_excessive_concepts(self):
        """Test that >6 concepts triggers warning."""
        files_data = {
            'log_20251213_test': {
                'filepath': 'logs/2025-12-13_test.md',
                'filename': '2025-12-13_test.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'feature',
                'concepts': ['auth', 'api', 'db', 'ui', 'testing', 'devops', 'security', 'perf'],
                'impacts': ['some_doc'],
            }
        }
        
        warnings = lint_data_quality(files_data, set())
        assert any('8 concepts' in w for w in warnings)

    def test_lint_acceptable_concept_count(self):
        """Test that <=6 concepts don't trigger warning."""
        files_data = {
            'log_20251213_test': {
                'filepath': 'logs/2025-12-13_test.md',
                'filename': '2025-12-13_test.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'feature',
                'concepts': ['auth', 'api', 'db'],
                'impacts': ['some_doc'],
            }
        }
        
        warnings = lint_data_quality(files_data, set())
        assert not any('concepts' in w and 'recommended' in w for w in warnings)

    def test_lint_stale_log(self):
        """Test that logs >30 days old trigger warning."""
        old_date = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')
        
        files_data = {
            f'log_{old_date.replace("-", "")}_test': {
                'filepath': f'logs/{old_date}_test.md',
                'filename': f'{old_date}_test.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'chore',
                'concepts': ['testing'],
                'impacts': ['some_doc'],
            }
        }
        
        warnings = lint_data_quality(files_data, set())
        assert any('days old' in w for w in warnings)

    @patch('ontos_config.LOG_RETENTION_COUNT', 2)
    def test_lint_exceeds_retention_count(self):
        """Test that active logs > LOG_RETENTION_COUNT triggers warning."""
        files_data = {}
        for i in range(5):
            date = datetime.now().strftime('%Y-%m-%d')
            files_data[f'log_{i}'] = {
                'filepath': f'logs/{date}_test{i}.md',
                'filename': f'{date}_test{i}.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'chore',
                'concepts': ['testing'],
                'impacts': ['some_doc'],
            }
        
        warnings = lint_data_quality(files_data, set())
        assert any('exceeds threshold' in w for w in warnings)

    def test_lint_skips_non_log_docs(self):
        """Test that non-log documents are skipped by lint."""
        files_data = {
            'mission': {
                'filepath': 'kernel/mission.md',
                'filename': 'mission.md',
                'type': 'kernel',
                'status': 'active',
                'depends_on': [],
            }
        }
        
        warnings = lint_data_quality(files_data, set())
        assert len(warnings) == 0


class TestLoadCommonConcepts:
    """Tests for load_common_concepts function."""

    def test_returns_empty_set_when_no_file(self):
        """Test that missing file returns empty set."""
        from ontos_generate_context_map import load_common_concepts
        
        with patch('os.path.exists', return_value=False):
            concepts = load_common_concepts()
            assert concepts == set()
