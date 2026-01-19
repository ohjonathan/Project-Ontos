#!/usr/bin/env python3
"""Create Level 1 stub documents interactively or from arguments.

Usage:
    python3 ontos.py stub                        # Interactive mode
    python3 ontos.py stub --goal "..." --type product  # With arguments
    python3 ontos.py stub --output docs/my-feature.md  # Specify output file

Options:
    --goal TEXT         Goal description for the document
    --type TYPE         Document type (kernel, strategy, product, atom, log)
    --id DOC_ID         Document ID (auto-generated from --output if not specified)
    --output PATH       Output file path
    --depends-on IDS    Comma-separated list of dependency IDs
    -h, --help          Show this help

The stub command creates Level 1 documents with minimal frontmatter,
allowing users to gradually curate their documentation.
"""

import argparse
import sys
from pathlib import Path

# Fix sys.path to avoid ontos.py shadowing the ontos package.
# Python auto-inserts script dir at sys.path[0]; remove it before importing ontos.
SCRIPTS_DIR = Path(__file__).parent.resolve()
if sys.path and Path(sys.path[0]).resolve() == SCRIPTS_DIR:
    sys.path.pop(0)

# Import ontos package BEFORE adding scripts dir back to path
from ontos.core.context import SessionContext
from ontos.core.schema import serialize_frontmatter
from ontos.core.curation import create_stub, generate_id_from_path
from ontos.ui.output import OutputHandler

# Now add scripts dir to import ontos_config_defaults
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))
from ontos_config_defaults import PROJECT_ROOT, VALID_TYPES


def interactive_stub(output: OutputHandler) -> dict:
    """Interactively create a stub.
    
    Args:
        output: OutputHandler for messages.
        
    Returns:
        Dict with stub parameters or empty dict if cancelled.
    """
    print()
    output.info("Create Level 1 Stub Document")
    print("-" * 40)
    
    # Get document ID
    doc_id = input("Document ID (e.g., checkout_flow): ").strip()
    if not doc_id:
        output.error("Document ID is required")
        return {}
    
    # Get type
    valid_types = ', '.join(sorted(VALID_TYPES))
    print(f"\nValid types: {valid_types}")
    doc_type = input("Document type: ").strip().lower()
    if doc_type not in VALID_TYPES:
        output.error(f"Invalid type '{doc_type}'. Must be one of: {valid_types}")
        return {}
    
    # Get goal
    goal = input("\nGoal (what does this document aim to describe?): ").strip()
    if not goal:
        output.warning("No goal provided. Documents at Level 1 should have a goal.")
        goal = ""
    
    # Optional depends_on
    deps = input("\nDepends on (comma-separated IDs, or empty): ").strip()
    depends_on = [d.strip() for d in deps.split(',') if d.strip()] if deps else None
    
    # Output path
    output_path = input("\nOutput file path (or empty for stdout): ").strip()
    
    return {
        'id': doc_id,
        'type': doc_type,
        'goal': goal,
        'depends_on': depends_on,
        'output': output_path or None
    }


def write_stub_file(
    filepath: Path,
    frontmatter: dict,
    ctx: SessionContext = None,
    output: OutputHandler = None
) -> bool:
    """Write stub to file.
    
    Args:
        filepath: Path to write to.
        frontmatter: Stub frontmatter dict.
        ctx: Optional SessionContext.
        output: Optional OutputHandler.
        
    Returns:
        True if successful.
    """
    _owns_ctx = ctx is None
    if _owns_ctx:
        ctx = SessionContext()
    
    if output is None:
        output = OutputHandler()
    
    try:
        # Serialize frontmatter
        fm_yaml = serialize_frontmatter(frontmatter)
        
        # Create document content
        title = frontmatter.get('id', 'Untitled').replace('_', ' ').title()
        goal = frontmatter.get('goal', '')
        
        content = f"""---
{fm_yaml}
---

# {title}

## Goal

{goal if goal else '<!-- Describe the goal of this document -->'}

## Content

<!-- Add your content here -->
"""
        
        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Buffer the write
        ctx.buffer_write(filepath, content)
        
        if _owns_ctx:
            ctx.commit()
        
        output.success(f"Created stub: {filepath}")
        return True
        
    except Exception as e:
        output.error(f"Failed to create stub: {e}")
        return False


def print_stub_to_stdout(frontmatter: dict, output: OutputHandler = None):
    """Print stub content to stdout.
    
    Args:
        frontmatter: Stub frontmatter dict.
        output: Optional OutputHandler.
    """
    if output is None:
        output = OutputHandler()
    
    fm_yaml = serialize_frontmatter(frontmatter)
    title = frontmatter.get('id', 'Untitled').replace('_', ' ').title()
    goal = frontmatter.get('goal', '')
    
    print()
    print("-" * 40)
    print(f"""---
{fm_yaml}
---

# {title}

## Goal

{goal if goal else '<!-- Describe the goal of this document -->'}

## Content

<!-- Add your content here -->
""")
    print("-" * 40)


def main() -> int:
    """Main entry point for stub command."""
    parser = argparse.ArgumentParser(
        description="Create Level 1 stub documents."
    )
    parser.add_argument(
        '--goal', '-g',
        help="Goal description for the document"
    )
    parser.add_argument(
        '--type', '-t', dest='doc_type',
        choices=sorted(VALID_TYPES),
        help="Document type"
    )
    parser.add_argument(
        '--id',
        help="Document ID (auto-generated from --output if not specified)"
    )
    parser.add_argument(
        '--output', '-o',
        help="Output file path"
    )
    parser.add_argument(
        '--depends-on', '-d',
        help="Comma-separated list of dependency IDs"
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help="Minimal output"
    )
    
    args = parser.parse_args()
    output = OutputHandler(quiet=args.quiet)
    
    # Determine if interactive mode needed
    interactive = not (args.goal and args.doc_type)
    
    if interactive:
        params = interactive_stub(output)
        if not params:
            return 1
    else:
        # Parse depends_on
        depends_on = None
        if args.depends_on:
            depends_on = [d.strip() for d in args.depends_on.split(',') if d.strip()]
        
        # Determine ID
        doc_id = args.id
        if not doc_id and args.output:
            doc_id = generate_id_from_path(Path(args.output))
        if not doc_id:
            output.error("Document ID required (via --id or --output)")
            return 1
        
        params = {
            'id': doc_id,
            'type': args.doc_type,
            'goal': args.goal,
            'depends_on': depends_on,
            'output': args.output
        }
    
    # Create stub frontmatter
    frontmatter = create_stub(
        doc_id=params['id'],
        doc_type=params['type'],
        goal=params.get('goal', ''),
        depends_on=params.get('depends_on')
    )
    
    # Output to file or stdout
    if params.get('output'):
        filepath = Path(params['output'])
        if not filepath.is_absolute():
            filepath = Path(PROJECT_ROOT) / filepath
        return 0 if write_stub_file(filepath, frontmatter, output=output) else 1
    else:
        print_stub_to_stdout(frontmatter, output)
        return 0


def emit_deprecation_notice(message: str) -> None:
    """Always-visible CLI notice for deprecated usage."""
    import sys
    print(f"[DEPRECATION] {message}", file=sys.stderr)


if __name__ == '__main__':
    import os
    if not os.environ.get('ONTOS_CLI_DISPATCH'):
        if not os.environ.get('ONTOS_NO_DEPRECATION_WARNINGS'):
            emit_deprecation_notice(
                f"Direct execution of {Path(__file__).name} is deprecated. "
                "Use 'python3 ontos.py stub' instead. "
                "Direct script execution will be removed in v3.0."
            )
    sys.exit(main())
