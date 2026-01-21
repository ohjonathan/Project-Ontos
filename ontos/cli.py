# ontos/cli.py
"""
Ontos CLI - Unified command interface.

Full argparse implementation per Spec v1.1 Section 4.1.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import ontos
from ontos.ui.json_output import emit_json, emit_error, validate_json_output
from ontos.commands.map import CompactMode


def _get_subprocess_env() -> dict:
    """Get environment for subprocess calls.

    Sets:
    - ONTOS_PROJECT_ROOT: User's current working directory (for legacy script compatibility)
    - PYTHONPATH: Includes both user's project root (for config imports) and
                  package installation root (for ontos.core imports)
    """
    env = os.environ.copy()
    # Use user's CWD as project root, not package installation directory
    try:
        project_root = str(Path.cwd())
    except OSError:
        # CWD deleted or inaccessible; subprocess will fail gracefully
        project_root = "/"
    env.setdefault('ONTOS_PROJECT_ROOT', project_root)
    
    # Package installation root (needed for legacy scripts to import ontos.core)
    package_root = str(Path(__file__).parent.parent)
    
    # Build PYTHONPATH: project_root + package_root + existing
    existing_pythonpath = env.get('PYTHONPATH', '')
    path_parts = [project_root, package_root]
    if existing_pythonpath:
        path_parts.append(existing_pythonpath)
    env['PYTHONPATH'] = os.pathsep.join(path_parts)
    return env


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all commands."""
    # Parent parser for shared options (used by all subparsers)
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-essential output"
    )
    global_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    # Main parser
    parser = argparse.ArgumentParser(
        prog="ontos",
        description="Local-first documentation management for AI-assisted development",
        parents=[global_parser],
    )

    # Global-only options (not needed in subparsers)
    parser.add_argument(
        "--version", "-V",
        action="store_true",
        help="Show version and exit"
    )

    # Subcommands (all inherit from global_parser)
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Register commands with shared parent
    _register_init(subparsers, global_parser)
    _register_map(subparsers, global_parser)
    _register_log(subparsers, global_parser)
    _register_doctor(subparsers, global_parser)
    _register_agents(subparsers, global_parser)
    _register_export(subparsers, global_parser)  # Deprecated alias
    _register_hook(subparsers, global_parser)
    _register_verify(subparsers, global_parser)
    _register_query(subparsers, global_parser)
    _register_migrate(subparsers, global_parser)
    _register_consolidate(subparsers, global_parser)
    _register_promote(subparsers, global_parser)
    _register_scaffold(subparsers, global_parser)
    _register_stub(subparsers, global_parser)

    return parser


# ============================================================================
# Command registration
# ============================================================================

def _register_init(subparsers, parent):
    """Register init command."""
    p = subparsers.add_parser("init", help="Initialize Ontos in a project", parents=[parent])
    p.add_argument("--force", "-f", action="store_true",
                   help="Overwrite existing config and hooks")
    p.add_argument("--skip-hooks", action="store_true",
                   help="Don't install git hooks")
    p.add_argument("--yes", "-y", action="store_true",
                   help="Non-interactive mode: accept all defaults")
    p.set_defaults(func=_cmd_init)


def _register_map(subparsers, parent):
    """Register map command."""
    p = subparsers.add_parser("map", help="Generate context map", parents=[parent])
    p.add_argument("--strict", action="store_true",
                   help="Treat warnings as errors")
    p.add_argument("--output", "-o", type=Path,
                   help="Output path (default: Ontos_Context_Map.md)")
    p.add_argument("--obsidian", action="store_true",
                   help="Enable Obsidian-compatible output (wikilinks, tags)")
    p.add_argument("--compact", nargs="?", const="basic", default="off",
                   choices=["basic", "rich"],
                   help="Compact output: 'basic' (default) or 'rich' (with summaries)")
    p.add_argument("--filter", "-f", metavar="EXPR",
                   help="Filter documents by expression (e.g., 'type:strategy')")
    p.add_argument("--no-cache", action="store_true",
                   help="Bypass document cache (for debugging)")
    p.set_defaults(func=_cmd_map)


def _register_log(subparsers, parent):
    """Register log command."""
    p = subparsers.add_parser("log", help="End session logging", parents=[parent])
    p.add_argument("topic", nargs="?",
                   help="Log entry title/topic")
    p.add_argument("--event-type", "-e",
                   help="Session event type (feature, fix, refactor, exploration, chore, decision, release)")
    p.add_argument("--source", "-s",
                   help="Session source (e.g., tool/agent name)")
    p.add_argument("--epoch",
                   help="(Deprecated) Alias for --source")
    p.add_argument("--title", "-t",
                   help="Log entry title (overrides positional topic)")
    p.add_argument("--auto", action="store_true",
                   help="Skip confirmation prompt")
    p.set_defaults(func=_cmd_log)


def _register_doctor(subparsers, parent):
    """Register doctor command."""
    p = subparsers.add_parser("doctor", help="Health check and diagnostics", parents=[parent])
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Show detailed output")
    p.set_defaults(func=_cmd_doctor)


