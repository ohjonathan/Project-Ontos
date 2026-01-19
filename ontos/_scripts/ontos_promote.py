#!/usr/bin/env python3
"""Promote documents from Level 0/1 to Level 2 interactively.

Usage:
    python3 ontos.py promote                    # Interactive mode
    python3 ontos.py promote docs/feature.md   # Promote specific file
    python3 ontos.py promote --check           # Show promotable docs
    python3 ontos.py promote --all-ready       # Batch promote ready docs

Options:
    --check         Show documents that can be promoted
    --all-ready     Promote all documents that are ready
    --quiet         Minimal output
    -h, --help      Show this help

The promote command guides users through completing Level 2 curation,
prompting for depends_on and concepts as needed.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

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
    CurationLevel,
    CurationInfo,
    detect_curation_level,
    get_curation_info,
    promote_to_full,
    check_promotion_readiness,
    level_marker,
)
from ontos.ui.output import OutputHandler

# Now add scripts dir to import ontos_config_defaults
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))
from ontos_config_defaults import PROJECT_ROOT, VALID_TYPES


def find_all_document_ids(docs_dir: Path) -> List[str]:
    """Get all document IDs for fuzzy matching.
    
    Args:
        docs_dir: Directory to scan.
        
    Returns:
        List of document IDs found.
    """
    ids = []
    
    for md_file in docs_dir.rglob("*.md"):
        try:
            content = md_file.read_text()
            fm, _ = parse_frontmatter(content)
            if fm and 'id' in fm:
                ids.append(fm['id'])
        except Exception:
            continue
    
    return sorted(set(ids))


def find_promotable_documents(
    docs_dir: Path
) -> List[Tuple[Path, dict, CurationInfo]]:
    """Scan for L0/L1 documents that can be promoted.
    
    Args:
        docs_dir: Directory to scan.
        
    Returns:
        List of (filepath, frontmatter, curation_info) tuples.
    """
    promotable = []
    
    for md_file in docs_dir.rglob("*.md"):
        try:
            content = md_file.read_text()
            fm, _ = parse_frontmatter(content)
            if not fm or 'id' not in fm:
                continue
            
            info = get_curation_info(fm)
            
            # Only include L0/L1 that could potentially be promoted
            if info.level < CurationLevel.FULL:
                promotable.append((md_file, fm, info))
                
        except Exception:
            continue
    
    return promotable


def fuzzy_match_ids(query: str, all_ids: List[str]) -> List[str]:
    """Simple fuzzy matching for document IDs.
    
    Args:
        query: Search query.
        all_ids: List of valid IDs.
        
    Returns:
        Matching IDs (prefix and substring matches).
    """
    query_lower = query.lower()
    
    # Exact match first
    if query in all_ids:
        return [query]
    
    # Prefix matches
    prefix_matches = [id for id in all_ids if id.lower().startswith(query_lower)]
    if prefix_matches:
        return prefix_matches[:5]
    
    # Substring matches
    substring_matches = [id for id in all_ids if query_lower in id.lower()]
    return substring_matches[:5]


def interactive_get_depends_on(
    doc_type: str,
    existing_ids: List[str],
    output: OutputHandler
) -> Optional[List[str]]:
    """Prompt user for depends_on with fuzzy ID matching.
    
    Args:
        doc_type: Document type.
        existing_ids: Valid document IDs for matching.
        output: OutputHandler for messages.
        
    Returns:
        List of dependency IDs or None if cancelled.
    """
    if doc_type in ('kernel', 'log'):
        # Kernel docs and logs don't require depends_on
        return None
    
    print(f"\n  This is a '{doc_type}' document. What does it depend on?")
    print("  (Type to search, comma-separate multiple, or empty to skip)")
    
    while True:
        user_input = input("  > ").strip()
        
        if not user_input:
            return None
        
        # Parse comma-separated input
        parts = [p.strip() for p in user_input.split(',') if p.strip()]
        
        resolved = []
        for part in parts:
            matches = fuzzy_match_ids(part, existing_ids)
            if len(matches) == 1:
                resolved.append(matches[0])
            elif len(matches) > 1:
                print(f"    Multiple matches for '{part}': {matches}")
                choice = input(f"    Choose one (or exact ID): ").strip()
                if choice in matches or choice in existing_ids:
                    resolved.append(choice)
                else:
                    print(f"    Skipping '{part}'")
            else:
                # Allow exact ID even if not in list (forward reference)
                output.warning(f"    ID '{part}' not found - adding anyway")
                resolved.append(part)
        
        if resolved:
            print(f"  ✓ depends_on: {resolved}")
            return resolved
        
        return None


def interactive_get_concepts(
    doc_type: str,
    output: OutputHandler
) -> Optional[List[str]]:
    """Prompt user for concepts.
    
    Args:
        doc_type: Document type.
        output: OutputHandler for messages.
        
    Returns:
        List of concepts or None if not needed.
    """
    if doc_type != 'log':
        return None
    
    print("\n  Logs require concepts. Enter concepts (comma-separated):")
    user_input = input("  > ").strip()
    
    if not user_input:
        output.warning("  No concepts provided - log requires concepts at L2")
        return None
    
    concepts = [c.strip() for c in user_input.split(',') if c.strip()]
    print(f"  ✓ concepts: {concepts}")
    return concepts


def apply_promotion(
    filepath: Path,
    frontmatter: dict,
    depends_on: Optional[List[str]],
    concepts: Optional[List[str]],
    ctx: SessionContext,
    output: OutputHandler
) -> bool:
    """Apply promotion to a document.
    
    Args:
        filepath: Path to the document.
        frontmatter: Current frontmatter.
        depends_on: Dependencies to add.
        concepts: Concepts to add.
        ctx: SessionContext for buffered writes.
        output: OutputHandler for messages.
        
    Returns:
        True if successful.
    """
    try:
        # Read original content
        content = filepath.read_text()
        
        # Get body (content after frontmatter)
        _, body = parse_frontmatter(content)
        
        # Promote frontmatter
        new_fm, summary_seed = promote_to_full(
            frontmatter,
            depends_on=depends_on,
            concepts=concepts
        )
        
        # Serialize new frontmatter
        fm_yaml = serialize_frontmatter(new_fm)
        
        # Reconstruct document
        new_content = f"---\n{fm_yaml}\n---\n{body}"
        
        # Buffer the write
        ctx.buffer_write(filepath, new_content)
        
        output.success(f"Promoted: {frontmatter.get('id')} → Level 2")
        
        if summary_seed:
            output.info(f"  💡 Goal preserved: \"{summary_seed[:50]}...\"")
        
        return True
        
    except Exception as e:
        output.error(f"Failed to promote {filepath}: {e}")
        return False


def promote_interactive(
    filepath: Path,
    frontmatter: dict,
    info: CurationInfo,
    existing_ids: List[str],
    ctx: SessionContext,
    output: OutputHandler
) -> bool:
    """Full interactive flow for promoting one document.
    
    Args:
        filepath: Path to the document.
        frontmatter: Current frontmatter.
        info: Curation info.
        existing_ids: Valid IDs for fuzzy matching.
        ctx: SessionContext.
        output: OutputHandler.
        
    Returns:
        True if promoted, False otherwise.
    """
    doc_id = frontmatter.get('id', 'unknown')
    doc_type = frontmatter.get('type', 'unknown')
    
    print(f"\n{'='*60}")
    output.info(f"Promoting: {doc_id} ({level_marker(info.level)} → [L2])")
    print(f"  Type: {doc_type}")
    print(f"  Path: {filepath}")
    
    if info.promotion_blockers:
        print(f"\n  Blockers to resolve:")
        for blocker in info.promotion_blockers:
            print(f"    - {blocker}")
    
    # Get depends_on if needed
    depends_on = None
    if doc_type not in ('kernel', 'log') and not frontmatter.get('depends_on'):
        depends_on = interactive_get_depends_on(doc_type, existing_ids, output)
        if depends_on is None and doc_type not in ('kernel', 'log'):
            output.warning("  depends_on required for this type. Skipping.")
            return False
    
    # Get concepts if needed
    concepts = None
    if doc_type == 'log' and not frontmatter.get('concepts'):
        concepts = interactive_get_concepts(doc_type, output)
        if concepts is None:
            output.warning("  concepts required for logs. Skipping.")
            return False
    
    # Confirm promotion
    confirm = input("\n  Promote this document? [Y/n]: ").strip().lower()
    if confirm in ('n', 'no'):
        output.info("  Skipped.")
        return False
    
    return apply_promotion(filepath, frontmatter, depends_on, concepts, ctx, output)


def main() -> int:
    """Main entry point for promote command."""
    parser = argparse.ArgumentParser(
        description="Promote documents from Level 0/1 to Level 2."
    )
    parser.add_argument(
        'files', nargs='*',
        help="Specific files to promote"
    )
    parser.add_argument(
        '--check', action='store_true',
        help="Show promotable documents without changing anything"
    )
    parser.add_argument(
        '--all-ready', action='store_true',
        help="Batch promote all documents that are ready"
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help="Minimal output"
    )
    
    args = parser.parse_args()
    output = OutputHandler(quiet=args.quiet)
    
    docs_dir = Path(PROJECT_ROOT)
    
    # Get all existing IDs for fuzzy matching
    existing_ids = find_all_document_ids(docs_dir)
    
    # Find promotable documents
    if args.files:
        # Specific files
        promotable = []
        for f in args.files:
            filepath = Path(f)
            if not filepath.is_absolute():
                filepath = docs_dir / f
            if filepath.exists():
                try:
                    content = filepath.read_text()
                    fm, _ = parse_frontmatter(content)
                    if fm:
                        info = get_curation_info(fm)
                        promotable.append((filepath, fm, info))
                except Exception as e:
                    output.error(f"Cannot read {filepath}: {e}")
    else:
        promotable = find_promotable_documents(docs_dir)
    
    # Filter to only L0/L1
    promotable = [(p, fm, info) for p, fm, info in promotable 
                  if info.level < CurationLevel.FULL]
    
    if not promotable:
        if not args.quiet:
            output.success("No documents need promotion - all at Level 2!")
        return 0
    
    # Check mode - just show what can be promoted
    if args.check:
        output.info(f"Found {len(promotable)} document(s) that can be promoted:\n")
        
        for filepath, fm, info in promotable:
            rel_path = filepath.relative_to(docs_dir)
            marker = level_marker(info.level)
            ready = "✓ ready" if info.promotable else "○ needs work"
            print(f"  {marker} {fm.get('id'):<30} {ready}")
            if not info.promotable:
                for blocker in info.promotion_blockers[:2]:
                    print(f"      → {blocker}")
        
        return 0
    
    # Batch promote ready docs
    if args.all_ready:
        ready_docs = [(p, fm, info) for p, fm, info in promotable if info.promotable]
        
        if not ready_docs:
            output.warning("No documents are ready for automatic promotion.")
            output.info("Use interactive mode to provide missing fields.")
            return 0
        
        output.info(f"Batch promoting {len(ready_docs)} ready document(s)...")
        
        ctx = SessionContext()
        success = 0
        
        for filepath, fm, info in ready_docs:
            if apply_promotion(filepath, fm, fm.get('depends_on'), fm.get('concepts'), ctx, output):
                success += 1
        
        ctx.commit()
        output.success(f"Promoted {success}/{len(ready_docs)} documents")
        return 0 if success == len(ready_docs) else 1
    
    # Interactive mode
    output.info(f"Found {len(promotable)} document(s) at L0/L1")
    
    ctx = SessionContext()
    success_count = 0
    
    for filepath, fm, info in promotable:
        if promote_interactive(filepath, fm, info, existing_ids, ctx, output):
            success_count += 1
    
    # Commit all changes
    ctx.commit()
    
    if success_count > 0:
        output.success(f"Promoted {success_count} document(s) to Level 2")
    
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
                "Use 'python3 ontos.py promote' instead. "
                "Direct script execution will be removed in v3.0."
            )
    sys.exit(main())
