#!/usr/bin/env python3
"""Update describes_verified field in document frontmatter.

v2.7: Helper script to mark documentation as current after review.

Usage:
    python3 .ontos/scripts/ontos_verify.py docs/reference/Ontos_Manual.md
    python3 .ontos/scripts/ontos_verify.py --all
    python3 .ontos/scripts/ontos_verify.py docs/manual.md --date 2025-12-15
"""

import os
import sys
import argparse
import re
from datetime import date
from pathlib import Path
from typing import Optional

# Add scripts directory to path

from ontos.core.frontmatter import parse_frontmatter
from ontos.core.staleness import normalize_describes, parse_describes_verified, check_staleness
from ontos.core.paths import get_decision_history_path

from ontos_config import (
    __version__,
    DOCS_DIR,
)

from ontos_config_defaults import (
    PROJECT_ROOT,
    is_ontos_repo,
)

from ontos.core.context import SessionContext
from ontos.ui.output import OutputHandler


def find_stale_documents() -> list[dict]:
    """Find all documents with stale describes fields.
    
    Returns:
        List of dicts with 'doc_id', 'filepath', 'stale_atoms' info.
    """
    from ontos_generate_context_map import scan_docs
    
    # Determine scan directories
    if is_ontos_repo():
        target_dirs = [DOCS_DIR, 'docs']
    else:
        target_dirs = [DOCS_DIR]
    
    files_data = scan_docs(target_dirs)
    
    # Build ID to path mapping
    id_to_path = {doc_id: data['filepath'] for doc_id, data in files_data.items()}
    
    stale_docs = []
    for doc_id, data in files_data.items():
        describes = data.get('describes', [])
        if not describes:
            continue
        
        staleness = check_staleness(
            doc_id=doc_id,
            doc_path=data['filepath'],
            describes=describes,
            describes_verified=data.get('describes_verified'),
            id_to_path=id_to_path
        )
        
        if staleness and staleness.is_stale:
            stale_docs.append({
                'doc_id': doc_id,
                'filepath': data['filepath'],
                'staleness': staleness
            })
    
    return stale_docs


def update_describes_verified(
    filepath: str,
    new_date: date,
    output: OutputHandler = None,
    ctx: SessionContext = None
) -> bool:
    """Update the describes_verified field in a document.
    
    Args:
        filepath: Path to the markdown file.
        new_date: New date to set.
        output: OutputHandler instance (creates default if None).
        ctx: SessionContext for transactional writes.
        
    Returns:
        True if successful, False otherwise.
    """
    _owns_ctx = ctx is None
    if _owns_ctx:
        ctx = SessionContext.from_repo(Path.cwd())
    if output is None:
        output = OutputHandler()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except IOError as e:
        output.error(f"Error reading {filepath}: {e}")
        return False
    
    if not content.startswith('---'):
        output.error(f"{filepath} has no frontmatter")
        return False
    
    # Find the frontmatter section
    parts = content.split('---', 2)
    if len(parts) < 3:
        output.error(f"Invalid frontmatter in {filepath}")
        return False
    
    frontmatter = parts[1]
    body = parts[2]
    
    date_str = new_date.isoformat()
    
    # Check if describes_verified already exists
    if re.search(r'^describes_verified:', frontmatter, re.MULTILINE):
        # Update existing field
        new_frontmatter = re.sub(
            r'^describes_verified:.*$',
            f'describes_verified: {date_str}',
            frontmatter,
            flags=re.MULTILINE
        )
    else:
        # Add after describes field
        if re.search(r'^describes:', frontmatter, re.MULTILINE):
            new_frontmatter = re.sub(
                r'^(describes:.*(?:\n  - .*)*)$',
                f'\\1\ndescribes_verified: {date_str}',
                frontmatter,
                flags=re.MULTILINE
            )
        else:
            # Just append at end of frontmatter
            new_frontmatter = frontmatter.rstrip() + f'\ndescribes_verified: {date_str}\n'
    
    new_content = f'---{new_frontmatter}---{body}'
    
    try:
        # v2.8.4: Use buffer_write instead of direct write
        ctx.buffer_write(Path(filepath), new_content)
        
        if _owns_ctx:
            ctx.commit()
        return True
    except Exception as e:
        if _owns_ctx:
            ctx.rollback()
        output.error(f"Error writing {filepath}: {e}")
        return False


