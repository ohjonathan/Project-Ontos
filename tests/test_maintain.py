
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

_LEGACY_SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.ontos/scripts'))
sys.path.insert(0, _LEGACY_SCRIPTS)
try:
    from ontos_maintain import run_script, main as maintain_main
finally:
    sys.path.remove(_LEGACY_SCRIPTS)

def test_runs_migrate_then_generate():
    # v2.4: Now runs 3 steps: migrate, generate, consolidate
    with patch("ontos_maintain.run_script", return_value=(True, "")) as mock_run:
        with patch("sys.exit") as mock_exit:
            maintain_main()
            assert mock_run.call_count == 3
            assert mock_run.call_args_list[0][0][0] == 'ontos_migrate_frontmatter.py'
            assert mock_run.call_args_list[1][0][0] == 'ontos_generate_context_map.py'
            assert mock_run.call_args_list[2][0][0] == 'ontos_consolidate.py'

def test_strict_mode_fails_on_issues():
    # If one script fails (3 calls needed for v2.4)
    with patch("ontos_maintain.run_script", side_effect=[(True, ""), (False, "error"), (True, "")]) as mock_run:
        with patch("sys.exit") as mock_exit:
            with patch("sys.argv", ["ontos_maintain.py", "--strict"]):
                maintain_main()
                mock_exit.assert_called_with(1)

def test_lint_flag_passed_to_generate():
    with patch("ontos_maintain.run_script", return_value=(True, "")) as mock_run:
        with patch("sys.exit"):
            with patch("sys.argv", ["ontos_maintain.py", "--lint"]):
                maintain_main()
                # Check args of generate call (second call)
                call_args = mock_run.call_args_list[1]
                assert '--lint' in call_args[0][1]


def test_consolidation_step_added():
    """v2.4: Verify consolidation step exists in maintenance."""
    with patch("ontos_maintain.run_script", return_value=(True, "")) as mock_run:
        with patch("sys.exit"):
            maintain_main()
            # Verify consolidate.py is called as step 3
            scripts_called = [call[0][0] for call in mock_run.call_args_list]
            assert 'ontos_consolidate.py' in scripts_called
