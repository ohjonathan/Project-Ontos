"""Tests for dual-mode (user/contributor) functionality.

These tests verify that Ontos works correctly in both:
- Contributor mode: Ontos developing itself (.ontos-internal/)
- User mode: Projects using Ontos (docs/)
"""

import os
import pytest


class TestDualModeScaffolding:
    """Test that scaffolding creates correct structure in both modes."""
    
    def test_mode_aware_project_has_correct_structure(self, mode_aware_project, project_mode):
        """Verify project structure is created based on mode."""
        tmp_path = mode_aware_project
        
        if project_mode == "contributor":
            # Contributor mode should have .ontos-internal
            assert (tmp_path / '.ontos-internal').exists()
            assert (tmp_path / '.ontos').exists()
        else:
            # User mode should have docs/ with full structure
            assert (tmp_path / 'docs').exists()
            assert (tmp_path / 'docs' / 'logs').exists()
            assert (tmp_path / 'docs' / 'strategy').exists()
            assert (tmp_path / 'docs' / 'archive' / 'logs').exists()
    
    def test_docs_dir_fixture_matches_mode(self, project_mode, docs_dir):
        """Verify docs_dir fixture returns correct path for mode."""
        if project_mode == "contributor":
            assert docs_dir == ".ontos-internal"
        else:
            assert docs_dir == "docs"


class TestDualModePathHelpers:
    """Test that path helpers work correctly in both modes."""
    
    def test_decision_history_path_respects_mode(self, mode_aware_project, project_mode):
        """Verify decision_history.md path is correct for mode."""
        # Can't fully test path helpers without config, but verify structure exists
        if project_mode == "user":
            assert (mode_aware_project / 'docs' / 'strategy' / 'decision_history.md').exists()
