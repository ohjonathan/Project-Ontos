"""Update Ontos to the latest version from GitHub."""

import os
import sys
import shutil
import tempfile
import subprocess
import argparse
import re
from typing import Optional

from ontos_config import __version__
from ontos_config_defaults import ONTOS_VERSION, ONTOS_REPO_URL

# Files that should be updated (relative to .ontos/scripts/)
UPDATABLE_SCRIPTS = [
    'ontos_config_defaults.py',
    'ontos_generate_context_map.py',
    'ontos_migrate_frontmatter.py',
    'ontos_end_session.py',
    'ontos_remove_frontmatter.py',
    'ontos_update.py',  # Self-update
    'ontos_install_hooks.py',
    'ontos_migrate_v2.py',
]

# Files that should be updated in the project root
UPDATABLE_ROOT_FILES = [
    'ontos_init.py',
]

# Hooks to update (relative to .ontos/hooks/)
UPDATABLE_HOOKS = [
    'pre-push',
]

# Files that should NEVER be overwritten (user customizations)
PROTECTED_FILES = [
    'ontos_config.py',
]

# Documentation files to update (relative to project root)
# Can be string (src=dest) or tuple (src, dest)
UPDATABLE_DOCS = [
    'docs/reference/Ontos_Manual.md',
    'docs/reference/Ontos_Agent_Instructions.md',
    ('.ontos-internal/reference/Common_Concepts.md', 'docs/reference/Common_Concepts.md'),
]


def get_local_version() -> str:
    """Get the current local Ontos version.

    Returns:
        Version string (e.g., '1.0.0').
    """
    return ONTOS_VERSION


def parse_version(version_str: str) -> tuple[int, int, int]:
    """Parse a version string into a tuple.

    Args:
        version_str: Version string like '1.0.0'.

    Returns:
        Tuple of (major, minor, patch).
    """
    match = re.match(r'(\d+)\.(\d+)\.(\d+)', version_str)
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return (0, 0, 0)


def clone_latest(temp_dir: str, quiet: bool = False) -> bool:
    """Clone the latest Ontos from GitHub.

    Args:
        temp_dir: Directory to clone into.
        quiet: Suppress output if True.

    Returns:
        True if successful.
    """
    try:
        cmd = ['git', 'clone', '--depth', '1', ONTOS_REPO_URL, temp_dir]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            print(f"Error cloning repository: {result.stderr}")
            return False
        if not quiet:
            print(f"Cloned latest Ontos from {ONTOS_REPO_URL}")
        return True
    except subprocess.TimeoutExpired:
        print("Error: Git clone timed out")
        return False
    except FileNotFoundError:
        print("Error: Git is not installed or not in PATH")
        return False
    except Exception as e:
        print(f"Error cloning repository: {e}")
        return False


