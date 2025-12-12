"""Tests for orphan detection functionality."""

import pytest
from unittest.mock import patch
from ontos_generate_context_map import validate_dependencies

# Default orphan types (User Mode) - atoms should be flagged as orphans
DEFAULT_ALLOWED_ORPHAN_TYPES = ['product', 'strategy', 'kernel']


class TestOrphanDetection:
    """Tests for orphan document detection."""

    @patch('ontos_generate_context_map.ALLOWED_ORPHAN_TYPES', DEFAULT_ALLOWED_ORPHAN_TYPES)
    def test_detect_orphan_atom(self):
        """Test that orphan atoms are detected in User Mode."""
        files_data = {
            'orphan_atom': {
                'filepath': 'docs/orphan.md',
                'filename': 'orphan.md',
                'type': 'atom',
                'depends_on': [],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        orphan_issues = [i for i in issues if '[ORPHAN]' in i]
        assert len(orphan_issues) == 1
        assert 'orphan_atom' in orphan_issues[0]

    def test_skip_orphan_kernel(self):
        """Test that kernel types are not flagged as orphans."""
        files_data = {
            'mission': {
                'filepath': 'docs/mission.md',
                'filename': 'mission.md',
                'type': 'kernel',
                'depends_on': [],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        orphan_issues = [i for i in issues if '[ORPHAN]' in i]
        assert len(orphan_issues) == 0

    def test_skip_orphan_strategy(self):
        """Test that strategy types are not flagged as orphans."""
        files_data = {
            'roadmap': {
                'filepath': 'docs/roadmap.md',
                'filename': 'roadmap.md',
                'type': 'strategy',
                'depends_on': [],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        orphan_issues = [i for i in issues if '[ORPHAN]' in i]
        assert len(orphan_issues) == 0

    def test_skip_orphan_product(self):
        """Test that product types are not flagged as orphans."""
        files_data = {
            'feature': {
                'filepath': 'docs/feature.md',
                'filename': 'feature.md',
                'type': 'product',
                'depends_on': [],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        orphan_issues = [i for i in issues if '[ORPHAN]' in i]
        assert len(orphan_issues) == 0

    def test_skip_orphan_log_file(self):
        """Test that files in /logs/ directory are not flagged as orphans."""
        files_data = {
            'log_20250101': {
                'filepath': 'docs/logs/2025-01-01.md',
                'filename': '2025-01-01.md',
                'type': 'atom',
                'depends_on': [],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        orphan_issues = [i for i in issues if '[ORPHAN]' in i]
        assert len(orphan_issues) == 0

    def test_skip_orphan_template(self):
        """Test that template files are not flagged as orphans."""
        files_data = {
            'template': {
                'filepath': 'docs/_template.md',
                'filename': '_template.md',
                'type': 'atom',
                'depends_on': [],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        orphan_issues = [i for i in issues if '[ORPHAN]' in i]
        assert len(orphan_issues) == 0

    @patch('ontos_generate_context_map.ALLOWED_ORPHAN_TYPES', DEFAULT_ALLOWED_ORPHAN_TYPES)
    def test_non_orphan_with_dependent(self):
        """Test that documents with dependents are not flagged as orphans in User Mode."""
        files_data = {
            'parent': {
                'filepath': 'docs/parent.md',
                'filename': 'parent.md',
                'type': 'atom',
                'depends_on': [],
                'status': 'active'
            },
            'child': {
                'filepath': 'docs/child.md',
                'filename': 'child.md',
                'type': 'atom',
                'depends_on': ['parent'],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        orphan_issues = [i for i in issues if '[ORPHAN]' in i]
        # parent is not orphan (child depends on it)
        # child is orphan (nothing depends on it)
        assert len(orphan_issues) == 1
        assert 'child' in orphan_issues[0]
        assert 'parent' not in orphan_issues[0]


class TestTypeHierarchy:
    """Tests for architectural violation detection."""

    def test_kernel_depending_on_atom_violation(self):
        """Test that kernel depending on atom is flagged."""
        files_data = {
            'bad_kernel': {
                'filepath': 'docs/kernel.md',
                'filename': 'kernel.md',
                'type': 'kernel',
                'depends_on': ['some_atom'],
                'status': 'active'
            },
            'some_atom': {
                'filepath': 'docs/atom.md',
                'filename': 'atom.md',
                'type': 'atom',
                'depends_on': [],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        arch_issues = [i for i in issues if '[ARCHITECTURE]' in i]
        assert len(arch_issues) == 1
        assert 'bad_kernel' in arch_issues[0]

    def test_atom_depending_on_kernel_valid(self):
        """Test that atom depending on kernel is valid."""
        files_data = {
            'kernel': {
                'filepath': 'docs/kernel.md',
                'filename': 'kernel.md',
                'type': 'kernel',
                'depends_on': [],
                'status': 'active'
            },
            'atom': {
                'filepath': 'docs/atom.md',
                'filename': 'atom.md',
                'type': 'atom',
                'depends_on': ['kernel'],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        arch_issues = [i for i in issues if '[ARCHITECTURE]' in i]
        assert len(arch_issues) == 0

    def test_strategy_depending_on_atom_violation(self):
        """Test that strategy depending on atom is flagged."""
        files_data = {
            'strategy': {
                'filepath': 'docs/strategy.md',
                'filename': 'strategy.md',
                'type': 'strategy',
                'depends_on': ['atom'],
                'status': 'active'
            },
            'atom': {
                'filepath': 'docs/atom.md',
                'filename': 'atom.md',
                'type': 'atom',
                'depends_on': [],
                'status': 'active'
            }
        }

        issues = validate_dependencies(files_data)
        arch_issues = [i for i in issues if '[ARCHITECTURE]' in i]
        assert len(arch_issues) == 1


class TestDependencyDepth:
    """Tests for dependency depth checking."""

    def test_deep_dependency_chain(self):
        """Test that deep chains (>5) are flagged."""
        # Create a chain of 7 docs: doc0 -> doc1 -> doc2 -> ... -> doc6
        files_data = {}
        for i in range(7):
            files_data[f'doc{i}'] = {
                'filepath': f'docs/doc{i}.md',
                'filename': f'doc{i}.md',
                'type': 'atom',
                'depends_on': [f'doc{i+1}'] if i < 6 else [],
                'status': 'active'
            }

        issues = validate_dependencies(files_data)
        depth_issues = [i for i in issues if '[DEPTH]' in i]
        assert len(depth_issues) >= 1

    def test_shallow_chain_ok(self):
        """Test that shallow chains (<=5) are not flagged."""
        # Create a chain of 4 docs
        files_data = {}
        for i in range(4):
            files_data[f'doc{i}'] = {
                'filepath': f'docs/doc{i}.md',
                'filename': f'doc{i}.md',
                'type': 'atom',
                'depends_on': [f'doc{i+1}'] if i < 3 else [],
                'status': 'active'
            }

        issues = validate_dependencies(files_data)
        depth_issues = [i for i in issues if '[DEPTH]' in i]
        assert len(depth_issues) == 0
