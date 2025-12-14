
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../.ontos/scripts')))

from ontos_query import (
    query_depends_on,
    query_depended_by,
    query_concept,
    query_stale,
    query_health
)

@pytest.fixture
def sample_data():
    return {
        'doc1': {
            'filepath': '/path/to/doc1.md',
            'type': 'note',
            'depends_on': ['doc2'],
            'concepts': ['concept1'],
            'impacts': []
        },
        'doc2': {
            'filepath': '/path/to/doc2.md',
            'type': 'note',
            'depends_on': [],
            'concepts': ['concept2'],
            'impacts': []
        },
        'kernel1': {
            'filepath': '/path/to/kernel1.md',
            'type': 'kernel',
            'depends_on': [],
            'concepts': [],
            'impacts': []
        },
        'orphan': {
            'filepath': '/path/to/orphan.md',
            'type': 'note',
            'depends_on': [],
            'concepts': [],
            'impacts': []
        }
    }

def test_depends_on_returns_direct_dependencies(sample_data):
    deps = query_depends_on(sample_data, 'doc1')
    assert deps == ['doc2']

def test_depends_on_nonexistent_returns_empty(sample_data):
    deps = query_depends_on(sample_data, 'nonexistent')
    assert deps == []

def test_depended_by_returns_reverse_graph(sample_data):
    depended = query_depended_by(sample_data, 'doc2')
    assert 'doc1' in depended

def test_concept_search_finds_matching_logs(sample_data):
    matches = query_concept(sample_data, 'concept1')
    assert 'doc1' in matches

def test_stale_uses_git_log_not_mtime(sample_data):
    with patch("ontos_query.get_git_last_modified") as mock_git:
        # Mock git returning old date
        mock_git.return_value = datetime(2020, 1, 1)
        stale = query_stale(sample_data, 30)
        assert len(stale) > 0
        assert stale[0][0] == 'doc1' # Or whichever is iterated

from datetime import datetime
def test_health_calculates_connectivity(sample_data):
    health = query_health(sample_data)
    # kernel1 is connected to nothing, and depended by nothing.
    # So only kernel1 is reachable from kernel1?
    # doc1 -> doc2. Neither connected to kernel1.
    # So reachable is 1 (kernel1). Total docs 4. Connectivity 25%.
    assert health['connectivity'] == 25.0

def test_health_identifies_orphans(sample_data):
    health = query_health(sample_data)
    # Orphans: nodes not depended by anyone and not special type.
    # doc1 is not depended by anyone. type note. Orphan.
    # doc2 is depended by doc1. Not orphan.
    # kernel1 not depended. type kernel. Not orphan (special).
    # orphan not depended. type note. Orphan.
    # So doc1 and orphan are orphans.
    assert health['orphans'] == 2
