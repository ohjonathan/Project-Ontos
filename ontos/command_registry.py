"""Declarative metadata for the public Ontos command surface.

Argument definitions remain close to their handlers in :mod:`ontos.cli`, but
this registry is the single source of truth for top-level command discovery,
visibility, aliases, and nested command-path resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Optional, Protocol


class ResultKind(str, Enum):
    """The kind of result a command normally produces."""

    OPERATION = "operation"
    DIAGNOSTIC = "diagnostic"


@dataclass(frozen=True)
class CommandSpec:
    """Metadata needed to register and identify one top-level command."""

    name: str
    registrar: str
    result_kind: ResultKind = ResultKind.OPERATION
    hidden: bool = False
    alias_for: Optional[str] = None
    subcommand_dest: Optional[str] = None


COMMAND_SPECS = (
    CommandSpec("activate", "_register_activate", ResultKind.DIAGNOSTIC),
    CommandSpec("init", "_register_init"),
    CommandSpec("map", "_register_map", ResultKind.DIAGNOSTIC),
    CommandSpec("log", "_register_log"),
    CommandSpec("doctor", "_register_doctor", ResultKind.DIAGNOSTIC),
    CommandSpec("maintain", "_register_maintain", ResultKind.DIAGNOSTIC),
    CommandSpec("link-check", "_register_link_check", ResultKind.DIAGNOSTIC),
    CommandSpec("rename", "_register_rename"),
    CommandSpec("retrofit", "_register_retrofit"),
    CommandSpec("env", "_register_env"),
    CommandSpec("mcp", "_register_mcp", subcommand_dest="mcp_command"),
    CommandSpec("serve", "_register_serve"),
    CommandSpec("agents", "_register_agents"),
    CommandSpec("export", "_register_export", subcommand_dest="export_command"),
    CommandSpec("verify", "_register_verify", ResultKind.DIAGNOSTIC),
    CommandSpec("query", "_register_query", ResultKind.DIAGNOSTIC),
    CommandSpec("schema-migrate", "_register_schema_migrate", ResultKind.DIAGNOSTIC),
    CommandSpec("consolidate", "_register_consolidate"),
    CommandSpec("promote", "_register_promote"),
    CommandSpec("scaffold", "_register_scaffold"),
    CommandSpec("stub", "_register_stub"),
    CommandSpec("migration-report", "_register_migration_report", ResultKind.DIAGNOSTIC),
    CommandSpec("migrate", "_register_migrate_convenience"),
    CommandSpec(
        "agent-export",
        "_register_agent_export",
        hidden=True,
        alias_for="agents",
    ),
    CommandSpec("hook", "_register_hook", hidden=True),
    CommandSpec(
        "tree",
        "_register_tree_alias",
        ResultKind.DIAGNOSTIC,
        hidden=True,
        alias_for="map",
    ),
    CommandSpec(
        "validate",
        "_register_validate_alias",
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
