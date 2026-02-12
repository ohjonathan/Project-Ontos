"""Native query command implementation."""

import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from ontos.core.types import DocumentData, DocumentType
from ontos.core.graph import build_graph as core_build_graph, detect_cycles
from ontos.core.config import get_git_last_modified
from ontos.io.git import get_file_mtime as git_mtime_provider
from ontos.io.config import load_project_config
from ontos.io.files import find_project_root, load_documents, DocumentLoadResult
from ontos.io.scan_scope import collect_scoped_documents, resolve_scan_scope
from ontos.io.yaml import parse_frontmatter_content
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
    scope: Optional[str] = None
    runtime_data: Dict[str, Any] = field(default_factory=dict)


def scan_docs_for_query(root: Path, scope: Optional[str], explicit_dirs: Optional[List[Path]] = None) -> DocumentLoadResult:
    """Scan documentation files for query operations using canonical loader."""
    from ontos.core.curation import load_ontosignore

    config = load_project_config(repo_root=root)
    effective_scope = resolve_scan_scope(scope, config.scanning.default_scope)
    ignore_patterns = load_ontosignore(root)
    files = collect_scoped_documents(
        root,
        config,
        effective_scope,
        base_skip_patterns=ignore_patterns,
        explicit_dirs=explicit_dirs,
    )

    return load_documents(files, parse_frontmatter_content)


# Local build_graph removed in favor of ontos.core.graph.build_graph


def query_stale(files_data: Dict[str, DocumentData], days: int) -> List[Tuple[str, int]]:
    """Find documents not updated in N days."""
    stale = []
    today = datetime.now()
    
    for doc_id, doc in files_data.items():
        filepath = str(doc.filepath)
        last_modified = get_git_last_modified(filepath, git_mtime_provider=git_mtime_provider)
        
        if last_modified is None:
            # Fallback: filename date for logs
            filename = doc.filepath.name
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


def query_health(files_data: Dict[str, DocumentData]) -> dict:
    """Calculate graph health metrics using core graph primitives."""
    graph, _ = core_build_graph(files_data)
    cycles = detect_cycles(graph)
    
    by_type = defaultdict(int)
    for doc in files_data.values():
        doc_type = doc.type.value
        by_type[doc_type] += 1
    
    orphans = []
    allowed_orphan_types = ['kernel', 'strategy', 'product', 'log']
    for doc_id, node in graph.nodes.items():
        if node.doc_type not in allowed_orphan_types:
            if doc_id not in graph.reverse_edges or not graph.reverse_edges[doc_id]:
                orphans.append(doc_id)
    
    empty_impacts = []
    for doc_id, doc in files_data.items():
        if doc.type.value == 'log':
            if not doc.impacts:
                empty_impacts.append(doc_id)
    
    kernels = [d for d, node in graph.nodes.items() if node.doc_type == 'kernel']
    reachable = set()
    
    def traverse(node):
        if node in reachable:
            return
        reachable.add(node)
        for child in graph.reverse_edges.get(node, []):
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
        'cycles': len(cycles),
        'cycle_samples': cycles[:10],
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
        f"Cycles: {health.get('cycles', 0)}",
    ])

    if health.get('cycle_samples'):
        sample_lines = []
        for cycle in health['cycle_samples']:
            if isinstance(cycle, list):
                sample_lines.append(" -> ".join(str(node) for node in cycle))
            else:
                sample_lines.append(str(cycle))
        lines.append(f"  → {'; '.join(sample_lines)}")
    
    if health['orphan_ids']:
        lines.append(f"  → {', '.join(health['orphan_ids'])}")
    
    lines.append(f"Logs with empty impacts: {health['empty_impacts']}")
    
    if health['empty_impact_ids']:
        lines.append(f"  → {', '.join(health['empty_impact_ids'])}")
    
    return '\n'.join(lines)


def _run_query_command(options: QueryOptions) -> Tuple[int, str]:
    """Execute query command."""
    output = OutputHandler(quiet=options.quiet)
    options.runtime_data = {}
    root = find_project_root()

    explicit_dirs = [options.directory] if options.directory else None
    load_result = scan_docs_for_query(root, options.scope, explicit_dirs=explicit_dirs)
    if load_result.has_fatal_errors:
        for issue in load_result.issues:
            if issue.code in {"parse_error", "io_error"}:
                output.error(issue.message)
        return 1, "Document load failed"
        
    # Report duplicates as warnings for query
    if load_result.duplicate_ids:
        for issue in load_result.issues:
            if issue.code == "duplicate_id":
                output.warning(issue.message)
        
    files_data = load_result.documents
    if not files_data:
        if options.directory:
            output.error(f"No documents found in {options.directory}")
        else:
            output.error("No documents found in selected scope")
        return 1, "No documents found"

    if options.depends_on:
        doc = files_data.get(options.depends_on)
        results = doc.depends_on if doc else []
        options.runtime_data = {"depends_on": options.depends_on, "results": results}
        if results:
            output.info(f"{options.depends_on} depends on:")
            for r in results:
                output.detail(f"→ {r}")
        else:
            output.warning(f"{options.depends_on} has no dependencies (or doesn't exist)")
            
    elif options.depended_by:
        graph, _ = core_build_graph(files_data)
        results = graph.reverse_edges.get(options.depended_by, [])
        options.runtime_data = {"depended_by": options.depended_by, "results": results}
        if results:
            output.info(f"Documents that depend on {options.depended_by}:")
            for r in results:
                output.detail(f"← {r}")
        else:
            output.warning(f"Nothing depends on {options.depended_by}")
            
    elif options.concept:
        results = [doc_id for doc_id, doc in files_data.items() if options.concept in doc.frontmatter.get('concepts', [])]
        options.runtime_data = {"concept": options.concept, "results": results}
        if results:
            output.info(f"Documents with concept '{options.concept}':")
            for r in results:
                output.detail(f"• {r}")
        else:
            output.warning(f"No documents tagged with '{options.concept}'")
            
    elif options.stale is not None:
        results = query_stale(files_data, options.stale)
        options.runtime_data = {
            "stale_days": options.stale,
            "results": [{"id": doc_id, "age_days": age} for doc_id, age in results],
        }
        if results:
            output.info(f"Documents not updated in {options.stale}+ days:")
            for doc_id, age in results:
                output.detail(f"• {doc_id} ({age} days)")
        else:
            output.success(f"All documents updated within {options.stale} days")
            
    elif options.health:
        health = query_health(files_data)
        options.runtime_data = health
        output.plain(format_health(health))
        
    elif options.list_ids:
        options.runtime_data = {"ids": sorted(files_data.keys())}
        output.info("Document IDs:")
        for doc_id in sorted(files_data.keys()):
            doc = files_data[doc_id]
            doc_type = doc.type.value
            output.detail(f"{doc_id} ({doc_type})")
            
    return 0, "Query complete"


def query_command(options: QueryOptions) -> int:
    """Run query command and return exit code only."""
    exit_code, _ = _run_query_command(options)
    return exit_code
