"""Generate Ontos Context Map from documentation files."""

import os
import sys
import time
import re
import yaml
import datetime
import argparse
from typing import Optional

from ontos_config import (
    __version__,
    DOCS_DIR,
    CONTEXT_MAP_FILE,
    TYPE_HIERARCHY,
    MAX_DEPENDENCY_DEPTH,
    ALLOWED_ORPHAN_TYPES,
    SKIP_PATTERNS,
    is_ontos_repo
)

from ontos_lib import (
    parse_frontmatter,
    normalize_depends_on,
    normalize_type,
    load_common_concepts,
    resolve_config,
    get_logs_dir,
    get_log_count,
    get_logs_older_than,
    get_git_last_modified,
    load_decision_history_entries,
    get_decision_history_path,
)

from ontos_config_defaults import (
    VALID_STATUS,
    VALID_TYPE_STATUS,
    PROPOSAL_STALE_DAYS,
    REJECTED_REASON_MIN_LENGTH,
    PROJECT_ROOT,
)

OUTPUT_FILE = CONTEXT_MAP_FILE


def estimate_tokens(content: str) -> int:
    """Estimate token count using character-based heuristic.
    
    Formula: tokens ≈ characters / 4
    
    This is a rough approximation that works well for English text.
    More accurate than word count, simpler than actual tokenization.
    
    Args:
        content: File content as string.
        
    Returns:
        Estimated token count.
    """
    return len(content) // 4


