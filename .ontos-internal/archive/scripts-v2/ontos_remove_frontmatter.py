"""Remove YAML frontmatter from Ontos documentation files."""

import os
import argparse
import sys

from ontos_config import __version__, DOCS_DIR


def has_frontmatter(filepath: str) -> bool:
    """Checks if a file has YAML frontmatter.

    Args:
        filepath: Path to the file to check.

    Returns:
        True if the file starts with '---', False otherwise.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return f.readline().strip() == '---'
    except (IOError, PermissionError, OSError):
        return False


def remove_frontmatter(filepath: str) -> tuple[bool, str]:
    """Removes YAML frontmatter from a markdown file.

    Args:
        filepath: Path to the file to process.

    Returns:
        Tuple of (success, message).
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        if not content.startswith('---'):
            return False, "No frontmatter found"

        # Find the closing '---'
        parts = content.split('---', 2)
        if len(parts) < 3:
            return False, "Malformed frontmatter (no closing ---)"

        # parts[0] is empty (before first ---), parts[1] is frontmatter, parts[2] is content
        new_content = parts[2].lstrip('\n')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True, "Frontmatter removed"

    except (IOError, PermissionError, OSError) as e:
        return False, f"Error: {e}"


def scan_for_tagged_files(root_dir: str) -> list[str]:
    """Finds all markdown files with frontmatter.

    Args:
        root_dir: Directory to scan.

    Returns:
        List of file paths with frontmatter.
    """
    tagged = []
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(subdir, file)
                if has_frontmatter(filepath):
                    tagged.append(filepath)
    return tagged


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Remove YAML frontmatter from Ontos documentation files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ontos_remove_frontmatter.py                 # Scan and remove from 'docs' directory
  python3 ontos_remove_frontmatter.py --dir specs     # Scan 'specs' directory
  python3 ontos_remove_frontmatter.py --dry-run       # Preview without making changes
  python3 ontos_remove_frontmatter.py --file doc.md   # Remove from a single file
"""
    )
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--dir', type=str, default=DOCS_DIR,
                        help='Directory to scan (default: docs)')
    parser.add_argument('--file', type=str,
                        help='Process a single file instead of scanning directory')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress non-error output')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying files')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    # Single file mode
    if args.file:
        if not os.path.isfile(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)

        if args.dry_run:
            if has_frontmatter(args.file):
                print(f"Would remove frontmatter from: {args.file}")
            else:
                print(f"No frontmatter found in: {args.file}")
            return

        success, message = remove_frontmatter(args.file)
        if success:
            print(f"Removed frontmatter from: {args.file}")
        else:
            print(f"{args.file}: {message}")
        return

    # Directory scan mode
    tagged_files = scan_for_tagged_files(args.dir)

    if not tagged_files:
        if not args.quiet:
            print("No files with frontmatter found.")
        return

    if not args.quiet:
        print(f"Found {len(tagged_files)} files with frontmatter:\n")
        for f in tagged_files:
            print(f"   - {f}")
        print()

    if args.dry_run:
        print(f"Dry run: Would remove frontmatter from {len(tagged_files)} files.")
        return

    # Confirmation prompt
    if not args.yes:
        response = input(f"Remove frontmatter from {len(tagged_files)} files? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            return

    # Process files
    success_count = 0
    fail_count = 0

    for filepath in tagged_files:
        success, message = remove_frontmatter(filepath)
        if success:
            success_count += 1
            if not args.quiet:
                print(f"Removed: {filepath}")
        else:
            fail_count += 1
            print(f"Failed: {filepath} - {message}")

    if not args.quiet:
        print(f"\nDone. Removed frontmatter from {success_count} files.")
        if fail_count > 0:
            print(f"Failed: {fail_count} files.")


if __name__ == "__main__":
    main()
