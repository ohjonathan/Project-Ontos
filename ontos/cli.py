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
    _register_env(subparsers, global_parser)
    _register_agents(subparsers, global_parser)
    _register_agent_export(subparsers, global_parser)  # Deprecated alias
    _register_export(subparsers, global_parser)
    _register_hook(subparsers, global_parser)
    _register_verify(subparsers, global_parser)
    _register_query(subparsers, global_parser)
    _register_schema_migrate(subparsers, global_parser)
    _register_consolidate(subparsers, global_parser)
    _register_promote(subparsers, global_parser)
    _register_scaffold(subparsers, global_parser)
    _register_stub(subparsers, global_parser)
    _register_migration_report(subparsers, global_parser)
    _register_migrate_convenience(subparsers, global_parser)

    # Legacy Aliases (v3.2)
    _register_tree_alias(subparsers, global_parser)
    _register_validate_alias(subparsers, global_parser)

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
    # Scaffold flags (mutually exclusive)
    scaffold_group = p.add_mutually_exclusive_group()
    scaffold_group.add_argument("--scaffold", action="store_true",
                                help="Auto-scaffold untagged files (uses docs/ scope)")
    scaffold_group.add_argument("--no-scaffold", action="store_true",
                                help="Skip scaffold prompt")
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
    p.add_argument("--sync-agents", action="store_true",
                   help="Also sync AGENTS.md if it exists")
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


def _register_env(subparsers, parent):
    """Register env command."""
    p = subparsers.add_parser(
        "env",
        help="Detect and document environment manifests",
        parents=[parent]
    )
    p.add_argument(
        "--write", "-w",
        action="store_true",
        help="Write environment documentation to .ontos/environment.md"
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing environment.md (required with --write if file exists)"
    )
    p.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    p.set_defaults(func=_cmd_env)


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


def _register_agent_export(subparsers, parent):
    """Register agent-export command (deprecated alias for agents)."""
    p = subparsers.add_parser("agent-export", help="(Deprecated) Use 'ontos agents' instead", parents=[parent])
    p.add_argument("--force", "-f", action="store_true",
                   help="Overwrite existing file")
    p.add_argument("--output", "-o", type=Path,
                   help="Output path")
    p.set_defaults(func=_cmd_agent_export)


def _register_export(subparsers, parent):
    """Register export command with subcommands."""
    export_parser = subparsers.add_parser(
        "export",
        help="Export documents (use 'export data' or 'export claude')",
        parents=[parent]
    )
    export_subparsers = export_parser.add_subparsers(
        dest="export_command",
        title="export commands",
        metavar="<command>"
    )

    # export data
    data_parser = export_subparsers.add_parser(
        "data",
        help="Export documents as structured JSON",
        parents=[parent]
    )
    data_parser.add_argument("-o", "--output", type=Path,
                             help="Output file path")
    data_parser.add_argument("--type",
                             help="Filter by document type (comma-separated)")
    data_parser.add_argument("--status",
                             help="Filter by status (comma-separated)")
    data_parser.add_argument("--concept",
                             help="Filter by concept (comma-separated)")
    data_parser.add_argument("--no-content", action="store_true",
                             help="Exclude document content")
    data_parser.add_argument("--deterministic", action="store_true",
                             help="Stable output for testing")
    data_parser.add_argument("--force", "-f", action="store_true",
                             help="Overwrite existing file")
    data_parser.set_defaults(func=_cmd_export_data)

    # export claude
    claude_parser = export_subparsers.add_parser(
        "claude",
        help="Generate CLAUDE.md file",
        parents=[parent]
    )
    claude_parser.add_argument("-o", "--output", type=Path,
                               help="Output path (default: CLAUDE.md)")
    claude_parser.add_argument("--force", "-f", action="store_true",
                               help="Overwrite existing file")
    claude_parser.set_defaults(func=_cmd_export_claude)

    # Deprecated: bare 'export' defaults to 'export claude' with warning
    export_parser.set_defaults(func=_cmd_export_deprecated)


def _register_hook(subparsers, parent):
    """Register hook command (internal)."""
    p = subparsers.add_parser("hook", help="Git hook dispatcher (internal)", parents=[parent])
    p.add_argument("hook_type", choices=["pre-push", "pre-commit"],
                   help="Hook type to run")
    p.add_argument("extra_args", nargs="*", help="Extra arguments from git")
    p.set_defaults(func=_cmd_hook)


def _register_verify(subparsers, parent):
    """Register verify command."""
    p = subparsers.add_parser(
        "verify",
        help="Verify document describes dates",
        parents=[parent]
    )
    p.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="Specific file to verify"
    )
    p.add_argument(
        "--all", "-a",
        action="store_true",
        help="Verify all stale documents interactively"
    )
    p.add_argument(
        "--date", "-d",
        help="Verification date (YYYY-MM-DD, default: today)"
    )
    p.set_defaults(func=_cmd_verify)


