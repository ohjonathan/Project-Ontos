"""Native verify command implementation."""

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Optional, Tuple, List

from ontos.core.staleness import (
    normalize_describes,
    check_staleness,
)
from ontos.core.context import SessionContext
from ontos.io.config import load_project_config
from ontos.io.files import find_project_root, load_documents, load_frontmatter
from ontos.io.scan_scope import collect_scoped_documents, resolve_scan_scope
from ontos.io.yaml import parse_frontmatter_content
from ontos.ui.output import OutputHandler


@dataclass
class VerifyOptions:
    """Options for verify command."""
    path: Optional[Path] = None
    all: bool = False
    date: Optional[str] = None  # YYYY-MM-DD format
    quiet: bool = False
    json_output: bool = False
    scope: Optional[str] = None


def find_stale_documents_list(scope: Optional[str] = None) -> List[dict]:
    """Find all documents with stale describes fields using new architecture symbols."""
    from ontos.core.curation import load_ontosignore

    root = find_project_root()
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
    if load_result.has_fatal_errors or load_result.duplicate_ids:
        return [] # Caller will handle empty and check if it needs to fail
    
    # Build ID to path mapping for staleness checker
    id_to_path = {
        doc_id: str(doc.filepath) 
        for doc_id, doc in load_result.documents.items()
    }
    
    stale_docs = []
    for doc_id, doc in load_result.documents.items():
        describes = normalize_describes(doc.frontmatter.get('describes'))
        if not describes:
            continue
            
        staleness = check_staleness(
            doc_id=doc_id,
            doc_path=str(doc.filepath),
            describes=describes,
            describes_verified=doc.frontmatter.get('describes_verified'),
            id_to_path=id_to_path
        )
        
        if staleness and staleness.is_stale():
            stale_docs.append({
                'doc_id': doc_id,
                'filepath': str(doc.filepath),
                'staleness': staleness
            })
            
    return stale_docs


