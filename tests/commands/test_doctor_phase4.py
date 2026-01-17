"""Tests for doctor command (Phase 4)."""

from unittest.mock import patch, MagicMock

import pytest

from ontos.commands.doctor import (
    CheckResult,
    DoctorOptions,
    DoctorResult,
    check_configuration,
    check_git_hooks,
    check_python_version,
    doctor_command,
    format_doctor_output,
)


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_creates_with_required_fields(self):
        result = CheckResult(name="test", status="pass", message="OK")
        assert result.name == "test"
        assert result.status == "pass"
        assert result.message == "OK"
        assert result.details is None

    def test_creates_with_details(self):
        result = CheckResult(
            name="test",
            status="fail",
            message="Failed",
            details="Extra info"
        )
        assert result.details == "Extra info"


class TestDoctorResult:
    """Tests for DoctorResult dataclass."""

    def test_status_pass_when_no_failures(self):
        result = DoctorResult(passed=7, failed=0, warnings=0)
        assert result.status == "pass"

    def test_status_fail_when_has_failures(self):
        result = DoctorResult(passed=5, failed=2, warnings=0)
        assert result.status == "fail"

    def test_status_warn_when_only_warnings(self):
        result = DoctorResult(passed=5, failed=0, warnings=2)
        assert result.status == "warn"


class TestCheckPythonVersion:
    """Tests for check_python_version."""

    def test_passes_for_current_python(self):
        """Current Python should be >= 3.9."""
        result = check_python_version()
        assert result.status == "pass"
        assert "3.9" in result.message


