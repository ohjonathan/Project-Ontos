#!/usr/bin/env python3
"""Generate Level 0 scaffold frontmatter for untagged markdown files.

Usage:
    python3 ontos.py scaffold                    # Preview (dry-run, default)
    python3 ontos.py scaffold --apply            # Apply scaffolding
    python3 ontos.py scaffold docs/new.md --apply  # Scaffold specific file

Options:
    --apply         Apply scaffolding (required to modify files)
    --dry-run       Preview changes without applying (default)
    --quiet         Minimal output
    -h, --help      Show this help

The scaffold command adds minimal Ontos frontmatter to markdown files that
don't have any. It uses heuristics to infer document type from path and content.

Respects .ontosignore file patterns in repository root.
"""

import argparse
import sys
from pathlib import Path

# Fix sys.path to avoid ontos.py shadowing the ontos package.
# Python auto-inserts script dir at sys.path[0]; remove it before importing ontos.
SCRIPTS_DIR = Path(__file__).parent.resolve()
if sys.path and Path(sys.path[0]).resolve() == SCRIPTS_DIR:
    sys.path.pop(0)

# Import ontos package BEFORE adding scripts dir back to path
from ontos.core.context import SessionContext
from ontos.core.frontmatter import parse_frontmatter
from ontos.core.schema import serialize_frontmatter
from ontos.core.curation import (
    create_scaffold,
    load_ontosignore,
    should_ignore,
    CurationLevel,
)
from ontos.ui.output import OutputHandler

# Now add scripts dir to import ontos_config_defaults
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))
from ontos_config_defaults import PROJECT_ROOT


def find_untagged_markdown(
    root: Path = None,
    ignore_patterns: list = None
) -> list:
    """Find markdown files without Ontos frontmatter.
    
    Args:
        root: Directory to search from (default: PROJECT_ROOT).
        ignore_patterns: Patterns to exclude.
        
    Returns:
        List of Path objects for files needing scaffolding.
    """
    if root is None:
        root = Path(PROJECT_ROOT)
    if ignore_patterns is None:
        ignore_patterns = []
    
    # Default ignore patterns (in addition to .ontosignore)
    default_ignores = [
        '.git', '__pycache__', 'node_modules', '.venv', 'venv',
        'vendor', '.pytest_cache', '.mypy_cache',
    ]
    
    untagged = []
    
    for md_file in root.rglob("*.md"):
        # Skip hidden directories
        if any(part.startswith('.') for part in md_file.parts[:-1]):
            if '.ontos' not in str(md_file) and '.ontos-internal' not in str(md_file):
                continue
        
        # Skip default ignores
        if any(ignore in str(md_file) for ignore in default_ignores):
            continue
        
        # Skip .ontosignore patterns
        if should_ignore(md_file, ignore_patterns):
            continue
        
        # Check if file has frontmatter
        try:
            content = md_file.read_text()
            if not content.strip():
                continue  # Skip empty files
            
            fm, _ = parse_frontmatter(content)
            if not fm or 'id' not in fm:
                # No valid frontmatter, needs scaffolding
                untagged.append(md_file)
        except Exception:
            continue  # Skip files that can't be read
    
    return untagged


def apply_scaffold_to_file(
    filepath: Path,
    ctx: SessionContext = None,
    output: OutputHandler = None
) -> bool:
    """Apply scaffold frontmatter to a single file.
    
    Args:
        filepath: Path to the markdown file.
        ctx: Optional SessionContext for buffered writes.
        output: Optional OutputHandler for messages.
        
    Returns:
        True if successful, False otherwise.
    """
    _owns_ctx = ctx is None
    if _owns_ctx:
        ctx = SessionContext()
    
    if output is None:
        output = OutputHandler()
    
    try:
        content = filepath.read_text()
        
        # Generate scaffold frontmatter
        fm = create_scaffold(filepath, content)
        
        # Serialize frontmatter
        fm_yaml = serialize_frontmatter(fm)
        
        # Combine with original content
        new_content = f"---\n{fm_yaml}\n---\n\n{content}"
        
        # Buffer the write
        ctx.buffer_write(filepath, new_content)
        
        if _owns_ctx:
            ctx.commit()
        
        output.success(f"Scaffolded: {filepath}")
        return True
        
    except Exception as e:
        output.error(f"Failed to scaffold {filepath}: {e}")
        return False


