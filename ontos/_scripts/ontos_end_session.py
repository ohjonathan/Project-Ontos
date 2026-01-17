#!/usr/bin/env python3
"""
End Session and Create Log.

DEPRECATED: This script is a compatibility wrapper.
Use `ontos log` or `python -m ontos.commands.log` instead.

Phase 2 v3.0: Reduced to <200 lines per spec requirement.
"""

import argparse
import sys
import warnings
from pathlib import Path

# === DEPRECATION WARNING ===
warnings.warn(
    "ontos_end_session.py is deprecated. Use `ontos log` instead.",
    DeprecationWarning,
    stacklevel=2
)

# === IMPORTS FROM NEW MODULES ===
from ontos.io.git import (
    get_current_branch,
    get_commits_since_push,
    get_changed_files_since_push,
)
from ontos.commands.log import (
    create_session_log,
    suggest_session_impacts,
    validate_session_concepts,
    EndSessionOptions,
)

# === LEGACY CONFIG IMPORTS (Phase 3 will move to .ontos.toml) ===
from ontos_config import (
    __version__,
    PROJECT_ROOT,
    CONTEXT_MAP_FILE,
)

# Try to get default source
try:
    from ontos_config import DEFAULT_SOURCE
except ImportError:
    DEFAULT_SOURCE = None


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create session log",
        epilog="DEPRECATED: Use `ontos log` instead."
    )
    parser.add_argument(
        "--event-type", "-e",
        default="chore",
        choices=["feat", "fix", "chore", "docs", "refactor", "test", "perf", "release"],
        help="Event type (default: chore)"
    )
    parser.add_argument(
        "--topic", "-t",
        help="Session topic (auto-generated if not provided)"
    )
    parser.add_argument(
        "--source", "-s",
        default=DEFAULT_SOURCE,
        help="Author/source identifier"
    )
    parser.add_argument(
        "--concepts", "-c",
        nargs="*",
        default=[],
        help="Concepts to tag"
    )
    parser.add_argument(
        "--impacts", "-i",
        nargs="*",
        default=[],
        help="Impact doc IDs (auto-suggested if not provided)"
    )
    parser.add_argument(
        "--auto", "-a",
        action="store_true",
        help="Auto mode (no prompts)"
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

    project_root = Path(PROJECT_ROOT)
    context_map_path = project_root / CONTEXT_MAP_FILE

    # --- Step 1: Gather git information ---
    print("Gathering git information...")
    branch = get_current_branch() or "unknown"
    commits = get_commits_since_push()
    changed_files = get_changed_files_since_push()

    print(f"  Branch: {branch}")
    print(f"  Commits since push: {len(commits)}")
    print(f"  Files changed: {len(changed_files)}")

    git_info = {
        "branch": branch,
        "commits": commits,
        "changed_files": changed_files,
    }

    # --- Step 2: Get or prompt for source ---
    source = args.source
    if not source and not args.auto:
        source = input("Source (author): ").strip()
    source = source or "unknown"

    # --- Step 3: Get or prompt for topic ---
    topic = args.topic
    if not topic and not args.auto:
        suggested = commits[0][:50] if commits else "session"
        topic = input(f"Topic [{suggested}]: ").strip() or suggested

    # --- Step 4: Suggest impacts if not provided ---
    impacts = list(args.impacts)
    if not impacts:
        print("Suggesting impacts...")
        impacts = suggest_session_impacts(context_map_path, changed_files, commits)
        if impacts:
            print(f"  Suggested: {', '.join(impacts[:5])}")

    # --- Step 5: Validate concepts ---
    concepts = list(args.concepts)
    if concepts:
        valid, unknown = validate_session_concepts(context_map_path, concepts)
        if unknown:
            print(f"  Warning: Unknown concepts: {', '.join(unknown)}")

    # --- Step 6: Create session log ---
    options = EndSessionOptions(
        event_type=args.event_type,
        topic=topic,
        source=source,
        concepts=concepts,
        impacts=impacts,
        branch=branch,
        dry_run=args.dry_run,
    )

    content, output_path = create_session_log(project_root, options, git_info)

    # --- Step 7: Output ---
    if args.dry_run:
        print("\n--- DRY RUN (not writing) ---")
        print(content)
        print(f"\nWould write to: {output_path}")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"\nCreated: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
