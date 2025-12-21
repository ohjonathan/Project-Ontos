"""Run Ontos maintenance tasks."""

import subprocess
import sys
import os
import re
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ontos_config import __version__, PROJECT_ROOT
from ontos_lib import find_draft_proposals, get_proposals_dir, get_decision_history_path

# v2.8.4: Import from ontos_end_session to avoid duplication
# These functions were refactored with v2.8 transactional pattern in PR #27
from ontos_end_session import graduate_proposal
from ontos.ui.output import OutputHandler

SCRIPTS_DIR = os.path.join(PROJECT_ROOT, '.ontos', 'scripts')


def review_proposals(quiet: bool = False, output: OutputHandler = None) -> bool:
    """Review draft proposals and prompt for graduation.

    v2.6.1: Step 4 of Maintain Ontos.
    v2.8.4: Added OutputHandler support.

    Args:
        quiet: Suppress output.
        output: OutputHandler instance (creates default if None).

    Returns:
        True if any proposals were graduated.
    """
    if output is None:
        output = OutputHandler(quiet=quiet)
    
    drafts = find_draft_proposals()

    if not drafts:
        output.success("No draft proposals to review.")
        return False

    # Skip interactive prompts in non-TTY mode (e.g., pytest, CI)
    interactive = sys.stdin.isatty() if hasattr(sys.stdin, 'isatty') else False

    output.info(f"Found {len(drafts)} draft proposal(s):")

    graduated_any = False

    for prop in drafts:
        version_note = ""
        if prop.get('version_match'):
            version_note = f" ⚠️  ONTOS_VERSION matches {prop['version']}"
        elif prop.get('version'):
            version_note = f" (v{prop['version']})"

        output.detail(f"{prop['id']}{version_note}")
        output.detail(f"{prop['age_days']} days old")

        if interactive:
            try:
                response = input("     Graduate to strategy/? [y/N/skip all]: ").strip().lower()
                if response == 'skip all':
                    output.info("Skipping remaining proposals.")
                    break
                if response in ('y', 'yes'):
                    if graduate_proposal(prop, quiet, output=output):
                        graduated_any = True
            except (EOFError, KeyboardInterrupt):
                output.info("Skipping remaining proposals.")
                break
        else:
            output.detail("(Run interactively to graduate)")

    return graduated_any


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
3. ontos_consolidate.py - Consolidate logs exceeding retention count
4. Review proposals - Prompt to graduate implemented proposals

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
    
    # v2.8.4: Create OutputHandler for all output
    output = OutputHandler(quiet=args.quiet)
    
    output.info("Running Ontos maintenance...")
    
    all_success = True
    
    # Step 1: Check for untagged files
    output.info("Step 1: Checking for untagged files...")
    
    migrate_args = []
    if args.strict:
        migrate_args.append('--strict')
    
    success, script_output = run_script('ontos_migrate_frontmatter.py', migrate_args, args.quiet)
    if script_output.strip():
        output.plain(script_output)
    all_success = all_success and success
    
    # Step 2: Rebuild context map
    output.info("Step 2: Rebuilding context map...")
    
    generate_args = []
    if args.strict:
        generate_args.append('--strict')
    if args.lint:
        generate_args.append('--lint')
    
    success, script_output = run_script('ontos_generate_context_map.py', generate_args, args.quiet)
    if script_output.strip():
        output.plain(script_output)
    all_success = all_success and success
    
    # Step 3: Consolidate logs (v2.4+, count-based since v2.6.2)
    try:
        from ontos_lib import resolve_config
        auto_consolidate = resolve_config('AUTO_CONSOLIDATE', True)
    except ImportError:
        auto_consolidate = True

    if auto_consolidate:
        output.info("Step 3: Consolidating excess logs...")

        # Get retention count from config (mode/user-aware)
        retention_count = resolve_config('LOG_RETENTION_COUNT', 15)

        consolidate_args = ['--all', '--count', str(retention_count)]
        success, script_output = run_script('ontos_consolidate.py', consolidate_args, args.quiet)
        if script_output.strip():
            output.plain(script_output)
        # Consolidation failures are non-critical
        if not success:
            output.warning("Consolidation had issues (non-critical)")
    else:
        output.info("Step 3: Consolidation (skipped, AUTO_CONSOLIDATE is False)")
        output.detail("Run `python3 .ontos/scripts/ontos_consolidate.py` manually if needed.")

    # Step 4: Review proposals (v2.6.1)
    output.info("Step 4: Reviewing proposals...")

    graduated = review_proposals(args.quiet, output=output)
    if graduated:
        # Regenerate context map if proposals were graduated
        output.info("Regenerating context map after graduation...")
        run_script('ontos_generate_context_map.py', [], args.quiet)

    # Summary
    if all_success:
        output.success("Maintenance complete. No issues found.")
    else:
        output.warning("Maintenance complete with issues. Review output above.")
    
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