def update_describes_verified(
    filepath: Path,
    new_date: date,
    ctx: SessionContext,
    output: OutputHandler
) -> bool:
    """Update the describes_verified field in a document.
    
    Matches exact regex replacement logic from legacy script.
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        
        if not content.startswith('---'):
            output.error(f"{filepath} has no frontmatter")
            return False
        
        parts = content.split('---', 2)
        if len(parts) < 3:
            output.error(f"Invalid frontmatter in {filepath}")
            return False
        
        frontmatter = parts[1]
        body = parts[2]
        date_str = new_date.isoformat()
        
        # Check if describes_verified already exists
        if re.search(r'^describes_verified:', frontmatter, re.MULTILINE):
            new_frontmatter = re.sub(
                r'^describes_verified:.*$',
                f'describes_verified: {date_str}',
                frontmatter,
                flags=re.MULTILINE
            )
        else:
            # Add after describes field
            if re.search(r'^describes:', frontmatter, re.MULTILINE):
                new_frontmatter = re.sub(
                    r'^(describes:.*(?:\n  - .*)*)$',
                    f'\\1\ndescribes_verified: {date_str}',
                    frontmatter,
                    flags=re.MULTILINE
                )
            else:
                new_frontmatter = frontmatter.rstrip() + f'\ndescribes_verified: {date_str}\n'
        
        new_content = f'---{new_frontmatter}---{body}'
        ctx.buffer_write(filepath, new_content)
        return True
    except Exception as e:
        output.error(f"Error updating {filepath}: {e}")
        return False


def verify_document(path: Path, verify_date: str) -> Tuple[bool, str]:
    """Helper for verify command."""
    # Ensure path is Path object
    p = Path(path)
    root = find_project_root()
    ctx = SessionContext.from_repo(root)
    output = OutputHandler(quiet=True)
    
    try:
        dt = date.fromisoformat(verify_date)
    except ValueError:
        return False, "Invalid date format"
        
    success = update_describes_verified(p, dt, ctx, output)
    if success:
        try:
            ctx.commit()
        except Exception as exc:
            return False, f"Commit failed: {exc}"
        return True, "Verified"
    return False, "Failed"


def verify_all_interactive(verify_date: date, output: OutputHandler, scope: Optional[str] = None) -> int:
    """Interactively verify all stale documents."""
    root = find_project_root()
    from ontos.core.curation import load_ontosignore
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
    
    if load_result.has_fatal_errors or load_result.duplicate_ids:
        for issue in load_result.issues:
            if issue.code in {"duplicate_id", "parse_error", "io_error"}:
                output.error(issue.message)
        return 1

    stale_docs = find_stale_documents_list(scope=scope)
    
    if not stale_docs:
        output.success("No stale documents found.")
        return 0
    
    updated = 0
    skipped = 0
    ctx = SessionContext.from_repo(root)
    
    for i, doc in enumerate(stale_docs, 1):
        staleness = doc['staleness']
        # Show up to 3 stale atoms
        stale_atoms_str = ", ".join([f"{a} changed {d}" for a, d in staleness.stale_atoms[:3]])
        
        output.plain(f"\n[{i}/{len(stale_docs)}] {doc['doc_id']}")
        output.detail(f"File: {doc['filepath']}")
        output.detail(f"Stale because: {stale_atoms_str}")
        
        try:
            response = input("      Verify as current? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            output.warning("Aborted")
            return 1
            
        if response == 'y':
            if update_describes_verified(Path(doc['filepath']), verify_date, ctx, output):
                output.success(f"Updated describes_verified to {verify_date}")
                updated += 1
            else:
                output.error("Failed to update")
        else:
            output.info("Skipped")
            skipped += 1
            
    if updated > 0:
        try:
            ctx.commit()
        except Exception as exc:
            output.error(f"Failed to commit verify updates: {exc}")
            return 1
        
    output.info(f"Done. Updated: {updated}, Skipped: {skipped}")
    return 0


def _run_verify_command(options: VerifyOptions) -> Tuple[int, str]:
    """Execute verify command."""
    output = OutputHandler(quiet=options.quiet)
    
    # Parse date
    verify_date = date.today()
    if options.date:
        try:
            verify_date = date.fromisoformat(options.date)
        except ValueError:
            output.error(f"Invalid date format: {options.date}. Use YYYY-MM-DD.")
            return 1, f"Invalid date format: {options.date}"

    if options.path:
        # Single file mode
        if not options.path.exists():
            output.error(f"File not found: {options.path}")
            return 1, f"File not found: {options.path}"
            
        root = find_project_root()
        ctx = SessionContext.from_repo(root)
        
        # Check if doc has describes
        fm, _ = load_frontmatter(options.path, parse_frontmatter_content)
        if not fm:
            output.error(f"Failed to parse frontmatter in {options.path}")
            return 1, "Parse failure"
            
        describes = normalize_describes(fm.get('describes'))
        if not describes:
            output.warning(f"{options.path} has no describes field, nothing to verify")
            return 0, "Nothing to verify"
            
        if update_describes_verified(options.path, verify_date, ctx, output):
            try:
                ctx.commit()
            except Exception as exc:
                output.error(f"Failed to commit verify updates: {exc}")
                return 1, f"Commit failed: {exc}"
            output.success(f"Updated describes_verified to {verify_date}")
            return 0, "Success"
        else:
            return 1, "Update failed"

    elif options.all:
        # Interactive all mode
        result = verify_all_interactive(verify_date, output, scope=options.scope)
        return result, "Interactive session ended"
        
    else:
        output.error("Specify a file path or use --all")
        return 1, "No target specified"


def verify_command(options: VerifyOptions) -> int:
    """Run verify command and return exit code only."""
    exit_code, _ = _run_verify_command(options)
    return exit_code


def verify_portfolio(
    *,
    portfolio_db_path: Path,
    registry_path: Path,
    json_output: bool = False,
) -> int:
    """Compare portfolio DB projects against the dev-hub registry."""
    if not portfolio_db_path.exists():
        message = "Portfolio DB not found. Run `ontos serve --portfolio` first."
        _emit_verify_portfolio_result(
            clean=False,
            missing_in_db=[],
            missing_in_json=[],
            field_mismatches=[],
            summary=message,
            json_output=json_output,
            exit_code=2,
        )
        return 2

    if not registry_path.exists():
        message = (
            f"Registry file not found at {registry_path}. "
            "Check portfolio.toml registry_path."
        )
        _emit_verify_portfolio_result(
            clean=False,
            missing_in_db=[],
            missing_in_json=[],
            field_mismatches=[],
            summary=message,
            json_output=json_output,
            exit_code=2,
        )
        return 2

    try:
        db_projects = _load_portfolio_db_projects(portfolio_db_path)
        registry_projects = _load_registry_projects(registry_path)
    except (sqlite3.DatabaseError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        _emit_verify_portfolio_result(
            clean=False,
            missing_in_db=[],
            missing_in_json=[],
            field_mismatches=[],
            summary=f"Portfolio verification failed: {exc}",
            json_output=json_output,
            exit_code=2,
        )
        return 2

    db_slugs = set(db_projects.keys())
    registry_slugs = set(registry_projects.keys())
    missing_in_db = sorted(registry_slugs - db_slugs)
    missing_in_json = sorted(db_slugs - registry_slugs)

    field_mismatches: list[dict[str, Any]] = []
    for slug in sorted(db_slugs & registry_slugs):
        db_row = db_projects[slug]
        registry_row = registry_projects[slug]
        for field in ("path", "status", "has_ontos"):
            db_value = db_row.get(field)
            registry_value = registry_row.get(field)
            if db_value != registry_value:
                field_mismatches.append(
                    {
                        "slug": slug,
                        "field": field,
                        "db_value": db_value,
                        "json_value": registry_value,
                    }
                )

    discrepancies = len(missing_in_db) + len(missing_in_json) + len(field_mismatches)
    clean = discrepancies == 0
    summary = "No discrepancies found." if clean else f"{discrepancies} discrepancies found."
    exit_code = 0 if clean else 1
    _emit_verify_portfolio_result(
        clean=clean,
        missing_in_db=missing_in_db,
        missing_in_json=missing_in_json,
        field_mismatches=field_mismatches,
        summary=summary,
        json_output=json_output,
        exit_code=exit_code,
    )
    return exit_code


def _load_portfolio_db_projects(portfolio_db_path: Path) -> dict[str, dict[str, Any]]:
    connection = sqlite3.connect(str(portfolio_db_path))
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT slug, path, status, has_ontos FROM projects"
        ).fetchall()
    finally:
        connection.close()

    projects: dict[str, dict[str, Any]] = {}
    for row in rows:
        slug = str(row["slug"])
        projects[slug] = {
            "path": _normalize_path(row["path"]),
            "status": str(row["status"]),
            "has_ontos": bool(row["has_ontos"]),
        }
    return projects


def _load_registry_projects(registry_path: Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    registry_root = _registry_root(raw, registry_path.parent)
    if isinstance(raw, dict):
        records = raw.get("projects", [])
    else:
        records = raw
    if not isinstance(records, list):
        raise ValueError("Registry JSON must contain a list of project objects.")

    projects: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        path_value = record.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            continue
        normalized_path = _normalize_registry_path(path_value, registry_root)
        slug = _slugify_path_name(normalized_path)
        status = str(record.get("status", "unknown"))
        has_ontos = _registry_has_ontos(record, normalized_path)
        projects[slug] = {
            "path": normalized_path,
            "status": status,
            "has_ontos": has_ontos,
        }
    return projects


def _normalize_path(path_value: Any) -> str:
    return str(Path(str(path_value)).expanduser().resolve(strict=False))


def _normalize_registry_path(path_value: Any, registry_root: Path) -> str:
    path = Path(str(path_value)).expanduser()
    if not path.is_absolute():
        path = registry_root / path
    return str(path.resolve(strict=False))


def _registry_root(raw: object, default_root: Path) -> Path:
    if isinstance(raw, dict):
        dev_root = raw.get("dev_root")
        if isinstance(dev_root, str) and dev_root.strip():
            return Path(dev_root).expanduser().resolve(strict=False)
    return default_root.resolve(strict=False)


def _registry_has_ontos(record: dict[str, Any], normalized_path: str) -> bool:
    if "has_ontos" in record:
        return bool(record.get("has_ontos"))
    return (Path(normalized_path) / ".ontos.toml").exists()


def _slugify_path_name(path_value: str) -> str:
    path_name = Path(path_value).name
    try:
        from ontos.mcp.scanner import slugify
    except Exception:
        slugify = None
    if slugify is not None:
        return slugify(path_name)
    lowered = path_name.strip().lower()
    result: list[str] = []
    previous_dash = False
    for char in lowered:
        if char.isalnum():
            result.append(char)
            previous_dash = False
            continue
        if not previous_dash:
            result.append("-")
        previous_dash = True
    slug = "".join(result).strip("-")
    return slug or "workspace"


def _emit_verify_portfolio_result(
    *,
    clean: bool,
    missing_in_db: list[str],
    missing_in_json: list[str],
    field_mismatches: list[dict[str, Any]],
    summary: str,
    json_output: bool,
    exit_code: int,
) -> None:
    if json_output:
        payload: dict[str, Any] = {
            "clean": clean,
            "missing_in_db": missing_in_db,
            "missing_in_json": missing_in_json,
            "field_mismatches": field_mismatches,
            "summary": summary,
        }
        if exit_code == 2:
            payload["error"] = True
        print(json.dumps(payload, ensure_ascii=True))
        return

    if clean:
        print(summary)
        return
    if exit_code == 2:
        print(summary)
        return

    print(summary)
    if missing_in_db:
        print("Missing in portfolio DB:")
        for slug in missing_in_db:
            print(f"  - {slug}")
    if missing_in_json:
        print("Missing in projects.json:")
        for slug in missing_in_json:
            print(f"  - {slug}")
    if field_mismatches:
        print("Field mismatches:")
        for mismatch in field_mismatches:
            print(
                "  - "
                f"{mismatch['slug']} {mismatch['field']}: "
                f"db={mismatch['db_value']!r} json={mismatch['json_value']!r}"
            )
