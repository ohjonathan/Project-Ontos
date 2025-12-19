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
from typing import Optional

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ontos_lib import (
    parse_frontmatter,
    normalize_describes,
    parse_describes_verified,
    check_staleness,
    get_decision_history_path,
)

from ontos_config import (
    __version__,
    DOCS_DIR,
)

from ontos_config_defaults import (
    PROJECT_ROOT,
    is_ontos_repo,
)


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


def update_describes_verified(filepath: str, new_date: date) -> bool:
    """Update the describes_verified field in a document.
    
    Args:
        filepath: Path to the markdown file.
        new_date: New date to set.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except IOError as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    if not content.startswith('---'):
        print(f"Error: {filepath} has no frontmatter")
        return False
    
    # Find the frontmatter section
    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f"Error: Invalid frontmatter in {filepath}")
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
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    except IOError as e:
        print(f"Error writing {filepath}: {e}")
        return False


def verify_single(filepath: str, verify_date: Optional[date] = None) -> int:
    """Verify a single document as current.
    
    Args:
        filepath: Path to the document.
        verify_date: Date to set (default: today).
        
    Returns:
        0 on success, 1 on failure.
    """
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return 1
    
    # Check if document has describes field
    frontmatter = parse_frontmatter(filepath)
    if not frontmatter:
        print(f"Error: No frontmatter in {filepath}")
        return 1
    
    describes = normalize_describes(frontmatter.get('describes'))
    if not describes:
        print(f"Warning: {filepath} has no describes field, nothing to verify")
        return 0
    
    target_date = verify_date or date.today()
    
    if update_describes_verified(filepath, target_date):
        print(f"✅ Updated describes_verified to {target_date}")
        return 0
    else:
        return 1


def verify_all_interactive() -> int:
    """Interactively verify all stale documents.
    
    Returns:
        0 on success, 1 on failure.
    """
    stale_docs = find_stale_documents()
    
    if not stale_docs:
        print("No stale documents found.")
        return 0
    
    print(f"Found {len(stale_docs)} stale documents:\n")
    
    updated = 0
    skipped = 0
    
    for i, doc in enumerate(stale_docs, 1):
        staleness = doc['staleness']
        stale_atoms_str = ", ".join([f"{a} changed {d}" for a, d in staleness.stale_atoms[:3]])
        
        print(f"[{i}/{len(stale_docs)}] {doc['doc_id']}")
        print(f"      File: {doc['filepath']}")
        print(f"      Stale because: {stale_atoms_str}")
        
        try:
            response = input("      Verify as current? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n⏹️  Aborted")
            return 1
        
        if response == 'y':
            if update_describes_verified(doc['filepath'], date.today()):
                print(f"      ✅ Updated describes_verified to {date.today()}")
                updated += 1
            else:
                print("      ❌ Failed to update")
        else:
            print("      ⏭️  Skipped")
            skipped += 1
        print()
    
    print(f"Done. Updated: {updated}, Skipped: {skipped}")
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
    
    if args.all:
        return verify_all_interactive()
    elif args.filepath:
        verify_date = None
        if args.date:
            try:
                verify_date = date.fromisoformat(args.date)
            except ValueError:
                print(f"Error: Invalid date format: {args.date}. Use YYYY-MM-DD.")
                return 1
        return verify_single(args.filepath, verify_date)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
