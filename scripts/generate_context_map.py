import os
import yaml
import datetime
import argparse

DEFAULT_DOCS_DIR = 'docs'
OUTPUT_FILE = 'CONTEXT_MAP.md'

def parse_frontmatter(filepath):
    """Parses YAML frontmatter from a markdown file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    if content.startswith('---'):
        try:
            # Split by '---' and take the second element (the frontmatter)
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                return frontmatter
        except yaml.YAMLError as e:
            print(f"Error parsing YAML in {filepath}: {e}")
    return None

def scan_docs(root_dir):
    """Scans the docs directory for markdown files and parses their metadata."""
    files_data = {}
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(subdir, file)
                frontmatter = parse_frontmatter(filepath)
                if frontmatter and 'id' in frontmatter:
                    files_data[frontmatter['id']] = {
                        'filepath': filepath,
                        'filename': file,
                        'type': frontmatter.get('type', 'unknown'),
                        'depends_on': frontmatter.get('depends_on', []),
                        'status': frontmatter.get('status', 'unknown')
                    }
    return files_data

def generate_tree(files_data):
    """Generates a hierarchy tree string."""
    tree = []
    
    # Group by type
    by_type = {'kernel': [], 'strategy': [], 'product': [], 'atom': [], 'unknown': []}
    for doc_id, data in files_data.items():
        doc_type = data['type']
        if isinstance(doc_type, list):
            doc_type = doc_type[0] if doc_type else 'unknown'
            # Clean up if it looks like "[option1 | option2]"
            if '|' in str(doc_type): 
                 doc_type = 'unknown'

        if doc_type in by_type:
            by_type[doc_type].append(doc_id)
        else:
            by_type['unknown'].append(doc_id)
            
    order = ['kernel', 'strategy', 'product', 'atom', 'unknown']
    
    for doc_type in order:
        if by_type[doc_type]:
            tree.append(f"### {doc_type.upper()}")
            for doc_id in by_type[doc_type]:
                data = files_data[doc_id]
                deps = ", ".join(data['depends_on']) if data['depends_on'] else "None"
                tree.append(f"- **{doc_id}** ({data['filename']})")
                tree.append(f"  - Status: {data['status']}")
                tree.append(f"  - Depends On: {deps}")
            tree.append("")
            
    return "\n".join(tree)

def validate_dependencies(files_data):
    """Checks for broken links."""
    broken_links = []
    existing_ids = set(files_data.keys())
    
    for doc_id, data in files_data.items():
        deps = data['depends_on']
        if deps:
            for dep in deps:
                if dep not in existing_ids:
                    broken_links.append(f"- **{doc_id}** links to missing ID: `{dep}`")
                    
    return broken_links

def generate_context_map(target_dir):
    """Main function to generate the CONTEXT_MAP.md file."""
    print(f"Scanning {target_dir}...")
    files_data = scan_docs(target_dir)
    
    print("Generating tree...")
    tree_view = generate_tree(files_data)
    
    print("Validating dependencies...")
    broken_links = validate_dependencies(files_data)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f"""# Ontos Context Map
Generated on: {timestamp}
Scanned Directory: `{target_dir}`

## 1. Hierarchy Tree
{tree_view}

## 2. Dependency Audit
{'No broken links found.' if not broken_links else chr(10).join(broken_links)}

## 3. Index
| ID | Filename | Type |
|---|---|---|
"""
    
    for doc_id, data in files_data.items():
        content += f"| {doc_id} | [{data['filename']}]({data['filepath']}) | {data['type']} |\n"
        
    with open(OUTPUT_FILE, 'w') as f:
        f.write(content)
        
    print(f"Successfully generated {OUTPUT_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Ontos Context Map')
    parser.add_argument('--dir', type=str, default=DEFAULT_DOCS_DIR, help='Directory to scan for documentation (default: docs)')
    args = parser.parse_args()
    
    generate_context_map(args.dir)
