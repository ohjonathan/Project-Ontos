"""Native verify command implementation."""

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional, Tuple, List

from ontos.core.frontmatter import parse_frontmatter
from ontos.core.staleness import (
    normalize_describes,
    check_staleness,
)
from ontos.core.context import SessionContext
from ontos.io.files import find_project_root, scan_documents
from ontos.ui.output import OutputHandler


@dataclass
class VerifyOptions:
    """Options for verify command."""
    path: Optional[Path] = None
    all: bool = False
    date: Optional[str] = None  # YYYY-MM-DD format
    quiet: bool = False
    json_output: bool = False


def find_stale_documents_list() -> List[dict]:
    """Find all documents with stale describes fields using new architecture symbols."""
    from ontos.core.curation import load_ontosignore
    
    root = find_project_root()
    ignore_patterns = load_ontosignore(root)
    files = scan_documents([root], skip_patterns=ignore_patterns) # Should probably use a more targeted scan if possible
    
    # Build ID to path mapping and gather data
    files_data = {}
    id_to_path = {}
    
    for f in files:
        try:
            # We need raw frontmatter for fields
            # Better to use a unified document loader if available, 
            # but for now we'll match legacy script logic.
            fm = parse_frontmatter(str(f))
            if not fm:
                continue
            
            doc_id = fm.get('id', f.stem)
            id_to_path[doc_id] = str(f)
            files_data[doc_id] = {
                'filepath': str(f),
                'describes': normalize_describes(fm.get('describes')),
                'describes_verified': fm.get('describes_verified')
            }
        except Exception:
            continue
            
    stale_docs = []
    for doc_id, data in files_data.items():
        if not data['describes']:
            continue
            
        staleness = check_staleness(
            doc_id=doc_id,
            doc_path=data['filepath'],
            describes=data['describes'],
            describes_verified=data['describes_verified'],
            id_to_path=id_to_path
        )
        
        if staleness and staleness.is_stale():
            stale_docs.append({
                'doc_id': doc_id,
                'filepath': data['filepath'],
                'staleness': staleness
            })
            
    return stale_docs


def update_describes_verified(
    filepath: Path,
    new_date: date,
    ctx: SessionContext,
    output: OutputHandler
) -> bool:
    """Update the describes_verified field in a document.
    
    Matches exact regex replacement logic from legacy script.
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        
        if not content.startswith('---'):
            output.error(f"{filepath} has no frontmatter")
            return False
        
        parts = content.split('---', 2)
        if len(parts) < 3:
            output.error(f"Invalid frontmatter in {filepath}")
            return False
        
        frontmatter = parts[1]
        body = parts[2]
        date_str = new_date.isoformat()
        
        # Check if describes_verified already exists
        if re.search(r'^describes_verified:', frontmatter, re.MULTILINE):
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
                new_frontmatter = frontmatter.rstrip() + f'\ndescribes_verified: {date_str}\n'
        
        new_content = f'---{new_frontmatter}---{body}'
        ctx.buffer_write(filepath, new_content)
        return True
    except Exception as e:
        output.error(f"Error updating {filepath}: {e}")
        return False


def verify_document(path: Path, verify_date: str) -> Tuple[bool, str]:
    """Helper for verify command."""
    # Ensure path is Path object
    p = Path(path)
    root = find_project_root()
    ctx = SessionContext.from_repo(root)
    output = OutputHandler(quiet=True)
    
    try:
        dt = date.fromisoformat(verify_date)
    except ValueError:
        return False, "Invalid date format"
        
    success = update_describes_verified(p, dt, ctx, output)
    if success:
        ctx.commit()
        return True, "Verified"
    return False, "Failed"


def verify_all_interactive(verify_date: date, output: OutputHandler) -> int:
    """Interactively verify all stale documents."""
    stale_docs = find_stale_documents_list()
    
    if not stale_docs:
        output.success("No stale documents found.")
        return 0
    
    output.info(f"Found {len(stale_docs)} stale documents:")
    
    root = find_project_root()
    ctx = SessionContext.from_repo(root)
    updated = 0
    skipped = 0
    
    for i, doc in enumerate(stale_docs, 1):
        staleness = doc['staleness']
        # Show up to 3 stale atoms
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
            if update_describes_verified(Path(doc['filepath']), verify_date, ctx, output):
                output.success(f"Updated describes_verified to {verify_date}")
                updated += 1
            else:
                output.error("Failed to update")
        else:
            output.info("Skipped")
            skipped += 1
            
    if updated > 0:
        ctx.commit()
        
    output.info(f"Done. Updated: {updated}, Skipped: {skipped}")
    return 0


def verify_command(options: VerifyOptions) -> Tuple[int, str]:
    """Execute verify command."""
    output = OutputHandler(quiet=options.quiet)
    
    # Parse date
    verify_date = date.today()
    if options.date:
        try:
            verify_date = date.fromisoformat(options.date)
        except ValueError:
            output.error(f"Invalid date format: {options.date}. Use YYYY-MM-DD.")
            return 1, f"Invalid date format: {options.date}"

    if options.path:
        # Single file mode
        if not options.path.exists():
            output.error(f"File not found: {options.path}")
            return 1, f"File not found: {options.path}"
            
        root = find_project_root()
        ctx = SessionContext.from_repo(root)
        
        # Check if doc has describes
        fm = parse_frontmatter(str(options.path))
        if not fm:
            output.error(f"No frontmatter in {options.path}")
            return 1, "No frontmatter"
            
        describes = normalize_describes(fm.get('describes'))
        if not describes:
            output.warning(f"{options.path} has no describes field, nothing to verify")
            return 0, "Nothing to verify"
            
        if update_describes_verified(options.path, verify_date, ctx, output):
            ctx.commit()
            output.success(f"Updated describes_verified to {verify_date}")
            return 0, "Success"
        else:
            return 1, "Update failed"

    elif options.all:
        # Interactive all mode
        result = verify_all_interactive(verify_date, output)
        return result, "Interactive session ended"
        
    else:
        output.error("Specify a file path or use --all")
        return 1, "No target specified"
