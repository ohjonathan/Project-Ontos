"""Native scaffold command implementation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from ontos.core.curation import create_scaffold, load_ontosignore, should_ignore
from ontos.core.schema import serialize_frontmatter
from ontos.core.context import SessionContext
from ontos.io.config import load_project_config
from ontos.io.files import find_project_root, scan_documents, load_documents, load_frontmatter
from ontos.io.scan_scope import collect_scoped_documents, resolve_scan_scope
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
    scope: Optional[str] = None
    runtime_failures: List[str] = field(default_factory=list)


def _find_untagged_files_with_failures(
    paths: Optional[List[Path]] = None,
    root: Optional[Path] = None,
    scope: Optional[str] = None,
) -> Tuple[List[Path], List[str]]:
    """Find markdown files without valid frontmatter.

    Args:
        paths: Specific files/directories, or None for default scan
        root: Project root to use (falls back to search)

    Returns:
        Tuple of (paths needing scaffolding, failure messages)
    """
    root = root or find_project_root()
    failures: List[str] = []
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
        # Default scan from configured scope
        config = load_project_config(repo_root=root)
        effective_scope = resolve_scan_scope(scope, config.scanning.default_scope)
        ignore_patterns = load_ontosignore(root)
        files = collect_scoped_documents(
            root,
            config,
            effective_scope,
            base_skip_patterns=ignore_patterns,
        )

    load_result = load_documents(files, parse_frontmatter_content)
    if load_result.has_fatal_errors:
        # We can't safely scaffold if the graph is broken
        for issue in load_result.issues:
            if issue.code in {"parse_error", "io_error"}:
                failures.append(f"{issue.path}: {issue.message}" if issue.path else issue.message)
        return [], failures
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
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            failures.append(f"{f}: {exc}")
            continue

    return untagged, failures


def find_untagged_files(
    paths: Optional[List[Path]] = None,
    root: Optional[Path] = None,
    scope: Optional[str] = None,
) -> List[Path]:
    """Find markdown files without valid frontmatter."""
    files, _ = _find_untagged_files_with_failures(paths=paths, root=root, scope=scope)
    return files


def scaffold_file(
    path: Path,
    ctx: SessionContext,
    dry_run: bool = True,
) -> Tuple[bool, Optional[dict], Optional[str]]:
    """Add scaffold frontmatter to a file.

    Args:
        path: File to scaffold
        ctx: SessionContext for buffering writes
        dry_run: If True, return preview without modifying

    Returns:
        (success, fm_dict, error_message) tuple
    """
    try:
        content = path.read_text(encoding="utf-8")
        fm = create_scaffold(path, content)
        
        if dry_run:
            return True, fm, None
            
        fm_yaml = serialize_frontmatter(fm)
        new_content = f"---\n{fm_yaml}\n---\n\n{content}"
        
        ctx.buffer_write(path, new_content)
        return True, fm, None
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return False, None, str(exc)


def _run_scaffold_command(options: ScaffoldOptions) -> Tuple[int, str]:
    """Execute scaffold command.

    Args:
        options: Command options

    Returns:
        (exit_code, message) tuple
    """
    output = OutputHandler(quiet=options.quiet)
    options.runtime_failures = []

    # 1. Find untagged files
    root = find_project_root()
    config = load_project_config(repo_root=root)
    effective_scope = resolve_scan_scope(options.scope, config.scanning.default_scope)
    
    ignore_patterns = load_ontosignore(root)
    # Explicitly exclude archives and tmp to avoid duplicate ID noise
    ignore_patterns.extend(["**/archive/**", "**/tmp/**", "archive/*", ".ontos-internal/archive/*", ".ontos-internal/tmp/*"])
    
    all_files = collect_scoped_documents(
        root,
        config,
        effective_scope,
        base_skip_patterns=ignore_patterns,
    ) or []
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

    untagged, discovery_failures = _find_untagged_files_with_failures(
        options.paths,
        scope=options.scope,
    )
    options.runtime_failures.extend(discovery_failures)
    if not untagged:
        if not options.quiet:
            output.success("No files need scaffolding")
            for failure in discovery_failures:
                output.error(f"Failed to inspect: {failure}")
        return (1 if discovery_failures else 0), "No files need scaffolding"

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
    failures: List[str] = []

    for path in untagged:
        try:
            rel_path = path.relative_to(root)
        except ValueError:
            rel_path = path

        if options.dry_run:
            success, fm, error = scaffold_file(path, ctx, dry_run=True)
            if success and fm:
                if not options.quiet:
                    print(f"\n  {rel_path}")
                    print(f"    id: {fm.get('id')}")
                    print(f"    type: {fm.get('type')}")
                    print(f"    status: scaffold")
                success_count += 1
            else:
                failure = f"{rel_path}: {error or 'unknown error'}"
                failures.append(failure)
                if not options.quiet:
                    output.error(f"Failed to scaffold {rel_path}: {error or 'unknown error'}")
        else:
            success, _, error = scaffold_file(path, ctx, dry_run=False)
            if success:
                output.success(f"Scaffolded: {rel_path}")
                success_count += 1
            else:
                failure = f"{rel_path}: {error or 'unknown error'}"
                failures.append(failure)
                output.error(f"Failed to scaffold {rel_path}: {error or 'unknown error'}")

    # 3. Commit if not dry run
    if not options.dry_run:
        try:
            ctx.commit()
        except Exception as exc:
            output.error(f"Failed to commit scaffold changes: {exc}")
            failures.append(f"commit: {exc}")

    options.runtime_failures.extend(failures)

    # 4. Summary
    if options.dry_run:
        if not options.quiet:
            print()
            output.info("Run with --apply to execute scaffolding")
            for failure in failures:
                output.error(f"Failed: {failure}")
        exit_code = 0 if not failures else 1
        return exit_code, f"Dry run: {success_count} files would be scaffolded"
    else:
        if not options.quiet:
            output.success(f"Scaffolded {success_count}/{len(untagged)} files")
            for failure in failures:
                output.error(f"Failed: {failure}")
        return (0 if success_count == len(untagged) and not failures else 1), f"Processed {success_count} files"


def scaffold_command(options: ScaffoldOptions) -> int:
    """Run scaffold command and return exit code only."""
    exit_code, _ = _run_scaffold_command(options)
    return exit_code
