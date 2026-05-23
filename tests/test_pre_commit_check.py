"""Tests for pre-commit hook functionality (v2.5).

Tests cover:
- CI environment detection
- Rebase/cherry-pick detection  
- Dual condition triggering
- Shared helper functions
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.ontos', 'scripts'))


class TestCIDetection:
    """Test CI environment detection."""
    
    def test_detects_github_actions(self):
        from ontos_pre_commit_check import is_ci_environment
        
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true'}):
            assert is_ci_environment() is True
    
    def test_detects_gitlab_ci(self):
        from ontos_pre_commit_check import is_ci_environment
        
        with patch.dict(os.environ, {'GITLAB_CI': 'true'}):
            assert is_ci_environment() is True
    
    def test_detects_generic_ci(self):
        from ontos_pre_commit_check import is_ci_environment
        
        with patch.dict(os.environ, {'CI': 'true'}):
            assert is_ci_environment() is True
    
    def test_returns_false_when_no_ci(self):
        from ontos_pre_commit_check import is_ci_environment
        
        # Clear any CI env vars
        with patch.dict(os.environ, {}, clear=True):
            assert is_ci_environment() is False


class TestRebaseDetection:
    """Test rebase/cherry-pick detection."""
    
    def test_detects_rebase_merge(self, tmp_path):
        from ontos_pre_commit_check import is_special_git_operation
        
        # Create mock git dir with rebase marker
        git_dir = tmp_path / '.git'
        git_dir.mkdir()
        (git_dir / 'rebase-merge').mkdir()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=str(git_dir)
            )
            assert is_special_git_operation() is True
    
    def test_detects_cherry_pick(self, tmp_path):
        from ontos_pre_commit_check import is_special_git_operation
        
        git_dir = tmp_path / '.git'
        git_dir.mkdir()
        (git_dir / 'CHERRY_PICK_HEAD').touch()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=str(git_dir)
            )
            assert is_special_git_operation() is True
    
    def test_returns_false_for_normal_operation(self, tmp_path):
        from ontos_pre_commit_check import is_special_git_operation
        
        git_dir = tmp_path / '.git'
        git_dir.mkdir()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=str(git_dir)
            )
            assert is_special_git_operation() is False


class TestDualCondition:
    """Test dual condition for consolidation triggering."""
    
    def test_skips_when_count_below_threshold(self):
        from ontos_pre_commit_check import should_consolidate
        
        with patch('ontos_pre_commit_check.get_mode', return_value='automated'), \
             patch('ontos_pre_commit_check.is_ci_environment', return_value=False), \
             patch('ontos_pre_commit_check.is_special_git_operation', return_value=False), \
             patch('ontos_pre_commit_check.resolve_config') as mock_config, \
             patch('ontos_pre_commit_check.get_log_count', return_value=10):
            
            mock_config.side_effect = lambda key, default=None: {
                'AUTO_CONSOLIDATE_ON_COMMIT': True,
                'LOG_RETENTION_COUNT': 15,
            }.get(key, default)
            
            assert should_consolidate() is False
    
    def test_skips_when_count_at_threshold(self):
        """v2.6.2: Count-based - skips when count equals threshold."""
        from ontos_pre_commit_check import should_consolidate

        with patch('ontos_pre_commit_check.get_mode', return_value='automated'), \
             patch('ontos_pre_commit_check.is_ci_environment', return_value=False), \
             patch('ontos_pre_commit_check.is_special_git_operation', return_value=False), \
             patch('ontos_pre_commit_check.resolve_config') as mock_config, \
             patch('ontos_pre_commit_check.get_log_count', return_value=20):

            mock_config.side_effect = lambda key, default=None: {
                'AUTO_CONSOLIDATE_ON_COMMIT': True,
                'LOG_WARNING_THRESHOLD': 20,
            }.get(key, default)

            # 20 logs == 20 threshold, should NOT consolidate
            assert should_consolidate() is False

    def test_triggers_when_count_exceeds_threshold(self):
        """v2.6.2: Count-based - triggers when count > threshold."""
        from ontos_pre_commit_check import should_consolidate

        with patch('ontos_pre_commit_check.get_mode', return_value='automated'), \
             patch('ontos_pre_commit_check.is_ci_environment', return_value=False), \
             patch('ontos_pre_commit_check.is_special_git_operation', return_value=False), \
             patch('ontos_pre_commit_check.resolve_config') as mock_config, \
             patch('ontos_pre_commit_check.get_log_count', return_value=25):

            mock_config.side_effect = lambda key, default=None: {
                'AUTO_CONSOLIDATE_ON_COMMIT': True,
                'LOG_WARNING_THRESHOLD': 20,
            }.get(key, default)

            # 25 logs > 20 threshold, SHOULD consolidate
            assert should_consolidate() is True
    
    def test_skips_non_automated_mode(self):
        from ontos_pre_commit_check import should_consolidate
        
        with patch('ontos_pre_commit_check.get_mode', return_value='prompted'):
            assert should_consolidate() is False


class TestSharedHelpers:
    """Test shared helper functions in ontos_lib."""
    
    def test_get_logs_dir_returns_path(self):
        from ontos.core.paths import get_logs_dir
        
        result = get_logs_dir()
        assert result is not None
        assert isinstance(result, str)
    
    def test_get_log_count_returns_int(self):
        from ontos.core.paths import get_log_count
        
        result = get_log_count()
        assert isinstance(result, int)
        assert result >= 0
    
    def test_get_logs_older_than_returns_list(self):
        from ontos.core.paths import get_logs_older_than
        
        result = get_logs_older_than(30)
        assert isinstance(result, list)
    
    def test_get_archive_dir_returns_path(self):
        from ontos.core.paths import get_archive_dir
        
        result = get_archive_dir()
        assert result is not None
        assert isinstance(result, str)
    
    def test_get_decision_history_path_returns_path(self):
        from ontos.core.paths import get_decision_history_path
        
        result = get_decision_history_path()
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith('decision_history.md')


class TestMainNeverBlocks:
    """Test that main() always returns 0."""
    
    def test_returns_zero_on_no_consolidation(self):
        from ontos_pre_commit_check import main
        
        with patch('ontos_pre_commit_check.should_consolidate', return_value=False):
            assert main() == 0
    
    def test_returns_zero_on_consolidation_success(self):
        from ontos_pre_commit_check import main
        
        with patch('ontos_pre_commit_check.should_consolidate', return_value=True), \
             patch('ontos_pre_commit_check.get_log_count', return_value=20), \
             patch('ontos_pre_commit_check.resolve_config', return_value=15), \
             patch('ontos_pre_commit_check.run_consolidation', return_value=(True, '')), \
             patch('ontos_pre_commit_check.stage_consolidated_files'):
            assert main() == 0
    
    def test_returns_zero_on_consolidation_failure(self):
        from ontos_pre_commit_check import main
        
        with patch('ontos_pre_commit_check.should_consolidate', return_value=True), \
             patch('ontos_pre_commit_check.get_log_count', return_value=20), \
             patch('ontos_pre_commit_check.resolve_config', return_value=15), \
             patch('ontos_pre_commit_check.run_consolidation', return_value=(False, 'Error')):
            assert main() == 0
    
    def test_returns_zero_on_exception(self):
        from ontos_pre_commit_check import main

        with patch('ontos_pre_commit_check.should_consolidate', side_effect=Exception('Test error')):
            assert main() == 0


class TestValidateCheckMode:
    """Regression coverage for issue #122: --check must validate without writing."""

    REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    SCRIPT = os.path.join(REPO_ROOT, '.ontos', 'scripts', 'ontos_generate_context_map.py')

    @staticmethod
    def _read_bytes(path):
        with open(path, 'rb') as f:
            return f.read()

    def _run_check(self, *extra_args, cwd=None):
        import subprocess
        return subprocess.run(
            [sys.executable, self.SCRIPT, '--strict', '--quiet', '--check', *extra_args],
            cwd=cwd or self.REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, 'ONTOS_NO_DEPRECATION_WARNINGS': '1'},
        )

    def test_check_mode_does_not_write_context_map(self):
        context_map = os.path.join(self.REPO_ROOT, 'Ontos_Context_Map.md')
        if not os.path.exists(context_map):
            pytest.skip("Ontos_Context_Map.md not present; nothing to compare against.")

        before = self._read_bytes(context_map)
        before_mtime = os.stat(context_map).st_mtime_ns

        result = self._run_check()

        assert result.returncode in (0, 1), (
            f"unexpected exit {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert self._read_bytes(context_map) == before, (
            "Ontos_Context_Map.md was rewritten by --check (issue #122 regression)"
        )
        assert os.stat(context_map).st_mtime_ns == before_mtime, (
            "Ontos_Context_Map.md mtime changed under --check (issue #122 regression)"
        )

    def test_check_mode_does_not_write_decision_history(self):
        history = os.path.join(
            self.REPO_ROOT, '.ontos-internal', 'reference', 'decision_history.md'
        )
        if not os.path.exists(history):
            pytest.skip("decision_history.md not present; nothing to compare against.")

        before = self._read_bytes(history)
        before_mtime = os.stat(history).st_mtime_ns

        result = self._run_check()

        assert result.returncode in (0, 1), (
            f"unexpected exit {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert self._read_bytes(history) == before, (
            "decision_history.md was rewritten by --check (issue #122 regression)"
        )
        assert os.stat(history).st_mtime_ns == before_mtime, (
            "decision_history.md mtime changed under --check (issue #122 regression)"
        )

    def test_check_mode_still_reports_validation_errors(self, tmp_path):
        docs = tmp_path / 'docs'
        docs.mkdir()
        (docs / 'good.md').write_text(
            "---\nid: good_doc\ntype: atom\nstatus: active\n---\n# Good\n",
            encoding='utf-8',
        )
        (docs / 'bad.md').write_text(
            "---\nid: bad_doc\ntype: atom\nstatus: active\n"
            "depends_on: [nonexistent_dep_for_test_122]\n---\n# Bad\n",
            encoding='utf-8',
        )

        result = self._run_check('--dir', str(docs), cwd=tmp_path)

        assert result.returncode != 0, (
            "--strict --check must exit non-zero when validation errors exist.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        combined = (result.stdout + result.stderr).lower()
        assert 'nonexistent_dep_for_test_122' in combined, (
            f"Expected broken-dep error in output. Got:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