class TestCheckGitHooks:
    """Tests for check_git_hooks."""

    def test_warns_when_not_git_repo(self, tmp_path, monkeypatch):
        """Should warn when not in a git repo."""
        monkeypatch.chdir(tmp_path)
        result = check_git_hooks()
        assert result.status in ("warn", "fail")

    def test_handles_git_not_installed(self, tmp_path, monkeypatch):
        """Should fail gracefully when git not installed."""
        monkeypatch.chdir(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = check_git_hooks()

        assert result.status == "fail"
        assert "not found" in result.message.lower()


class TestCheckConfiguration:
    """Tests for check_configuration."""

    def test_fails_when_no_config(self, tmp_path, monkeypatch):
        """Should fail when .ontos.toml doesn't exist."""
        monkeypatch.chdir(tmp_path)
        result = check_configuration()
        assert result.status == "fail"
        assert "not found" in result.message.lower()


class TestDoctorCommand:
    """Tests for doctor_command."""

    def test_returns_exit_code_0_when_checks_pass(self):
        """Should return 0 when all checks pass or warn."""
        with patch("ontos.commands.doctor.check_configuration") as mock_config, \
             patch("ontos.commands.doctor.check_git_hooks") as mock_hooks, \
             patch("ontos.commands.doctor.check_python_version") as mock_python, \
             patch("ontos.commands.doctor.check_docs_directory") as mock_docs, \
             patch("ontos.commands.doctor.check_context_map") as mock_map, \
             patch("ontos.commands.doctor.check_validation") as mock_valid, \
             patch("ontos.commands.doctor.check_cli_availability") as mock_cli, \
             patch("ontos.commands.doctor.check_agents_staleness") as mock_agents:

            for mock in [mock_config, mock_hooks, mock_python, mock_docs,
                        mock_map, mock_valid, mock_cli, mock_agents]:
                mock.return_value = CheckResult(
                    name="test", status="pass", message="OK"
                )

            options = DoctorOptions()
            exit_code, result = doctor_command(options)

            assert exit_code == 0
            assert result.passed == 8
            assert result.failed == 0

    def test_returns_exit_code_1_when_check_fails(self):
        """Should return 1 when any check fails."""
        with patch("ontos.commands.doctor.check_configuration") as mock_config, \
             patch("ontos.commands.doctor.check_git_hooks") as mock_hooks, \
             patch("ontos.commands.doctor.check_python_version") as mock_python, \
             patch("ontos.commands.doctor.check_docs_directory") as mock_docs, \
             patch("ontos.commands.doctor.check_context_map") as mock_map, \
             patch("ontos.commands.doctor.check_validation") as mock_valid, \
             patch("ontos.commands.doctor.check_cli_availability") as mock_cli, \
             patch("ontos.commands.doctor.check_agents_staleness") as mock_agents:

            for mock in [mock_hooks, mock_python, mock_docs,
                        mock_map, mock_valid, mock_cli, mock_agents]:
                mock.return_value = CheckResult(
                    name="test", status="pass", message="OK"
                )

            mock_config.return_value = CheckResult(
                name="configuration", status="fail", message="Not found"
            )

            options = DoctorOptions()
            exit_code, result = doctor_command(options)

            assert exit_code == 1
            assert result.failed == 1


class TestFormatDoctorOutput:
    """Tests for format_doctor_output."""

    def test_formats_passing_checks(self):
        result = DoctorResult(
            checks=[
                CheckResult(name="test1", status="pass", message="OK"),
                CheckResult(name="test2", status="pass", message="Good"),
            ],
            passed=2, failed=0, warnings=0
        )
        output = format_doctor_output(result)
        assert "OK: test1: OK" in output
        assert "OK: test2: Good" in output
        assert "2 passed" in output

    def test_formats_failing_checks(self):
        result = DoctorResult(
            checks=[
                CheckResult(name="test1", status="fail", message="Bad"),
            ],
            passed=0, failed=1, warnings=0
        )
        output = format_doctor_output(result)
        assert "FAIL: test1: Bad" in output

    def test_includes_details_when_verbose(self):
        result = DoctorResult(
            checks=[
                CheckResult(
                    name="test1",
                    status="fail",
                    message="Bad",
                    details="Extra info"
                ),
            ],
            passed=0, failed=1, warnings=0
        )
        output = format_doctor_output(result, verbose=True)
        assert "Extra info" in output


class TestCheckAgentsStaleness:
    """Tests for check_agents_staleness (M8)."""

    def test_warns_when_agents_not_found(self, tmp_path, monkeypatch):
        """Should warn when AGENTS.md doesn't exist."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        
        from ontos.commands.doctor import check_agents_staleness
        result = check_agents_staleness()
        
        assert result.status == "warn"
        assert "not found" in result.message.lower()

    def test_passes_when_agents_up_to_date(self, tmp_path, monkeypatch):
        """Should pass when AGENTS.md is newer than source files."""
        import time
        monkeypatch.chdir(tmp_path)
        
        # Create source files
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        (tmp_path / "Ontos_Context_Map.md").write_text("# Map")
        
        # Wait and create AGENTS.md (newer)
        time.sleep(0.1)
        (tmp_path / "AGENTS.md").write_text("# AGENTS.md")
        
        from ontos.commands.doctor import check_agents_staleness
        result = check_agents_staleness()
        
        assert result.status == "pass"
        assert "up to date" in result.message.lower()

    def test_warns_when_agents_stale(self, tmp_path, monkeypatch):
        """Should warn when AGENTS.md is older than source files."""
        import time
        monkeypatch.chdir(tmp_path)
        
        # Create AGENTS.md first
        (tmp_path / "AGENTS.md").write_text("# AGENTS.md")
        
        # Wait and create source files (newer)
        time.sleep(0.1)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        
        from ontos.commands.doctor import check_agents_staleness
        result = check_agents_staleness()
        
        assert result.status == "warn"
        assert "stale" in result.message.lower()

    def test_warns_when_no_source_files(self, tmp_path, monkeypatch):
        """Should warn when no source files can be found."""
        monkeypatch.chdir(tmp_path)
        # Only AGENTS.md, no config or context map
        (tmp_path / "AGENTS.md").write_text("# AGENTS.md")
        
        from ontos.commands.doctor import check_agents_staleness
        result = check_agents_staleness()
        
        assert result.status == "warn"
        assert "no source files" in result.message.lower()

