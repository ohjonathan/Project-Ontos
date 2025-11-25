import os

import argparse

DEFAULT_DOCS_DIR = 'docs'
PROMPT_FILE = 'migration_prompt.txt'

def has_frontmatter(filepath):
    """Checks if a file already has YAML frontmatter."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return f.readline().strip() == '---'
    except (IOError, PermissionError, OSError):
        return False

def scan_for_untagged_files(root_dir):
    """Finds all markdown files without frontmatter."""
    untagged = []
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(subdir, file)
                if not has_frontmatter(filepath):
                    untagged.append(filepath)
    return untagged

def generate_prompt(files):
    """Generates a prompt for the agent to process."""
    prompt = """# Ontos Migration Task

You are tagging documentation files with YAML frontmatter.

## Type Taxonomy

| Type | Definition | Signal Words |
|------|------------|--------------|
| kernel | Immutable foundational principles that rarely change | mission, values, philosophy, principles |
| strategy | High-level decisions about goals, audiences, approaches | goals, roadmap, monetization, target market |
| product | User-facing features, journeys, requirements | user flow, feature spec, requirements, user story |
| atom | Technical implementation details and specifications | API, schema, config, implementation, technical spec |

## Classification Heuristic

When uncertain: "If this document changes, what else breaks?"
- Everything breaks → kernel
- Business direction changes → strategy
- User experience changes → product
- Only implementation changes → atom

## Your Task

For each file below:
1. Read the file content
2. Determine the appropriate type, id, and dependencies
3. Add YAML frontmatter to the beginning of the file
4. After all files are tagged, run `python3 scripts/generate_context_map.py` to validate

## Files to Tag:

"""
    for filepath in files:
        prompt += f"- {filepath}\n"

    return prompt

def main():
    parser = argparse.ArgumentParser(description='Scan for untagged Ontos documentation files.')
    parser.add_argument('--dir', type=str, default=DEFAULT_DOCS_DIR,
                        help='Directory to scan (default: docs)')
    args = parser.parse_args()

    untagged = scan_for_untagged_files(args.dir)

    if not untagged:
        print("✅ All files are tagged. No migration needed.")
        return

    print(f"📋 Found {len(untagged)} untagged files:\n")
    for f in untagged:
        print(f"   - {f}")

    prompt = generate_prompt(untagged)

    with open(PROMPT_FILE, 'w') as f:
        f.write(prompt)

    print(f"\n📄 Migration prompt saved to '{PROMPT_FILE}'")
    print("\n💡 Next steps:")
    print("   1. Read each file listed above")
    print("   2. Add appropriate YAML frontmatter")
    print("   3. Run: python3 scripts/generate_context_map.py")

if __name__ == "__main__":
    main()
