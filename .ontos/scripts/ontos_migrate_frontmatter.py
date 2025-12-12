"""Scan for untagged Ontos documentation files."""

import os
import argparse
import sys

from ontos_config import __version__, DOCS_DIR, MIGRATION_PROMPT_FILE, TYPE_DEFINITIONS, SKIP_PATTERNS

PROMPT_FILE = MIGRATION_PROMPT_FILE


def has_frontmatter(filepath: str) -> bool:
    """Checks if a file already has YAML frontmatter.

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


def scan_for_untagged_files(root_dir: str) -> list[str]:
    """Finds all markdown files without frontmatter.

    Args:
        root_dir: Directory to scan.

    Returns:
        List of file paths without frontmatter.
    """
    untagged = []
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md'):
                # Skip files matching skip patterns (e.g., Ontos_ tooling files)
                if any(pattern in file for pattern in SKIP_PATTERNS):
                    continue
                filepath = os.path.join(subdir, file)
                if not has_frontmatter(filepath):
                    untagged.append(filepath)
    return untagged


def generate_taxonomy_table() -> str:
    """Generate the type taxonomy table from TYPE_DEFINITIONS.

    Returns:
        Formatted markdown table string.
    """
    lines = ["| Type | Rank | Description |", "|------|------|-------------|"]

    # Sort by rank to maintain hierarchy order, exclude 'unknown' and 'log'
    # (log is Time ontology, not relevant for document classification)
    sorted_types = sorted(
        [(k, v) for k, v in TYPE_DEFINITIONS.items()
         if k not in ('unknown', 'log') and v.get('rank') is not None],
        key=lambda x: x[1]['rank']
    )

    for type_name, type_info in sorted_types:
        description = type_info.get('description', '')
        rank = type_info.get('rank', '?')
        lines.append(f"| {type_name} | {rank} | {description} |")

    return '\n'.join(lines)


def generate_prompt(files: list[str]) -> str:
    """Generates a prompt for the agent to process.

    Args:
        files: List of file paths to include in the prompt.

    Returns:
        Formatted prompt string.
    """
    taxonomy_table = generate_taxonomy_table()

    prompt = f"""# Ontos Migration Task

You are tagging documentation files with YAML frontmatter.

## Type Taxonomy

{taxonomy_table}

## Classification Heuristic

When uncertain: "If this document changes, what else breaks?"
- Everything breaks → kernel
- Business direction changes → strategy
- User experience changes → product
- Only implementation changes → atom

## Your Task

For each file below:
1. Read the file content
2. Determine the appropriate type, id, and dependencies
3. Add YAML frontmatter to the beginning of the file
4. After all files are tagged, run `python3 .ontos/scripts/ontos_generate_context_map.py` to validate

## Files to Tag:

"""
    for filepath in files:
        prompt += f"- {filepath}\n"

    return prompt


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scan for untagged Ontos documentation files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ontos_migrate_frontmatter.py                 # Scan default 'docs' directory
  python3 ontos_migrate_frontmatter.py --dir specs     # Scan 'specs' directory
  python3 ontos_migrate_frontmatter.py --dry-run       # Show what would be done
  python3 ontos_migrate_frontmatter.py --strict        # Exit with error if untagged files found
"""
    )
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--dir', type=str, default=DOCS_DIR,
                        help='Directory to scan (default: docs)')
    parser.add_argument('--strict', action='store_true', help='Exit with error if untagged files found')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress non-error output')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without writing files')
    args = parser.parse_args()

    untagged = scan_for_untagged_files(args.dir)

    if not untagged:
        if not args.quiet:
            print("✅ All files are tagged. No migration needed.")
        return

    if args.strict:
        print(f"❌ Strict mode: Found {len(untagged)} untagged files.")
        for f in untagged:
            print(f"   - {f}")
        sys.exit(1)

    if not args.quiet:
        print(f"📋 Found {len(untagged)} untagged files:\n")
        for f in untagged:
            print(f"   - {f}")

    if args.dry_run:
        print(f"\n🔍 Dry run: Would generate prompt for {len(untagged)} files")
        print(f"   Output would be written to: {PROMPT_FILE}")
        return

    prompt = generate_prompt(untagged)

    with open(PROMPT_FILE, 'w', encoding='utf-8') as f:
        f.write(prompt)

    if not args.quiet:
        print(f"\n📄 Migration prompt saved to '{PROMPT_FILE}'")
        print("\n💡 Next steps:")
        print("   1. Read each file listed above")
        print("   2. Add appropriate YAML frontmatter")
        print("   3. Run: python3 .ontos/scripts/ontos_generate_context_map.py")


if __name__ == "__main__":
    main()
