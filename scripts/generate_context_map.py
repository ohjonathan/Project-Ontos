"""Generate Ontos Context Map from documentation files."""

import os
import sys
import time
import yaml
import datetime
import argparse
from typing import Optional

from config import (
    __version__,
    DEFAULT_DOCS_DIR,
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
                    filepath = os.path.join(subdir, file)
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
                        files_data[doc_id] = {
                            'filepath': filepath,
                            'filename': file,
                            'type': normalize_type(frontmatter.get('type')),
                            'depends_on': normalize_depends_on(frontmatter.get('depends_on')),
                            'status': str(frontmatter.get('status') or 'unknown').strip() or 'unknown'
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
    by_type = {'kernel': [], 'strategy': [], 'product': [], 'atom': [], 'unknown': []}
    for doc_id, data in files_data.items():
        doc_type = data['type']
        if doc_type in by_type:
            by_type[doc_type].append(doc_id)
        else:
            by_type['unknown'].append(doc_id)

    order = ['kernel', 'strategy', 'product', 'atom', 'unknown']

    for doc_type in order:
        if by_type[doc_type]:
            tree.append(f"### {doc_type.upper()}")
            for doc_id in sorted(by_type[doc_type]):
                data = files_data[doc_id]
                deps = ", ".join(data['depends_on']) if data['depends_on'] else "None"
                tree.append(f"- **{doc_id}** ({data['filename']})")
                tree.append(f"  - Status: {data['status']}")
                tree.append(f"  - Depends On: {deps}")
            tree.append("")

    return "\n".join(tree)


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
                f"  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in config.py"
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


def generate_context_map(target_dirs: list[str], quiet: bool = False) -> int:
    """Main function to generate the CONTEXT_MAP.md file.

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

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""# Ontos Context Map
Generated on: {timestamp}
Scanned Directory: `{dirs_str}`

## 1. Hierarchy Tree
{tree_view}

## 2. Dependency Audit
{'No issues found.' if not issues else chr(10).join(issues)}

## 3. Index
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

    if not quiet:
        print(f"Successfully generated {OUTPUT_FILE}")
        print(f"Scanned {len(files_data)} documents, found {len(issues)} issues.")

    return len(issues)


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
  python3 generate_context_map.py                    # Scan default 'docs' directory
  python3 generate_context_map.py --dir docs --dir specs  # Scan multiple directories
  python3 generate_context_map.py --watch            # Watch for changes
  python3 generate_context_map.py --strict           # Exit with error if issues found
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
    target_dirs = args.dirs if args.dirs else [DEFAULT_DOCS_DIR]

    if args.watch:
        watch_mode(target_dirs, args.quiet)
    else:
        issue_count = generate_context_map(target_dirs, args.quiet)

        if args.strict and issue_count > 0:
            print(f"\n❌ Strict mode: {issue_count} issues detected. Exiting with error.")
            sys.exit(1)
