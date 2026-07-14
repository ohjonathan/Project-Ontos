"""Fast, recursive coverage for the declarative CLI help surface."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterator, Tuple

import pytest

from ontos.cli import create_parser
from ontos.command_registry import iter_command_specs


CommandPath = Tuple[str, ...]


def _walk_parsers(
    parser: argparse.ArgumentParser,
    path: CommandPath = (),
) -> Iterator[tuple[CommandPath, argparse.ArgumentParser]]:
    yield path, parser
    actions = [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    assert len(actions) <= 1, f"multiple subparser registries at {' '.join(path) or 'root'}"
    if not actions:
        return
    for name, child in actions[0].choices.items():
        yield from _walk_parsers(child, path + (name,))


@pytest.fixture(scope="module")
def parser_by_path() -> dict[CommandPath, argparse.ArgumentParser]:
    return dict(_walk_parsers(create_parser(include_hidden=True)))


def test_recursive_parser_tree_matches_command_registry(parser_by_path):
    actual = set(parser_by_path) - {()}
    expected = set()
    for spec in iter_command_specs(include_hidden=True):
        expected.add((spec.name,))
        expected.update((spec.name, child.name) for child in spec.children)

    assert actual == expected


def test_every_registered_parser_formats_help_in_process(parser_by_path):
    for path, parser in parser_by_path.items():
        help_text = parser.format_help()
        expected_prog = "ontos" if not path else f"ontos {' '.join(path)}"
        assert help_text.startswith(f"usage: {expected_prog}")
        assert "-h, --help" in help_text


@pytest.mark.parametrize("command", ["verify", "query", "scaffold"])
def test_command_format_help_matches_golden(command, parser_by_path, assert_help_parity):
    golden = (
        Path(__file__).parent / "commands" / "golden" / f"{command}_help.txt"
    ).read_text(encoding="utf-8")

    assert_help_parity(parser_by_path[(command,)].format_help(), golden)


def test_public_help_visibility_comes_from_registry():
    public_paths = dict(_walk_parsers(create_parser(include_hidden=False)))
    public_names = {path[0] for path in public_paths if len(path) == 1}
    expected = {spec.name for spec in iter_command_specs(include_hidden=False)}

    assert public_names == expected


def test_nested_help_retains_command_specific_options(parser_by_path):
    expected_options = {
        ("rename",): "--apply",
        ("map",): "--sync-agents",
        ("mcp", "install"): "--scope",
        ("export", "data"): "--output",
        ("export", "claude"): "--output",
        ("migration-report",): "--output",
        ("migrate",): "--out-dir",
        ("schema-migrate",): "--check",
        ("promote",): "--check",
        ("consolidate",): "--count",
        ("stub",): "--goal",
    }
    for path, option in expected_options.items():
        assert option in parser_by_path[path].format_help()


def test_scope_option_is_registered_consistently(parser_by_path):
    scoped_paths = {
        ("map",),
        ("maintain",),
        ("query",),
        ("verify",),
        ("scaffold",),
        ("promote",),
        ("schema-migrate",),
        ("agents",),
        ("doctor",),
        ("export", "data"),
        ("migration-report",),
        ("migrate",),
        ("tree",),
        ("validate",),
        ("agent-export",),
        ("link-check",),
        ("rename",),
    }
    for path in scoped_paths:
        assert "--scope" in parser_by_path[path].format_help()
    assert "--scope" not in parser_by_path[("export", "claude")].format_help()
