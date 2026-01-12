"""Install Ontos git hooks into the current repository."""

import os
import sys
import shutil
import stat
import argparse


def find_project_root() -> str:
    """Find the project root by looking for .git directory.

    Returns:
        Path to project root.

    Raises:
        SystemExit: If not in a git repository.
    """
    current = os.path.dirname(os.path.abspath(__file__))

    # Walk up to find .git
    while current != os.path.dirname(current):
        if os.path.isdir(os.path.join(current, '.git')):
            return current
        current = os.path.dirname(current)

    print("Error: Not in a git repository")
    sys.exit(1)


def find_ontos_hooks_dir(project_root: str) -> str:
    """Find the .ontos/hooks directory.

    Args:
        project_root: Path to project root.

    Returns:
        Path to hooks directory.

    Raises:
        SystemExit: If hooks directory not found.
    """
    hooks_dir = os.path.join(project_root, '.ontos', 'hooks')
    if not os.path.isdir(hooks_dir):
        print(f"Error: Ontos hooks directory not found: {hooks_dir}")
        sys.exit(1)
    return hooks_dir


def install_hook(src_path: str, dest_path: str, quiet: bool = False, dry_run: bool = False) -> bool:
    """Install a single hook file.

    Args:
        src_path: Source hook file path.
        dest_path: Destination in .git/hooks/.
        quiet: Suppress output if True.
        dry_run: Preview without making changes.

    Returns:
        True if successful or would be successful.
    """
    hook_name = os.path.basename(src_path)

    if dry_run:
        if os.path.exists(dest_path):
            print(f"  Would update: {hook_name}")
        else:
            print(f"  Would install: {hook_name}")
        return True

    try:
        # Check if destination exists and is different
        if os.path.exists(dest_path):
            with open(src_path, 'r', encoding='utf-8') as f:
                src_content = f.read()
            with open(dest_path, 'r', encoding='utf-8') as f:
                dest_content = f.read()

            if src_content == dest_content:
                if not quiet:
                    print(f"  Already up to date: {hook_name}")
                return True

            # Backup existing hook
            backup_path = dest_path + '.backup'
            shutil.copy2(dest_path, backup_path)
            if not quiet:
                print(f"  Backed up existing hook to: {hook_name}.backup")

        # Copy the hook
        shutil.copy2(src_path, dest_path)

        # Make executable
        os.chmod(dest_path, os.stat(dest_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        if not quiet:
            print(f"  Installed: {hook_name}")
        return True

    except (IOError, OSError) as e:
        print(f"  Error installing {hook_name}: {e}")
        return False


def install_hooks(quiet: bool = False, dry_run: bool = False) -> int:
    """Install all Ontos hooks.

    Args:
        quiet: Suppress output if True.
        dry_run: Preview without making changes.

    Returns:
        Number of hooks installed.
    """
    project_root = find_project_root()
    hooks_src_dir = find_ontos_hooks_dir(project_root)
    hooks_dest_dir = os.path.join(project_root, '.git', 'hooks')

    # Ensure .git/hooks exists
    if not dry_run:
        os.makedirs(hooks_dest_dir, exist_ok=True)

    installed = 0

    # Find all hook files in .ontos/hooks/
    for hook_file in os.listdir(hooks_src_dir):
        src_path = os.path.join(hooks_src_dir, hook_file)

        # Skip non-files and hidden files
        if not os.path.isfile(src_path) or hook_file.startswith('.'):
            continue

        dest_path = os.path.join(hooks_dest_dir, hook_file)

        if install_hook(src_path, dest_path, quiet, dry_run):
            installed += 1

    return installed


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Install Ontos git hooks into the current repository.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script installs git hooks from .ontos/hooks/ to .git/hooks/.

Hooks installed:
  - pre-push: BLOCKS push until session is archived (enforces context capture)

Examples:
  python3 ontos_install_hooks.py           # Install hooks
  python3 ontos_install_hooks.py --dry-run # Preview what would be installed
"""
    )
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Preview what would be installed without making changes')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress non-error output')
    args = parser.parse_args()

    if not args.quiet:
        if args.dry_run:
            print("Dry run - no changes will be made:\n")
        else:
            print("Installing Ontos git hooks...\n")

    installed = install_hooks(args.quiet, args.dry_run)

    if not args.quiet:
        print()
        if args.dry_run:
            print(f"Would install {installed} hook(s).")
        else:
            print(f"Successfully installed {installed} hook(s).")
            print("\nThe pre-push hook will BLOCK push until you archive your session.")
            print("Run 'Archive Ontos' before pushing. Bypass with: git push --no-verify")


if __name__ == "__main__":
    main()