def _register_agents(subparsers, parent):
    """Register agents command."""
    p = subparsers.add_parser("agents", help="Generate AGENTS.md and .cursorrules", parents=[parent])
    p.add_argument("--force", "-f", action="store_true",
                   help="Overwrite existing files (creates .bak backup)")
    p.add_argument("--format", choices=["agents", "cursor"], default="agents",
                   help="Output format (default: agents)")
    p.add_argument("--all", dest="all_formats", action="store_true",
                   help="Generate both AGENTS.md and .cursorrules")
    p.add_argument("--output", "-o", type=Path,
                   help="Output path for AGENTS.md")
    p.set_defaults(func=_cmd_agents)


def _register_export(subparsers, parent):
    """Register export command (deprecated alias for agents)."""
    p = subparsers.add_parser("export", help="(Deprecated) Use 'ontos agents' instead", parents=[parent])
    p.add_argument("--force", "-f", action="store_true",
                   help="Overwrite existing file")
    p.add_argument("--output", "-o", type=Path,
                   help="Output path")
    p.set_defaults(func=_cmd_export)


def _register_hook(subparsers, parent):
    """Register hook command (internal)."""
    p = subparsers.add_parser("hook", help="Git hook dispatcher (internal)", parents=[parent])
    p.add_argument("hook_type", choices=["pre-push", "pre-commit"],
                   help="Hook type to run")
    p.set_defaults(func=_cmd_hook)


def _register_verify(subparsers, parent):
    """Register verify command (wrapper)."""
    p = subparsers.add_parser("verify", help="Verify describes dates", parents=[parent])
    p.set_defaults(func=_cmd_wrapper, wrapper_name="verify")


def _register_query(subparsers, parent):
    """Register query command (wrapper)."""
    p = subparsers.add_parser("query", help="Search documents", parents=[parent])
    p.add_argument("query_string", nargs="?", help="Search query")
    p.set_defaults(func=_cmd_wrapper, wrapper_name="query")


def _register_migrate(subparsers, parent):
    """Register migrate command (wrapper)."""
    p = subparsers.add_parser("migrate", help="Schema migration", parents=[parent])
    p.set_defaults(func=_cmd_wrapper, wrapper_name="migrate")


def _register_consolidate(subparsers, parent):
    """Register consolidate command (wrapper)."""
    p = subparsers.add_parser("consolidate", help="Archive old logs", parents=[parent])
    p.set_defaults(func=_cmd_wrapper, wrapper_name="consolidate")


def _register_promote(subparsers, parent):
    """Register promote command (wrapper)."""
    p = subparsers.add_parser("promote", help="Promote curation level", parents=[parent])
    p.add_argument("file", nargs="?", help="File to promote")
    p.set_defaults(func=_cmd_wrapper, wrapper_name="promote")


def _register_scaffold(subparsers, parent):
    """Register scaffold command (wrapper)."""
    p = subparsers.add_parser("scaffold", help="Generate scaffolds", parents=[parent])
    p.set_defaults(func=_cmd_wrapper, wrapper_name="scaffold")


def _register_stub(subparsers, parent):
    """Register stub command (wrapper)."""
    p = subparsers.add_parser("stub", help="Create stub documents", parents=[parent])
    p.add_argument("name", nargs="?", help="Stub name")
    p.set_defaults(func=_cmd_wrapper, wrapper_name="stub")


# ============================================================================
# Command handlers
# ============================================================================

def _cmd_init(args) -> int:
    """Handle init command."""
    from ontos.commands.init import init_command, InitOptions

    options = InitOptions(
        path=Path.cwd(),
        force=args.force,
        skip_hooks=getattr(args, "skip_hooks", False),
        yes=getattr(args, "yes", False),
    )
    code, msg = init_command(options)

    if args.json:
        emit_json({
            "status": "success" if code == 0 else "error",
            "message": msg,
            "exit_code": code
        })
    elif not args.quiet:
        print(msg)

    return code


def _cmd_map(args) -> int:
    """Handle map command."""
    from ontos.commands.map import map_command, MapOptions

    options = MapOptions(
        output=args.output,
        strict=args.strict,
        json_output=args.json,
        quiet=args.quiet,
        obsidian=args.obsidian,
        compact=CompactMode(args.compact) if args.compact != "off" else CompactMode.OFF,
        filter_expr=getattr(args, 'filter', None),
        no_cache=getattr(args, 'no_cache', False),
    )

    return map_command(options)


def _cmd_log(args) -> int:
    """Handle log command."""
    from ontos.commands.log import log_command, LogOptions

    options = LogOptions(
        event_type=args.event_type or "",
        source=args.source or "",
        epoch=args.epoch or "",
        title=args.title or "",
        topic=args.topic or "",
        auto=args.auto,
        json_output=args.json,
        quiet=args.quiet,
    )

    return log_command(options)


