"""Native scaffold command implementation."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ontos.core.frontmatter import parse_frontmatter
from ontos.core.curation import create_scaffold, load_ontosignore, should_ignore
from ontos.core.schema import serialize_frontmatter
from ontos.core.context import SessionContext
from ontos.io.files import find_project_root, scan_documents
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

        # Check for frontmatter
        try:
            content = f.read_text(encoding="utf-8")
            if not content.strip():
                continue
            
            fm = parse_frontmatter(str(f)) # parse_frontmatter reads the file
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
    try:
        untagged = find_untagged_files(options.paths)
    except FileNotFoundError as e:
        output.error(str(e))
        return 1, str(e)

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