def _register_query(subparsers, parent):
    """Register query command."""
    p = subparsers.add_parser(
        "query",
        help="Search and analyze document graph",
        parents=[parent]
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--depends-on", metavar="ID",
                       help="What does this document depend on?")
    group.add_argument("--depended-by", metavar="ID",
                       help="What documents depend on this one?")
    group.add_argument("--concept", metavar="TAG",
                       help="Find all documents with this concept")
    group.add_argument("--stale", metavar="DAYS", type=int,
                       help="Find documents not updated in N days")
    group.add_argument("--health", action="store_true",
                       help="Show graph health metrics")
    group.add_argument("--list-ids", action="store_true",
                       help="List all document IDs")
    
    p.add_argument("--dir", type=Path,
                   help="Documentation directory to scan")
    p.set_defaults(func=_cmd_query)


def _register_schema_migrate(subparsers, parent):
    """Register schema migration command."""
    p = subparsers.add_parser(
        "schema-migrate",
        help="Migrate document schema versions",
        parents=[parent]
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true",
                       help="Check which files need migration")
    group.add_argument("--dry-run", "-n", action="store_true",
                       help="Preview changes without applying")
    group.add_argument("--apply", action="store_true",
                       help="Apply schema migrations")
    
    p.add_argument("--dirs", nargs="+", type=Path,
                   help="Directories to scan")
    p.set_defaults(func=_cmd_schema_migrate)


def _register_consolidate(subparsers, parent):
    """Register consolidate command."""
    p = subparsers.add_parser(
        "consolidate",
        help="Archive old session logs",
        parents=[parent]
    )
    p.add_argument(
        "--count",
        type=int,
        default=15,
        help="Number of newest logs to keep (default: 15)"
    )
    p.add_argument(
        "--by-age",
        action="store_true",
        help="Use age-based instead of count-based"
    )
    p.add_argument(
        "--days",
        type=int,
        default=30,
        help="Age threshold in days, requires --by-age (default: 30)"
    )
    p.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview changes without applying"
    )
    p.add_argument(
        "--all", "-a",
        action="store_true",
        help="Process all logs without prompting"
    )
    p.set_defaults(func=_cmd_consolidate)


def _register_promote(subparsers, parent):
    """Register promote command."""
    p = subparsers.add_parser(
        "promote",
        help="Promote documents to Level 2",
        parents=[parent]
    )
    p.add_argument("files", nargs="*", type=Path, help="Specific files to promote")
    p.add_argument("--check", action="store_true", help="Show promotable documents")
    p.add_argument("--all-ready", action="store_true", help="Promote all ready documents")
    p.set_defaults(func=_cmd_promote)


def _register_scaffold(subparsers, parent):
    """Register scaffold command."""
    p = subparsers.add_parser(
        "scaffold",
        help="Add frontmatter to markdown files",
        description="Add frontmatter to markdown files",
        parents=[parent]
    )
    p.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="File(s) or directory to scaffold (default: scan all)"
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="Apply scaffolding (default: dry-run)"
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    p.set_defaults(func=_cmd_scaffold)


def _register_stub(subparsers, parent):
    """Register stub command."""
    p = subparsers.add_parser(
        "stub",
        help="Create new document stub",
        parents=[parent]
    )
    p.add_argument("--goal", "-g", help="Goal description")
    p.add_argument("--type", "-t", dest="doc_type", help="Document type")
    p.add_argument("--id", help="Document ID")
    p.add_argument("--output", "-o", type=Path, help="Output file path")
    p.add_argument("--depends-on", "-d", help="Comma-separated list of dependencies")
    p.set_defaults(func=_cmd_stub)


def _register_migration_report(subparsers, parent):
    """Register migration-report command."""
    p = subparsers.add_parser(
        "migration-report",
        help="Analyze documents for migration safety",
        parents=[parent]
    )
    p.add_argument("-o", "--output", type=Path,
                   help="Output file path")
    p.add_argument("--format", choices=["md", "json"], default="md",
                   help="Output format (default: md)")
    p.add_argument("--force", "-f", action="store_true",
                   help="Overwrite existing file")
    p.set_defaults(func=_cmd_migration_report)


def _register_migrate_convenience(subparsers, parent):
    """Register migrate convenience command."""
    p = subparsers.add_parser(
        "migrate",
        help="Generate migration artifacts (snapshot + report)",
        parents=[parent]
    )
    p.add_argument("--out-dir", type=Path, default=Path("./migration/"),
                   help="Output directory (default: ./migration/)")
    p.add_argument("--force", "-f", action="store_true",
                   help="Overwrite existing files")
    p.set_defaults(func=_cmd_migrate_convenience)


