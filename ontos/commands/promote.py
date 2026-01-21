"""Native promote command implementation."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ontos.core.frontmatter import parse_frontmatter
from ontos.core.schema import serialize_frontmatter
from ontos.core.curation import (
    CurationLevel,
    CurationInfo,
    get_curation_info,
    promote_to_full,
    level_marker,
)
from ontos.core.context import SessionContext
from ontos.io.files import find_project_root, scan_documents
from ontos.ui.output import OutputHandler


@dataclass
class PromoteOptions:
    """Options for promote command."""
    files: Optional[List[Path]] = None
    check: bool = False
    all_ready: bool = False
    quiet: bool = False
    json_output: bool = False


def fuzzy_match_ids(query: str, all_ids: List[str]) -> List[str]:
    """Simple fuzzy matching for document IDs."""
    query_lower = query.lower()
    if query in all_ids:
        return [query]
    prefix_matches = [id for id in all_ids if id.lower().startswith(query_lower)]
    if prefix_matches:
        return prefix_matches[:5]
    substring_matches = [id for id in all_ids if query_lower in id.lower()]
    return substring_matches[:5]


def interactive_get_depends_on(
    doc_id: str,
    doc_type: str,
    existing_ids: List[str],
    output: OutputHandler
) -> Optional[List[str]]:
    """Prompt user for depends_on."""
    if doc_type in ('kernel', 'log'):
        return None
    
    print(f"\n  This is a '{doc_type}' document. What does it depend on?")
    print("  (Type to search, comma-separate multiple, or empty to skip)")
    
    while True:
        try:
            user_input = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
            
        if not user_input:
            return None
        
        parts = [p.strip() for p in user_input.split(',') if p.strip()]
        resolved = []
        for part in parts:
            matches = fuzzy_match_ids(part, existing_ids)
            if len(matches) == 1:
                resolved.append(matches[0])
            elif len(matches) > 1:
                print(f"    Multiple matches for '{part}': {matches}")
                try:
                    choice = input(f"    Choose one (or exact ID): ").strip()
                except (EOFError, KeyboardInterrupt):
                    continue
                if choice in matches or choice in existing_ids:
                    resolved.append(choice)
                else:
                    print(f"    Skipping '{part}'")
            else:
                output.warning(f"    ID '{part}' not found - adding anyway")
                resolved.append(part)
        
        if resolved:
            print(f"  ✓ depends_on: {resolved}")
            return resolved
        return None


def interactive_get_concepts(doc_type: str, output: OutputHandler) -> Optional[List[str]]:
    """Prompt user for concepts."""
    if doc_type != 'log':
        return None
    
    print("\n  Logs require concepts. Enter concepts (comma-separated):")
    try:
        user_input = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
        
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
    """Apply promotion to a document."""
    try:
        content = filepath.read_text(encoding='utf-8')
        # Splitting logic to get body
        parts = content.split('---', 2)
        if len(parts) < 3:
            output.error(f"Invalid format in {filepath}")
            return False
            
        body = parts[2]
        
        new_fm, summary_seed = promote_to_full(
            frontmatter,
            depends_on=depends_on,
            concepts=concepts
        )
        
        fm_yaml = serialize_frontmatter(new_fm)
        new_content = f"---\n{fm_yaml}\n---{body}"
        
        ctx.buffer_write(filepath, new_content)
        output.success(f"Promoted: {frontmatter.get('id')} → Level 2")
        return True
    except Exception as e:
        output.error(f"Failed to promote {filepath}: {e}")
        return False


def promote_command(options: PromoteOptions) -> Tuple[int, str]:
    """Execute promote command."""
    output = OutputHandler(quiet=options.quiet)
    root = find_project_root()
    
    # 1. Gather files
    if options.files:
        files = [root / f if not f.is_absolute() else f for f in options.files]
    else:
        # Scan all documents
        dirs = [root / d for d in ['docs', '.ontos-internal'] if (root / d).exists()]
        if not dirs:
            dirs = [root]
        from ontos.core.curation import load_ontosignore
        ignore_patterns = load_ontosignore(root)
        files = scan_documents(dirs, skip_patterns=ignore_patterns)
        files = [f for f in files if f.suffix == ".md"]

    # 2. Extract info and filter promotable
    promotable = []
    existing_ids = []
    for f in files:
        try:
            fm = parse_frontmatter(str(f))
            if fm and 'id' in fm:
                doc_id = fm['id']
                existing_ids.append(doc_id)
                info = get_curation_info(fm)
                if info.level < CurationLevel.FULL:
                    promotable.append((f, fm, info))
        except Exception:
            continue
            
    if not promotable:
        if not options.quiet:
            output.success("No documents need promotion - all at Level 2!")
        return 0, "No documents to promote"

    # 3. Handle --check
    if options.check:
        output.info(f"Found {len(promotable)} document(s) that can be promoted:\n")
        for f, fm, info in promotable:
            rel = f.relative_to(root)
            marker = level_marker(info.level)
            ready = "✓ ready" if info.promotable else "○ needs work"
            print(f"  {marker} {fm.get('id'):<30} {ready}")
            if not info.promotable:
                for blocker in info.promotion_blockers[:2]:
                    print(f"      → {blocker}")
        return 0, f"{len(promotable)} documents find"

    ctx = SessionContext.from_repo(root)
    success_count = 0
    
    # 4. Handle --all-ready
    if options.all_ready:
        ready_docs = [(f, fm, info) for f, fm, info in promotable if info.promotable]
        if not ready_docs:
            output.warning("No documents are ready for automatic promotion.")
            return 0, "Nothing ready"
            
        output.info(f"Batch promoting {len(ready_docs)} ready document(s)...")
        for f, fm, info in ready_docs:
            if apply_promotion(f, fm, fm.get('depends_on'), fm.get('concepts'), ctx, output):
                success_count += 1
        ctx.commit()
        return 0, f"Promoted {success_count} documents"

    # 5. Interactive Mode
    output.info(f"Found {len(promotable)} document(s) at L0/L1")
    for f, fm, info in promotable:
        doc_id = fm.get('id', 'unknown')
        doc_type = fm.get('type', 'unknown')
        
        print(f"\n{'='*60}")
        output.info(f"Promoting: {doc_id} ({level_marker(info.level)} → [L2])")
        print(f"  Type: {doc_type}")
        print(f"  Path: {f.relative_to(root)}")
        
        if info.promotion_blockers:
            print(f"\n  Blockers to resolve:")
            for blocker in info.promotion_blockers:
                print(f"    - {blocker}")
        
        # Get depends_on if needed
        depends_on = fm.get('depends_on')
        if doc_type not in ('kernel', 'log') and not depends_on:
            depends_on = interactive_get_depends_on(doc_id, doc_type, existing_ids, output)
            if depends_on is None and doc_type not in ('kernel', 'log'):
                output.warning("  depends_on required for this type. Skipping.")
                continue
        
        # Get concepts if needed
        concepts = fm.get('concepts')
        if doc_type == 'log' and not concepts:
            concepts = interactive_get_concepts(doc_type, output)
            if concepts is None:
                output.warning("  concepts required for logs. Skipping.")
                continue
        
        try:
            confirm = input("\n  Promote this document? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled.")
            break
            
        if confirm in ('n', 'no'):
            output.info("  Skipped.")
            continue
            
        if apply_promotion(f, fm, depends_on, concepts, ctx, output):
            success_count += 1

    ctx.commit()
    if success_count > 0:
        output.success(f"Promoted {success_count} document(s) to Level 2")
    return 0, f"Promoted {success_count} documents"