def _cmd_doctor(args) -> int:
    """Handle doctor command."""
    from ontos.commands.doctor import doctor_command, DoctorOptions, format_doctor_output
    from ontos.ui.json_output import to_json

    options = DoctorOptions(
        verbose=args.verbose,
        json_output=args.json,
    )

    exit_code, result = doctor_command(options)

    if args.json:
        emit_json({
            "status": result.status,
            "checks": [to_json(c) for c in result.checks],
            "summary": {
                "passed": result.passed,
                "failed": result.failed,
                "warnings": result.warnings
            }
        })
    elif not args.quiet:
        print(format_doctor_output(result, verbose=args.verbose))

    return exit_code


def _cmd_agents(args) -> int:
    """Handle agents command."""
    from ontos.commands.agents import agents_command, AgentsOptions

    options = AgentsOptions(
        output_path=args.output,
        force=args.force,
        format=getattr(args, 'format', 'agents'),
        all_formats=getattr(args, 'all_formats', False),
    )

    exit_code, message = agents_command(options)

    if args.json:
        emit_json({
            "status": "success" if exit_code == 0 else "error",
            "message": message,
            "exit_code": exit_code
        })
    elif not args.quiet:
        print(message)

    return exit_code


def _cmd_export(args) -> int:
    """Handle export command (deprecated - delegates to agents)."""
    import sys
    print("Warning: 'ontos export' is deprecated. Use 'ontos agents' instead.", file=sys.stderr)
    
    from ontos.commands.agents import agents_command, AgentsOptions

    options = AgentsOptions(
        output_path=args.output,
        force=args.force,
        format="agents",
        all_formats=False,
    )

    exit_code, message = agents_command(options)

    if args.json:
        emit_json({
            "status": "success" if exit_code == 0 else "error",
            "message": message,
            "exit_code": exit_code
        })
    elif not args.quiet:
        print(message)

    return exit_code


def _cmd_hook(args) -> int:
    """Handle hook command."""
    from ontos.commands.hook import hook_command, HookOptions

    options = HookOptions(
        hook_type=args.hook_type,
        args=[],
    )

    return hook_command(options)


def _cmd_wrapper(args) -> int:
    """
    Handle wrapper commands that delegate to legacy scripts.

    Per Decision: Option A with JSON validation fallback.
    """
    wrapper_name = args.wrapper_name

    # Find the legacy script
    scripts_dir = Path(__file__).parent / "_scripts"
    script_map = {
        "verify": "ontos_verify.py",
        "query": "ontos_query.py",
        "migrate": "ontos_migrate_schema.py",
        "consolidate": "ontos_consolidate.py",
        "promote": "ontos_promote.py",
        "scaffold": "ontos_scaffold.py",
        "stub": "ontos_stub.py",
    }

    script_name = script_map.get(wrapper_name)
    if not script_name:
        if args.json:
            emit_error(f"Unknown wrapper command: {wrapper_name}", "E_UNKNOWN_CMD")
        else:
            print(f"Error: Unknown wrapper command: {wrapper_name}", file=sys.stderr)
        return 5

    script_path = scripts_dir / script_name
    if not script_path.exists():
        if args.json:
            emit_error(f"Script not found: {script_name}", "E_NOT_FOUND")
        else:
            print(f"Error: Script not found: {script_path}", file=sys.stderr)
        return 5

    # Build command
    cmd = [sys.executable, str(script_path)]

    # Pass through JSON flag if requested
    if args.json:
        cmd.append("--json")

    # Run the wrapper
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=_get_subprocess_env())

        # JSON validation per Decision
        if args.json:
            if validate_json_output(result.stdout):
                print(result.stdout, end="")
            else:
                emit_error(
                    message=f"Command '{wrapper_name}' does not support JSON output",
                    code="E_JSON_UNSUPPORTED",
                    details=result.stdout[:500] if result.stdout else result.stderr[:500]
                )
        else:
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, file=sys.stderr, end="")

        return result.returncode

    except Exception as e:
        if args.json:
            emit_error(f"Wrapper execution failed: {e}", "E_EXEC_FAIL")
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 5


# ============================================================================
# Main entry point
# ============================================================================

def main() -> int:
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Workaround for argparse parent inheritance issue:
    # When --json is before the command, it's consumed by parent parser
    # but not propagated to subparser namespace. Check sys.argv as fallback.
    if '--json' in sys.argv and not args.json:
        args.json = True
    if '-q' in sys.argv or '--quiet' in sys.argv:
        if not getattr(args, 'quiet', False):
            args.quiet = True

    # Handle --version
    if args.version:
        if args.json:
            emit_json({"version": ontos.__version__})
        else:
            print(f"ontos {ontos.__version__}")
        return 0

    # No command specified
    if not args.command:
        if args.json:
            emit_error("No command specified", "E_NO_CMD")
        else:
            parser.print_help()
        return 0

    # Route to command handler
    try:
        return args.func(args)
    except KeyboardInterrupt:
        if not args.quiet:
            print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        if args.json:
            emit_error(f"Internal error: {e}", "E_INTERNAL")
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    sys.exit(main())