def get_remote_version(temp_dir: str) -> Optional[str]:
    """Get the version from the cloned repository.

    Args:
        temp_dir: Directory containing cloned repo.

    Returns:
        Version string or None if not found.
    """
    defaults_path = os.path.join(temp_dir, '.ontos', 'scripts', 'ontos_config_defaults.py')

    if not os.path.exists(defaults_path):
        # Fall back to old config location
        defaults_path = os.path.join(temp_dir, '.ontos', 'scripts', 'ontos_config.py')

    if not os.path.exists(defaults_path):
        return None

    try:
        with open(defaults_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for ONTOS_VERSION or __version__
        match = re.search(r"(?:ONTOS_VERSION|__version__)\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            return match.group(1)
    except (IOError, OSError):
        pass

    return None


def backup_file(filepath: str, backup_dir: str) -> Optional[str]:
    """Create a backup of a file.

    Args:
        filepath: Path to file to backup.
        backup_dir: Directory to store backup.

    Returns:
        Path to backup file or None if failed.
    """
    if not os.path.exists(filepath):
        return None

    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, os.path.basename(filepath) + '.bak')

    try:
        shutil.copy2(filepath, backup_path)
        return backup_path
    except (IOError, OSError) as e:
        print(f"Warning: Could not backup {filepath}: {e}")
        return None


def update_file(src: str, dest: str, quiet: bool = False) -> bool:
    """Copy a file from source to destination.

    Args:
        src: Source file path.
        dest: Destination file path.
        quiet: Suppress output if True.

    Returns:
        True if successful.
    """
    try:
        # Ensure destination directory exists
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
        if not quiet:
            print(f"  Updated: {dest}")
        return True
    except (IOError, OSError) as e:
        print(f"  Error updating {dest}: {e}")
        return False


def update_scripts(temp_dir: str, backup_dir: str, quiet: bool = False, dry_run: bool = False) -> int:
    """Update Ontos scripts from the cloned repository.

    Args:
        temp_dir: Directory containing cloned repo.
        backup_dir: Directory for backups.
        quiet: Suppress output if True.
        dry_run: Preview changes without applying.

    Returns:
        Number of files updated.
    """
    updated = 0
    scripts_src = os.path.join(temp_dir, '.ontos', 'scripts')
    scripts_dest = '.ontos/scripts'

    for script in UPDATABLE_SCRIPTS:
        src_path = os.path.join(scripts_src, script)
        dest_path = os.path.join(scripts_dest, script)

        if not os.path.exists(src_path):
            if not quiet:
                print(f"  Skipped (not in source): {script}")
            continue

        if dry_run:
            if os.path.exists(dest_path):
                print(f"  Would update: {dest_path}")
            else:
                print(f"  Would create: {dest_path}")
            updated += 1
            continue

        # Backup existing file
        if os.path.exists(dest_path):
            backup_file(dest_path, backup_dir)

        if update_file(src_path, dest_path, quiet):
            updated += 1

    return updated


def update_docs(temp_dir: str, backup_dir: str, quiet: bool = False, dry_run: bool = False) -> int:
    """Update Ontos documentation from the cloned repository.

    Args:
        temp_dir: Directory containing cloned repo.
        backup_dir: Directory for backups.
        quiet: Suppress output if True.
        dry_run: Preview changes without applying.

    Returns:
        Number of files updated.
    """
    updated = 0

    for doc in UPDATABLE_DOCS:
        if isinstance(doc, tuple):
            src_rel, dest_rel = doc
        else:
            src_rel = dest_rel = doc
            
        src_path = os.path.join(temp_dir, src_rel)
        dest_path = dest_rel

        if not os.path.exists(src_path):
            if not quiet:
                print(f"  Skipped (not in source): {doc}")
            continue

        if dry_run:
            if os.path.exists(dest_path):
                print(f"  Would update: {dest_path}")
            else:
                print(f"  Would create: {dest_path}")
            updated += 1
            continue

        # Backup existing file
        if os.path.exists(dest_path):
            backup_file(dest_path, backup_dir)

        if update_file(src_path, dest_path, quiet):
            updated += 1

    return updated


def update_hooks(temp_dir: str, backup_dir: str, quiet: bool = False, dry_run: bool = False) -> int:
    """Update Ontos hooks from the cloned repository.

    Args:
        temp_dir: Directory containing cloned repo.
        backup_dir: Directory for backups.
        quiet: Suppress output if True.
        dry_run: Preview changes without applying.

    Returns:
        Number of hooks updated.
    """
    import stat

    updated = 0
    hooks_src = os.path.join(temp_dir, '.ontos', 'hooks')
    hooks_dist = '.ontos/hooks'
    hooks_installed = '.git/hooks'

    for hook in UPDATABLE_HOOKS:
        src_path = os.path.join(hooks_src, hook)
        dist_path = os.path.join(hooks_dist, hook)
        installed_path = os.path.join(hooks_installed, hook)

        if not os.path.exists(src_path):
            if not quiet:
                print(f"  Skipped (not in source): {hook}")
            continue

        if dry_run:
            print(f"  Would update: {dist_path}")
            if os.path.exists('.git'):
                print(f"  Would update: {installed_path}")
            updated += 1
            continue

        # Backup and update distribution copy
        if os.path.exists(dist_path):
            backup_file(dist_path, backup_dir)

        if update_file(src_path, dist_path, quiet):
            # Make executable
            os.chmod(dist_path, os.stat(dist_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            updated += 1

        # Also update installed hook if .git exists
        if os.path.exists('.git'):
            os.makedirs(hooks_installed, exist_ok=True)
            if os.path.exists(installed_path):
                backup_file(installed_path, backup_dir)
            if update_file(src_path, installed_path, quiet):
                os.chmod(installed_path, os.stat(installed_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return updated


def update_root_files(temp_dir: str, backup_dir: str, quiet: bool = False, dry_run: bool = False) -> int:
    """Update root-level files from the cloned repository.

    Args:
        temp_dir: Directory containing cloned repo.
        backup_dir: Directory for backups.
        quiet: Suppress output if True.
        dry_run: Preview changes without applying.

    Returns:
        Number of files updated.
    """
    updated = 0
    
    for filename in UPDATABLE_ROOT_FILES:
        src_path = os.path.join(temp_dir, filename)
        dest_path = filename

        if not os.path.exists(src_path):
            if not quiet:
                print(f"  Skipped (not in source): {filename}")
            continue

        if dry_run:
            if os.path.exists(dest_path):
                print(f"  Would update: {dest_path}")
            else:
                print(f"  Would create: {dest_path}")
            updated += 1
            continue

        # Backup existing file
        if os.path.exists(dest_path):
            backup_file(dest_path, backup_dir)

        if update_file(src_path, dest_path, quiet):
            updated += 1

    return updated


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Update Ontos to the latest version from GitHub.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Current version: {ONTOS_VERSION}
Repository: {ONTOS_REPO_URL}

Examples:
  python3 ontos_update.py                # Check for updates and apply
  python3 ontos_update.py --check        # Only check, don't update
  python3 ontos_update.py --dry-run      # Preview what would be updated
  python3 ontos_update.py --force        # Update even if versions match
  python3 ontos_update.py --scripts-only # Only update scripts, not docs

Protected files (never overwritten):
  - ontos_config.py (your customizations)

Backups are created in .ontos/backups/ before updating.
"""
    )
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--check', '-c', action='store_true',
                        help='Only check for updates, do not apply')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Preview what would be updated without making changes')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force update even if versions match')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress non-error output')
    parser.add_argument('--scripts-only', action='store_true',
                        help='Only update scripts, not documentation')
    parser.add_argument('--docs-only', action='store_true',
                        help='Only update documentation, not scripts')
    args = parser.parse_args()

    local_version = get_local_version()
    if not args.quiet:
        print(f"Current Ontos version: {local_version}")
        print(f"Checking for updates from {ONTOS_REPO_URL}...")
        print()

    # Create temp directory for cloning
    temp_dir = tempfile.mkdtemp(prefix='ontos_update_')
    backup_dir = '.ontos/backups'

    try:
        # Clone latest
        if not clone_latest(temp_dir, args.quiet):
            sys.exit(1)

        # Get remote version
        remote_version = get_remote_version(temp_dir)
        if not remote_version:
            print("Error: Could not determine remote version")
            sys.exit(1)

        if not args.quiet:
            print(f"Latest version available: {remote_version}")
            print()

        # Compare versions
        local_tuple = parse_version(local_version)
        remote_tuple = parse_version(remote_version)

        if remote_tuple <= local_tuple and not args.force:
            if not args.quiet:
                print("You are already running the latest version!")
            if args.check:
                sys.exit(0)
            if not args.force:
                print("Use --force to update anyway.")
                sys.exit(0)

        if args.check:
            print(f"Update available: {local_version} -> {remote_version}")
            print("Run without --check to apply the update.")
            sys.exit(0)

        # Perform update
        if not args.quiet:
            if args.dry_run:
                print("Dry run - no changes will be made:\n")
            else:
                print("Updating Ontos...\n")

        total_updated = 0

        # Update scripts
        if not args.docs_only:
            if not args.quiet:
                print("Scripts:")
            total_updated += update_scripts(temp_dir, backup_dir, args.quiet, args.dry_run)

        # Update docs
        if not args.scripts_only:
            if not quiet:
                print("\nDocumentation:")
            total_updated += update_docs(temp_dir, backup_dir, args.quiet, args.dry_run)

        # Update root files
        if not args.docs_only:
            if not args.quiet:
                print("\nRoot Files:")
            total_updated += update_root_files(temp_dir, backup_dir, args.quiet, args.dry_run)

        # Update hooks
        if not args.docs_only:
            if not args.quiet:
                print("\nHooks:")
            total_updated += update_hooks(temp_dir, backup_dir, args.quiet, args.dry_run)

        if not args.quiet:
            print()
            if args.dry_run:
                print(f"Would update {total_updated} files.")
                print("\nRun without --dry-run to apply changes.")
            else:
                print(f"Successfully updated {total_updated} files.")
                print(f"Updated from {local_version} to {remote_version}")
                print(f"\nBackups saved to: {backup_dir}/")
                print("\nNote: Your ontos_config.py customizations were preserved.")

    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
        except (IOError, OSError):
            pass


def emit_deprecation_notice(message: str) -> None:
    """Always-visible CLI notice for deprecated usage."""
    print(f"[DEPRECATION] {message}", file=sys.stderr)


if __name__ == "__main__":
    if not os.environ.get('ONTOS_CLI_DISPATCH'):
        if not os.environ.get('ONTOS_NO_DEPRECATION_WARNINGS'):
            from pathlib import Path
            emit_deprecation_notice(
                f"Direct execution of {Path(__file__).name} is deprecated. "
                "Use 'python3 ontos.py update' instead. "
                "Direct script execution will be removed in v3.0."
            )
    main()
