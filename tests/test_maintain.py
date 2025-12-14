
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../.ontos/scripts')))

from ontos_maintain import run_script, main as maintain_main

def test_runs_migrate_then_generate():
    with patch("ontos_maintain.run_script", return_value=(True, "")) as mock_run:
        with patch("sys.exit") as mock_exit:
            maintain_main()
            assert mock_run.call_count == 2
            assert mock_run.call_args_list[0][0][0] == 'ontos_migrate_frontmatter.py'
            assert mock_run.call_args_list[1][0][0] == 'ontos_generate_context_map.py'

def test_strict_mode_fails_on_issues():
    # If one script fails
    with patch("ontos_maintain.run_script", side_effect=[(True, ""), (False, "error")]) as mock_run:
        with patch("sys.exit") as mock_exit:
            with patch("sys.argv", ["ontos_maintain.py", "--strict"]):
                maintain_main()
                mock_exit.assert_called_with(1)

def test_lint_flag_passed_to_generate():
    with patch("ontos_maintain.run_script", return_value=(True, "")) as mock_run:
        with patch("sys.exit"):
            with patch("sys.argv", ["ontos_maintain.py", "--lint"]):
                maintain_main()
                # Check args of confirm call
                # run_script('ontos_generate_context_map.py', ['--lint'], False)
                call_args = mock_run.call_args_list[1]
                assert '--lint' in call_args[0][1]
