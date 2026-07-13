"""Declarative metadata for the public Ontos command surface.

This registry is the single source of truth for discovery, parser builders,
handlers, visibility, aliases, result kinds, and nested command paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterator, Mapping, Optional, Protocol, Tuple


class ResultKind(str, Enum):
    """The kind of result a command normally produces."""

    OPERATION = "operation"
    DIAGNOSTIC = "diagnostic"


@dataclass(frozen=True)
class ArgumentSpec:
    """Declarative argparse argument description for simple command entries."""

    flags: Tuple[str, ...]
    options: Mapping[str, Any]


@dataclass(frozen=True)
class SubcommandSpec:
    name: str
    handler: str


@dataclass(frozen=True)
class CommandSpec:
    """Complete registration and dispatch metadata for one command."""

    name: str
    parser_builder: str
    handler: str
    result_kind: ResultKind = ResultKind.OPERATION
    hidden: bool = False
    alias_for: Optional[str] = None
    subcommand_dest: Optional[str] = None
    arguments: Tuple[ArgumentSpec, ...] = ()
    children: Tuple[SubcommandSpec, ...] = ()


COMMAND_SPECS = (
    CommandSpec("activate", "_register_activate", "_cmd_activate", ResultKind.DIAGNOSTIC),
    CommandSpec("init", "_register_init", "_cmd_init"),
    CommandSpec("map", "_register_map", "_cmd_map", ResultKind.DIAGNOSTIC),
    CommandSpec("log", "_register_log", "_cmd_log"),
    CommandSpec("doctor", "_register_doctor", "_cmd_doctor", ResultKind.DIAGNOSTIC),
    CommandSpec("maintain", "_register_maintain", "_cmd_maintain", ResultKind.DIAGNOSTIC),
    CommandSpec("link-check", "_register_link_check", "_cmd_link_check", ResultKind.DIAGNOSTIC),
    CommandSpec("rename", "_register_rename", "_cmd_rename"),
    CommandSpec("retrofit", "_register_retrofit", "_cmd_retrofit"),
    CommandSpec("env", "_register_env", "_cmd_env"),
    CommandSpec(
        "mcp", "_register_mcp", "_cmd_mcp_root", subcommand_dest="mcp_command",
        children=(SubcommandSpec("install", "_cmd_mcp_install"), SubcommandSpec("uninstall", "_cmd_mcp_uninstall"), SubcommandSpec("print-config", "_cmd_mcp_print_config")),
    ),
    CommandSpec("serve", "_register_serve", "_cmd_serve"),
    CommandSpec("agents", "_register_agents", "_cmd_agents"),
    CommandSpec(
        "export", "_register_export", "_cmd_export_deprecated", subcommand_dest="export_command",
        children=(SubcommandSpec("data", "_cmd_export_data"), SubcommandSpec("claude", "_cmd_export_claude")),
    ),
    CommandSpec("verify", "_register_verify", "_cmd_verify", ResultKind.DIAGNOSTIC),
    CommandSpec("query", "_register_query", "_cmd_query", ResultKind.DIAGNOSTIC),
    CommandSpec("schema-migrate", "_register_schema_migrate", "_cmd_schema_migrate", ResultKind.DIAGNOSTIC),
    CommandSpec("consolidate", "_register_consolidate", "_cmd_consolidate"),
    CommandSpec("promote", "_register_promote", "_cmd_promote"),
    CommandSpec("scaffold", "_register_scaffold", "_cmd_scaffold"),
    CommandSpec("stub", "_register_stub", "_cmd_stub"),
    CommandSpec("migration-report", "_register_migration_report", "_cmd_migration_report", ResultKind.DIAGNOSTIC),
    CommandSpec("migrate", "_register_migrate_convenience", "_cmd_migrate_convenience"),
    CommandSpec(
        "agent-export",
        "_register_agent_export",
        "_cmd_agent_export",
        hidden=True,
        alias_for="agents",
    ),
    CommandSpec("hook", "_register_hook", "_cmd_hook", hidden=True),
    CommandSpec(
        "tree",
        "_register_tree_alias",
        "_cmd_tree",
        ResultKind.DIAGNOSTIC,
        hidden=True,
        alias_for="map",
    ),
    CommandSpec(
        "validate",
        "_register_validate_alias",
        "_cmd_validate",
        ResultKind.DIAGNOSTIC,
        hidden=True,
        alias_for="verify",
    ),
)


_BY_NAME = {spec.name: spec for spec in COMMAND_SPECS}
if len(_BY_NAME) != len(COMMAND_SPECS):  # pragma: no cover - import-time invariant
    raise RuntimeError("Command registry contains duplicate top-level names")


HIDDEN_COMMANDS = frozenset(spec.name for spec in COMMAND_SPECS if spec.hidden)


def iter_command_specs(*, include_hidden: bool = False) -> Iterator[CommandSpec]:
    """Yield commands in stable help/registration order."""

    for spec in COMMAND_SPECS:
        if include_hidden or not spec.hidden:
            yield spec


def get_command_spec(name: Optional[str]) -> Optional[CommandSpec]:
    """Return metadata for a parsed top-level command, if known."""

    if name is None:
        return None
    return _BY_NAME.get(name)


def handler_name(args: "ParsedCommand") -> Optional[str]:
    """Resolve a top-level or nested handler from declarative metadata."""

    spec = get_command_spec(getattr(args, "command", None))
    if spec is None:
        return None
    if spec.subcommand_dest:
        selected = getattr(args, spec.subcommand_dest, None)
        for child in spec.children:
            if child.name == selected:
                return child.handler
    return spec.handler


class ParsedCommand(Protocol):
    """Small namespace protocol used by :func:`command_path`."""

    command: Optional[str]


def command_path(args: ParsedCommand) -> str:
    """Return the canonical, space-joined path for a parsed command."""

    name = getattr(args, "command", None)
    spec = get_command_spec(name)
    if spec is None:
        return name or "ontos"
    if spec.subcommand_dest:
        child = getattr(args, spec.subcommand_dest, None)
        if child:
            return f"{spec.name} {child}"
    return spec.name