def _register_tree_alias(subparsers, parent):
    """Register tree command (deprecated alias for map)."""
    p = subparsers.add_parser("tree", help="(Deprecated) Use 'ontos map' instead", parents=[parent])
    # Include map arguments to maintain compatibility
    p.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    p.add_argument("--output", "-o", type=Path, help="Output path")
    p.add_argument("--obsidian", action="store_true", help="Enable Obsidian output")
    p.add_argument("--compact", nargs="?", const="basic", default="off",
                   choices=["basic", "rich"], help="Compact output")
    p.add_argument("--filter", "-f", metavar="EXPR", help="Filter documents")
    p.add_argument("--no-cache", action="store_true", help="Bypass cache")
    p.set_defaults(func=_cmd_tree)


def _register_validate_alias(subparsers, parent):
    """Register validate command (deprecated alias for verify)."""
    p = subparsers.add_parser("validate", help="(Deprecated) Use 'ontos verify' instead", parents=[parent])
    p.add_argument("path", nargs="?", type=Path, help="Specific file to verify")
    p.add_argument("--all", "-a", action="store_true", help="Verify all stale documents")
    p.add_argument("--date", "-d", help="Verification date")
    p.set_defaults(func=_cmd_validate)


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
        scaffold=getattr(args, "scaffold", False),
        no_scaffold=getattr(args, "no_scaffold", False),
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
        sync_agents=getattr(args, 'sync_agents', False),
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


def _cmd_env(args) -> int:
    """Handle env command."""
    from ontos.commands.env import env_command, EnvOptions

    options = EnvOptions(
        path=Path.cwd(),
        write=getattr(args, "write", False),
        force=getattr(args, "force", False),  # v1.1: --force flag
        format=getattr(args, "format", "text"),
        quiet=args.quiet,
    )

    exit_code, output = env_command(options)

    if args.json or options.format == "json":
        # Already JSON formatted
        if output:
            print(output)
    elif not args.quiet and output:
        print(output)

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


def _cmd_agent_export(args) -> int:
    """Handle agent-export command (deprecated - delegates to agents)."""
    import sys
    print("Warning: 'ontos agent-export' is deprecated. Use 'ontos agents' instead.", file=sys.stderr)
    
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


def _cmd_export_data(args) -> int:
    """Handle export data command."""
    from ontos.commands.export_data import export_data_command, ExportDataOptions

    options = ExportDataOptions(
        output_path=args.output,
        types=args.type,
        status=args.status,
        concepts=args.concept,
        no_content=args.no_content,
        deterministic=args.deterministic,
        force=args.force,
        quiet=args.quiet,
        json_output=args.json,
    )

    exit_code, message = export_data_command(options)

    if exit_code == 0 and not args.output:
        # Output is JSON to stdout
        print(message)
    elif args.json:
        emit_json({
            "status": "success" if exit_code == 0 else "error",
            "message": message if args.output else "Exported to stdout",
            "exit_code": exit_code
        })
    elif not args.quiet:
        print(message)

    return exit_code


def _cmd_export_claude(args) -> int:
    """Handle export claude command."""
    from ontos.commands.export_claude import export_claude_command, ExportClaudeOptions

    options = ExportClaudeOptions(
        output_path=args.output,
        force=args.force,
        quiet=args.quiet,
        json_output=args.json,
    )

    exit_code, message = export_claude_command(options)

    if args.json:
        emit_json({
            "status": "success" if exit_code == 0 else "error",
            "message": message,
            "exit_code": exit_code
        })
    elif not args.quiet:
        print(message)

    return exit_code


def _cmd_export_deprecated(args) -> int:
    """Handle deprecated bare export command."""
    import sys
    print("Warning: 'ontos export' is deprecated. Use 'ontos export claude' or 'ontos export data'.", file=sys.stderr)
    print("This alias will be removed in v3.4.", file=sys.stderr)

    # Ensure args has required attributes for _cmd_export_claude
    if not hasattr(args, 'output'):
        setattr(args, 'output', None)
    if not hasattr(args, 'force'):
        setattr(args, 'force', False)

    # Delegate to export claude
    return _cmd_export_claude(args)


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




def _cmd_schema_migrate(args) -> int:
    """Handle schema-migrate command."""
    from ontos.commands.migrate import MigrateOptions, migrate_command

    options = MigrateOptions(
        check=args.check,
        dry_run=args.dry_run,
        apply=args.apply,
        dirs=args.dirs,
        quiet=args.quiet,
        json_output=args.json,
    )
    exit_code, message = migrate_command(options)
    return exit_code