def preview_scaffold(filepath: Path, output: OutputHandler = None) -> dict:
    """Preview what scaffold would be applied.
    
    Args:
        filepath: Path to the markdown file.
        output: Optional OutputHandler for messages.
        
    Returns:
        Scaffold frontmatter dict.
    """
    if output is None:
        output = OutputHandler()
    
    try:
        content = filepath.read_text()
        fm = create_scaffold(filepath, content)
        return fm
    except Exception as e:
        output.error(f"Failed to preview {filepath}: {e}")
        return {}


def main() -> int:
    """Main entry point for scaffold command."""
    parser = argparse.ArgumentParser(
        description="Generate Level 0 scaffold frontmatter for untagged files."
    )
    parser.add_argument(
        'files', nargs='*',
        help="Specific files to scaffold (default: scan all)"
    )
    parser.add_argument(
        '--apply', action='store_true',
        help="Apply scaffolding (required to modify files)"
    )
    parser.add_argument(
        '--dry-run', action='store_true', default=True,
        help="Preview changes without applying (default)"
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    # --apply overrides --dry-run
    dry_run = not args.apply
    
    output = OutputHandler(quiet=args.quiet)
    
    if not args.quiet:
        if dry_run:
            output.info("Scaffold preview (use --apply to execute)")
        else:
            output.info("Applying scaffolds...")
    
    # Load ignore patterns
    ignore_patterns = load_ontosignore(Path(PROJECT_ROOT))
    
    # Find or use specified files
    if args.files:
        files = [Path(f) for f in args.files if Path(f).exists()]
        if not files:
            output.error("No valid files specified")
            return 1
    else:
        files = find_untagged_markdown(
            Path(PROJECT_ROOT),
            ignore_patterns
        )
    
    if not files:
        if not args.quiet:
            output.success("No files need scaffolding")
        return 0
    
    if not args.quiet:
        output.info(f"Found {len(files)} file(s) needing scaffolding")
    
    # Preview or apply
    if dry_run:
        for filepath in files:
            fm = preview_scaffold(filepath, output)
            if fm:
                rel_path = filepath.relative_to(PROJECT_ROOT)
                print(f"\n  {rel_path}")
                print(f"    id: {fm.get('id')}")
                print(f"    type: {fm.get('type')}")
                print(f"    status: scaffold")
        
        if not args.quiet:
            print()
            output.info("Run with --apply to execute scaffolding")
        return 0
    else:
        # Apply with transactional context
        ctx = SessionContext()
        success_count = 0
        
        for filepath in files:
            if apply_scaffold_to_file(filepath, ctx, output):
                success_count += 1
        
        # Commit all changes
        ctx.commit()
        
        if not args.quiet:
            output.success(f"Scaffolded {success_count}/{len(files)} files")
        
        return 0 if success_count == len(files) else 1


def emit_deprecation_notice(message: str) -> None:
    """Always-visible CLI notice for deprecated usage."""
    import sys
    print(f"[DEPRECATION] {message}", file=sys.stderr)


if __name__ == '__main__':
    import os
    if not os.environ.get('ONTOS_CLI_DISPATCH'):
        if not os.environ.get('ONTOS_NO_DEPRECATION_WARNINGS'):
            emit_deprecation_notice(
                f"Direct execution of {Path(__file__).name} is deprecated. "
                "Use 'python3 ontos.py scaffold' instead. "
                "Direct script execution will be removed in v3.0."
            )
    sys.exit(main())
