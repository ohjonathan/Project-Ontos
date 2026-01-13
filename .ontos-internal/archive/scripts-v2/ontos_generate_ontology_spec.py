#!/usr/bin/env python3
"""Generate ontology_spec.md from ontology.py.

Usage:
    python3 ontos_generate_ontology_spec.py

Output:
    docs/reference/ontology_spec.md
"""

import importlib.util
from datetime import datetime, timezone
from pathlib import Path


def _load_module(module_name: str, rel_path: str):
    """Load a module dynamically without sys.path mutation."""
    module_path = Path(__file__).resolve().parent / rel_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_name} at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ontology = _load_module("ontos.core.ontology", "ontos/core/ontology.py")
schema = _load_module("ontos.core.schema", "ontos/core/schema.py")

TYPE_DEFINITIONS = ontology.TYPE_DEFINITIONS
FIELD_DEFINITIONS = ontology.FIELD_DEFINITIONS
SCHEMA_DEFINITIONS = schema.SCHEMA_DEFINITIONS


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
        "> Schema: v1.0–v3.0 (see schema.py for version differences)",
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
        "### Required Fields (All Types)",
        "",
        "| Field | Type | Description |",
        "|-------|------|-------------|",
    ])

    # Required + universal
    for name, fd in FIELD_DEFINITIONS.items():
        if fd.required and fd.applies_to is None:
            lines.append(f"| `{name}` | {fd.field_type} | {fd.description} |")

    lines.extend([
        "",
        "### Required Fields (Type-Specific)",
        "",
        "| Field | Type | Applies To | Description |",
        "|-------|------|------------|-------------|",
    ])

    # Required + type-specific
    for name, fd in FIELD_DEFINITIONS.items():
        if fd.required and fd.applies_to is not None:
            applies = ", ".join(fd.applies_to)
            lines.append(f"| `{name}` | {fd.field_type} | {applies} | {fd.description} |")

    lines.extend([
        "",
        "### Optional Fields",
        "",
        "| Field | Type | Applies To | Description |",
        "|-------|------|------------|-------------|",
    ])

    # Optional only
    for name, fd in FIELD_DEFINITIONS.items():
        if not fd.required:
            applies = ", ".join(fd.applies_to) if fd.applies_to else "all"
            lines.append(f"| `{name}` | {fd.field_type} | {applies} | {fd.description} |")

    # Schema version requirements section
    lines.extend([
        "",
        "---",
        "",
        "## 3. Schema Requirements by Version",
        "",
    ])

    for version in sorted(SCHEMA_DEFINITIONS.keys()):
        schema_def = SCHEMA_DEFINITIONS[version]
        required = ", ".join(schema_def.get("required", [])) or "(none)"
        optional = ", ".join(schema_def.get("optional", [])) or "(none)"
        lines.extend([
            f"### Schema v{version}",
            f"- Required: {required}",
            f"- Optional: {optional}",
            "",
        ])

    lines.extend([
        "---",
        "",
        "*End of Specification*",
    ])

    return "\n".join(lines) + "\n"


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
