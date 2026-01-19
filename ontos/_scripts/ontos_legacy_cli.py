#!/usr/bin/env python3
"""Ontos CLI - Unified command interface.

Usage:
    python3 ontos.py <command> [options]
    python3 ontos.py --help
    python3 ontos.py --version

Commands:
    log         Archive a session (creates log file)
    map         Generate context map
    verify      Verify describes dates
    maintain    Run maintenance tasks
    consolidate Archive old logs
    query       Search documents
    update      Update Ontos scripts
    migrate     Migrate schema versions

Examples:
    python3 ontos.py log -e feature         # Log a feature session
    python3 ontos.py map --strict           # Generate with strict validation
    python3 ontos.py verify --all           # Verify all stale docs
    python3 ontos.py migrate --check        # Check schema versions
"""

import sys
import os
from pathlib import Path

# v3.0: Get project root from env var set by cli.py
PROJECT_ROOT = os.environ.get("ONTOS_PROJECT_ROOT", os.getcwd())

# Must come first to ensure project config wins over bundled config
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Add bundled scripts directory for ontos_*.py imports
SCRIPTS_DIR = Path(__file__).parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(1, str(SCRIPTS_DIR))

COMMANDS = {
    'init': ('ontos_init', 'Initialize Ontos in a project'),
    'log': ('ontos_end_session', 'Archive a session'),
    'map': ('ontos_generate_context_map', 'Generate context map'),
    'verify': ('ontos_verify', 'Verify describes dates'),
    'maintain': ('ontos_maintain', 'Run maintenance'),
    'consolidate': ('ontos_consolidate', 'Archive old logs'),
    'query': ('ontos_query', 'Search documents'),
    'update': ('ontos_update', 'Update Ontos'),
    'migrate': ('ontos_migrate_schema', 'Migrate schema versions'),
    'scaffold': ('ontos_scaffold', 'Generate L0 scaffolds'),
    'stub': ('ontos_stub', 'Create L1 stub document'),
    'promote': ('ontos_promote', 'Promote L0/L1 to Level 2'),
}

ALIASES = {
    'archive': 'log',
    'session': 'log',
    'context': 'map',
    'generate': 'map',
    'check': 'verify',
    'maintenance': 'maintain',
    'archive-old': 'consolidate',
    'search': 'query',
    'find': 'query',
    'upgrade': 'update',
    'schema': 'migrate',
    'curate': 'scaffold',  # v2.9: curation alias
}


def print_help():
    """Print help message."""
    print(__doc__)
    print("Aliases:")
    for alias, cmd in sorted(ALIASES.items()):
        print(f"    {alias:15} → {cmd}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print_help()
        return 0

    if sys.argv[1] in ('-V', '--version'):
        from ontos_config import __version__
        print(f"Ontos {__version__}")
        return 0

    command = sys.argv[1]

    # Resolve aliases
    command = ALIASES.get(command, command)

    # Phase 3: Route init to legacy script (native init is handled in cli.py)
    # Note: When invoked via `python -m ontos`, cli.py handles init natively
    # This fallback is for direct script execution only
    if command == 'init':
        # Fall through to legacy ontos_init (this path is rarely used)
        pass

    if command not in COMMANDS:
        print(f"Error: Unknown command '{sys.argv[1]}'")
        print(f"Available commands: {', '.join(sorted(COMMANDS.keys()))}")
        print(f"Run 'python3 ontos.py --help' for usage information.")
        return 1

    module_name, _ = COMMANDS[command]

    # v2.9.2: Signal to scripts that they're being called via unified CLI
    # This suppresses deprecation warnings about direct script execution
    os.environ['ONTOS_CLI_DISPATCH'] = '1'

    # Import and run the module
    import importlib
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        print(f"Error: Could not load command '{command}': {e}")
        return 1

    # Replace sys.argv for the subcommand
    sys.argv = [module_name + '.py'] + sys.argv[2:]

    # Run the subcommand's main()
    try:
        return module.main() or 0
    except SystemExit as e:
        # Handle sys.exit() from subcommands
        return e.code if isinstance(e.code, int) else 0
    except Exception as e:
        print(f"Error running '{command}': {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
