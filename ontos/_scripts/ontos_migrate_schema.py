#!/usr/bin/env python3
"""Migrate documents to use explicit ontos_schema field.

This script adds the ontos_schema field to Ontos documents that don't have it.
For legacy documents, it infers the schema version from existing fields.

Usage:
    python3 ontos_migrate_schema.py --check        # Check which files need migration
    python3 ontos_migrate_schema.py --dry-run      # Preview changes
    python3 ontos_migrate_schema.py --apply        # Apply changes

Examples:
    # Check all documents
    python3 ontos_migrate_schema.py --check
    
    # Preview what would change
    python3 ontos_migrate_schema.py --dry-run
    
    # Apply migrations with specific directory
    python3 ontos_migrate_schema.py --apply --dirs docs .ontos-internal
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

# Fix sys.path to avoid ontos.py shadowing the ontos package.
# Python auto-inserts script dir at sys.path[0]; remove it before importing ontos.
SCRIPTS_DIR = Path(__file__).parent.resolve()
if sys.path and Path(sys.path[0]).resolve() == SCRIPTS_DIR:
    sys.path.pop(0)

# Import ontos package BEFORE adding scripts dir back to path
from ontos.core.schema import (
    detect_schema_version,
    serialize_frontmatter,
    add_schema_to_frontmatter,
    CURRENT_SCHEMA_VERSION,
)
from ontos.core.context import SessionContext
from ontos.ui.output import OutputHandler
from ontos.core.frontmatter import parse_frontmatter

# Now add scripts dir for ontos_config_defaults imports (used later)
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))


def find_markdown_files(directories: List[str], skip_patterns: List[str] = None) -> List[Path]:
    """Find all markdown files in directories.
    
    Args:
        directories: List of directory paths to search.
        skip_patterns: Patterns to skip (e.g., 'archive', 'node_modules').
        
    Returns:
        List of Path objects for markdown files.
    """
    if skip_patterns is None:
        skip_patterns = ['archive', 'node_modules', '.git', '__pycache__']
    
    files = []
    for dir_path in directories:
        path = Path(dir_path)
        if not path.exists():
            continue
        
        for md_file in path.rglob('*.md'):
            # Skip based on patterns
            skip = False
            for pattern in skip_patterns:
                if pattern in str(md_file):
                    skip = True
                    break
            
            if not skip:
                files.append(md_file)
    
    return sorted(files)


def check_file_needs_migration(filepath: Path) -> Tuple[bool, str, str]:
    """Check if a file needs schema migration.
    
    Args:
        filepath: Path to markdown file.
        
    Returns:
        Tuple of (needs_migration, current_schema, message).
    """
    fm = parse_frontmatter(str(filepath))
    
    if fm is None:
        return False, "", "No frontmatter"
    
    if 'id' not in fm:
        return False, "", "No id field (not an Ontos document)"
    
    if 'ontos_schema' in fm:
        schema = fm['ontos_schema']
        return False, schema, f"Already has ontos_schema: {schema}"
    
    # Infer schema version
    inferred = detect_schema_version(fm)
    return True, inferred, f"Would add ontos_schema: {inferred}"


def migrate_file(filepath: Path, dry_run: bool = True, output: OutputHandler = None) -> bool:
    """Migrate a single file to include ontos_schema.
    
    Args:
        filepath: Path to markdown file.
        dry_run: If True, don't actually write changes.
        output: OutputHandler for user messages.
        
    Returns:
        True if file was (or would be) migrated, False otherwise.
    """
    if output is None:
        output = OutputHandler()
    
    # Read file content
    try:
        content = filepath.read_text(encoding='utf-8')
    except IOError as e:
        output.error(f"Could not read {filepath}: {e}")
        return False
    
    # Parse frontmatter
    fm = parse_frontmatter(str(filepath))
    if fm is None or 'id' not in fm:
        return False
    
    if 'ontos_schema' in fm:
        return False  # Already migrated
    
    # Add schema version
    new_fm = add_schema_to_frontmatter(fm)
    schema = new_fm['ontos_schema']
    
    if dry_run:
        output.info(f"Would migrate: {filepath}")
        output.detail(f"  ontos_schema: {schema}")
        return True
    
    # Build new content
    # Find end of frontmatter
    if not content.startswith('---'):
        output.error(f"Invalid frontmatter format in {filepath}")
        return False
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        output.error(f"Incomplete frontmatter in {filepath}")
        return False
    
    # Serialize new frontmatter
    new_fm_str = serialize_frontmatter(new_fm)
    new_content = f"---\n{new_fm_str}\n---{parts[2]}"
    
    # Write back
    try:
        filepath.write_text(new_content, encoding='utf-8')
        output.success(f"Migrated: {filepath} → ontos_schema: {schema}")
        return True
    except IOError as e:
        output.error(f"Could not write {filepath}: {e}")
        return False


def run_check(directories: List[str], output: OutputHandler) -> int:
    """Check which files need migration.
    
    Args:
        directories: Directories to scan.
        output: OutputHandler for messages.
        
    Returns:
        Exit code (0 if no migrations needed, 1 if migrations needed).
    """
    files = find_markdown_files(directories)
    
    needs_migration = []
    already_migrated = []
    not_ontos = []
    
    for filepath in files:
        needs, schema, msg = check_file_needs_migration(filepath)
        
        if needs:
            needs_migration.append((filepath, schema))
        elif schema:
            already_migrated.append((filepath, schema))
        else:
            not_ontos.append(filepath)
    
    # Report
    output.info(f"\n📊 Schema Migration Check")
    output.info(f"   Scanned: {len(files)} files")
    output.info(f"   Already migrated: {len(already_migrated)}")
    output.info(f"   Need migration: {len(needs_migration)}")
    output.info(f"   Not Ontos documents: {len(not_ontos)}")
    
    if needs_migration:
        output.info("\n📝 Files needing migration:")
        for filepath, schema in needs_migration:
            output.detail(f"  {filepath} → {schema}")
        
        output.info(f"\nRun with --dry-run to preview or --apply to migrate.")
        return 1
    else:
        output.success("\n✅ All Ontos documents have explicit schema versions.")
        return 0


def run_migration(directories: List[str], dry_run: bool, output: OutputHandler) -> int:
    """Run migration on files.
    
    Args:
        directories: Directories to scan.
        dry_run: If True, don't apply changes.
        output: OutputHandler for messages.
        
    Returns:
        Exit code (0 if successful).
    """
    files = find_markdown_files(directories)
    
    migrated = 0
    errors = 0
    
    mode = "Dry-run" if dry_run else "Applying"
    output.info(f"\n🔄 {mode} Schema Migration...")
    output.info(f"   Scanning: {', '.join(directories)}")
    
    for filepath in files:
        needs, schema, msg = check_file_needs_migration(filepath)
        
        if needs:
            success = migrate_file(filepath, dry_run=dry_run, output=output)
            if success:
                migrated += 1
            else:
                errors += 1
    
    # Summary
    if dry_run:
        output.info(f"\n📊 Dry-run complete: {migrated} files would be migrated")
        if migrated > 0:
            output.info("Run with --apply to apply changes.")
    else:
        output.success(f"\n✅ Migration complete: {migrated} files migrated")
        if errors > 0:
            output.error(f"   {errors} errors occurred")
            return 1
    
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate Ontos documents to use explicit ontos_schema field.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --check              Check which files need migration
  %(prog)s --dry-run            Preview changes without applying
  %(prog)s --apply              Apply migrations
  %(prog)s --apply --dirs docs  Migrate specific directory
"""
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true',
                       help="Check which files need migration")
    group.add_argument('--dry-run', action='store_true',
                       help="Preview changes without applying")
    group.add_argument('--apply', action='store_true',
                       help="Apply schema migrations")
    
    parser.add_argument('--dirs', nargs='+', default=None,
                        help="Directories to scan (default: docs, .ontos-internal)")
    parser.add_argument('--quiet', '-q', action='store_true',
                        help="Reduce output verbosity")
    parser.add_argument('--version', '-V', action='store_true',
                        help="Show version and exit")
    
    args = parser.parse_args()
    
    if args.version:
        try:
            from ontos_config import ONTOS_VERSION
        except ImportError:
            from ontos_config_defaults import ONTOS_VERSION
        print(f"Ontos {ONTOS_VERSION}")
        return 0
    
    output = OutputHandler(quiet=args.quiet)
    
    # Determine directories to scan
    if args.dirs:
        directories = args.dirs
    else:
        # Default directories
        directories = []
        for default in ['docs', '.ontos-internal']:
            if Path(default).exists():
                directories.append(default)
        
        if not directories:
            output.error("No default directories found. Use --dirs to specify.")
            return 1
    
    # Run appropriate mode
    if args.check:
        return run_check(directories, output)
    elif args.dry_run:
        return run_migration(directories, dry_run=True, output=output)
    elif args.apply:
        return run_migration(directories, dry_run=False, output=output)
    
    return 0


def emit_deprecation_notice(message: str) -> None:
    """Always-visible CLI notice for deprecated usage."""
    print(f"[DEPRECATION] {message}", file=sys.stderr)


if __name__ == '__main__':
    import os
    if not os.environ.get('ONTOS_CLI_DISPATCH'):
        if not os.environ.get('ONTOS_NO_DEPRECATION_WARNINGS'):
            emit_deprecation_notice(
                f"Direct execution of {Path(__file__).name} is deprecated. "
                "Use 'python3 ontos.py migrate' instead. "
                "Direct script execution will be removed in v3.0."
            )
    sys.exit(main())
