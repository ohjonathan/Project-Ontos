"""Run Ontos maintenance tasks."""

import subprocess
import sys
import os
import re
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ontos_config import __version__, PROJECT_ROOT
from ontos_lib import find_draft_proposals, get_proposals_dir, get_decision_history_path

SCRIPTS_DIR = os.path.join(PROJECT_ROOT, '.ontos', 'scripts')


def graduate_proposal(proposal: dict, quiet: bool = False) -> bool:
    """Graduate a proposal from proposals/ to strategy/.

    v2.6.1: Moved here for Maintain Ontos integration.

    Args:
        proposal: Dict with 'id', 'filepath', 'version'
        quiet: Suppress output

    Returns:
        True if graduation succeeded.
    """
    import shutil
    import datetime

    filepath = proposal['filepath']
    proposals_dir = get_proposals_dir()

    # Determine destination
    rel_path = os.path.relpath(filepath, proposals_dir)
    strategy_dir = os.path.dirname(proposals_dir)  # Parent of proposals
    dest_path = os.path.join(strategy_dir, rel_path)
    dest_dir = os.path.dirname(dest_path)

    try:
        os.makedirs(dest_dir, exist_ok=True)

        # Read and update frontmatter
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update status: draft -> active
        content = re.sub(
            r'^(status:\s*)draft\s*$',
            r'\1active',
            content,
            flags=re.MULTILINE
        )

        # Write to new location
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Remove original
        os.remove(filepath)

        # Try to remove empty parent directories
        try:
            parent = os.path.dirname(filepath)
            if os.path.isdir(parent) and not os.listdir(parent):
                os.rmdir(parent)
        except OSError:
            pass

        # Add entry to decision_history.md
        add_graduation_to_ledger(proposal, dest_path)

        if not quiet:
            print(f"   ✅ Graduated: {proposal['id']}")
            print(f"      proposals/{rel_path} → strategy/{rel_path}")

        return True

    except (IOError, OSError, shutil.Error) as e:
        if not quiet:
            print(f"   ❌ Graduation failed: {e}")
        return False


def add_graduation_to_ledger(proposal: dict, new_path: str) -> None:
    """Add APPROVED entry to decision_history.md."""
    import datetime

    history_path = get_decision_history_path()
    if not history_path or not os.path.exists(history_path):
        return

    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            content = f.read()

        today = datetime.datetime.now().strftime('%Y-%m-%d')
        slug = proposal['id'].replace('_', '-')
        version = proposal.get('version', '')

        new_entry = (
            f"| {today} | {slug} | feature | "
            f"APPROVED: {version or 'Proposal'} implemented. | "
            f"v2_strategy, schema | `{new_path}` |\n"
        )

        # Insert after the header row
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('|:--') or line.startswith('| Date'):
                continue
            if line.startswith('|') and '|' in line[1:]:
                lines.insert(i, new_entry.strip())
                break

        with open(history_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    except (IOError, OSError):
        pass


def review_proposals(quiet: bool = False) -> bool:
    """Review draft proposals and prompt for graduation.

    v2.6.1: Step 4 of Maintain Ontos.

    Returns:
        True if any proposals were graduated.
    """
    drafts = find_draft_proposals()

    if not drafts:
        if not quiet:
            print("✅ No draft proposals to review.")
        return False

    # Skip interactive prompts in non-TTY mode (e.g., pytest, CI)
    interactive = sys.stdin.isatty() if hasattr(sys.stdin, 'isatty') else False

    if not quiet:
        print(f"📋 Found {len(drafts)} draft proposal(s):\n")

    graduated_any = False

    for prop in drafts:
        version_note = ""
        if prop.get('version_match'):
            version_note = f" ⚠️  ONTOS_VERSION matches {prop['version']}"
        elif prop.get('version'):
            version_note = f" (v{prop['version']})"

        if not quiet:
            print(f"   - {prop['id']}{version_note}")
            print(f"     {prop['age_days']} days old")

            if interactive:
                try:
                    response = input("     Graduate to strategy/? [y/N/skip all]: ").strip().lower()
                    if response == 'skip all':
                        print("   Skipping remaining proposals.")
                        break
                    if response in ('y', 'yes'):
                        if graduate_proposal(prop, quiet):
                            graduated_any = True
                except (EOFError, KeyboardInterrupt):
                    print("\n   Skipping remaining proposals.")
                    break
            else:
                print("     (Run interactively to graduate)")

            print()

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
    
    # Step 3: Consolidate logs (v2.4, mode-aware)
    try:
        from ontos_lib import resolve_config
        auto_consolidate = resolve_config('AUTO_CONSOLIDATE', True)
    except ImportError:
        auto_consolidate = True
    
    if auto_consolidate:
        if not args.quiet:
            print("\nStep 3: Consolidating stale logs...")
        
        # Get consolidation threshold days from config (mode/user-aware)
        threshold_days = resolve_config('CONSOLIDATION_THRESHOLD_DAYS', 30)
        
        consolidate_args = ['--all', '--days', str(threshold_days)]
        success, output = run_script('ontos_consolidate.py', consolidate_args, args.quiet)
        if not args.quiet and output.strip():
            print(output)
        # Consolidation failures are non-critical
        if not success and not args.quiet:
            print("   ⚠️  Consolidation had issues (non-critical)")
    else:
        if not args.quiet:
            print("\nStep 3: Consolidation (skipped, AUTO_CONSOLIDATE is False)")
            print("   Run `python3 .ontos/scripts/ontos_consolidate.py` manually if needed.")

    # Step 4: Review proposals (v2.6.1)
    if not args.quiet:
        print("\nStep 4: Reviewing proposals...")

    graduated = review_proposals(args.quiet)
    if graduated:
        # Regenerate context map if proposals were graduated
        if not args.quiet:
            print("\n   Regenerating context map after graduation...")
        run_script('ontos_generate_context_map.py', [], args.quiet)

    # Summary
    if not args.quiet:
        if all_success:
            print("\n✅ Maintenance complete. No issues found.")
        else:
            print("\n⚠️  Maintenance complete with issues. Review output above.")
    
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
