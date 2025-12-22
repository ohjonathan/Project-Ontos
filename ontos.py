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
from pathlib import Path

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent / '.ontos' / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

COMMANDS = {
    'log': ('ontos_end_session', 'Archive a session'),
    'map': ('ontos_generate_context_map', 'Generate context map'),
    'verify': ('ontos_verify', 'Verify describes dates'),
    'maintain': ('ontos_maintain', 'Run maintenance'),
    'consolidate': ('ontos_consolidate', 'Archive old logs'),
    'query': ('ontos_query', 'Search documents'),
    'update': ('ontos_update', 'Update Ontos'),
    'migrate': ('ontos_migrate_schema', 'Migrate schema versions'),
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

    if command not in COMMANDS:
        print(f"Error: Unknown command '{sys.argv[1]}'")
        print(f"Available commands: {', '.join(sorted(COMMANDS.keys()))}")
        print(f"Run 'python3 ontos.py --help' for usage information.")
        return 1

    module_name, _ = COMMANDS[command]

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
