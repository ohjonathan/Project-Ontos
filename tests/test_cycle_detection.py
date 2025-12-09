"""Tests for cycle detection functionality."""

import pytest
from ontos_generate_context_map import validate_dependencies


class TestCycleDetection:
    """Tests for circular dependency detection."""

    def test_detect_simple_cycle(self):
        """Test detection of simple A -> B -> A cycle."""
        files_data = {
            'doc_a': {
                'filepath': 'docs/doc_a.md',
                'filename': 'doc_a.md',
                'type': 'atom',
                'depends_on': ['doc_b'],
                'status': 'active'
            },
            'doc_b': {
                'filepath': 'docs/doc_b.md',
                'filename': 'doc_b.md',
                'type': 'atom',
                'depends_on': ['doc_a'],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        cycle_issues = [i for i in issues if '[CYCLE]' in i]
        assert len(cycle_issues) == 1
        assert 'doc_a' in cycle_issues[0] or 'doc_b' in cycle_issues[0]

    def test_detect_three_node_cycle(self):
        """Test detection of A -> B -> C -> A cycle."""
        files_data = {
            'doc_a': {
                'filepath': 'docs/doc_a.md',
                'filename': 'doc_a.md',
                'type': 'atom',
                'depends_on': ['doc_b'],
                'status': 'active'
            },
            'doc_b': {
                'filepath': 'docs/doc_b.md',
                'filename': 'doc_b.md',
                'type': 'atom',
                'depends_on': ['doc_c'],
                'status': 'active'
            },
            'doc_c': {
                'filepath': 'docs/doc_c.md',
                'filename': 'doc_c.md',
                'type': 'atom',
                'depends_on': ['doc_a'],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        cycle_issues = [i for i in issues if '[CYCLE]' in i]
        assert len(cycle_issues) >= 1

    def test_no_cycle_in_valid_graph(self):
        """Test that no cycle is reported for valid DAG."""
        files_data = {
            'kernel': {
                'filepath': 'docs/kernel.md',
                'filename': 'kernel.md',
                'type': 'kernel',
                'depends_on': [],
                'status': 'active'
            },
            'strategy': {
                'filepath': 'docs/strategy.md',
                'filename': 'strategy.md',
                'type': 'strategy',
                'depends_on': ['kernel'],
                'status': 'active'
            },
            'atom': {
                'filepath': 'docs/atom.md',
                'filename': 'atom.md',
                'type': 'atom',
                'depends_on': ['strategy'],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        cycle_issues = [i for i in issues if '[CYCLE]' in i]
        assert len(cycle_issues) == 0

    def test_self_reference_cycle(self):
        """Test detection of self-referencing document."""
        files_data = {
            'self_ref': {
                'filepath': 'docs/self_ref.md',
                'filename': 'self_ref.md',
                'type': 'atom',
                'depends_on': ['self_ref'],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        cycle_issues = [i for i in issues if '[CYCLE]' in i]
        assert len(cycle_issues) == 1


class TestBrokenLinks:
    """Tests for broken link detection."""

    def test_detect_broken_link(self):
        """Test detection of reference to nonexistent document."""
        files_data = {
            'doc_with_broken_link': {
                'filepath': 'docs/broken.md',
                'filename': 'broken.md',
                'type': 'atom',
                'depends_on': ['nonexistent'],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        broken_issues = [i for i in issues if '[BROKEN LINK]' in i]
        assert len(broken_issues) == 1
        assert 'nonexistent' in broken_issues[0]

    def test_no_broken_link_for_valid_reference(self):
        """Test that valid references don't report broken links."""
        files_data = {
            'target': {
                'filepath': 'docs/target.md',
                'filename': 'target.md',
                'type': 'kernel',
                'depends_on': [],
                'status': 'active'
            },
            'source': {
                'filepath': 'docs/source.md',
                'filename': 'source.md',
                'type': 'atom',
                'depends_on': ['target'],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        broken_issues = [i for i in issues if '[BROKEN LINK]' in i]
        assert len(broken_issues) == 0

    def test_string_depends_on_handling(self):
        """Test that string depends_on (instead of list) is handled."""
        files_data = {
            'doc': {
                'filepath': 'docs/doc.md',
                'filename': 'doc.md',
                'type': 'atom',
                'depends_on': 'nonexistent',  # String instead of list
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        broken_issues = [i for i in issues if '[BROKEN LINK]' in i]
        assert len(broken_issues) == 1
