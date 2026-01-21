"""Native query command implementation."""

import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from ontos.core.frontmatter import parse_frontmatter, normalize_depends_on, normalize_type
from ontos.core.config import get_git_last_modified
from ontos.io.git import get_file_mtime as git_mtime_provider
from ontos.io.files import find_project_root, scan_documents
from ontos.ui.output import OutputHandler


@dataclass
class QueryOptions:
    """Options for query command."""
    depends_on: Optional[str] = None
    depended_by: Optional[str] = None
    concept: Optional[str] = None
    stale: Optional[int] = None
    health: bool = False
    list_ids: bool = False
    directory: Optional[Path] = None
    quiet: bool = False
    json_output: bool = False


def scan_docs_for_query(root: Path) -> Dict[str, dict]:
    """Scan documentation files for query operations."""
    from ontos.core.curation import load_ontosignore
    
    ignore_patterns = load_ontosignore(root)
    files = scan_documents([root], skip_patterns=ignore_patterns)
    
    files_data = {}
    for f in files:
        try:
            fm = parse_frontmatter(str(f))
            if fm and fm.get('id'):
                doc_id = str(fm['id']).strip()
                files_data[doc_id] = {
                    'filepath': str(f),
                    'filename': f.name,
                    'type': normalize_type(fm.get('type')),
                    'depends_on': normalize_depends_on(fm.get('depends_on')),
                    'status': str(fm.get('status') or 'unknown').strip(),
                    'concepts': fm.get('concepts', []),
                    'impacts': fm.get('impacts', []),
                }
        except Exception:
            continue
    return files_data


def build_graph(files_data: Dict[str, dict]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Build adjacency and reverse adjacency lists."""
    depends_on = defaultdict(list)
    depended_by = defaultdict(list)
    
    for doc_id, data in files_data.items():
        deps = data.get('depends_on', [])
        for dep in deps:
            depends_on[doc_id].append(dep)
            depended_by[dep].append(doc_id)
    
    return dict(depends_on), dict(depended_by)


def query_stale(files_data: Dict[str, dict], days: int) -> List[Tuple[str, int]]:
    """Find documents not updated in N days."""
    stale = []
    today = datetime.now()
    
    for doc_id, data in files_data.items():
        filepath = data.get('filepath', '')
        last_modified = get_git_last_modified(filepath, git_mtime_provider=git_mtime_provider)
        
        if last_modified is None:
            # Fallback: filename date for logs
            filename = data.get('filename', '')
            if len(filename) >= 10 and filename[4] == '-':
                try:
                    last_modified = datetime.strptime(filename[:10], '%Y-%m-%d')
                except ValueError:
                    pass
        
        if last_modified is None:
            # Final fallback: mtime
            if os.path.exists(filepath):
                last_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
        
        if last_modified:
            if last_modified.tzinfo is not None:
                last_modified = last_modified.replace(tzinfo=None)
            age = (today - last_modified).days
            if age > days:
                stale.append((doc_id, age))
    
    return sorted(stale, key=lambda x: -x[1])


def query_health(files_data: Dict[str, dict]) -> dict:
    """Calculate graph health metrics."""
    depends_on_graph, depended_by = build_graph(files_data)
    
    by_type = defaultdict(int)
    for doc_id, data in files_data.items():
        by_type[data.get('type', 'unknown')] += 1
    
    orphans = []
    for doc_id, data in files_data.items():
        if doc_id not in depended_by:
            if data.get('type') not in ['kernel', 'strategy', 'product', 'log']:
                orphans.append(doc_id)
    
    empty_impacts = []
    for doc_id, data in files_data.items():
        if data.get('type') == 'log':
            if not data.get('impacts'):
                empty_impacts.append(doc_id)
    
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


def query_command(options: QueryOptions) -> Tuple[int, str]:
    """Execute query command."""
    output = OutputHandler(quiet=options.quiet)
    root = find_project_root()
    search_dir = options.directory if options.directory else root
    
    files_data = scan_docs_for_query(search_dir)
    if not files_data:
        output.error(f"No documents found in {search_dir}")
        return 1, "No documents found"

    if options.depends_on:
        results = files_data.get(options.depends_on, {}).get('depends_on', [])
        if results:
            output.info(f"{options.depends_on} depends on:")
            for r in results:
                output.detail(f"→ {r}")
        else:
            output.warning(f"{options.depends_on} has no dependencies (or doesn't exist)")
            
    elif options.depended_by:
        _, depended_by = build_graph(files_data)
        results = depended_by.get(options.depended_by, [])
        if results:
            output.info(f"Documents that depend on {options.depended_by}:")
            for r in results:
                output.detail(f"← {r}")
        else:
            output.warning(f"Nothing depends on {options.depended_by}")
            
    elif options.concept:
        results = [doc_id for doc_id, data in files_data.items() if options.concept in data.get('concepts', [])]
        if results:
            output.info(f"Documents with concept '{options.concept}':")
            for r in results:
                output.detail(f"• {r}")
        else:
            output.warning(f"No documents tagged with '{options.concept}'")
            
    elif options.stale is not None:
        results = query_stale(files_data, options.stale)
        if results:
            output.info(f"Documents not updated in {options.stale}+ days:")
            for doc_id, age in results:
                output.detail(f"• {doc_id} ({age} days)")
        else:
            output.success(f"All documents updated within {options.stale} days")
            
    elif options.health:
        health = query_health(files_data)
        output.plain(format_health(health))
        
    elif options.list_ids:
        output.info("Document IDs:")
        for doc_id in sorted(files_data.keys()):
            doc_type = files_data[doc_id].get('type', '?')
            output.detail(f"{doc_id} ({doc_type})")
            
    return 0, "Query complete"
