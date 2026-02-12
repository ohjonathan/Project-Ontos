"""Tests for CLI (Phase 4)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestCLIGlobalOptions:
    """Tests for CLI global options."""

    def test_version_flag(self):
        """--version should print version."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "--version"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "ontos" in result.stdout.lower()

    def test_version_json(self):
        """--json --version should output JSON."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "--json", "--version"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "version" in data

    def test_help_flag(self):
        """--help should print help."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "commands" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_no_command_prints_help(self):
        """No command should print help."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos"],
            capture_output=True, text=True
        )
        assert result.returncode == 2


class TestCLICommands:
    """Tests for CLI command routing."""

    def test_init_help(self):
        """init --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "init", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "force" in result.stdout.lower()

    def test_map_help(self):
        """map --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "map", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "strict" in result.stdout.lower()

    def test_doctor_help(self):
        """doctor --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "doctor", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "verbose" in result.stdout.lower()

    def test_link_check_help(self):
        """link-check --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "link-check", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "--scope" in result.stdout

    def test_export_help(self):
        """export --help should work (v3.2: subcommand pattern)."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "export", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        # v3.2: export now has subcommands (data, claude)
        assert "data" in result.stdout.lower()
        assert "claude" in result.stdout.lower()

    def test_hook_help(self):
        """hook --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "hook", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0


class TestCLIErrorRouting:
    """Tests for typed error handling in cli.main()."""

    def test_main_routes_ontos_user_error_json(self, monkeypatch, capsys):
        """OntosUserError should return exit 2 with JSON envelope."""
        import argparse
        import ontos.cli as cli
        from ontos.core.errors import OntosUserError

        class _FakeParser:
            def parse_args(self):
                return argparse.Namespace(
                    command="fake",
                    version=False,
                    json=True,
                    quiet=False,
                    func=lambda _args: (_ for _ in ()).throw(
                        OntosUserError("bad input", code="E_USER_INPUT", details="detail")
                    ),
                )

            def print_help(self):
                pass

        monkeypatch.setattr(cli, "_first_command", lambda _argv: "fake")
        monkeypatch.setattr(cli, "create_parser", lambda include_hidden=True: _FakeParser())
        monkeypatch.setattr(cli.sys, "argv", ["ontos", "--json", "fake"])

        exit_code = cli.main()
        captured = capsys.readouterr()
        payload = json.loads(captured.out)

        assert exit_code == 2
        assert payload["status"] == "error"
        assert payload["error"]["code"] == "E_USER_INPUT"
        assert payload["error"]["details"] == "detail"

    def test_main_routes_unexpected_error_json(self, monkeypatch, capsys):
        """Unexpected errors should return exit 5 with E_INTERNAL envelope."""
        import argparse
        import ontos.cli as cli

        class _FakeParser:
            def parse_args(self):
                return argparse.Namespace(
                    command="fake",
                    version=False,
                    json=True,
                    quiet=False,
                    func=lambda _args: (_ for _ in ()).throw(RuntimeError("boom")),
                )

            def print_help(self):
                pass

        monkeypatch.setattr(cli, "_first_command", lambda _argv: "fake")
        monkeypatch.setattr(cli, "create_parser", lambda include_hidden=True: _FakeParser())
        monkeypatch.setattr(cli.sys, "argv", ["ontos", "--json", "fake"])

        exit_code = cli.main()
        captured = capsys.readouterr()
        payload = json.loads(captured.out)

        assert exit_code == 5
        assert payload["status"] == "error"
        assert payload["error"]["code"] == "E_INTERNAL"


class TestCLIDoctorCommand:
    """Tests for doctor command via CLI."""

    def test_doctor_runs(self, tmp_path, monkeypatch):
        """doctor command should run."""
        monkeypatch.chdir(tmp_path)
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "doctor"],
            capture_output=True, text=True
        )
        # Will fail some checks, but should run
        assert "configuration" in result.stdout.lower() or "fail" in result.stdout.lower()

    def test_doctor_json(self, tmp_path, monkeypatch):
        """--json doctor should output JSON."""
        monkeypatch.chdir(tmp_path)
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "--json", "doctor"],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        assert "status" in data
        assert "checks" in data


class TestCLIExportCommand:
    """Tests for export command via CLI."""

    def test_export_creates_file(self, tmp_path, monkeypatch):
        """export should create AGENTS.md (deprecated alias for agents)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        (tmp_path / ".ontos-internal").mkdir()

        result = subprocess.run(
            [sys.executable, "-m", "ontos", "export"],
            capture_output=True, text=True
        )

        assert result.returncode == 0
        assert (tmp_path / "CLAUDE.md").exists()  # v3.2: export creates CLAUDE.md (delegates to export claude)


class TestCLIInitCommand:
    """Tests for init command via CLI."""

    def test_init_in_fresh_git_repo(self, tmp_path, monkeypatch):
        """init should work in a fresh git repo."""
        monkeypatch.chdir(tmp_path)
        # Create git repo
        subprocess.run(["git", "init"], capture_output=True, cwd=tmp_path)

        result = subprocess.run(
            [sys.executable, "-m", "ontos", "init"],
            capture_output=True, text=True
        )

        assert result.returncode == 0
        assert (tmp_path / ".ontos.toml").exists()

    def test_init_fails_outside_git(self, tmp_path, monkeypatch):
        """init should fail outside git repo."""
        monkeypatch.chdir(tmp_path)

        result = subprocess.run(
            [sys.executable, "-m", "ontos", "init"],
            capture_output=True, text=True
        )

        assert result.returncode == 2
        assert "git" in result.stdout.lower()