def format_token_count(tokens: int) -> str:
    """Format token count for display.
    
    Args:
        tokens: Token count.
        
    Returns:
        Formatted string (e.g., "~450 tokens" or "~2,100 tokens").
    """
    if tokens < 1000:
        return f"~{tokens} tokens"
    else:
        # Round to nearest 100 for larger counts
        rounded = (tokens // 100) * 100
        return f"~{rounded:,} tokens"



def lint_data_quality(files_data: dict[str, dict], common_concepts: set[str]) -> list[str]:
    """Check for data quality issues that don't break validation but hurt v3.0.
    
    Checks:
    1. Empty impacts on active logs
    2. Unknown concepts not in vocabulary
    3. Excessive concepts per log (>6)
    4. Stale logs (>30 days)
    5. Too many active logs (exceeds LOG_RETENTION_COUNT)
    """
    from datetime import datetime
    
    try:
        from ontos_config import LOG_RETENTION_COUNT
    except ImportError:
        LOG_RETENTION_COUNT = 15
    
    warnings = []
    active_logs = []
    
    for doc_id, data in files_data.items():
        if data['type'] != 'log':
            continue
        
        filepath = data['filepath']
        is_active = data.get('status') != 'archived'
        
        if is_active:
            active_logs.append((doc_id, data))
        
        # Check 1: Empty impacts on active logs
        if is_active:
            impacts = data.get('impacts', [])
            if not impacts:
                warnings.append(
                    f"- [LINT] **{doc_id}** ({filepath}): Empty impacts\n"
                    f"  → Creates dead end in knowledge graph. Add impacted document IDs."
                )
        
        # Check 1b (v2.4): Auto-generated logs need enrichment
        if data.get('status') == 'auto-generated':
            warnings.append(
                f"- [LINT] **{doc_id}** ({filepath}): Auto-generated log needs enrichment\n"
                f"  → Run `python3 .ontos/scripts/ontos_end_session.py --enhance` to add context"
            )
        
        # Check 2: Unknown concepts
        if common_concepts:
            concepts = data.get('concepts', [])
            for concept in concepts:
                if concept and concept not in common_concepts:
                    warnings.append(
                        f"- [LINT] **{doc_id}**: Unknown concept `{concept}`\n"
                        f"  → Check `Common_Concepts.md`. Did you mean a standard term?"
                    )
        
        # Check 3: Too many concepts
        concepts = data.get('concepts', [])
        if len(concepts) > 6:
            warnings.append(
                f"- [LINT] **{doc_id}**: {len(concepts)} concepts (recommended: 2-4)\n"
                f"  → Too many concepts dilutes graph connectivity. Be specific."
            )
    
    # Check 4: Stale logs
    threshold_days = 30
    today = datetime.now()
    
    for doc_id, data in active_logs:
        filename = data['filename']
        if len(filename) >= 10:
            try:
                log_date = datetime.strptime(filename[:10], '%Y-%m-%d')
                age_days = (today - log_date).days
                if age_days > threshold_days:
                    warnings.append(
                        f"- [LINT] **{doc_id}**: {age_days} days old (threshold: {threshold_days})\n"
                        f"  → Consider consolidating and archiving. See Manual section 3."
                    )
            except ValueError:
                pass
    
    # Check 5: Too many active logs
    active_count = len(active_logs)
    if active_count > LOG_RETENTION_COUNT:
        excess = active_count - LOG_RETENTION_COUNT
        warnings.insert(0,
            f"- [LINT] **Active log count ({active_count}) exceeds threshold ({LOG_RETENTION_COUNT})**\n"
            f"  → {excess} logs over limit. Run consolidation ritual to archive oldest logs.\n"
            f"  → This directly impacts context window size. See Manual section 3."
        )
    
    return warnings


def scan_docs(root_dirs: list[str]) -> dict[str, dict]:
    """Scans directories for markdown files and parses their metadata.

    Args:
        root_dirs: List of directories to scan.

    Returns:
        Dictionary mapping doc IDs to their metadata.
    """
    files_data = {}
    for root_dir in root_dirs:
        if not os.path.isdir(root_dir):
            print(f"Warning: Directory not found: {root_dir}")
            continue
        for subdir, dirs, files in os.walk(root_dir):
            # Prune directories matching skip patterns (e.g., 'archive/')
            dirs[:] = [d for d in dirs if not any(pattern.rstrip('/') == d for pattern in SKIP_PATTERNS)]

            for file in files:
                if file.endswith('.md'):
                    # Skip files matching skip patterns (e.g., Ontos_ tooling files)
                    if any(pattern in file for pattern in SKIP_PATTERNS):
                        continue
                    filepath = os.path.join(subdir, file)
                    
                    # Read full content for token estimation
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                            full_content = f.read()
                    except Exception:
                        full_content = ""

                    frontmatter = parse_frontmatter(filepath)
                    if frontmatter and 'id' in frontmatter:
                        doc_id = frontmatter['id']
                        # Skip if ID is None or empty
                        if not doc_id or not str(doc_id).strip():
                            continue
                        doc_id = str(doc_id).strip()
                        # Skip internal/template documents (IDs starting with underscore)
                        if doc_id.startswith('_'):
                            continue

                        # Normalize fields to handle YAML null/empty values
                        doc_type = normalize_type(frontmatter.get('type'))
                        
                        # Deliverable 5: Auto-Normalization of v1.x Logs
                        # Treat legacy logs (type: atom, id: log_*) as v2.0 logs (type: log)
                        if doc_id.startswith('log_') and doc_type == 'atom':
                            doc_type = 'log'
                        
                        files_data[doc_id] = {
                            'filepath': filepath,
                            'filename': file,
                            'type': doc_type,
                            'depends_on': normalize_depends_on(frontmatter.get('depends_on')),
                            'status': str(frontmatter.get('status') or 'unknown').strip() or 'unknown',
                            # NEW v2.0 fields for logs
                            'event_type': frontmatter.get('event_type'),
                            'concepts': frontmatter.get('concepts', []),
                            'impacts': frontmatter.get('impacts', []),
                            'tokens': estimate_tokens(full_content),  # NEW v2.1
                            # NEW v2.6 fields for rejection metadata
                            'rejected_reason': frontmatter.get('rejected_reason', ''),
                            'rejected_date': frontmatter.get('rejected_date', ''),
                            'rejected_by': frontmatter.get('rejected_by', ''),
                            'revisit_when': frontmatter.get('revisit_when', ''),
                        }
    return files_data


def generate_tree(files_data: dict[str, dict]) -> str:
    """Generates a hierarchy tree string.

    Args:
        files_data: Dictionary of document metadata (already normalized).

    Returns:
        Formatted tree string.
    """
    tree = []

    # Group by type (data is already normalized by scan_docs)
    by_type = {'kernel': [], 'strategy': [], 'product': [], 'atom': [], 'log': [], 'unknown': []}
    for doc_id, data in files_data.items():
        doc_type = data['type']
        if doc_type in by_type:
            by_type[doc_type].append(doc_id)
        else:
            by_type['unknown'].append(doc_id)

    order = ['kernel', 'strategy', 'product', 'atom', 'log', 'unknown']

    for doc_type in order:
        if by_type[doc_type]:
            tree.append(f"### {doc_type.upper()}")
            for doc_id in sorted(by_type[doc_type]):
                data = files_data[doc_id]
                deps = ", ".join(data['depends_on']) if data['depends_on'] else "None"
                tokens = format_token_count(data.get('tokens', 0))
                status_indicator = get_status_indicator(data.get('status', 'unknown'))
                
                tree.append(f"- **{doc_id}**{status_indicator} ({data['filename']}) {tokens}")
                tree.append(f"  - Status: {data['status']}")
                if data['type'] != 'log':
                    tree.append(f"  - Depends On: {deps}")
                else:
                    impacts = ", ".join(data.get('impacts', [])) or "None"
                    tree.append(f"  - Impacts: {impacts}")
            tree.append("")

    return "\n".join(tree)


def generate_timeline(files_data: dict[str, dict], max_entries: int = 10) -> str:
    """Generate the Recent Timeline section from log documents.
    
    Args:
        files_data: Dictionary of document metadata.
        max_entries: Maximum number of timeline entries to show.
        
    Returns:
        Formatted timeline string.
    """
    # Extract log documents
    logs = [
        (doc_id, data) for doc_id, data in files_data.items()
        if data['type'] == 'log'
    ]
    
    if not logs:
        return "No session logs found."
    
    # Sort by filename (which starts with date) in reverse order
    logs.sort(key=lambda x: x[1]['filename'], reverse=True)
    
    # Take most recent entries
    recent_logs = logs[:max_entries]
    
    lines = []
    for doc_id, data in recent_logs:
        filename = data['filename']
        event_type = data.get('event_type', 'chore')
        impacts = data.get('impacts', [])
        concepts = data.get('concepts', [])
        
        # Extract date from filename (format: YYYY-MM-DD_slug.md)
        date_part = filename[:10] if len(filename) >= 10 else filename
        
        # Extract title from slug
        slug = filename[11:-3] if len(filename) > 14 else filename[:-3]
        title = slug.replace('-', ' ').replace('_', ' ').title()
        
        # Format line
        line = f"- **{date_part}** [{event_type}] **{title}** (`{doc_id}`)"
        
        if impacts:
            line += f"\n  - Impacted: {', '.join(f'`{i}`' for i in impacts)}"
        
        if concepts:
            line += f"\n  - Concepts: {', '.join(concepts)}"
        
        lines.append(line)
    
    if len(logs) > max_entries:
        lines.append(f"\n*Showing {max_entries} of {len(logs)} sessions*")
    
    return "\n".join(lines)


def generate_provenance_header() -> str:
    """Generate metadata header for the context map.
    
    The provenance header provides audit information:
    - Mode: Contributor or User
    - Root: Which directory was scanned
    - Timestamp: When the map was generated (UTC)
    
    Returns:
        HTML comment string with provenance info.
    """
    from ontos_config import DOCS_DIR, PROJECT_ROOT, is_ontos_repo
    
    mode = "Contributor" if is_ontos_repo() else "User"
    
    # Make root path relative
    try:
        scanned_dir = os.path.relpath(DOCS_DIR, PROJECT_ROOT)
    except ValueError:
        scanned_dir = DOCS_DIR
        
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    header = f"""<!--
Ontos Context Map
Generated: {timestamp}
Mode: {mode}
Scanned: {scanned_dir}
-->"""

    # Add notice for Project Ontos repo (serves as example for users)
    if is_ontos_repo():
        header += """
> **Note for users:** This context map documents Project Ontos's own development.
> When you run `python3 ontos_init.py` or `python3 .ontos/scripts/ontos_generate_context_map.py`
> in your project, this file will be overwritten with your project's context.
"""

    return header



def validate_dependencies(files_data: dict[str, dict]) -> list[str]:
    """Checks for broken links, cycles, orphans, depth, and type violations.

    Args:
        files_data: Dictionary of document metadata.

    Returns:
        List of issue strings.
    """
    issues = []
    existing_ids = set(files_data.keys())

    # 1. Build Adjacency List & Reverse Graph
    adj: dict[str, list[str]] = {doc_id: [] for doc_id in existing_ids}
    rev_adj: dict[str, list[str]] = {doc_id: [] for doc_id in existing_ids}

    for doc_id, data in files_data.items():
        # Normalize depends_on in case it wasn't processed by scan_docs
        deps = normalize_depends_on(data.get('depends_on'))
        for dep in deps:
            if dep not in existing_ids:
                issues.append(
                    f"- [BROKEN LINK] **{doc_id}** ({data['filepath']}) references missing ID: `{dep}`\n"
                    f"  Fix: Add a document with `id: {dep}` or remove it from depends_on"
                )
            else:
                adj[doc_id].append(dep)
                rev_adj[dep].append(doc_id)

    # 2. Cycle Detection (DFS)
    visited: set[str] = set()
    recursion_stack: set[str] = set()

    def detect_cycle(node: str, path: list[str]) -> bool:
        visited.add(node)
        recursion_stack.add(node)
        path.append(node)

        for neighbor in adj[node]:
            if neighbor not in visited:
                if detect_cycle(neighbor, path):
                    return True
            elif neighbor in recursion_stack:
                cycle_path = " -> ".join(path[path.index(neighbor):] + [neighbor])
                issues.append(
                    f"- [CYCLE] Circular dependency: {cycle_path}\n"
                    f"  Fix: Remove one of the depends_on links to break the cycle"
                )
                return True

        recursion_stack.remove(node)
        path.pop()
        return False

    for doc_id in existing_ids:
        if doc_id not in visited:
            detect_cycle(doc_id, [])

    # 3. Orphan Detection
    for doc_id in existing_ids:
        if not rev_adj[doc_id]:
            doc_type = files_data[doc_id]['type']
            filename = files_data[doc_id]['filename']
            filepath = files_data[doc_id]['filepath']
            status = files_data[doc_id].get('status', 'unknown')

            if doc_type in ALLOWED_ORPHAN_TYPES:
                continue
            if any(pattern in filename for pattern in SKIP_PATTERNS):
                continue
            if '/logs/' in filepath or '\\logs\\' in filepath:
                continue
            
            # v2.6: Skip draft proposals - they're naturally orphans until approved
            if status == 'draft' and 'proposals/' in filepath:
                continue

            issues.append(
                f"- [ORPHAN] **{doc_id}** ({filepath}) has no dependents\n"
                f"  Fix: Add `{doc_id}` to another document's depends_on, or delete if unused"
            )

    # 4. Dependency Depth
    memo_depth: dict[str, int] = {}

    def get_depth(node: str) -> int:
        if node in memo_depth:
            return memo_depth[node]
        if not adj[node]:
            return 0

        memo_depth[node] = 0  # Prevent infinite recursion in cycles

        max_d = 0
        for neighbor in adj[node]:
            max_d = max(max_d, get_depth(neighbor))

        memo_depth[node] = 1 + max_d
        return memo_depth[node]

    for doc_id in existing_ids:
        depth = get_depth(doc_id)
        if depth > MAX_DEPENDENCY_DEPTH:
            issues.append(
                f"- [DEPTH] **{doc_id}** has dependency depth {depth} (max: {MAX_DEPENDENCY_DEPTH})\n"
                f"  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py"
            )

    # 5. Type Hierarchy Violations
    type_rank = TYPE_HIERARCHY

    for doc_id, data in files_data.items():
        my_type = normalize_type(data.get('type'))
        my_rank = type_rank.get(my_type, 4)

        # Normalize depends_on in case it wasn't processed by scan_docs
        deps = normalize_depends_on(data.get('depends_on'))
        for dep in deps:
            if dep in files_data:
                dep_type = files_data[dep]['type']
                dep_rank = type_rank.get(dep_type, 4)

                if my_rank < dep_rank:
                    issues.append(
                        f"- [ARCHITECTURE] **{doc_id}** ({my_type}) depends on **{dep}** ({dep_type})\n"
                        f"  Fix: {my_type} should not depend on {dep_type}. Invert the dependency or change document types"
                    )

    return issues



def validate_log_schema(files_data: dict[str, dict]) -> list[str]:
    """Validate log-type documents have required v2.0 fields.
    
    Rules:
    1. Logs MUST have event_type field
    2. event_type MUST be one of: feature, fix, refactor, exploration, chore
    3. Logs MUST have impacts field (can be empty list)
    4. Logs SHOULD NOT have depends_on (warning, not error)
    
    Args:
        files_data: Dictionary of document metadata.
        
    Returns:
        List of issue strings.
    """
    from ontos_config import VALID_EVENT_TYPES, TYPE_DEFINITIONS
    
    issues = []
    
    for doc_id, data in files_data.items():
        if data['type'] != 'log':
            continue
            
        filepath = data['filepath']
        
        # Rule 1: event_type is required
        event_type = data.get('event_type')
        if event_type is None:
            issues.append(
                f"- [MISSING FIELD] **{doc_id}** ({filepath}) is type 'log' but missing required field: event_type\n"
                f"  Fix: Add `event_type: feature|fix|refactor|exploration|chore` to frontmatter"
            )
        # Rule 2: event_type must be valid
        elif event_type not in VALID_EVENT_TYPES:
            issues.append(
                f"- [INVALID VALUE] **{doc_id}** ({filepath}) has invalid event_type: '{event_type}'\n"
                f"  Fix: Use one of: {', '.join(sorted(VALID_EVENT_TYPES))}"
            )
        
        # Rule 3: impacts is required (empty list is OK)
        if 'impacts' not in data:
            issues.append(
                f"- [MISSING FIELD] **{doc_id}** ({filepath}) is type 'log' but missing required field: impacts\n"
                f"  Fix: Add `impacts: []` or `impacts: [doc_id1, doc_id2]` to frontmatter"
            )
        
        # Rule 4: depends_on should not be used (check config for allows_depends_on)
        type_config = TYPE_DEFINITIONS.get('log', {})
        if not type_config.get('allows_depends_on', True):
            if data.get('depends_on') and len(data['depends_on']) > 0:
                issues.append(
                    f"- [WARNING] **{doc_id}** ({filepath}) is type 'log' but has depends_on field\n"
                    f"  Fix: Logs should use `impacts` instead of `depends_on`. Remove depends_on."
                )
    
    return issues


def validate_impacts(files_data: dict[str, dict]) -> list[str]:
    """Validate that impacts[] references exist in Space Ontology.

    The impacts field connects History (logs) to Truth (space documents).

    Validation Rules:
    - Active logs: impacts MUST reference existing Space documents (ERROR)
    - Archived logs: broken references are noted but not errors (INFO)

    Rationale: History is immutable. If a Space document is deleted,
    historical logs that referenced it shouldn't turn red. The log
    recorded what was true at that moment.

    Args:
        files_data: Dictionary of document metadata.

    Returns:
        List of issue strings.
    """
    issues = []
    
    # Build set of Space document IDs (everything except logs)
    space_ids = {
        doc_id for doc_id, data in files_data.items()
        if data['type'] != 'log'
    }
    
    for doc_id, data in files_data.items():
        if data['type'] != 'log':
            continue
        
        # Check if this log is archived (historical)
        is_archived = data.get('status') == 'archived'
        
        impacts = data.get('impacts', [])
        if not isinstance(impacts, list):
            impacts = [impacts] if impacts else []
        
        for impact_id in impacts:
            # Check if impact references another log (not allowed)
            if impact_id.startswith('log_'):
                issues.append(
                    f"- [INVALID REFERENCE] **{doc_id}** ({data['filepath']}) "
                    f"impacts references another log: `{impact_id}`\n"
                    f"  Fix: impacts should reference Space documents, not other logs"
                )
                continue
            
            if impact_id not in space_ids:
                if is_archived:
                    # =========================================================
                    # ARCHIVED LOGS: Informational only (even in strict mode)
                    # History is immutable—don't error on deleted references
                    # The log recorded what was true at that moment.
                    # =========================================================
                    issues.append(
                        f"- [INFO] **{doc_id}** references deleted document `{impact_id}` "
                        f"(archived log, no action needed)"
                    )
                else:
                    # =========================================================
                    # ACTIVE LOGS: This is a real problem
                    # Either the reference is wrong or the doc needs to exist
                    # =========================================================
                    issues.append(
                        f"- [BROKEN LINK] **{doc_id}** ({data['filepath']}) "
                        f"impacts non-existent document: `{impact_id}`\n"
                        f"  Fix: Create `{impact_id}`, correct the reference, or archive this log"
                    )
    
    return issues


def validate_v26_status(files_data: dict[str, dict]) -> tuple[list[str], list[str]]:
    """Validate v2.6 status rules: type-status matrix, proposals, rejections.
    
    Returns:
        Tuple of (errors, warnings) - errors are blocking, warnings are advisory
    """
    from datetime import datetime
    
    errors = []  # Hard errors - block context map generation
    warnings = []  # Advisory warnings
    
    # Load decision history for ledger validation
    ledger = load_decision_history_entries()
    
    for doc_id, data in files_data.items():
        filepath = data['filepath']
        doc_type = normalize_type(data.get('type'))
        status = data.get('status', 'unknown')
        
        # 1. Basic status validation (unknown status = warning)
        if status not in VALID_STATUS:
            warnings.append(
                f"- [LINT] **{doc_id}**: Invalid status '{status}'. "
                f"Use one of: {', '.join(sorted(VALID_STATUS))}"
            )
        
        # 2. Type-status matrix validation (HARD ERROR)
        if doc_type in VALID_TYPE_STATUS:
            valid_statuses = VALID_TYPE_STATUS[doc_type]
            if status not in valid_statuses and status in VALID_STATUS:
                errors.append(
                    f"- [ERROR] **{doc_id}**: Invalid status '{status}' for type '{doc_type}' "
                    f"(valid: {', '.join(sorted(valid_statuses))}). "
                    f"This violates the type-status matrix."
                )
        
        # 3. Stale proposal detection (with mtime fallback)
        if status == 'draft' and 'proposals/' in filepath:
            last_modified = get_git_last_modified(filepath)
            if last_modified is None:
                try:
                    mtime = os.path.getmtime(filepath)
                    last_modified = datetime.fromtimestamp(mtime)
                except OSError:
                    last_modified = None
            
            if last_modified:
                age_days = (datetime.now() - last_modified).days
                if age_days > PROPOSAL_STALE_DAYS:
                    warnings.append(
                        f"- [LINT] **{doc_id}**: Draft proposal is {age_days} days old. "
                        f"Approve (move to strategy/) or reject (move to archive/proposals/)."
                    )
        
        # 4. Rejection metadata and location enforcement
        if status == 'rejected':
            rejected_reason = data.get('rejected_reason', '')
            
            if not rejected_reason:
                warnings.append(
                    f"- [LINT] **{doc_id}**: status: rejected requires 'rejected_reason' field."
                )
            elif len(rejected_reason) < REJECTED_REASON_MIN_LENGTH:
                warnings.append(
                    f"- [LINT] **{doc_id}**: rejected_reason too short ({len(rejected_reason)} chars, min {REJECTED_REASON_MIN_LENGTH})."
                )
            
            if not data.get('rejected_date'):
                warnings.append(
                    f"- [LINT] **{doc_id}**: Consider adding 'rejected_date' for temporal context."
                )
            
            if 'archive/proposals/' not in filepath:
                warnings.append(
                    f"- [LINT] **{doc_id}**: Rejected proposals should be in archive/proposals/."
                )
            
            # Ledger validation - deterministic matching by path or slug
            relative_path = os.path.relpath(filepath, PROJECT_ROOT)
            path_matched = relative_path in ledger['archive_paths']
            doc_slug = doc_id.replace('_', '-')
            slug_matched = doc_slug in ledger['rejected_slugs']
            
            if not path_matched and not slug_matched:
                warnings.append(
                    f"- [LINT] **{doc_id}**: Rejected proposal not in decision_history.md."
                )
        
        # 5. Approval path enforcement
        if status == 'active' and 'proposals/' in filepath:
            warnings.append(
                f"- [LINT] **{doc_id}**: Active document in proposals/. Graduate to strategy/."
            )
        
        # 6. Approval ledger symmetry (soft warning) - deterministic matching
        if status == 'active' and 'strategy/' in filepath and 'proposals/' not in filepath:
            if 'proposal' in doc_id.lower():
                doc_slug = doc_id.replace('_', '-')
                slug_matched = doc_slug in ledger['approved_slugs']
                if not slug_matched:
                    warnings.append(
                        f"- [LINT] **{doc_id}**: Graduated proposal may not be in decision_history.md."
                    )
    
    return errors, warnings


def get_status_indicator(status: str) -> str:
    """Return status indicator for non-active documents."""
    if status in ('draft', 'rejected', 'deprecated'):
        return f' [{status}]'
    return ''


def generate_context_map(target_dirs: list[str], quiet: bool = False, strict: bool = False, 
                         lint: bool = False, include_rejected: bool = False,
                         include_archived: bool = False) -> int:
    """Main function to generate the Ontos_Context_Map.md file.

    Args:
        target_dirs: List of directories to scan.
        quiet: Suppress output if True.
        include_rejected: Include rejected proposals in context map.
        include_archived: Include archived logs in context map.

    Returns:
        Number of issues found.
    """
    dirs_str = ", ".join(target_dirs)
    if not quiet:
        print(f"Scanning {dirs_str}...")
    files_data = scan_docs(target_dirs)
    
    # v2.6: Filter out rejected documents unless --include-rejected
    if not include_rejected:
        rejected_count = sum(1 for d in files_data.values() if d.get('status') == 'rejected')
        files_data = {k: v for k, v in files_data.items() if v.get('status') != 'rejected'}
        if rejected_count > 0 and not quiet:
            print(f"  (Excluding {rejected_count} rejected docs. Use --include-rejected to show.)")
    
    # v2.6.1: Filter out archived logs unless --include-archived
    if not include_archived:
        archived_count = sum(1 for v in files_data.values() 
                           if v.get('status') == 'archived' or 'archive/' in v.get('filepath', ''))
        files_data = {k: v for k, v in files_data.items() 
                     if v.get('status') != 'archived' and 'archive/' not in v.get('filepath', '')}
        if archived_count > 0 and not quiet:
            print(f"  (Excluding {archived_count} archived docs. Use --include-archived to show.)")

    if not quiet:
        print("Generating tree...")
    tree_view = generate_tree(files_data)

    if not quiet:
        print("Validating dependencies...")
    issues = validate_dependencies(files_data)

    # NEW: Validate log schema
    if not quiet:
        print("Validating log schema...")
    log_issues = validate_log_schema(files_data)
    issues.extend(log_issues)

    # NEW: Validate impacts references
    if not quiet:
        print("Validating impacts references...")
    impact_issues = validate_impacts(files_data)
    issues.extend(impact_issues)

    # v2.6: Validate status rules (type-status matrix, proposals, rejections)
    if not quiet:
        print("Validating status rules...")
    v26_errors, v26_warnings = validate_v26_status(files_data)
    
    # Hard errors block context map generation
    if v26_errors:
        if not quiet:
            print(f"\n## ERRORS (blocking)\n")
            for e in v26_errors:
                print(e)
            print("\n❌ Context map generation failed due to errors above.")
        sys.exit(1)
    
    # Warnings are added to lint output
    issues.extend(v26_warnings)

    # Lint mode
    lint_warnings = []
    if lint:
        if not quiet:
            print("Running data quality lint...")
        common_concepts = load_common_concepts()
        lint_warnings = lint_data_quality(files_data, common_concepts)

    # NEW: Generate Timeline
    timeline = generate_timeline(files_data)
    
    # NEW: Generate Provenance Header
    provenance = generate_provenance_header()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""{provenance}
# Ontos Context Map
Generated on: {timestamp}
Scanned Directory: `{dirs_str}`

## 1. Hierarchy Tree
{tree_view}

## 2. Recent Timeline
{timeline}

## 3. Dependency Audit
{'No issues found.' if not issues else chr(10).join(issues)}

## 4. Index
| ID | Filename | Type |
|---|---|---|
"""

    for doc_id, data in sorted(files_data.items()):
        content += f"| {doc_id} | [{data['filename']}]({data['filepath']}) | {data['type']} |\n"

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
    except (IOError, OSError, PermissionError) as e:
        print(f"Error: Failed to write {OUTPUT_FILE}: {e}")
        sys.exit(1)

    # Count error-level issues (exclude INFO for strict mode purposes)
    error_issues = [i for i in issues if '[INFO]' not in i]

    # Display lint warnings
    if lint_warnings and not quiet:
        print(f"\n📋 Data Quality Warnings ({len(lint_warnings)} issues):")
        for warning in lint_warnings:
            print(warning)
        print()
        print("These are soft warnings — they don't fail validation but hurt v3.0 readiness.")
    elif lint and not quiet:
        print("\n📋 Data Quality Warnings (0 issues):")
        print("No data quality warnings. Nice work!")

    if not quiet:
        print(f"Successfully generated {OUTPUT_FILE}")
        print(f"Scanned {len(files_data)} documents, found {len(issues)} issues.")
        
        if error_issues:
            print(f"\n❌ Validation Errors ({len(error_issues)} issues):")
            for issue in error_issues:
                print(issue)

    # Return only error-level issues for strict mode
    return len(error_issues)


def watch_mode(target_dirs: list[str], quiet: bool = False) -> None:
    """Watch for file changes and regenerate map.

    Args:
        target_dirs: List of directories to watch.
        quiet: Suppress output if True.
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("Error: watchdog not installed. Install with: pip install watchdog")
        print("Or add watchdog to requirements.txt")
        sys.exit(1)

    class ChangeHandler(FileSystemEventHandler):
        def __init__(self):
            self.last_run = 0
            self.debounce_seconds = 1  # Prevent rapid re-runs

        def on_any_event(self, event):
            if event.src_path.endswith('.md'):
                current_time = time.time()
                if current_time - self.last_run > self.debounce_seconds:
                    self.last_run = current_time
                    print(f"\n🔄 Change detected: {event.src_path}")
                    generate_context_map(target_dirs, quiet)

    observer = Observer()
    handler = ChangeHandler()

    for target_dir in target_dirs:
        if os.path.isdir(target_dir):
            observer.schedule(handler, target_dir, recursive=True)

    observer.start()
    dirs_str = ", ".join(target_dirs)
    print(f"👀 Watching {dirs_str} for changes... (Ctrl+C to stop)")

    # Generate initial map
    generate_context_map(target_dirs, quiet)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n✅ Watch mode stopped.")
    observer.join()


def check_consolidation_status() -> None:
    """Print warning if consolidation needed (prompted/advisory modes only).

    Called at end of context map generation to honor the "prompted" promise.
    Agents always activate (read context map) before work, so this warning
    is reliable without requiring a separate script.
    
    v2.5: This implements the "Keep me in the loop" promise for prompted mode.
    Uses shared helpers from ontos_lib for config-agnostic path resolution.
    """
    mode = resolve_config('ONTOS_MODE', 'prompted')
    if mode == 'automated':
        return  # Auto-consolidation handles this in pre-commit hook
    
    # Use shared helpers for config-agnostic paths
    log_count = get_log_count()
    threshold_count = resolve_config('LOG_RETENTION_COUNT', 15)
    
    if log_count <= threshold_count:
        return  # Count is fine
    
    # Count old logs using shared helper
    threshold_days = resolve_config('CONSOLIDATION_THRESHOLD_DAYS', 30)
    old_logs = get_logs_older_than(threshold_days)
    
    if len(old_logs) > 0:
        # Use ASCII text instead of emoji for terminal compatibility
        print(f"\n[WARNING] {log_count} active logs (threshold: {threshold_count})")
        print(f"          {len(old_logs)} logs are older than {threshold_days} days")
        print(f"          Run: python3 .ontos/scripts/ontos_consolidate.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate Ontos Context Map',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ontos_generate_context_map.py                    # Scan default 'docs' directory
  python3 ontos_generate_context_map.py --dir docs --dir specs  # Scan multiple directories
  python3 ontos_generate_context_map.py --watch            # Watch for changes
  python3 ontos_generate_context_map.py --strict           # Exit with error if issues found
"""
    )
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--dir', type=str, action='append', dest='dirs',
                        help='Directory to scan (can be specified multiple times)')
    parser.add_argument('--strict', action='store_true', help='Exit with error code 1 if issues found')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress non-error output')
    parser.add_argument('--watch', '-w', action='store_true', help='Watch for file changes and regenerate')
    parser.add_argument('--lint', action='store_true', help='Show warnings for data quality issues (empty impacts, unknown concepts)')
    parser.add_argument('--include-rejected', action='store_true', 
                        help='Include rejected proposals in context map (default: excluded)')
    parser.add_argument('--include-archived', action='store_true',
                        help='Include archived logs in context map (default: excluded)')
    args = parser.parse_args()

    # Default to docs directory if none specified
    if args.dirs:
        target_dirs = args.dirs
    elif is_ontos_repo():
        # In contributor mode, scan both internal "brain" and public docs
        target_dirs = [DOCS_DIR, 'docs']
    else:
        target_dirs = [DOCS_DIR]

    if args.watch:
        # Note: Watch mode doesn't support strict flag in this implementation yet
        watch_mode(target_dirs, args.quiet)
    else:
        issue_count = generate_context_map(target_dirs, args.quiet, args.strict, args.lint, 
                                           getattr(args, 'include_rejected', False),
                                           getattr(args, 'include_archived', False))
        
        # v2.5: Check consolidation status for prompted/advisory modes
        if not args.quiet:
            check_consolidation_status()

        if args.strict and issue_count > 0:
            print(f"\n❌ Strict mode: {issue_count} issues detected. Exiting with error.")
            sys.exit(1)

