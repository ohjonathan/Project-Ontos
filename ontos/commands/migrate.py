"""Native migrate command implementation."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ontos.core.schema import (
    detect_schema_version,
    serialize_frontmatter,
    add_schema_to_frontmatter,
)
from ontos.core.frontmatter import parse_frontmatter
from ontos.core.context import SessionContext
from ontos.io.files import find_project_root, scan_documents
from ontos.ui.output import OutputHandler


@dataclass
class MigrateOptions:
    """Options for migrate command."""
    check: bool = False
    dry_run: bool = False
    apply: bool = False
    dirs: Optional[List[Path]] = None
    quiet: bool = False
    json_output: bool = False


def check_file_needs_migration(filepath: Path) -> Tuple[bool, str, str]:
    """Check if a file needs schema migration."""
    try:
        fm = parse_frontmatter(str(filepath))
        if fm is None:
            return False, "", "No frontmatter"
        
        if 'id' not in fm:
            return False, "", "No id field"
        
        if 'ontos_schema' in fm:
            schema = str(fm['ontos_schema'])
            return False, schema, f"Already has ontos_schema: {schema}"
        
        inferred = detect_schema_version(fm)
        return True, inferred, f"Would add ontos_schema: {inferred}"
    except Exception as e:
        return False, "", f"Error: {e}"


def migrate_command(options: MigrateOptions) -> Tuple[int, str]:
    """Execute migrate command."""
    output = OutputHandler(quiet=options.quiet)
    root = find_project_root()
    
    # Determine directories to scan
    search_dirs = options.dirs if options.dirs else []
    if not search_dirs:
        for d in ['docs', '.ontos-internal']:
            p = root / d
            if p.exists():
                search_dirs.append(p)
    
    if not search_dirs:
        output.error("No default directories found. Use --dirs to specify.")
        return 1, "No directories to scan"

    from ontos.core.curation import load_ontosignore
    ignore_patterns = load_ontosignore(root)
    files = scan_documents(search_dirs, skip_patterns=ignore_patterns) # Filter by .md only
    files = [f for f in files if f.suffix == ".md"]

    needs_migration = []
    already_migrated = 0
    not_ontos = 0
    errors = 0
    
    for f in files:
        needs, schema, msg = check_file_needs_migration(f)
        if needs:
            needs_migration.append((f, schema))
        elif schema:
            already_migrated += 1
        else:
            not_ontos += 1

    if options.check:
        output.info(f"\n📊 Schema Migration Check")
        output.info(f"   Scanned: {len(files)} files")
        output.info(f"   Already migrated: {already_migrated}")
        output.info(f"   Need migration: {len(needs_migration)}")
        output.info(f"   Not Ontos documents: {not_ontos}")
        
        if needs_migration:
            output.info("\n📝 Files needing migration:")
            for f, schema in needs_migration:
                output.detail(f"  {f} → {schema}")
            return 1, f"{len(needs_migration)} files need migration"
        else:
            output.success("\n✅ All Ontos documents have explicit schema versions.")
            return 0, "All documents up to date"

    if not needs_migration:
        if not options.quiet:
            output.success("Nothing to migrate.")
        return 0, "Nothing to migrate"

    mode_str = "Dry-run" if options.dry_run else "Applying"
    output.info(f"\n🔄 {mode_str} Schema Migration...")
    
    ctx = SessionContext.from_repo(root)
    migrated_count = 0
    
    for f, schema in needs_migration:
        try:
            content = f.read_text(encoding='utf-8')
            fm = parse_frontmatter(str(f))
            new_fm = add_schema_to_frontmatter(fm, schema_version=schema)
            
            if options.dry_run:
                output.info(f"Would migrate: {f} (schema: {schema})")
                migrated_count += 1
                continue
                
            # Build new content
            parts = content.split('---', 2)
            if len(parts) < 3:
                output.error(f"Incomplete frontmatter in {f}")
                errors += 1
                continue
                
            new_fm_str = serialize_frontmatter(new_fm)
            new_content = f"---\n{new_fm_str}\n---{parts[2]}"
            
            ctx.buffer_write(f, new_content)
            output.success(f"Migrated: {f} → ontos_schema: {schema}")
            migrated_count += 1
        except Exception as e:
            output.error(f"Error migrating {f}: {e}")
            errors += 1

    if not options.dry_run and migrated_count > 0:
        ctx.commit()

    action = 'Would migrate' if options.dry_run else 'Migrated'
    output.info(f"\n{action} {migrated_count} file(s).")
    
    if errors > 0:
        return 1, f"Migration completed with {errors} errors"
    return 0, f"Migration completed successfully"
