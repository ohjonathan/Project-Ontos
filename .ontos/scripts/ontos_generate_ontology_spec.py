#!/usr/bin/env python3
"""Generate ontology_spec.md from ontology.py.

Usage:
    python3 ontos_generate_ontology_spec.py

Output:
    docs/reference/ontology_spec.md
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from ontos.core.ontology import (
    TYPE_DEFINITIONS,
    FIELD_DEFINITIONS,
)


def generate_spec() -> str:
    """Generate markdown specification from ontology definitions."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "---",
        "id: ontology_spec",
        "type: kernel",
        "status: active",
        "depends_on: [mission]",
        "---",
        "",
        "# Ontos Ontology Specification",
        "",
        "> **GENERATED FILE - DO NOT EDIT DIRECTLY**",
        ">",
        f"> Generated: {timestamp}",
        "> Source: `.ontos/scripts/ontos/core/ontology.py`",
        "",
        "---",
        "",
        "## 1. Document Types",
        "",
        "| Type | Rank | Can Depend On | Valid Statuses |",
        "|------|------|---------------|----------------|",
    ]

    for name, td in TYPE_DEFINITIONS.items():
        deps = ", ".join(td.can_depend_on) if td.can_depend_on else "(none)"
        statuses = ", ".join(td.valid_statuses)
        lines.append(f"| `{name}` | {td.rank} | {deps} | {statuses} |")

    lines.extend([
        "",
        "### Type Descriptions",
        "",
    ])

    for name, td in TYPE_DEFINITIONS.items():
        lines.append(f"- **{name}**: {td.description}")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Frontmatter Fields",
        "",
        "### Required Fields",
        "",
        "| Field | Type | Description |",
        "|-------|------|-------------|",
    ])

    for name, fd in FIELD_DEFINITIONS.items():
        if fd.required and fd.applies_to is None:
            lines.append(f"| `{name}` | {fd.field_type} | {fd.description} |")

    lines.extend([
        "",
        "### Optional Fields",
        "",
        "| Field | Type | Applies To | Description |",
        "|-------|------|------------|-------------|",
    ])

    for name, fd in FIELD_DEFINITIONS.items():
        if not fd.required or fd.applies_to is not None:
            applies = ", ".join(fd.applies_to) if fd.applies_to else "all"
            lines.append(f"| `{name}` | {fd.field_type} | {applies} | {fd.description} |")

    lines.extend([
        "",
        "---",
        "",
        "*End of Specification*",
    ])

    return "\n".join(lines)


def main():
    spec = generate_spec()

    # Determine output path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent  # .ontos/scripts -> project root
    output_path = project_root / "docs" / "reference" / "ontology_spec.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(spec, encoding="utf-8")

    print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
