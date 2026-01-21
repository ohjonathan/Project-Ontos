"""Native stub command implementation."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ontos.core.curation import create_stub, generate_id_from_path
from ontos.core.schema import serialize_frontmatter
from ontos.core.context import SessionContext
from ontos.io.files import find_project_root
from ontos.ui.output import OutputHandler


@dataclass
class StubOptions:
    """Options for stub command."""
    goal: Optional[str] = None
    doc_type: Optional[str] = None
    id: Optional[str] = None
    output: Optional[Path] = None
    depends_on: Optional[List[str]] = None
    quiet: bool = False
    json_output: bool = False


def interactive_stub(output: OutputHandler) -> dict:
    """Interactively create a stub."""
    # Note: For types, we'd ideally load them from ontology.py
    # For now, we'll use a standard list matching legacy.
    VALID_TYPES = ["kernel", "strategy", "product", "atom", "log"]
    
    print()
    output.info("Create Level 1 Stub Document")
    print("-" * 40)
    
    doc_id = input("Document ID (e.g., checkout_flow): ").strip()
    if not doc_id:
        output.error("Document ID is required")
        return {}
    
    valid_types_str = ', '.join(sorted(VALID_TYPES))
    print(f"\nValid types: {valid_types_str}")
    doc_type = input("Document type: ").strip().lower()
    if doc_type not in VALID_TYPES:
        output.error(f"Invalid type '{doc_type}'. Must be one of: {valid_types_str}")
        return {}
    
    goal = input("\nGoal (what does this document aim to describe?): ").strip()
    
    deps = input("\nDepends on (comma-separated IDs, or empty): ").strip()
    depends_on = [d.strip() for d in deps.split(',') if d.strip()] if deps else None
    
    output_path = input("\nOutput file path (or empty for stdout): ").strip()
    
    return {
        'id': doc_id,
        'type': doc_type,
        'goal': goal,
        'depends_on': depends_on,
        'output': Path(output_path) if output_path else None
    }


def write_stub_to_context(
    filepath: Path,
    frontmatter: dict,
    ctx: SessionContext,
    output: OutputHandler
) -> bool:
    """Generate content and buffer write for stub."""
    try:
        fm_yaml = serialize_frontmatter(frontmatter)
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
        filepath.parent.mkdir(parents=True, exist_ok=True)
        ctx.buffer_write(filepath, content)
        return True
    except Exception as e:
        output.error(f"Failed to prepare stub: {e}")
        return False


def stub_command(options: StubOptions) -> Tuple[int, str]:
    """Execute stub command."""
    output = OutputHandler(quiet=options.quiet)
    root = find_project_root()
    
    # Determine if interactive mode needed
    # Legacy logic: interactive if either goal or type is missing
    interactive = not (options.goal and options.doc_type)
    
    if interactive:
        params = interactive_stub(output)
        if not params:
            return 1, "Cancelled"
    else:
        doc_id = options.id
        if not doc_id and options.output:
            doc_id = generate_id_from_path(options.output)
            
        if not doc_id:
            output.error("Document ID required (via --id or --output)")
            return 1, "Missing ID"
            
        params = {
            'id': doc_id,
            'type': options.doc_type,
            'goal': options.goal,
            'depends_on': options.depends_on,
            'output': options.output
        }

    # Create stub frontmatter
    fm = create_stub(
        doc_id=params['id'],
        doc_type=params['type'],
        goal=params.get('goal', ''),
        depends_on=params.get('depends_on')
    )
    
    if params.get('output'):
        dest = params['output']
        if not dest.is_absolute():
            dest = root / dest
            
        ctx = SessionContext.from_repo(root)
        if write_stub_to_context(dest, fm, ctx, output):
            ctx.commit()
            output.success(f"Created stub: {dest}")
            return 0, f"Created {dest}"
        else:
            return 1, "Failed to write stub"
    else:
        # Print to stdout
        fm_yaml = serialize_frontmatter(fm)
        title = fm.get('id', 'Untitled').replace('_', ' ').title()
        goal = fm.get('goal', '')
        
        print("\n" + "-" * 40)
        print(f"---")
        print(fm_yaml)
        print("---")
        print(f"\n# {title}")
        print("\n## Goal")
        print(f"\n{goal if goal else '<!-- Describe the goal of this document -->'}")
        print("\n## Content")
        print("\n<!-- Add your content here -->")
        print("-" * 40)
        return 0, "Stub printed to stdout"
