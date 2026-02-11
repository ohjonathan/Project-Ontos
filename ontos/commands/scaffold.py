"""Native scaffold command implementation."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ontos.core.curation import create_scaffold, load_ontosignore, should_ignore
from ontos.core.schema import serialize_frontmatter
from ontos.core.context import SessionContext
from ontos.io.files import find_project_root, scan_documents, load_documents, load_frontmatter
from ontos.io.yaml import parse_frontmatter_content
from ontos.ui.output import OutputHandler

# Hardcoded exclusion patterns for dependency directories.
# These are always skipped regardless of .ontosignore presence.
# Mirrors legacy _scripts/ontos_scaffold.py behavior.
DEFAULT_IGNORES = [
    'node_modules', '.venv', 'venv', 'vendor',
    '__pycache__', '.pytest_cache', '.mypy_cache',
    'dist', 'build', '.tox', '.eggs',
]


@dataclass
class ScaffoldOptions:
    """Options for scaffold command."""
    paths: List[Path] = None  # File(s) or directory to scaffold
    apply: bool = False
    dry_run: bool = True
    quiet: bool = False
    json_output: bool = False


def find_untagged_files(paths: Optional[List[Path]] = None, root: Optional[Path] = None) -> List[Path]:
    """Find markdown files without valid frontmatter.

    Args:
        paths: Specific files/directories, or None for default scan
        root: Project root to use (falls back to search)

    Returns:
        List of paths needing scaffolding
    """
    root = root or find_project_root()
    if paths:
        # Filter only existing markdown files from provided paths
        search_paths = []
        for p in paths:
            if not p.is_absolute():
                p = root / p
            if p.is_file() and p.suffix == ".md":
                search_paths.append(p)
            elif p.is_dir():
                search_paths.extend(scan_documents([p], skip_patterns=load_ontosignore(root)))
        # Deduplicate and sort
        files = sorted(list(set(search_paths)))
    else:
        # Default scan from root
        ignore_patterns = load_ontosignore(root)
        files = scan_documents([root], skip_patterns=ignore_patterns)

    load_result = load_documents(files, parse_frontmatter_content)
    if load_result.has_fatal_errors:
        # We can't safely scaffold if the graph is broken
        return [] 
    # Duplicate IDs are intentionally tolerated in scaffold context.
    # Scaffold creates new files and only needs the existing ID set for
    # collision avoidance — first-wins resolution is sufficient.

    untagged = []
    for f in files:
        # Skip hidden directories except .ontos and .ontos-internal
        try:
            rel_path = f.relative_to(root)
        except ValueError:
            rel_path = f

        if any(part.startswith('.') for part in rel_path.parts[:-1]):
            if '.ontos' not in str(f) and '.ontos-internal' not in str(f):
                continue

        # Skip DEFAULT_IGNORES directories (safety: prevents modifying dependency files)
        if any(ignore in rel_path.parts for ignore in DEFAULT_IGNORES):
            continue

        # Check for frontmatter using canonical loader
        try:
            fm, raw_content = load_frontmatter(f, parse_frontmatter_content)
            if not raw_content or not raw_content.strip():
                continue
            
            if not fm or 'id' not in fm:
                untagged.append(f)
        except Exception:
            continue
            
    return untagged


def scaffold_file(path: Path, ctx: SessionContext, dry_run: bool = True) -> Tuple[bool, Optional[dict]]:
    """Add scaffold frontmatter to a file.

    Args:
        path: File to scaffold
        ctx: SessionContext for buffering writes
        dry_run: If True, return preview without modifying

    Returns:
        (success, fm_dict) tuple
    """
    try:
        content = path.read_text(encoding="utf-8")
        fm = create_scaffold(path, content)
        
        if dry_run:
            return True, fm
            
        fm_yaml = serialize_frontmatter(fm)
        new_content = f"---\n{fm_yaml}\n---\n\n{content}"
        
        ctx.buffer_write(path, new_content)
        return True, fm
    except Exception:
        return False, None


def scaffold_command(options: ScaffoldOptions) -> Tuple[int, str]:
    """Execute scaffold command.

    Args:
        options: Command options

    Returns:
        (exit_code, message) tuple
    """
    output = OutputHandler(quiet=options.quiet)

    # 1. Find untagged files
    root = find_project_root()
    from ontos.io.config import load_project_config
    config = load_project_config(repo_root=root)
    
    docs_dir = root / config.paths.docs_dir
    logs_dir = root / config.paths.logs_dir
    scan_dirs = [d for d in [docs_dir, logs_dir] if d.exists()]
    
    ignore_patterns = load_ontosignore(root)
    # Explicitly exclude archives and tmp to avoid duplicate ID noise
    ignore_patterns.extend(["**/archive/**", "**/tmp/**", "archive/*", ".ontos-internal/archive/*", ".ontos-internal/tmp/*"])
    
    all_files = scan_documents(scan_dirs, skip_patterns=ignore_patterns) or []
    load_result = load_documents(all_files, parse_frontmatter_content)
    
    if load_result.has_fatal_errors:
        fatal = False
        for issue in load_result.issues:
            if issue.code in {"parse_error", "io_error"}:
                output.error(issue.message)
                fatal = True
            elif issue.code == "duplicate_id":
                # Duplicates are reported but not always fatal for scaffolding
                output.warning(issue.message)
        
        # Duplicate IDs are intentionally tolerated in scaffold context.
        # Scaffold creates new files and only needs the existing ID set for
        # collision avoidance — first-wins resolution is sufficient.
        if fatal:
            return 1, "Document load failed"
    
    # Check specifically for duplicates of paths we are trying to scaffold?
    # Actually, scan_documents already picked them up.

    untagged = find_untagged_files(options.paths)
    if not untagged:
        if not options.quiet:
            output.success("No files need scaffolding")
        return 0, "No files need scaffolding"

    if not options.quiet:
        if options.dry_run:
            output.info("Scaffold preview (use --apply to execute)")
        else:
            output.info("Applying scaffolds...")
        output.info(f"Found {len(untagged)} file(s) needing scaffolding")

    # 2. Process each file
    root = find_project_root()
    ctx = SessionContext.from_repo(root)
    success_count = 0

    for path in untagged:
        try:
            rel_path = path.relative_to(root)
        except ValueError:
            rel_path = path

        if options.dry_run:
            success, fm = scaffold_file(path, ctx, dry_run=True)
            if success and fm:
                if not options.quiet:
                    print(f"\n  {rel_path}")
                    print(f"    id: {fm.get('id')}")
                    print(f"    type: {fm.get('type')}")
                    print(f"    status: scaffold")
                success_count += 1
        else:
            success, _ = scaffold_file(path, ctx, dry_run=False)
            if success:
                output.success(f"Scaffolded: {rel_path}")
                success_count += 1
            else:
                output.error(f"Failed to scaffold {rel_path}")

    # 3. Commit if not dry run
    if not options.dry_run:
        ctx.commit()

    # 4. Summary
    if options.dry_run:
        if not options.quiet:
            print()
            output.info("Run with --apply to execute scaffolding")
        return 0, f"Dry run: {success_count} files would be scaffolded"
    else:
        if not options.quiet:
            output.success(f"Scaffolded {success_count}/{len(untagged)} files")
        return (0 if success_count == len(untagged) else 1), f"Processed {success_count} files"
