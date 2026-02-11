"""Native migrate command implementation."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import ontos
from ontos.core.schema import (
    SCHEMA_DEFINITIONS,
    SchemaCompatibility,
    check_compatibility,
    detect_schema_version,
    serialize_frontmatter,
    add_schema_to_frontmatter,
)
from ontos.core.context import SessionContext
from ontos.io.config import load_project_config
from ontos.io.files import find_project_root, load_documents, load_frontmatter
from ontos.io.scan_scope import collect_scoped_documents, resolve_scan_scope
from ontos.io.yaml import parse_frontmatter_content
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
    scope: Optional[str] = None


def check_file_needs_migration(filepath: Path) -> Tuple[bool, str, str]:
    """Check if a file needs schema migration."""
    try:
        fm, _ = load_frontmatter(filepath, parse_frontmatter_content)
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


def _validate_migrate_mode(options: MigrateOptions) -> Optional[str]:
    """Validate command mode contract for check/dry-run/apply."""
    selected = [bool(options.check), bool(options.dry_run), bool(options.apply)]
    if sum(selected) != 1:
        return "Select exactly one mode: --check, --dry-run, or --apply"

    if options.check and (options.dry_run or options.apply):
        return "--check cannot be combined with --dry-run/--apply"
    if options.dry_run and options.apply:
        return "--dry-run cannot be combined with --apply"
    if not options.check and not options.dry_run and not options.apply:
        return "One mode is required: --check, --dry-run, or --apply"

    return None


def migrate_command(options: MigrateOptions) -> Tuple[int, str]:
    """Execute migrate command."""
    output = OutputHandler(quiet=options.quiet)
    root = find_project_root()

    mode_error = _validate_migrate_mode(options)
    if mode_error:
        output.error(mode_error)
        return 1, mode_error

    from ontos.core.curation import load_ontosignore
    config = load_project_config(repo_root=root)
    effective_scope = resolve_scan_scope(options.scope, config.scanning.default_scope)
    ignore_patterns = load_ontosignore(root)
    files = collect_scoped_documents(
        root,
        config,
        effective_scope,
        base_skip_patterns=ignore_patterns,
        explicit_dirs=options.dirs,
    )

    load_result = load_documents(files, parse_frontmatter_content)
    if load_result.has_fatal_errors or load_result.duplicate_ids:
        for issue in load_result.issues:
            if issue.code in {"duplicate_id", "parse_error", "io_error"}:
                output.error(issue.message)
        return 1, "Document load failed"

    needs_migration: List[Tuple[Path, str]] = []
    unsupported: List[Tuple[Path, str, str]] = []
    already_migrated = 0
    not_ontos = 0
    errors = 0
    tool_version = getattr(ontos, "__version__", "") or "0.0"
    
    for f in files:
        try:
            fm, _ = load_frontmatter(f, parse_frontmatter_content)
            if fm is None:
                not_ontos += 1
                continue

            if "id" not in fm:
                not_ontos += 1
                continue

            explicit_schema_raw = fm.get("ontos_schema")
            if explicit_schema_raw is not None:
                schema = str(explicit_schema_raw).strip()
                if schema not in SCHEMA_DEFINITIONS:
                    unsupported.append((f, schema, "unknown schema version"))
                    continue

                compatibility = check_compatibility(schema, tool_version)
                if compatibility.compatibility != SchemaCompatibility.COMPATIBLE:
                    unsupported.append((f, schema, compatibility.message))
                    continue

                already_migrated += 1
                continue

            inferred = detect_schema_version(fm)
            needs_migration.append((f, inferred))
        except Exception as e:
            errors += 1
            output.error(f"Error inspecting {f}: {e}")

    if options.check:
        output.info(f"\n📊 Schema Migration Check")
        output.info(f"   Scanned: {len(files)} files")
        output.info(f"   Already migrated: {already_migrated}")
        output.info(f"   Need migration: {len(needs_migration)}")
        output.info(f"   Unsupported schema: {len(unsupported)}")
        output.info(f"   Not Ontos documents: {not_ontos}")
        
        if needs_migration:
            output.info("\n📝 Files needing migration:")
            for f, schema in needs_migration:
                output.detail(f"  {f} → {schema}")

        if unsupported:
            output.warning("\n⚠️ Unsupported schema versions:")
            for f, schema, reason in unsupported:
                output.detail(f"  {f} (ontos_schema: {schema}) - {reason}")

        if needs_migration or unsupported:
            return 1, (
                f"{len(needs_migration)} files need migration; "
                f"{len(unsupported)} files have unsupported schema versions"
            )

        output.success("\n✅ All Ontos documents have explicit supported schema versions.")
        return 0, "All documents up to date"

    if not needs_migration:
        if unsupported and options.apply:
            if not options.quiet:
                output.warning("No migratable files, but unsupported schema versions were found.")
            return 1, f"Unsupported schema versions in {len(unsupported)} file(s)"

        if not options.quiet:
            output.success("Nothing to migrate.")
            if unsupported:
                output.warning(f"Found {len(unsupported)} unsupported schema file(s); no writes attempted.")
        return 0, "Nothing to migrate"

    mode_str = "Dry-run" if options.dry_run else "Applying"
    output.info(f"\n🔄 {mode_str} Schema Migration...")

    if unsupported:
        output.warning(f"Skipping {len(unsupported)} file(s) with unsupported schema versions:")
        for f, schema, reason in unsupported:
            output.detail(f"  {f} (ontos_schema: {schema}) - {reason}")
    
    ctx = SessionContext.from_repo(root)
    migrated_count = 0
    
    for f, schema in needs_migration:
        try:
            fm, body = load_frontmatter(f, parse_frontmatter_content)
            if fm is None:
                errors += 1
                continue
            new_fm = add_schema_to_frontmatter(fm, schema_version=schema)
            
            if options.dry_run:
                output.info(f"Would migrate: {f} (schema: {schema})")
                migrated_count += 1
                continue
                
            # load_frontmatter returns parsed frontmatter + body, not raw content.
            new_fm_str = serialize_frontmatter(new_fm)
            body_text = body or ""
            separator = "\n" if body_text and not body_text.startswith("\n") else ""
            new_content = f"---\n{new_fm_str}\n---{separator}{body_text}"
            
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

    if options.apply and unsupported:
        errors += len(unsupported)

    if errors > 0:
        return 1, f"Migration completed with {errors} errors"
    return 0, f"Migration completed successfully"
