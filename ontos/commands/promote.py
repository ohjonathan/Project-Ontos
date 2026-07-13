"""Native promote command implementation."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from ontos.core.config import ConfigError
from ontos.core.frontmatter_edit import (
    InvalidDocumentEncodingError,
    patch_frontmatter_fields,
    read_utf8_for_mutation,
)
from ontos.core.types import DocumentData, DocumentType
from ontos.core.curation import (
    CurationLevel,
    CurationInfo,
    get_curation_info,
    promote_to_full,
    level_marker,
)
from ontos.core.context import SessionContext
from ontos.io.config import load_project_config
from ontos.io.files import find_project_root, load_documents, load_frontmatter
from ontos.io.scan_scope import collect_scoped_documents, resolve_scan_scope
from ontos.io.yaml import parse_frontmatter_content
from ontos.ui.output import OutputHandler


@dataclass
class PromoteOptions:
    """Options for promote command."""
    files: Optional[List[Path]] = None
    check: bool = False
    all_ready: bool = False
    yes: bool = False
    quiet: bool = False
    json_output: bool = False
    scope: Optional[str] = None
    repo_root: Optional[Path] = None


def fuzzy_match_ids(query: str, all_ids: List[str]) -> List[str]:
    """Simple fuzzy matching for document IDs."""
    query_lower = query.lower()
    if query in all_ids:
        return [query]
    prefix_matches = [id for id in all_ids if id.lower().startswith(query_lower)]
    if prefix_matches:
        return prefix_matches[:5]
    substring_matches = [id for id in all_ids if query_lower in id.lower()]
    return substring_matches[:5]


def interactive_get_depends_on(
    doc_id: str,
    doc_type: str,
    existing_ids: List[str],
    output: OutputHandler
) -> Optional[List[str]]:
    """Prompt user for depends_on."""
    if doc_type in ('kernel', 'log'):
        return None
    
    print(f"\n  This is a '{doc_type}' document. What does it depend on?")
    print("  (Type to search, comma-separate multiple, or empty to skip)")
    
    while True:
        try:
            user_input = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
            
        if not user_input:
            return None
        
        parts = [p.strip() for p in user_input.split(',') if p.strip()]
        resolved = []
        for part in parts:
            matches = fuzzy_match_ids(part, existing_ids)
            if len(matches) == 1:
                resolved.append(matches[0])
            elif len(matches) > 1:
                print(f"    Multiple matches for '{part}': {matches}")
                try:
                    choice = input(f"    Choose one (or exact ID): ").strip()
                except (EOFError, KeyboardInterrupt):
                    continue
                if choice in matches or choice in existing_ids:
                    resolved.append(choice)
                else:
                    print(f"    Skipping '{part}'")
            else:
                output.warning(f"    ID '{part}' not found - adding anyway")
                resolved.append(part)
        
        if resolved:
            print(f"  ✓ depends_on: {resolved}")
            return resolved
        return None


def interactive_get_concepts(doc_type: str, output: OutputHandler) -> Optional[List[str]]:
    """Prompt user for concepts."""
    if doc_type != 'log':
        return None
    
    print("\n  Logs require concepts. Enter concepts (comma-separated):")
    try:
        user_input = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
        
    if not user_input:
        output.warning("  No concepts provided - log requires concepts at L2")
        return None
    
    concepts = [c.strip() for c in user_input.split(',') if c.strip()]
    print(f"  ✓ concepts: {concepts}")
    return concepts


def apply_promotion(
    filepath: Path,
    frontmatter: dict,
    depends_on: Optional[List[str]],
    concepts: Optional[List[str]],
    ctx: SessionContext,
    output: OutputHandler
) -> bool:
    """Apply promotion to a document."""
    try:
        content = read_utf8_for_mutation(filepath)
        new_fm, summary_seed = promote_to_full(
            frontmatter,
            depends_on=depends_on,
            concepts=concepts
        )
        
        updates = {
            key: value
            for key, value in new_fm.items()
            if key not in frontmatter or frontmatter[key] != value
        }
        new_content = patch_frontmatter_fields(content, updates)
        
        ctx.buffer_write(filepath, new_content)
        output.success(f"Promoted: {frontmatter.get('id')} → Level 2")
        return True
    except InvalidDocumentEncodingError:
        raise
    except Exception as e:
        output.error(f"Failed to promote {filepath}: {e}")
        return False


def _run_promote_command(options: PromoteOptions) -> Tuple[int, str]:
    """Execute promote command."""
    output = OutputHandler(quiet=options.quiet)
    if options.json_output and not (options.check or options.all_ready):
        return 2, "JSON mode requires --check or --all-ready"
    try:
        root = options.repo_root if options.repo_root is not None else find_project_root()
    except FileNotFoundError as exc:
        return 2, str(exc)
    
    # 1. Gather files
    if options.files:
        files = [root / f if not f.is_absolute() else f for f in options.files]
    else:
        # Scan by configured scope.
        try:
            config = load_project_config(repo_root=root)
        except ConfigError as exc:
            return 2, f"Config error: {exc}"
        except Exception as exc:
            return 5, f"Config error: {exc}"
        effective_scope = resolve_scan_scope(options.scope, config.scanning.default_scope)
        from ontos.core.curation import load_ontosignore
        ignore_patterns = load_ontosignore(root)
        files = collect_scoped_documents(
            root,
            config,
            effective_scope,
            base_skip_patterns=ignore_patterns,
        )

    # 2. Extract info and filter promotable using canonical loader
    load_result = load_documents(files, parse_frontmatter_content)
    if load_result.has_fatal_errors or load_result.duplicate_ids:
        fatal = False
        for issue in load_result.issues:
            if issue.code in {"parse_error", "io_error"}:
                output.error(issue.message)
                fatal = True
            elif issue.code == "duplicate_id":
                output.error(issue.message)
                fatal = True
        
        if fatal:
            return 5, "Document load failed"

    promotable = []
    for doc_id, doc in load_result.documents.items():
        info = get_curation_info(doc.frontmatter)
        if info.level < CurationLevel.FULL:
            promotable.append((doc.filepath, doc.frontmatter, info))
            
    existing_ids = list(load_result.documents.keys())
            
    if not promotable:
        if not options.quiet:
            output.success("No documents need promotion - all at Level 2!")
        return 0, "No documents to promote"

    # 3. Handle --check
    if options.check:
        ready_count = sum(1 for _, _, info in promotable if info.promotable)
        output.info(f"Found {len(promotable)} candidate(s), {ready_count} ready for promotion:\n")
        if not options.quiet:
            root_resolved = root.resolve()
            for f, fm, info in promotable:
                try:
                    rel = f.resolve().relative_to(root_resolved)
                except ValueError:
                    rel = f # Fallback to absolute if not under root
                marker = level_marker(info.level)
                ready = "✓ ready" if info.promotable else "○ needs work"
                print(f"  {marker} {fm.get('id'):<30} {ready}")
                if not info.promotable:
                    for blocker in info.promotion_blockers[:2]:
                        print(f"      → {blocker}")
        return 1, f"{ready_count} ready for promotion ({len(promotable)} candidates)"

    ctx = SessionContext.from_repo(root)
    success_count = 0
    
    # 4. Handle --all-ready
    if options.all_ready:
        ready_docs = [(f, fm, info) for f, fm, info in promotable if info.promotable]
        if not ready_docs:
            output.warning("No documents are ready for automatic promotion.")
            return 3, "Nothing ready"
            
        output.info(f"Batch promoting {len(ready_docs)} ready document(s)...")
        for f, fm, info in ready_docs:
            try:
                promoted = apply_promotion(
                    f,
                    fm,
                    fm.get('depends_on'),
                    fm.get('concepts'),
                    ctx,
                    output,
                )
            except InvalidDocumentEncodingError as exc:
                output.error(str(exc))
                return 5, str(exc)
            if promoted:
                success_count += 1
            else:
                return 5, f"Failed to promote {f}"
        if success_count > 0:
            try:
                ctx.commit()
            except Exception as exc:
                output.error(f"Failed to commit promoted documents: {exc}")
                return 5, f"Commit failed: {exc}"
        return 0, f"Promoted {success_count} documents"

    # 5. Interactive Mode
    output.info(f"Found {len(promotable)} document(s) at L0/L1")
    for f, fm, info in promotable:
        doc_id = fm.get('id', 'unknown')
        doc_type = fm.get('type', 'unknown')
        
        print(f"\n{'='*60}")
        output.info(f"Promoting: {doc_id} ({level_marker(info.level)} → [L2])")
        print(f"  Type: {doc_type}")
        try:
            print(f"  Path: {f.resolve().relative_to(root.resolve())}")
        except ValueError:
            print(f"  Path: {f}")
        
        if info.promotion_blockers:
            print(f"\n  Blockers to resolve:")
            for blocker in info.promotion_blockers:
                print(f"    - {blocker}")
        
        # Get depends_on if needed
        depends_on = fm.get('depends_on')
        if doc_type not in ('kernel', 'log') and not depends_on:
            depends_on = interactive_get_depends_on(doc_id, doc_type, existing_ids, output)
            if depends_on is None and doc_type not in ('kernel', 'log'):
                output.warning("  depends_on required for this type. Skipping.")
                continue
        
        # Get concepts if needed
        concepts = fm.get('concepts')
        if doc_type == 'log' and not concepts:
            concepts = interactive_get_concepts(doc_type, output)
            if concepts is None:
                output.warning("  concepts required for logs. Skipping.")
                continue
        
        if options.yes:
            confirm = "y"
        else:
            try:
                confirm = input("\n  Promote this document? [Y/n]: ").strip().lower()
            except EOFError:
                print("\n  Cancelled.")
                return 2, "Cancelled"
            except KeyboardInterrupt:
                return 130, "Interrupted"
            
        if confirm in ('n', 'no'):
            output.info("  Skipped.")
            continue
            
        try:
            promoted = apply_promotion(
                f,
                fm,
                depends_on,
                concepts,
                ctx,
                output,
            )
        except InvalidDocumentEncodingError as exc:
            output.error(str(exc))
            return 5, str(exc)
        if promoted:
            success_count += 1
        else:
            return 5, f"Failed to promote {f}"

    if success_count > 0:
        try:
            ctx.commit()
        except Exception as exc:
            output.error(f"Failed to commit promoted documents: {exc}")
            return 5, f"Commit failed: {exc}"
    if success_count > 0:
        output.success(f"Promoted {success_count} document(s) to Level 2")
    return 0, f"Promoted {success_count} documents"


def promote_command(options: PromoteOptions) -> int:
    """Run promote command and return exit code only."""
    exit_code, _ = _run_promote_command(options)
    return exit_code
