"""Generate Ontos Context Map from documentation files."""

import os
import sys
import time
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
    SKIP_PATTERNS
)

OUTPUT_FILE = CONTEXT_MAP_FILE


def parse_frontmatter(filepath: str) -> Optional[dict]:
    """Parses YAML frontmatter from a markdown file.

    Args:
        filepath: Path to the markdown file.

    Returns:
        Dictionary of frontmatter fields, or None if no valid frontmatter.
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    if content.startswith('---'):
        try:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                return frontmatter
        except yaml.YAMLError as e:
            print(f"Error parsing YAML in {filepath}: {e}")
    return None


def normalize_depends_on(value) -> list[str]:
    """Normalize depends_on field to a list of strings.

    Handles YAML edge cases: null, empty, string, or list.

    Args:
        value: Raw value from YAML frontmatter.

    Returns:
        List of dependency IDs (empty list if none).
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        # Filter out None/empty values in list
        return [str(v) for v in value if v is not None and str(v).strip()]
    return []


def normalize_type(value) -> str:
    """Normalize type field to a string.

    Handles YAML edge cases: null, empty, string, or list.

    Args:
        value: Raw value from YAML frontmatter.

    Returns:
        Type string ('unknown' if invalid).
    """
    if value is None:
        return 'unknown'
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or '|' in stripped:
            return 'unknown'
        return stripped
    if isinstance(value, list):
        if value and value[0] is not None:
            first = str(value[0]).strip()
            # Clean up if it looks like "[option1 | option2]"
            if '|' in first:
                return 'unknown'
            return first if first else 'unknown'
    return 'unknown'


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
                
                tree.append(f"- **{doc_id}** ({data['filename']}) {tokens}")
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
    
    return f"""<!--
Ontos Context Map
Generated: {timestamp}
Mode: {mode}
Scanned: {scanned_dir}
-->"""



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

            if doc_type in ALLOWED_ORPHAN_TYPES:
                continue
            if any(pattern in filename for pattern in SKIP_PATTERNS):
                continue
            if '/logs/' in filepath or '\\logs\\' in filepath:
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


def generate_context_map(target_dirs: list[str], quiet: bool = False, strict: bool = False) -> int:
    """Main function to generate the Ontos_Context_Map.md file.

    Args:
        target_dirs: List of directories to scan.
        quiet: Suppress output if True.

    Returns:
        Number of issues found.
    """
    dirs_str = ", ".join(target_dirs)
    if not quiet:
        print(f"Scanning {dirs_str}...")
    files_data = scan_docs(target_dirs)

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

    if not quiet:
        print(f"Successfully generated {OUTPUT_FILE}")
        print(f"Scanned {len(files_data)} documents, found {len(issues)} issues.")

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
    args = parser.parse_args()

    # Default to docs directory if none specified
    target_dirs = args.dirs if args.dirs else [DOCS_DIR]

    if args.watch:
        # Note: Watch mode doesn't support strict flag in this implementation yet
        watch_mode(target_dirs, args.quiet)
    else:
        issue_count = generate_context_map(target_dirs, args.quiet, args.strict)

        if args.strict and issue_count > 0:
            print(f"\n❌ Strict mode: {issue_count} issues detected. Exiting with error.")
            sys.exit(1)