def _cmd_migration_report(args) -> int:
    """Handle migration-report command."""
    from ontos.commands.migration_report import migration_report_command, MigrationReportOptions

    options = MigrationReportOptions(
        output_path=args.output,
        format=args.format,
        force=args.force,
        quiet=args.quiet,
        json_output=args.json,
    )

    exit_code, message = migration_report_command(options)

    if exit_code == 0 and not args.output:
        # Output is report to stdout
        print(message)
    elif args.json:
        emit_json({
            "status": "success" if exit_code == 0 else "error",
            "message": message if args.output else "Report output to stdout",
            "exit_code": exit_code
        })
    elif not args.quiet:
        print(message)

    return exit_code


def _cmd_migrate_convenience(args) -> int:
    """Handle migrate convenience command."""
    from ontos.commands.migrate_cmd import migrate_convenience_command, MigrateOptions

    options = MigrateOptions(
        out_dir=args.out_dir,
        force=args.force,
        quiet=args.quiet,
        json_output=args.json,
    )

    exit_code, message = migrate_convenience_command(options)

    if args.json:
        emit_json({
            "status": "success" if exit_code == 0 else "error",
            "message": message,
            "exit_code": exit_code
        })
    elif not args.quiet:
        print(message)

    return exit_code


def _cmd_consolidate(args) -> int:
    """Handle consolidate command."""
    from ontos.commands.consolidate import ConsolidateOptions, consolidate_command

    options = ConsolidateOptions(
        count=args.count,
        by_age=args.by_age,
        days=args.days,
        dry_run=args.dry_run,
        quiet=args.quiet,
        all=args.all,
        json_output=args.json,
    )
    exit_code, message = consolidate_command(options)
    return exit_code


def _cmd_stub(args) -> int:
    """Handle stub command."""
    from ontos.commands.stub import StubOptions, stub_command

    # Parse depends_on
    depends_on = None
    if args.depends_on:
        depends_on = [d.strip() for d in args.depends_on.split(',') if d.strip()]

    options = StubOptions(
        goal=args.goal,
        doc_type=args.doc_type,
        id=args.id,
        output=args.output,
        depends_on=depends_on,
        quiet=args.quiet,
        json_output=args.json,
    )
    exit_code, message = stub_command(options)
    return exit_code


def _cmd_promote(args) -> int:
    """Handle promote command."""
    from ontos.commands.promote import PromoteOptions, promote_command

    options = PromoteOptions(
        files=args.files,
        check=args.check,
        all_ready=args.all_ready,
        quiet=args.quiet,
        json_output=args.json,
    )
    exit_code, message = promote_command(options)
    return exit_code


def _cmd_query(args) -> int:
    """Handle query command."""
    from ontos.commands.query import QueryOptions, query_command

    options = QueryOptions(
        depends_on=args.depends_on,
        depended_by=args.depended_by,
        concept=args.concept,
        stale=args.stale,
        health=args.health,
        list_ids=args.list_ids,
        directory=args.dir,
        quiet=args.quiet,
        json_output=args.json,
    )
    exit_code, message = query_command(options)
    return exit_code


def _cmd_verify(args) -> int:
    """Handle verify command."""
    from ontos.commands.verify import VerifyOptions, verify_command

    options = VerifyOptions(
        path=args.path,
        all=args.all,
        date=args.date,
        quiet=args.quiet,
        json_output=args.json,
    )
    exit_code, message = verify_command(options)
    return exit_code


def _cmd_scaffold(args) -> int:
    """Handle scaffold command."""
    from ontos.commands.scaffold import ScaffoldOptions, scaffold_command

    options = ScaffoldOptions(
        paths=args.paths if args.paths else None,
        apply=args.apply,
        dry_run=not args.apply,  # Default to dry-run
        quiet=args.quiet,
        json_output=args.json,
    )
    exit_code, message = scaffold_command(options)
    return exit_code


def _cmd_tree(args) -> int:
    """Handle tree command (deprecated alias for map)."""
    import sys
    print("Warning: 'ontos tree' is deprecated. Use 'ontos map' instead.", file=sys.stderr)
    return _cmd_map(args)


def _cmd_validate(args) -> int:
    """Handle validate command (deprecated alias for verify)."""
    import sys
    print("Warning: 'ontos validate' is deprecated. Use 'ontos verify' instead.", file=sys.stderr)
    return _cmd_verify(args)


def _cmd_hook(args) -> int:
    """Handle hook command."""
    from ontos.commands.hook import hook_command, HookOptions

    options = HookOptions(
        hook_type=args.hook_type,
        args=getattr(args, "extra_args", []),
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
        "consolidate": "ontos_consolidate.py",
        "promote": "ontos_promote.py",
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
