#!/usr/bin/env python3
"""
Generate Ontos Context Map.

DEPRECATED: This script is a compatibility wrapper.
Use `ontos map` or `python -m ontos.commands.map` instead.

Phase 2 v3.0: Reduced to <200 lines per spec requirement.
"""

import argparse
import sys
import warnings
from pathlib import Path

# === DEPRECATION WARNING ===
warnings.warn(
    "ontos_generate_context_map.py is deprecated. Use `ontos map` instead.",
    DeprecationWarning,
    stacklevel=2
)

# === IMPORTS FROM NEW MODULES ===
from ontos.io.files import scan_documents, load_document
from ontos.io.yaml import parse_frontmatter_content
from ontos.core.validation import ValidationOrchestrator
from ontos.core.tokens import estimate_tokens, format_token_count
from ontos.commands.map import generate_context_map, GenerateMapOptions

# === LEGACY CONFIG IMPORTS (Phase 3 will move to .ontos.toml) ===
from ontos_config import (
    __version__,
    DOCS_DIR,
    CONTEXT_MAP_FILE,
    SKIP_PATTERNS,
    MAX_DEPENDENCY_DEPTH,
    ALLOWED_ORPHAN_TYPES,
)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Ontos Context Map",
        epilog="DEPRECATED: Use `ontos map` instead."
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path(CONTEXT_MAP_FILE),
        help="Output file path"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error on validation warnings"
    )
    parser.add_argument(
        "--no-staleness",
        action="store_true",
        help="Skip staleness detection"
    )
    parser.add_argument(
        "--no-timeline",
        action="store_true",
        help="Skip timeline section"
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Include lint warnings"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without writing"
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"ontos {__version__}"
    )

    args = parser.parse_args()

    # --- Step 1: Scan and load documents ---
    print(f"Scanning {DOCS_DIR}...")
    docs = {}
    doc_paths = list(scan_documents([Path(DOCS_DIR)], SKIP_PATTERNS))

    for path in doc_paths:
        try:
            doc = load_document(path, parse_frontmatter_content)
            docs[doc.id] = doc
        except Exception as e:
            print(f"  Warning: Failed to load {path}: {e}", file=sys.stderr)

    print(f"  Found {len(docs)} documents")

    # --- Step 2: Configure generation options ---
    options = GenerateMapOptions(
        output_path=args.output,
        strict=args.strict,
        include_staleness=not args.no_staleness,
        include_timeline=not args.no_timeline,
        include_lint=args.lint,
        max_dependency_depth=MAX_DEPENDENCY_DEPTH,
        dry_run=args.dry_run,
    )

    config = {
        "project_name": "Ontos",
        "allowed_orphan_types": ALLOWED_ORPHAN_TYPES,
        "version": __version__,
    }

    # --- Step 3: Generate context map ---
    print("Generating context map...")
    content, result = generate_context_map(docs, config, options)

    # --- Step 4: Report validation results ---
    if result.errors:
        print(f"\nErrors ({len(result.errors)}):", file=sys.stderr)
        for error in result.errors:
            print(f"  - {error.doc_id}: {error.message}", file=sys.stderr)

    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  - {warning.doc_id}: {warning.message}")

    # --- Step 5: Write output ---
    if args.dry_run:
        print("\n--- DRY RUN (not writing) ---")
        print(f"Would write {len(content)} bytes to {args.output}")
        token_count = estimate_tokens(content)
        print(f"Token estimate: {format_token_count(token_count)}")
    else:
        args.output.write_text(content, encoding="utf-8")
        print(f"\nGenerated: {args.output}")
        token_count = estimate_tokens(content)
        print(f"Token estimate: {format_token_count(token_count)}")

    # --- Step 6: Exit code ---
    if result.errors:
        return 1
    if args.strict and result.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
