"""Run Ontos maintenance tasks."""

import subprocess
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ontos_config import __version__, PROJECT_ROOT

SCRIPTS_DIR = os.path.join(PROJECT_ROOT, '.ontos', 'scripts')


def run_script(name: str, args: list = None, quiet: bool = False) -> tuple:
    """Run an Ontos script.
    
    Returns:
        Tuple of (success, output)
    """
    script_path = os.path.join(SCRIPTS_DIR, name)
    cmd = [sys.executable, script_path] + (args or [])
    
    if quiet:
        cmd.append('--quiet')
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr


def main():
    parser = argparse.ArgumentParser(
        description='Run Ontos maintenance tasks.',
        epilog="""
This command runs:
1. ontos_migrate_frontmatter.py - Find untagged files
2. ontos_generate_context_map.py - Rebuild graph and validate

Example:
  python3 ontos_maintain.py          # Run maintenance
  python3 ontos_maintain.py --strict # Fail on any issues
  python3 ontos_maintain.py --lint   # Include data quality checks
"""
    )
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--strict', action='store_true', help='Exit with error if issues found')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress output')
    parser.add_argument('--lint', action='store_true', help='Include data quality checks')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🔧 Running Ontos maintenance...\n")
    
    all_success = True
    
    # Step 1: Check for untagged files
    if not args.quiet:
        print("Step 1: Checking for untagged files...")
    
    migrate_args = []
    if args.strict:
        migrate_args.append('--strict')
    
    success, output = run_script('ontos_migrate_frontmatter.py', migrate_args, args.quiet)
    if not args.quiet and output.strip():
        print(output)
    all_success = all_success and success
    
    # Step 2: Rebuild context map
    if not args.quiet:
        print("\nStep 2: Rebuilding context map...")
    
    generate_args = []
    if args.strict:
        generate_args.append('--strict')
    if args.lint:
        generate_args.append('--lint')
    
    success, output = run_script('ontos_generate_context_map.py', generate_args, args.quiet)
    if not args.quiet and output.strip():
        print(output)
    all_success = all_success and success
    
    # Summary
    if not args.quiet:
        if all_success:
            print("\n✅ Maintenance complete. No issues found.")
        else:
            print("\n⚠️  Maintenance complete with issues. Review output above.")
    
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
