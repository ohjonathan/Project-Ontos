"""Query the Ontos knowledge graph."""

import os
import sys
import argparse
import re
from collections import defaultdict
from datetime import datetime

# Add scripts dir to path

from ontos.core.frontmatter import parse_frontmatter, normalize_depends_on, normalize_type
from ontos.core.config import get_git_last_modified
from ontos_config import __version__, DOCS_DIR, SKIP_PATTERNS
from ontos.ui.output import OutputHandler


def scan_docs_for_query(root_dir: str) -> dict:
    """Scan documentation files for query operations.
    
    Simplified version of scan_docs from ontos_generate_context_map.py.
    """
    files_data = {}
    
    if not os.path.isdir(root_dir):
        return files_data
    
    for subdir, dirs, files in os.walk(root_dir):
        # Prune skipped directories
        dirs[:] = [d for d in dirs if not any(p.rstrip('/') == d for p in SKIP_PATTERNS)]
        
        for file in files:
            if not file.endswith('.md'):
                continue
            if any(pattern in file for pattern in SKIP_PATTERNS):
                continue
            
            filepath = os.path.join(subdir, file)
            frontmatter = parse_frontmatter(filepath)
            
            if frontmatter and frontmatter.get('id'):
                doc_id = str(frontmatter['id']).strip()
                if not doc_id or doc_id.startswith('_'):
                    continue
                
                files_data[doc_id] = {
                    'filepath': filepath,
                    'filename': file,
                    'type': normalize_type(frontmatter.get('type')),
                    'depends_on': normalize_depends_on(frontmatter.get('depends_on')),
                    'status': str(frontmatter.get('status') or 'unknown').strip(),
                    'concepts': frontmatter.get('concepts', []),
                    'impacts': frontmatter.get('impacts', []),
                }
    
    return files_data


def build_graph(files_data: dict) -> tuple:
    """Build adjacency and reverse adjacency lists."""
    depends_on = defaultdict(list)
    depended_by = defaultdict(list)
    
    for doc_id, data in files_data.items():
        deps = data.get('depends_on', [])
        for dep in deps:
            depends_on[doc_id].append(dep)
            depended_by[dep].append(doc_id)
    
    return dict(depends_on), dict(depended_by)


def query_depends_on(files_data: dict, target_id: str) -> list:
    """What does this document depend on?"""
    if target_id not in files_data:
        return []
    return files_data[target_id].get('depends_on', [])


def query_depended_by(files_data: dict, target_id: str) -> list:
    """What documents depend on this one?"""
    _, depended_by = build_graph(files_data)
    return depended_by.get(target_id, [])


def query_concept(files_data: dict, concept: str) -> list:
    """Find all documents with this concept."""
    matches = []
    for doc_id, data in files_data.items():
        concepts = data.get('concepts', [])
        if concept in concepts:
            matches.append(doc_id)
    return matches


def query_stale(files_data: dict, days: int) -> list:
    """Find documents not updated in N days.
    
    Uses git history for accurate dates (from Gemini feedback).
    """
    stale = []
    today = datetime.now()
    
    for doc_id, data in files_data.items():
        filepath = data.get('filepath', '')
        
        # Try git first (from Gemini feedback)
        last_modified = get_git_last_modified(filepath)
        
        if last_modified is None:
            # Fallback: try filename date for logs
            filename = data.get('filename', '')
            if len(filename) >= 10 and filename[4] == '-':
                try:
                    last_modified = datetime.strptime(filename[:10], '%Y-%m-%d')
                except ValueError:
                    pass
        
        if last_modified is None:
            # Final fallback: file mtime (least reliable)
            if os.path.exists(filepath):
                last_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
        
        if last_modified:
            # Handle timezone-aware vs naive datetime
            if last_modified.tzinfo is not None:
                last_modified = last_modified.replace(tzinfo=None)
            age = (today - last_modified).days
            if age > days:
                stale.append((doc_id, age))
    
    return sorted(stale, key=lambda x: -x[1])


def query_health(files_data: dict) -> dict:
    """Calculate graph health metrics."""
    depends_on_graph, depended_by = build_graph(files_data)
    
    # Count by type
    by_type = defaultdict(int)
    for doc_id, data in files_data.items():
        by_type[data.get('type', 'unknown')] += 1
    
    # Orphans
    orphans = []
    for doc_id, data in files_data.items():
        if doc_id not in depended_by:
            if data.get('type') not in ['kernel', 'strategy', 'product', 'log']:
                orphans.append(doc_id)
    
    # Logs with empty impacts
    empty_impacts = []
    for doc_id, data in files_data.items():
        if data.get('type') == 'log':
            if not data.get('impacts'):
                empty_impacts.append(doc_id)
    
    # Connectivity from kernel
    kernels = [d for d, data in files_data.items() if data.get('type') == 'kernel']
    reachable = set()
    
    def traverse(node):
        if node in reachable:
            return
        reachable.add(node)
        for child in depended_by.get(node, []):
            traverse(child)
    
    for k in kernels:
        traverse(k)
    
    connectivity = len(reachable) / len(files_data) * 100 if files_data else 0
    
    return {
        'total_docs': len(files_data),
        'by_type': dict(by_type),
        'orphans': len(orphans),
        'orphan_ids': orphans[:5],
        'empty_impacts': len(empty_impacts),
        'empty_impact_ids': empty_impacts[:5],
        'connectivity': connectivity,
        'reachable_from_kernel': len(reachable),
    }