def verify_single(
    filepath: str,
    verify_date: Optional[date] = None,
    output: OutputHandler = None,
    ctx: SessionContext = None
) -> int:
    """Verify a single document as current.
    
    Args:
        filepath: Path to the document.
        verify_date: Date to set (default: today).
        output: OutputHandler instance (creates default if None).
        ctx: SessionContext for transactional writes.
        
    Returns:
        0 on success, 1 on failure.
    """
    if output is None:
        output = OutputHandler()
    
    if not os.path.exists(filepath):
        output.error(f"File not found: {filepath}")
        return 1
    
    # Check if document has describes field
    frontmatter = parse_frontmatter(filepath)
    if not frontmatter:
        output.error(f"No frontmatter in {filepath}")
        return 1
    
    describes = normalize_describes(frontmatter.get('describes'))
    if not describes:
        output.warning(f"{filepath} has no describes field, nothing to verify")
        return 0
    
    target_date = verify_date or date.today()
    
    if update_describes_verified(filepath, target_date, output=output, ctx=ctx):
        output.success(f"Updated describes_verified to {target_date}")
        return 0
    else:
        return 1


def verify_all_interactive(output: OutputHandler = None) -> int:
    """Interactively verify all stale documents.
    
    Args:
        output: OutputHandler instance (creates default if None).
    
    Returns:
        0 on success, 1 on failure.
    """
    if output is None:
        output = OutputHandler()
    
    stale_docs = find_stale_documents()
    
    if not stale_docs:
        output.success("No stale documents found.")
        return 0
    
    output.info(f"Found {len(stale_docs)} stale documents:")
    
    updated = 0
    skipped = 0
    
    for i, doc in enumerate(stale_docs, 1):
        staleness = doc['staleness']
        stale_atoms_str = ", ".join([f"{a} changed {d}" for a, d in staleness.stale_atoms[:3]])
        
        output.plain(f"\n[{i}/{len(stale_docs)}] {doc['doc_id']}")
        output.detail(f"File: {doc['filepath']}")
        output.detail(f"Stale because: {stale_atoms_str}")
        
        try:
            response = input("      Verify as current? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            output.warning("Aborted")
            return 1
        
        if response == 'y':
            if update_describes_verified(doc['filepath'], date.today(), output=output):
                output.success(f"Updated describes_verified to {date.today()}")
                updated += 1
            else:
                output.error("Failed to update")
        else:
            output.info("Skipped")
            skipped += 1
    
    output.info(f"Done. Updated: {updated}, Skipped: {skipped}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Verify documentation as current (update describes_verified)',
        epilog="""
Examples:
  python3 ontos_verify.py docs/reference/Ontos_Manual.md       # Single file
  python3 ontos_verify.py --all                                 # Interactive: all stale docs
  python3 ontos_verify.py docs/manual.md --date 2025-12-15     # Backdate
"""
    )
    parser.add_argument('filepath', nargs='?', help='Path to document to verify')
    parser.add_argument('--all', action='store_true', help='Interactively verify all stale documents')
    parser.add_argument('--date', type=str, help='Set specific date (YYYY-MM-DD), default: today')
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    args = parser.parse_args()
    
    # v2.8.4: Create OutputHandler at top of main()
    output = OutputHandler()
    
    if args.all:
        return verify_all_interactive(output=output)
    elif args.filepath:
        verify_date = None
        if args.date:
            try:
                verify_date = date.fromisoformat(args.date)
            except ValueError:
                output.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD.")
                return 1
        return verify_single(args.filepath, verify_date, output=output)
    else:
        parser.print_help()
        return 1


def emit_deprecation_notice(message: str) -> None:
    """Always-visible CLI notice for deprecated usage."""
    print(f"[DEPRECATION] {message}", file=sys.stderr)


if __name__ == '__main__':
    import os
    from pathlib import Path
    if not os.environ.get('ONTOS_CLI_DISPATCH'):
        if not os.environ.get('ONTOS_NO_DEPRECATION_WARNINGS'):
            emit_deprecation_notice(
                f"Direct execution of {Path(__file__).name} is deprecated. "
                "Use 'python3 ontos.py verify' instead. "
                "Direct script execution will be removed in v3.0."
            )
    sys.exit(main())
