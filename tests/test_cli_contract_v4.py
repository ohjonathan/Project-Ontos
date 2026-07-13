"""Characterization tests for the schema-v4 CLI contract and registry."""

from __future__ import annotations

import argparse
import json
from argparse import Namespace

from ontos.cli import (
    _cmd_consolidate,
    _cmd_env,
    _cmd_promote,
    _emit_handler_result_json,
    create_parser,
    main,
)
from ontos.command_registry import COMMAND_SPECS, command_path
from ontos.ui.json_output import (
    ExitCategory,
    ExitCode,
    _exit_category,
    emit_command_error,
    emit_command_success,
)


def _subparsers(parser: argparse.ArgumentParser) -> argparse._SubParsersAction:
    return next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )


def _argument_contract(parser: argparse.ArgumentParser) -> dict[str, object]:
    ignored = {"help", "json", "quiet"}
    return {
        action.dest: (
            tuple(action.option_strings),
            action.nargs,
            tuple(action.choices) if action.choices is not None else None,
            action.required,
        )
        for action in parser._actions
        if action.dest not in ignored
    }


def test_registry_is_the_complete_unique_top_level_source() -> None:
    public = create_parser(include_hidden=False)
    complete = create_parser(include_hidden=True)

    assert len({spec.name for spec in COMMAND_SPECS}) == len(COMMAND_SPECS)
    assert set(_subparsers(public).choices) == {
        spec.name for spec in COMMAND_SPECS if not spec.hidden
    }
    assert set(_subparsers(complete).choices) == {
        spec.name for spec in COMMAND_SPECS
    }
    assert all(spec.parser_builder and spec.handler for spec in COMMAND_SPECS)
    assert all(choice.get_default("_handler_name") for choice in _subparsers(complete).choices.values())


def test_exit_code_four_remains_reserved() -> None:
    assert {int(code) for code in ExitCode} == {0, 1, 2, 3, 5, 130}
    assert 4 not in {int(code) for code in ExitCode}
    assert _exit_category(
        execution_status="error",
        exit_code=4,
        result_status="error",
    ) == ExitCategory.ERROR.value


def test_aliases_share_canonical_argument_contracts() -> None:
    choices = _subparsers(create_parser(include_hidden=True)).choices

    assert _argument_contract(choices["tree"]) == _argument_contract(choices["map"])
    assert _argument_contract(choices["validate"]) == _argument_contract(
        choices["verify"]
    )


def test_global_flags_survive_both_positions_but_not_double_dash_data() -> None:
    parser = create_parser(include_hidden=False)

    assert parser.parse_args(["--json", "doctor"]).json is True
    assert parser.parse_args(["doctor", "--json"]).json is True
    assert parser.parse_args(["--quiet", "doctor"]).quiet is True
    assert parser.parse_args(["doctor", "--quiet"]).quiet is True

    literal = parser.parse_args(["log", "--auto", "--", "--json"])
    assert literal.json is False
    assert literal.topic == "--json"


def test_json_argparse_errors_use_the_v4_envelope(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["ontos", "--json", "stub", "--definitely-invalid"],
    )
    assert main() == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert captured.err == ""
    assert payload["schema_version"] == "4.0"
    assert payload["command"] == "stub"
    assert payload["error"]["code"] == "E_USAGE"
    assert payload["result"]["exit_category"] == "usage"


def test_json_verify_missing_target_is_a_usage_envelope(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["ontos", "--json", "verify"])
    assert main() == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert captured.err == ""
    assert payload["command"] == "verify"
    assert payload["error"]["code"] == "E_USER_INPUT"
    assert payload["result"]["exit_category"] == "usage"


def test_canonical_nested_command_paths() -> None:
    assert command_path(Namespace(command="mcp", mcp_command="install")) == "mcp install"
    assert command_path(Namespace(command="export", export_command="data")) == "export data"
    assert command_path(Namespace(command="verify")) == "verify"


def test_v4_envelope_separates_execution_findings_and_count_basis(capsys) -> None:
    emit_command_error(
        command="map",
        exit_code=1,
        code="E_COMMAND_FAILED",
        message="Generated with issues",
        data={
            "result_status": "failing",
            "summary": {"errors": 2, "warnings": 3},
        },
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["schema_version"] == "4.0"
    assert payload["status"] == "success"
    assert payload["error"] is None
    assert payload["result"]["status"] == "findings"
    assert payload["result"]["exit_category"] == "findings"
    assert payload["result"]["diagnostics"] == {
        "basis": "data.summary",
        "complete": True,
        "counts": {"errors": 2, "warnings": 3},
    }


def test_v4_envelope_marks_unknown_counts_and_incomplete_diagnostics(capsys) -> None:
    emit_command_success(
        command="link-check",
        exit_code=0,
        message="Scan complete",
        data={
            "result_status": "clean",
            "summary": {"load_warnings": 1, "broken_references": 0},
        },
    )
    incomplete = json.loads(capsys.readouterr().out)
    assert incomplete["result"]["status"] == "incomplete"

    _emit_handler_result_json(
        command="verify",
        exit_code=0,
        message="Nothing to verify",
    )
    tuple_result = json.loads(capsys.readouterr().out)
    assert tuple_result["data"] == {"summary": "Nothing to verify"}
    assert tuple_result["result"]["diagnostics"]["complete"] is False


def test_env_json_forces_structured_env_dialect(monkeypatch, capsys) -> None:
    import ontos.commands.env as env_module

    seen = []

    def fake_run(options):
        seen.append(options)
        return 0, json.dumps({"$schema": "ontos-env-v1", "manifests": []})

    monkeypatch.setattr(env_module, "_run_env_command", fake_run)
    result = _cmd_env(
        Namespace(json=True, quiet=False, write=False, force=False, format="text")
    )
    payload = json.loads(capsys.readouterr().out)

    assert result == 0
    assert seen[0].format == "json"
    assert payload["data"]["$schema"] == "ontos-env-v1"


def test_json_workflows_force_noninteractive_options(monkeypatch, capsys) -> None:
    import ontos.commands.consolidate as consolidate_module
    import ontos.commands.promote as promote_module

    observed = {}

    def fake_consolidate(options):
        observed["all"] = options.all
        return 0, "done"

    def fake_promote(options):
        observed["yes"] = options.yes
        return 0, "done"

    monkeypatch.setattr(
        consolidate_module, "_run_consolidate_command", fake_consolidate
    )
    monkeypatch.setattr(promote_module, "_run_promote_command", fake_promote)

    assert _cmd_consolidate(
        Namespace(
            count=15,
            by_age=False,
            days=30,
            dry_run=False,
            quiet=False,
            json=True,
            all=False,
        )
    ) == 0
    capsys.readouterr()
    assert _cmd_promote(
        Namespace(
            files=[],
            check=True,
            all_ready=False,
            quiet=False,
            json=True,
            yes=False,
            scope=None,
        )
    ) == 0
    capsys.readouterr()

    assert observed == {"all": True, "yes": True}