def format_health(health: dict) -> str:
    """Format health metrics for display."""
    lines = [
        "📊 Graph Health Report",
        "=" * 40,
        f"Total documents: {health['total_docs']}",
        "",
        "By type:",
    ]
    
    for t, count in sorted(health['by_type'].items()):
        lines.append(f"  {t}: {count}")
    
    lines.extend([
        "",
        f"Connectivity: {health['connectivity']:.1f}% reachable from kernel",
        f"Orphans: {health['orphans']}",
    ])
    
    if health['orphan_ids']:
        lines.append(f"  → {', '.join(health['orphan_ids'])}")
    
    lines.append(f"Logs with empty impacts: {health['empty_impacts']}")
    
    if health['empty_impact_ids']:
        lines.append(f"  → {', '.join(health['empty_impact_ids'])}")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Query the Ontos knowledge graph.',
        epilog="""
Examples:
  ontos_query.py --depends-on auth_flow     # What does auth_flow depend on?
  ontos_query.py --depended-by mission      # What depends on mission?
  ontos_query.py --concept auth             # All docs tagged with 'auth'
  ontos_query.py --stale 90                 # Docs not updated in 90 days
  ontos_query.py --health                   # Graph health metrics
  ontos_query.py --list-ids                 # List all document IDs
"""
    )
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--depends-on', metavar='ID',
                       help='What does this document depend on?')
    group.add_argument('--depended-by', metavar='ID',
                       help='What documents depend on this one?')
    group.add_argument('--concept', metavar='TAG',
                       help='Find all documents with this concept')
    group.add_argument('--stale', metavar='DAYS', type=int,
                       help='Find documents not updated in N days')
    group.add_argument('--health', action='store_true',
                       help='Show graph health metrics')
    group.add_argument('--list-ids', action='store_true',
                       help='List all document IDs')
    
    parser.add_argument('--dir', type=str, default=DOCS_DIR,
                        help=f'Documentation directory (default: {DOCS_DIR})')
    
    args = parser.parse_args()
    
    # v2.8.4: Add OutputHandler for consistency
    output = OutputHandler()
    
    files_data = scan_docs_for_query(args.dir)
    
    if not files_data:
        output.error(f"No documents found in {args.dir}")
        sys.exit(1)
    
    if args.depends_on:
        results = query_depends_on(files_data, args.depends_on)
        if results:
            output.info(f"{args.depends_on} depends on:")
            for r in results:
                output.detail(f"→ {r}")
        else:
            output.warning(f"{args.depends_on} has no dependencies (or doesn't exist)")
    
    elif args.depended_by:
        results = query_depended_by(files_data, args.depended_by)
        if results:
            output.info(f"Documents that depend on {args.depended_by}:")
            for r in results:
                output.detail(f"← {r}")
        else:
            output.warning(f"Nothing depends on {args.depended_by}")
    
    elif args.concept:
        results = query_concept(files_data, args.concept)
        if results:
            output.info(f"Documents with concept '{args.concept}':")
            for r in results:
                output.detail(f"• {r}")
        else:
            output.warning(f"No documents tagged with '{args.concept}'")
    
    elif args.stale is not None:
        results = query_stale(files_data, args.stale)
        if results:
            output.info(f"Documents not updated in {args.stale}+ days:")
            for doc_id, age in results:
                output.detail(f"• {doc_id} ({age} days)")
        else:
            output.success(f"All documents updated within {args.stale} days")
    
    elif args.health:
        health = query_health(files_data)
        output.plain(format_health(health))
    
    elif args.list_ids:
        output.info("Document IDs:")
        for doc_id in sorted(files_data.keys()):
            doc_type = files_data[doc_id].get('type', '?')
            output.detail(f"{doc_id} ({doc_type})")


def emit_deprecation_notice(message: str) -> None:
    """Always-visible CLI notice for deprecated usage."""
    import sys
    print(f"[DEPRECATION] {message}", file=sys.stderr)


if __name__ == "__main__":
    import os
    from pathlib import Path
    if not os.environ.get('ONTOS_CLI_DISPATCH'):
        if not os.environ.get('ONTOS_NO_DEPRECATION_WARNINGS'):
            emit_deprecation_notice(
                f"Direct execution of {Path(__file__).name} is deprecated. "
                "Use 'python3 ontos.py query' instead. "
                "Direct script execution will be removed in v3.0."
            )
    main()
